"""
计划管理模块服务层
"""
from dataclasses import dataclass
from django.utils import timezone
from ..adjudicator import adjudicate_plan_status, AdjudicationResult


@dataclass
class StatusResult:
    """状态计算结果（兼容旧接口）"""
    old: str
    new: str
    changed: bool
    should_log: bool = False  # 是否需要写日志
    base_reason: str = ''  # 基础原因（不包含来源信息，由调用方拼装）


def recalc_plan_status(plan, old_status=None) -> StatusResult:
    """
    P1 状态判定（只支持 4 状态）：
    1) progress>=100 -> completed
    2) cancelled 保持（手动设置的状态）
    3) 否则按时间判断：in_progress / draft
    
    注意：P1 不包含审批流（pending_approval/approving/approved）和逾期状态（overdue）
    这些功能将在 P2 实现。
    
    Args:
        plan: Plan 实例
        old_status: 可选，指定旧状态（如果不提供则使用 plan.status）
    
    Returns:
        StatusResult: 包含旧状态、新状态和是否变更的标记
    """
    old = old_status if old_status is not None else plan.status
    now = timezone.now()

    # P1: 所有状态变更必须通过裁决器
    # 这里只处理系统事实触发的状态变更（如进度更新）
    system_facts = {}
    
    # 检查进度是否达到 100%（系统事实）
    progress = getattr(plan, "progress", 0)
    if progress is not None:
        try:
            progress_float = float(progress)
            if progress_float >= 100:
                # 通过裁决器处理完成状态
                result = adjudicate_plan_status(plan, decision=None, system_facts={'all_tasks_completed': True})
                plan.status = result.new_status
                return StatusResult(
                    result.old_status,
                    result.new_status,
                    result.changed,
                    should_log=result.changed,
                    base_reason=result.reason
                )
        except (ValueError, TypeError):
            pass
    
    # 其他情况：通过裁决器裁决（不传入 decision，只检查系统事实）
    result = adjudicate_plan_status(plan, decision=None, system_facts=system_facts)
    plan.status = result.new_status
    return StatusResult(
        result.old_status,
        result.new_status,
        result.changed,
        should_log=result.changed,
        base_reason=result.reason
    )

