"""
配置发文审批流程
流程：经办人（创建人）-> 多级上级审批 -> 总经理审批
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from backend.apps.workflow_engine.models import WorkflowTemplate, ApprovalNode
from backend.apps.system_management.models import Role

User = get_user_model()


class Command(BaseCommand):
    help = '配置发文审批流程：经办人（创建人）-> 多级上级审批 -> 总经理'

    def handle(self, *args, **options):
        self.stdout.write('开始配置发文审批流程...')
        
        # 获取或创建流程模板
        workflow, created = WorkflowTemplate.objects.get_or_create(
            code='outgoing_document_approval',
            defaults={
                'name': '发文审批流程',
                'description': '发文审批流程：经办人（创建人）提交后，需要经过多级上级审批，最后总经理审批通过后才能发出',
                'category': '发文管理',
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
                self.stdout.write(self.style.WARNING('  警告：部分节点已有审批记录'))
                # 对于有记录的节点，更新配置而不是删除
                for node in nodes_with_records:
                    # 如果节点类型是 department_manager 且系统中没有该角色，更新为 creator_manager
                    if node.approver_type == 'department_manager':
                        from backend.apps.system_management.models import Role
                        dept_manager_role = Role.objects.filter(code='department_manager').first()
                        if not dept_manager_role:
                            node.approver_type = 'creator_manager'
                            if '部门经理' in node.name:
                                node.name = '多级上级审批'
                            node.description = '创建人的直接上级审批，系统会自动查找部门负责人或高级角色'
                            node.save()
                            self.stdout.write(f'  ✓ 已更新节点 "{node.name}" 的配置（department_manager -> creator_manager）')
                
                # 只删除没有审批记录的节点
                nodes_to_delete = workflow.nodes.exclude(id__in=nodes_with_records.values_list('id', flat=True))
                deleted_count = nodes_to_delete.delete()[0]
                if deleted_count > 0:
                    self.stdout.write(f'  已删除 {deleted_count} 个无记录的旧节点')
            else:
                # 删除旧节点
                workflow.nodes.all().delete()
                self.stdout.write('  已清除旧节点配置')
        
        # 获取总经理角色
        general_manager_role = Role.objects.filter(code='general_manager').first()
        
        if not general_manager_role:
            self.stdout.write(self.style.ERROR('错误：未找到总经理角色（general_manager），请先创建该角色'))
            self.stdout.write('提示：可以在系统管理-角色管理中创建角色，代码为 general_manager')
            return
        
        # 节点0：开始节点
        start_node = ApprovalNode.objects.create(
            workflow=workflow,
            name='开始',
            node_type='start',
            sequence=0,
            description='审批流程开始节点，经办人（创建人）提交发文申请'
        )
        self.stdout.write(self.style.SUCCESS(f'✓ 创建开始节点：{start_node.name}'))
        
        # 节点1：多级上级审批
        # 使用 creator_manager 类型，系统会自动找到创建人的上级进行审批
        # 如果上级还有上级，会逐级向上审批，直到没有上级或到达指定层级
        node1 = ApprovalNode.objects.create(
            workflow=workflow,
            name='多级上级审批',
            node_type='approval',
            sequence=1,
            approver_type='creator_manager',  # 创建人的上级
            approval_mode='single',  # 单人审批，逐级向上
            is_required=True,
            can_reject=True,
            can_transfer=False,
            timeout_hours=24,
            description='创建人的直接上级审批，如果上级还有上级，会逐级向上审批。审批通过后进入下一节点。'
        )
        self.stdout.write(self.style.SUCCESS(f'✓ 创建节点1：{node1.name}'))
        self.stdout.write(f'  审批人类型：创建人的上级（自动识别）')
        self.stdout.write(f'  说明：系统会自动找到创建人的直接上级进行审批')
        
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
            description='总经理最终审批发文申请，审批通过后可以发出文件'
        )
        
        # 设置总经理角色
        node2.approver_roles.add(general_manager_role)
        self.stdout.write(f'  节点2审批人：{general_manager_role.name}（角色：{general_manager_role.code}）')
        
        self.stdout.write(self.style.SUCCESS(f'✓ 创建节点2：{node2.name}'))
        
        # 节点3：结束节点
        end_node = ApprovalNode.objects.create(
            workflow=workflow,
            name='结束',
            node_type='end',
            sequence=3,
            description='审批流程结束节点，审批通过后可以发出文件'
        )
        self.stdout.write(self.style.SUCCESS(f'✓ 创建结束节点：{end_node.name}'))
        
        # 显示流程配置摘要
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('发文审批流程配置完成！'))
        self.stdout.write('='*60)
        self.stdout.write(f'流程名称：{workflow.name}')
        self.stdout.write(f'流程代码：{workflow.code}')
        self.stdout.write(f'流程状态：{workflow.get_status_display()}')
        self.stdout.write('\n审批节点：')
        for i, node in enumerate(workflow.nodes.all().order_by('sequence'), 1):
            approver_info = '未配置'
            if node.node_type == 'start':
                approver_info = '流程开始（经办人提交）'
            elif node.node_type == 'end':
                approver_info = '流程结束'
            elif node.approver_type == 'creator_manager':
                approver_info = '创建人的上级（自动识别，逐级向上）'
            elif node.approver_type == 'role' and node.approver_roles.exists():
                roles = ', '.join([r.name for r in node.approver_roles.all()])
                approver_info = f'角色：{roles}'
            
            self.stdout.write(f'  {i}. {node.name} (顺序：{node.sequence})')
            self.stdout.write(f'     节点类型：{node.get_node_type_display()}')
            self.stdout.write(f'     审批人：{approver_info}')
            if node.node_type == 'approval':
                self.stdout.write(f'     审批模式：{node.get_approval_mode_display()}')
                self.stdout.write(f'     超时时间：{node.timeout_hours or workflow.timeout_hours}小时')
                self.stdout.write(f'     可驳回：{"是" if node.can_reject else "否"}')
                self.stdout.write(f'     可转交：{"是" if node.can_transfer else "否"}')
        
        self.stdout.write('\n' + '='*60)
        self.stdout.write('流程说明：')
        self.stdout.write('1. 经办人（创建人）创建发文并提交审批')
        self.stdout.write('2. 多级上级审批：系统自动找到创建人的直接上级进行审批')
        self.stdout.write('   - 如果上级审批通过，继续向上级审批（如果有）')
        self.stdout.write('   - 直到没有上级或到达指定层级，进入下一节点')
        self.stdout.write('3. 总经理审批：总经理角色用户进行最终审批')
        self.stdout.write('4. 审批完成，发文可以发出')
        self.stdout.write('\n注意事项：')
        self.stdout.write('- 每个节点审批超时时间为24小时')
        self.stdout.write('- 审批过程中可以驳回，驳回后流程终止，需要重新提交')
        self.stdout.write('- 审批过程中可以撤回（如果流程配置允许）')
        self.stdout.write('- 多级上级审批会自动识别创建人的上级关系')
        self.stdout.write('- 确保用户设置了正确的上级关系（在用户管理中配置）')
        self.stdout.write('='*60)
        
        # 提示如何关联到发文模型
        self.stdout.write('\n' + '='*60)
        self.stdout.write('如何在业务代码中使用此流程：')
        self.stdout.write('='*60)
        self.stdout.write('''
# 在发文提交审批时，启动审批流程：

from backend.apps.workflow_engine.models import WorkflowTemplate
from backend.apps.workflow_engine.services import ApprovalEngine
from django.contrib.contenttypes.models import ContentType

# 获取流程模板
workflow = WorkflowTemplate.objects.get(code='outgoing_document_approval')

# 启动审批流程（在发文提交审批时调用）
instance = ApprovalEngine.start_approval(
    workflow=workflow,
    content_object=outgoing_document,  # OutgoingDocument实例
    applicant=request.user,            # 经办人（创建人）
    comment='提交发文审批'              # 申请说明
)

# 更新发文状态
outgoing_document.status = 'reviewing'
outgoing_document.save()
        ''')
        self.stdout.write('='*60)

