"""
计划管理模块信号处理器
监听审批流程状态变化，自动更新计划状态
监听计划状态变化，自动处理计划发布后的操作（月度、周、日计划）
监听业务操作，自动完成相关待办事项
"""
import logging
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from datetime import datetime, timedelta
from django.db.models import Q

from backend.apps.workflow_engine.models import ApprovalInstance
from backend.apps.plan_management.models import Plan, PlanStatusLog, StrategicGoal, PlanProgressRecord, GoalProgressRecord, TodoTask
from backend.apps.plan_management.services.plan_approval import PlanApprovalService
from backend.apps.plan_management.services.todo_service import mark_todo_completed

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
            
            # 【修复漏洞】自动完成相关的日计划分解待办
            try:
                _auto_complete_daily_plan_todos(instance)
            except Exception as e:
                logger.error(f'自动完成日计划分解待办失败: {str(e)}', exc_info=True)
        
        # 【修复漏洞】自动完成周计划分解待办
        if instance.plan_period == 'weekly' and instance.level == 'personal':
            try:
                _auto_complete_weekly_plan_todos(instance)
            except Exception as e:
                logger.error(f'自动完成周计划分解待办失败: {str(e)}', exc_info=True)
        
        # 【修复漏洞】自动完成计划创建待办（个人计划对齐公司计划）
        if instance.level == 'personal' and instance.parent_plan_id:
            try:
                _auto_complete_plan_creation_todos(instance)
            except Exception as e:
                logger.error(f'自动完成计划创建待办失败: {str(e)}', exc_info=True)


# ==================== 待办事项自动完成辅助函数 ====================

def _auto_complete_daily_plan_todos(plan: Plan):
    """
    自动完成日计划分解待办
    当日计划发布时，检查并自动完成相关的日计划分解待办
    """
    if not plan.start_time:
        return
    
    target_date = plan.start_time.date()
    target_start = timezone.make_aware(datetime.combine(target_date, datetime.min.time()))
    target_end = timezone.make_aware(datetime.combine(target_date, datetime.max.time()))
    
    # 查找相关的日计划分解待办
    user = plan.owner or plan.responsible_person
    if not user:
        return
    
    todos = TodoTask.objects.filter(
        user=user,
        task_type='plan_decomposition_daily',
        status__in=['pending', 'overdue']
    )
    
    for todo in todos:
        try:
            # 检查待办是否匹配目标日期
            target_date_match = False
            if todo.deadline:
                target_date_match = todo.deadline.date() == target_date
            else:
                # 尝试从标题/描述中提取日期
                from backend.apps.plan_management.services.todo_service import extract_date_from_text
                combined_text = f"{todo.title} {todo.description or ''}"
                extracted_date = extract_date_from_text(combined_text)
                if extracted_date:
                    target_date_match = extracted_date == target_date
            
            # 如果有关联计划，检查是否匹配
            if todo.related_object_type == 'plan' and todo.related_object_id:
                if str(todo.related_object_id) == str(plan.id):
                    target_date_match = True
                elif str(todo.related_object_id) == str(plan.parent_plan_id):
                    target_date_match = True
            
            # 如果匹配，自动完成待办
            if target_date_match or (plan.start_time >= target_start and plan.start_time <= target_end):
                if plan.status == 'published':
                    mark_todo_completed(todo, user=user, via='auto')
                    logger.info(f'自动完成日计划分解待办 #{todo.id}（计划 #{plan.id}）')
        except Exception as e:
            logger.warning(f'处理日计划分解待办 #{todo.id} 时出错: {str(e)}')
            continue


def _auto_complete_weekly_plan_todos(plan: Plan):
    """
    自动完成周计划分解待办
    当周计划发布时，检查并自动完成相关的周计划分解待办
    """
    if not plan.start_time:
        return
    
    plan_start_date = plan.start_time.date()
    # 计算周计划的周一
    days_since_monday = plan_start_date.weekday()
    monday = plan_start_date - timedelta(days=days_since_monday)
    sunday = monday + timedelta(days=6)
    week_start = timezone.make_aware(datetime.combine(monday, datetime.min.time()))
    week_end = timezone.make_aware(datetime.combine(sunday, datetime.max.time()))
    
    user = plan.owner or plan.responsible_person
    if not user:
        return
    
    # 查找相关的周计划分解待办
    todos = TodoTask.objects.filter(
        user=user,
        task_type='plan_decomposition_weekly',
        status__in=['pending', 'overdue']
    )
    
    for todo in todos:
        try:
            # 检查待办的截止日期是否在周计划的时间范围内
            if todo.deadline:
                deadline_date = todo.deadline.date()
                if monday <= deadline_date <= sunday:
                    if plan.status != 'draft' and plan.status != 'cancelled':
                        mark_todo_completed(todo, user=user, via='auto')
                        logger.info(f'自动完成周计划分解待办 #{todo.id}（计划 #{plan.id}）')
            else:
                # 如果没有截止日期，检查计划时间是否匹配
                if plan.start_time >= week_start and plan.start_time <= week_end:
                    if plan.status != 'draft' and plan.status != 'cancelled':
                        mark_todo_completed(todo, user=user, via='auto')
                        logger.info(f'自动完成周计划分解待办 #{todo.id}（计划 #{plan.id}）')
        except Exception as e:
            logger.warning(f'处理周计划分解待办 #{todo.id} 时出错: {str(e)}')
            continue


def _auto_complete_plan_creation_todos(plan: Plan):
    """
    自动完成计划创建待办（个人计划对齐公司计划）
    当个人计划创建时，检查并自动完成相关的计划创建待办
    """
    if not plan.parent_plan_id:
        return
    
    user = plan.owner or plan.responsible_person
    if not user:
        return
    
    # 查找相关的计划创建待办
    todos = TodoTask.objects.filter(
        user=user,
        task_type='plan_creation',
        related_object_type='plan',
        related_object_id=str(plan.parent_plan_id),
        status__in=['pending', 'overdue']
    )
    
    for todo in todos:
        try:
            # 检查是否在待办创建之后创建的计划
            if plan.created_time >= todo.created_at:
                if plan.status != 'draft' and plan.status != 'cancelled':
                    mark_todo_completed(todo, user=user, via='auto')
                    logger.info(f'自动完成计划创建待办 #{todo.id}（计划 #{plan.id}）')
        except Exception as e:
            logger.warning(f'处理计划创建待办 #{todo.id} 时出错: {str(e)}')
            continue


@receiver(post_save, sender=StrategicGoal)
def handle_goal_created(sender, instance, created, **kwargs):
    """
    【修复漏洞】监听目标创建，自动完成相关待办
    """
    if not created:
        return
    
    try:
        # 目标创建待办：如果创建了公司目标，自动完成相关待办
        if instance.level == 'company' and instance.created_by:
            todos = TodoTask.objects.filter(
                user=instance.created_by,
                task_type='goal_creation',
                status__in=['pending', 'overdue'],
                created_at__lte=instance.created_time
            )
            for todo in todos:
                try:
                    mark_todo_completed(todo, user=instance.created_by, via='auto')
                    logger.info(f'自动完成目标创建待办 #{todo.id}（目标 #{instance.id}）')
                except Exception as e:
                    logger.warning(f'处理目标创建待办 #{todo.id} 时出错: {str(e)}')
        
        # 目标分解待办：如果创建了个人目标，自动完成相关待办
        if instance.level == 'personal' and instance.parent_goal_id and instance.owner:
            todos = TodoTask.objects.filter(
                user=instance.owner,
                task_type='goal_decomposition',
                related_object_type='goal',
                related_object_id=str(instance.parent_goal_id),
                status__in=['pending', 'overdue']
            )
            for todo in todos:
                try:
                    if instance.created_time >= todo.created_at:
                        if instance.status != 'cancelled':
                            mark_todo_completed(todo, user=instance.owner, via='auto')
                            logger.info(f'自动完成目标分解待办 #{todo.id}（目标 #{instance.id}）')
                except Exception as e:
                    logger.warning(f'处理目标分解待办 #{todo.id} 时出错: {str(e)}')
    except Exception as e:
        logger.error(f'处理目标创建信号失败: {str(e)}', exc_info=True)


@receiver(post_save, sender=PlanProgressRecord)
def handle_plan_progress_record_created(sender, instance, created, **kwargs):
    """
    【修复漏洞】监听计划进度记录创建，自动完成相关待办
    """
    if not created or not instance.recorded_by:
        return
    
    try:
        todos = TodoTask.objects.filter(
            user=instance.recorded_by,
            task_type='plan_progress_update',
            related_object_type='plan',
            related_object_id=str(instance.plan_id),
            status__in=['pending', 'overdue'],
            created_at__lte=instance.recorded_time
        )
        
        for todo in todos:
            try:
                mark_todo_completed(todo, user=instance.recorded_by, via='auto')
                logger.info(f'自动完成计划进度更新待办 #{todo.id}（进度记录 #{instance.id}）')
            except Exception as e:
                logger.warning(f'处理计划进度更新待办 #{todo.id} 时出错: {str(e)}')
    except Exception as e:
        logger.error(f'处理计划进度记录信号失败: {str(e)}', exc_info=True)


@receiver(post_save, sender=GoalProgressRecord)
def handle_goal_progress_record_created(sender, instance, created, **kwargs):
    """
    【修复漏洞】监听目标进度记录创建，自动完成相关待办
    """
    if not created or not instance.recorded_by:
        return
    
    try:
        todos = TodoTask.objects.filter(
            user=instance.recorded_by,
            task_type='goal_progress_update',
            related_object_type='goal',
            related_object_id=str(instance.goal_id),
            status__in=['pending', 'overdue'],
            created_at__lte=instance.recorded_time
        )
        
        for todo in todos:
            try:
                mark_todo_completed(todo, user=instance.recorded_by, via='auto')
                logger.info(f'自动完成目标进度更新待办 #{todo.id}（进度记录 #{instance.id}）')
            except Exception as e:
                logger.warning(f'处理目标进度更新待办 #{todo.id} 时出错: {str(e)}')
    except Exception as e:
        logger.error(f'处理目标进度记录信号失败: {str(e)}', exc_info=True)

