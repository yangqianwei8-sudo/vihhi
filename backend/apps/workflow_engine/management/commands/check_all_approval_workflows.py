"""
检查所有审批流程模板和实例，确保配置正确
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Count, Q
from backend.apps.workflow_engine.models import WorkflowTemplate, ApprovalNode, ApprovalInstance, ApprovalRecord
from backend.apps.workflow_engine.services import ApprovalEngine


class Command(BaseCommand):
    help = '检查所有审批流程模板和实例，确保配置正确'

    def add_arguments(self, parser):
        parser.add_argument(
            '--fix',
            action='store_true',
            help='自动修复发现的问题',
        )
        parser.add_argument(
            '--workflow-code',
            type=str,
            help='只检查指定的流程代码',
        )

    def handle(self, *args, **options):
        fix_issues = options.get('fix', False)
        workflow_code = options.get('workflow_code')
        
        self.stdout.write(self.style.SUCCESS('=' * 80))
        self.stdout.write(self.style.SUCCESS('开始检查所有审批流程'))
        self.stdout.write(self.style.SUCCESS('=' * 80))
        self.stdout.write('')
        
        # 获取所有流程模板
        if workflow_code:
            workflows = WorkflowTemplate.objects.filter(code=workflow_code)
        else:
            workflows = WorkflowTemplate.objects.all().order_by('code')
        
        if not workflows.exists():
            self.stdout.write(self.style.WARNING('未找到审批流程模板'))
            return
        
        total_issues = 0
        total_fixed = 0
        
        for workflow in workflows:
            self.stdout.write('-' * 80)
            self.stdout.write(self.style.SUCCESS(f'检查流程: {workflow.name} ({workflow.code})'))
            self.stdout.write(f'  状态: {workflow.get_status_display()}')
            self.stdout.write(f'  分类: {workflow.category or "未设置"}')
            self.stdout.write('')
            
            # 检查1: 流程是否有节点
            nodes = workflow.nodes.all().order_by('sequence')
            if not nodes.exists():
                self.stdout.write(self.style.ERROR('  ❌ 问题1: 流程没有配置任何节点'))
                total_issues += 1
                continue
            
            # 检查2: 是否有开始节点
            start_node = nodes.filter(node_type='start').first()
            if not start_node:
                self.stdout.write(self.style.ERROR('  ❌ 问题2: 流程没有开始节点'))
                total_issues += 1
                if fix_issues:
                    # 创建开始节点
                    start_node = ApprovalNode.objects.create(
                        workflow=workflow,
                        sequence=0,
                        name='开始',
                        node_type='start',
                        description='审批流程开始节点'
                    )
                    self.stdout.write(self.style.SUCCESS('    ✓ 已创建开始节点'))
                    total_fixed += 1
            
            # 检查3: 是否有结束节点
            end_node = nodes.filter(node_type='end').first()
            if not end_node:
                self.stdout.write(self.style.ERROR('  ❌ 问题3: 流程没有结束节点'))
                total_issues += 1
                if fix_issues:
                    # 创建结束节点
                    max_sequence = nodes.aggregate(max_seq=Count('sequence'))['max_seq'] or 0
                    end_node = ApprovalNode.objects.create(
                        workflow=workflow,
                        sequence=max_sequence + 1,
                        name='结束',
                        node_type='end',
                        description='审批流程结束节点'
                    )
                    self.stdout.write(self.style.SUCCESS('    ✓ 已创建结束节点'))
                    total_fixed += 1
            
            # 检查4: 节点顺序是否连续
            sequences = list(nodes.values_list('sequence', flat=True).order_by('sequence'))
            expected_sequences = list(range(len(sequences)))
            if sequences != expected_sequences:
                self.stdout.write(self.style.WARNING('  ⚠ 问题4: 节点顺序不连续'))
                self.stdout.write(f'    当前顺序: {sequences}')
                self.stdout.write(f'    期望顺序: {expected_sequences}')
                total_issues += 1
                if fix_issues:
                    # 重新排序节点
                    for idx, node in enumerate(nodes.order_by('sequence')):
                        if node.sequence != idx:
                            node.sequence = idx
                            node.save()
                    self.stdout.write(self.style.SUCCESS('    ✓ 已修复节点顺序'))
                    total_fixed += 1
            
            # 检查5: 检查每个审批节点是否有审批人配置
            approval_nodes = nodes.filter(node_type='approval')
            for node in approval_nodes:
                # 尝试用示例实例检查审批人配置
                sample_instance = ApprovalInstance.objects.filter(workflow=workflow).first()
                approvers = []
                
                if sample_instance:
                    approvers = ApprovalEngine._get_approvers(node, sample_instance)
                else:
                    # 如果没有实例，根据节点类型检查配置
                    if node.approver_type == 'user':
                        approvers = list(node.approver_users.all())
                    elif node.approver_type == 'role':
                        from backend.apps.system_management.models import User, Role
                        role_ids = node.approver_roles.values_list('id', flat=True)
                        approvers = list(User.objects.filter(roles__id__in=role_ids, is_active=True).distinct())
                    elif node.approver_type == 'department':
                        from backend.apps.system_management.models import User
                        dept_ids = node.approver_departments.values_list('id', flat=True)
                        approvers = list(User.objects.filter(department_id__in=dept_ids, is_active=True).distinct())
                    # department_manager 和 creator 类型需要实例才能检查，这里跳过
                
                if not approvers and node.is_required:
                        self.stdout.write(self.style.WARNING(
                            f'  ⚠ 问题5: 审批节点 "{node.name}" (顺序: {node.sequence}) 是必审节点但没有配置审批人'
                        ))
                        self.stdout.write(f'    审批人类型: {node.get_approver_type_display()}')
                        if node.approver_type == 'role':
                            roles = node.approver_roles.all()
                            if roles.exists():
                                self.stdout.write(f'    配置的角色: {", ".join([r.name for r in roles])}')
                            else:
                                self.stdout.write('    未配置角色')
                        elif node.approver_type == 'user':
                            users = node.approver_users.all()
                            if users.exists():
                                self.stdout.write(f'    配置的用户: {", ".join([u.get_full_name() or u.username for u in users])}')
                            else:
                                self.stdout.write('    未配置用户')
                        total_issues += 1
            
            # 检查6: 检查流程实例
            instances = ApprovalInstance.objects.filter(workflow=workflow)
            pending_instances = instances.filter(status='pending')
            
            self.stdout.write(f'  流程实例统计:')
            self.stdout.write(f'    总数: {instances.count()}')
            self.stdout.write(f'    审批中: {pending_instances.count()}')
            self.stdout.write(f'    已通过: {instances.filter(status="approved").count()}')
            self.stdout.write(f'    已驳回: {instances.filter(status="rejected").count()}')
            self.stdout.write(f'    已撤回: {instances.filter(status="withdrawn").count()}')
            
            # 检查7: 检查卡住的审批实例
            stuck_instances = []
            for instance in pending_instances:
                issues = []
                
                # 检查当前节点
                if not instance.current_node:
                    issues.append('当前节点为空')
                elif instance.current_node.node_type == 'end':
                    issues.append('卡在结束节点')
                elif instance.current_node.node_type == 'approval':
                    # 检查节点是否已完成但未进入下一节点
                    is_completed = ApprovalEngine._check_node_completed(instance, instance.current_node)
                    if is_completed:
                        next_node = ApprovalEngine._get_next_node(instance.current_node)
                        if next_node:
                            issues.append(f'节点已完成但未进入下一节点: {next_node.name}')
                        else:
                            issues.append('节点已完成但没有下一个节点')
                
                if issues:
                    stuck_instances.append((instance, issues))
            
            if stuck_instances:
                self.stdout.write(self.style.WARNING(f'  ⚠ 问题6: 发现 {len(stuck_instances)} 个卡住的审批实例:'))
                for instance, issues in stuck_instances:
                    self.stdout.write(f'    - {instance.instance_number}: {", ".join(issues)}')
                    if fix_issues:
                        # 尝试修复
                        try:
                            from backend.apps.workflow_engine.management.commands.fix_stuck_approvals import Command as FixCommand
                            fix_cmd = FixCommand()
                            fix_cmd.stdout = self.stdout
                            fix_cmd.style = self.style
                            # 这里可以调用修复逻辑，但为了简化，我们直接提示运行修复命令
                            self.stdout.write(self.style.SUCCESS(f'      提示: 运行 python manage.py fix_stuck_approvals --instance-number {instance.instance_number} 来修复'))
                        except Exception as e:
                            self.stdout.write(self.style.ERROR(f'      修复失败: {str(e)}'))
                total_issues += len(stuck_instances)
            
            # 检查8: 节点配置完整性
            self.stdout.write('  节点配置:')
            for node in nodes.order_by('sequence'):
                node_info = f'    {node.sequence}. {node.name} ({node.get_node_type_display()})'
                if node.node_type == 'approval':
                    approver_info = '未配置'
                    if node.approver_type == 'department_manager':
                        approver_info = '部门经理（自动获取）'
                    elif node.approver_type == 'role' and node.approver_roles.exists():
                        approver_info = f'角色: {", ".join([r.name for r in node.approver_roles.all()])}'
                    elif node.approver_type == 'user' and node.approver_users.exists():
                        approver_info = f'用户: {", ".join([u.get_full_name() or u.username for u in node.approver_users.all()])}'
                    node_info += f' - 审批人: {approver_info}'
                    node_info += f' - 必审: {"是" if node.is_required else "否"}'
                self.stdout.write(node_info)
            
            self.stdout.write('')
        
        # 输出总结
        self.stdout.write('')
        self.stdout.write('=' * 80)
        self.stdout.write(self.style.SUCCESS('检查完成'))
        self.stdout.write('=' * 80)
        self.stdout.write(f'  检查的流程数: {workflows.count()}')
        self.stdout.write(self.style.ERROR(f'  发现的问题数: {total_issues}'))
        if fix_issues:
            self.stdout.write(self.style.SUCCESS(f'  已修复的问题数: {total_fixed}'))
        else:
            self.stdout.write('  提示: 使用 --fix 参数可以自动修复部分问题')
            self.stdout.write('  提示: 使用 python manage.py fix_stuck_approvals 修复卡住的审批实例')
        
        if total_issues == 0:
            self.stdout.write(self.style.SUCCESS('  ✓ 所有审批流程配置正常！'))
