"""
配置创建目标审批流程
流程：申请人 -> 总经理审批
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from backend.apps.workflow_engine.models import WorkflowTemplate, ApprovalNode
from backend.apps.system_management.models import Role

User = get_user_model()


class Command(BaseCommand):
    help = '配置创建目标审批流程：申请人 -> 总经理'

    def handle(self, *args, **options):
        self.stdout.write('开始配置创建目标审批流程...')

        # 获取或创建审批流程模板
        workflow, created = WorkflowTemplate.objects.get_or_create(
            code='goal_creation_approval',
            defaults={
                'name': '创建目标审批流程',
                'description': '战略目标创建操作的审批流程',
                'category': '计划管理',
                'status': 'active',
                'allow_withdraw': True,
                'allow_reject': True,
                'allow_transfer': False,
                'timeout_hours': 24,
                'timeout_action': 'notify',
                'applicable_models': ['strategicgoal'],
                'form_filter_conditions': {
                    'strategicgoal': ['strategicgoal']  # 仅适用于创建战略目标表单
                },
                'created_by': User.objects.filter(is_superuser=True).first() or User.objects.first(),
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'✓ 创建审批流程：{workflow.name}'))
        else:
            self.stdout.write(self.style.WARNING(f'⚠ 流程已存在：{workflow.name}'))
            # 如果流程已存在，删除现有节点（如果没有审批记录）
            from backend.apps.workflow_engine.models import ApprovalRecord
            nodes_with_records = workflow.nodes.filter(records__isnull=False).distinct()
            if nodes_with_records.exists():
                nodes_to_delete = workflow.nodes.exclude(id__in=nodes_with_records.values_list('id', flat=True))
                nodes_to_delete.delete()
            else:
                workflow.nodes.all().delete()

        # 查找总经理角色
        general_manager_role = Role.objects.filter(code='general_manager').first()
        if not general_manager_role:
            self.stdout.write(self.style.ERROR('未找到总经理角色（general_manager），请先创建该角色'))
            return

        # 创建开始节点
        start_node = ApprovalNode.objects.create(
            workflow=workflow,
            name='开始',
            node_type='start',
            sequence=0,
            description='开始节点'
        )
        self.stdout.write(self.style.SUCCESS('✓ 创建开始节点'))

        # 创建总经理审批节点
        manager_node = ApprovalNode.objects.create(
            workflow=workflow,
            name='总经理审批',
            node_type='approval',
            sequence=1,
            approver_type='role',
            approval_mode='single',
            is_required=True,
            can_reject=True,
            can_transfer=False,
            timeout_hours=24,
            description='总经理审批创建目标申请'
        )
        manager_node.approver_roles.add(general_manager_role)
        self.stdout.write(self.style.SUCCESS('✓ 创建总经理审批节点'))

        # 创建结束节点
        end_node = ApprovalNode.objects.create(
            workflow=workflow,
            name='结束',
            node_type='end',
            sequence=2,
            description='结束节点'
        )
        self.stdout.write(self.style.SUCCESS('✓ 创建结束节点'))

        self.stdout.write(self.style.SUCCESS('\n创建目标审批流程配置完成！'))
        self.stdout.write(f'流程代码：{workflow.code}')
        self.stdout.write(f'流程名称：{workflow.name}')
        self.stdout.write(f'审批节点：开始 -> 总经理审批 -> 结束')
