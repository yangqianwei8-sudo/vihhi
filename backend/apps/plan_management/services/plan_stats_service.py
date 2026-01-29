"""
P2-5: 计划统计服务

首页计划数据统计，禁止在 view 中直接写 ORM
"""
from django.utils import timezone
from django.db.models import Count, Avg, Q
from datetime import date, datetime, timedelta
from typing import Dict, Any
from ..models import Plan


def get_user_plan_stats(user, filter_department_id=None, filter_responsible_person_id=None, filter_start_date=None, filter_end_date=None) -> Dict[str, Any]:
    """
    获取用户的计划统计（个人计划）
    
    Args:
        user: User 对象
        filter_department_id: 筛选部门ID（可选）
        filter_responsible_person_id: 筛选负责人ID（可选）
        filter_start_date: 筛选开始日期（可选，格式：'YYYY-MM-DD'）
        filter_end_date: 筛选结束日期（可选，格式：'YYYY-MM-DD'）
    
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
    
    # 根据筛选条件决定查询逻辑
    # 如果筛选了负责人或部门，查询所有符合条件的计划（不限制owner和level）
    # 如果没有筛选，查询当前用户相关的计划（owner、responsible_person、participants）
    if filter_responsible_person_id or filter_department_id:
        # 筛选了负责人或部门，查询所有符合条件的计划（包括个人和公司级别）
        my_plans = Plan.objects.all()
        if filter_responsible_person_id:
            try:
                my_plans = my_plans.filter(responsible_person_id=filter_responsible_person_id)
            except ValueError:
                pass
        if filter_department_id:
            try:
                my_plans = my_plans.filter(responsible_department_id=filter_department_id)
            except ValueError:
                pass
    else:
        # 没有筛选，查询当前用户相关的计划（owner、responsible_person、participants）
        from django.db.models import Q
        my_plans = Plan.objects.filter(
            Q(owner=user) | Q(responsible_person=user) | Q(participants=user)
        ).distinct()
    
    # 应用日期筛选条件（使用执行时间范围：start_time 和 end_time）
    if filter_start_date:
        try:
            start_date = datetime.strptime(filter_start_date, '%Y-%m-%d').date()
            start_datetime = timezone.make_aware(datetime.combine(start_date, datetime.min.time()))
            # 筛选：结束时间 >= 筛选开始日期（计划在执行时间范围内）
            my_plans = my_plans.filter(end_time__gte=start_datetime)
        except ValueError:
            pass
    if filter_end_date:
        try:
            end_date = datetime.strptime(filter_end_date, '%Y-%m-%d').date()
            end_datetime = timezone.make_aware(datetime.combine(end_date, datetime.max.time()))
            # 筛选：开始时间 <= 筛选结束日期（计划在执行时间范围内）
            my_plans = my_plans.filter(start_time__lte=end_datetime)
        except ValueError:
            pass
    
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
    overdue_qs = my_plans.filter(
        status__in=['draft', 'published', 'in_progress'],
        end_time__lt=now
    )
    
    # 先统计总数，再获取列表（避免切片后count只返回切片数量）
    overdue = overdue_qs.count()
    overdue_plans = overdue_qs.select_related('parent_plan', 'responsible_person').order_by('end_time')[:5]
    
    return {
        'total': total,
        'in_progress': in_progress,
        'today': today_plans,
        'overdue': overdue,
        'overdue_plans': list(overdue_plans),
    }


def get_user_collaboration_plan_stats(user, filter_department_id=None, filter_responsible_person_id=None, filter_start_date=None, filter_end_date=None) -> Dict[str, Any]:
    """
    获取用户协作的计划统计（作为参与者）
    
    Args:
        user: User 对象
        filter_department_id: 筛选部门ID（可选）
        filter_responsible_person_id: 筛选负责人ID（可选）
        filter_start_date: 筛选开始日期（可选，格式：'YYYY-MM-DD'）
        filter_end_date: 筛选结束日期（可选，格式：'YYYY-MM-DD'）
    
    Returns:
        Dict: 协作计划统计
            - total: 总计划数
            - in_progress: 执行中计划数
            - today: 今日应执行计划数
            - overdue: 逾期计划数
    """
    now = timezone.now()
    today = now.date()
    today_start = timezone.make_aware(datetime.combine(today, datetime.min.time()))
    today_end = timezone.make_aware(datetime.combine(today, datetime.max.time()))
    
    # 根据筛选条件决定查询逻辑
    # 如果筛选了负责人或部门，查询所有符合条件的计划（不限制参与者）
    # 如果没有筛选，查询当前用户作为参与者的计划（排除自己负责的）
    if filter_responsible_person_id or filter_department_id:
        # 筛选了负责人或部门，查询所有符合条件的计划
        collaboration_plans = Plan.objects.all()
        if filter_responsible_person_id:
            try:
                collaboration_plans = collaboration_plans.filter(responsible_person_id=filter_responsible_person_id)
            except ValueError:
                pass
        if filter_department_id:
            try:
                collaboration_plans = collaboration_plans.filter(responsible_department_id=filter_department_id)
            except ValueError:
                pass
    else:
        # 没有筛选，查询当前用户作为参与者的计划（排除自己负责的）
        collaboration_plans = Plan.objects.filter(participants=user).exclude(responsible_person=user)
    
    # 应用日期筛选条件（使用执行时间范围：start_time 和 end_time）
    if filter_start_date:
        try:
            start_date = datetime.strptime(filter_start_date, '%Y-%m-%d').date()
            start_datetime = timezone.make_aware(datetime.combine(start_date, datetime.min.time()))
            # 筛选：结束时间 >= 筛选开始日期（计划在执行时间范围内）
            collaboration_plans = collaboration_plans.filter(end_time__gte=start_datetime)
        except ValueError:
            pass
    if filter_end_date:
        try:
            end_date = datetime.strptime(filter_end_date, '%Y-%m-%d').date()
            end_datetime = timezone.make_aware(datetime.combine(end_date, datetime.max.time()))
            # 筛选：开始时间 <= 筛选结束日期（计划在执行时间范围内）
            collaboration_plans = collaboration_plans.filter(start_time__lte=end_datetime)
        except ValueError:
            pass
    
    # 总计划数
    total = collaboration_plans.count()
    
    # 执行中计划
    in_progress = collaboration_plans.filter(status='in_progress').count()
    
    # 今日应执行计划
    today_plans = collaboration_plans.filter(
        status='in_progress',
        start_time__lte=today_end,
        end_time__gte=today_start
    ).count()
    
    # 逾期计划
    overdue = collaboration_plans.filter(
        status__in=['draft', 'published', 'in_progress'],
        end_time__lt=now
    ).count()
    
    return {
        'total': total,
        'in_progress': in_progress,
        'today': today_plans,
        'overdue': overdue,
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
        status__in=['draft', 'published', 'in_progress'],
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

