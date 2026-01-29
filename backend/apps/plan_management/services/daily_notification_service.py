"""
每日通知服务

提供每日通知内容生成功能（昨日战报、今日战场、风险预警）
"""
from django.utils import timezone
from django.contrib.auth import get_user_model
from datetime import date, datetime, timedelta
from typing import Dict, Any, List
import logging

from ..models import StrategicGoal, Plan, PlanProgressRecord

User = get_user_model()
logger = logging.getLogger(__name__)


def get_yesterday_achievements(user) -> Dict[str, Any]:
    """
    获取昨日战报
    
    Args:
        user: 用户对象
    
    Returns:
        Dict: 包含昨日完成的任务和提前完成的任务
    """
    try:
        now = timezone.now()
        yesterday = now.date() - timedelta(days=1)
        yesterday_start = timezone.make_aware(datetime.combine(yesterday, datetime.min.time()))
        yesterday_end = timezone.make_aware(datetime.combine(yesterday, datetime.max.time()))
        
        # 昨天已完成的任务
        completed_plans = Plan.objects.filter(
            owner=user,
            status='completed',
            completed_at__gte=yesterday_start,
            completed_at__lte=yesterday_end
        )
        
        completed_tasks = []
        early_completions = []
        
        for plan in completed_plans:
            task_info = {
                'plan_name': plan.name,
                'plan_number': plan.plan_number,
                'completed_at': plan.completed_at.isoformat() if plan.completed_at else None
            }
            completed_tasks.append(task_info)
            
            # 检查是否提前完成
            if plan.end_time and plan.completed_at:
                days_ahead = (plan.end_time.date() - plan.completed_at.date()).days
                if days_ahead > 0:
                    early_completions.append({
                        'plan_name': plan.name,
                        'plan_number': plan.plan_number,
                        'days_ahead': days_ahead
                    })
        
        return {
            'completed_tasks': completed_tasks,
            'early_completions': early_completions,
            'total_completed': len(completed_tasks),
            'total_early': len(early_completions)
        }
        
    except Exception as e:
        logger.error(f"获取昨日战报失败（用户：{user.username}）: {str(e)}", exc_info=True)
        return {
            'completed_tasks': [],
            'early_completions': [],
            'total_completed': 0,
            'total_early': 0
        }


def get_today_battlefield(user) -> Dict[str, Any]:
    """
    获取今日战场
    
    Args:
        user: 用户对象
    
    Returns:
        Dict: 包含所有截止到今天未完成的任务，高亮显示已逾期任务
    """
    try:
        now = timezone.now()
        today = now.date()
        today_end = timezone.make_aware(datetime.combine(today, datetime.max.time()))
        
        # 所有截止到今天未完成的任务
        pending_plans = Plan.objects.filter(
            owner=user,
            status__in=['draft', 'published', 'in_progress'],
            end_time__lte=today_end
        ).order_by('end_time')
        
        tasks = []
        overdue_tasks = []
        
        for plan in pending_plans:
            is_overdue = plan.end_time.date() < today
            days_overdue = (today - plan.end_time.date()).days if is_overdue else 0
            
            task_info = {
                'plan_name': plan.name,
                'plan_number': plan.plan_number,
                'status': plan.status,
                'end_time': plan.end_time.isoformat() if plan.end_time else None,
                'is_overdue': is_overdue,
                'days_overdue': days_overdue,
                'progress': float(plan.progress)
            }
            
            tasks.append(task_info)
            if is_overdue:
                overdue_tasks.append(task_info)
        
        return {
            'tasks': tasks,
            'overdue_tasks': overdue_tasks,
            'total_tasks': len(tasks),
            'total_overdue': len(overdue_tasks)
        }
        
    except Exception as e:
        logger.error(f"获取今日战场失败（用户：{user.username}）: {str(e)}", exc_info=True)
        return {
            'tasks': [],
            'overdue_tasks': [],
            'total_tasks': 0,
            'total_overdue': 0
        }


def get_risk_warnings(user) -> Dict[str, Any]:
    """
    获取风险预警
    
    Args:
        user: 用户对象
    
    Returns:
        Dict: 包含各种风险预警信息
    """
    try:
        now = timezone.now()
        today = now.date()
        three_days_later = today + timedelta(days=3)
        three_days_later_dt = timezone.make_aware(datetime.combine(three_days_later, datetime.max.time()))
        
        # 目标进度滞后数量
        lagging_goals = StrategicGoal.objects.filter(
            owner=user,
            status='in_progress'
        )
        
        lagging_count = 0
        for goal in lagging_goals:
            # 计算目标进度是否滞后（完成率低于预期）
            expected_progress = 0
            if goal.start_date and goal.end_date:
                total_days = (goal.end_date - goal.start_date).days
                elapsed_days = (today - goal.start_date).days
                if total_days > 0:
                    expected_progress = min(100, (elapsed_days / total_days) * 100)
            
            if goal.completion_rate < expected_progress - 10:  # 滞后10%以上
                lagging_count += 1
        
        # 三天内到期任务数量
        due_soon_plans = Plan.objects.filter(
            owner=user,
            status__in=['draft', 'published', 'in_progress'],
            end_time__lte=three_days_later_dt,
            end_time__gte=now
        )
        
        # 负责项目的关键路径阻塞（需要项目模块支持，这里简化处理）
        blocked_projects = []  # 占位符，需要根据项目模块实现
        
        # 下属逾期任务（上级关注）
        subordinate_overdue = []
        if hasattr(user, 'department') and user.department:
            # 查找部门成员
            department_members = User.objects.filter(
                department=user.department,
                is_active=True
            ).exclude(id=user.id)
            
            for member in department_members:
                overdue_plans = Plan.objects.filter(
                    owner=member,
                    status__in=['draft', 'published', 'in_progress'],
                    end_time__lt=now
                )
                
                if overdue_plans.exists():
                    subordinate_overdue.append({
                        'member_name': member.get_full_name() or member.username,
                        'overdue_count': overdue_plans.count()
                    })
        
        return {
            'lagging_goals_count': lagging_count,
            'due_soon_tasks_count': due_soon_plans.count(),
            'blocked_projects': blocked_projects,
            'subordinate_overdue': subordinate_overdue,
            'has_warnings': lagging_count > 0 or due_soon_plans.exists() or len(subordinate_overdue) > 0
        }
        
    except Exception as e:
        logger.error(f"获取风险预警失败（用户：{user.username}）: {str(e)}", exc_info=True)
        return {
            'lagging_goals_count': 0,
            'due_soon_tasks_count': 0,
            'blocked_projects': [],
            'subordinate_overdue': [],
            'has_warnings': False
        }


def generate_daily_notification_content(user) -> str:
    """
    生成每日通知内容
    
    Args:
        user: 用户对象
    
    Returns:
        str: 通知内容文本
    """
    try:
        content_parts = []
        
        # 昨日战报
        achievements = get_yesterday_achievements(user)
        if achievements['total_completed'] > 0:
            content_parts.append("📊 昨日战报：")
            content_parts.append(f"  • 已完成任务：{achievements['total_completed']} 项")
            if achievements['total_early'] > 0:
                content_parts.append(f"  • 提前完成：{achievements['total_early']} 项")
                for early in achievements['early_completions']:
                    content_parts.append(f"    - 《{early['plan_name']}》提前 {early['days_ahead']} 天完成，表现出色！")
            content_parts.append("")
        
        # 今日战场
        battlefield = get_today_battlefield(user)
        if battlefield['total_tasks'] > 0:
            content_parts.append("🎯 今日战场：")
            content_parts.append(f"  • 待完成任务：{battlefield['total_tasks']} 项")
            if battlefield['total_overdue'] > 0:
                content_parts.append(f"  ⚠️ 已逾期任务：{battlefield['total_overdue']} 项（需重点关注）")
                for overdue in battlefield['overdue_tasks'][:5]:  # 最多显示5个
                    content_parts.append(f"    - 《{overdue['plan_name']}》已逾期 {overdue['days_overdue']} 天")
            content_parts.append("")
        
        # 风险预警
        warnings = get_risk_warnings(user)
        if warnings['has_warnings']:
            content_parts.append("⚠️ 风险预警：")
            if warnings['lagging_goals_count'] > 0:
                content_parts.append(f"  • 您有 {warnings['lagging_goals_count']} 个目标进度已滞后，点击查看。")
            if warnings['due_soon_tasks_count'] > 0:
                content_parts.append(f"  • 您有 {warnings['due_soon_tasks_count']} 个任务即将在三天内到期。")
            if warnings['subordinate_overdue']:
                content_parts.append("  • 上级关注：")
                for sub in warnings['subordinate_overdue']:
                    content_parts.append(f"    - 您的下属 {sub['member_name']} 有 {sub['overdue_count']} 项任务已逾期，请跟进。")
        
        return "\n".join(content_parts) if content_parts else "今日暂无通知内容。"
        
    except Exception as e:
        logger.error(f"生成每日通知内容失败（用户：{user.username}）: {str(e)}", exc_info=True)
        return "生成通知内容时发生错误。"
