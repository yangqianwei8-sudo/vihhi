"""
计划决策服务层（P1 裁决模型 v2）

所有 Plan.status 的状态变更必须通过此服务层，确保规则统一、可审计。
"""
from django.db import transaction, IntegrityError
from django.utils import timezone
from django.core.exceptions import ValidationError, PermissionDenied
from rest_framework import status as http_status

from backend.apps.plan_management.models import Plan, PlanDecision


class PlanDecisionError(ValidationError):
    """计划决策相关错误（映射到 HTTP 409 Conflict）"""
    status_code = http_status.HTTP_409_CONFLICT


def _ensure_plan_status(plan: Plan, allowed: set[str], action: str):
    """确保计划状态在允许的范围内"""
    if plan.status not in allowed:
        raise PlanDecisionError(f"Plan({plan.id}) status={plan.status} 不允许执行 {action}")


@transaction.atomic
def request_start(plan: Plan, user, reason: str | None = None) -> PlanDecision:
    """
    发起启动请求
    
    Args:
        plan: 计划实例
        user: 请求用户
        reason: 请求原因（可选）
    
    Returns:
        PlanDecision: 创建的决策记录
    
    Raises:
        PlanDecisionError: 如果状态不允许或已存在待处理的请求
        ValidationError: 如果验收标准为空
    """
    _ensure_plan_status(plan, {"draft"}, "start_request")
    
    # 提交审批前必须填写验收标准
    if not plan.acceptance_criteria or not plan.acceptance_criteria.strip():
        raise PlanDecisionError("提交审批前必须填写验收标准，明确说明如何判定计划完成")

    try:
        decision = PlanDecision.objects.create(
            plan=plan,
            request_type="start",
            decision=None,
            requested_by=user,
            requested_at=timezone.now(),
            reason=reason or "",
        )
    except IntegrityError:
        # 来自"同 plan + request_type 只能 1 个 pending"的约束
        raise PlanDecisionError("该计划已存在待裁决的 start 请求")

    return decision


@transaction.atomic
def request_cancel(plan: Plan, user, reason: str | None = None) -> PlanDecision:
    """
    发起取消请求
    
    Args:
        plan: 计划实例
        user: 请求用户
        reason: 请求原因（可选）
    
    Returns:
        PlanDecision: 创建的决策记录
    
    Raises:
        PlanDecisionError: 如果状态不允许或已存在待处理的请求
    """
    _ensure_plan_status(plan, {"draft", "in_progress"}, "cancel_request")

    try:
        decision = PlanDecision.objects.create(
            plan=plan,
            request_type="cancel",
            decision=None,
            requested_by=user,
            requested_at=timezone.now(),
            reason=reason or "",
        )
    except IntegrityError:
        raise PlanDecisionError("该计划已存在待裁决的 cancel 请求")

    return decision


@transaction.atomic
def decide(decision_id: int, user, approve: bool, reason: str | None = None) -> PlanDecision:
    """
    裁决决策
    
    Args:
        decision_id: 决策记录ID
        user: 裁决用户
        approve: 是否通过（True=通过，False=驳回）
        reason: 裁决原因（可选）
    
    Returns:
        PlanDecision: 更新后的决策记录
    
    Raises:
        PlanDecisionError: 如果决策已处理或状态不允许
        PermissionDenied: 如果用户无裁决权限
    """
    # 使用 select_for_update 锁行，防止并发问题
    decision = PlanDecision.objects.select_for_update().select_related("plan").get(id=decision_id)
    
    # 只处理 pending
    if decision.decided_at is not None:
        raise PlanDecisionError("该裁决已处理，不能重复裁决")

    # 这里先复用现有权限体系：最小可行做法
    # 你们若已有"裁决权限"，替换成对应 has_perm
    if not user.is_superuser and not user.has_perm("plan_management.change_plan"):
        raise PermissionDenied("无裁决权限")

    decision.decision = "approve" if approve else "reject"
    decision.decided_by = user
    decision.decided_at = timezone.now()
    if reason is not None:
        decision.reason = reason

    plan = decision.plan

    # 只有 approve 才改 Plan.status
    if approve:
        if decision.request_type == "start":
            _ensure_plan_status(plan, {"draft"}, "start_approve")
            plan.status = "in_progress"
            plan.save(update_fields=["status"])
        elif decision.request_type == "cancel":
            _ensure_plan_status(plan, {"draft", "in_progress"}, "cancel_approve")
            plan.status = "cancelled"
            plan.save(update_fields=["status"])
        else:
            raise PlanDecisionError(f"未知 request_type={decision.request_type}")

    decision.save(update_fields=["decision", "decided_by", "decided_at", "reason"])
    return decision


@transaction.atomic
def system_complete_if_ready(plan: Plan) -> bool:
    """
    系统判定完成：只有 in_progress 且进度达到 100% 才能置 completed
    返回是否发生了状态变化
    
    Args:
        plan: Plan 实例
    
    Returns:
        bool: 是否发生了状态变化
    """
    if plan.status != "in_progress":
        return False

    # 检查进度是否达到 100%（系统事实）
    progress = getattr(plan, "progress", 0)
    if progress is None:
        return False
    
    try:
        progress_float = float(progress)
        if progress_float < 100:
            return False
    except (ValueError, TypeError):
        return False

    # 通过裁决器处理完成状态
    from ..adjudicator import adjudicate_plan_status
    result = adjudicate_plan_status(plan, decision=None, system_facts={'all_tasks_completed': True})
    
    if result.changed:
        plan.status = result.new_status
        plan.save(update_fields=["status"])
        return True
    
    return False

