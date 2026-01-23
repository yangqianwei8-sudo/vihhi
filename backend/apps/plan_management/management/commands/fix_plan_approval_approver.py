"""
修复计划审批流程的审批人配置
运行方式：python manage.py fix_plan_approval_approver --username 杨乾维
"""
import logging
from django.core.management.base import BaseCommand
from django.contrib.contenttypes.models import ContentType
from backend.apps.workflow_engine.models import WorkflowTemplate, ApprovalNode
from backend.apps.system_management.models import User

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = '修复计划审批流程的审批人配置，将审批节点改为指定用户'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            required=True,
            help='审批人的用户名',
        )
        parser.add_argument(
            '--workflow-code',
            type=str,
            default='plan_start_approval',
            help='审批流程代码（默认：plan_start_approval）',
        )

    def handle(self, *args, **options):
        username = options['username']
        workflow_code = options['workflow_code']
        
        self.stdout.write(self.style.SUCCESS(f'开始修复审批流程: {workflow_code}'))
        
        # 查找审批人
        try:
            approver = User.objects.get(username=username)
            self.stdout.write(self.style.SUCCESS(f'找到审批人: {approver.username} ({approver.get_full_name() or approver.username})'))
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'用户不存在: {username}'))
            return
        
        # 查找审批流程模板
        try:
            workflow = WorkflowTemplate.objects.get(code=workflow_code, status='active')
            self.stdout.write(self.style.SUCCESS(f'找到审批流程: {workflow.name}'))
        except WorkflowTemplate.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'审批流程不存在或未启用: {workflow_code}'))
            return
        
        # 查找审批节点（第一个审批节点）
        approval_nodes = workflow.nodes.filter(node_type='approval').order_by('sequence')
        if not approval_nodes.exists():
            self.stdout.write(self.style.ERROR(f'审批流程中没有审批节点'))
            return
        
        updated_count = 0
        for node in approval_nodes:
            self.stdout.write(f'\n处理节点: {node.name}')
            self.stdout.write(f'  当前审批人类型: {node.approver_type}')
            
            # 将审批人类型改为 'user'，并添加指定用户
            node.approver_type = 'user'
            node.save()
            
            # 清除现有的审批人，添加新审批人
            node.approver_users.clear()
            node.approver_users.add(approver)
            
            self.stdout.write(self.style.SUCCESS(f'  ✓ 已更新为指定用户: {approver.username}'))
            updated_count += 1
        
        self.stdout.write(self.style.SUCCESS(f'\n完成！已更新 {updated_count} 个审批节点'))
        self.stdout.write(self.style.WARNING('\n注意：'))
        self.stdout.write(self.style.WARNING('1. 审批节点已改为指定用户模式'))
        self.stdout.write(self.style.WARNING('2. 后续提交的审批将自动分配给指定的审批人'))
        self.stdout.write(self.style.WARNING('3. 如果之前提交的审批没有审批人，需要重新提交审批'))
