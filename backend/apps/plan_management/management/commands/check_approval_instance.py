"""
检查审批实例的状态
运行方式：python manage.py check_approval_instance --instance-number PLAN-20260123-0001
"""
import logging
from django.core.management.base import BaseCommand
from django.contrib.contenttypes.models import ContentType
from backend.apps.workflow_engine.models import ApprovalInstance, ApprovalRecord
from backend.apps.plan_management.models import Plan

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = '检查审批实例的状态和详细信息'

    def add_arguments(self, parser):
        parser.add_argument(
            '--instance-number',
            type=str,
            required=True,
            help='审批实例编号（如：PLAN-20260123-0001）',
        )

    def handle(self, *args, **options):
        instance_number = options['instance_number']
        
        self.stdout.write(self.style.SUCCESS(f'查找审批实例: {instance_number}'))
        
        # 查找审批实例
        try:
            instance = ApprovalInstance.objects.select_related(
                'workflow', 'applicant', 'current_node', 'content_type'
            ).get(instance_number=instance_number)
        except ApprovalInstance.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'审批实例不存在: {instance_number}'))
            self.stdout.write(self.style.WARNING('\n可能的原因：'))
            self.stdout.write(self.style.WARNING('1. 审批实例已被删除'))
            self.stdout.write(self.style.WARNING('2. 审批实例编号不正确'))
            self.stdout.write(self.style.WARNING('3. 审批实例在不同的数据库中'))
            return
        
        # 显示基本信息
        self.stdout.write(self.style.SUCCESS(f'\n✓ 找到审批实例'))
        self.stdout.write(f'  实例编号: {instance.instance_number}')
        self.stdout.write(f'  工作流: {instance.workflow.name} ({instance.workflow.code})')
        self.stdout.write(f'  状态: {instance.status}')
        self.stdout.write(f'  申请人: {instance.applicant.username} ({instance.applicant.get_full_name() or instance.applicant.username})')
        self.stdout.write(f'  申请时间: {instance.apply_time}')
        self.stdout.write(f'  当前节点: {instance.current_node.name if instance.current_node else "无"}')
        
        # 显示关联对象
        try:
            content_obj = instance.content_type.get_object_for_this_type(id=instance.object_id)
            if isinstance(content_obj, Plan):
                self.stdout.write(f'\n关联计划:')
                self.stdout.write(f'  计划编号: {content_obj.plan_number}')
                self.stdout.write(f'  计划名称: {content_obj.name}')
                self.stdout.write(f'  计划状态: {content_obj.status}')
                self.stdout.write(f'  公司ID: {content_obj.company_id if hasattr(content_obj, "company_id") else "无"}')
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'\n无法获取关联对象: {e}'))
        
        # 显示审批记录
        records = ApprovalRecord.objects.filter(instance=instance).select_related('approver', 'node').order_by('created_time')
        if records.exists():
            self.stdout.write(f'\n审批记录 ({records.count()} 条):')
            for i, record in enumerate(records, 1):
                self.stdout.write(f'  {i}. 节点: {record.node.name}')
                self.stdout.write(f'     审批人: {record.approver.username} ({record.approver.get_full_name() or record.approver.username})')
                self.stdout.write(f'     结果: {record.result}')
                self.stdout.write(f'     审批时间: {record.approval_time or "待审批"}')
                if record.comment:
                    self.stdout.write(f'     备注: {record.comment}')
        else:
            self.stdout.write(self.style.WARNING('\n⚠ 没有审批记录'))
            self.stdout.write(self.style.WARNING('这可能意味着：'))
            self.stdout.write(self.style.WARNING('1. 审批节点没有找到审批人'))
            self.stdout.write(self.style.WARNING('2. 审批记录创建失败'))
        
        # 检查为什么在审批列表中不显示
        self.stdout.write(f'\n诊断信息:')
        
        # 1. 检查状态
        if instance.status not in ['pending', 'in_progress']:
            self.stdout.write(self.style.WARNING(f'  ⚠ 状态不是 pending 或 in_progress，当前状态: {instance.status}'))
            self.stdout.write(self.style.WARNING('    审批列表只显示 pending 和 in_progress 状态的实例'))
        else:
            self.stdout.write(self.style.SUCCESS(f'  ✓ 状态正确: {instance.status}'))
        
        # 2. 检查工作流代码
        from backend.apps.plan_management.services.plan_approval import PlanApprovalService
        valid_codes = [
            PlanApprovalService.PLAN_START_WORKFLOW_CODE,
            PlanApprovalService.PLAN_CANCEL_WORKFLOW_CODE
        ]
        if instance.workflow.code not in valid_codes:
            self.stdout.write(self.style.WARNING(f'  ⚠ 工作流代码不在允许的列表中: {instance.workflow.code}'))
            self.stdout.write(self.style.WARNING(f'    允许的代码: {valid_codes}'))
        else:
            self.stdout.write(self.style.SUCCESS(f'  ✓ 工作流代码正确: {instance.workflow.code}'))
        
        # 3. 检查内容类型
        plan_content_type = ContentType.objects.get_for_model(Plan)
        if instance.content_type != plan_content_type:
            self.stdout.write(self.style.WARNING(f'  ⚠ 内容类型不匹配'))
        else:
            self.stdout.write(self.style.SUCCESS(f'  ✓ 内容类型正确'))
        
        # 4. 检查计划是否存在
        try:
            plan = Plan.objects.get(id=instance.object_id)
            self.stdout.write(self.style.SUCCESS(f'  ✓ 关联计划存在: {plan.plan_number}'))
        except Plan.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'  ✗ 关联计划不存在 (ID: {instance.object_id})'))
        
        self.stdout.write(f'\n完成！')
