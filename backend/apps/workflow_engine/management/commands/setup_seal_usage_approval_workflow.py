"""
配置用印申请审批流程
流程：申请人 -> 部门经理审批 -> 结束
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from backend.apps.workflow_engine.models import WorkflowTemplate, ApprovalNode
from backend.apps.system_management.models import Role

User = get_user_model()


class Command(BaseCommand):
    help = '配置用印申请审批流程：申请人 -> 部门经理审批'

    def handle(self, *args, **options):
        self.stdout.write('开始配置用印申请审批流程...')
        
        # 获取或创建流程模板
        workflow, created = WorkflowTemplate.objects.get_or_create(
            code='seal_usage_approval',
            defaults={
                'name': '用印申请审批流程',
                'description': '用印申请的审批流程：申请人 -> 部门经理审批',
                'category': '行政管理',
                'status': 'active',
                'allow_withdraw': True,
                'allow_reject': True,
                'allow_transfer': False,
                'timeout_hours': 24,  # 24小时超时
                'timeout_action': 'notify',
                'created_by': User.objects.filter(is_superuser=True).first() or User.objects.first(),
            }
        )
        
        # 更新适用模型
        try:
            from backend.apps.administrative_management.models import SealUsage
            content_type = ContentType.objects.get_for_model(SealUsage)
            model_name = content_type.model.lower()  # 'sealusage'
            if model_name not in workflow.applicable_models:
                workflow.applicable_models.append(model_name)
                workflow.save()
                self.stdout.write(f'✓ 已添加适用模型：{model_name}')
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'⚠ 无法自动添加适用模型：{e}'))
            self.stdout.write('  请手动在后台管理中配置适用模型为：sealusage')
        
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
        
        # 节点0：开始节点
        start_node, _ = ApprovalNode.objects.get_or_create(
            workflow=workflow,
            sequence=0,
            defaults={
                'name': '开始',
                'node_type': 'start',
                'description': '审批流程开始节点'
            }
        )
        if start_node.node_type != 'start':
            start_node.node_type = 'start'
            start_node.name = '开始'
            start_node.save()
        self.stdout.write(self.style.SUCCESS(f'✓ 创建/更新开始节点：{start_node.name}'))
        
        # 节点1：部门经理审批
        node1, _ = ApprovalNode.objects.get_or_create(
            workflow=workflow,
            sequence=1,
            defaults={
                'name': '部门经理审批',
                'node_type': 'approval',
                'approver_type': 'department_manager',  # 使用部门经理类型
                'approval_mode': 'single',  # 单人审批
                'is_required': True,
                'can_reject': True,
                'can_transfer': False,
                'timeout_hours': 24,
                'description': '申请人所在部门的经理审批用印申请'
            }
        )
        # 更新节点配置（如果已存在）
        if not _:
            node1.name = '部门经理审批'
            node1.node_type = 'approval'
            node1.approver_type = 'department_manager'
            node1.approval_mode = 'single'
            node1.is_required = True
            node1.can_reject = True
            node1.can_transfer = False
            node1.timeout_hours = 24
            node1.description = '申请人所在部门的经理审批用印申请'
            node1.save()
        
        self.stdout.write(self.style.SUCCESS(f'✓ 创建/更新节点1：{node1.name}'))
        self.stdout.write(f'  审批人类型：部门经理（自动获取申请人所在部门的经理）')
        
        # 节点2：结束节点
        end_node, _ = ApprovalNode.objects.get_or_create(
            workflow=workflow,
            sequence=2,
            defaults={
                'name': '结束',
                'node_type': 'end',
                'description': '审批流程结束节点'
            }
        )
        if end_node.node_type != 'end':
            end_node.node_type = 'end'
            end_node.name = '结束'
            end_node.save()
        self.stdout.write(self.style.SUCCESS(f'✓ 创建/更新结束节点：{end_node.name}'))
        
        # 显示流程配置摘要
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('用印申请审批流程配置完成！'))
        self.stdout.write('='*60)
        self.stdout.write(f'流程名称：{workflow.name}')
        self.stdout.write(f'流程代码：{workflow.code}')
        self.stdout.write(f'流程状态：{workflow.get_status_display()}')
        self.stdout.write(f'适用模型：{", ".join(workflow.applicable_models) if workflow.applicable_models else "未配置"}')
        self.stdout.write('\n审批节点：')
        for i, node in enumerate(workflow.nodes.all().order_by('sequence'), 1):
            approver_info = '未配置'
            if node.approver_type == 'department_manager':
                approver_info = '申请人所在部门的经理'
            elif node.approver_type == 'role' and node.approver_roles.exists():
                roles = ', '.join([r.name for r in node.approver_roles.all()])
                approver_info = f'角色：{roles}'
            elif node.approver_type == 'user' and node.approver_users.exists():
                users = ', '.join([u.username for u in node.approver_users.all()])
                approver_info = f'用户：{users}'
            
            self.stdout.write(f'  {i}. {node.name} (顺序：{node.sequence})')
            self.stdout.write(f'     节点类型：{node.get_node_type_display()}')
            if node.node_type == 'approval':
                self.stdout.write(f'     审批人：{approver_info}')
                self.stdout.write(f'     审批模式：{node.get_approval_mode_display()}')
                self.stdout.write(f'     是否必审：{"是" if node.is_required else "否"}')
                self.stdout.write(f'     可驳回：{"是" if node.can_reject else "否"}')
                self.stdout.write(f'     可转交：{"是" if node.can_transfer else "否"}')
                self.stdout.write(f'     超时时间：{node.timeout_hours or workflow.timeout_hours}小时')
            if node.description:
                self.stdout.write(f'     描述：{node.description}')
        
        self.stdout.write('\n' + '='*60)
        self.stdout.write('流程说明：')
        self.stdout.write('1. 申请人提交用印申请')
        self.stdout.write('2. 申请人所在部门的经理审批（必须通过）')
        self.stdout.write('3. 审批完成，用印申请生效')
        self.stdout.write('\n使用方法：')
        self.stdout.write('在用印申请创建视图中调用：')
        self.stdout.write('  from backend.apps.workflow_engine.services import ApprovalEngine')
        self.stdout.write('  ApprovalEngine.start_approval(workflow, seal_usage, user, comment)')
        self.stdout.write('\n注意事项：')
        self.stdout.write('- 每个节点审批超时时间为24小时')
        self.stdout.write('- 审批过程中可以驳回，驳回后流程终止')
        self.stdout.write('- 审批过程中可以撤回（如果流程配置允许）')
        self.stdout.write('- 适用模型：sealusage（用印申请）')
        self.stdout.write('='*60)
