"""
P1 计划状态裁决器
严格按 P1 状态裁决表执行，不处理历史兼容，不做 fallback
"""
from dataclasses import dataclass
from typing import Optional, Dict, Any
from django.utils import timezone


@dataclass
class AdjudicationResult:
    """裁决结果"""
    old_status: str
    new_status: str
    changed: bool
    reason: str = ''  # 裁决原因


def adjudicate_plan_status(
    plan,
    decision: Optional[str] = None,
    system_facts: Optional[Dict[str, Any]] = None
) -> AdjudicationResult:
    """
    P1 状态裁决函数
    严格按 P1 状态裁决表执行
    
    Args:
        plan: Plan 实例
        decision: 人为输入事件
            - approve: 审批通过
            - reject: 审批驳回
            - approve_cancel: 同意取消
            - reject_cancel: 驳回取消
        system_facts: 系统事实
            - all_tasks_completed: bool - 所有任务已完成
    
    Returns:
        AdjudicationResult: 裁决结果
    """
    old_status = plan.status
    new_status = old_status
    reason = ''
    
    # 确保状态合法（P1 只认 4 个状态）
    valid_statuses = {'draft', 'in_progress', 'completed', 'cancelled'}
    if old_status not in valid_statuses:
        # 非法状态，强制重置为 draft
        new_status = 'draft'
        reason = f'非法状态 {old_status}，重置为 draft'
        return AdjudicationResult(old_status, new_status, True, reason)
    
    # 终态锁定：completed 和 cancelled 不可变更
    if old_status in ('completed', 'cancelled'):
        return AdjudicationResult(old_status, old_status, False, '终态锁定，不可变更')
    
    # 按状态裁决表执行
    if old_status == 'draft':
        new_status, reason = _adjudicate_draft(plan, decision, system_facts)
    elif old_status == 'in_progress':
        new_status, reason = _adjudicate_in_progress(plan, decision, system_facts)
    else:
        # 其他状态保持
        new_status = old_status
        reason = '状态保持'
    
    changed = (old_status != new_status)
    return AdjudicationResult(old_status, new_status, changed, reason)


def _adjudicate_draft(plan, decision, system_facts):
    """草稿状态裁决"""
    # 根据裁决表：draft 状态的处理
    if decision == 'approve':
        # 审批通过：检查执行条件
        if _check_execution_conditions(plan):
            return 'in_progress', '审批通过且条件满足，进入执行中'
        else:
            return 'draft', '审批通过但条件不满足，保持草稿'
    elif decision == 'reject':
        # 审批驳回：保持草稿
        return 'draft', '审批驳回，保持草稿'
    elif decision == 'approve_cancel':
        # 同意取消：进入已取消
        return 'cancelled', '同意取消，进入已取消'
    else:
        # 其他情况保持草稿（submit_for_approval 和 request_cancel 不改变状态）
        return 'draft', '保持草稿'


def _adjudicate_in_progress(plan, decision, system_facts):
    """执行中状态裁决"""
    # 优先检查系统事实：all_tasks_completed
    if system_facts and system_facts.get('all_tasks_completed'):
        return 'completed', '所有任务已完成，系统自动完成'
    
    # 检查进度是否达到 100%
    progress = getattr(plan, 'progress', 0)
    if progress is not None:
        try:
            if float(progress) >= 100:
                return 'completed', '进度达到100%，系统自动完成'
        except (ValueError, TypeError):
            pass
    
    # 处理取消申请
    if decision == 'approve_cancel':
        # 同意取消：检查是否已完成
        progress = getattr(plan, 'progress', 0)
        if progress is not None:
            try:
                if float(progress) >= 100:
                    # 已完成，不能取消
                    return 'in_progress', '已完成，不能取消'
            except (ValueError, TypeError):
                pass
        return 'cancelled', '同意取消，进入已取消'
    elif decision == 'reject_cancel':
        # 驳回取消：保持执行中
        return 'in_progress', '驳回取消，保持执行中'
    
    # request_cancel 不改变状态（只是触发审批流程）
    # progress_updated 不改变状态（只是更新进度）
    
    # 默认保持执行中
    return 'in_progress', '保持执行中'


def _check_execution_conditions(plan):
    """
    检查是否满足执行条件
    根据裁决表：approve 时需要检查"结构完整 + 无阻断"
    """
    # P1 最小实现：检查基本结构
    # 1. 必须有负责人
    if not hasattr(plan, 'responsible_person') or not plan.responsible_person:
        return False
    
    # 2. 必须有开始时间
    if not hasattr(plan, 'start_time') or not plan.start_time:
        return False
    
    # 3. 必须有名称
    if not hasattr(plan, 'name') or not plan.name:
        return False
    
    # P1 阶段：不检查阻断风险（P2 功能）
    # P1 阶段：不检查子任务结构（P2 功能）
    
    return True
