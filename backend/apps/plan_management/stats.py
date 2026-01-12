"""
计划管理模块统计函数
A3-3-7: 使用统一的筛选逻辑，确保统计口径与列表口径一致
"""
from django.db.models import Count, Avg, Q

from backend.apps.plan_management.models import Plan, StrategicGoal
from backend.apps.plan_management.utils import apply_company_scope
from backend.apps.plan_management.filters import (
    ListFilterSpec,
    apply_range,
    apply_mine_participating,
    apply_overdue,
)


def plan_stats(user, params: dict):
    """
    计划统计
    
    Args:
        user: User 对象
        params: 查询参数字典，支持 mine, participating, range, overdue
    
    Returns:
        dict: 统计结果
    """
    # A3-3-7: 使用统一的筛选规格
    spec = ListFilterSpec.from_params(params, allow_overdue=True)
    
    qs = Plan.objects.all()
    qs = apply_company_scope(qs, user)  # 公司隔离
    qs = apply_range(qs, "created_time", spec.range)
    qs = apply_mine_participating(qs, user, spec.mine, spec.participating)
    qs = apply_overdue(qs, spec.overdue)

    agg = qs.aggregate(
        total=Count("id"),
        draft=Count("id", filter=Q(status="draft")),
        pending=Count("id", filter=Q(status="pending_approval")),
        in_progress=Count("id", filter=Q(status="in_progress")),
        overdue=Count("id", filter=Q(status="overdue")),
        completed=Count("id", filter=Q(status="completed")),
        cancelled=Count("id", filter=Q(status="cancelled")),
        avg_progress=Avg("progress"),
    )
    # None -> 0
    agg["avg_progress"] = float(agg["avg_progress"] or 0)
    return agg


def goal_stats(user, params: dict):
    """
    目标统计
    
    Args:
        user: User 对象
        params: 查询参数字典，支持 mine, participating, range
    
    Returns:
        dict: 统计结果
    """
    # A3-3-7: 使用统一的筛选规格
    spec = ListFilterSpec.from_params(params, allow_overdue=False)
    
    qs = StrategicGoal.objects.all()
    qs = apply_company_scope(qs, user)  # 公司隔离
    qs = apply_range(qs, "created_time", spec.range)
    qs = apply_mine_participating(qs, user, spec.mine, spec.participating,
                                   responsible_field="responsible_person", participants_field="participants")

    agg = qs.aggregate(
        total=Count("id"),
        draft=Count("id", filter=Q(status="draft")),
        published=Count("id", filter=Q(status="published")),
        in_progress=Count("id", filter=Q(status="in_progress")),
        completed=Count("id", filter=Q(status="completed")),
        cancelled=Count("id", filter=Q(status="cancelled")),
        avg_completion=Avg("completion_rate"),
    )
    agg["avg_completion"] = float(agg["avg_completion"] or 0)
    return agg

