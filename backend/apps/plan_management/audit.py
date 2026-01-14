"""
计划管理模块统一审计封装
A3-3-8-1: 提供统一的审计日志记录接口，确保所有关键动作都有审计追踪
"""
import logging
from typing import Optional, Dict, Any
from django.contrib.contenttypes.models import ContentType
try:
    from backend.apps.system_management.models import AuditLog, AuditAction
except ImportError:
    AuditLog = None
    AuditAction = None

logger = logging.getLogger(__name__)


def audit_event(
    actor,
    obj,
    action: str,
    event: str,
    changes: Optional[Dict[str, Dict[str, Any]]] = None,
    meta: Optional[Dict[str, Any]] = None,
    request=None
):
    """
    统一的审计事件记录入口
    
    Args:
        actor: User 对象，操作者
        obj: 被操作的对象（Plan 或 StrategicGoal）
        action: AuditAction 枚举值（如 AuditAction.PLAN_ACTION）
        event: 事件名称（如 "progress_update", "status_change", "create" 等）
        changes: 变更内容字典，格式：{"field": {"from": old_value, "to": new_value}}
        meta: 额外的元数据字典
        request: HttpRequest 对象（可选，用于自动提取 IP/UA）
    
    Returns:
        AuditLog: 创建的审计日志对象
    
    Examples:
        # 进度更新
        audit_event(
            actor=user,
            obj=plan,
            action=AuditAction.PLAN_ACTION,
            event="progress_update",
            changes={"progress": {"from": 50, "to": 80}},
            request=request
        )
        
        # 状态变更
        audit_event(
            actor=user,
            obj=plan,
            action=AuditAction.PLAN_ACTION,
            event="status_change",
            changes={"status": {"from": "draft", "to": "in_progress"}},
            request=request
        )
    """
    if not actor or not obj:
        logger.warning("audit_event: actor 或 obj 为空，跳过审计记录")
        return None
    
    # 构建 object_type（使用 _meta.label，如 "plan_management.Plan"）
    object_type = obj._meta.label
    
    # 构建 changes（确保格式统一）
    changes_dict = changes or {}
    
    # 构建 meta（合并自动提取的信息和用户传入的信息）
    meta_dict = meta or {}
    
    # 如果提供了 request，自动提取 IP 和 UA
    if request:
        meta_dict.setdefault("ip", request.META.get("REMOTE_ADDR"))
        meta_dict.setdefault("ua", request.META.get("HTTP_USER_AGENT"))
    
    # 确保 event 在 meta 中
    meta_dict["event"] = event
    
    if not AuditLog:
        logger.warning("AuditLog 不可用，跳过审计记录")
        return None
    
    try:
        audit_log = AuditLog.objects.create(
            actor=actor,
            action=action,
            object_type=object_type,
            object_id=str(obj.pk),
            changes=changes_dict,
            meta=meta_dict,
        )
        
        logger.info(
            f"审计日志已记录: {action} / {event} / {object_type}:{obj.pk} / "
            f"actor={actor.username if hasattr(actor, 'username') else actor}"
        )
        
        return audit_log
    
    except Exception as e:
        logger.error(f"记录审计日志失败: {str(e)}", exc_info=True)
        return None


def audit_plan_event(
    actor,
    plan,
    event: str,
    changes: Optional[Dict[str, Dict[str, Any]]] = None,
    meta: Optional[Dict[str, Any]] = None,
    request=None
):
    """
    计划审计事件快捷方法
    
    Args:
        actor: User 对象
        plan: Plan 对象
        event: 事件名称（progress_update, status_change, create, update, submit_approval, approve, reject, apply_adjustment）
        changes: 变更内容
        meta: 元数据
        request: HttpRequest 对象
    
    Returns:
        AuditLog: 创建的审计日志对象
    """
    return audit_event(
        actor=actor,
        obj=plan,
        action=AuditAction.PLAN_ACTION,
        event=event,
        changes=changes,
        meta=meta,
        request=request
    )


def audit_goal_event(
    actor,
    goal,
    event: str,
    changes: Optional[Dict[str, Dict[str, Any]]] = None,
    meta: Optional[Dict[str, Any]] = None,
    request=None
):
    """
    目标审计事件快捷方法
    
    Args:
        actor: User 对象
        goal: StrategicGoal 对象
        event: 事件名称（progress_update, status_change, create, update, submit_approval, approve, reject, apply_adjustment）
        changes: 变更内容
        meta: 元数据
        request: HttpRequest 对象
    
    Returns:
        AuditLog: 创建的审计日志对象
    """
    # 使用 GOAL_ACTION（已在 AuditAction 中定义）
    action = AuditAction.GOAL_ACTION
    
    return audit_event(
        actor=actor,
        obj=goal,
        action=action,
        event=event,
        changes=changes,
        meta=meta,
        request=request
    )

