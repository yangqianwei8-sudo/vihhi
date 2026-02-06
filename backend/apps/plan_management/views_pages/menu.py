# 计划管理 - 菜单与权限过滤、上下文
from django.db.models import Q
from django.shortcuts import get_object_or_404

from backend.apps.system_management.services import get_user_permission_codes
from backend.core.views import _permission_granted, _build_full_top_nav

from .common import _build_unified_sidebar_nav, Plan, PlanDecision, StrategicGoal


# 计划管理菜单结构定义（简化：单子项分组已展平为顶级项）
PLAN_MANAGEMENT_MENU_STRUCTURE = [
    {'id': 'plan_home', 'label': '首页', 'icon': '🏠', 'url_name': 'plan_pages:plan_management_home', 'permission': 'plan_management.view'},
    {'id': 'strategic_goal_list', 'label': '目标列表', 'icon': '🎯', 'url_name': 'plan_pages:strategic_goal_list', 'permission': ['plan_management.manage_goal', 'plan_management.goal.view_assigned', 'plan_management.goal.view_all']},
    {'id': 'plan_list', 'label': '计划列表', 'icon': '📅', 'url_name': 'plan_pages:plan_list', 'permission': 'plan_management.view'},
    {
        'id': 'plan_analysis',
        'label': '分析报表',
        'icon': '📈',
        'permission': 'plan_management.view_analysis',
        'expanded': True,
        'children': [
            {'id': 'plan_completion_analysis', 'label': '完成度分析', 'icon': '✅', 'url_name': 'plan_pages:plan_completion_analysis', 'permission': 'plan_management.view_analysis'},
            {'id': 'plan_goal_achievement', 'label': '目标达成分析', 'icon': '🎯', 'url_name': 'plan_pages:plan_goal_achievement', 'permission': 'plan_management.view_analysis'},
            {'id': 'plan_statistics', 'label': '统计报表', 'icon': '📊', 'url_name': 'plan_pages:plan_statistics', 'permission': 'plan_management.view_analysis'},
        ]
    },
    {'id': 'todo_task_list', 'label': '待办列表', 'icon': '📝', 'url_name': 'plan_pages:todo_task_list', 'permission': 'plan_management.view'},
]


def _build_plan_management_menu(permission_set, active_id=None):
    """生成计划管理模块左侧菜单（统一格式，兼容旧接口）"""
    return _build_plan_management_sidebar_nav(permission_set, request_path=None, active_id=active_id)


def _build_plan_management_sidebar_nav(permission_set, request_path=None, active_id=None):
    """生成计划管理左侧菜单（统一格式）"""
    return _build_unified_sidebar_nav(PLAN_MANAGEMENT_MENU_STRUCTURE, permission_set, active_id=active_id)


def _filter_plans_by_permission(plans, user, permission_set):
    """根据用户权限过滤计划列表"""
    if not user or not getattr(user, 'is_authenticated', False):
        return plans.none()
    if getattr(user, 'is_superuser', False):
        return plans
    if 'plan_management.plan.view_all' in permission_set:
        return plans
    return plans.filter(Q(responsible_person=user) | Q(owner=user)).distinct()


def get_plan_qs_for_user(request):
    """统一计划查询集：先公司隔离，再权限过滤。"""
    from backend.apps.plan_management.utils import apply_company_scope
    permission_set = get_user_permission_codes(request.user)
    qs = Plan.objects.all()
    qs = apply_company_scope(qs, request.user)
    return _filter_plans_by_permission(qs, request.user, permission_set)


def get_plan_or_404(request, plan_id):
    """取当前用户可见范围内的计划，否则 404。"""
    return get_object_or_404(get_plan_qs_for_user(request), id=plan_id)


def get_pending_decision_or_404(request, decision_id):
    """取当前用户可见计划范围内的待裁决决策，否则 404。"""
    allowed_plan_ids = get_plan_qs_for_user(request).values_list('id', flat=True)
    return get_object_or_404(
        # G1-4: PlanDecision 已退场，不再作为待办来源
        # 待办统一使用 ApprovalInstance（审批引擎）
        # 历史 PlanDecision 数据保留为只读，不在此处查询
        [],
        id=decision_id
    )


def get_goal_qs_for_user(request):
    """统一目标查询集：先按部门公司隔离，再复用 goal_list 的权限过滤逻辑。"""
    from backend.apps.plan_management.utils import apply_goal_company_scope
    permission_set = get_user_permission_codes(request.user)
    goals = StrategicGoal.objects.all()
    goals = apply_goal_company_scope(goals, request.user)  # 目标按部门公司隔离
    has_view_all = _permission_granted('plan_management.goal.view_all', permission_set)
    has_view_assigned = _permission_granted('plan_management.goal.view_assigned', permission_set)
    if has_view_all:
        return goals
    if has_view_assigned:
        return goals.filter(
            Q(responsible_person=request.user) |
            Q(owner=request.user) |
            Q(participants=request.user) |
            Q(level='company')
        ).distinct()
    return goals.filter(
        Q(level='company') |
        Q(responsible_person=request.user) |
        Q(owner=request.user) |
        Q(participants=request.user)
    ).distinct()


def _context(page_title, page_icon, description, summary_cards=None, sections=None, request=None):
    """生成页面上下文"""
    context = {
        'page_title': page_title,
        'page_icon': page_icon,
        'description': description,
        'summary_cards': summary_cards or [],
        'sections': sections or [],
    }
    if request and request.user.is_authenticated:
        permission_set = get_user_permission_codes(request.user)
        context['full_top_nav'] = _build_full_top_nav(permission_set, request.user)
        context['sidebar_nav'] = _build_plan_management_sidebar_nav(permission_set, request.path)
        context['sidebar_title'] = '计划管理'
        context['sidebar_subtitle'] = 'Plan Management'
    else:
        context['full_top_nav'] = []
        context['sidebar_nav'] = []
    return context
