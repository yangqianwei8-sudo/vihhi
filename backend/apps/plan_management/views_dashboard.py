from __future__ import annotations

from datetime import timedelta

from django.shortcuts import render
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Max, Q, OuterRef, Subquery
from django.db.models.functions import Coalesce

from .models import Plan, PlanStatusLog, PlanProgressRecord

# 兼容导入：你们在 B1 做过 require_perm helper，但位置可能不同
try:
    # 推荐你把 require_perm 放这里（若已存在就用）
    from .permissions import require_perm  # type: ignore
except Exception:  # pragma: no cover
    from .views_pages import require_perm  # type: ignore

# 公司隔离工具（你们 A3 已抽过 apply_company_scope）
try:
    from .utils import apply_company_scope  # type: ignore
except Exception:  # pragma: no cover
    apply_company_scope = None  # type: ignore

# 导入菜单和上下文构建函数
try:
    from .views_pages import (
        _build_plan_management_sidebar_nav,
        _context,
    )
    from backend.apps.system_management.services import get_user_permission_codes
except Exception:  # pragma: no cover
    _build_plan_management_sidebar_nav = None  # type: ignore
    _context = None  # type: ignore
    get_user_permission_codes = None  # type: ignore


def _company_scope(request, qs):
    """
    最小安全：普通用户按公司隔离，超管不过滤。
    优先复用你们已有 apply_company_scope()，否则回退到最基础过滤。
    """
    user = request.user
    if getattr(user, "is_superuser", False):
        return qs

    if apply_company_scope:
        return apply_company_scope(qs, user)

    # fallback：尽量不报错（但建议优先用 apply_company_scope）
    profile = getattr(user, "profile", None)
    company = getattr(profile, "company", None) if profile else None
    if not company:
        return qs.none()
    return qs.filter(company=company)


@login_required
def plan_dashboard(request):
    """
    D1: 执行总览页
    
    只读页面 + 公司隔离 + 3 个风险表 + 4 个统计卡
    """
    # B1-2: 权限检查（返回 403，不重定向）
    # 统一使用业务权限 plan_management.view（兼容 plan_management.plan.view）
    try:
        from backend.apps.system_management.services import get_user_permission_codes
        permission_codes = get_user_permission_codes(request.user)
        from backend.core.views import _permission_granted
        if not _permission_granted('plan_management.view', permission_codes):
            raise PermissionDenied('您没有权限查看计划管理仪表板')
    except PermissionDenied as e:
        from django.contrib import messages
        from django.http import HttpResponseForbidden
        messages.error(request, str(e))
        return HttpResponseForbidden(str(e))
    
    user = request.user
    now = timezone.now()

    base_qs = Plan.objects.all().select_related("responsible_person")
    base_qs = _company_scope(request, base_qs)

    # ===== 顶部统计卡（最小：4个数字）=====
    total_count = base_qs.count()
    in_progress_count = base_qs.filter(status="in_progress").count()
    overdue_count = base_qs.filter(status="overdue").count()
    pending_count = base_qs.filter(status="pending_approval").count()

    # ===== 风险列表（最多10条）=====
    overdue_plans = (
        base_qs.filter(status="overdue")
        .order_by("end_time")[:10]
    )

    # 7天未更新（排除已完成/取消）
    # 坑2修复：用 PlanProgressRecord.recorded_time 的 max() 作为最后更新时间
    # 如果从未有进度记录，用 created_time 作为基准
    seven_days_ago = now - timedelta(days=7)
    stale_plans = (
        base_qs.exclude(status__in=["completed", "cancelled"])
        .annotate(
            last_progress_time=Max("progress_records__recorded_time")
        )
        .filter(
            Q(last_progress_time__lt=seven_days_ago) | 
            (Q(last_progress_time__isnull=True) & Q(created_time__lt=seven_days_ago))
        )
        .order_by("last_progress_time", "created_time", "end_time")[:10]
    )

    # 待审批超3天
    # 坑1修复：用 PlanStatusLog 中进入 pending_approval 的时间，而不是 Plan.created_time
    # 兜底：如果 PlanStatusLog 没有记录，用 created_time 作为基准
    three_days_ago = now - timedelta(days=3)
    # 子查询：获取每个 plan 最近一次进入 pending_approval 的时间
    pending_approval_time_subquery = PlanStatusLog.objects.filter(
        plan=OuterRef("pk"),
        new_status="pending_approval"
    ).order_by("-changed_time").values("changed_time")[:1]
    
    pending_long = (
        base_qs.filter(status="pending_approval")
        .annotate(
            pending_since=Subquery(pending_approval_time_subquery)
        )
        .annotate(
            pending_since_safe=Coalesce("pending_since", "created_time")
        )
        .filter(pending_since_safe__lt=three_days_ago)
        .order_by("pending_since_safe")[:10]  # 按进入 pending_approval 时间最早的在前
    )

    # 构建上下文（如果可用，添加菜单支持）
    if _context and get_user_permission_codes:
        context = _context(
            page_title="执行总览",
            page_icon="📊",
            description="查看计划执行情况和风险预警",
            request=request,
        )
    else:
        context = {}
    
    # 添加数据
    context.update({
        "now": now,
        "cards": {
            "total": total_count,
            "in_progress": in_progress_count,
            "overdue": overdue_count,
            "pending": pending_count,
        },
        "overdue_plans": overdue_plans,
        "stale_plans": stale_plans,
        "pending_long": pending_long,
    })
    
    return render(request, "plan_management/plan_dashboard.html", context)

