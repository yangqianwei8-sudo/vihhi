"""
P2-5: 目标统计服务

首页目标数据统计，禁止在 view 中直接写 ORM
"""
from django.utils import timezone
from django.db.models import Count, Q
from datetime import date, timedelta
from typing import Dict, Any
from ..models import StrategicGoal


def get_user_goal_stats(user) -> Dict[str, Any]:
    """
    获取用户的目标统计（个人目标）
    
    Args:
        user: User 对象
    
    Returns:
        Dict: 目标统计
            - total: 总目标数
            - in_progress: 执行中目标数
            - overdue: 逾期目标数
            - this_month: 本月需完成目标数
            - overdue_goals: 逾期目标列表（前5条）
    """
    today = timezone.now().date()
    this_month_start = today.replace(day=1)
    this_month_end = (this_month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    
    # 个人目标
    my_goals = StrategicGoal.objects.filter(level='personal', owner=user)
    
    # 总目标数
    total = my_goals.count()
    
    # 执行中目标
    in_progress = my_goals.filter(status='in_progress').count()
    
    # 逾期目标（需要立刻处理的）
    overdue_qs = my_goals.filter(
        status__in=['published', 'accepted', 'in_progress'],
        end_date__lt=today
    )
    
    # 先统计总数，再获取列表（避免切片后count只返回切片数量）
    overdue = overdue_qs.count()
    overdue_goals = overdue_qs.select_related('parent_goal', 'responsible_person').order_by('end_date')[:5]
    
    # 本月需完成目标
    this_month = my_goals.filter(
        end_date__year=today.year,
        end_date__month=today.month,
        status__in=['published', 'accepted', 'in_progress']
    ).count()
    
    return {
        'total': total,
        'in_progress': in_progress,
        'overdue': overdue,
        'this_month': this_month,
        'overdue_goals': list(overdue_goals),
    }


def get_user_collaboration_goal_stats(user) -> Dict[str, Any]:
    """
    获取用户协作的目标统计（作为参与者）
    
    Args:
        user: User 对象
    
    Returns:
        Dict: 协作目标统计
            - total: 总目标数
            - in_progress: 执行中目标数
            - overdue: 逾期目标数
            - this_month: 本月需完成目标数
    """
    today = timezone.now().date()
    this_month_start = today.replace(day=1)
    this_month_end = (this_month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    
    # 用户作为参与者的目标（排除自己负责的）
    collaboration_goals = StrategicGoal.objects.filter(participants=user).exclude(responsible_person=user)
    
    # 总目标数
    total = collaboration_goals.count()
    
    # 执行中目标
    in_progress = collaboration_goals.filter(status='in_progress').count()
    
    # 逾期目标
    overdue = collaboration_goals.filter(
        status__in=['published', 'accepted', 'in_progress'],
        end_date__lt=today
    ).count()
    
    # 本月需完成目标
    this_month = collaboration_goals.filter(
        end_date__year=today.year,
        end_date__month=today.month,
        status__in=['published', 'accepted', 'in_progress']
    ).count()
    
    return {
        'total': total,
        'in_progress': in_progress,
        'overdue': overdue,
        'this_month': this_month,
    }


def get_company_goal_stats(user) -> Dict[str, Any]:
    """
    获取公司目标统计（管理视角）
    
    Args:
        user: User 对象（用于权限检查）
    
    Returns:
        Dict: 公司目标统计
            - total: 总目标数
            - status_distribution: 状态分布
            - progress_overview: 进度概览
    """
    # 公司目标
    company_goals = StrategicGoal.objects.filter(level='company')
    
    # 总目标数
    total = company_goals.count()
    
    # 状态分布
    status_distribution = {}
    for status_code, status_label in StrategicGoal.STATUS_CHOICES:
        count = company_goals.filter(status=status_code).count()
        if count > 0:
            status_distribution[status_code] = {
                'label': status_label,
                'count': count,
                'percentage': round(count / total * 100, 1) if total > 0 else 0
            }
    
    # 进度概览（执行中目标的平均完成率）
    in_progress_goals = company_goals.filter(status='in_progress')
    avg_completion_rate = 0
    if in_progress_goals.exists():
        total_rate = sum(goal.completion_rate for goal in in_progress_goals)
        avg_completion_rate = round(total_rate / in_progress_goals.count(), 1)
    
    return {
        'total': total,
        'status_distribution': status_distribution,
        'progress_overview': {
            'in_progress_count': in_progress_goals.count(),
            'avg_completion_rate': avg_completion_rate,
        }
    }

