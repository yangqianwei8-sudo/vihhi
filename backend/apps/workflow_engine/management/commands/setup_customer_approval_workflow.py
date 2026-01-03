"""
配置客户管理审批流程
流程：申请人 -> 部门经理审批 -> 部门总监审批（可选）-> 总经理审批
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from backend.apps.workflow_engine.models import WorkflowTemplate, ApprovalNode
from backend.apps.system_management.models import Role

User = get_user_model()


class Command(BaseCommand):
    help = '配置客户管理审批流程：申请人 -> 连续多级审批 -> 总经理'

    def handle(self, *args, **options):
        self.stdout.write('开始配置客户管理审批流程...')
        
        # 获取或创建流程模板
        workflow, created = WorkflowTemplate.objects.get_or_create(
            code='customer_management_approval',
            defaults={
                'name': '客户管理审批流程',
                'description': '客户创建、修改等操作的审批流程，包含多级审批：部门经理 -> 部门总监 -> 总经理',
                'category': '客户管理',
                'status': 'active',
                'allow_withdraw': True,
                'allow_reject': True,
                'allow_transfer': False,
                'timeout_hours': 24,  # 每个节点24小时超时
                'timeout_action': 'notify',
                'created_by': User.objects.filter(is_superuser=True).first() or User.objects.first(),
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f'✓ 创建审批流程模板：{workflow.name}'))
        else:
            self.stdout.write(self.style.WARNING(f'⚠ 审批流程模板已存在：{workflow.name}，将更新节点配置'))
            # 检查是否有审批记录关联到节点
            from backend.apps.workflow_engine.models import ApprovalRecord
            nodes_with_records = workflow.nodes.filter(records__isnull=False).distinct()
            if nodes_with_records.exists():
                self.stdout.write(self.style.WARNING('  警告：部分节点已有审批记录，将保留这些节点，仅更新无记录的节点'))
                # 只删除没有审批记录的节点
                nodes_to_delete = workflow.nodes.exclude(id__in=nodes_with_records.values_list('id', flat=True))
                deleted_count = nodes_to_delete.delete()[0]
                if deleted_count > 0:
                    self.stdout.write(f'  已删除 {deleted_count} 个无记录的旧节点')
            else:
                # 删除旧节点
                workflow.nodes.all().delete()
                self.stdout.write('  已清除旧节点配置')
        
        # 获取角色
        business_manager_role = Role.objects.filter(code='business_manager').first()
        business_team_role = Role.objects.filter(code='business_team').first()
        general_manager_role = Role.objects.filter(code='general_manager').first()
        
        if not general_manager_role:
            self.stdout.write(self.style.ERROR('错误：未找到总经理角色（general_manager），请先创建该角色'))
            return
        
        # 节点0：开始节点
        start_node = ApprovalNode.objects.create(
            workflow=workflow,
            name='开始',
            node_type='start',
            sequence=0,
            description='审批流程开始节点'
        )
        self.stdout.write(self.style.SUCCESS(f'✓ 创建开始节点：{start_node.name}'))
        
        # 节点1：部门经理审批
        node1 = ApprovalNode.objects.create(
            workflow=workflow,
            name='部门经理审批',
            node_type='approval',
            sequence=1,
            approver_type='role',
            approval_mode='single',  # 单人审批
            is_required=True,
            can_reject=True,
            can_transfer=False,
            timeout_hours=24,
            description='部门经理审批客户创建申请，审核客户基本信息、资质等'
        )
        
        # 设置审批人角色（优先使用business_manager，如果没有则使用business_team）
        if business_manager_role:
            node1.approver_roles.add(business_manager_role)
            self.stdout.write(f'  节点1审批人：{business_manager_role.name}')
        elif business_team_role:
            node1.approver_roles.add(business_team_role)
            self.stdout.write(f'  节点1审批人：{business_team_role.name}')
        else:
            self.stdout.write(self.style.WARNING('  警告：未找到商务部经理角色，节点1将使用部门经理类型'))
            node1.approver_type = 'department_manager'
            node1.save()
        
        self.stdout.write(self.style.SUCCESS(f'✓ 创建节点1：{node1.name}'))
        
        # 节点2：总经理审批
        node2 = ApprovalNode.objects.create(
            workflow=workflow,
            name='总经理审批',
            node_type='approval',
            sequence=2,
            approver_type='role',
            approval_mode='single',  # 单人审批
            is_required=True,
            can_reject=True,
            can_transfer=False,
            timeout_hours=24,
            description='总经理最终审批客户创建申请'
        )
        
        # 设置总经理角色
        node2.approver_roles.add(general_manager_role)
        self.stdout.write(f'  节点2审批人：{general_manager_role.name}')
        
        self.stdout.write(self.style.SUCCESS(f'✓ 创建节点2：{node2.name}'))
        
        # 节点3：结束节点
        end_node = ApprovalNode.objects.create(
            workflow=workflow,
            name='结束',
            node_type='end',
            sequence=3,
            description='审批流程结束节点'
        )
        self.stdout.write(self.style.SUCCESS(f'✓ 创建结束节点：{end_node.name}'))
        
        # 显示流程配置摘要
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('客户管理审批流程配置完成！'))
        self.stdout.write('='*60)
        self.stdout.write(f'流程名称：{workflow.name}')
        self.stdout.write(f'流程代码：{workflow.code}')
        self.stdout.write(f'流程状态：{workflow.get_status_display()}')
        self.stdout.write('\n审批节点：')
        for i, node in enumerate(workflow.nodes.all().order_by('sequence'), 1):
            approver_info = '未配置'
            if node.approver_type == 'role' and node.approver_roles.exists():
                roles = ', '.join([r.name for r in node.approver_roles.all()])
                approver_info = f'角色：{roles}'
            elif node.approver_type == 'department_manager':
                approver_info = '部门经理'
            
            self.stdout.write(f'  {i}. {node.name} (顺序：{node.sequence})')
            self.stdout.write(f'     审批人：{approver_info}')
            self.stdout.write(f'     审批模式：{node.get_approval_mode_display()}')
            self.stdout.write(f'     超时时间：{node.timeout_hours or workflow.timeout_hours}小时')
        
        self.stdout.write('\n' + '='*60)
        self.stdout.write('流程说明：')
        self.stdout.write('1. 申请人创建客户并提交审批')
        self.stdout.write('2. 部门经理审批（必须通过，审核客户基本信息、资质等）')
        self.stdout.write('3. 总经理审批（必须通过，最终审核）')
        self.stdout.write('4. 审批完成，客户正式创建')
        self.stdout.write('\n注意事项：')
        self.stdout.write('- 每个节点审批超时时间为24小时')
        self.stdout.write('- 审批过程中可以驳回，驳回后流程终止')
        self.stdout.write('- 审批过程中可以撤回（如果流程配置允许）')
        self.stdout.write('='*60)

