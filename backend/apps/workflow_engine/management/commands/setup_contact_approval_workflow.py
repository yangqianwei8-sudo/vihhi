"""
配置联系人管理审批流程
流程：申请人 -> 部门经理审批
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from backend.apps.workflow_engine.models import WorkflowTemplate, ApprovalNode
from backend.apps.system_management.models import Role

User = get_user_model()


class Command(BaseCommand):
    help = '配置联系人管理审批流程：申请人 -> 部门经理'

    def handle(self, *args, **options):
        self.stdout.write('开始配置联系人管理审批流程...')
        
        # 获取或创建流程模板
        workflow, created = WorkflowTemplate.objects.get_or_create(
            code='contact_approval',
            defaults={
                'name': '联系人管理审批流程',
                'description': '联系人创建、修改等操作的审批流程：申请人 -> 部门经理',
                'category': '客户管理',
                'status': 'active',
                'allow_withdraw': True,
                'allow_reject': True,
                'allow_transfer': False,
                'timeout_hours': 24,  # 24小时超时
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
        
        # 创建审批节点：部门经理审批
        node1 = ApprovalNode.objects.create(
            workflow=workflow,
            name='部门经理审批',
            node_type='approval',
            sequence=1,
            approver_type='department_manager',  # 使用部门经理类型
            approval_mode='single',  # 单人审批
            is_required=True,
            can_reject=True,
            can_transfer=False,
            timeout_hours=24,
            description='申请人所在部门的经理审批联系人管理操作'
        )
        
        self.stdout.write(self.style.SUCCESS(f'✓ 创建节点：{node1.name}'))
        self.stdout.write(f'  审批人类型：部门经理（自动获取申请人所在部门的经理）')
        
        # 显示流程配置摘要
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('联系人管理审批流程配置完成！'))
        self.stdout.write('='*60)
        self.stdout.write(f'流程名称：{workflow.name}')
        self.stdout.write(f'流程代码：{workflow.code}')
        self.stdout.write(f'流程状态：{workflow.get_status_display()}')
        self.stdout.write('\n审批节点：')
        for i, node in enumerate(workflow.nodes.all().order_by('sequence'), 1):
            approver_info = '未配置'
            if node.approver_type == 'department_manager':
                approver_info = '申请人所在部门的经理'
            elif node.approver_type == 'role' and node.approver_roles.exists():
                roles = ', '.join([r.name for r in node.approver_roles.all()])
                approver_info = f'角色：{roles}'
            
            self.stdout.write(f'  {i}. {node.name} (顺序：{node.sequence})')
            self.stdout.write(f'     审批人：{approver_info}')
            self.stdout.write(f'     审批模式：{node.get_approval_mode_display()}')
            self.stdout.write(f'     是否必审：{"是" if node.is_required else "否"}')
            self.stdout.write(f'     可驳回：{"是" if node.can_reject else "否"}')
            self.stdout.write(f'     超时时间：{node.timeout_hours or workflow.timeout_hours}小时')
        
        self.stdout.write('\n' + '='*60)
        self.stdout.write('流程说明：')
        self.stdout.write('1. 申请人提交联系人创建/修改申请')
        self.stdout.write('2. 申请人所在部门的经理审批（必须通过）')
        self.stdout.write('3. 审批完成，联系人信息生效')
        self.stdout.write('\n使用方法：')
        self.stdout.write('在联系人创建视图中调用：')
        self.stdout.write('  ApprovalEngine.start_approval(workflow, contact, user, comment)')
        self.stdout.write('='*60)








