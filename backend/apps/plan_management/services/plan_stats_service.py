"""
P2-5: 计划统计服务

首页计划数据统计，禁止在 view 中直接写 ORM
"""
from django.utils import timezone
from django.db.models import Count, Avg, Q
from datetime import date, datetime, timedelta
from typing import Dict, Any
from ..models import Plan


def get_user_plan_stats(user) -> Dict[str, Any]:
    """
    获取用户的计划统计（个人计划）
    
    Args:
        user: User 对象
    
    Returns:
        Dict: 计划统计
            - total: 总计划数
            - in_progress: 执行中计划数
            - today: 今日应执行计划数
            - overdue: 逾期计划数
            - overdue_plans: 逾期计划列表（前5条）
    """
    now = timezone.now()
    today = now.date()
    today_start = timezone.make_aware(datetime.combine(today, datetime.min.time()))
    today_end = timezone.make_aware(datetime.combine(today, datetime.max.time()))
    
    # 个人计划
    my_plans = Plan.objects.filter(level='personal', owner=user)
    
    # 总计划数
    total = my_plans.count()
    
    # 执行中计划
    in_progress = my_plans.filter(status='in_progress').count()
    
    # 今日应执行计划
    today_plans = my_plans.filter(
        status='in_progress',
        start_time__lte=today_end,
        end_time__gte=today_start
    ).count()
    
    # 逾期计划（需要立刻处理的）
    overdue_plans = my_plans.filter(
        status__in=['draft', 'published', 'accepted', 'in_progress'],
        end_time__lt=now
    ).select_related('parent_plan', 'responsible_person').order_by('end_time')[:5]
    
    overdue = overdue_plans.count()
    
    return {
        'total': total,
        'in_progress': in_progress,
        'today': today_plans,
        'overdue': overdue,
        'overdue_plans': list(overdue_plans),
    }


def get_company_plan_stats(user) -> Dict[str, Any]:
    """
    获取公司计划统计（管理视角）
    
    Args:
        user: User 对象（用于权限检查）
    
    Returns:
        Dict: 公司计划统计
            - total: 总计划数
            - status_distribution: 状态分布
            - overdue_trend: 逾期趋势（简单统计）
    """
    # 公司计划
    company_plans = Plan.objects.filter(level='company')
    
    # 总计划数
    total = company_plans.count()
    
    # 状态分布
    status_distribution = {}
    for status_code, status_label in Plan.STATUS_CHOICES:
        count = company_plans.filter(status=status_code).count()
        if count > 0:
            status_distribution[status_code] = {
                'label': status_label,
                'count': count,
                'percentage': round(count / total * 100, 1) if total > 0 else 0
            }
    
    # 逾期趋势（简单统计）
    now = timezone.now()
    overdue_total = company_plans.filter(
        status__in=['draft', 'published', 'accepted', 'in_progress'],
        end_time__lt=now
    ).count()
    
    return {
        'total': total,
        'status_distribution': status_distribution,
        'overdue_trend': {
            'overdue_total': overdue_total,
            'overdue_percentage': round(overdue_total / total * 100, 1) if total > 0 else 0
        }
    }

