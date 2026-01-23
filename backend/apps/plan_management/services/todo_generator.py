"""
待办事项自动生成逻辑

提供各种待办事项的自动生成函数
"""
from django.utils import timezone
from django.contrib.auth import get_user_model
from datetime import datetime, timedelta
from typing import List, Optional
import logging

from ..models import StrategicGoal, Plan
from .todo_service import create_todo_task
from ..notifications import safe_approval_notification

User = get_user_model()
logger = logging.getLogger(__name__)


def generate_goal_creation_todo(deadline: datetime = None) -> List:
    """
    生成目标创建待办（给总经理）
    
    Args:
        deadline: 截止时间，如果为None则使用默认值（当月10日9点）
    
    Returns:
        List[TodoTask]: 创建的待办列表
    """
    try:
        # 查找所有总经理
        general_managers = User.objects.filter(
            roles__code='general_manager',
            is_active=True
        ).distinct()
        
        if not general_managers.exists():
            logger.warning("未找到总经理角色用户，无法生成目标创建待办")
            return []
        
        # 如果没有指定截止时间，使用当月10日9点
        if deadline is None:
            now = timezone.now()
            deadline = now.replace(day=10, hour=9, minute=0, second=0, microsecond=0)
            # 如果今天已经超过10日，则使用下个月10日
            if now.day > 10:
                if now.month == 12:
                    deadline = deadline.replace(year=now.year + 1, month=1)
                else:
                    deadline = deadline.replace(month=now.month + 1)
        
        todos = []
        for gm in general_managers:
            try:
                todo = create_todo_task(
                    task_type='goal_creation',
                    user=gm,
                    title='【目标创建】请创建季度战略目标',
                    description=f'请在每个自然季度起始月10日9点前完成季度战略目标的创建。截止时间：{deadline.strftime("%Y-%m-%d %H:%M")}',
                    deadline=deadline,
                    auto_generated=True
                )
                todos.append(todo)
                
                # 发送系统通知
                safe_approval_notification(
                    user=gm,
                    title='【待办提醒】目标创建待办事项',
                    content=f'系统已为您生成目标创建待办事项，请在{deadline.strftime("%Y年%m月%d日 %H:%M")}前完成。',
                    object_type='todo',
                    object_id=str(todo.id),
                    event='goal_creation',
                    is_read=False
                )
                
            except Exception as e:
                logger.error(f"为总经理 {gm.username} 创建目标创建待办失败: {str(e)}", exc_info=True)
        
        logger.info(f"成功生成 {len(todos)} 个目标创建待办")
        return todos
        
    except Exception as e:
        logger.error(f"生成目标创建待办失败: {str(e)}", exc_info=True)
        return []


def generate_goal_decomposition_todo(goal: StrategicGoal) -> List:
    """
    生成目标分解待办（给员工）
    
    Args:
        goal: 公司目标对象
    
    Returns:
        List[TodoTask]: 创建的待办列表
    """
    try:
        if goal.level != 'company' or goal.status != 'published':
            logger.warning(f"目标 #{goal.id} 不是已发布的公司目标，跳过生成分解待办")
            return []
        
        # 通知对象：公司内所有活跃员工
        from django.contrib.auth.models import User
        
        recipients = User.objects.filter(is_active=True)
        # 公司隔离（如果有company字段）
        if hasattr(goal, 'company') and goal.company:
            recipients = recipients.filter(profile__company=goal.company)
        
        # 排除创建人
        recipients = recipients.exclude(id=goal.created_by_id)
        
        # 计算截止时间：自然季度起始月10日9点
        now = timezone.now()
        goal_start_month = goal.start_date.month
        
        # 判断目标所属季度
        if goal_start_month in [1, 2, 3]:
            quarter_start_month = 1
        elif goal_start_month in [4, 5, 6]:
            quarter_start_month = 4
        elif goal_start_month in [7, 8, 9]:
            quarter_start_month = 7
        else:
            quarter_start_month = 10
        
        deadline = now.replace(month=quarter_start_month, day=10, hour=9, minute=0, second=0, microsecond=0)
        # 如果目标开始日期所在季度已过，使用当前季度
        if deadline < now:
            current_month = now.month
            if current_month in [1, 2, 3]:
                quarter_start_month = 1
            elif current_month in [4, 5, 6]:
                quarter_start_month = 4
            elif current_month in [7, 8, 9]:
                quarter_start_month = 7
            else:
                quarter_start_month = 10
            deadline = now.replace(month=quarter_start_month, day=10, hour=9, minute=0, second=0, microsecond=0)
            if deadline < now:
                if quarter_start_month == 10:
                    deadline = deadline.replace(year=now.year + 1, month=1)
                else:
                    deadline = deadline.replace(month=quarter_start_month + 3)
        
        todos = []
        for recipient in recipients:
            try:
                todo = create_todo_task(
                    task_type='goal_decomposition',
                    user=recipient,
                    title=f'【目标分解】请创建个人目标对齐：{goal.name}',
                    description=f'公司目标《{goal.name}》已发布，请创建个人目标进行对齐。截止时间：{deadline.strftime("%Y-%m-%d %H:%M")}',
                    related_object_type='goal',
                    related_object_id=str(goal.id),
                    deadline=deadline,
                    auto_generated=True
                )
                todos.append(todo)
                
                # 发送系统通知
                safe_approval_notification(
                    user=recipient,
                    title='【待办提醒】目标分解待办事项',
                    content=f'公司目标《{goal.name}》已发布，请创建个人目标进行对齐。截止时间：{deadline.strftime("%Y年%m月%d日 %H:%M")}',
                    object_type='goal',
                    object_id=str(goal.id),
                    event='company_goal_published',
                    is_read=False
                )
                
            except Exception as e:
                logger.error(f"为用户 {recipient.username} 创建目标分解待办失败: {str(e)}", exc_info=True)
        
        logger.info(f"成功生成 {len(todos)} 个目标分解待办（目标 #{goal.id}）")
        return todos
        
    except Exception as e:
        logger.error(f"生成目标分解待办失败: {str(e)}", exc_info=True)
        return []


def generate_goal_progress_update_todo(goal: StrategicGoal, deadline: datetime = None) -> Optional:
    """
    生成目标进度更新待办
    
    Args:
        goal: 目标对象
        deadline: 截止时间，如果为None则使用默认值（当天下午5点）
    
    Returns:
        TodoTask实例或None
    """
    try:
        if goal.status != 'in_progress' or not goal.owner:
            return None
        
        # 如果没有指定截止时间，使用当天下午5点
        if deadline is None:
            now = timezone.now()
            deadline = now.replace(hour=17, minute=0, second=0, microsecond=0)
            # 如果已经过了5点，使用明天下午5点
            if now.hour >= 17:
                deadline = deadline + timedelta(days=1)
        
        todo = create_todo_task(
            task_type='goal_progress_update',
            user=goal.owner,
            title=f'【目标进度更新】请更新目标进度：{goal.name}',
            description=f'请更新目标《{goal.name}》的进度。截止时间：{deadline.strftime("%Y-%m-%d %H:%M")}',
            related_object_type='goal',
            related_object_id=str(goal.id),
            deadline=deadline,
            auto_generated=True
        )
        
        # 发送系统通知
        safe_approval_notification(
            user=goal.owner,
            title='【待办提醒】目标进度更新待办事项',
            content=f'请更新目标《{goal.name}》的进度。截止时间：{deadline.strftime("%Y年%m月%d日 %H:%M")}',
            object_type='goal',
            object_id=str(goal.id),
            event='goal_progress_update',
            is_read=False
        )
        
        return todo
        
    except Exception as e:
        logger.error(f"生成目标进度更新待办失败（目标 #{goal.id}）: {str(e)}", exc_info=True)
        return None


def generate_plan_creation_todo(plan_type: str = 'monthly', deadline: datetime = None) -> List:
    """
    生成计划创建待办
    
    Args:
        plan_type: 计划类型（monthly/daily）
        deadline: 截止时间
    
    Returns:
        List[TodoTask]: 创建的待办列表
    """
    try:
        if plan_type == 'monthly':
            # 月度公司计划创建待办（给总经理）
            general_managers = User.objects.filter(
                roles__code='general_manager',
                is_active=True
            ).distinct()
            
            if not general_managers.exists():
                logger.warning("未找到总经理角色用户，无法生成月度公司计划创建待办")
                return []
            
            # 如果没有指定截止时间，使用当月23日下午5点
            if deadline is None:
                now = timezone.now()
                deadline = now.replace(day=23, hour=17, minute=0, second=0, microsecond=0)
                # 如果今天已经超过23日，则使用下个月23日
                if now.day > 23:
                    if now.month == 12:
                        deadline = deadline.replace(year=now.year + 1, month=1)
                    else:
                        deadline = deadline.replace(month=now.month + 1)
            
            todos = []
            for gm in general_managers:
                try:
                    todo = create_todo_task(
                        task_type='plan_creation',
                        user=gm,
                        title='【计划创建】请创建月度公司计划',
                        description=f'请在每月23日下午5点前完成月度公司计划的创建。截止时间：{deadline.strftime("%Y-%m-%d %H:%M")}',
                        deadline=deadline,
                        auto_generated=True
                    )
                    todos.append(todo)
                    
                    # 发送系统通知
                    safe_approval_notification(
                        user=gm,
                        title='【待办提醒】月度公司计划创建待办事项',
                        content=f'系统已为您生成月度公司计划创建待办事项，请在{deadline.strftime("%Y年%m月%d日 %H:%M")}前完成。',
                        object_type='todo',
                        object_id=str(todo.id),
                        event='plan_creation',
                        is_read=False
                    )
                    
                except Exception as e:
                    logger.error(f"为总经理 {gm.username} 创建月度公司计划创建待办失败: {str(e)}", exc_info=True)
            
            logger.info(f"成功生成 {len(todos)} 个月度公司计划创建待办")
            return todos
        
        return []
        
    except Exception as e:
        logger.error(f"生成计划创建待办失败: {str(e)}", exc_info=True)
        return []


def generate_plan_decomposition_todo(plan_type: str = 'weekly', deadline: datetime = None) -> List:
    """
    生成计划分解待办（周计划/日计划）
    
    Args:
        plan_type: 计划类型（weekly/daily）
        deadline: 截止时间
    
    Returns:
        List[TodoTask]: 创建的待办列表
    """
    try:
        users = User.objects.filter(is_active=True)
        
        if plan_type == 'weekly':
            # 周计划分解待办
            # 如果没有指定截止时间，使用当天下午6点
            if deadline is None:
                now = timezone.now()
                deadline = now.replace(hour=18, minute=0, second=0, microsecond=0)
                # 如果已经过了6点，使用明天下午6点
                if now.hour >= 18:
                    deadline = deadline + timedelta(days=1)
            
            todos = []
            for user in users:
                try:
                    todo = create_todo_task(
                        task_type='plan_decomposition_weekly',
                        user=user,
                        title='【周计划分解】请创建下周工作计划',
                        description=f'请在每周五下午6点前完成下周工作计划的分解。截止时间：{deadline.strftime("%Y-%m-%d %H:%M")}',
                        deadline=deadline,
                        auto_generated=True
                    )
                    todos.append(todo)
                    
                    # 发送系统通知
                    safe_approval_notification(
                        user=user,
                        title='【待办提醒】周计划分解待办事项',
                        content=f'系统已为您生成周计划分解待办事项，请在{deadline.strftime("%Y年%m月%d日 %H:%M")}前完成。',
                        object_type='todo',
                        object_id=str(todo.id),
                        event='weekly_plan_reminder',
                        is_read=False
                    )
                    
                except Exception as e:
                    logger.error(f"为用户 {user.username} 创建周计划分解待办失败: {str(e)}", exc_info=True)
            
            logger.info(f"成功生成 {len(todos)} 个周计划分解待办")
            return todos
        
        elif plan_type == 'daily':
            # 日计划分解待办
            # 如果没有指定截止时间，使用明天上午9点
            if deadline is None:
                now = timezone.now()
                tomorrow = now + timedelta(days=1)
                deadline = tomorrow.replace(hour=9, minute=0, second=0, microsecond=0)
            
            todos = []
            for user in users:
                try:
                    todo = create_todo_task(
                        task_type='plan_decomposition_daily',
                        user=user,
                        title='【日计划分解】请创建明日工作计划',
                        description=f'请在明天上午9点前完成明日工作计划的分解。截止时间：{deadline.strftime("%Y-%m-%d %H:%M")}',
                        deadline=deadline,
                        auto_generated=True
                    )
                    todos.append(todo)
                    
                    # 发送系统通知
                    safe_approval_notification(
                        user=user,
                        title='【待办提醒】日计划分解待办事项',
                        content=f'系统已为您生成日计划分解待办事项，请在{deadline.strftime("%Y年%m月%d日 %H:%M")}前完成。',
                        object_type='todo',
                        object_id=str(todo.id),
                        event='daily_plan_reminder',
                        is_read=False
                    )
                    
                except Exception as e:
                    logger.error(f"为用户 {user.username} 创建日计划分解待办失败: {str(e)}", exc_info=True)
            
            logger.info(f"成功生成 {len(todos)} 个日计划分解待办")
            return todos
        
        return []
        
    except Exception as e:
        logger.error(f"生成计划分解待办失败: {str(e)}", exc_info=True)
        return []


def generate_plan_progress_update_todo(plan: Plan, deadline: datetime = None) -> Optional:
    """
    生成计划进度更新待办
    
    Args:
        plan: 计划对象
        deadline: 截止时间，如果为None则使用默认值（当天下午6点）
    
    Returns:
        TodoTask实例或None
    """
    try:
        if plan.status != 'in_progress' or not plan.responsible_person:
            return None
        
        # 如果没有指定截止时间，使用当天下午6点
        if deadline is None:
            now = timezone.now()
            deadline = now.replace(hour=18, minute=0, second=0, microsecond=0)
            # 如果已经过了6点，使用明天下午6点
            if now.hour >= 18:
                deadline = deadline + timedelta(days=1)
        
        todo = create_todo_task(
            task_type='plan_progress_update',
            user=plan.responsible_person,
            title=f'【计划进度更新】请更新计划进度：{plan.name}',
            description=f'请更新计划《{plan.name}》的进度。截止时间：{deadline.strftime("%Y-%m-%d %H:%M")}',
            related_object_type='plan',
            related_object_id=str(plan.id),
            deadline=deadline,
            auto_generated=True
        )
        
        # 发送系统通知
        safe_approval_notification(
            user=plan.responsible_person,
            title='【待办提醒】计划进度更新待办事项',
            content=f'请更新计划《{plan.name}》的进度。截止时间：{deadline.strftime("%Y年%m月%d日 %H:%M")}',
            object_type='plan',
            object_id=str(plan.id),
            event='plan_progress_update',
            is_read=False
        )
        
        return todo
        
    except Exception as e:
        logger.error(f"生成计划进度更新待办失败（计划 #{plan.id}）: {str(e)}", exc_info=True)
        return None


def generate_monthly_personal_plan_todos(plan: Plan) -> List:
    """
    生成月度个人计划创建待办（公司计划发布后）
    
    Args:
        plan: 公司计划对象
    
    Returns:
        List[TodoTask]: 创建的待办列表
    """
    try:
        if plan.level != 'company' or plan.status != 'published':
            logger.warning(f"计划 #{plan.id} 不是已发布的公司计划，跳过生成个人计划创建待办")
            return []
        
        # 通知对象：公司内所有活跃员工
        recipients = User.objects.filter(is_active=True)
        # 公司隔离（如果有company字段）
        if hasattr(plan, 'company') and plan.company:
            recipients = recipients.filter(profile__company=plan.company)
        
        # 排除创建人
        recipients = recipients.exclude(id=plan.created_by_id)
        
        # 计算截止时间：当月27日下午5点
        now = timezone.now()
        deadline = now.replace(day=27, hour=17, minute=0, second=0, microsecond=0)
        # 如果今天已经超过27日，则使用下个月27日
        if now.day > 27:
            if now.month == 12:
                deadline = deadline.replace(year=now.year + 1, month=1)
            else:
                deadline = deadline.replace(month=now.month + 1)
        
        todos = []
        for recipient in recipients:
            try:
                todo = create_todo_task(
                    task_type='plan_creation',
                    user=recipient,
                    title=f'【计划创建】请创建月度个人计划对齐：{plan.name}',
                    description=f'公司计划《{plan.name}》已发布，请创建月度个人计划进行对齐。截止时间：{deadline.strftime("%Y-%m-%d %H:%M")}',
                    related_object_type='plan',
                    related_object_id=str(plan.id),
                    deadline=deadline,
                    auto_generated=True
                )
                todos.append(todo)
                
                # 发送系统通知
                safe_approval_notification(
                    user=recipient,
                    title='【待办提醒】月度个人计划创建待办事项',
                    content=f'公司计划《{plan.name}》已发布，请创建月度个人计划进行对齐。截止时间：{deadline.strftime("%Y年%m月%d日 %H:%M")}',
                    object_type='plan',
                    object_id=str(plan.id),
                    event='company_plan_published',
                    is_read=False
                )
                
            except Exception as e:
                logger.error(f"为用户 {recipient.username} 创建月度个人计划创建待办失败: {str(e)}", exc_info=True)
        
        logger.info(f"成功生成 {len(todos)} 个月度个人计划创建待办（计划 #{plan.id}）")
        return todos
        
    except Exception as e:
        logger.error(f"生成月度个人计划创建待办失败: {str(e)}", exc_info=True)
        return []
