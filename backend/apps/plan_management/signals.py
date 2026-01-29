"""
计划管理模块信号处理器
监听审批流程状态变化，自动更新计划状态
监听计划状态变化，自动处理计划发布后的操作（月度、周、日计划）
"""
import logging
from django.db.models.signals import post_save, pre_save
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


# 用于跟踪计划状态变化
_plan_status_cache = {}


@receiver(pre_save, sender=Plan)
def cache_plan_status(sender, instance, **kwargs):
    """缓存计划状态，用于检测状态变化"""
    if instance.pk:
        try:
            old_instance = Plan.objects.get(pk=instance.pk)
            _plan_status_cache[instance.pk] = old_instance.status
        except Plan.DoesNotExist:
            pass


@receiver(post_save, sender=Plan)
def handle_plan_status_change(sender, instance, created, **kwargs):
    """
    监听计划状态变化，处理计划发布后的操作
    
    当月度公司计划状态变为 published 时：
    1. 自动为员工生成月度个人计划创建待办
    2. 计划自动推送至"月计划"卡片（通过计划管理首页显示）
    
    当周计划（个人计划）状态变为 published 时：
    1. 计划自动推送至"周计划"卡片（通过计划管理首页显示）
    
    当日计划（个人计划）状态变为 published 时：
    1. 计划自动推送至"日计划"卡片（通过计划管理首页显示）
    """
    if created:
        # 新建计划，不需要处理（新建时状态可能是 published，但不需要触发通知）
        return
    
    # 检查状态是否从非 published 变为 published
    old_status = _plan_status_cache.get(instance.pk)
    
    # 如果缓存中没有旧状态，说明可能是第一次保存，不需要处理
    if old_status is None:
        return
    
    # 清除缓存
    _plan_status_cache.pop(instance.pk, None)
    
    # 只处理状态从非 published 变为 published 的情况
    if instance.status == 'published' and old_status != 'published':
        # 检查是否是月度公司计划
        if instance.plan_period == 'monthly' and instance.level == 'company':
            logger.info(f'月度公司计划已发布：{instance.plan_number} - {instance.name}')
            
            # 自动为员工生成月度个人计划创建待办
            try:
                from backend.apps.plan_management.notifications import notify_company_plan_published
                notify_company_plan_published(instance)
                logger.info(f'已为员工生成月度个人计划创建待办（计划 #{instance.id}）')
            except Exception as e:
                logger.error(f'生成月度个人计划创建待办失败: {str(e)}', exc_info=True)
            
            # 计划自动推送至"月计划"卡片（通过计划管理首页的显示逻辑自动实现）
            logger.info(f'月度计划已推送至"月计划"卡片（计划 #{instance.id}）')
        
        # 检查是否是周计划（个人计划）
        elif instance.plan_period == 'weekly' and instance.level == 'personal':
            logger.info(f'周计划已发布：{instance.plan_number} - {instance.name}')
            
            # 周计划自动推送至"周计划"卡片（通过计划管理首页的显示逻辑自动实现）
            logger.info(f'周计划已推送至"周计划"卡片（计划 #{instance.id}）')
        
        # 检查是否是日计划（个人计划）
        elif instance.plan_period == 'daily' and instance.level == 'personal':
            logger.info(f'日计划已发布：{instance.plan_number} - {instance.name}')
            
            # 日计划自动推送至"日计划"卡片（通过计划管理首页的显示逻辑自动实现）
            logger.info(f'日计划已推送至"日计划"卡片（计划 #{instance.id}）')

