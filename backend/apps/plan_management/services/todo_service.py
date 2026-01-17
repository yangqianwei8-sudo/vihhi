"""
P2-4: 待办中心服务

待办来源：
- 待接收目标/计划（published，owner=user）
- 待执行目标/计划（accepted，owner=user）
- 今日应执行计划（in_progress，today在[start_time, end_time]）
- 风险计划（逾期）

原则：
- 不存表，通过查询实现
- 所有待办必须能点进去处理
"""
from django.utils import timezone
from django.urls import reverse
from datetime import date, datetime, timedelta
from typing import List, Dict, Any
from ..models import StrategicGoal, Plan


def get_user_todos(user) -> List[Dict[str, Any]]:
    """
    获取用户的待办列表
    
    Args:
        user: User 对象
    
    Returns:
        List[Dict]: 待办列表，每个待办包含：
            - type: 待办类型（'goal_accept', 'plan_accept', 'goal_execute', 'plan_execute', 'plan_today', 'plan_risk'）
            - title: 待办标题
            - description: 待办描述
            - priority: 优先级（'high', 'medium', 'low'）
            - url: 跳转链接
            - object: 关联的对象（StrategicGoal 或 Plan）
            - created_at: 创建时间（用于排序）
    """
    todos = []
    now = timezone.now()
    today = now.date()
    
    # ========== 1. 待接收目标（published，owner=user）==========
    pending_goals = StrategicGoal.objects.filter(
        level='personal',
        status='published',
        owner=user
    ).select_related('parent_goal', 'responsible_person')
    
    for goal in pending_goals:
        todos.append({
            'type': 'goal_accept',
            'title': f'待接收目标：{goal.name}',
            'description': f'您有一个待接收的目标，请及时接收',
            'priority': 'high',
            'url': reverse('plan_pages:strategic_goal_detail', args=[goal.id]),
            'object': goal,
            'created_at': goal.published_at or goal.created_time,
        })
    
    # ========== 2. 待接收计划（published，owner=user）==========
    pending_plans = Plan.objects.filter(
        level='personal',
        status='published',
        owner=user
    ).select_related('parent_plan', 'responsible_person')
    
    for plan in pending_plans:
        todos.append({
            'type': 'plan_accept',
            'title': f'待接收计划：{plan.name}',
            'description': f'您有一个待接收的计划，请及时接收',
            'priority': 'high',
            'url': reverse('plan_pages:plan_detail', args=[plan.id]),
            'object': plan,
            'created_at': plan.published_at or plan.created_time,
        })
    
    # ========== 3. 待执行目标（accepted，owner=user）==========
    accepted_goals = StrategicGoal.objects.filter(
        level='personal',
        status='accepted',
        owner=user
    ).select_related('parent_goal', 'responsible_person')
    
    for goal in accepted_goals:
        todos.append({
            'type': 'goal_execute',
            'title': f'待执行目标：{goal.name}',
            'description': f'目标已接收，请开始执行',
            'priority': 'medium',
            'url': reverse('plan_pages:strategic_goal_detail', args=[goal.id]),
            'object': goal,
            'created_at': goal.accepted_at or goal.created_time,
        })
    
    # ========== 4. 待执行计划（accepted，owner=user）==========
    accepted_plans = Plan.objects.filter(
        level='personal',
        status='accepted',
        owner=user
    ).select_related('parent_plan', 'responsible_person')
    
    for plan in accepted_plans:
        todos.append({
            'type': 'plan_execute',
            'title': f'待执行计划：{plan.name}',
            'description': f'计划已接收，请开始执行',
            'priority': 'medium',
            'url': reverse('plan_pages:plan_detail', args=[plan.id]),
            'object': plan,
            'created_at': plan.accepted_at or plan.created_time,
        })
    
    # ========== 5. 今日应执行计划（in_progress，today在[start_time, end_time]）==========
    today_start = timezone.make_aware(datetime.combine(today, datetime.min.time()))
    today_end = timezone.make_aware(datetime.combine(today, datetime.max.time()))
    
    today_plans = Plan.objects.filter(
        level='personal',
        status='in_progress',
        owner=user,
        start_time__lte=today_end,
        end_time__gte=today_start
    ).select_related('responsible_person')
    
    for plan in today_plans:
        todos.append({
            'type': 'plan_today',
            'title': f'今日应执行：{plan.name}',
            'description': f'计划应在今天执行，请及时更新进度',
            'priority': 'high',
            'url': reverse('plan_pages:plan_execution_track', args=[plan.id]),
            'object': plan,
            'created_at': plan.start_time or plan.created_time,
        })
    
    # ========== 6. 风险计划（逾期）==========
    overdue_plans = Plan.objects.filter(
        level='personal',
        status__in=['draft', 'published', 'accepted', 'in_progress'],
        owner=user,
        end_time__lt=now
    ).select_related('responsible_person')
    
    for plan in overdue_plans:
        days_overdue = (now.date() - plan.end_time.date()).days
        todos.append({
            'type': 'plan_risk',
            'title': f'⚠️ 逾期计划：{plan.name}',
            'description': f'计划已逾期 {days_overdue} 天，请尽快处理',
            'priority': 'high',
            'url': reverse('plan_pages:plan_detail', args=[plan.id]),
            'object': plan,
            'created_at': plan.end_time,
        })
    
    # ========== 7. 风险目标（逾期）==========
    overdue_goals = StrategicGoal.objects.filter(
        level='personal',
        status__in=['published', 'accepted', 'in_progress'],
        owner=user,
        end_date__lt=today
    ).select_related('parent_goal', 'responsible_person')
    
    for goal in overdue_goals:
        days_overdue = (today - goal.end_date).days
        todos.append({
            'type': 'goal_risk',
            'title': f'⚠️ 逾期目标：{goal.name}',
            'description': f'目标已逾期 {days_overdue} 天，请尽快处理',
            'priority': 'high',
            'url': reverse('plan_pages:strategic_goal_detail', args=[goal.id]),
            'object': goal,
            'created_at': goal.end_date,
        })
    
    # ========== 排序：优先级 > 创建时间 ==========
    priority_order = {'high': 0, 'medium': 1, 'low': 2}
    todos.sort(key=lambda x: (priority_order.get(x['priority'], 2), x['created_at'] or timezone.now()))
    
    return todos


def get_user_todo_summary(user) -> Dict[str, int]:
    """
    获取用户待办汇总统计
    
    Args:
        user: User 对象
    
    Returns:
        Dict: 待办统计
            - total: 总待办数
            - pending_accept: 待接收数（目标+计划）
            - pending_execute: 待执行数（目标+计划）
            - today_plans: 今日应执行计划数
            - risk_items: 风险项数（逾期目标+计划）
    """
    todos = get_user_todos(user)
    
    summary = {
        'total': len(todos),
        'pending_accept': len([t for t in todos if t['type'] in ['goal_accept', 'plan_accept']]),
        'pending_execute': len([t for t in todos if t['type'] in ['goal_execute', 'plan_execute']]),
        'today_plans': len([t for t in todos if t['type'] == 'plan_today']),
        'risk_items': len([t for t in todos if t['type'] in ['plan_risk', 'goal_risk']]),
    }
    
    return summary

