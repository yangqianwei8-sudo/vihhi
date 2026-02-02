"""
配置商机审批流程
流程：申请人 -> 部门经理审批 -> 总经理审批
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from backend.apps.workflow_engine.models import WorkflowTemplate, ApprovalNode
from backend.apps.system_management.models import Role

User = get_user_model()


class Command(BaseCommand):
    help = '配置商机审批流程：申请人 -> 部门经理 -> 总经理'

    def handle(self, *args, **options):
        self.stdout.write('开始配置商机审批流程...')

        workflow, created = WorkflowTemplate.objects.get_or_create(
            code='opportunity_approval',
            defaults={
                'name': '商机审批流程',
                'description': '商机创建、重大变更等操作的审批流程',
                'category': '商机管理',
                'status': 'active',
                'allow_withdraw': True,
                'allow_reject': True,
                'allow_transfer': False,
                'timeout_hours': 24,
                'timeout_action': 'notify',
                'applicable_models': ['businessopportunity'],
                'created_by': User.objects.filter(is_superuser=True).first() or User.objects.first(),
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'✓ 创建审批流程：{workflow.name}'))
        else:
            self.stdout.write(self.style.WARNING(f'⚠ 流程已存在：{workflow.name}'))
            from backend.apps.workflow_engine.models import ApprovalRecord
            nodes_with_records = workflow.nodes.filter(records__isnull=False).distinct()
            if nodes_with_records.exists():
                nodes_to_delete = workflow.nodes.exclude(id__in=nodes_with_records.values_list('id', flat=True))
                nodes_to_delete.delete()
            else:
                workflow.nodes.all().delete()

        business_manager_role = Role.objects.filter(code='business_manager').first()
        business_team_role = Role.objects.filter(code='business_team').first()
        general_manager_role = Role.objects.filter(code='general_manager').first()
        if not general_manager_role:
            self.stdout.write(self.style.ERROR('未找到总经理角色（general_manager）'))
            return

        start_node = ApprovalNode.objects.create(
            workflow=workflow, name='开始', node_type='start', sequence=0, description='开始'
        )
        node1 = ApprovalNode.objects.create(
            workflow=workflow, name='部门经理审批', node_type='approval', sequence=1,
            approver_type='role', approval_mode='single', is_required=True, can_reject=True,
            can_transfer=False, timeout_hours=24, description='部门经理审批'
        )
        if business_manager_role:
            node1.approver_roles.add(business_manager_role)
        elif business_team_role:
            node1.approver_roles.add(business_team_role)
        else:
            node1.approver_type = 'department_manager'
            node1.save()

        node2 = ApprovalNode.objects.create(
            workflow=workflow, name='总经理审批', node_type='approval', sequence=2,
            approver_type='role', approval_mode='single', is_required=True, can_reject=True,
            can_transfer=False, timeout_hours=24, description='总经理审批'
        )
        node2.approver_roles.add(general_manager_role)

        ApprovalNode.objects.create(
            workflow=workflow, name='结束', node_type='end', sequence=3, description='结束'
        )

        self.stdout.write(self.style.SUCCESS('商机审批流程配置完成'))
        self.stdout.write(f'流程代码：{workflow.code}')
