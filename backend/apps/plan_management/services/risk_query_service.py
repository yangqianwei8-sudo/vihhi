"""
P2-5: 风险查询服务

首页风险数据查询，禁止在 view 中直接写 ORM
"""
from django.utils import timezone
from django.urls import reverse
from datetime import date, datetime
from typing import List, Dict, Any, Optional
from django.contrib.auth import get_user_model
from ..models import StrategicGoal, Plan, GoalProgressRecord, PlanProgressRecord

User = get_user_model()


# ========== 进度计算辅助函数 ==========

def _get_goal_actual_progress(goal):
    """
    从 GoalProgressRecord 获取目标的实际进度（最新记录的完成率）
    
    Args:
        goal: StrategicGoal 对象
    
    Returns:
        float: 实际进度（0-100）
    """
    latest_record = goal.progress_records.first()
    if latest_record:
        return float(latest_record.completion_rate)
    return 0.0


def _get_plan_actual_progress(plan):
    """
    从 PlanProgressRecord 获取计划的实际进度（最新记录的进度，如果没有则使用 plan.progress）
    
    Args:
        plan: Plan 对象
    
    Returns:
        float: 实际进度（0-100）
    """
    latest_record = plan.progress_records.first()
    if latest_record:
        return float(latest_record.progress)
    return float(plan.progress or 0)


def _calculate_time_progress_goal(goal, today):
    """
    计算目标的时间进度
    
    公式：时间进度 = (当前日期 - 开始日期) / (结束日期 - 开始日期) * 100
    
    Args:
        goal: StrategicGoal 对象
        today: 当前日期（date对象）
    
    Returns:
        float: 时间进度（0-100）
    """
    if not goal.start_date or not goal.end_date:
        return 0.0
    total_days = (goal.end_date - goal.start_date).days
    if total_days <= 0:
        return 0.0
    elapsed_days = (today - goal.start_date).days
    time_progress = (elapsed_days / total_days) * 100
    return min(100.0, max(0.0, time_progress))


def _calculate_time_progress_plan(plan, now):
    """
    计算计划的时间进度
    
    公式：时间进度 = (当前时间 - 开始时间) / (结束时间 - 开始时间) * 100
    
    Args:
        plan: Plan 对象
        now: 当前时间（datetime对象）
    
    Returns:
        float: 时间进度（0-100）
    """
    if not plan.start_time or not plan.end_time:
        return 0.0
    total_seconds = (plan.end_time - plan.start_time).total_seconds()
    if total_seconds <= 0:
        return 0.0
    elapsed_seconds = (now - plan.start_time).total_seconds()
    time_progress = (elapsed_seconds / total_seconds) * 100
    return min(100.0, max(0.0, time_progress))


def _is_progress_behind_goal(goal, today):
    """
    判断目标是否进度落后
    
    判定条件：实际进度/时间进度 < 1.0
    
    Args:
        goal: StrategicGoal 对象
        today: 当前日期（date对象）
    
    Returns:
        bool: True表示进度落后，False表示进度正常或还未开始
    """
    actual_progress = _get_goal_actual_progress(goal)
    time_progress = _calculate_time_progress_goal(goal, today)
    
    # 如果时间进度 <= 0（还未开始），不显示风险
    if time_progress <= 0:
        return False
    
    # 如果时间进度 > 0，计算进度比例
    progress_ratio = actual_progress / time_progress if time_progress > 0 else 0
    return progress_ratio < 1.0


def _is_progress_behind_plan(plan, now):
    """
    判断计划是否进度落后
    
    判定条件：实际进度/时间进度 < 1.0
    
    Args:
        plan: Plan 对象
        now: 当前时间（datetime对象）
    
    Returns:
        bool: True表示进度落后，False表示进度正常或还未开始
    """
    actual_progress = _get_plan_actual_progress(plan)
    time_progress = _calculate_time_progress_plan(plan, now)
    
    # 如果时间进度 <= 0（还未开始），不显示风险
    if time_progress <= 0:
        return False
    
    # 如果时间进度 > 0，计算进度比例
    progress_ratio = actual_progress / time_progress if time_progress > 0 else 0
    return progress_ratio < 1.0


def _build_risk_item(risk_type, obj, actual_progress, time_progress, status):
    """
    构建风险项字典的辅助函数
    
    Args:
        risk_type: 'goal_risk' 或 'plan_risk'
        obj: StrategicGoal 或 Plan 对象
        actual_progress: 实际进度（0-100）
        time_progress: 时间进度（0-100）
        status: 状态
    
    Returns:
        dict: 风险项字典
    """
    status_weight = {
        'in_progress': 100,
        'accepted': 50,
        'published': 10,
        'draft': 5,
    }.get(status, 0)
    
    # 计算进度差距（时间进度 - 实际进度）
    progress_gap = max(0, time_progress - actual_progress)
    
    # 优先级分数：进度差距越大，优先级越高
    priority_score = progress_gap * 100 + status_weight
    
    # 计算进度比例
    progress_ratio = actual_progress / time_progress if time_progress > 0 else 0
    
    if risk_type == 'goal_risk':
        # 计算逾期天数（如果有）
        today = timezone.now().date()
        days_overdue = max(0, (today - obj.end_date).days) if obj.end_date and today > obj.end_date else 0
        
        # 构建描述
        if days_overdue > 0:
            description = f'目标进度落后（实际{actual_progress:.1f}% / 时间{time_progress:.1f}%），已逾期{days_overdue}天'
        else:
            description = f'目标进度落后（实际{actual_progress:.1f}% / 时间{time_progress:.1f}%）'
        
        return {
            'type': 'goal_risk',
            'title': f'⚠️ 风险目标：{obj.name}',
            'description': description,
            'priority': 'high',
            'url': reverse('plan_pages:strategic_goal_detail', args=[obj.id]),
            'object': obj,
            'actual_progress': actual_progress,
            'time_progress': time_progress,
            'progress_ratio': progress_ratio,
            'days_overdue': days_overdue,
            'status': status,
            '_priority_score': priority_score,
        }
    else:  # plan_risk
        # 计算逾期天数（如果有）
        now = timezone.now()
        days_overdue = max(0, (now.date() - obj.end_time.date()).days) if obj.end_time and now.date() > obj.end_time.date() else 0
        
        # 构建描述
        if days_overdue > 0:
            description = f'计划进度落后（实际{actual_progress:.1f}% / 时间{time_progress:.1f}%），已逾期{days_overdue}天'
        else:
            description = f'计划进度落后（实际{actual_progress:.1f}% / 时间{time_progress:.1f}%）'
        
        return {
            'type': 'plan_risk',
            'title': f'⚠️ 风险计划：{obj.name}',
            'description': description,
            'priority': 'high',
            'url': reverse('plan_pages:plan_detail', args=[obj.id]),
            'object': obj,
            'actual_progress': actual_progress,
            'time_progress': time_progress,
            'progress_ratio': progress_ratio,
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
    
    # ========== 风险目标（进度落后的）==========
    # 根据筛选条件决定查询逻辑
    if filter_responsible_person_id or filter_department_id:
        # 筛选了负责人或部门，查询所有符合条件的未完成目标
        all_goals = StrategicGoal.objects.filter(
            level='personal',
            status__in=['published', 'accepted', 'in_progress']
        ).select_related('parent_goal', 'responsible_person').prefetch_related('progress_records')
        all_goals = apply_filters(all_goals, 'goal')
    else:
        # 没有筛选，查询当前用户拥有的未完成个人目标
        all_goals = StrategicGoal.objects.filter(
            level='personal',
            owner=user,
            status__in=['published', 'accepted', 'in_progress']
        ).select_related('parent_goal', 'responsible_person').prefetch_related('progress_records')
    
    # 过滤出进度落后的目标
    for goal in all_goals:
        if _is_progress_behind_goal(goal, today):
            actual_progress = _get_goal_actual_progress(goal)
            time_progress = _calculate_time_progress_goal(goal, today)
            risk_items.append(_build_risk_item('goal_risk', goal, actual_progress, time_progress, goal.status))
    
    # ========== 风险计划（进度落后的）==========
    # 根据筛选条件决定查询逻辑
    if filter_responsible_person_id or filter_department_id:
        # 筛选了负责人或部门，查询所有符合条件的未完成计划
        all_plans = Plan.objects.filter(
            level='personal',
            status__in=['draft', 'published', 'accepted', 'in_progress']
        ).select_related('parent_plan', 'responsible_person').prefetch_related('progress_records')
        all_plans = apply_filters(all_plans, 'plan')
    else:
        # 没有筛选，查询当前用户拥有的未完成个人计划
        all_plans = Plan.objects.filter(
            level='personal',
            owner=user,
            status__in=['draft', 'published', 'accepted', 'in_progress']
        ).select_related('parent_plan', 'responsible_person').prefetch_related('progress_records')
    
    # 过滤出进度落后的计划
    for plan in all_plans:
        if _is_progress_behind_plan(plan, now):
            actual_progress = _get_plan_actual_progress(plan)
            time_progress = _calculate_time_progress_plan(plan, now)
            risk_items.append(_build_risk_item('plan_risk', plan, actual_progress, time_progress, plan.status))
    
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
    
    # ========== 风险目标（负责人负责的，进度落后的）==========
    all_goals = StrategicGoal.objects.filter(
        responsible_person=responsible_user,
        status__in=['published', 'accepted', 'in_progress']
    ).select_related('parent_goal', 'responsible_person', 'owner').prefetch_related('progress_records')
    all_goals = apply_filters(all_goals, 'goal')
    
    # 过滤出进度落后的目标
    for goal in all_goals:
        if _is_progress_behind_goal(goal, today):
            actual_progress = _get_goal_actual_progress(goal)
            time_progress = _calculate_time_progress_goal(goal, today)
            risk_items.append(_build_risk_item('goal_risk', goal, actual_progress, time_progress, goal.status))
    
    # ========== 风险计划（负责人负责的，进度落后的）==========
    all_plans = Plan.objects.filter(
        responsible_person=responsible_user,
        status__in=['draft', 'published', 'accepted', 'in_progress']
    ).select_related('parent_plan', 'responsible_person', 'owner').prefetch_related('progress_records')
    all_plans = apply_filters(all_plans, 'plan')
    
    # 过滤出进度落后的计划
    for plan in all_plans:
        if _is_progress_behind_plan(plan, now):
            actual_progress = _get_plan_actual_progress(plan)
            time_progress = _calculate_time_progress_plan(plan, now)
            risk_items.append(_build_risk_item('plan_risk', plan, actual_progress, time_progress, plan.status))
    
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
    
    # ========== 风险目标（下属负责的，进度落后的）==========
    # 与统计卡片保持一致：包含 owner、responsible_person、created_by
    from django.db.models import Q
    all_goals = StrategicGoal.objects.filter(
        Q(owner__in=subordinates) | Q(responsible_person__in=subordinates) | Q(created_by__in=subordinates),
        status__in=['published', 'accepted', 'in_progress']
    ).distinct().select_related('parent_goal', 'responsible_person', 'owner').prefetch_related('progress_records')
    all_goals = apply_filters(all_goals, 'goal')
    
    # 过滤出进度落后的目标
    for goal in all_goals:
        if _is_progress_behind_goal(goal, today):
            actual_progress = _get_goal_actual_progress(goal)
            time_progress = _calculate_time_progress_goal(goal, today)
            risk_items.append(_build_risk_item('goal_risk', goal, actual_progress, time_progress, goal.status))
    
    # ========== 风险计划（下属负责的，进度落后的）==========
    # 与统计卡片保持一致：包含 owner、responsible_person、created_by
    all_plans = Plan.objects.filter(
        Q(owner__in=subordinates) | Q(responsible_person__in=subordinates) | Q(created_by__in=subordinates),
        status__in=['draft', 'published', 'accepted', 'in_progress']
    ).distinct().select_related('parent_plan', 'responsible_person', 'owner').prefetch_related('progress_records')
    all_plans = apply_filters(all_plans, 'plan')
    
    # 过滤出进度落后的计划
    for plan in all_plans:
        if _is_progress_behind_plan(plan, now):
            actual_progress = _get_plan_actual_progress(plan)
            time_progress = _calculate_time_progress_plan(plan, now)
            risk_items.append(_build_risk_item('plan_risk', plan, actual_progress, time_progress, plan.status))
    
    # ========== 排序：优先级分数降序 ==========
    risk_items.sort(key=lambda x: x['_priority_score'], reverse=True)
    
    # ========== 去重：基于 (type, object.id) ==========
    seen_objects = set()
    unique_risk_items = []
    for item in risk_items:
        obj = item.get('object')
        if obj:
            obj_key = (item.get('type', ''), obj.id)
            if obj_key not in seen_objects:
                seen_objects.add(obj_key)
                unique_risk_items.append(item)
        else:
            # 如果没有 object，也添加（但这种情况应该很少）
            unique_risk_items.append(item)
    
    # 移除内部排序字段
    for item in unique_risk_items:
        item.pop('_priority_score', None)
    
    return unique_risk_items[:limit]

