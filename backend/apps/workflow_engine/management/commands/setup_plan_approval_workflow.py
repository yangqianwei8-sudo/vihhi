"""
配置计划管理审批流程
流程：申请人 -> 部门经理审批 -> 总经理审批
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from backend.apps.workflow_engine.models import WorkflowTemplate, ApprovalNode
from backend.apps.system_management.models import Role

User = get_user_model()


class Command(BaseCommand):
    help = '配置计划管理审批流程：申请人 -> 部门经理审批 -> 总经理'

    def handle(self, *args, **options):
        self.stdout.write('开始配置计划管理审批流程...')
        
        # 获取或创建流程模板
        workflow, created = WorkflowTemplate.objects.get_or_create(
            code='plan_management_approval',
            defaults={
                'name': '计划管理审批流程',
                'description': '工作计划创建、修改等操作的审批流程，包含多级审批：部门经理 -> 总经理',
                'category': '计划管理',
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
        
        # 获取角色（尝试多个可能的角色代码）
        general_manager_role = Role.objects.filter(
            code__in=['general_manager', 'professional_engineer', 'project_manager', 'technical_manager'],
            is_active=True
        ).first()
        
        if not general_manager_role:
            self.stdout.write(self.style.WARNING('警告：未找到合适的审批角色，将使用部门经理类型作为最终审批'))
            use_role_approval = False
        else:
            use_role_approval = True
            self.stdout.write(f'使用角色：{general_manager_role.code} ({general_manager_role.name})')
        
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
        if start_node.name != '开始':
            start_node.name = '开始'
            start_node.node_type = 'start'
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
                'approval_mode': 'single',
                'is_required': True,
                'can_reject': True,
                'can_transfer': False,
                'timeout_hours': 24,
                'description': '部门经理审批计划创建申请，审核计划内容、时间安排等'
            }
        )
        if node1.name != '部门经理审批':
            node1.name = '部门经理审批'
            node1.node_type = 'approval'
            node1.approver_type = 'department_manager'
            node1.approval_mode = 'single'
            node1.is_required = True
            node1.can_reject = True
            node1.can_transfer = False
            node1.timeout_hours = 24
            node1.save()
        self.stdout.write(self.style.SUCCESS(f'✓ 创建/更新审批节点：{node1.name}'))
        
        # 节点2：最终审批（总经理或部门总监）
        if use_role_approval:
            node2_name = '最终审批'
            node2_desc = f'{general_manager_role.name}最终审批计划'
            node2, _ = ApprovalNode.objects.get_or_create(
                workflow=workflow,
                sequence=2,
                defaults={
                    'name': node2_name,
                    'node_type': 'approval',
                    'approver_type': 'role',
                    'approval_mode': 'single',
                    'is_required': True,
                    'can_reject': True,
                    'can_transfer': False,
                    'timeout_hours': 24,
                    'description': node2_desc
                }
            )
            if node2.name != node2_name:
                node2.name = node2_name
                node2.node_type = 'approval'
                node2.approver_type = 'role'
                node2.approval_mode = 'single'
                node2.is_required = True
                node2.can_reject = True
                node2.can_transfer = False
                node2.timeout_hours = 24
                node2.description = node2_desc
                node2.save()
            # 设置审批人角色
            if general_manager_role not in node2.approver_roles.all():
                node2.approver_roles.add(general_manager_role)
            self.stdout.write(self.style.SUCCESS(f'✓ 创建/更新审批节点：{node2.name}（审批人：{general_manager_role.name}）'))
        else:
            # 如果没有角色，使用部门总监类型
            node2_name = '部门总监审批'
            node2_desc = '部门总监最终审批计划'
            node2, _ = ApprovalNode.objects.get_or_create(
                workflow=workflow,
                sequence=2,
                defaults={
                    'name': node2_name,
                    'node_type': 'approval',
                    'approver_type': 'department_manager',  # 使用部门经理类型（会向上查找）
                    'approval_mode': 'single',
                    'is_required': True,
                    'can_reject': True,
                    'can_transfer': False,
                    'timeout_hours': 24,
                    'description': node2_desc
                }
            )
            if node2.name != node2_name:
                node2.name = node2_name
                node2.node_type = 'approval'
                node2.approver_type = 'department_manager'
                node2.approval_mode = 'single'
                node2.is_required = True
                node2.can_reject = True
                node2.can_transfer = False
                node2.timeout_hours = 24
                node2.description = node2_desc
                node2.save()
            self.stdout.write(self.style.SUCCESS(f'✓ 创建/更新审批节点：{node2.name}（使用部门经理类型）'))
        
        # 节点3：结束节点
        end_node, _ = ApprovalNode.objects.get_or_create(
            workflow=workflow,
            sequence=3,
            defaults={
                'name': '结束',
                'node_type': 'end',
                'description': '审批流程结束节点'
            }
        )
        if end_node.name != '结束':
            end_node.name = '结束'
            end_node.node_type = 'end'
            end_node.save()
        self.stdout.write(self.style.SUCCESS(f'✓ 创建/更新结束节点：{end_node.name}'))
        
        # 节点连接关系通过 sequence 字段自动确定，无需手动设置
        # ApprovalEngine._get_next_node() 会根据 sequence 自动查找下一个节点
        
        self.stdout.write(self.style.SUCCESS('\n✅ 计划管理审批流程配置完成！'))
        self.stdout.write(f'   流程代码：{workflow.code}')
        self.stdout.write(f'   流程名称：{workflow.name}')
        self.stdout.write(f'   流程状态：{workflow.get_status_display()}')
        self.stdout.write(f'   节点数量：{workflow.nodes.count()}')
        self.stdout.write('\n流程节点：')
        for node in workflow.nodes.order_by('sequence'):
            approver_info = ''
            if node.node_type == 'approval':
                if node.approver_type == 'role':
                    roles = node.approver_roles.all()
                    if roles:
                        approver_info = f'（审批人：{", ".join([r.name for r in roles])}）'
                    else:
                        approver_info = '（审批人：未配置）'
                elif node.approver_type == 'department_manager':
                    approver_info = '（审批人：部门经理）'
            self.stdout.write(f'   {node.sequence}. {node.name} [{node.get_node_type_display()}] {approver_info}')

