"""
配置客户关系等级升级审批流程
流程：申请人 -> 部门经理审批 -> 总经理审批
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from backend.apps.workflow_engine.models import WorkflowTemplate, ApprovalNode
from backend.apps.system_management.models import Role

User = get_user_model()


class Command(BaseCommand):
    help = '配置客户关系等级升级审批流程：申请人 -> 部门经理审批 -> 总经理审批'

    def handle(self, *args, **options):
        self.stdout.write('开始配置客户关系等级升级审批流程...')
        
        # 获取或创建流程模板
        workflow, created = WorkflowTemplate.objects.get_or_create(
            code='customer_relationship_upgrade_approval',
            defaults={
                'name': '客户关系等级升级审批流程',
                'description': '客户关系等级升级审批流程，当关系等级升级到"合作意向"、"合作认可"或"外部合伙人"时需要审批',
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
        
        # 节点1：部门经理审批
        # 注意：根据需求，部门经理应该是申请人所在部门的部门经理
        # 这里使用 department_manager 类型，系统会自动获取申请人所在部门的部门经理
        node1 = ApprovalNode.objects.create(
            workflow=workflow,
            name='部门经理审批',
            node_type='approval',
            sequence=1,
            approver_type='department_manager',  # 使用部门经理类型，自动获取申请人所在部门的部门经理
            approval_mode='single',  # 单人审批
            is_required=True,
            can_reject=True,
            can_transfer=False,
            timeout_hours=24,
            description='部门经理审批关系等级升级申请（自动获取申请人所在部门的部门经理）'
        )
        
        self.stdout.write(self.style.SUCCESS(f'✓ 创建节点1：{node1.name}（审批人：申请人所在部门的部门经理）'))
        
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
            description='总经理最终审批关系等级升级'
        )
        
        # 设置总经理角色
        node2.approver_roles.add(general_manager_role)
        self.stdout.write(f'  节点2审批人：{general_manager_role.name}')
        
        self.stdout.write(self.style.SUCCESS(f'✓ 创建节点2：{node2.name}'))
        
        # 显示流程配置摘要
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('客户关系等级升级审批流程配置完成！'))
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
                approver_info = '申请人所在部门的部门经理（自动获取）'
            
            self.stdout.write(f'  {i}. {node.name} (顺序：{node.sequence})')
            self.stdout.write(f'     审批人：{approver_info}')
            self.stdout.write(f'     审批模式：{node.get_approval_mode_display()}')
            self.stdout.write(f'     超时时间：{node.timeout_hours or workflow.timeout_hours}小时')
        
        self.stdout.write('\n' + '='*60)
        self.stdout.write('流程说明：')
        self.stdout.write('1. 申请人提交关系等级升级申请')
        self.stdout.write('2. 部门经理审批（申请人所在部门的部门经理，必须通过）')
        self.stdout.write('3. 总经理审批（必须通过）')
        self.stdout.write('4. 审批完成，关系等级升级生效')
        self.stdout.write('\n注意：')
        self.stdout.write('- 关系等级升级到"合作意向"、"合作认可"或"外部合伙人"时需要审批')
        self.stdout.write('- 关系等级升级到"需求沟通"时无需审批，直接生效')
        self.stdout.write('='*60)

