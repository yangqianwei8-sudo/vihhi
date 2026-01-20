"""
计划管理模块API视图（RESTful API）

提供计划管理的RESTful API接口
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied, ValidationError
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.utils import timezone
from datetime import timedelta
from django.db.models import Q
from backend.apps.plan_management.models import Plan, StrategicGoal, PlanStatusLog, PlanProgressRecord 
from .serializers import PlanSerializer, StrategicGoalSerializer
# Optional dependency: AuditMixin (if available)
try:
    from backend.core.audit import AuditMixin
except ImportError:
    # 可选依赖：如果 audit 模块不存在，使用占位符
    # 实际审计功能已通过 compat.py 中的 safe_audit_log() 实现
    class AuditMixin:
        """占位符：AuditMixin 功能已迁移到 compat.py 中的 safe_audit_log"""
        pass
from .compat import safe_audit_log, get_audit_action, legacy_api_gone
from .services import recalc_plan_status
from .services.plan_decisions import request_start, request_cancel, PlanDecisionError
from .adjudicator import adjudicate_plan_status
from .filters import ListFilterSpec, apply_range, apply_mine_participating, apply_overdue
from .audit import audit_plan_event
from .notifications import notify_approvers, notify_submitter
import logging

logger = logging.getLogger(__name__)


# ==================== 第二刀：卡住项强制填写处理说明 ====================

def _require_handling_note_if_blocked(obj, request):
    """
    第二刀：卡住项推进时强制要求填写处理说明
    
    Args:
        obj: Plan 或 StrategicGoal 实例
        request: HttpRequest 对象，从 request.data 取 handling_note
    
    Returns:
        tuple: (is_blocked: bool, handling_note: str)
    
    Raises:
        ValidationError: 如果卡住且未提供处理说明
    """
    from .models import GoalStatusLog
    
    DRAFT_TIMEOUT_DAYS = 7
    PENDING_TIMEOUT_DAYS = 3
    
    now = timezone.now()
    draft_deadline = now - timedelta(days=DRAFT_TIMEOUT_DAYS)
    pending_deadline = now - timedelta(days=PENDING_TIMEOUT_DAYS)
    
    # 判断是否卡住
    is_blocked = False
    
    if obj.status == 'draft':
        # draft 超 7 天（按 created_time）
        if obj.created_time < draft_deadline:
            is_blocked = True
    elif obj.status == 'pending_approval':
        # pending_approval 超 3 天（按 StatusLog.changed_time，无则 created_time）
        if isinstance(obj, Plan):
            # 查询 PlanStatusLog 中 pending_approval 状态变更时间
            pending_log = PlanStatusLog.objects.filter(
                plan=obj,
                new_status="pending_approval"
            ).order_by("-changed_time").first()
            
            if pending_log:
                pending_since_safe = pending_log.changed_time
            else:
                pending_since_safe = obj.created_time
            
            if pending_since_safe < pending_deadline:
                is_blocked = True
        elif isinstance(obj, StrategicGoal):
            # 查询 GoalStatusLog 中 pending_approval 状态变更时间
            pending_log = GoalStatusLog.objects.filter(
                goal=obj,
                new_status="pending_approval"
            ).order_by("-changed_time").first()
            
            if pending_log:
                pending_since_safe = pending_log.changed_time
            else:
                pending_since_safe = obj.created_time
            
            if pending_since_safe < pending_deadline:
                is_blocked = True
    
    # 从 request.data 获取处理说明（支持多种字段名）
    handling_note = (
        request.data.get('handling_note') or
        request.data.get('reason') or
        request.data.get('comment') or
        ''
    ).strip()
    
    # 如果卡住，必须提供处理说明
    if is_blocked and not handling_note:
        raise ValidationError("卡住事项推进时必须填写处理说明（handling_note）。请说明推进原因或处理计划。")
    
    return (is_blocked, handling_note)


class StrategicGoalViewSet(AuditMixin, viewsets.ModelViewSet):
    """
    战略目标视图集
    
    提供战略目标的CRUD操作
    """
    queryset = StrategicGoal.objects.all()
    serializer_class = StrategicGoalSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'goal_type', 'goal_period']
    search_fields = ['goal_number', 'indicator_name']
    ordering_fields = ['created_time', 'completion_rate']
    ordering = ['-created_time']

    def _require_change_perm(self, request, perm):
        """
        B2-1: 统一检查 change 权限
        
        Args:
            request: HttpRequest 对象
            perm: 权限代码名，例如 'plan_management.change_strategicgoal'
        
        Raises:
            PermissionDenied: 如果用户没有权限
        """
        if request.user.is_superuser:
            return
        if not request.user.has_perm(perm):
            raise PermissionDenied(f"缺少权限: {perm}")

    def _require_approve_perm(self, request, perm):
        """
        B3-3: 统一检查审批权限
        
        Args:
            request: HttpRequest 对象
            perm: 权限代码名，例如 'plan_management.approve_strategicgoal'
        
        Raises:
            PermissionDenied: 如果用户没有权限
        """
        if request.user.is_superuser:
            return
        if not request.user.has_perm(perm):
            raise PermissionDenied(f"缺少审批权限: {perm}")

    def _get_profile_org(self):
        """获取当前用户的公司/部门信息"""
        user = getattr(self.request, "user", None)
        if not user or not user.is_authenticated:
            return None, None
        profile = getattr(user, "profile", None)
        if not profile:
            return None, None
        return getattr(profile, "company", None), getattr(profile, "department", None)

    def get_queryset(self):
        """获取查询集"""
        qs = super().get_queryset()
        user = self.request.user
        if not user.is_authenticated:
            return qs.none()
        if user.is_superuser:
            return qs
        company, _dept = self._get_profile_org()
        if not company:
            return qs.none()
        qs = qs.filter(company=company)
        
        # A3-3-7: 使用统一的筛选逻辑
        spec = ListFilterSpec.from_params(self.request.query_params, allow_overdue=False)
        qs = apply_range(qs, "created_time", spec.range)
        qs = apply_mine_participating(qs, user, spec.mine, spec.participating)
        
        # 默认排序：离现在最近/最新
        return qs.order_by("-created_time", "-id")

    def perform_create(self, serializer):
        """创建目标时自动赋值 company/org_department"""
        user = self.request.user
        company, dept = self._get_profile_org()

        # 第二刀：卡住项过多时禁止新增
        from backend.apps.plan_management.views_pages import get_blocked_count_for_user
        
        creator = user
        owner = serializer.validated_data.get('responsible_person')
        
        creator_blocked = get_blocked_count_for_user(creator)
        owner_blocked = get_blocked_count_for_user(owner) if owner else 0
        
        if creator_blocked >= 5:
            raise ValidationError(f'您当前有 {creator_blocked} 个卡住事项，请先处理后再创建新目标。')
        elif owner_blocked >= 5:
            raise ValidationError(f'负责人当前有 {owner_blocked} 个卡住事项，请先处理后再创建新目标。')

        extra = {}
        # 普通用户：强制继承（防止前端乱传穿透）
        if not user.is_superuser:
            if not company:
                raise PermissionDenied("用户未绑定公司，禁止创建。")
            extra["company"] = company
            extra["org_department"] = dept
            serializer.save(**extra)
            return

        # 超管：允许代录，但若前端未传则用 profile 默认
        if company and not serializer.validated_data.get("company"):
            extra["company"] = company
        if dept and not serializer.validated_data.get("org_department"):
            extra["org_department"] = dept
        serializer.save(**extra)

    ORG_FIELDS = ("company", "org_department")

    def _reject_org_change_if_needed(self, instance, serializer):
        """检查并拒绝普通用户修改归属字段"""
        user = self.request.user
        if user.is_superuser:
            return  # 超管允许

        # 普通用户禁止改归属
        incoming_company = serializer.validated_data.get("company", None)
        incoming_dept = serializer.validated_data.get("org_department", None)

        if incoming_company and instance.company_id != incoming_company.id:
            raise PermissionDenied("禁止修改 company")
        if incoming_dept and instance.org_department_id != incoming_dept.id:
            raise PermissionDenied("禁止修改 org_department")

    def perform_update(self, serializer):
        """更新目标时保护归属字段"""
        instance = self.get_object()
        self._reject_org_change_if_needed(instance, serializer)

        user = self.request.user
        old_company_id = instance.company_id
        old_dept_id = instance.org_department_id

        obj = serializer.save()

        # 普通用户：如果为空才补齐（不覆盖）
        if not user.is_superuser:
            company, dept = self._get_profile_org()
            changed = False
            if not obj.company_id and company:
                obj.company = company
                changed = True
            if not obj.org_department_id and dept:
                obj.org_department = dept
                changed = True
            if changed:
                obj.save(update_fields=["company", "org_department"])
            return

        # 超管：如果改了归属，写 AuditLog
        changes = {}
        if old_company_id != obj.company_id:
            changes["company"] = {"from": old_company_id, "to": obj.company_id}
        if old_dept_id != obj.org_department_id:
            changes["org_department"] = {"from": old_dept_id, "to": obj.org_department_id}

        if changes:
            audit_action = get_audit_action()
            if audit_action:
                safe_audit_log(
                    actor=user,
                    action=audit_action.ORG_CHANGE,
                    object_type=f"{obj._meta.app_label}.{obj.__class__.__name__}",
                    object_id=str(obj.pk),
                    changes=changes,
                    meta={
                        "ip": self.request.META.get("REMOTE_ADDR"),
                        "ua": self.request.META.get("HTTP_USER_AGENT"),
                    },
                )

    @action(detail=True, methods=['post'], url_path='submit-approval')
    def submit_approval(self, request, pk=None):
        """
        P1 v2: 接口已废弃
        
        提交审批的功能已废弃，请使用 PlanDecision 裁决机制。
        """
        return legacy_api_gone()
        
        # 以下代码已废弃，保留用于参考
        # # B2-1: 统一检查 change 权限
        # self._require_change_perm(request, "plan_management.change_strategicgoal")
        
        # B2-2: 使用 get_object() 确保只能操作本公司数据
        goal = self.get_object()
        user = request.user
        
        # 检查当前状态是否允许提交审批
        if goal.status != 'draft':
            raise ValidationError(
                f"当前状态为 {goal.get_status_display()}，无法提交审批。只有草稿状态的目标才能提交审批。"
            )
        
        # 第二刀：卡住项推进时必须填写处理说明
        is_blocked, handling_note = _require_handling_note_if_blocked(goal, request)
        comment = request.data.get('comment', '')
        # 如果卡住，优先使用 handling_note；否则使用 comment
        if is_blocked and handling_note:
            comment = handling_note
        
        old_status = goal.status
        
        # 更新状态
        goal.status = 'pending_approval'
        goal.save(update_fields=['status'])
        
        # 尝试创建工作流实例（路径 A：先业务内置，工作流只做通知/留痕）
        workflow_instance_id = None
        try:
            from django.contrib.contenttypes.models import ContentType
            from backend.apps.workflow_engine.models import ApprovalInstance, WorkflowTemplate
            from backend.apps.workflow_engine.services import ApprovalEngine
            
            content_type = ContentType.objects.get_for_model(StrategicGoal)
            # 检查是否已有审批实例
            existing_instance = ApprovalInstance.objects.filter(
                content_type=content_type,
                object_id=goal.pk,
                status__in=['pending', 'in_progress']
            ).first()
            
            if not existing_instance:
                # 尝试获取目标审批流程模板
                try:
                    workflow = WorkflowTemplate.objects.filter(
                        code='goal_approval',
                        status='active'
                    ).first()
                    
                    if workflow:
                        instance = ApprovalEngine.start_approval(
                            workflow=workflow,
                            content_object=goal,
                            applicant=user,
                            comment=comment or f'用户 {user.username} 提交目标审批'
                        )
                        workflow_instance_id = instance.id
                except Exception as e:
                    logger.warning(f"创建工作流实例失败（不影响业务）：{str(e)}")
        except Exception as e:
            logger.warning(f"工作流引擎不可用（不影响业务）：{str(e)}")
        
        # 记录状态日志
        from .models import GoalStatusLog
        GoalStatusLog.objects.create(
            goal=goal,
            old_status=old_status,
            new_status='pending_approval',
            changed_by=user,
            change_reason=handling_note if is_blocked and handling_note else '提交审批'
        )
        
        # B2-3: 记录审计日志
        from .audit import audit_goal_event
        audit_goal_event(
            actor=user,
            goal=goal,
            event="submit_approval",
            changes={
                "status": {"from": old_status, "to": "pending_approval"}
            },
            meta={
                "event": "submit_approval",
                "comment": comment[:200] if comment else "",
                "workflow_instance_id": workflow_instance_id,
                "source": "api",
            },
            request=request
        )
        
        # C3-2: 通知审批人
        notify_approvers(goal, 'submit', user, comment)
        
        serializer = self.get_serializer(goal)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='approve')
    def approve(self, request, pk=None):
        """
        P1 v2: 接口已废弃
        
        审批通过的功能已废弃，请使用 PlanDecision 裁决机制。
        """
        return legacy_api_gone()
        
        # 以下代码已废弃，保留用于参考
        # # B3-3: 检查审批权限
        # self._require_approve_perm(request, "plan_management.approve_strategicgoal")
        
        # B2-2: 使用 get_object() 确保只能操作本公司数据
        goal = self.get_object()
        user = request.user
        
        # 检查当前状态
        if goal.status != 'pending_approval':
            raise ValidationError(f"当前状态为 {goal.get_status_display()}，无法审批。只有审批中的目标才能审批。")
        
        # 第二刀：卡住项推进时必须填写处理说明
        is_blocked, handling_note = _require_handling_note_if_blocked(goal, request)
        comment = request.data.get('comment', '')
        # 如果卡住，优先使用 handling_note；否则使用 comment
        if is_blocked and handling_note:
            comment = handling_note
        
        old_status = goal.status
        
        # 更新状态为 published
        goal.status = 'published'
        goal.save(update_fields=['status'])
        
        # 尝试更新工作流实例（路径 A：业务回写状态，然后通知工作流）
        workflow_instance_id = None
        try:
            from django.contrib.contenttypes.models import ContentType
            from backend.apps.workflow_engine.models import ApprovalInstance
            
            content_type = ContentType.objects.get_for_model(StrategicGoal)
            instance = ApprovalInstance.objects.filter(
                content_type=content_type,
                object_id=goal.pk,
                status__in=['pending', 'in_progress']
            ).first()
            
            if instance:
                workflow_instance_id = instance.id
                # 尝试完成审批节点（如果工作流引擎支持）
                try:
                    from backend.apps.workflow_engine.services import ApprovalEngine
                    ApprovalEngine.approve_node(
                        instance=instance,
                        approver=user,
                        comment=comment or '审批通过'
                    )
                except Exception as e:
                    logger.warning(f"更新工作流节点失败（不影响业务）：{str(e)}")
        except Exception as e:
            logger.warning(f"工作流引擎不可用（不影响业务）：{str(e)}")
        
        # 记录状态日志
        from .models import GoalStatusLog
        # 第二刀：如果卡住，使用 handling_note；否则使用原有格式
        if is_blocked and handling_note:
            change_reason = handling_note
        else:
            change_reason = f'审批通过{": " + comment if comment else ""}'
        
        GoalStatusLog.objects.create(
            goal=goal,
            old_status=old_status,
            new_status='published',
            changed_by=user,
            change_reason=change_reason
        )
        
        # B2-3: 记录审计日志
        from .audit import audit_goal_event
        audit_goal_event(
            actor=user,
            goal=goal,
            event="approve",
            changes={
                "status": {"from": old_status, "to": "published"}
            },
            meta={
                "event": "approve",
                "comment": comment[:200] if comment else "",
                "workflow_instance_id": workflow_instance_id,
                "source": "api",
            },
            request=request
        )
        
        # C3-2: 通知提交人
        notify_submitter(goal, 'approve', user, comment)
        
        serializer = self.get_serializer(goal)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='reject')
    def reject(self, request, pk=None):
        """
        P1 v2: 接口已废弃
        
        审批驳回的功能已废弃，请使用 PlanDecision 裁决机制。
        """
        return legacy_api_gone()
        
        # 以下代码已废弃，保留用于参考
        # # B3-3: 检查审批权限
        # self._require_approve_perm(request, "plan_management.approve_strategicgoal")
        
        # B2-2: 使用 get_object() 确保只能操作本公司数据
        goal = self.get_object()
        user = request.user
        
        # 检查当前状态
        if goal.status != 'pending_approval':
            raise ValidationError(f"当前状态为 {goal.get_status_display()}，无法驳回。只有审批中的目标才能驳回。")
        
        # 第二刀：卡住项推进时必须填写处理说明
        is_blocked, handling_note = _require_handling_note_if_blocked(goal, request)
        reason = request.data.get('reason', '')
        # 如果卡住，优先使用 handling_note；否则使用 reason
        if is_blocked and handling_note:
            reason = handling_note
        
        old_status = goal.status
        
        # 更新状态为 draft
        goal.status = 'draft'
        goal.save(update_fields=['status'])
        
        # 尝试更新工作流实例（路径 A：业务回写状态，然后通知工作流）
        workflow_instance_id = None
        try:
            from django.contrib.contenttypes.models import ContentType
            from backend.apps.workflow_engine.models import ApprovalInstance
            
            content_type = ContentType.objects.get_for_model(StrategicGoal)
            instance = ApprovalInstance.objects.filter(
                content_type=content_type,
                object_id=goal.pk,
                status__in=['pending', 'in_progress']
            ).first()
            
            if instance:
                workflow_instance_id = instance.id
                # 尝试驳回审批节点（如果工作流引擎支持）
                try:
                    from backend.apps.workflow_engine.services import ApprovalEngine
                    ApprovalEngine.reject_node(
                        instance=instance,
                        approver=user,
                        comment=reason or '审批驳回'
                    )
                except Exception as e:
                    logger.warning(f"更新工作流节点失败（不影响业务）：{str(e)}")
        except Exception as e:
            logger.warning(f"工作流引擎不可用（不影响业务）：{str(e)}")
        
        # 记录状态日志
        from .models import GoalStatusLog
        # 第二刀：如果卡住，使用 handling_note；否则使用原有格式
        if is_blocked and handling_note:
            change_reason = handling_note
        else:
            change_reason = f'审批驳回{": " + reason if reason else ""}'
        
        GoalStatusLog.objects.create(
            goal=goal,
            old_status=old_status,
            new_status='draft',
            changed_by=user,
            change_reason=change_reason
        )
        
        # B2-3: 记录审计日志
        from .audit import audit_goal_event
        audit_goal_event(
            actor=user,
            goal=goal,
            event="reject",
            changes={
                "status": {"from": old_status, "to": "draft"}
            },
            meta={
                "event": "reject",
                "reason": reason[:200] if reason else "",
                "workflow_instance_id": workflow_instance_id,
                "source": "api",
            },
            request=request
        )
        
        # C3-2: 通知提交人
        notify_submitter(goal, 'reject', user, reason)
        
        serializer = self.get_serializer(goal)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='cancel-approval')
    def cancel_approval(self, request, pk=None):
        """
        P1 v2: 接口已废弃
        
        取消审批的功能已废弃，请使用 PlanDecision 裁决机制。
        """
        return legacy_api_gone()
        
        # 以下代码已废弃，保留用于参考
        # # B2-1: 统一检查 change 权限
        # self._require_change_perm(request, "plan_management.change_strategicgoal")
        
        # B2-2: 使用 get_object() 确保只能操作本公司数据
        goal = self.get_object()
        user = request.user
        
        # 检查当前状态
        if goal.status != 'pending_approval':
            raise ValidationError(f"当前状态为 {goal.get_status_display()}，无法取消审批。只有审批中的目标才能取消审批。")
        
        reason = request.data.get('reason', '')
        old_status = goal.status
        
        # 更新状态为 draft
        goal.status = 'draft'
        goal.save(update_fields=['status'])
        
        # 尝试取消工作流实例（路径 A：业务回写状态，然后通知工作流）
        workflow_instance_id = None
        try:
            from django.contrib.contenttypes.models import ContentType
            from backend.apps.workflow_engine.models import ApprovalInstance
            
            content_type = ContentType.objects.get_for_model(StrategicGoal)
            instance = ApprovalInstance.objects.filter(
                content_type=content_type,
                object_id=goal.pk,
                status__in=['pending', 'in_progress']
            ).first()
            
            if instance:
                workflow_instance_id = instance.id
                # 尝试取消审批流程（如果工作流引擎支持）
                try:
                    from backend.apps.workflow_engine.services import ApprovalEngine
                    ApprovalEngine.withdraw_approval(
                        instance=instance,
                        user=user,
                        comment=reason or '取消审批'
                    )
                except Exception as e:
                    logger.warning(f"取消工作流实例失败（不影响业务）：{str(e)}")
        except Exception as e:
            logger.warning(f"工作流引擎不可用（不影响业务）：{str(e)}")
        
        # 记录状态日志
        from .models import GoalStatusLog
        # 第二刀：如果卡住，使用 handling_note；否则使用原有格式
        if is_blocked and handling_note:
            change_reason = handling_note
        else:
            change_reason = f'取消审批{": " + reason if reason else ""}'
        
        GoalStatusLog.objects.create(
            goal=goal,
            old_status=old_status,
            new_status='draft',
            changed_by=user,
            change_reason=change_reason
        )
        
        # B2-3: 记录审计日志
        from .audit import audit_goal_event
        audit_goal_event(
            actor=user,
            goal=goal,
            event="cancel_approval",
            changes={
                "status": {"from": old_status, "to": "draft"}
            },
            meta={
                "event": "cancel_approval",
                "reason": reason[:200] if reason else "",
                "workflow_instance_id": workflow_instance_id,
                "source": "api",
            },
            request=request
        )
        
        serializer = self.get_serializer(goal)
        return Response(serializer.data, status=status.HTTP_200_OK)


class PlanViewSet(AuditMixin, viewsets.ModelViewSet):
    """
    计划视图集
    
    提供计划的CRUD操作
    """
    queryset = Plan.objects.all()
    serializer_class = PlanSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    # 修复：plan_type不是数据库字段，使用level字段替代
    # plan_type字段已在P2-1迁移中被level字段替代，保留向后兼容
    filterset_fields = ['status', 'level', 'plan_period']
    search_fields = ['plan_number', 'name']
    ordering_fields = ['created_time', 'start_time', 'end_time', 'progress']
    ordering = ['-created_time']
    
    def list(self, request, *args, **kwargs):
        """列表视图，支持向后兼容plan_type参数"""
        # 向后兼容：将plan_type参数映射到level参数
        if 'plan_type' in request.query_params:
            plan_type_value = request.query_params.get('plan_type')
            # plan_type到level的映射
            plan_type_to_level_map = {
                'company': 'company',
                'personal': 'personal',
                'department': 'company',  # 部门计划映射为公司计划
                'project': 'company',     # 项目计划映射为公司计划
            }
            mapped_level = plan_type_to_level_map.get(plan_type_value)
            if mapped_level:
                # 创建新的QueryDict，添加level参数
                from django.http import QueryDict
                new_params = request.query_params.copy()
                new_params['level'] = mapped_level
                # 移除plan_type参数，避免重复过滤
                new_params.pop('plan_type', None)
                # 修改request的query_params
                request._request.GET = new_params
                request._full_cache = {}
        
        return super().list(request, *args, **kwargs)

    def _require_change_perm(self, request, perm):
        """
        B2-1: 统一检查 change 权限
        
        Args:
            request: HttpRequest 对象
            perm: 权限代码名，例如 'plan_management.change_plan'
        
        Raises:
            PermissionDenied: 如果用户没有权限
        """
        if request.user.is_superuser:
            return
        if not request.user.has_perm(perm):
            raise PermissionDenied(f"缺少权限: {perm}")

    def _require_approve_perm(self, request, perm):
        """
        B3-3: 统一检查审批权限
        
        Args:
            request: HttpRequest 对象
            perm: 权限代码名，例如 'plan_management.approve_plan'
        
        Raises:
            PermissionDenied: 如果用户没有权限
        """
        if request.user.is_superuser:
            return
        if not request.user.has_perm(perm):
            raise PermissionDenied(f"缺少审批权限: {perm}")

    def _get_profile_org(self):
        """获取当前用户的公司/部门信息"""
        user = getattr(self.request, "user", None)
        if not user or not user.is_authenticated:
            return None, None
        profile = getattr(user, "profile", None)
        if not profile:
            return None, None
        return getattr(profile, "company", None), getattr(profile, "department", None)

    def get_queryset(self):
        """获取查询集"""
        qs = super().get_queryset()
        user = self.request.user
        if not user.is_authenticated:
            return qs.none()
        if user.is_superuser:
            return qs
        company, _dept = self._get_profile_org()
        if not company:
            return qs.none()
        qs = qs.filter(company=company)
        
        # A3-3-7: 使用统一的筛选逻辑
        spec = ListFilterSpec.from_params(self.request.query_params, allow_overdue=True)
        qs = apply_range(qs, "created_time", spec.range)
        qs = apply_mine_participating(qs, user, spec.mine, spec.participating)
        qs = apply_overdue(qs, spec.overdue)
        
        # 默认排序：离现在最近/最新
        return qs.order_by("-created_time", "-id")

    def perform_create(self, serializer):
        """创建计划时自动赋值 company/org_department"""
        user = self.request.user
        company, dept = self._get_profile_org()

        # 第二刀：卡住项过多时禁止新增
        from backend.apps.plan_management.views_pages import get_blocked_count_for_user
        
        creator = user
        owner = serializer.validated_data.get('responsible_person')
        
        creator_blocked = get_blocked_count_for_user(creator)
        owner_blocked = get_blocked_count_for_user(owner) if owner else 0
        
        if creator_blocked >= 5:
            raise ValidationError(f'您当前有 {creator_blocked} 个卡住事项，请先处理后再创建新计划。')
        elif owner_blocked >= 5:
            raise ValidationError(f'负责人当前有 {owner_blocked} 个卡住事项，请先处理后再创建新计划。')

        extra = {}
        # 普通用户：强制继承（防止前端乱传穿透）
        if not user.is_superuser:
            if not company:
                raise PermissionDenied("用户未绑定公司，禁止创建。")
            extra["company"] = company
            extra["org_department"] = dept
            serializer.save(**extra)
            return

        # 超管：允许代录，但若前端未传则用 profile 默认
        if company and not serializer.validated_data.get("company"):
            extra["company"] = company
        if dept and not serializer.validated_data.get("org_department"):
            extra["org_department"] = dept
        serializer.save(**extra)

    ORG_FIELDS = ("company", "org_department")

    def _reject_org_change_if_needed(self, instance, serializer):
        """检查并拒绝普通用户修改归属字段"""
        user = self.request.user
        if user.is_superuser:
            return  # 超管允许

        # 普通用户禁止改归属
        incoming_company = serializer.validated_data.get("company", None)
        incoming_dept = serializer.validated_data.get("org_department", None)

        if incoming_company and instance.company_id != incoming_company.id:
            raise PermissionDenied("禁止修改 company")
        if incoming_dept and instance.org_department_id != incoming_dept.id:
            raise PermissionDenied("禁止修改 org_department")

    def perform_update(self, serializer):
        """更新计划时保护归属字段并重算状态"""
        instance = self.get_object()
        self._reject_org_change_if_needed(instance, serializer)

        # P1: 硬拒绝直接修改 status
        if "status" in self.request.data:
            raise ValidationError("status 禁止直接修改，请使用裁决接口（start-request/cancel-request + decide）")

        user = self.request.user
        old_company_id = instance.company_id
        old_dept_id = instance.org_department_id
        old_status = instance.status
        old_progress = instance.progress

        # A3-3-5 重算状态（如果进度或时间字段变更）
        validated_data = serializer.validated_data
        should_recalc = any(key in validated_data for key in ['progress', 'start_time', 'end_time'])
        
        obj = serializer.save()
        
        status_result = None
        if should_recalc:
            # 使用保存前的旧状态进行重算（因为 serializer.save() 可能已经更新了状态）
            status_result = recalc_plan_status(obj, old_status=old_status)
            if status_result.changed:
                # 字段治理说明：这是 status 字段的写入口之一（recalc 自动更新）。
                # 现状：会自动创建 StatusLog（见下行），但直接 save(update_fields=["status"]) 可能绕过部分校验。
                obj.save(update_fields=["status"])
                # 记录状态日志
                PlanStatusLog.objects.create(
                    plan=obj,
                    old_status=status_result.old,
                    new_status=status_result.new,
                    changed_by=user,
                    change_reason='进度/时间更新自动触发状态重算'
                )

        # 普通用户：如果为空才补齐（不覆盖）
        if not user.is_superuser:
            company, dept = self._get_profile_org()
            changed = False
            if not obj.company_id and company:
                obj.company = company
                changed = True
            if not obj.org_department_id and dept:
                obj.org_department = dept
                changed = True
            if changed:
                obj.save(update_fields=["company", "org_department"])
            
            # A3-3-5 写入 AuditLog（如果状态变更）
            if status_result and status_result.changed:
                changes = {
                    "status": {"from": status_result.old, "to": status_result.new}
                }
                if old_progress != obj.progress:
                    changes["progress"] = {"from": float(old_progress) if old_progress else 0, "to": float(obj.progress) if obj.progress else 0}
                
                audit_action = get_audit_action()
                if audit_action:
                    safe_audit_log(
                        actor=user,
                        action=audit_action.PLAN_ACTION,
                        object_type=f"{obj._meta.app_label}.{obj.__class__.__name__}",
                        object_id=str(obj.pk),
                        changes=changes,
                        meta={
                            "event": "progress_update",
                            "ip": self.request.META.get("REMOTE_ADDR"),
                            "ua": self.request.META.get("HTTP_USER_AGENT"),
                        },
                    )
            return

        # 超管：如果改了归属，写 AuditLog
        changes = {}
        if old_company_id != obj.company_id:
            changes["company"] = {"from": old_company_id, "to": obj.company_id}
        if old_dept_id != obj.org_department_id:
            changes["org_department"] = {"from": old_dept_id, "to": obj.org_department_id}
        
        # 如果状态变更，也记录
        if status_result and status_result.changed:
            if "status" not in changes:
                changes["status"] = {"from": status_result.old, "to": status_result.new}
            else:
                changes["status"] = {"from": status_result.old, "to": status_result.new}
            if old_progress != obj.progress:
                changes["progress"] = {"from": float(old_progress) if old_progress else 0, "to": float(obj.progress) if obj.progress else 0}

        if changes:
            audit_action = get_audit_action()
            if audit_action:
                safe_audit_log(
                    actor=user,
                    action=audit_action.ORG_CHANGE,
                    object_type=f"{obj._meta.app_label}.{obj.__class__.__name__}",
                    object_id=str(obj.pk),
                    changes=changes,
                    meta={
                        "ip": self.request.META.get("REMOTE_ADDR"),
                        "ua": self.request.META.get("HTTP_USER_AGENT"),
                    },
                )


    @action(detail=True, methods=['post'], url_path='progress')
    def update_progress(self, request, pk=None):
        """
        更新计划进度
        
        POST /api/plan/plans/{id}/progress/
        Body: {
            "progress": 50,
            "progress_description": "已完成第一阶段工作",
            "execution_result": "执行顺利",
            "execution_issues": "",
            "notes": "备注信息"
        }
        """
        # B2-1: 统一检查 change 权限
        self._require_change_perm(request, "plan_management.change_plan")
        
        # B2-2: 使用 get_object() 确保只能操作本公司数据（已在 get_queryset 中过滤）
        plan = self.get_object()
        user = request.user
        
        # 业务权限检查：负责人或参与人可以更新进度（在 change 权限基础上）
        if not user.is_superuser:
            if plan.responsible_person != user and user not in plan.participants.all():
                raise PermissionDenied("只有负责人或参与人可以更新进度")
        
        # 获取请求数据
        progress = request.data.get('progress')
        progress_description = request.data.get('progress_description', '')
        execution_result = request.data.get('execution_result', '')
        execution_issues = request.data.get('execution_issues', '')
        notes = request.data.get('notes', '')
        
        # 验证进度值
        if progress is None:
            raise ValidationError("progress 字段是必填项")
        
        try:
            progress = float(progress)
            if progress < 0 or progress > 100:
                raise ValidationError("进度必须在 0-100 之间")
        except (ValueError, TypeError):
            raise ValidationError("进度必须是数字")
        
        if not progress_description:
            raise ValidationError("progress_description 字段是必填项")
        
        # 记录旧值
        old_progress = plan.progress
        old_status = plan.status
        
        # 更新计划进度
        plan.progress = progress
        plan.save(update_fields=['progress'])
        
        # 创建进度记录
        progress_record = PlanProgressRecord.objects.create(
            plan=plan,
            progress=progress,
            progress_description=progress_description,
            execution_result=execution_result,
            execution_issues=execution_issues,
            recorded_by=user,
            notes=notes,
        )
        
        # 重算状态（如果进度变化可能触发状态变化）
        status_result = recalc_plan_status(plan, old_status=old_status)
        if status_result.changed:
            # 字段治理说明：这是 status 字段的写入口之一（进度更新触发状态重算）。
            # 现状：会自动创建 StatusLog（见下行），然后 save(update_fields=['status'])。
            plan.save(update_fields=['status'])
            # 记录状态日志
            PlanStatusLog.objects.create(
                plan=plan,
                old_status=status_result.old,
                new_status=status_result.new,
                changed_by=user,
                change_reason='进度更新自动触发状态重算'
            )
        
        # B2-3: 记录审计日志（统一 meta 结构）
        changes = {
            "progress": {"from": float(old_progress) if old_progress else 0, "to": float(progress)}
        }
        if status_result.changed:
            changes["status"] = {"from": status_result.old, "to": status_result.new}
        
        audit_plan_event(
            actor=user,
            plan=plan,
            event="progress_update",
            changes=changes,
            meta={
                "event": "progress_update",
                "progress_record_id": progress_record.id,
                "progress_description": progress_description[:200],
                "source": "api",
            },
            request=request
        )
        
        # 返回更新后的计划
        serializer = self.get_serializer(plan)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='status')
    def change_status(self, request, pk=None):
        """
        P1 v2: 接口已废弃
        
        手动变更计划状态的功能已废弃，请使用 PlanDecision 裁决机制：
        - 启动计划：POST /api/plan/plans/{id}/start-request/ + POST /api/plan/plan-decisions/{id}/decide/
        - 取消计划：POST /api/plan/plans/{id}/cancel-request/ + POST /api/plan/plan-decisions/{id}/decide/
        - 完成计划：系统自动判定（progress >= 100）
        """
        return legacy_api_gone()
        
        # 以下代码已废弃，保留用于参考
        # # B2-1: 统一检查 change 权限
        # self._require_change_perm(request, "plan_management.change_plan")
        
        # B2-2: 使用 get_object() 确保只能操作本公司数据（已在 get_queryset 中过滤）
        plan = self.get_object()
        user = request.user
        
        # 业务权限检查：负责人可以变更状态（在 change 权限基础上）
        if not user.is_superuser:
            if plan.responsible_person != user:
                raise PermissionDenied("只有负责人可以变更状态")
        
        # 获取请求数据
        new_status = request.data.get('status')
        reason = request.data.get('reason', '手动状态变更')
        
        if not new_status:
            raise ValidationError("status 字段是必填项")
        
        # 验证状态转换是否合法
        # W1-Fix-3: 超管也必须遵守状态转换规则
        if new_status == plan.status:
            raise ValidationError("状态未发生变化")
        
        valid_transitions = plan.get_valid_transitions()
        status_choices = dict(plan._meta.get_field('status').choices)
        
        if new_status not in valid_transitions:
            valid_display = [status_choices.get(t, t) for t in valid_transitions]
            new_status_display = status_choices.get(new_status, new_status)
            raise ValidationError(
                f"无法从 {plan.get_status_display()} 转换到 {new_status_display}。"
                f"允许的转换：{', '.join(valid_display)}"
            )
        
        # 第二刀：卡住项推进时必须填写处理说明
        is_blocked, handling_note = _require_handling_note_if_blocked(plan, request)
        # 如果卡住，优先使用 handling_note；否则使用 reason
        if is_blocked and handling_note:
            reason = handling_note
        
        # P1: 状态变更必须通过裁决器
        # 注意：change_status API 在 P1 阶段应该被限制使用
        # 因为状态应该由裁决器根据 decision 和 system_facts 决定
        # 这里暂时保留，但应该通过裁决器处理
        result = adjudicate_plan_status(plan, decision=None, system_facts=None)
        if result.new_status != new_status:
            raise ValidationError(f"状态变更不符合裁决规则：期望 {new_status}，裁决结果为 {result.new_status}。原因：{result.reason}")
        
        old_status = result.old_status
        plan.status = result.new_status
        plan.save(update_fields=['status'])
        
        # 记录状态日志
        PlanStatusLog.objects.create(
            plan=plan,
            old_status=old_status,
            new_status=result.new_status,
            changed_by=user,
            change_reason=handling_note if is_blocked and handling_note else reason
        )
        
        # B2-3: 记录审计日志（统一 meta 结构）
        audit_plan_event(
            actor=user,
            plan=plan,
            event="status_change",
            changes={
                "status": {"from": old_status, "to": new_status}
            },
            meta={
                "event": "status_change",
                "reason": reason[:200],
                "source": "api",
            },
            request=request
        )
        
        # 返回更新后的计划
        serializer = self.get_serializer(plan)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='submit-approval')
    def submit_approval(self, request, pk=None):
        """
        P1 v2: 接口已废弃
        
        提交审批的功能已废弃，请使用 PlanDecision 裁决机制：
        - 启动计划：POST /api/plan/plans/{id}/start-request/ + POST /api/plan/plan-decisions/{id}/decide/
        """
        return legacy_api_gone()
        
        # 以下代码已废弃，保留用于参考
        # # B2-1: 统一检查 change 权限
        # self._require_change_perm(request, "plan_management.change_plan")
        
        # B2-2: 使用 get_object() 确保只能操作本公司数据
        plan = self.get_object()
        user = request.user
        
        # 检查当前状态是否允许提交审批
        allowed_statuses = ['draft', 'delayed', 'paused']
        if plan.status not in allowed_statuses:
            raise ValidationError(
                f"当前状态为 {plan.get_status_display()}，无法提交审批。"
                f"允许的状态：{', '.join([dict(plan._meta.get_field('status').choices).get(s, s) for s in allowed_statuses])}"
            )
        
        # 第二刀：卡住项推进时必须填写处理说明
        is_blocked, handling_note = _require_handling_note_if_blocked(plan, request)
        comment = request.data.get('comment', '')
        # 如果卡住，优先使用 handling_note；否则使用 comment
        if is_blocked and handling_note:
            comment = handling_note
        
        old_status = plan.status
        
        # P1: 禁止直接写入 pending_approval（非法状态）
        # 提交审批应该触发审批流程，但不直接改状态
        # 状态变更必须通过裁决器
        # plan.status = 'pending_approval'  # ❌ 已删除：非法状态写入
        # plan.save(update_fields=['status'])
        
        # 尝试创建工作流实例（路径 A：先业务内置，工作流只做通知/留痕）
        workflow_instance_id = None
        try:
            from django.contrib.contenttypes.models import ContentType
            from backend.apps.workflow_engine.models import ApprovalInstance, WorkflowTemplate
            from backend.apps.workflow_engine.services import ApprovalEngine
            
            content_type = ContentType.objects.get_for_model(Plan)
            # 检查是否已有审批实例
            existing_instance = ApprovalInstance.objects.filter(
                content_type=content_type,
                object_id=plan.pk,
                status__in=['pending', 'in_progress']
            ).first()
            
            if not existing_instance:
                # 尝试获取计划审批流程模板
                try:
                    workflow = WorkflowTemplate.objects.filter(
                        code='plan_approval',
                        status='active'
                    ).first()
                    
                    if workflow:
                        instance = ApprovalEngine.start_approval(
                            workflow=workflow,
                            content_object=plan,
                            applicant=user,
                            comment=comment or f'用户 {user.username} 提交计划审批'
                        )
                        workflow_instance_id = instance.id
                except Exception as e:
                    logger.warning(f"创建工作流实例失败（不影响业务）：{str(e)}")
        except Exception as e:
            logger.warning(f"工作流引擎不可用（不影响业务）：{str(e)}")
        
        # 记录状态日志
        PlanStatusLog.objects.create(
            plan=plan,
            old_status=old_status,
            new_status='pending_approval',
            changed_by=user,
            change_reason=handling_note if is_blocked and handling_note else '提交审批'
        )
        
        # B2-3: 记录审计日志
        audit_plan_event(
            actor=user,
            plan=plan,
            event="submit_approval",
            changes={
                "status": {"from": old_status, "to": "pending_approval"}
            },
            meta={
                "event": "submit_approval",
                "comment": comment[:200] if comment else "",
                "workflow_instance_id": workflow_instance_id,
                "source": "api",
            },
            request=request
        )
        
        # C3-2: 通知审批人
        notify_approvers(plan, 'submit', user, comment)
        
        serializer = self.get_serializer(plan)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='approve')
    def approve(self, request, pk=None):
        """
        P1 v2: 接口已废弃
        
        审批通过的功能已废弃，请使用 PlanDecision 裁决机制：
        - 裁决启动请求：POST /api/plan/plan-decisions/{decision_id}/decide/ (approve=true)
        """
        return legacy_api_gone()
        
        # 以下代码已废弃，保留用于参考
        # # B3-3: 检查审批权限
        # self._require_approve_perm(request, "plan_management.approve_plan")
        
        # B2-2: 使用 get_object() 确保只能操作本公司数据
        plan = self.get_object()
        user = request.user
        
        # P1: 审批通过必须通过裁决器
        # 检查当前状态（P1 不认 pending_approval，改为检查 draft）
        if plan.status != 'draft':
            raise ValidationError(f"当前状态为 {plan.get_status_display()}，无法审批。只有草稿状态的计划才能审批。")
        
        # 第二刀：卡住项推进时必须填写处理说明
        is_blocked, handling_note = _require_handling_note_if_blocked(plan, request)
        comment = request.data.get('comment', '')
        # 如果卡住，优先使用 handling_note；否则使用 comment
        if is_blocked and handling_note:
            comment = handling_note
        
        # P1: 通过裁决器处理审批通过
        result = adjudicate_plan_status(plan, decision='approve', system_facts=None)
        old_status = result.old_status
        plan.status = result.new_status
        plan.save(update_fields=['status'])
        
        # 第四刀：先记录审批通过日志（第一条日志，不覆盖）
        # 第二刀：如果卡住，使用 handling_note；否则使用原有格式
        if is_blocked and handling_note:
            approval_reason = handling_note[:500]
        else:
            approval_reason = f'审批通过{": " + comment if comment else ""}'[:500]
        
        PlanStatusLog.objects.create(
            plan=plan,
            old_status=old_status,
            new_status='in_progress',  # 审批后的状态是 in_progress
            changed_by=user,
            change_reason=approval_reason
        )
        
        # 尝试更新工作流实例（路径 A：业务回写状态，然后通知工作流）
        workflow_instance_id = None
        try:
            from django.contrib.contenttypes.models import ContentType
            from backend.apps.workflow_engine.models import ApprovalInstance
            
            content_type = ContentType.objects.get_for_model(Plan)
            instance = ApprovalInstance.objects.filter(
                content_type=content_type,
                object_id=plan.pk,
                status__in=['pending', 'in_progress']
            ).first()
            
            if instance:
                workflow_instance_id = instance.id
                # 尝试完成审批节点（如果工作流引擎支持）
                try:
                    from backend.apps.workflow_engine.services import ApprovalEngine
                    ApprovalEngine.approve_node(
                        instance=instance,
                        approver=user,
                        comment=comment or '审批通过'
                    )
                except Exception as e:
                    logger.warning(f"更新工作流节点失败（不影响业务）：{str(e)}")
        except Exception as e:
            logger.warning(f"工作流引擎不可用（不影响业务）：{str(e)}")
        
        # 第四刀：调用 recalc_plan_status 做纠偏（可能自动完成）
        # 第四刀修正：完成日志统一由 Plan.save() 兜底保证，避免重复写 log。
        # 如果状态变为 completed，Plan.save() 会自动写 completed log，并记录审批人作为责任人。
        status_result = recalc_plan_status(plan, old_status='in_progress')
        if status_result.changed:
            # 如果变为 completed，传递审批人信息给 Plan.save()，确保责任可归属
            if status_result.should_log and status_result.new == 'completed':
                plan.save(update_fields=['status'], trigger_user=user, change_reason_prefix='审批后状态纠偏')
            else:
                plan.save(update_fields=['status'])
        
        # B2-3: 记录审计日志
        audit_plan_event(
            actor=user,
            plan=plan,
            event="approve",
            changes={
                "status": {"from": old_status, "to": plan.status}
            },
            meta={
                "event": "approve",
                "comment": comment[:200] if comment else "",
                "workflow_instance_id": workflow_instance_id,
                "source": "api",
            },
            request=request
        )
        
        # C3-2: 通知提交人
        notify_submitter(plan, 'approve', user, comment)
        
        serializer = self.get_serializer(plan)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='reject')
    def reject(self, request, pk=None):
        """
        P1 v2: 接口已废弃
        
        审批驳回的功能已废弃，请使用 PlanDecision 裁决机制：
        - 裁决启动请求：POST /api/plan/plan-decisions/{decision_id}/decide/ (approve=false)
        """
        return legacy_api_gone()
        
        # 以下代码已废弃，保留用于参考
        # # B3-3: 检查审批权限
        # self._require_approve_perm(request, "plan_management.approve_plan")
        
        # B2-2: 使用 get_object() 确保只能操作本公司数据
        plan = self.get_object()
        user = request.user
        
        # P1: 审批驳回必须通过裁决器
        # 检查当前状态（P1 不认 pending_approval，改为检查 draft）
        if plan.status != 'draft':
            raise ValidationError(f"当前状态为 {plan.get_status_display()}，无法驳回。只有草稿状态的计划才能驳回。")
        
        # 第二刀：卡住项推进时必须填写处理说明
        is_blocked, handling_note = _require_handling_note_if_blocked(plan, request)
        reason = request.data.get('reason', '')
        # 如果卡住，优先使用 handling_note；否则使用 reason
        if is_blocked and handling_note:
            reason = handling_note
        
        # P1: 通过裁决器处理审批驳回
        result = adjudicate_plan_status(plan, decision='reject', system_facts=None)
        old_status = result.old_status
        plan.status = result.new_status
        plan.save(update_fields=['status'])
        
        # 尝试更新工作流实例（路径 A：业务回写状态，然后通知工作流）
        workflow_instance_id = None
        try:
            from django.contrib.contenttypes.models import ContentType
            from backend.apps.workflow_engine.models import ApprovalInstance
            
            content_type = ContentType.objects.get_for_model(Plan)
            instance = ApprovalInstance.objects.filter(
                content_type=content_type,
                object_id=plan.pk,
                status__in=['pending', 'in_progress']
            ).first()
            
            if instance:
                workflow_instance_id = instance.id
                # 尝试驳回审批节点（如果工作流引擎支持）
                try:
                    from backend.apps.workflow_engine.services import ApprovalEngine
                    ApprovalEngine.reject_node(
                        instance=instance,
                        approver=user,
                        comment=reason or '审批驳回'
                    )
                except Exception as e:
                    logger.warning(f"更新工作流节点失败（不影响业务）：{str(e)}")
        except Exception as e:
            logger.warning(f"工作流引擎不可用（不影响业务）：{str(e)}")
        
        # 记录状态日志
        # 第二刀：如果卡住，使用 handling_note；否则使用原有格式
        if is_blocked and handling_note:
            change_reason = handling_note
        else:
            change_reason = f'审批驳回{": " + reason if reason else ""}'
        
        PlanStatusLog.objects.create(
            plan=plan,
            old_status=old_status,
            new_status='draft',
            changed_by=user,
            change_reason=change_reason
        )
        
        # B2-3: 记录审计日志
        audit_plan_event(
            actor=user,
            plan=plan,
            event="reject",
            changes={
                "status": {"from": old_status, "to": "draft"}
            },
            meta={
                "event": "reject",
                "reason": reason[:200] if reason else "",
                "workflow_instance_id": workflow_instance_id,
                "source": "api",
            },
            request=request
        )
        
        # C3-2: 通知提交人
        notify_submitter(plan, 'reject', user, reason)
        
        serializer = self.get_serializer(plan)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='cancel-approval')
    def cancel_approval(self, request, pk=None):
        """
        P1 v2: 接口已废弃
        
        取消审批的功能已废弃，请使用 PlanDecision 裁决机制：
        - 取消计划：POST /api/plan/plans/{id}/cancel-request/ + POST /api/plan/plan-decisions/{id}/decide/
        """
        return legacy_api_gone()
        
        # 以下代码已废弃，保留用于参考
        # # B2-1: 统一检查 change 权限
        # self._require_change_perm(request, "plan_management.change_plan")
        
        # B2-2: 使用 get_object() 确保只能操作本公司数据
        plan = self.get_object()
        user = request.user
        
        # P1: 取消审批必须通过裁决器
        # 检查当前状态（P1 不认 pending_approval，改为检查 draft）
        if plan.status != 'draft':
            raise ValidationError(f"当前状态为 {plan.get_status_display()}，无法取消审批。只有草稿状态的计划才能取消审批。")
        
        # 第二刀：卡住项推进时必须填写处理说明
        is_blocked, handling_note = _require_handling_note_if_blocked(plan, request)
        reason = request.data.get('reason', '')
        # 如果卡住，优先使用 handling_note；否则使用 reason
        if is_blocked and handling_note:
            reason = handling_note
        
        # P1: 通过裁决器处理取消审批（approve_cancel）
        result = adjudicate_plan_status(plan, decision='approve_cancel', system_facts=None)
        old_status = result.old_status
        plan.status = result.new_status
        plan.save(update_fields=['status'])
        
        # 尝试取消工作流实例（路径 A：业务回写状态，然后通知工作流）
        workflow_instance_id = None
        try:
            from django.contrib.contenttypes.models import ContentType
            from backend.apps.workflow_engine.models import ApprovalInstance
            
            content_type = ContentType.objects.get_for_model(Plan)
            instance = ApprovalInstance.objects.filter(
                content_type=content_type,
                object_id=plan.pk,
                status__in=['pending', 'in_progress']
            ).first()
            
            if instance:
                workflow_instance_id = instance.id
                # 尝试取消审批流程（如果工作流引擎支持）
                try:
                    from backend.apps.workflow_engine.services import ApprovalEngine
                    ApprovalEngine.withdraw_approval(
                        instance=instance,
                        user=user,
                        comment=reason or '取消审批'
                    )
                except Exception as e:
                    logger.warning(f"取消工作流实例失败（不影响业务）：{str(e)}")
        except Exception as e:
            logger.warning(f"工作流引擎不可用（不影响业务）：{str(e)}")
        
        # 记录状态日志
        # 第二刀：如果卡住，使用 handling_note；否则使用原有格式
        if is_blocked and handling_note:
            change_reason = handling_note
        else:
            change_reason = f'取消审批{": " + reason if reason else ""}'
        
        PlanStatusLog.objects.create(
            plan=plan,
            old_status=old_status,
            new_status='draft',
            changed_by=user,
            change_reason=change_reason
        )
        
        # B2-3: 记录审计日志
        audit_plan_event(
            actor=user,
            plan=plan,
            event="cancel_approval",
            changes={
                "status": {"from": old_status, "to": "draft"}
            },
            meta={
                "event": "cancel_approval",
                "reason": reason[:200] if reason else "",
                "workflow_instance_id": workflow_instance_id,
                "source": "api",
            },
            request=request
        )
        
        serializer = self.get_serializer(plan)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], url_path="start-request")
    def start_request(self, request, pk=None):
        """
        发起启动请求
        
        POST /api/plan/plans/{id}/start-request/
        Body: {
            "reason": "启动原因（可选）"
        }
        """
        plan = self.get_object()
        try:
            decision = request_start(plan, request.user, reason=request.data.get("reason"))
        except PlanDecisionError as e:
            # P1 v2: 使用 409 Conflict 更语义化（重复请求/状态冲突）
            error_status = getattr(e, 'status_code', status.HTTP_409_CONFLICT)
            return Response({"success": False, "message": str(e)}, status=error_status)

        return Response({
            "success": True,
            "plan_id": plan.id,
            "plan_status": plan.status,
            "decision_id": decision.id,
        }, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], url_path="cancel-request")
    def cancel_request(self, request, pk=None):
        """
        发起取消请求
        
        POST /api/plan/plans/{id}/cancel-request/
        Body: {
            "reason": "取消原因（可选）"
        }
        """
        plan = self.get_object()
        try:
            decision = request_cancel(plan, request.user, reason=request.data.get("reason"))
        except PlanDecisionError as e:
            # P1 v2: 使用 409 Conflict 更语义化（重复请求/状态冲突）
            error_status = getattr(e, 'status_code', status.HTTP_409_CONFLICT)
            return Response({"success": False, "message": str(e)}, status=error_status)

        return Response({
            "success": True,
            "plan_id": plan.id,
            "plan_status": plan.status,
            "decision_id": decision.id,
        }, status=status.HTTP_201_CREATED)
