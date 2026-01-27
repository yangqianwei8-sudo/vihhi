"""
P2-5: 风险查询服务

首页风险数据查询，禁止在 view 中直接写 ORM
"""
from django.utils import timezone
from django.urls import reverse
from datetime import date, datetime
from typing import List, Dict, Any, Optional
from django.contrib.auth import get_user_model
from ..models import StrategicGoal, Plan

User = get_user_model()


def _build_risk_item(risk_type, obj, days_overdue, status):
    """构建风险项字典的辅助函数"""
    status_weight = {
        'in_progress': 100,
        'accepted': 50,
        'published': 10,
        'draft': 5,
    }.get(status, 0)
    
    priority_score = days_overdue * 1000 + status_weight
    
    if risk_type == 'goal_risk':
        return {
            'type': 'goal_risk',
            'title': f'⚠️ 逾期目标：{obj.name}',
            'description': f'目标已逾期 {days_overdue} 天，请尽快处理',
            'priority': 'high',
            'url': reverse('plan_pages:strategic_goal_detail', args=[obj.id]),
            'object': obj,
            'days_overdue': days_overdue,
            'status': status,
            '_priority_score': priority_score,
        }
    else:  # plan_risk
        return {
            'type': 'plan_risk',
            'title': f'⚠️ 逾期计划：{obj.name}',
            'description': f'计划已逾期 {days_overdue} 天，请尽快处理',
            'priority': 'high',
            'url': reverse('plan_pages:plan_detail', args=[obj.id]),
            'object': obj,
            'days_overdue': days_overdue,
            'status': status,
            '_priority_score': priority_score,
        }


def get_user_risk_items(user, limit=5, filter_department_id=None, filter_responsible_person_id=None, filter_start_date=None, filter_end_date=None) -> List[Dict[str, Any]]:
    """
    获取用户的风险项（需要立刻处理的）
    
    P2-5 风险展示规则：
    - 只展示"需要人立刻处理的"
    - 不展示历史风险
    - 不展示已完成风险
    - 排序优先级：逾期天数多 > 执行中 > 已接收 > 已发布
    
    Args:
        user: User 对象
        limit: 返回数量限制，默认5条
        filter_department_id: 筛选部门ID（可选）
        filter_responsible_person_id: 筛选负责人ID（可选）
        filter_start_date: 筛选开始日期（可选，格式：'YYYY-MM-DD'）
        filter_end_date: 筛选结束日期（可选，格式：'YYYY-MM-DD'）
    
    Returns:
        List[Dict]: 风险项列表
            - type: 'goal_risk' | 'plan_risk'
            - title: 风险标题
            - description: 风险描述
            - priority: 优先级（'high'）
            - url: 跳转链接
            - object: 关联的对象
            - days_overdue: 逾期天数
            - status: 状态
    """
    now = timezone.now()
    today = now.date()
    risk_items = []
    
    # 辅助函数：应用筛选条件到查询集
    def apply_filters(qs, model_type='plan'):
        if filter_department_id:
            try:
                if model_type == 'plan':
                    qs = qs.filter(responsible_department_id=filter_department_id)
                elif model_type == 'goal':
                    qs = qs.filter(responsible_department_id=filter_department_id)
            except ValueError:
                pass
        if filter_responsible_person_id:
            try:
                if model_type == 'plan':
                    qs = qs.filter(responsible_person_id=filter_responsible_person_id)
                elif model_type == 'goal':
                    qs = qs.filter(responsible_person_id=filter_responsible_person_id)
            except ValueError:
                pass
        if filter_start_date:
            try:
                start_date = datetime.strptime(filter_start_date, '%Y-%m-%d').date()
                qs = qs.filter(created_time__gte=start_date)
            except ValueError:
                pass
        if filter_end_date:
            try:
                end_date = datetime.strptime(filter_end_date, '%Y-%m-%d').date()
                end_datetime = datetime.combine(end_date, datetime.max.time())
                qs = qs.filter(created_time__lte=end_datetime)
            except ValueError:
                pass
        return qs
    
    # ========== 逾期目标（需要立刻处理的）==========
    # 根据筛选条件决定查询逻辑
    if filter_responsible_person_id or filter_department_id:
        # 筛选了负责人或部门，查询所有符合条件的目标
        overdue_goals = StrategicGoal.objects.filter(
            level='personal',
            status__in=['published', 'accepted', 'in_progress'],
            end_date__lt=today
        ).select_related('parent_goal', 'responsible_person')
        overdue_goals = apply_filters(overdue_goals, 'goal')
    else:
        # 没有筛选，查询当前用户拥有的个人目标
        overdue_goals = StrategicGoal.objects.filter(
            level='personal',
            owner=user,
            status__in=['published', 'accepted', 'in_progress'],
            end_date__lt=today
        ).select_related('parent_goal', 'responsible_person')
    
    for goal in overdue_goals:
        days_overdue = (today - goal.end_date).days
        risk_items.append(_build_risk_item('goal_risk', goal, days_overdue, goal.status))
    
    # ========== 逾期计划（需要立刻处理的）==========
    # 根据筛选条件决定查询逻辑
    if filter_responsible_person_id or filter_department_id:
        # 筛选了负责人或部门，查询所有符合条件的计划
        overdue_plans = Plan.objects.filter(
            level='personal',
            status__in=['draft', 'published', 'accepted', 'in_progress'],
            end_time__lt=now
        ).select_related('parent_plan', 'responsible_person')
        overdue_plans = apply_filters(overdue_plans, 'plan')
    else:
        # 没有筛选，查询当前用户拥有的个人计划
        overdue_plans = Plan.objects.filter(
            level='personal',
            owner=user,
            status__in=['draft', 'published', 'accepted', 'in_progress'],
            end_time__lt=now
        ).select_related('parent_plan', 'responsible_person')
    
    for plan in overdue_plans:
        days_overdue = (today - plan.end_time.date()).days
        risk_items.append(_build_risk_item('plan_risk', plan, days_overdue, plan.status))
    
    # ========== 排序：优先级分数降序 ==========
    risk_items.sort(key=lambda x: x['_priority_score'], reverse=True)
    
    # 移除内部排序字段
    for item in risk_items:
        item.pop('_priority_score', None)
    
    return risk_items[:limit]


def get_responsible_risk_items(responsible_user, limit=5, filter_department_id=None, filter_responsible_person_id=None, filter_start_date=None, filter_end_date=None) -> List[Dict[str, Any]]:
    """
    获取指定负责人负责的风险项
    
    Args:
        responsible_user: 负责人User对象
        limit: 返回数量限制，默认5条
        filter_department_id: 筛选部门ID（可选）
        filter_responsible_person_id: 筛选负责人ID（可选）
        filter_start_date: 筛选开始日期（可选，格式：'YYYY-MM-DD'）
        filter_end_date: 筛选结束日期（可选，格式：'YYYY-MM-DD'）
    
    Returns:
        List[Dict]: 风险项列表
    """
    now = timezone.now()
    today = now.date()
    risk_items = []
    
    # 如果筛选了负责人，但当前负责人不匹配，返回空列表
    if filter_responsible_person_id:
        try:
            if str(responsible_user.id) != str(filter_responsible_person_id):
                return []
        except (ValueError, AttributeError):
            pass
    
    # 辅助函数：应用筛选条件到查询集
    def apply_filters(qs, model_type='plan'):
        if filter_department_id:
            try:
                if model_type == 'plan':
                    qs = qs.filter(responsible_department_id=filter_department_id)
                elif model_type == 'goal':
                    qs = qs.filter(responsible_department_id=filter_department_id)
            except ValueError:
                pass
        if filter_responsible_person_id:
            try:
                if model_type == 'plan':
                    qs = qs.filter(responsible_person_id=filter_responsible_person_id)
                elif model_type == 'goal':
                    qs = qs.filter(responsible_person_id=filter_responsible_person_id)
            except ValueError:
                pass
        if filter_start_date:
            try:
                start_date = datetime.strptime(filter_start_date, '%Y-%m-%d').date()
                qs = qs.filter(created_time__gte=start_date)
            except ValueError:
                pass
        if filter_end_date:
            try:
                end_date = datetime.strptime(filter_end_date, '%Y-%m-%d').date()
                end_datetime = datetime.combine(end_date, datetime.max.time())
                qs = qs.filter(created_time__lte=end_datetime)
            except ValueError:
                pass
        return qs
    
    # ========== 逾期目标（负责人负责的）==========
    overdue_goals = StrategicGoal.objects.filter(
        responsible_person=responsible_user,
        status__in=['published', 'accepted', 'in_progress'],
        end_date__lt=today
    ).select_related('parent_goal', 'responsible_person', 'owner')
    overdue_goals = apply_filters(overdue_goals, 'goal')
    
    for goal in overdue_goals:
        days_overdue = (today - goal.end_date).days
        risk_items.append(_build_risk_item('goal_risk', goal, days_overdue, goal.status))
    
    # ========== 逾期计划（负责人负责的）==========
    overdue_plans = Plan.objects.filter(
        responsible_person=responsible_user,
        status__in=['draft', 'published', 'accepted', 'in_progress'],
        end_time__lt=now
    ).select_related('parent_plan', 'responsible_person', 'owner')
    overdue_plans = apply_filters(overdue_plans, 'plan')
    
    for plan in overdue_plans:
        days_overdue = (today - plan.end_time.date()).days
        risk_items.append(_build_risk_item('plan_risk', plan, days_overdue, plan.status))
    
    # ========== 排序：优先级分数降序 ==========
    risk_items.sort(key=lambda x: x['_priority_score'], reverse=True)
    
    # 移除内部排序字段
    for item in risk_items:
        item.pop('_priority_score', None)
    
    return risk_items[:limit]


def get_subordinates_risk_items(subordinates, limit=5, filter_department_id=None, filter_responsible_person_id=None, filter_start_date=None, filter_end_date=None) -> List[Dict[str, Any]]:
    """
    获取下属负责的风险项
    
    Args:
        subordinates: 下属用户QuerySet或列表
        limit: 返回数量限制，默认5条
        filter_department_id: 筛选部门ID（可选）
        filter_responsible_person_id: 筛选负责人ID（可选）
        filter_start_date: 筛选开始日期（可选，格式：'YYYY-MM-DD'）
        filter_end_date: 筛选结束日期（可选，格式：'YYYY-MM-DD'）
    
    Returns:
        List[Dict]: 风险项列表
    """
    now = timezone.now()
    today = now.date()
    risk_items = []
    
    if not subordinates.exists() if hasattr(subordinates, 'exists') else not subordinates:
        return []
    
    # 如果筛选了负责人，只包含该负责人的风险项
    if filter_responsible_person_id:
        try:
            subordinates = subordinates.filter(id=filter_responsible_person_id)
            if not subordinates.exists():
                return []
        except (ValueError, AttributeError):
            pass
    
    # 辅助函数：应用筛选条件到查询集
    def apply_filters(qs, model_type='plan'):
        if filter_department_id:
            try:
                if model_type == 'plan':
                    qs = qs.filter(responsible_department_id=filter_department_id)
                elif model_type == 'goal':
                    qs = qs.filter(responsible_department_id=filter_department_id)
            except ValueError:
                pass
        if filter_responsible_person_id:
            try:
                if model_type == 'plan':
                    qs = qs.filter(responsible_person_id=filter_responsible_person_id)
                elif model_type == 'goal':
                    qs = qs.filter(responsible_person_id=filter_responsible_person_id)
            except ValueError:
                pass
        if filter_start_date:
            try:
                start_date = datetime.strptime(filter_start_date, '%Y-%m-%d').date()
                qs = qs.filter(created_time__gte=start_date)
            except ValueError:
                pass
        if filter_end_date:
            try:
                end_date = datetime.strptime(filter_end_date, '%Y-%m-%d').date()
                end_datetime = datetime.combine(end_date, datetime.max.time())
                qs = qs.filter(created_time__lte=end_datetime)
            except ValueError:
                pass
        return qs
    
    # ========== 逾期目标（下属负责的）==========
    overdue_goals = StrategicGoal.objects.filter(
        responsible_person__in=subordinates,
        status__in=['published', 'accepted', 'in_progress'],
        end_date__lt=today
    ).select_related('parent_goal', 'responsible_person', 'owner')
    overdue_goals = apply_filters(overdue_goals, 'goal')
    
    for goal in overdue_goals:
        days_overdue = (today - goal.end_date).days
        risk_items.append(_build_risk_item('goal_risk', goal, days_overdue, goal.status))
    
    # ========== 逾期计划（下属负责的）==========
    overdue_plans = Plan.objects.filter(
        responsible_person__in=subordinates,
        status__in=['draft', 'published', 'accepted', 'in_progress'],
        end_time__lt=now
    ).select_related('parent_plan', 'responsible_person', 'owner')
    overdue_plans = apply_filters(overdue_plans, 'plan')
    
    for plan in overdue_plans:
        days_overdue = (today - plan.end_time.date()).days
        risk_items.append(_build_risk_item('plan_risk', plan, days_overdue, plan.status))
    
    # ========== 排序：优先级分数降序 ==========
    risk_items.sort(key=lambda x: x['_priority_score'], reverse=True)
    
    # 移除内部排序字段
    for item in risk_items:
        item.pop('_priority_score', None)
    
    return risk_items[:limit]

