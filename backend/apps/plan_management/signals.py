"""
计划管理模块信号处理器
监听审批流程状态变化，自动更新计划状态
"""
import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone

from backend.apps.workflow_engine.models import ApprovalInstance
from backend.apps.plan_management.models import Plan, PlanStatusLog
from backend.apps.plan_management.services.plan_approval import PlanApprovalService

logger = logging.getLogger(__name__)


@receiver(post_save, sender=ApprovalInstance)
def handle_plan_approval_status_change(sender, instance, created, **kwargs):
    """
    监听审批实例状态变化，自动更新关联的计划状态
    """
    # 只处理状态为"已通过"或"已驳回"的情况
    if instance.status not in ['approved', 'rejected']:
        return
    
    # 获取关联的业务对象
    content_type = instance.content_type
    object_id = instance.object_id
    
    try:
        # 判断对象类型并更新状态
        if content_type.model == 'plan':
            # 计划审批
            plan = Plan.objects.get(id=object_id)
            
            if instance.workflow.code == PlanApprovalService.PLAN_START_WORKFLOW_CODE:
                # 计划启动审批
                if instance.status == 'approved':
                    logger.info(f'计划启动审批通过：{plan.plan_number}')
                    # 使用服务层处理审批结果
                    PlanApprovalService.handle_approval_result(instance, plan)
                elif instance.status == 'rejected':
                    logger.info(f'计划启动审批驳回：{plan.plan_number}')
                    # 记录驳回日志
                    PlanStatusLog.objects.create(
                        plan=plan,
                        old_status=plan.status,
                        new_status=plan.status,  # 状态不变
                        changed_by=instance.applicant,
                        change_reason=f"启动审批被驳回：{instance.final_comment or '无说明'}"
                    )
            
            elif instance.workflow.code == PlanApprovalService.PLAN_CANCEL_WORKFLOW_CODE:
                # 计划取消审批
                if instance.status == 'approved':
                    logger.info(f'计划取消审批通过：{plan.plan_number}')
                    # 使用服务层处理审批结果
                    PlanApprovalService.handle_approval_result(instance, plan)
                elif instance.status == 'rejected':
                    logger.info(f'计划取消审批驳回：{plan.plan_number}')
                    # 记录驳回日志
                    PlanStatusLog.objects.create(
                        plan=plan,
                        old_status=plan.status,
                        new_status=plan.status,  # 状态不变
                        changed_by=instance.applicant,
                        change_reason=f"取消审批被驳回：{instance.final_comment or '无说明'}"
                    )
    
    except Plan.DoesNotExist:
        logger.warning(f'计划对象不存在：object_id={object_id}')
    except Exception as e:
        logger.error(f'处理计划审批状态变化失败: {str(e)}', exc_info=True)

