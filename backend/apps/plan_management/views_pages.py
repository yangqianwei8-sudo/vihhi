"""
计划管理模块页面视图
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse, NoReverseMatch
from django.core.paginator import Paginator
from django.db.models import Q, Count, Sum
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from decimal import Decimal, InvalidOperation
from backend.apps.system_management.services import get_user_permission_codes
from backend.apps.system_management.models import User, Department

# P1: 兼容导入，避免 core.views 变更导致 plan_management 无法启动
try:
    from backend.core.views import _permission_granted, _build_full_top_nav, _build_unified_sidebar_nav
except ImportError:
    # Fallback: 如果 _build_unified_sidebar_nav 不存在，提供简单实现
    from backend.core.views import _permission_granted, _build_full_top_nav
    
    def _build_unified_sidebar_nav(menu_structure, permission_set, active_id=None):
        """Fallback: 简单的侧边栏菜单构建函数"""
        nav = []
        for item in menu_structure:
            if item.get('permission'):
                if not _permission_granted(item['permission'], permission_set):
                    continue
            nav_item = {
                'label': item.get('label', ''),
                'icon': item.get('icon', ''),
                'url': item.get('url', '#'),
                'active': item.get('id') == active_id if active_id else False,
            }
            if 'children' in item:
                nav_item['children'] = _build_unified_sidebar_nav(item['children'], permission_set, active_id)
            nav.append(nav_item)
        return nav
from .models import (
    StrategicGoal, GoalProgressRecord, GoalAdjustment, GoalStatusLog,
    Plan, PlanProgressRecord, PlanIssue, PlanStatusLog, PlanDecision
)
from .forms import (
    StrategicGoalForm, GoalProgressUpdateForm, GoalAdjustmentForm,
    PlanForm, PlanProgressUpdateForm, PlanIssueForm
)
from .adjudicator import adjudicate_plan_status


# ==================== 菜单结构定义 ====================

PLAN_MANAGEMENT_MENU = [
    {
        'id': 'strategic_goal',
        'label': '战略目标',
        'icon': '🎯',
        'permission': 'plan_management.manage_goal',
        'children': [
            {
                'id': 'strategic_goal_list',
                'label': '目标制定',
                'icon': '🎯',
                'url_name': 'plan_pages:strategic_goal_list',
                'permission': 'plan_management.manage_goal',
            },
            {
                'id': 'strategic_goal_decompose',
                'label': '目标分解',
                'icon': '📊',
                'url_name': 'plan_pages:strategic_goal_decompose_entry',
                'permission': 'plan_management.manage_goal',
            },
            {
                'id': 'strategic_goal_track',
                'label': '目标跟踪',
                'icon': '📈',
                'url_name': 'plan_pages:strategic_goal_track_entry',
                'permission': 'plan_management.manage_goal',
            },
        ]
    },
    {
        'id': 'plan_management',
        'label': '计划管理',
        'icon': '📋',
        'permission': 'plan_management.view',
        'children': [
            {
                'id': 'plan_list',
                'label': '计划列表',
                'icon': '📋',
                'url_name': 'plan_pages:plan_list',
                'permission': 'plan_management.view',
            },
            {
                'id': 'plan_decompose',
                'label': '计划分解',
                'icon': '📊',
                'url_name': 'plan_pages:plan_decompose_entry',
                'permission': 'plan_management.view',
            },
            {
                'id': 'plan_goal_alignment',
                'label': '目标对齐',
                'icon': '🔗',
                'url_name': 'plan_pages:plan_goal_alignment',
                'permission': 'plan_management.view',
            },
            {
                'id': 'plan_approval',
                'label': '计划审批',
                'icon': '📝',
                'url_name': 'plan_pages:plan_approval_list',
                'permission': 'plan_management.approve',
            },
        ]
    },
    {
        'id': 'plan_execution',
        'label': '计划执行',
        'icon': '✅',
        'permission': 'plan_management.view',
        'children': [
            {
                'id': 'plan_execution_track',
                'label': '执行跟踪',
                'icon': '📊',
                'url_name': 'plan_pages:plan_execution_track',
                'permission': 'plan_management.view',
            },
            {
                'id': 'plan_progress_update',
                'label': '进度更新',
                'icon': '📈',
                'url_name': 'plan_pages:plan_progress_update',
                'permission': 'plan_management.view',
            },
            {
                'id': 'plan_issue_list',
                'label': '问题管理',
                'icon': '⚠️',
                'url_name': 'plan_pages:plan_issue_list',
                'permission': 'plan_management.view',
            },
            {
                'id': 'plan_complete',
                'label': '计划完成情况',
                'icon': '✅',
                'url_name': 'plan_pages:plan_complete',
                'permission': 'plan_management.view',
            },
        ]
    },
    {
        'id': 'plan_analysis',
        'label': '计划分析',
        'icon': '📈',
        'permission': 'plan_management.view',
        'children': [
            {
                'id': 'plan_completion_analysis',
                'label': '完成分析',
                'icon': '📊',
                'url_name': 'plan_pages:plan_completion_analysis',
                'permission': 'plan_management.view',
            },
            {
                'id': 'plan_goal_achievement',
                'label': '目标达成',
                'icon': '🎯',
                'url_name': 'plan_pages:plan_goal_achievement',
                'permission': 'plan_management.view',
            },
            {
                'id': 'plan_statistics',
                'label': '计划统计',
                'icon': '📈',
                'url_name': 'plan_pages:plan_statistics',
                'permission': 'plan_management.view',
            },
        ]
    },
]


# ==================== 菜单生成函数 ====================

def _build_plan_management_menu(permission_set, active_id=None):
    """生成计划管理模块左侧菜单（统一格式，兼容旧接口）"""
    # 使用统一的菜单构建函数
    return _build_plan_management_sidebar_nav(permission_set, request_path=None, active_id=active_id)


# ==================== 辅助函数 ====================

# 计划管理菜单结构定义
PLAN_MANAGEMENT_MENU_STRUCTURE = [
    {
        'id': 'plan_home',
        'label': '计划管理首页',
        'icon': '🏠',
        'url_name': 'plan_pages:plan_management_home',
        'permission': 'plan_management.view',
    },
    {
        'id': 'strategic_goal',
        'label': '战略目标',
        'icon': '🎯',
        'permission': 'plan_management.manage_goal',
        'children': [
            {'id': 'strategic_goal_list', 'label': '目标制定', 'icon': '🎯', 'url_name': 'plan_pages:strategic_goal_list', 'permission': 'plan_management.manage_goal'},
            {'id': 'strategic_goal_decompose', 'label': '目标分解', 'icon': '📊', 'url_name': 'plan_pages:strategic_goal_decompose_entry', 'permission': 'plan_management.manage_goal'},
            {'id': 'strategic_goal_track', 'label': '目标跟踪', 'icon': '📈', 'url_name': 'plan_pages:strategic_goal_track_entry', 'permission': 'plan_management.view_goal_progress'},
        ]
    },
    {
        'id': 'plan_management',
        'label': '计划管理',
        'icon': '📅',
        'permission': 'plan_management.view',
        'children': [
            {'id': 'plan_list', 'label': '计划列表', 'icon': '📋', 'url_name': 'plan_pages:plan_list', 'permission': 'plan_management.view'},
            {'id': 'plan_create', 'label': '创建计划', 'icon': '➕', 'url_name': 'plan_pages:plan_create', 'permission': 'plan_management.create'},
            {'id': 'plan_approval', 'label': '计划审批', 'icon': '✅', 'url_name': 'plan_pages:plan_approval_list', 'permission': 'plan_management.approve'},
            {'id': 'plan_execution', 'label': '计划执行', 'icon': '🏃', 'url_name': 'plan_pages:plan_execution_track', 'permission': 'plan_management.track_execution'},
            {'id': 'plan_issues', 'label': '计划问题', 'icon': '❗', 'url_name': 'plan_pages:plan_issue_list', 'permission': 'plan_management.view_issues'},
        ]
    },
    {
        'id': 'plan_analysis',
        'label': '计划分析',
        'icon': '📈',
        'permission': 'plan_management.view_analysis',
        'children': [
            {'id': 'plan_completion_analysis', 'label': '完成度分析', 'icon': '✅', 'url_name': 'plan_pages:plan_completion_analysis', 'permission': 'plan_management.view_analysis'},
            {'id': 'plan_goal_achievement', 'label': '目标达成分析', 'icon': '🎯', 'url_name': 'plan_pages:plan_goal_achievement', 'permission': 'plan_management.view_analysis'},
            {'id': 'plan_statistics', 'label': '统计报表', 'icon': '📊', 'url_name': 'plan_pages:plan_statistics', 'permission': 'plan_management.view_analysis'},
        ]
    },
]


def _build_plan_management_sidebar_nav(permission_set, request_path=None, active_id=None):
    """生成计划管理左侧菜单（统一格式）"""
    # 使用统一的菜单构建函数
    return _build_unified_sidebar_nav(PLAN_MANAGEMENT_MENU_STRUCTURE, permission_set, active_id=active_id)


def _context(page_title, page_icon, description, summary_cards=None, sections=None, request=None):
    """
    生成页面上下文
    
    参数:
        page_title: 页面标题
        page_icon: 页面图标
        description: 页面描述
        summary_cards: 统计卡片数据（可选）
        sections: 功能区域数据（可选）
        request: 请求对象（可选）
    
    返回:
        dict: 页面上下文字典
    """
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
        context['module_sidebar_nav'] = _build_plan_management_sidebar_nav(permission_set, request.path)
    else:
        context['full_top_nav'] = []
        context['module_sidebar_nav'] = []
    
    return context


# ==================== 占位视图函数（待实现） ====================

@login_required
def plan_management_home(request):
    """计划管理首页"""
    permission_codes = get_user_permission_codes(request.user)
    today = timezone.now().date()
    this_month_start = today.replace(day=1)
    
    # 权限检查
    if not _permission_granted('plan_management.view', permission_codes):
        messages.error(request, '您没有权限访问计划管理')
        return redirect('admin:index')
    
    # 收集统计数据
    summary_cards = []
    
    try:
        # 计划统计
        total_plans = Plan.objects.count()
        active_plans = Plan.objects.filter(
            status__in=['in_progress', 'planning']
        ).count()
        # P1: 逾期功能在 P2，这里只统计进行中的计划（不区分是否逾期）
        overdue_plans = 0  # P2 功能，暂不实现
        this_month_plans = Plan.objects.filter(
            created_time__gte=this_month_start
        ).count()
        
        summary_cards.append({
            'label': '计划总数',
            'icon': '📅',
            'value': str(total_plans),
            'subvalue': f'进行中 {active_plans} 个 · 逾期 {overdue_plans} 个',
            'url': reverse('plan_pages:plan_list'),
            'variant': 'danger' if overdue_plans > 0 else 'info'
        })
        
        summary_cards.append({
            'label': '本月新增',
            'icon': '➕',
            'value': str(this_month_plans),
            'subvalue': '本月创建计划',
            'url': reverse('plan_pages:plan_list'),
            'variant': 'success'
        })
        
        # 战略目标统计
        try:
            total_goals = StrategicGoal.objects.count()
            active_goals = StrategicGoal.objects.filter(
                status__in=['in_progress', 'planning']
            ).count()
            
            summary_cards.append({
                'label': '战略目标',
                'icon': '🎯',
                'value': str(total_goals),
                'subvalue': f'进行中 {active_goals} 个',
                'url': reverse('plan_pages:strategic_goal_list'),
                'variant': 'info'
            })
        except Exception:
            pass
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception('获取统计数据失败: %s', str(e))
    
    # 快捷操作
    quick_actions = []
    
    if _permission_granted('plan_management.create', permission_codes):
        try:
            quick_actions.append({
                'label': '新建计划',
                'icon': '➕',
                'description': '创建新的工作计划',
                'url': reverse('plan_pages:plan_create'),
                'link_label': '创建计划 →'
            })
        except Exception:
            pass
    
    if _permission_granted('plan_management.manage_goal', permission_codes):
        try:
            quick_actions.append({
                'label': '新建战略目标',
                'icon': '🎯',
                'description': '创建新的战略目标',
                'url': reverse('plan_pages:strategic_goal_create'),
                'link_label': '创建目标 →'
            })
        except Exception:
            pass
    
    # 功能模块入口
    module_entries = []
    
    if _permission_granted('plan_management.view', permission_codes):
        try:
            module_entries.append({
                'label': '计划列表',
                'icon': '📋',
                'description': '查看和管理所有计划',
                'url': reverse('plan_pages:plan_list'),
                'link_label': '进入模块 →'
            })
            
            module_entries.append({
                'label': '战略目标',
                'icon': '🎯',
                'description': '管理战略目标',
                'url': reverse('plan_pages:strategic_goal_list'),
                'link_label': '进入模块 →'
            })
        except Exception:
            pass
    
    # 构建区域
    sections = []
    
    if quick_actions:
        sections.append({
            'title': '快捷操作',
            'description': '常用的快速操作入口',
            'items': quick_actions,
            'layout': 'grid'
        })
    
    if module_entries:
        sections.append({
            'title': '功能模块',
            'description': '计划管理的各个功能模块入口',
            'items': module_entries,
            'layout': 'grid'
        })
    
    # 构建上下文
    context = _context(
        page_title="计划管理",
        page_icon="📅",
        description="管理工作计划和战略目标",
        summary_cards=summary_cards,
        sections=sections,
        request=request,
    )
    
    return render(request, "plan_management/home.html", context)


@login_required
def plan_list(request):
    """计划列表页面"""
    from django.template.loader import get_template
    
    permission_set = get_user_permission_codes(request.user)
    
    # 权限检查
    if not _permission_granted('plan_management.view', permission_set):
        messages.error(request, '您没有权限访问计划管理')
        return redirect('admin:index')
    
    # 获取筛选参数
    search = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    plan_type_filter = request.GET.get('plan_type', '')
    plan_period_filter = request.GET.get('plan_period', '')
    related_goal_filter = request.GET.get('related_goal', '')
    responsible_filter = request.GET.get('responsible', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    # 查询计划
    plans = Plan.objects.select_related(
        'responsible_person', 'responsible_department', 'related_goal',
        'related_project', 'parent_plan', 'created_by'
    ).prefetch_related('participants').all()
    
    # 应用筛选
    if search:
        plans = plans.filter(
            Q(plan_number__icontains=search) |
            Q(name__icontains=search) |
            Q(responsible_person__username__icontains=search) |
            Q(responsible_person__full_name__icontains=search)
        )
    
    if status_filter:
        plans = plans.filter(status=status_filter)
    
    if plan_type_filter:
        plans = plans.filter(plan_type=plan_type_filter)
    
    if plan_period_filter:
        plans = plans.filter(plan_period=plan_period_filter)
    
    if related_goal_filter:
        plans = plans.filter(related_goal_id=related_goal_filter)
    
    if responsible_filter:
        plans = plans.filter(responsible_person_id=responsible_filter)
    
    if date_from:
        plans = plans.filter(start_time__date__gte=date_from)
    
    if date_to:
        plans = plans.filter(end_time__date__lte=date_to)
    
    # 排序
    plans = plans.order_by('-created_time')
    
    # 分页
    paginator = Paginator(plans, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # 统计信息
    total_count = Plan.objects.count()
    in_progress_count = Plan.objects.filter(status='in_progress').count()
    completed_count = Plan.objects.filter(status='completed').count()
    cancelled_count = Plan.objects.filter(status='cancelled').count()
    
    # 获取所有用户和战略目标（用于筛选）
    all_users = User.objects.filter(is_active=True).order_by('username')
    all_goals = StrategicGoal.objects.filter(
        status__in=['published', 'in_progress']
    ).order_by('name')
    
    context = _context(
        "计划列表",
        "📋",
        "查看和管理所有计划",
        request=request,
    )
    
    # 生成左侧菜单
    context['plan_menu'] = _build_plan_management_menu(
        permission_set,
        active_id='plan_list'
    )
    
    context.update({
        'plans': page_obj,
        'total_count': total_count,
        'in_progress_count': in_progress_count,
        'completed_count': completed_count,
        'cancelled_count': cancelled_count,
        'all_users': all_users,
        'all_goals': all_goals,
        'search': search,
        'status_filter': status_filter,
        'plan_type_filter': plan_type_filter,
        'plan_period_filter': plan_period_filter,
        'related_goal_filter': related_goal_filter,
        'responsible_filter': responsible_filter,
        'date_from': date_from,
        'date_to': date_to,
    })
    
    from django.template.loader import get_template
    tpl = get_template("plan_management/plan_list.html")
    print("TEMPLATE_ORIGIN =", tpl.origin.name)
    
    return render(request, "plan_management/plan_list.html", context)


@login_required
def strategic_goal_list(request):
    """战略目标列表页面"""
    permission_set = get_user_permission_codes(request.user)
    
    # 权限检查
    if not _permission_granted('plan_management.manage_goal', permission_set):
        messages.error(request, '您没有权限访问战略目标管理')
        return redirect('admin:index')
    
    # 获取筛选参数
    search = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    goal_type_filter = request.GET.get('goal_type', '')
    goal_period_filter = request.GET.get('goal_period', '')
    responsible_filter = request.GET.get('responsible', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    # 查询目标
    goals = StrategicGoal.objects.select_related(
        'responsible_person', 'responsible_department', 'parent_goal', 'created_by'
    ).prefetch_related('participants').all()
    
    # 应用筛选
    if search:
        goals = goals.filter(
            Q(goal_number__icontains=search) |
            Q(name__icontains=search) |
            Q(responsible_person__username__icontains=search) |
            Q(responsible_person__full_name__icontains=search)
        )
    
    if status_filter:
        goals = goals.filter(status=status_filter)
    
    if goal_type_filter:
        goals = goals.filter(goal_type=goal_type_filter)
    
    if goal_period_filter:
        goals = goals.filter(goal_period=goal_period_filter)
    
    if responsible_filter:
        goals = goals.filter(responsible_person_id=responsible_filter)
    
    if date_from:
        goals = goals.filter(start_date__gte=date_from)
    
    if date_to:
        goals = goals.filter(end_date__lte=date_to)
    
    # 排序
    goals = goals.order_by('-created_time')
    
    # 分页
    paginator = Paginator(goals, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # 统计信息
    total_count = StrategicGoal.objects.count()
    in_progress_count = StrategicGoal.objects.filter(status='in_progress').count()
    completed_count = StrategicGoal.objects.filter(status='completed').count()
    cancelled_count = StrategicGoal.objects.filter(status='cancelled').count()
    
    # 获取所有用户（用于筛选）
    all_users = User.objects.filter(is_active=True).order_by('username')
    
    context = _context(
        "战略目标列表",
        "🎯",
        "查看和管理所有战略目标",
        request=request,
    )
    
    # 生成左侧菜单
    context['plan_menu'] = _build_plan_management_menu(
        permission_set,
        active_id='strategic_goal_list'
    )
    
    context.update({
        'goals': page_obj,
        'total_count': total_count,
        'in_progress_count': in_progress_count,
        'completed_count': completed_count,
        'cancelled_count': cancelled_count,
        'all_users': all_users,
        'search': search,
        'status_filter': status_filter,
        'goal_type_filter': goal_type_filter,
        'goal_period_filter': goal_period_filter,
        'responsible_filter': responsible_filter,
        'date_from': date_from,
        'date_to': date_to,
    })
    
    return render(request, "plan_management/strategic_goal_list.html", context)


# ==================== 其他占位视图函数（待实现） ====================

@login_required
def plan_create(request):
    """计划创建页面"""
    permission_set = get_user_permission_codes(request.user)
    
    # 权限检查
    if not _permission_granted('plan_management.create', permission_set):
        messages.error(request, '您没有权限创建计划')
        return redirect('plan_pages:plan_list')
    
    if request.method == 'POST':
        form = PlanForm(request.POST, user=request.user)
        if form.is_valid():
            plan = form.save(commit=False)
            plan.created_by = request.user
            plan.save()
            
            # 保存多对多关系
            if 'participants' in form.cleaned_data:
                plan.participants.set(form.cleaned_data['participants'])
            
            messages.success(request, f'计划 {plan.name} 创建成功')
            return redirect('plan_pages:plan_detail', plan_id=plan.id)
        else:
            messages.error(request, '表单验证失败，请检查输入')
            # 关键：无效就回渲染，不要 redirect
            context = _context("创建计划", "➕", "创建新的工作计划", request=request)
            context['plan_menu'] = _build_plan_management_menu(permission_set, active_id='plan_create')
            context['form'] = form
            context['page_title'] = "创建计划"
            context['submit_text'] = "创建"
            return render(request, "plan_management/plan_form.html", context)
    else:
        form = PlanForm(user=request.user)
    
    context = _context("创建计划", "➕", "创建新的工作计划", request=request)
    context['plan_menu'] = _build_plan_management_menu(permission_set, active_id='plan_create')
    context['form'] = form
    context['page_title'] = "创建计划"
    context['submit_text'] = "创建"
    return render(request, "plan_management/plan_form.html", context)


@login_required
def plan_detail(request, plan_id):
    """计划详情页面"""
    permission_set = get_user_permission_codes(request.user)
    
    # 权限检查
    if not _permission_granted('plan_management.view', permission_set):
        messages.error(request, '您没有权限查看计划详情')
        return redirect('plan_pages:plan_list')
    
    plan = get_object_or_404(
        Plan.objects.select_related(
            'responsible_person', 'responsible_department', 'related_goal',
            'related_project', 'parent_plan', 'created_by'
        ).prefetch_related('participants', 'child_plans'),
        id=plan_id
    )
    
    # 获取进度记录
    progress_records = PlanProgressRecord.objects.filter(
        plan=plan
    ).select_related('recorded_by').order_by('-recorded_time')[:10]
    
    # 获取状态日志
    status_logs = PlanStatusLog.objects.filter(
        plan=plan
    ).select_related('changed_by').order_by('-changed_time')[:10]
    
    # 获取问题列表
    issues = PlanIssue.objects.filter(
        plan=plan
    ).select_related('assigned_to', 'created_by').order_by('-created_time')
    
    # 获取不作为记录（系统自动生成，只读展示）
    inactivity_logs = plan.inactivity_logs.all().order_by('-detected_at')
    
    # 获取下级计划
    child_plans = plan.child_plans.select_related(
        'responsible_person', 'responsible_department', 'related_goal'
    ).all()
    
    context = _context(
        f"计划详情 - {plan.name}",
        "📋",
        plan.name,
        request=request,
    )
    context['plan_menu'] = _build_plan_management_menu(permission_set, active_id='plan_list')
    
    # P1: 权限判断（围绕 decision 的裁决）
    can_submit_approval = (_permission_granted('plan_management.create', permission_set) or plan.responsible_person == request.user) and plan.status == 'draft'
    can_request_cancel = (_permission_granted('plan_management.create', permission_set) or plan.responsible_person == request.user) and plan.status == 'in_progress'
    
    # 检查是否存在 pending 的决策
    has_pending_start = PlanDecision.objects.filter(plan=plan, request_type='start', decided_at__isnull=True).exists()
    has_pending_cancel = PlanDecision.objects.filter(plan=plan, request_type='cancel', decided_at__isnull=True).exists()
    
    # 获取待审批的决策列表（用于审批人）
    pending_decisions = PlanDecision.objects.filter(plan=plan, decided_at__isnull=True).order_by('-requested_at')
    can_approve = _permission_granted('plan_management.approve_plan', permission_set) or request.user.is_superuser
    
    context.update({
        'plan': plan,
        'progress_records': progress_records,
        'status_logs': status_logs,
        'issues': issues,
        'child_plans': child_plans,
        'inactivity_logs': inactivity_logs,  # P2: 不作为记录
        'can_edit': _permission_granted('plan_management.create', permission_set) and plan.status == 'draft',
        'can_delete': _permission_granted('plan_management.create', permission_set) and plan.status == 'draft',
        # P1 新增权限
        'can_submit_approval': can_submit_approval and not has_pending_start,
        'can_request_cancel': can_request_cancel and not has_pending_cancel,
        'pending_decisions': pending_decisions,
        'can_approve': can_approve,
    })
    return render(request, "plan_management/plan_detail.html", context)


@login_required
def plan_edit(request, plan_id):
    """计划编辑页面"""
    permission_set = get_user_permission_codes(request.user)
    
    # 权限检查
    if not _permission_granted('plan_management.create', permission_set):
        messages.error(request, '您没有权限编辑计划')
        return redirect('plan_pages:plan_list')
    
    plan = get_object_or_404(Plan, id=plan_id)
    
    # 检查是否可以编辑
    if plan.status != 'draft':
        messages.error(request, '只有草稿状态的计划可以编辑')
        return redirect('plan_pages:plan_detail', plan_id=plan_id)
    
    if request.method == 'POST':
        form = PlanForm(request.POST, instance=plan, user=request.user)
        if form.is_valid():
            plan = form.save()
            messages.success(request, f'计划 {plan.name} 更新成功')
            return redirect('plan_pages:plan_detail', plan_id=plan.id)
        else:
            messages.error(request, '表单验证失败，请检查输入')
            # 关键：无效就回渲染，不要 redirect
            context = _context(
                f"编辑计划 - {plan.name}",
                "✏️",
                "编辑工作计划",
                request=request,
            )
            context['plan_menu'] = _build_plan_management_menu(permission_set, active_id='plan_list')
            context['form'] = form
            context['plan'] = plan
            context['page_title'] = f"编辑计划 - {plan.name}"
            context['submit_text'] = "保存"
            return render(request, "plan_management/plan_form.html", context)
    else:
        form = PlanForm(instance=plan, user=request.user)
    
    context = _context(
        f"编辑计划 - {plan.name}",
        "✏️",
        "编辑工作计划",
        request=request,
    )
    context['plan_menu'] = _build_plan_management_menu(permission_set, active_id='plan_list')
    context['form'] = form
    context['plan'] = plan
    context['page_title'] = f"编辑计划 - {plan.name}"
    context['submit_text'] = "保存"
    return render(request, "plan_management/plan_form.html", context)


@login_required
def plan_decompose_entry(request):
    """计划分解入口页面 - 显示可分解的计划列表"""
    permission_set = get_user_permission_codes(request.user)
    
    # 权限检查
    if not _permission_granted('plan_management.view', permission_set):
        messages.error(request, '您没有权限进行计划分解')
        return redirect('plan_pages:plan_list')
    
    # 获取筛选参数
    search = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    plan_type_filter = request.GET.get('plan_type', '')
    
    # 查询可分解的计划（排除已取消的计划，优先显示已审批和执行中的计划）
    plans = Plan.objects.select_related(
        'responsible_person', 'responsible_department', 'related_goal'
    ).exclude(status='cancelled')
    
    # 应用筛选
    if search:
        plans = plans.filter(
            Q(plan_number__icontains=search) |
            Q(name__icontains=search) |
            Q(responsible_person__username__icontains=search) |
            Q(responsible_person__full_name__icontains=search)
        )
    
    if status_filter:
        plans = plans.filter(status=status_filter)
    else:
        # P1: 默认只显示执行中的计划
        plans = plans.filter(status='in_progress')
    
    if plan_type_filter:
        plans = plans.filter(plan_type=plan_type_filter)
    
    # 排序：优先显示已审批和执行中的计划
    plans = plans.order_by('-status', '-created_time')
    
    # 分页
    paginator = Paginator(plans, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # 获取所有用户（用于筛选）
    all_users = User.objects.filter(is_active=True).order_by('username')
    
    context = _context(
        "计划分解",
        "📊",
        "选择要分解的计划",
        request=request,
    )
    context['plan_menu'] = _build_plan_management_menu(permission_set, active_id='plan_decompose')
    context.update({
        'plans': page_obj,
        'all_users': all_users,
        'search': search,
        'status_filter': status_filter,
        'plan_type_filter': plan_type_filter,
        'total_count': plans.count(),
    })
    return render(request, "plan_management/plan_decompose_entry.html", context)


@login_required
def plan_decompose(request, plan_id):
    """计划分解页面"""
    permission_set = get_user_permission_codes(request.user)
    
    # 权限检查
    if not _permission_granted('plan_management.view', permission_set):
        messages.error(request, '您没有权限进行计划分解')
        return redirect('plan_pages:plan_list')
    
    plan = get_object_or_404(
        Plan.objects.select_related('responsible_person', 'responsible_department', 'related_goal'),
        id=plan_id
    )
    
    # 获取所有下级计划（递归）
    def get_plan_tree(parent_plan, level=0):
        """递归获取计划树"""
        children = parent_plan.child_plans.select_related(
            'responsible_person', 'responsible_department', 'related_goal'
        ).all()
        result = [(parent_plan, level)]
        for child in children:
            result.extend(get_plan_tree(child, level + 1))
        return result
    
    plan_tree = get_plan_tree(plan)
    
    # 获取所有用户（用于创建子计划）
    users = User.objects.filter(is_active=True).order_by('username')
    
    # 获取所有部门（用于创建部门计划）
    departments = Department.objects.filter(is_active=True).order_by('name')
    
    context = _context(
        f"计划分解 - {plan.name}",
        "📊",
        "将计划分解为子计划和任务",
        request=request,
    )
    context['plan_menu'] = _build_plan_management_menu(permission_set, active_id='plan_decompose')
    context.update({
        'plan': plan,
        'plan_tree': plan_tree,
        'users': users,
        'departments': departments,
    })
    return render(request, "plan_management/plan_decompose.html", context)


@login_required
def plan_goal_alignment(request, plan_id):
    """目标对齐页面"""
    permission_set = get_user_permission_codes(request.user)
    
    # 权限检查
    if not _permission_granted('plan_management.view', permission_set):
        messages.error(request, '您没有权限查看目标对齐')
        return redirect('plan_pages:plan_list')
    
    plan = get_object_or_404(
        Plan.objects.select_related('related_goal', 'responsible_person'),
        id=plan_id
    )
    
    # 计算对齐度（简化版）
    alignment_score = plan.alignment_score
    if alignment_score == 0 and plan.related_goal:
        # 简单的对齐度计算：基于关键词匹配
        # TODO: 实现更复杂的对齐度计算算法
        alignment_score = 75  # 默认值
    
    # 对齐度分析
    alignment_analysis = ""
    if plan.related_goal:
        if alignment_score >= 80:
            alignment_analysis = "计划目标与战略目标高度对齐，能够有效支持战略目标的实现。"
        elif alignment_score >= 60:
            alignment_analysis = "计划目标与战略目标基本对齐，建议进一步优化以提升对齐度。"
        else:
            alignment_analysis = "计划目标与战略目标对齐度较低，建议重新审视计划目标或调整战略目标。"
    
    # 对齐度提升建议
    suggestions = []
    if alignment_score < 80:
        suggestions.append("检查计划目标是否与战略目标的关键指标一致")
        suggestions.append("确保计划内容能够直接或间接支持战略目标的实现")
        suggestions.append("考虑调整计划的时间安排以更好地配合战略目标的时间节点")
    
    context = _context(
        f"目标对齐 - {plan.name}",
        "🔗",
        "检查计划与战略目标的对齐情况",
        request=request,
    )
    context['plan_menu'] = _build_plan_management_menu(permission_set, active_id='plan_goal_alignment')
    context.update({
        'plan': plan,
        'alignment_score': alignment_score,
        'alignment_analysis': alignment_analysis,
        'suggestions': suggestions,
    })
    return render(request, "plan_management/plan_goal_alignment.html", context)


@login_required
def plan_approval_list(request):
    """
    P2: 计划审批列表（v2）
    展示所有待裁决 PlanDecision（decided_at is null）
    """
    from .models import PlanDecision
    
    permission_set = get_user_permission_codes(request.user)
    can_approve = _permission_granted('plan_management.approve_plan', permission_set) or request.user.is_superuser
    
    pending_decisions = (
        PlanDecision.objects
        .filter(decided_at__isnull=True)
        .select_related("plan", "requested_by", "plan__responsible_person", "plan__created_by")
        .order_by("-requested_at")
    )
    
    # 统计信息
    pending_count = pending_decisions.filter(request_type='start').count()
    cancel_count = pending_decisions.filter(request_type='cancel').count()
    
    context = _context(
        "计划审批列表",
        "✅",
        "待裁决的计划请求",
        request=request,
    )
    context['plan_menu'] = _build_plan_management_menu(permission_set, active_id='plan_approval')
    context.update({
        "pending_decisions": pending_decisions,
        "can_approve": can_approve,
        "pending_count": pending_count,
        "cancel_count": cancel_count,
    })
    return render(request, "plan_management/plan_approval_list.html", context)


@login_required
def plan_execution_track(request, plan_id):
    """计划执行跟踪页面"""
    permission_set = get_user_permission_codes(request.user)
    
    # 权限检查
    if not _permission_granted('plan_management.view', permission_set):
        messages.error(request, '您没有权限跟踪计划执行')
        return redirect('plan_pages:plan_list')
    
    plan = get_object_or_404(
        Plan.objects.select_related(
            'responsible_person', 'responsible_department', 'related_goal', 'parent_plan'
        ),
        id=plan_id
    )
    
    # 获取所有进度记录
    progress_records = PlanProgressRecord.objects.filter(
        plan=plan
    ).select_related('recorded_by').order_by('-recorded_time')
    
    # 获取问题列表
    issues = PlanIssue.objects.filter(
        plan=plan
    ).select_related('assigned_to', 'created_by').order_by('-created_time')
    
    # 获取状态日志
    status_logs = PlanStatusLog.objects.filter(
        plan=plan
    ).select_related('changed_by').order_by('-changed_time')
    
    # 计算进度趋势（用于图表）
    progress_trend = []
    for record in progress_records[:30]:  # 最近30条记录
        progress_trend.append({
            'date': record.recorded_time.strftime('%Y-%m-%d'),
            'value': float(record.progress),
        })
    progress_trend.reverse()  # 按时间正序
    
    # 进度更新表单
    progress_form = PlanProgressUpdateForm(plan=plan)
    
    # 问题表单
    issue_form = PlanIssueForm(plan=plan, user=request.user)
    
    # 处理进度更新
    if request.method == 'POST' and 'update_progress' in request.POST:
        progress_form = PlanProgressUpdateForm(request.POST, plan=plan)
        if progress_form.is_valid():
            record = progress_form.save(commit=False)
            record.recorded_by = request.user
            record.save()
            messages.success(request, '进度更新成功')
            return redirect('plan_pages:plan_execution_track', plan_id=plan_id)
    
    # 处理问题创建
    if request.method == 'POST' and 'create_issue' in request.POST:
        issue_form = PlanIssueForm(request.POST, plan=plan, user=request.user)
        if issue_form.is_valid():
            issue = issue_form.save(commit=False)
            issue.created_by = request.user
            issue.save()
            messages.success(request, '问题创建成功')
            return redirect('plan_pages:plan_execution_track', plan_id=plan_id)
    
    # 处理状态转换
    if request.method == 'POST' and 'transition_status' in request.POST:
        new_status = request.POST.get('new_status')
        try:
            plan.transition_to(new_status, user=request.user)
            messages.success(request, f'计划状态已更新为：{plan.get_status_display()}')
            return redirect('plan_pages:plan_execution_track', plan_id=plan_id)
        except ValueError as e:
            messages.error(request, str(e))
    
    # 处理计划完成确认
    if request.method == 'POST' and 'complete_plan' in request.POST:
        if plan.status == 'in_progress':
            plan.transition_to('completed', user=request.user)
            messages.success(request, '计划已完成')
            return redirect('plan_pages:plan_execution_track', plan_id=plan_id)
        else:
            messages.error(request, '只有执行中的计划可以完成')
    
    context = _context(
        f"执行跟踪 - {plan.name}",
        "📊",
        "跟踪计划的执行情况",
        request=request,
    )
    context['plan_menu'] = _build_plan_management_menu(permission_set, active_id='plan_execution_track')
    context.update({
        'plan': plan,
        'progress_records': progress_records,
        'issues': issues,
        'status_logs': status_logs,
        'progress_trend': progress_trend,
        'progress_form': progress_form,
        'issue_form': issue_form,
        'can_update_progress': plan.status == 'in_progress',
        'can_complete': plan.status == 'in_progress',
        'valid_transitions': plan.get_valid_transitions(),
    })
    return render(request, "plan_management/plan_execution_track.html", context)


@login_required
def plan_progress_update(request, plan_id):
    """计划进度更新页面"""
    permission_set = get_user_permission_codes(request.user)
    
    # 权限检查
    if not _permission_granted('plan_management.view', permission_set):
        messages.error(request, '您没有权限更新计划进度')
        return redirect('plan_pages:plan_list')
    
    plan = get_object_or_404(Plan, id=plan_id)
    
    # 检查是否可以更新进度
    if plan.status != 'in_progress':
        messages.error(request, '只有执行中的计划可以更新进度')
        return redirect('plan_pages:plan_detail', plan_id=plan_id)
    
    if request.method == 'POST':
        form = PlanProgressUpdateForm(request.POST, plan=plan)
        if form.is_valid():
            record = form.save(commit=False)
            record.recorded_by = request.user
            record.save()
            messages.success(request, '进度更新成功')
            return redirect('plan_pages:plan_execution_track', plan_id=plan_id)
        else:
            messages.error(request, '表单验证失败，请检查输入')
    else:
        form = PlanProgressUpdateForm(plan=plan)
    
    context = _context(
        f"进度更新 - {plan.name}",
        "📈",
        "更新计划执行进度",
        request=request,
    )
    context['plan_menu'] = _build_plan_management_menu(permission_set, active_id='plan_progress_update')
    context['form'] = form
    context['plan'] = plan
    return render(request, "plan_management/plan_progress_update.html", context)


@login_required
def plan_issue_list(request, plan_id):
    """计划问题管理页面"""
    permission_set = get_user_permission_codes(request.user)
    
    # 权限检查
    if not _permission_granted('plan_management.view', permission_set):
        messages.error(request, '您没有权限查看计划问题')
        return redirect('plan_pages:plan_list')
    
    plan = get_object_or_404(Plan, id=plan_id)
    
    # 获取问题列表
    issues = PlanIssue.objects.filter(
        plan=plan
    ).select_related('assigned_to', 'created_by').order_by('-created_time')
    
    # 获取筛选参数
    status_filter = request.GET.get('status', '')
    severity_filter = request.GET.get('severity', '')
    
    if status_filter:
        issues = issues.filter(status=status_filter)
    
    if severity_filter:
        issues = issues.filter(severity=severity_filter)
    
    # 统计信息
    total_count = issues.count()
    open_count = issues.filter(status='open').count()
    in_progress_count = issues.filter(status='in_progress').count()
    resolved_count = issues.filter(status='resolved').count()
    
    # 问题表单
    issue_form = PlanIssueForm(plan=plan, user=request.user)
    
    # 处理问题创建
    if request.method == 'POST' and 'create_issue' in request.POST:
        issue_form = PlanIssueForm(request.POST, plan=plan, user=request.user)
        if issue_form.is_valid():
            issue = issue_form.save(commit=False)
            issue.created_by = request.user
            issue.save()
            messages.success(request, '问题创建成功')
            return redirect('plan_pages:plan_issue_list', plan_id=plan_id)
    
    context = _context(
        f"问题管理 - {plan.name}",
        "⚠️",
        "管理计划执行中的问题",
        request=request,
    )
    context['plan_menu'] = _build_plan_management_menu(permission_set, active_id='plan_issue_list')
    context.update({
        'plan': plan,
        'issues': issues,
        'total_count': total_count,
        'open_count': open_count,
        'in_progress_count': in_progress_count,
        'resolved_count': resolved_count,
        'issue_form': issue_form,
        'status_filter': status_filter,
        'severity_filter': severity_filter,
    })
    return render(request, "plan_management/plan_issue_list.html", context)


@login_required
def plan_complete(request, plan_id):
    """计划完成情况页面"""
    permission_set = get_user_permission_codes(request.user)
    
    # 权限检查
    if not _permission_granted('plan_management.view', permission_set):
        messages.error(request, '您没有权限查看计划完成情况')
        return redirect('plan_pages:plan_list')
    
    plan = get_object_or_404(
        Plan.objects.select_related(
            'responsible_person', 'related_goal', 'created_by'
        ),
        id=plan_id
    )
    
    # 检查是否可以完成
    if plan.status != 'in_progress':
        messages.error(request, '只有执行中的计划可以完成')
        return redirect('plan_pages:plan_detail', plan_id=plan_id)
    
    # 获取所有进度记录
    progress_records = PlanProgressRecord.objects.filter(
        plan=plan
    ).select_related('recorded_by').order_by('-recorded_time')
    
    # 获取问题列表（未解决的）
    unresolved_issues = PlanIssue.objects.filter(
        plan=plan,
        status__in=['open', 'in_progress']
    ).count()
    
    if request.method == 'POST':
        # 确认完成
        if 'confirm_complete' in request.POST:
            # 检查是否有未解决的问题
            if unresolved_issues > 0:
                messages.warning(request, f'计划还有 {unresolved_issues} 个未解决的问题，建议先解决后再完成')
                return redirect('plan_pages:plan_complete', plan_id=plan_id)
            
            # 更新进度为100%
            plan.progress = 100
            plan.save()
            
            # 记录进度
            PlanProgressRecord.objects.create(
                plan=plan,
                progress=100,
                progress_description='计划已完成',
                recorded_by=request.user
            )
            
            # 转换状态
            plan.transition_to('completed', user=request.user)
            messages.success(request, '计划已完成')
            return redirect('plan_pages:plan_detail', plan_id=plan_id)
    
    context = _context(
        f"计划完成 - {plan.name}",
        "✅",
        "确认计划完成情况",
        request=request,
    )
    context['plan_menu'] = _build_plan_management_menu(permission_set, active_id='plan_complete')
    context.update({
        'plan': plan,
        'progress_records': progress_records,
        'unresolved_issues': unresolved_issues,
    })
    return render(request, "plan_management/plan_complete.html", context)


@login_required
def strategic_goal_create(request):
    """创建战略目标页面"""
    permission_set = get_user_permission_codes(request.user)
    
    # 权限检查
    if not _permission_granted('plan_management.manage_goal', permission_set):
        messages.error(request, '您没有权限创建战略目标')
        return redirect('plan_pages:strategic_goal_list')
    
    if request.method == 'POST':
        form = StrategicGoalForm(request.POST, user=request.user)
        if form.is_valid():
            goal = form.save(commit=False)
            goal.created_by = request.user
            goal.save()
            
            # 保存多对多关系
            if 'participants' in form.cleaned_data:
                goal.participants.set(form.cleaned_data['participants'])
            if 'related_projects' in form.cleaned_data:
                goal.related_projects.set(form.cleaned_data['related_projects'])
            
            messages.success(request, f'战略目标 {goal.name} 创建成功')
            return redirect('plan_pages:strategic_goal_detail', goal_id=goal.id)
        else:
            messages.error(request, '表单验证失败，请检查输入')
    else:
        form = StrategicGoalForm(user=request.user)
    
    context = _context("创建战略目标", "➕", "创建新的战略目标", request=request)
    context['plan_menu'] = _build_plan_management_menu(permission_set, active_id='strategic_goal_list')
    context['form'] = form
    return render(request, "plan_management/strategic_goal_form.html", context)


@login_required
def strategic_goal_detail(request, goal_id):
    """战略目标详情页面"""
    permission_set = get_user_permission_codes(request.user)
    
    # 权限检查
    if not _permission_granted('plan_management.manage_goal', permission_set):
        messages.error(request, '您没有权限查看战略目标详情')
        return redirect('plan_pages:strategic_goal_list')
    
    goal = get_object_or_404(
        StrategicGoal.objects.select_related(
            'responsible_person', 'responsible_department', 'parent_goal', 'created_by'
        ).prefetch_related('participants', 'related_projects', 'child_goals'),
        id=goal_id
    )
    
    # 获取进度记录
    progress_records = GoalProgressRecord.objects.filter(
        goal=goal
    ).select_related('recorded_by').order_by('-recorded_time')[:10]
    
    # 获取状态日志
    status_logs = GoalStatusLog.objects.filter(
        goal=goal
    ).select_related('changed_by').order_by('-changed_time')[:10]
    
    # 获取调整申请
    adjustments = GoalAdjustment.objects.filter(
        goal=goal
    ).select_related('created_by', 'approved_by').order_by('-created_time')
    
    # 获取下级目标
    child_goals = goal.child_goals.select_related(
        'responsible_person', 'responsible_department'
    ).all()
    
    # 获取关联计划数量
    related_plans_count = Plan.objects.filter(related_goal=goal).count()
    
    context = _context(
        f"战略目标详情 - {goal.name}",
        "🎯",
        goal.name,
        request=request,
    )
    context['plan_menu'] = _build_plan_management_menu(permission_set, active_id='strategic_goal_list')
    context.update({
        'goal': goal,
        'progress_records': progress_records,
        'status_logs': status_logs,
        'adjustments': adjustments,
        'child_goals': child_goals,
        'related_plans_count': related_plans_count,
        'can_edit': _permission_granted('plan_management.manage_goal', permission_set) and goal.status in ['draft', 'published'],
        'can_delete': _permission_granted('plan_management.manage_goal', permission_set) and goal.status == 'draft' and not goal.has_related_plans(),
    })
    return render(request, "plan_management/strategic_goal_detail.html", context)


@login_required
def strategic_goal_edit(request, goal_id):
    """编辑战略目标页面"""
    permission_set = get_user_permission_codes(request.user)
    
    # 权限检查
    if not _permission_granted('plan_management.manage_goal', permission_set):
        messages.error(request, '您没有权限编辑战略目标')
        return redirect('plan_pages:strategic_goal_list')
    
    goal = get_object_or_404(StrategicGoal, id=goal_id)
    
    # 检查是否可以编辑
    if goal.status not in ['draft', 'published']:
        messages.error(request, '只有制定中或已发布状态的目标可以编辑')
        return redirect('plan_pages:strategic_goal_detail', goal_id=goal_id)
    
    if request.method == 'POST':
        form = StrategicGoalForm(request.POST, instance=goal, user=request.user)
        if form.is_valid():
            goal = form.save()
            messages.success(request, f'战略目标 {goal.name} 更新成功')
            return redirect('plan_pages:strategic_goal_detail', goal_id=goal.id)
        else:
            messages.error(request, '表单验证失败，请检查输入')
    else:
        form = StrategicGoalForm(instance=goal, user=request.user)
    
    context = _context(
        f"编辑战略目标 - {goal.name}",
        "✏️",
        "编辑战略目标信息",
        request=request,
    )
    context['plan_menu'] = _build_plan_management_menu(permission_set, active_id='strategic_goal_list')
    context['form'] = form
    context['goal'] = goal
    return render(request, "plan_management/strategic_goal_form.html", context)


@login_required
def strategic_goal_decompose_entry(request):
    """目标分解入口页面 - 自动跳转到第一个目标的分解页面"""
    permission_set = get_user_permission_codes(request.user)
    
    # 权限检查
    if not _permission_granted('plan_management.manage_goal', permission_set):
        messages.error(request, '您没有权限进行目标分解')
        return redirect('plan_pages:strategic_goal_list')
    
    # 查找第一个可用的战略目标（优先查找顶级目标，即没有父目标的目标）
    goal = StrategicGoal.objects.filter(parent_goal__isnull=True).order_by('-created_time').first()
    
    # 如果没有顶级目标，查找任意一个目标
    if not goal:
        goal = StrategicGoal.objects.order_by('-created_time').first()
    
    if goal:
        # 如果有目标，跳转到该目标的分解页面
        return redirect('plan_pages:strategic_goal_decompose', goal_id=goal.id)
    else:
        # 如果没有目标，跳转到列表页面并提示
        messages.info(request, '暂无战略目标，请先创建目标后再进行分解')
        return redirect('plan_pages:strategic_goal_list')


@login_required
def strategic_goal_decompose(request, goal_id):
    """战略目标分解页面"""
    permission_set = get_user_permission_codes(request.user)
    
    # 权限检查
    if not _permission_granted('plan_management.manage_goal', permission_set):
        messages.error(request, '您没有权限进行目标分解')
        return redirect('plan_pages:strategic_goal_list')
    
    goal = get_object_or_404(
        StrategicGoal.objects.select_related('responsible_person', 'responsible_department'),
        id=goal_id
    )
    
    # 获取所有下级目标（递归）
    def get_goal_tree(parent_goal, level=0):
        """递归获取目标树"""
        children = parent_goal.child_goals.select_related(
            'responsible_person', 'responsible_department'
        ).all()
        result = [(parent_goal, level)]
        for child in children:
            result.extend(get_goal_tree(child, level + 1))
        return result
    
    goal_tree = get_goal_tree(goal)
    
    # 获取所有部门（用于创建部门目标）
    departments = Department.objects.filter(is_active=True).order_by('name')
    
    # 获取所有用户（用于创建个人目标）
    users = User.objects.filter(is_active=True).order_by('username')
    
    context = _context(
        f"目标分解 - {goal.name}",
        "📊",
        "将战略目标分解为部门、团队、个人目标",
        request=request,
    )
    context['plan_menu'] = _build_plan_management_menu(permission_set, active_id='strategic_goal_decompose')
    context.update({
        'goal': goal,
        'goal_tree': goal_tree,
        'departments': departments,
        'users': users,
    })
    return render(request, "plan_management/strategic_goal_decompose.html", context)


@login_required
def strategic_goal_track_entry(request):
    """战略目标跟踪入口页面 - 选择要跟踪的目标"""
    permission_set = get_user_permission_codes(request.user)
    
    # 权限检查
    if not _permission_granted('plan_management.manage_goal', permission_set):
        messages.error(request, '您没有权限跟踪战略目标')
        return redirect('plan_pages:strategic_goal_list')
    
    # 获取所有目标（包括制定中的，但标记哪些可以跟踪）
    all_goals = StrategicGoal.objects.select_related(
        'responsible_person', 'responsible_department', 'parent_goal'
    ).order_by('-created_time')
    
    # 如果没有目标，跳转到列表页
    if not all_goals.exists():
        messages.info(request, '暂无战略目标，请先创建目标')
        return redirect('plan_pages:strategic_goal_list')
    
    # 筛选可跟踪的目标（已发布或执行中的目标）
    trackable_goals = all_goals.filter(status__in=['published', 'in_progress'])
    
    # 如果只有一个可跟踪的目标，直接跳转到该目标的跟踪页面
    if trackable_goals.count() == 1:
        return redirect('plan_pages:strategic_goal_track', goal_id=trackable_goals.first().id)
    
    # 显示选择页面（显示所有目标，但标记哪些可以跟踪）
    context = _context(
        "目标跟踪",
        "📈",
        "选择要跟踪的战略目标",
        request=request,
    )
    context['plan_menu'] = _build_plan_management_menu(permission_set, active_id='strategic_goal_track')
    context.update({
        'goals': all_goals,
        'trackable_goals': trackable_goals,
        'has_trackable_goals': trackable_goals.exists(),
    })
    return render(request, "plan_management/strategic_goal_track_entry.html", context)


@login_required
def strategic_goal_track(request, goal_id):
    """战略目标跟踪页面"""
    permission_set = get_user_permission_codes(request.user)
    
    # 权限检查
    if not _permission_granted('plan_management.manage_goal', permission_set):
        messages.error(request, '您没有权限跟踪战略目标')
        return redirect('plan_pages:strategic_goal_list')
    
    goal = get_object_or_404(
        StrategicGoal.objects.select_related(
            'responsible_person', 'responsible_department', 'parent_goal'
        ),
        id=goal_id
    )
    
    # 获取所有进度记录
    progress_records = GoalProgressRecord.objects.filter(
        goal=goal
    ).select_related('recorded_by').order_by('-recorded_time')
    
    # 获取状态日志
    status_logs = GoalStatusLog.objects.filter(
        goal=goal
    ).select_related('changed_by').order_by('-changed_time')
    
    # 获取调整申请
    adjustments = GoalAdjustment.objects.filter(
        goal=goal
    ).select_related('created_by', 'approved_by').order_by('-created_time')
    
    # 计算进度趋势（用于图表）
    progress_trend = []
    for record in progress_records[:30]:  # 最近30条记录
        progress_trend.append({
            'date': record.recorded_time.strftime('%Y-%m-%d'),
            'value': float(record.current_value),
            'rate': float(record.completion_rate),
        })
    progress_trend.reverse()  # 按时间正序
    
    # 进度更新表单
    progress_form = GoalProgressUpdateForm(goal=goal)
    
    # 调整申请表单
    adjustment_form = GoalAdjustmentForm(goal=goal)
    
    # 处理进度更新
    if request.method == 'POST' and 'update_progress' in request.POST:
        progress_form = GoalProgressUpdateForm(request.POST, goal=goal)
        if progress_form.is_valid():
            record = progress_form.save(commit=False)
            record.recorded_by = request.user
            record.completion_rate = goal.calculate_completion_rate()
            record.save()
            messages.success(request, '进度更新成功')
            return redirect('plan_pages:strategic_goal_track', goal_id=goal_id)
    
    # 处理状态转换
    if request.method == 'POST' and 'transition_status' in request.POST:
        new_status = request.POST.get('new_status')
        try:
            goal.transition_to(new_status, user=request.user)
            messages.success(request, f'目标状态已更新为：{goal.get_status_display()}')
            return redirect('plan_pages:strategic_goal_track', goal_id=goal_id)
        except ValueError as e:
            messages.error(request, str(e))
    
    # 处理目标完成确认
    if request.method == 'POST' and 'complete_goal' in request.POST:
        if goal.status == 'in_progress':
            goal.transition_to('completed', user=request.user)
            messages.success(request, '目标已完成')
            return redirect('plan_pages:strategic_goal_track', goal_id=goal_id)
        else:
            messages.error(request, '只有执行中的目标可以完成')
    
    context = _context(
        f"目标跟踪 - {goal.name}",
        "📈",
        "跟踪战略目标的执行进度",
        request=request,
    )
    context['plan_menu'] = _build_plan_management_menu(permission_set, active_id='strategic_goal_track')
    context.update({
        'goal': goal,
        'progress_records': progress_records,
        'status_logs': status_logs,
        'adjustments': adjustments,
        'progress_trend': progress_trend,
        'progress_form': progress_form,
        'adjustment_form': adjustment_form,
        'can_update_progress': goal.status in ['published', 'in_progress'],
        'can_complete': goal.status == 'in_progress',
        'valid_transitions': goal.get_valid_transitions(),
    })
    return render(request, "plan_management/strategic_goal_track.html", context)


@login_required
def strategic_goal_delete(request, goal_id):
    """删除战略目标"""
    permission_set = get_user_permission_codes(request.user)
    
    # 权限检查
    if not _permission_granted('plan_management.manage_goal', permission_set):
        messages.error(request, '您没有权限删除战略目标')
        return redirect('plan_pages:strategic_goal_list')
    
    goal = get_object_or_404(StrategicGoal, id=goal_id)
    
    if request.method == 'POST':
        # POST请求时进行删除前的所有检查
        # 检查是否可以删除
        if goal.status != 'draft':
            messages.error(request, '只有制定中状态的目标可以删除')
            return redirect('plan_pages:strategic_goal_detail', goal_id=goal_id)
        
        # 检查是否有关联计划
        if goal.has_related_plans():
            messages.error(request, '该目标有关联的计划，无法删除')
            return redirect('plan_pages:strategic_goal_detail', goal_id=goal_id)
        
        # 检查是否有下级目标
        if goal.get_child_goals_count() > 0:
            messages.error(request, '该目标有下级目标，无法删除')
            return redirect('plan_pages:strategic_goal_detail', goal_id=goal_id)
        
        # 执行删除
        goal_name = goal.name
        goal.delete()
        messages.success(request, f'战略目标 {goal_name} 已删除')
        return redirect('plan_pages:strategic_goal_list')
    
    # GET请求时显示确认页面，但检查是否可以删除（用于显示警告信息）
    can_delete = True
    delete_warnings = []
    
    if goal.status != 'draft':
        can_delete = False
        delete_warnings.append('只有制定中状态的目标可以删除')
    
    if goal.has_related_plans():
        can_delete = False
        delete_warnings.append('该目标有关联的计划，无法删除')
    
    if goal.get_child_goals_count() > 0:
        can_delete = False
        delete_warnings.append('该目标有下级目标，无法删除')
    
    context = _context(
        f"删除战略目标 - {goal.name}",
        "🗑️",
        "确认删除战略目标",
        request=request,
    )
    context['plan_menu'] = _build_plan_management_menu(permission_set, active_id='strategic_goal_list')
    context['goal'] = goal
    context['can_delete'] = can_delete
    context['delete_warnings'] = delete_warnings
    return render(request, "plan_management/strategic_goal_delete.html", context)


@login_required
@require_http_methods(["POST"])
def create_child_goal(request, parent_goal_id):
    """创建下级目标（AJAX）"""
    permission_set = get_user_permission_codes(request.user)
    
    # 权限检查
    if not _permission_granted('plan_management.manage_goal', permission_set):
        return JsonResponse({'success': False, 'message': '您没有权限创建下级目标'}, status=403)
    
    parent_goal = get_object_or_404(StrategicGoal, id=parent_goal_id)
    
    goal_type = request.POST.get('goal_type')  # 'department', 'team', 'personal'
    name = request.POST.get('name')
    target_value_str = request.POST.get('target_value')
    responsible_id = request.POST.get('responsible_id')
    department_id = request.POST.get('department_id', None)
    
    if not all([goal_type, name, target_value_str, responsible_id]):
        return JsonResponse({'success': False, 'message': '请填写完整信息'}, status=400)
    
    # 转换目标值为 Decimal 类型
    try:
        target_value = Decimal(str(target_value_str))
    except (ValueError, InvalidOperation, TypeError):
        return JsonResponse({'success': False, 'message': '目标值格式不正确'}, status=400)
    
    # 转换 responsible_id 和 department_id 为整数
    try:
        responsible_id = int(responsible_id)
    except (ValueError, TypeError):
        return JsonResponse({'success': False, 'message': '负责人ID格式不正确'}, status=400)
    
    if department_id:
        try:
            department_id = int(department_id)
        except (ValueError, TypeError):
            department_id = None
    
    try:
        child_goal = StrategicGoal.objects.create(
            name=name,
            goal_type=parent_goal.goal_type,
            goal_period=parent_goal.goal_period,
            status='draft',
            indicator_name=parent_goal.indicator_name,
            indicator_type=parent_goal.indicator_type,
            indicator_unit=parent_goal.indicator_unit,
            target_value=target_value,
            current_value=Decimal('0'),
            responsible_person_id=responsible_id,
            responsible_department_id=department_id,
            description=request.POST.get('description', ''),
            weight=Decimal('0'),
            start_date=parent_goal.start_date,
            end_date=parent_goal.end_date,
            parent_goal=parent_goal,
            created_by=request.user,
        )
        
        return JsonResponse({
            'success': True,
            'message': '下级目标创建成功',
            'goal_id': child_goal.id,
            'goal_number': child_goal.goal_number,
        })
    except Exception as e:
        import traceback
        print(f"创建下级目标失败: {str(e)}")
        print(traceback.format_exc())
        return JsonResponse({'success': False, 'message': f'创建失败：{str(e)}'}, status=500)


@login_required
def plan_completion_analysis(request):
    """计划完成分析页面"""
    permission_set = get_user_permission_codes(request.user)
    
    # 权限检查
    if not _permission_granted('plan_management.view', permission_set):
        messages.error(request, '您没有权限查看计划完成分析')
        return redirect('plan_pages:plan_list')
    
    # 获取筛选参数
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    plan_type = request.GET.get('plan_type', '')
    plan_period = request.GET.get('plan_period', '')
    
    # 查询计划
    plans = Plan.objects.select_related('responsible_person', 'related_goal')
    
    # 时间筛选
    if date_from:
        plans = plans.filter(start_time__gte=date_from)
    if date_to:
        plans = plans.filter(end_time__lte=date_to)
    
    # 类型筛选
    if plan_type:
        plans = plans.filter(plan_type=plan_type)
    
    # 周期筛选
    if plan_period:
        plans = plans.filter(plan_period=plan_period)
    
    # 统计信息
    total_count = plans.count()
    completed_count = plans.filter(status='completed').count()
    in_progress_count = plans.filter(status='in_progress').count()
    cancelled_count = plans.filter(status='cancelled').count()
    
    # 完成率统计
    completion_rate = (completed_count / total_count * 100) if total_count > 0 else 0
    
    # 按状态统计
    status_stats = plans.values('status').annotate(count=Count('id')).order_by('status')
    
    # 按类型统计
    type_stats = plans.values('plan_type').annotate(count=Count('id')).order_by('plan_type')
    
    # 按周期统计
    period_stats = plans.values('plan_period').annotate(count=Count('id')).order_by('plan_period')
    
    # 平均进度
    avg_progress = plans.aggregate(avg=Sum('progress'))['avg']
    if avg_progress and total_count > 0:
        avg_progress = avg_progress / total_count
    else:
        avg_progress = 0
    
    # 进度分布（使用下划线作为键名，避免模板语法问题）
    progress_distribution = {
        'progress_0_25': plans.filter(progress__gte=0, progress__lt=25).count(),
        'progress_25_50': plans.filter(progress__gte=25, progress__lt=50).count(),
        'progress_50_75': plans.filter(progress__gte=50, progress__lt=75).count(),
        'progress_75_100': plans.filter(progress__gte=75, progress__lt=100).count(),
        'progress_100': plans.filter(progress=100).count(),
    }
    
    context = _context("完成分析", "📊", "分析计划的完成情况", request=request)
    context['plan_menu'] = _build_plan_management_menu(permission_set, active_id='plan_completion_analysis')
    context.update({
        'total_count': total_count,
        'completed_count': completed_count,
        'in_progress_count': in_progress_count,
        'cancelled_count': cancelled_count,
        'completion_rate': round(completion_rate, 2),
        'avg_progress': round(avg_progress, 2),
        'status_stats': status_stats,
        'type_stats': type_stats,
        'period_stats': period_stats,
        'progress_distribution': progress_distribution,
        'date_from': date_from,
        'date_to': date_to,
        'plan_type': plan_type,
        'plan_period': plan_period,
    })
    return render(request, "plan_management/plan_completion_analysis.html", context)


@login_required
def plan_goal_achievement(request):
    """目标达成分析页面"""
    permission_set = get_user_permission_codes(request.user)
    
    # 权限检查
    if not _permission_granted('plan_management.view', permission_set):
        messages.error(request, '您没有权限查看目标达成分析')
        return redirect('plan_pages:plan_list')
    
    # 获取筛选参数
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    goal_type = request.GET.get('goal_type', '')
    goal_period = request.GET.get('goal_period', '')
    
    # 查询目标
    goals = StrategicGoal.objects.select_related('responsible_person', 'responsible_department')
    
    # 时间筛选
    if date_from:
        goals = goals.filter(start_date__gte=date_from)
    if date_to:
        goals = goals.filter(end_date__lte=date_to)
    
    # 类型筛选
    if goal_type:
        goals = goals.filter(goal_type=goal_type)
    
    # 周期筛选
    if goal_period:
        goals = goals.filter(goal_period=goal_period)
    
    # 统计信息
    total_count = goals.count()
    completed_count = goals.filter(status='completed').count()
    in_progress_count = goals.filter(status='in_progress').count()
    published_count = goals.filter(status='published').count()
    
    # 平均完成率
    avg_completion = goals.aggregate(avg=Sum('completion_rate'))['avg']
    if avg_completion and total_count > 0:
        avg_completion = avg_completion / total_count
    else:
        avg_completion = 0
    
    # 按状态统计
    status_stats = goals.values('status').annotate(count=Count('id')).order_by('status')
    
    # 按类型统计
    type_stats = goals.values('goal_type').annotate(count=Count('id')).order_by('goal_type')
    
    # 按周期统计
    period_stats = goals.values('goal_period').annotate(count=Count('id')).order_by('goal_period')
    
    # 完成率分布（使用下划线作为键名，避免模板语法问题）
    completion_distribution = {
        'completion_0_25': goals.filter(completion_rate__gte=0, completion_rate__lt=25).count(),
        'completion_25_50': goals.filter(completion_rate__gte=25, completion_rate__lt=50).count(),
        'completion_50_75': goals.filter(completion_rate__gte=50, completion_rate__lt=75).count(),
        'completion_75_100': goals.filter(completion_rate__gte=75, completion_rate__lt=100).count(),
        'completion_100': goals.filter(completion_rate=100).count(),
    }
    
    # 高完成率目标（>=80%）
    high_completion_goals = goals.filter(completion_rate__gte=80).order_by('-completion_rate')[:10]
    
    # 低完成率目标（<50%）
    low_completion_goals = goals.filter(completion_rate__lt=50).order_by('completion_rate')[:10]
    
    context = _context("目标达成", "🎯", "分析战略目标的达成情况", request=request)
    context['plan_menu'] = _build_plan_management_menu(permission_set, active_id='plan_goal_achievement')
    context.update({
        'total_count': total_count,
        'completed_count': completed_count,
        'in_progress_count': in_progress_count,
        'published_count': published_count,
        'avg_completion': round(avg_completion, 2),
        'status_stats': status_stats,
        'type_stats': type_stats,
        'period_stats': period_stats,
        'completion_distribution': completion_distribution,
        'high_completion_goals': high_completion_goals,
        'low_completion_goals': low_completion_goals,
        'date_from': date_from,
        'date_to': date_to,
        'goal_type': goal_type,
        'goal_period': goal_period,
    })
    return render(request, "plan_management/plan_goal_achievement.html", context)


@login_required
def plan_statistics(request):
    """计划统计页面"""
    permission_set = get_user_permission_codes(request.user)
    
    # 权限检查
    if not _permission_granted('plan_management.view', permission_set):
        messages.error(request, '您没有权限查看计划统计')
        return redirect('plan_pages:plan_list')
    
    # 获取筛选参数
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    # 查询计划
    plans = Plan.objects.select_related('responsible_person', 'related_goal')
    
    # 查询目标
    goals = StrategicGoal.objects.select_related('responsible_person')
    
    # 时间筛选
    if date_from:
        plans = plans.filter(start_time__gte=date_from)
        goals = goals.filter(start_date__gte=date_from)
    if date_to:
        plans = plans.filter(end_time__lte=date_to)
        goals = goals.filter(end_date__lte=date_to)
    
    # 计划统计
    plan_total = plans.count()
    plan_by_status = plans.values('status').annotate(count=Count('id'))
    plan_by_type = plans.values('plan_type').annotate(count=Count('id'))
    plan_by_period = plans.values('plan_period').annotate(count=Count('id'))
    
    # 目标统计
    goal_total = goals.count()
    goal_by_status = goals.values('status').annotate(count=Count('id'))
    goal_by_type = goals.values('goal_type').annotate(count=Count('id'))
    goal_by_period = goals.values('goal_period').annotate(count=Count('id'))
    
    # 问题统计
    issues = PlanIssue.objects.select_related('plan')
    if date_from or date_to:
        issues = issues.filter(discovered_time__gte=date_from if date_from else timezone.now() - timezone.timedelta(days=365))
        if date_to:
            issues = issues.filter(discovered_time__lte=date_to)
    
    issue_total = issues.count()
    issue_by_status = issues.values('status').annotate(count=Count('id'))
    issue_by_severity = issues.values('severity').annotate(count=Count('id'))
    
    # 进度记录统计
    progress_records = PlanProgressRecord.objects.select_related('plan')
    if date_from or date_to:
        progress_records = progress_records.filter(recorded_time__gte=date_from if date_from else timezone.now() - timezone.timedelta(days=365))
        if date_to:
            progress_records = progress_records.filter(recorded_time__lte=date_to)
    
    progress_record_count = progress_records.count()
    
    # 最近30天的进度更新趋势
    from datetime import timedelta
    trend_data = []
    for i in range(29, -1, -1):
        date = timezone.now().date() - timedelta(days=i)
        count = progress_records.filter(recorded_time__date=date).count()
        trend_data.append({
            'date': date.strftime('%Y-%m-%d'),
            'count': count,
        })
    
    context = _context("计划统计", "📈", "统计计划相关数据", request=request)
    context['plan_menu'] = _build_plan_management_menu(permission_set, active_id='plan_statistics')
    context.update({
        'plan_total': plan_total,
        'plan_by_status': plan_by_status,
        'plan_by_type': plan_by_type,
        'plan_by_period': plan_by_period,
        'goal_total': goal_total,
        'goal_by_status': goal_by_status,
        'goal_by_type': goal_by_type,
        'goal_by_period': goal_by_period,
        'issue_total': issue_total,
        'issue_by_status': issue_by_status,
        'issue_by_severity': issue_by_severity,
        'progress_record_count': progress_record_count,
        'trend_data': trend_data,
        'date_from': date_from,
        'date_to': date_to,
    })
    return render(request, "plan_management/plan_statistics.html", context)


# ==================== P1 决策接口（围绕 decision 的裁决） ====================

@login_required
def plan_request_start(request, plan_id):
    """发起启动计划请求（提交审批）"""
    permission_set = get_user_permission_codes(request.user)
    plan = get_object_or_404(Plan, id=plan_id)
    
    # 权限检查：plan_management.create 或负责人
    can_submit = _permission_granted('plan_management.create', permission_set) or plan.responsible_person == request.user
    if not can_submit:
        messages.error(request, '您没有权限提交审批')
        return redirect('plan_pages:plan_detail', plan_id=plan_id)
    
    # 检查状态
    if plan.status != 'draft':
        messages.error(request, f'只有草稿状态的计划可以提交审批，当前状态：{plan.get_status_display()}')
        return redirect('plan_pages:plan_detail', plan_id=plan_id)
    
    # 检查是否已存在 pending 的 start 请求
    existing_pending = PlanDecision.objects.filter(
        plan=plan,
        request_type='start',
        decided_at__isnull=True
    ).exists()
    
    if existing_pending:
        messages.warning(request, '该计划已有待处理的启动请求')
        return redirect('plan_pages:plan_detail', plan_id=plan_id)
    
    # 创建决策记录
    PlanDecision.objects.create(
        plan=plan,
        request_type='start',
        decision=None,
        requested_by=request.user,
        reason=request.POST.get('reason', '')
    )
    
    messages.success(request, '已提交审批请求')
    return redirect('plan_pages:plan_detail', plan_id=plan_id)


@login_required
def plan_request_cancel(request, plan_id):
    """发起取消计划请求"""
    permission_set = get_user_permission_codes(request.user)
    plan = get_object_or_404(Plan, id=plan_id)
    
    # 权限检查：plan_management.create 或负责人
    can_request = _permission_granted('plan_management.create', permission_set) or plan.responsible_person == request.user
    if not can_request:
        messages.error(request, '您没有权限发起取消请求')
        return redirect('plan_pages:plan_detail', plan_id=plan_id)
    
    # 检查状态
    if plan.status != 'in_progress':
        messages.error(request, f'只有执行中状态的计划可以申请取消，当前状态：{plan.get_status_display()}')
        return redirect('plan_pages:plan_detail', plan_id=plan_id)
    
    # 检查是否已存在 pending 的 cancel 请求
    existing_pending = PlanDecision.objects.filter(
        plan=plan,
        request_type='cancel',
        decided_at__isnull=True
    ).exists()
    
    if existing_pending:
        messages.warning(request, '该计划已有待处理的取消请求')
        return redirect('plan_pages:plan_detail', plan_id=plan_id)
    
    # 创建决策记录
    PlanDecision.objects.create(
        plan=plan,
        request_type='cancel',
        decision=None,
        requested_by=request.user,
        reason=request.POST.get('reason', '')
    )
    
    messages.success(request, '已发起取消审批请求')
    return redirect('plan_pages:plan_detail', plan_id=plan_id)


@login_required
def decision_approve(request, decision_id):
    """审批通过决策"""
    permission_set = get_user_permission_codes(request.user)
    decision = get_object_or_404(PlanDecision, id=decision_id, decided_at__isnull=True)
    plan = decision.plan
    
    # 权限检查：plan_management.approve_plan 或系统管理员
    can_approve = _permission_granted('plan_management.approve_plan', permission_set) or request.user.is_superuser
    if not can_approve:
        messages.error(request, '您没有权限审批')
        return redirect('plan_pages:plan_detail', plan_id=plan.id)
    
    # 更新决策记录
    decision.decision = 'approve'
    decision.decided_by = request.user
    decision.decided_at = timezone.now()
    decision.reason = request.POST.get('reason', decision.reason)
    decision.save()
    
    # 通过裁决器处理状态变更
    if decision.request_type == 'start':
        result = adjudicate_plan_status(plan, decision='approve', system_facts=None)
    elif decision.request_type == 'cancel':
        result = adjudicate_plan_status(plan, decision='approve_cancel', system_facts=None)
    else:
        messages.error(request, '未知的请求类型')
        return redirect('plan_pages:plan_detail', plan_id=plan.id)
    
    # 更新计划状态
    if result.changed:
        plan.status = result.new_status
        plan.save(update_fields=['status'])
        
        # 记录状态日志
        PlanStatusLog.objects.create(
            plan=plan,
            old_status=result.old_status,
            new_status=result.new_status,
            changed_by=request.user,
            change_reason=result.reason
        )
        messages.success(request, f'审批通过，计划状态已更新为：{plan.get_status_display()}')
    else:
        messages.info(request, f'审批通过，但状态未变更：{result.reason}')
    
    return redirect('plan_pages:plan_detail', plan_id=plan.id)


@login_required
def decision_reject(request, decision_id):
    """审批驳回决策"""
    permission_set = get_user_permission_codes(request.user)
    decision = get_object_or_404(PlanDecision, id=decision_id, decided_at__isnull=True)
    plan = decision.plan
    
    # 权限检查：plan_management.approve_plan 或系统管理员
    can_reject = _permission_granted('plan_management.approve_plan', permission_set) or request.user.is_superuser
    if not can_reject:
        messages.error(request, '您没有权限审批')
        return redirect('plan_pages:plan_detail', plan_id=plan.id)
    
    # 更新决策记录
    decision.decision = 'reject'
    decision.decided_by = request.user
    decision.decided_at = timezone.now()
    decision.reason = request.POST.get('reason', '')
    decision.save()
    
    # 通过裁决器处理（reject 不改状态，只记录）
    if decision.request_type == 'start':
        result = adjudicate_plan_status(plan, decision='reject', system_facts=None)
    elif decision.request_type == 'cancel':
        result = adjudicate_plan_status(plan, decision='reject_cancel', system_facts=None)
    else:
        messages.error(request, '未知的请求类型')
        return redirect('plan_pages:plan_detail', plan_id=plan.id)
    
    # reject 不改状态，只记录日志
    messages.success(request, '已驳回请求，计划状态保持不变')
    
    return redirect('plan_pages:plan_detail', plan_id=plan.id)

