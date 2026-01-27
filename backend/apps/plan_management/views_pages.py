"""
计划管理模块页面视图
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse, NoReverseMatch
from django.core.paginator import Paginator
from django.db.models import Q, Count, Sum, Avg
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django import forms
from decimal import Decimal, InvalidOperation
import logging
from datetime import datetime, timedelta, date
from backend.apps.system_management.services import get_user_permission_codes
from backend.apps.system_management.models import User, Department


def calculate_goal_progress_status(goal):
    """计算目标进度状态（辅助函数）"""
    from datetime import date
    today = date.today()
    completion_progress = float(goal.completion_rate) if goal.completion_rate else 0
    
    if goal.end_date and goal.end_date < today:
        # 已过期
        if completion_progress >= 100:
            return {'status': 'completed', 'label': '已完成', 'class': 'bg-success'}
        else:
            return {'status': 'overdue', 'label': '已逾期', 'class': 'bg-danger'}
    elif goal.start_date and goal.start_date > today:
        # 未开始
        return {'status': 'not_started', 'label': '未开始', 'class': 'bg-secondary'}
    else:
        # 进行中，计算时间进度并比较完成进度
        if goal.start_date and goal.end_date:
            total_days = (goal.end_date - goal.start_date).days + 1
            if total_days > 0:
                elapsed_days = max((today - goal.start_date).days + 1, 0)
                time_progress = min((elapsed_days / total_days) * 100, 100)
            else:
                time_progress = 0
        else:
            time_progress = 0
        
        # 比较完成进度和时间进度
        progress_diff = completion_progress - time_progress
        if completion_progress >= 100:
            return {'status': 'ahead_completed', 'label': '提前完成', 'class': 'bg-success'}
        elif progress_diff >= 10:
            return {'status': 'ahead', 'label': '提前', 'class': 'bg-info'}
        elif progress_diff >= -10:
            return {'status': 'on_track', 'label': '正常', 'class': 'bg-primary'}
        elif progress_diff >= -20:
            return {'status': 'behind', 'label': '滞后', 'class': 'bg-warning'}
        else:
            return {'status': 'seriously_behind', 'label': '严重滞后', 'class': 'bg-danger'}


def calculate_plan_progress_status(plan):
    """计算计划进度状态（辅助函数）"""
    from django.utils import timezone
    from datetime import date
    now = timezone.now()
    today = now.date()
    
    # 获取进度百分比
    progress = float(getattr(plan, 'progress', 0) or 0)
    
    if plan.end_time:
        end_date = plan.end_time.date() if hasattr(plan.end_time, 'date') else plan.end_time
        if end_date < today:
            # 已过期
            if progress >= 100:
                return {'status': 'completed', 'label': '已完成', 'class': 'bg-success'}
            else:
                return {'status': 'overdue', 'label': '已逾期', 'class': 'bg-danger'}
    
    if plan.start_time:
        start_date = plan.start_time.date() if hasattr(plan.start_time, 'date') else plan.start_time
        if start_date > today:
            # 未开始
            return {'status': 'not_started', 'label': '未开始', 'class': 'bg-secondary'}
    
    # 进行中，计算时间进度并比较完成进度
    if plan.start_time and plan.end_time:
        start_date = plan.start_time.date() if hasattr(plan.start_time, 'date') else plan.start_time
        end_date = plan.end_time.date() if hasattr(plan.end_time, 'date') else plan.end_time
        total_days = (end_date - start_date).days + 1
        if total_days > 0:
            elapsed_days = max((today - start_date).days + 1, 0)
            time_progress = min((elapsed_days / total_days) * 100, 100)
        else:
            time_progress = 0
    else:
        time_progress = 0
    
    # 比较完成进度和时间进度
    progress_diff = progress - time_progress
    if progress >= 100:
        return {'status': 'ahead_completed', 'label': '提前完成', 'class': 'bg-success'}
    elif progress_diff >= 10:
        return {'status': 'ahead', 'label': '提前', 'class': 'bg-info'}
    elif progress_diff >= -10:
        return {'status': 'on_track', 'label': '正常', 'class': 'bg-primary'}
    elif progress_diff >= -20:
        return {'status': 'behind', 'label': '滞后', 'class': 'bg-warning'}
    else:
        return {'status': 'seriously_behind', 'label': '严重滞后', 'class': 'bg-danger'}

# P1: 兼容导入，避免 core.views 变更导致 plan_management 无法启动
try:
    from backend.core.views import _permission_granted, _build_full_top_nav, _build_unified_sidebar_nav
except ImportError:
    # Fallback: 如果 _build_unified_sidebar_nav 不存在，提供简单实现
    from backend.core.views import _permission_granted, _build_full_top_nav
    from django.urls import reverse, NoReverseMatch
    
    def _build_unified_sidebar_nav(menu_structure, permission_set, active_id=None):
        """Fallback: 简单的侧边栏菜单构建函数（支持 url_name 转换）"""
        nav = []
        for item in menu_structure:
            if item.get('permission'):
                if not _permission_granted(item['permission'], permission_set):
                    continue
            
            # 处理 URL：优先使用 url_name 转换为真实 URL
            url = '#'
            url_name = item.get('url_name')
            if url_name:
                try:
                    url = reverse(url_name)
                except NoReverseMatch:
                    url = item.get('url', '#')
            else:
                url = item.get('url', '#')
            
            nav_item = {
                'label': item.get('label', ''),
                'icon': item.get('icon', ''),
                'url': url,
                'active': item.get('id') == active_id if active_id else False,
            }
            
            # 处理子菜单
            if 'children' in item:
                children = []
                for child in item['children']:
                    # 检查子菜单权限
                    if child.get('permission'):
                        if not _permission_granted(child['permission'], permission_set):
                            continue
                    
                    # 处理子菜单 URL
                    child_url = '#'
                    child_url_name = child.get('url_name')
                    if child_url_name:
                        try:
                            child_url = reverse(child_url_name)
                        except NoReverseMatch:
                            child_url = child.get('url', '#')
                    else:
                        child_url = child.get('url', '#')
                    
                    children.append({
                        'id': child.get('id'),
                        'label': child.get('label', ''),
                        'icon': child.get('icon', ''),
                        'url': child_url,
                        'active': child.get('id') == active_id if active_id else False,
                    })
                
                # 如果父菜单定义了子菜单，但所有子菜单都被过滤掉了，则跳过该父菜单
                if not children:
                    continue
                
                nav_item['children'] = children
                # 如果父菜单没有 url，使用第一个子菜单的 URL
                if nav_item['url'] == '#':
                    nav_item['url'] = children[0].get('url', '#')
                # 如果任意子菜单激活，父菜单也激活并展开
                if any(child.get('active') for child in children):
                    nav_item['active'] = True
                    nav_item['expanded'] = True
                # 如果菜单结构定义中设置了 expanded 属性，则使用该值（默认展开）
                elif item.get('expanded', False):
                    nav_item['expanded'] = True
            
            nav.append(nav_item)
        return nav
from .models import (
    GoalAdjustment,
    GoalProgressRecord,
    GoalStatusLog,
    Plan,
    PlanAdjustment,
    PlanDecision,
    PlanIssue,
    PlanProgressRecord,
    PlanStatusLog,
    StrategicGoal
)
from .forms import (
    StrategicGoalForm,
    GoalProgressUpdateForm,
    GoalAdjustmentForm,
    PlanForm,
    PlanProgressUpdateForm,
    PlanIssueForm,
    PlanAdjustmentForm,
    PlanItemFormSet,
)


def _form_errors_plain(form):
    """从表单提取纯文本错误信息，避免 HTML 标签（如 ul/li）混入 messages。"""
    parts = []
    for field, errs in form.errors.items():
        f = form.fields.get(field)
        label = (f.label if f and hasattr(f, 'label') else None) or field
        for e in (list(errs) if errs else []):
            parts.append(f'{label}: {e}')
    return '; '.join(parts)


def _validate_plan_fields(plan):
    """
    验证计划的必填字段
    
    Args:
        plan: Plan 实例
        
    Returns:
        tuple: (is_valid: bool, errors: list) 
            is_valid: 是否通过验证
            errors: 错误信息列表，每个元素为 {'field': 字段名, 'label': 字段标签, 'message': 错误信息}
    """
    errors = []
    
    # 必填字段列表
    required_fields = [
        ('name', '计划名称'),
        ('level', '计划层级'),
        ('plan_period', '计划周期'),
        ('responsible_person', '负责人'),
        ('start_time', '开始时间'),
        ('end_time', '结束时间'),
        ('related_goal', '关联战略目标'),
    ]
    
    # 检查必填字段
    for field_name, field_label in required_fields:
        value = getattr(plan, field_name, None)
        if not value:
            errors.append({
                'field': field_name,
                'label': field_label,
                'message': f'{field_label}为必填项，请填写'
            })
    
    # 检查计划内容（如果计划项为空，则基本信息表单的 content 必填）
    if not plan.content or not plan.content.strip():
        # 检查是否有子计划（计划项）
        has_child_plans = plan.child_plans.exists()
        if not has_child_plans:
            errors.append({
                'field': 'content',
                'label': '计划内容',
                'message': '计划内容为必填项，请填写计划内容或添加计划项'
            })
    
    # 检查计划目标
    if not plan.plan_objective or not plan.plan_objective.strip():
        errors.append({
            'field': 'plan_objective',
            'label': '计划目标',
            'message': '计划目标为必填项，请填写'
        })
    
    # 检查验收标准
    if not plan.acceptance_criteria or not plan.acceptance_criteria.strip():
        errors.append({
            'field': 'acceptance_criteria',
            'label': '验收标准',
            'message': '验收标准为必填项，请填写'
        })
    
    # 检查协作计划：如果选择了协作人员，必须填写协作计划
    if plan.participants.exists():
        if not plan.collaboration_plan or not plan.collaboration_plan.strip():
            errors.append({
                'field': 'collaboration_plan',
                'label': '协作计划',
                'message': '如果选择了协作人员，必须填写协作计划'
            })
    
    # 检查时间范围
    if plan.start_time and plan.end_time:
        if plan.end_time < plan.start_time:
            errors.append({
                'field': 'end_time',
                'label': '结束时间',
                'message': '结束时间不能早于开始时间'
            })
    
    is_valid = len(errors) == 0
    return is_valid, errors


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
        'expanded': True,  # 默认展开
        'children': [
            {'id': 'strategic_goal_list', 'label': '目标列表', 'icon': '🎯', 'url_name': 'plan_pages:strategic_goal_list', 'permission': 'plan_management.manage_goal'},
            {'id': 'strategic_goal_create', 'label': '创建目标', 'icon': '➕', 'url_name': 'plan_pages:strategic_goal_create', 'permission': 'plan_management.manage_goal'},
            {'id': 'strategic_goal_decompose', 'label': '目标分解', 'icon': '📊', 'url_name': 'plan_pages:strategic_goal_decompose_entry', 'permission': 'plan_management.manage_goal'},
            {'id': 'strategic_goal_track', 'label': '目标跟踪', 'icon': '📈', 'url_name': 'plan_pages:strategic_goal_track_entry', 'permission': 'plan_management.view_goal_progress'},
        ]
    },
    {
        'id': 'plan_management',
        'label': '计划管理',
        'icon': '📅',
        'permission': 'plan_management.view',
        'expanded': True,  # 默认展开
        'children': [
            {'id': 'plan_list', 'label': '计划列表', 'icon': '📋', 'url_name': 'plan_pages:plan_list', 'permission': 'plan_management.view'},
            {'id': 'plan_create', 'label': '创建计划', 'icon': '➕', 'url_name': 'plan_pages:plan_create', 'permission': 'plan_management.plan.create'},
            {'id': 'plan_decompose', 'label': '计划分解', 'icon': '📊', 'url_name': 'plan_pages:plan_decompose_entry', 'permission': 'plan_management.view'},
            {'id': 'plan_track', 'label': '计划跟踪', 'icon': '📈', 'url_name': 'plan_pages:plan_track_entry', 'permission': 'plan_management.view'},
        ]
    },
    {
        'id': 'plan_analysis',
        'label': '计划分析',
        'icon': '📈',
        'permission': 'plan_management.view_analysis',
        'expanded': True,  # 默认展开
        'children': [
            {'id': 'plan_completion_analysis', 'label': '完成度分析', 'icon': '✅', 'url_name': 'plan_pages:plan_completion_analysis', 'permission': 'plan_management.view_analysis'},
            {'id': 'plan_goal_achievement', 'label': '目标达成分析', 'icon': '🎯', 'url_name': 'plan_pages:plan_goal_achievement', 'permission': 'plan_management.view_analysis'},
            {'id': 'plan_statistics', 'label': '统计报表', 'icon': '📊', 'url_name': 'plan_pages:plan_statistics', 'permission': 'plan_management.view_analysis'},
            {'id': 'plan_approval', 'label': '计划审批', 'icon': '📝', 'url_name': 'plan_pages:plan_approval_list', 'permission': 'plan_management.approve_plan'},
        ]
    },
]


def _build_plan_management_sidebar_nav(permission_set, request_path=None, active_id=None):
    """生成计划管理左侧菜单（统一格式）"""
    # 使用统一的菜单构建函数
    return _build_unified_sidebar_nav(PLAN_MANAGEMENT_MENU_STRUCTURE, permission_set, active_id=active_id)


def _filter_plans_by_permission(plans, user, permission_set):
    """
    根据用户权限过滤计划列表
    
    权限级别（从高到低）：
    1. 超级用户: 查看全部计划
    2. 显式 view_all: 仅当拥有 plan_management.plan.view_all 时查看全部（不含 __all__ 特权）
    3. 普通员工: 只能查看本人的计划（owner=user 或 responsible_person=user）
    
    注意：system_admin / general_manager 等 __all__ 角色不再自动拥有「查看全部计划」；
    员工只能看到本人的工作计划。若需某人查看全部，须单独分配 plan_management.plan.view_all。
    
    Args:
        plans: 计划查询集
        user: 用户对象
        permission_set: 用户权限集合
    
    Returns:
        过滤后的计划查询集
    """
    if not user or not getattr(user, 'is_authenticated', False):
        return plans.none()
    
    # 超级用户拥有全部权限
    if getattr(user, 'is_superuser', False):
        return plans
    
    # 仅显式拥有 plan_management.plan.view_all 时可见全部（不把 __all__ 当作 view_all）
    if 'plan_management.plan.view_all' in permission_set:
        return plans
    
    # 普通员工（含 view_assigned、view、__all__ 等）：只能查看本人的计划
    return plans.filter(
        Q(responsible_person=user) |
        Q(owner=user)
    ).distinct()


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
        context['sidebar_nav'] = _build_plan_management_sidebar_nav(permission_set, request.path)
        # 添加侧边栏标题（计划管理模块）
        context['sidebar_title'] = '计划管理'
        context['sidebar_subtitle'] = 'Plan Management'
    else:
        context['full_top_nav'] = []
        context['sidebar_nav'] = []
    
    return context


# ==================== 占位视图函数（待实现） ====================

@login_required
def plan_management_home(request):
    """
    P2-5: 计划管理首页 - 数据展示中心（定版）
    
    首页结构（强制）：
    1. 第一行：目标中心（个人优先）
    2. 第二行：我的计划执行
    3. 第三行：待办 & 风险
    4. 第四行：管理视角（仅有权限者可见）
    
    原则：
    - 首页不做编辑，只做"看"
    - 首页不堆数据，只给"结论 + 入口"
    - 目标优先于计划
    - 风险高于统计
    - 所有数据来自 service，禁止直接 ORM
    """
    permission_codes = get_user_permission_codes(request.user)
    
    # 权限检查
    if not _permission_granted('plan_management.view', permission_codes):
        messages.error(request, '您没有权限访问计划管理')
        return redirect('admin:index')
    
    context = {}
    
    # ========== 获取筛选参数 ==========
    filter_department_id = request.GET.get('filter_department', '').strip()
    filter_responsible_person_id = request.GET.get('filter_responsible_person', '').strip()
    filter_start_date = request.GET.get('filter_start_date', '').strip()
    filter_end_date = request.GET.get('filter_end_date', '').strip()
    
    # 将筛选参数传递到context
    context['filter_department_id'] = filter_department_id
    context['filter_responsible_person_id'] = filter_responsible_person_id
    context['filter_start_date'] = filter_start_date
    context['filter_end_date'] = filter_end_date
    
    # 获取所有部门和用户（用于筛选下拉框）
    from backend.apps.plan_management.models import Plan, StrategicGoal
    all_departments = Department.objects.filter(is_active=True).order_by('order', 'name')
    context['all_departments'] = all_departments
    
    # 根据部门筛选用户
    filter_users = User.objects.filter(is_active=True)
    if filter_department_id:
        try:
            filter_users = filter_users.filter(department_id=filter_department_id)
        except ValueError:
            pass
    context['filter_users'] = filter_users.order_by('first_name', 'last_name', 'username')
    
    # 辅助函数：应用筛选条件到查询集
    def apply_filters_to_queryset(qs, model_type='plan'):
        """应用筛选条件到查询集"""
        if model_type == 'plan':
            if filter_department_id:
                try:
                    qs = qs.filter(responsible_department_id=filter_department_id)
                except ValueError:
                    pass
            if filter_responsible_person_id:
                try:
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
                    # 包含结束日期当天
                    end_datetime = datetime.combine(end_date, datetime.max.time())
                    qs = qs.filter(created_time__lte=end_datetime)
                except ValueError:
                    pass
        elif model_type == 'goal':
            if filter_department_id:
                try:
                    qs = qs.filter(responsible_department_id=filter_department_id)
                except ValueError:
                    pass
            if filter_responsible_person_id:
                try:
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
                    # 包含结束日期当天
                    end_datetime = datetime.combine(end_date, datetime.max.time())
                    qs = qs.filter(created_time__lte=end_datetime)
                except ValueError:
                    pass
        return qs
    
    try:
        # ========== P2-5: 导入所有 service ==========
        from backend.apps.plan_management.services.goal_stats_service import get_user_goal_stats, get_company_goal_stats, get_user_collaboration_goal_stats
        from backend.apps.plan_management.services.plan_stats_service import get_user_plan_stats, get_company_plan_stats, get_user_collaboration_plan_stats
        from backend.apps.plan_management.services.todo_service import get_user_todos, get_responsible_todos
        from backend.apps.plan_management.services.risk_query_service import get_user_risk_items, get_responsible_risk_items, get_subordinates_risk_items
        
        # ========== 第一行：目标中心（个人优先）==========
        goal_stats = get_user_goal_stats(
            request.user,
            filter_department_id=filter_department_id,
            filter_responsible_person_id=filter_responsible_person_id,
            filter_start_date=filter_start_date,
            filter_end_date=filter_end_date
        )
        
        goal_cards = [{
            'label': '我的目标',
            'icon': '🎯',
            'value': str(goal_stats['total']),
            'subvalue': f'执行中 {goal_stats["in_progress"]} | 逾期 {goal_stats["overdue"]} | 本月需完成 {goal_stats["this_month"]}',
            'url': reverse('plan_pages:strategic_goal_list') + '?level=personal',
            'variant': 'primary' if goal_stats['total'] > 0 else 'secondary'
        }]
        
        context['goal_cards'] = goal_cards
        context['goal_stats'] = goal_stats
        
        # ========== 第二行：我的计划执行 ==========
        plan_stats = get_user_plan_stats(
            request.user,
            filter_department_id=filter_department_id,
            filter_responsible_person_id=filter_responsible_person_id,
            filter_start_date=filter_start_date,
            filter_end_date=filter_end_date
        )
        
        plan_cards = [{
            'label': '我的计划',
            'icon': '📋',
            'value': str(plan_stats['total']),
            'subvalue': f'执行中 {plan_stats["in_progress"]} | 今日应执行 {plan_stats["today"]} | 逾期 {plan_stats["overdue"]}',
            'url': reverse('plan_pages:plan_list') + '?level=personal',
            'variant': 'primary' if plan_stats['total'] > 0 else 'secondary'
        }]
        
        context['plan_cards'] = plan_cards
        context['plan_stats'] = plan_stats
        
        # ========== 我协作的统计 ==========
        collaboration_plan_stats = get_user_collaboration_plan_stats(
            request.user,
            filter_department_id=filter_department_id,
            filter_responsible_person_id=filter_responsible_person_id,
            filter_start_date=filter_start_date,
            filter_end_date=filter_end_date
        )
        collaboration_goal_stats = get_user_collaboration_goal_stats(
            request.user,
            filter_department_id=filter_department_id,
            filter_responsible_person_id=filter_responsible_person_id,
            filter_start_date=filter_start_date,
            filter_end_date=filter_end_date
        )
        
        collaboration_plan_cards = [{
            'label': '我协作的计划',
            'icon': '🤝',
            'value': str(collaboration_plan_stats['total']),
            'subvalue': f'执行中 {collaboration_plan_stats["in_progress"]} | 今日应执行 {collaboration_plan_stats["today"]} | 逾期 {collaboration_plan_stats["overdue"]}',
            'url': reverse('plan_pages:plan_list') + '?participating=1',
            'variant': 'info' if collaboration_plan_stats['total'] > 0 else 'secondary'
        }]
        
        collaboration_goal_cards = [{
            'label': '我协作的目标',
            'icon': '🤝',
            'value': str(collaboration_goal_stats['total']),
            'subvalue': f'执行中 {collaboration_goal_stats["in_progress"]} | 逾期 {collaboration_goal_stats["overdue"]} | 本月需完成 {collaboration_goal_stats["this_month"]}',
            'url': reverse('plan_pages:strategic_goal_list') + '?participating=1',
            'variant': 'info' if collaboration_goal_stats['total'] > 0 else 'secondary'
        }]
        
        context['collaboration_plan_stats'] = collaboration_plan_stats
        context['collaboration_goal_stats'] = collaboration_goal_stats
        context['collaboration_plan_cards'] = collaboration_plan_cards
        context['collaboration_goal_cards'] = collaboration_goal_cards
        
        # ========== 第三行：待办 & 风险 ==========
        # 我的待办（左）
        user_todos = get_user_todos(
            request.user,
            filter_department_id=filter_department_id,
            filter_responsible_person_id=filter_responsible_person_id,
            filter_start_date=filter_start_date,
            filter_end_date=filter_end_date
        )
        
        # 按类型分类待办事项（本周待办、本月待办、今日待办）
        from django.utils import timezone
        from datetime import datetime, timedelta
        
        now = timezone.now()
        today = now.date()
        week_start = today - timedelta(days=today.weekday())  # 本周一
        week_end = week_start + timedelta(days=6)  # 本周日
        month_start = today.replace(day=1)  # 本月1日
        next_month = month_start + timedelta(days=32)
        month_end = (next_month.replace(day=1) - timedelta(days=1))  # 本月最后一天
        
        todo_items = []
        weekly_todos = []
        monthly_todos = []
        daily_todos = []
        
        for todo in user_todos:
            todo_item = {
                'title': todo.get('title', ''),
                'description': todo.get('description', ''),
                'url': todo.get('url', '#'),
                'type': todo.get('type', ''),
                'priority': todo.get('priority', 'medium'),
                'deadline': todo.get('deadline'),
                'is_overdue': todo.get('is_overdue', False),
                'overdue_days': todo.get('overdue_days', 0),
            }
            
            # 根据待办类型设置显示信息
            if todo.get('is_db_todo'):
                # 数据库待办事项
                todo_item['type'] = 'db_todo'
                deadline = todo.get('deadline')
                if deadline:
                    if isinstance(deadline, str):
                        try:
                            from django.utils.dateparse import parse_datetime
                            deadline = parse_datetime(deadline)
                        except:
                            try:
                                from datetime import datetime
                                deadline = datetime.fromisoformat(deadline.replace('Z', '+00:00'))
                            except:
                                deadline = None
                    
                    if deadline and hasattr(deadline, 'date'):
                        deadline_date = deadline.date() if hasattr(deadline, 'date') else deadline
                        days_left = (deadline_date - today).days
                        
                        if todo.get('is_overdue'):
                            todo_item['meta'] = f'已逾期 {todo.get("overdue_days", 0)} 天'
                        elif days_left >= 0:
                            todo_item['meta'] = f'剩余 {days_left} 天'
                        else:
                            todo_item['meta'] = f'已逾期 {abs(days_left)} 天'
                        
                        # 分类到对应的卡片
                        if deadline_date == today:
                            daily_todos.append(todo_item)
                        elif week_start <= deadline_date <= week_end:
                            weekly_todos.append(todo_item)
                        elif month_start <= deadline_date <= month_end:
                            monthly_todos.append(todo_item)
                        else:
                            todo_items.append(todo_item)  # 其他待办
                    else:
                        todo_items.append(todo_item)
                else:
                    todo_items.append(todo_item)
            else:
                # 查询生成的待办事项
                if todo.get('object'):
                    obj = todo['object']
                    if hasattr(obj, 'get_full_name'):
                        todo_item['responsible'] = obj.get_full_name() or obj.username
                    elif hasattr(obj, 'username'):
                        todo_item['responsible'] = obj.username
                    else:
                        todo_item['responsible'] = '系统'
                
                # 根据待办类型分类
                todo_type = todo.get('type', '')
                if todo_type in ['plan_decomposition_daily', 'plan_today']:
                    daily_todos.append(todo_item)
                elif todo_type in ['plan_decomposition_weekly', 'plan_creation']:
                    weekly_todos.append(todo_item)
                elif todo_type in ['plan_creation', 'goal_creation']:
                    monthly_todos.append(todo_item)
                else:
                    todo_items.append(todo_item)
        
        # 合并所有待办，优先显示今日、本周、本月
        all_todo_items = daily_todos[:3] + weekly_todos[:3] + monthly_todos[:3] + todo_items[:5]
        
        context['todo_items'] = all_todo_items[:10]  # 最多显示10条
        context['daily_todos_count'] = len(daily_todos)
        context['weekly_todos_count'] = len(weekly_todos)
        context['monthly_todos_count'] = len(monthly_todos)
        context['user_todos'] = user_todos[:5]  # 保留旧字段以兼容
        context['user_todos_count'] = len(user_todos)
        
        # 风险提醒（右）
        risk_items = get_user_risk_items(
            request.user,
            limit=5,
            filter_department_id=filter_department_id,
            filter_responsible_person_id=filter_responsible_person_id,
            filter_start_date=filter_start_date,
            filter_end_date=filter_end_date
        )
        context['risk_items'] = risk_items
        context['risk_items_count'] = len(risk_items)
        
        # ========== 第四行：管理视角（仅有权限者可见）==========
        can_view_management = _permission_granted('plan_management.manage_goal', permission_codes) or _permission_granted('plan_management.plan.manage', permission_codes)
        
        if can_view_management:
            # 公司目标统计
            company_goal_stats = get_company_goal_stats(request.user)
            context['company_goal_stats'] = company_goal_stats
            
            # 公司计划统计
            company_plan_stats = get_company_plan_stats(request.user)
            context['company_plan_stats'] = company_plan_stats
            
            # 审批统计（仅管理视角）
            # 待审批判定：decided_at is null（根据模型定义和注释）
            pending_decisions = PlanDecision.objects.filter(decided_at__isnull=True)
            pending_total = pending_decisions.count()
            pending_start = pending_decisions.filter(request_type='start').count()
            pending_cancel = pending_decisions.filter(request_type='cancel').count()
            
            context['management_view'] = {
                'pending_total': pending_total,
                'pending_start': pending_start,
                'pending_cancel': pending_cancel,
            }
        
        context['can_view_management'] = can_view_management
        
        # ========== 第五行：下属工作情况（仅部门负责人可见）==========
        from backend.apps.system_management.services import get_subordinate_users, is_department_manager
        from django.db.models import Q, Count
        from django.utils import timezone
        from datetime import datetime, timedelta
        
        is_manager = is_department_manager(request.user)
        context['is_department_manager'] = is_manager
        
        # 初始化subordinates变量
        subordinates = get_subordinate_users(request.user) if is_manager else User.objects.none()
        
        if is_manager:
            context['subordinates_count'] = subordinates.count()
            
            # 获取下属的计划统计
            subordinate_plan_stats = []
            now = timezone.now()
            
            for subordinate in subordinates[:10]:  # 最多显示10个下属
                # 获取下属的计划
                subordinate_plans = Plan.objects.filter(
                    Q(owner=subordinate) | Q(responsible_person=subordinate) | Q(created_by=subordinate)
                ).distinct()
                
                # 统计
                total = subordinate_plans.count()
                in_progress = subordinate_plans.filter(status='in_progress').count()
                overdue = subordinate_plans.filter(
                    status__in=['draft', 'published', 'accepted', 'in_progress'],
                    end_time__lt=now
                ).count()
                
                # 今日应执行
                today = now.date()
                today_plans = subordinate_plans.filter(
                    status__in=['draft', 'published', 'accepted', 'in_progress'],
                    start_time__lte=now,
                    end_time__gte=now
                )
                
                subordinate_plan_stats.append({
                    'user': subordinate,
                    'user_name': subordinate.get_full_name() or subordinate.username,
                    'total': total,
                    'in_progress': in_progress,
                    'overdue': overdue,
                    'today': today_plans.count(),
                })
            
            context['subordinate_plan_stats'] = subordinate_plan_stats
            
            # 获取下属的目标统计
            subordinate_goal_stats = []
            for subordinate in subordinates[:10]:
                subordinate_goals = StrategicGoal.objects.filter(
                    Q(owner=subordinate) | Q(responsible_person=subordinate) | Q(created_by=subordinate)
                ).distinct()
                
                total = subordinate_goals.count()
                in_progress = subordinate_goals.filter(status='in_progress').count()
                overdue = subordinate_goals.filter(
                    status__in=['draft', 'published', 'in_progress'],
                    end_date__lt=today
                ).count()
                
                # 本月需完成
                month_start = today.replace(day=1)
                month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
                this_month = subordinate_goals.filter(
                    status__in=['draft', 'published', 'in_progress'],
                    end_date__gte=month_start,
                    end_date__lte=month_end
                ).count()
                
                subordinate_goal_stats.append({
                    'user': subordinate,
                    'user_name': subordinate.get_full_name() or subordinate.username,
                    'total': total,
                    'in_progress': in_progress,
                    'overdue': overdue,
                    'this_month': this_month,
                })
            
            context['subordinate_goal_stats'] = subordinate_goal_stats
            
            # 计算"全部"分类的汇总数据（我的 + 下属的）
            # 汇总下属的计划统计
            subordinate_plan_summary = {
                'total': sum(stat['total'] for stat in subordinate_plan_stats),
                'in_progress': sum(stat['in_progress'] for stat in subordinate_plan_stats),
                'today': sum(stat['today'] for stat in subordinate_plan_stats),
                'overdue': sum(stat['overdue'] for stat in subordinate_plan_stats),
            }
            
            # 汇总下属的目标统计
            subordinate_goal_summary = {
                'total': sum(stat['total'] for stat in subordinate_goal_stats),
                'in_progress': sum(stat['in_progress'] for stat in subordinate_goal_stats),
                'overdue': sum(stat['overdue'] for stat in subordinate_goal_stats),
                'this_month': sum(stat['this_month'] for stat in subordinate_goal_stats),
            }
            
            # 获取下属协作的统计
            subordinate_collaboration_plan_stats = []
            subordinate_collaboration_goal_stats = []
            subordinate_collaboration_plan_summary = {'total': 0, 'in_progress': 0, 'today': 0, 'overdue': 0}
            subordinate_collaboration_goal_summary = {'total': 0, 'in_progress': 0, 'overdue': 0, 'this_month': 0}
            
            for subordinate in subordinates[:10]:
                # 下属协作的计划（作为参与者，排除自己负责的）
                sub_collab_plans = Plan.objects.filter(participants=subordinate).exclude(responsible_person=subordinate)
                sub_collab_plan_total = sub_collab_plans.count()
                sub_collab_plan_in_progress = sub_collab_plans.filter(status='in_progress').count()
                sub_collab_plan_overdue = sub_collab_plans.filter(
                    status__in=['draft', 'published', 'accepted', 'in_progress'],
                    end_time__lt=now
                ).count()
                today_start = timezone.make_aware(datetime.combine(today, datetime.min.time()))
                today_end = timezone.make_aware(datetime.combine(today, datetime.max.time()))
                sub_collab_plan_today = sub_collab_plans.filter(
                    status='in_progress',
                    start_time__lte=today_end,
                    end_time__gte=today_start
                ).count()
                
                subordinate_collaboration_plan_summary['total'] += sub_collab_plan_total
                subordinate_collaboration_plan_summary['in_progress'] += sub_collab_plan_in_progress
                subordinate_collaboration_plan_summary['today'] += sub_collab_plan_today
                subordinate_collaboration_plan_summary['overdue'] += sub_collab_plan_overdue
                
                # 下属协作的目标（作为参与者，排除自己负责的）
                sub_collab_goals = StrategicGoal.objects.filter(participants=subordinate).exclude(responsible_person=subordinate)
                sub_collab_goal_total = sub_collab_goals.count()
                sub_collab_goal_in_progress = sub_collab_goals.filter(status='in_progress').count()
                sub_collab_goal_overdue = sub_collab_goals.filter(
                    status__in=['published', 'accepted', 'in_progress'],
                    end_date__lt=today
                ).count()
                month_start = today.replace(day=1)
                month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
                sub_collab_goal_this_month = sub_collab_goals.filter(
                    end_date__year=today.year,
                    end_date__month=today.month,
                    status__in=['published', 'accepted', 'in_progress']
                ).count()
                
                subordinate_collaboration_goal_summary['total'] += sub_collab_goal_total
                subordinate_collaboration_goal_summary['in_progress'] += sub_collab_goal_in_progress
                subordinate_collaboration_goal_summary['overdue'] += sub_collab_goal_overdue
                subordinate_collaboration_goal_summary['this_month'] += sub_collab_goal_this_month
            
            context['subordinate_collaboration_plan_summary'] = subordinate_collaboration_plan_summary
            context['subordinate_collaboration_goal_summary'] = subordinate_collaboration_goal_summary
            
            # "全部" = 我负责的 + 下属负责的 + 我协作的 + 下属协作的
            # 但如果筛选了负责人或部门，只显示筛选后的数据（不合并下属和协作数据）
            if filter_responsible_person_id or filter_department_id:
                # 有筛选条件时，"全部"只显示筛选后的数据
                all_plan_stats = {
                    'total': plan_stats['total'] + collaboration_plan_stats['total'],
                    'in_progress': plan_stats['in_progress'] + collaboration_plan_stats['in_progress'],
                    'today': plan_stats['today'] + collaboration_plan_stats['today'],
                    'overdue': plan_stats['overdue'] + collaboration_plan_stats['overdue'],
                }
                
                all_goal_stats = {
                    'total': goal_stats['total'] + collaboration_goal_stats['total'],
                    'in_progress': goal_stats['in_progress'] + collaboration_goal_stats['in_progress'],
                    'overdue': goal_stats['overdue'] + collaboration_goal_stats['overdue'],
                    'this_month': goal_stats['this_month'] + collaboration_goal_stats['this_month'],
                }
            else:
                # 没有筛选条件时，合并所有数据
                all_plan_stats = {
                    'total': plan_stats['total'] + subordinate_plan_summary['total'] + collaboration_plan_stats['total'] + subordinate_collaboration_plan_summary['total'],
                    'in_progress': plan_stats['in_progress'] + subordinate_plan_summary['in_progress'] + collaboration_plan_stats['in_progress'] + subordinate_collaboration_plan_summary['in_progress'],
                    'today': plan_stats['today'] + subordinate_plan_summary['today'] + collaboration_plan_stats['today'] + subordinate_collaboration_plan_summary['today'],
                    'overdue': plan_stats['overdue'] + subordinate_plan_summary['overdue'] + collaboration_plan_stats['overdue'] + subordinate_collaboration_plan_summary['overdue'],
                }
                
                all_goal_stats = {
                    'total': goal_stats['total'] + subordinate_goal_summary['total'] + collaboration_goal_stats['total'] + subordinate_collaboration_goal_summary['total'],
                    'in_progress': goal_stats['in_progress'] + subordinate_goal_summary['in_progress'] + collaboration_goal_stats['in_progress'] + subordinate_collaboration_goal_summary['in_progress'],
                    'overdue': goal_stats['overdue'] + subordinate_goal_summary['overdue'] + collaboration_goal_stats['overdue'] + subordinate_collaboration_goal_summary['overdue'],
                    'this_month': goal_stats['this_month'] + subordinate_goal_summary['this_month'] + collaboration_goal_stats['this_month'] + subordinate_collaboration_goal_summary['this_month'],
                }
            
            context['all_plan_stats'] = all_plan_stats
            context['all_goal_stats'] = all_goal_stats
            context['subordinate_plan_summary'] = subordinate_plan_summary
            context['subordinate_goal_summary'] = subordinate_goal_summary
            
            # 为手风琴分类准备卡片数据
            # 全部分类的卡片
            all_goal_cards = [{
                'label': '全部目标',
                'icon': '🎯',
                'value': str(all_goal_stats['total']),
                'subvalue': f'执行中 {all_goal_stats["in_progress"]} | 逾期 {all_goal_stats["overdue"]} | 本月需完成 {all_goal_stats["this_month"]}',
                'url': reverse('plan_pages:strategic_goal_list'),
                'variant': 'primary' if all_goal_stats['total'] > 0 else 'secondary'
            }]
            
            all_plan_cards = [{
                'label': '全部计划',
                'icon': '📋',
                'value': str(all_plan_stats['total']),
                'subvalue': f'执行中 {all_plan_stats["in_progress"]} | 今日应执行 {all_plan_stats["today"]} | 逾期 {all_plan_stats["overdue"]}',
                'url': reverse('plan_pages:plan_list'),
                'variant': 'primary' if all_plan_stats['total'] > 0 else 'secondary'
            }]
            
            # 我负责的分类的卡片（使用现有的）
            my_goal_cards = goal_cards
            my_plan_cards = plan_cards
            
            # 我下属的分类的卡片
            subordinate_goal_cards = [{
                'label': '下属目标',
                'icon': '🎯',
                'value': str(subordinate_goal_summary['total']),
                'subvalue': f'执行中 {subordinate_goal_summary["in_progress"]} | 逾期 {subordinate_goal_summary["overdue"]} | 本月需完成 {subordinate_goal_summary["this_month"]}',
                'url': reverse('plan_pages:strategic_goal_list'),
                'variant': 'success' if subordinate_goal_summary['total'] > 0 else 'secondary'
            }]
            
            subordinate_plan_cards = [{
                'label': '下属计划',
                'icon': '📋',
                'value': str(subordinate_plan_summary['total']),
                'subvalue': f'执行中 {subordinate_plan_summary["in_progress"]} | 今日应执行 {subordinate_plan_summary["today"]} | 逾期 {subordinate_plan_summary["overdue"]}',
                'url': reverse('plan_pages:plan_list'),
                'variant': 'success' if subordinate_plan_summary['total'] > 0 else 'secondary'
            }]
            
            # 下属协作的卡片
            subordinate_collaboration_goal_cards = [{
                'label': '下属协作目标',
                'icon': '🤝',
                'value': str(subordinate_collaboration_goal_summary['total']),
                'subvalue': f'执行中 {subordinate_collaboration_goal_summary["in_progress"]} | 逾期 {subordinate_collaboration_goal_summary["overdue"]} | 本月需完成 {subordinate_collaboration_goal_summary["this_month"]}',
                'url': reverse('plan_pages:strategic_goal_list'),
                'variant': 'warning' if subordinate_collaboration_goal_summary['total'] > 0 else 'secondary'
            }]
            
            subordinate_collaboration_plan_cards = [{
                'label': '下属协作计划',
                'icon': '🤝',
                'value': str(subordinate_collaboration_plan_summary['total']),
                'subvalue': f'执行中 {subordinate_collaboration_plan_summary["in_progress"]} | 今日应执行 {subordinate_collaboration_plan_summary["today"]} | 逾期 {subordinate_collaboration_plan_summary["overdue"]}',
                'url': reverse('plan_pages:plan_list'),
                'variant': 'warning' if subordinate_collaboration_plan_summary['total'] > 0 else 'secondary'
            }]
            
            context['all_goal_cards'] = all_goal_cards
            context['all_plan_cards'] = all_plan_cards
            context['my_goal_cards'] = my_goal_cards
            context['my_plan_cards'] = my_plan_cards
            context['subordinate_goal_cards'] = subordinate_goal_cards
            context['subordinate_plan_cards'] = subordinate_plan_cards
            context['subordinate_collaboration_goal_cards'] = subordinate_collaboration_goal_cards
            context['subordinate_collaboration_plan_cards'] = subordinate_collaboration_plan_cards
        else:
            context['subordinates_count'] = 0
            context['subordinate_plan_stats'] = []
            context['subordinate_goal_stats'] = []
            # 非部门负责人，全部 = 我负责的 + 我协作的
            context['subordinate_plan_summary'] = {'total': 0, 'in_progress': 0, 'today': 0, 'overdue': 0}
            context['subordinate_goal_summary'] = {'total': 0, 'in_progress': 0, 'overdue': 0, 'this_month': 0}
            context['subordinate_plan_summary'] = {'total': 0, 'in_progress': 0, 'today': 0, 'overdue': 0}
            context['subordinate_goal_summary'] = {'total': 0, 'in_progress': 0, 'overdue': 0, 'this_month': 0}
            context['subordinate_collaboration_plan_summary'] = {'total': 0, 'in_progress': 0, 'today': 0, 'overdue': 0}
            context['subordinate_collaboration_goal_summary'] = {'total': 0, 'in_progress': 0, 'overdue': 0, 'this_month': 0}
            
            # 全部 = 我负责的 + 我协作的
            all_plan_stats = {
                'total': plan_stats['total'] + collaboration_plan_stats['total'],
                'in_progress': plan_stats['in_progress'] + collaboration_plan_stats['in_progress'],
                'today': plan_stats['today'] + collaboration_plan_stats['today'],
                'overdue': plan_stats['overdue'] + collaboration_plan_stats['overdue'],
            }
            
            all_goal_stats = {
                'total': goal_stats['total'] + collaboration_goal_stats['total'],
                'in_progress': goal_stats['in_progress'] + collaboration_goal_stats['in_progress'],
                'overdue': goal_stats['overdue'] + collaboration_goal_stats['overdue'],
                'this_month': goal_stats['this_month'] + collaboration_goal_stats['this_month'],
            }
            
            context['all_plan_stats'] = all_plan_stats
            context['all_goal_stats'] = all_goal_stats
            
            # 非部门负责人，只显示"全部"、"我负责的"和"我协作的"
            all_goal_cards = [{
                'label': '全部目标',
                'icon': '🎯',
                'value': str(all_goal_stats['total']),
                'subvalue': f'执行中 {all_goal_stats["in_progress"]} | 逾期 {all_goal_stats["overdue"]} | 本月需完成 {all_goal_stats["this_month"]}',
                'url': reverse('plan_pages:strategic_goal_list'),
                'variant': 'primary' if all_goal_stats['total'] > 0 else 'secondary'
            }]
            
            all_plan_cards = [{
                'label': '全部计划',
                'icon': '📋',
                'value': str(all_plan_stats['total']),
                'subvalue': f'执行中 {all_plan_stats["in_progress"]} | 今日应执行 {all_plan_stats["today"]} | 逾期 {all_plan_stats["overdue"]}',
                'url': reverse('plan_pages:plan_list'),
                'variant': 'primary' if all_plan_stats['total'] > 0 else 'secondary'
            }]
            
            context['all_goal_cards'] = all_goal_cards
            context['all_plan_cards'] = all_plan_cards
            context['my_goal_cards'] = goal_cards
            context['my_plan_cards'] = plan_cards
            context['subordinate_goal_cards'] = []
            context['subordinate_plan_cards'] = []
            context['subordinate_collaboration_goal_cards'] = []
            context['subordinate_collaboration_plan_cards'] = []
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception('获取统计数据失败: %s', str(e))
        # P2-5: 设置默认值避免模板错误
        context.setdefault('goal_cards', [])
        context.setdefault('plan_cards', [])
        context.setdefault('user_todos', [])
        context.setdefault('risk_items', [])
        context.setdefault('goal_stats', {'total': 0, 'in_progress': 0, 'overdue': 0, 'this_month': 0})
        context.setdefault('plan_stats', {'total': 0, 'in_progress': 0, 'today': 0, 'overdue': 0})
        context.setdefault('can_view_management', False)
        context.setdefault('is_department_manager', False)
        context.setdefault('subordinates_count', 0)
        # 确保 is_manager 变量被定义
        is_manager = False
        # 确保 subordinates 变量被定义
        subordinates = User.objects.none()
        # 确保 risk_items 变量被定义
        risk_items = []
        # 确保 all_todo_items 变量被定义
        all_todo_items = []
        context.setdefault('subordinate_plan_stats', [])
        context.setdefault('subordinate_goal_stats', [])
        context.setdefault('all_plan_stats', {'total': 0, 'in_progress': 0, 'today': 0, 'overdue': 0})
        context.setdefault('all_goal_stats', {'total': 0, 'in_progress': 0, 'overdue': 0, 'this_month': 0})
        context.setdefault('subordinate_plan_summary', {'total': 0, 'in_progress': 0, 'today': 0, 'overdue': 0})
        context.setdefault('subordinate_goal_summary', {'total': 0, 'in_progress': 0, 'overdue': 0, 'this_month': 0})
        context.setdefault('all_goal_cards', [])
        context.setdefault('all_plan_cards', [])
        context.setdefault('my_goal_cards', [])
        context.setdefault('my_plan_cards', [])
        context.setdefault('subordinate_goal_cards', [])
        context.setdefault('subordinate_plan_cards', [])
        context.setdefault('collaboration_goal_cards', [])
        context.setdefault('collaboration_plan_cards', [])
        context.setdefault('subordinate_collaboration_goal_cards', [])
        context.setdefault('subordinate_collaboration_plan_cards', [])
        context.setdefault('collaboration_plan_stats', {'total': 0, 'in_progress': 0, 'today': 0, 'overdue': 0})
        context.setdefault('collaboration_goal_stats', {'total': 0, 'in_progress': 0, 'overdue': 0, 'this_month': 0})
        context.setdefault('subordinate_collaboration_plan_summary', {'total': 0, 'in_progress': 0, 'today': 0, 'overdue': 0})
        context.setdefault('subordinate_collaboration_goal_summary', {'total': 0, 'in_progress': 0, 'overdue': 0, 'this_month': 0})
        context.setdefault('category_data', {
            'all': {'plan_status_dist': None, 'goal_status_dist': None, 'risk_items': [], 'todo_items': [], 'my_work': {}},
            'mine': {'plan_status_dist': None, 'goal_status_dist': None, 'risk_items': [], 'todo_items': [], 'my_work': {}},
            'collaboration': {'plan_status_dist': None, 'goal_status_dist': None, 'risk_items': [], 'todo_items': [], 'my_work': {}},
        })
    
    # ========== 安全字段检查（统一获取，避免重复）==========
    plan_fields = {f.name for f in Plan._meta.get_fields()}
    goal_fields = {f.name for f in StrategicGoal._meta.get_fields()}
    
    # ========== 计划状态分布（已清除）==========
    context['plan_status_dist'] = None
    
    # ========== 目标状态分布（已清除）==========
    context['goal_status_dist'] = None
    
    # 保留状态标签映射用于其他用途（如果需要）
    from django.db.models import Q
    plan_status_label_map = {}
    try:
        for code, label in getattr(Plan, 'STATUS_CHOICES', Plan._meta.get_field('status').choices):
            plan_status_label_map[code] = label
    except Exception:
        plan_status_label_map = {}
    
    goal_status_label_map = {}
    try:
        for code, label in getattr(StrategicGoal, 'STATUS_CHOICES', StrategicGoal._meta.get_field('status').choices):
            goal_status_label_map[code] = label
    except Exception:
        goal_status_label_map = {}
    
    # ========== 我的工作 ==========
    my_work = {}
    
    # 我负责的计划（安全字段检查）
    plan_related_fields = []
    if 'responsible_person' in plan_fields:
        plan_related_fields.append('responsible_person')
    if 'related_goal' in plan_fields:
        plan_related_fields.append('related_goal')
    
    my_plans_qs = Plan.objects.filter(responsible_person=request.user).order_by('-updated_time') if 'responsible_person' in plan_fields else Plan.objects.none()
    # 应用筛选条件
    my_plans_qs = apply_filters_to_queryset(my_plans_qs, 'plan')
    my_plans = my_plans_qs.select_related(*plan_related_fields)[:5] if plan_related_fields and my_plans_qs else []
    my_work['my_plans'] = [{
        'title': p.name,
        'progress': float(getattr(p, 'progress', 0) or 0),
        'progress_status': calculate_plan_progress_status(p),
        'url': reverse('plan_pages:plan_detail', args=[p.id])
    } for p in my_plans]
    my_work['my_plans_count'] = my_plans_qs.count()
    
    # 我负责的目标（安全字段检查）
    goal_related_fields = []
    if 'responsible_person' in goal_fields:
        goal_related_fields.append('responsible_person')
    if 'parent_goal' in goal_fields:
        goal_related_fields.append('parent_goal')
    
    my_goals_qs = StrategicGoal.objects.filter(responsible_person=request.user).order_by('-updated_time') if 'responsible_person' in goal_fields else StrategicGoal.objects.none()
    # 应用筛选条件
    my_goals_qs = apply_filters_to_queryset(my_goals_qs, 'goal')
    my_goals = my_goals_qs.select_related(*goal_related_fields)[:5] if goal_related_fields and my_goals_qs else []
    
    my_work['my_goals'] = [{
        'title': g.name,
        'target_value': float(g.target_value) if g.target_value else 0,
        'current_value': float(g.current_value) if g.current_value else 0,
        'indicator_unit': g.indicator_unit or '',
        'completion_rate': float(getattr(g, 'completion_rate', 0) or 0),
        'progress_status': calculate_goal_progress_status(g),
        'url': reverse('plan_pages:strategic_goal_detail', args=[g.id])
    } for g in my_goals]
    my_work['my_goals_count'] = my_goals_qs.count()
    
    # 我参与的计划（仅当 participants 字段存在才统计，避免 FieldError）
    # 注意：根据权限要求，员工只能看到本人的和公司级的工作计划
    # 所以这里只显示用户作为负责人或所有者的计划，不显示仅作为参与者的计划
    participating_plans = []
    participating_plans_count = 0
    # 移除"我参与的计划"功能，因为员工只能看到本人的和公司级的计划
    # 如果用户只是参与者但不是负责人或所有者，则不应该看到该计划
    
    my_work['participating_plans'] = participating_plans
    my_work['participating_plans_count'] = participating_plans_count
    
    context['my_work'] = my_work
    
    # ========== 最近活动 ==========
    # ========== 为每个分类准备完整数据 ==========
    # 由于代码量很大，我们为每个分类准备数据字典
    # 每个分类需要：plan_status_dist, goal_status_dist, risk_items, todo_items, my_work
    
    # 确保is_manager已定义（必须在subordinates之前）
    # 优先从 context 获取，如果没有则重新计算
    if 'is_manager' not in locals() and 'is_department_manager' in context:
        is_manager = context['is_department_manager']
    elif 'is_manager' not in locals():
        from backend.apps.system_management.services import is_department_manager
        is_manager = is_department_manager(request.user)
    
    # 确保subordinates变量已定义（如果还没有）
    if 'subordinates' not in locals():
        from backend.apps.system_management.services import get_subordinate_users
        subordinates = get_subordinate_users(request.user) if is_manager else User.objects.none()
    
    # 确保subordinates_count已定义
    if 'subordinates_count' not in context:
        context['subordinates_count'] = subordinates.count() if is_manager else 0
    
    # 分类数据字典
    category_data = {}
    
    # 预先定义所有需要的查询集（用于"全部"分类）
    # 下属负责的查询集
    subordinate_responsible_plans_qs = Plan.objects.none()
    subordinate_responsible_goals_qs = StrategicGoal.objects.none()
    if is_manager and subordinates.exists():
        subordinate_responsible_plans_qs = Plan.objects.filter(responsible_person__in=subordinates)
        subordinate_responsible_goals_qs = StrategicGoal.objects.filter(responsible_person__in=subordinates)
        # 应用筛选条件
        subordinate_responsible_plans_qs = apply_filters_to_queryset(subordinate_responsible_plans_qs, 'plan')
        subordinate_responsible_goals_qs = apply_filters_to_queryset(subordinate_responsible_goals_qs, 'goal')
    
    # 我协作的查询集
    my_collaboration_plans_qs = Plan.objects.filter(participants=request.user).exclude(responsible_person=request.user)
    my_collaboration_goals_qs = StrategicGoal.objects.filter(participants=request.user).exclude(responsible_person=request.user)
    # 应用筛选条件
    my_collaboration_plans_qs = apply_filters_to_queryset(my_collaboration_plans_qs, 'plan')
    my_collaboration_goals_qs = apply_filters_to_queryset(my_collaboration_goals_qs, 'goal')
    
    # 下属协作的查询集
    subordinate_collaboration_plans_qs = Plan.objects.none()
    subordinate_collaboration_goals_qs = StrategicGoal.objects.none()
    if is_manager and subordinates.exists():
        subordinate_collaboration_plans_qs = Plan.objects.filter(participants__in=subordinates).exclude(responsible_person__in=subordinates)
        subordinate_collaboration_goals_qs = StrategicGoal.objects.filter(participants__in=subordinates).exclude(responsible_person__in=subordinates)
        # 应用筛选条件
        subordinate_collaboration_plans_qs = apply_filters_to_queryset(subordinate_collaboration_plans_qs, 'plan')
        subordinate_collaboration_goals_qs = apply_filters_to_queryset(subordinate_collaboration_goals_qs, 'goal')
    
    # 1. 全部分类的数据（合并所有：我负责的+我协作的+下属负责的+下属协作的）
    # 计划状态分布和目标状态分布已清除
    
    # 全部分类的风险项：合并所有相关风险
    # 确保 risk_items 已定义
    if 'risk_items' not in locals():
        risk_items = context.get('risk_items', [])
    all_risk_items = list(risk_items)  # 我负责的风险（owner=user）
    
    # 如果筛选了负责人，只显示该负责人的风险，不再添加下属的风险
    # 如果筛选了部门，只显示该部门的风险
    # 如果没有筛选，才添加下属的风险
    if not filter_responsible_person_id and not filter_department_id:
        if is_manager and subordinates.exists():
            all_risk_items.extend(get_subordinates_risk_items(
                subordinates,
                limit=10,
                filter_department_id=filter_department_id,
                filter_responsible_person_id=filter_responsible_person_id,
                filter_start_date=filter_start_date,
                filter_end_date=filter_end_date
            ))
    # 排序并去重（基于对象ID）
    seen_objects = set()
    unique_risk_items = []
    for item in all_risk_items:
        obj = item.get('object')
        if obj:
            obj_key = (item['type'], obj.id)
            if obj_key not in seen_objects:
                seen_objects.add(obj_key)
                unique_risk_items.append(item)
    # 重新排序
    unique_risk_items.sort(key=lambda x: x.get('days_overdue', 0), reverse=True)
    
    # 全部分类的待办项：合并所有相关待办
    # 使用完整的 user_todos 变量（包含我负责的 + 我协作的），而不是从 context 中获取（只包含5条）
    if 'user_todos' not in locals():
        user_todos = context.get('user_todos', [])
    # 将 user_todos 转换为统一的格式
    all_category_todos = []
    for todo in user_todos:
        todo_item = {
            'title': todo.get('title', ''),
            'description': todo.get('description', ''),
            'url': todo.get('url', '#'),
            'type': todo.get('type', ''),
            'priority': todo.get('priority', 'medium'),
            'deadline': todo.get('deadline'),
            'is_overdue': todo.get('is_overdue', False),
            'overdue_days': todo.get('overdue_days', 0),
            'meta': todo.get('meta', todo.get('description', '')),
        }
        all_category_todos.append(todo_item)
    
    # 如果筛选了负责人，只显示该负责人的待办，不再添加下属的待办
    # 如果筛选了部门，只显示该部门的待办
    # 如果没有筛选，才添加下属负责的待办和下属协作的待办
    if not filter_responsible_person_id and not filter_department_id:
        if is_manager and subordinates.exists():
            # 添加下属负责的待办
            for subordinate in subordinates[:10]:
                sub_todos = get_responsible_todos(
                    subordinate,
                    filter_department_id=filter_department_id,
                    filter_responsible_person_id=filter_responsible_person_id,
                    filter_start_date=filter_start_date,
                    filter_end_date=filter_end_date
                )
                for todo in sub_todos:
                    todo_item = {
                        'title': todo.get('title', ''),
                        'description': todo.get('description', ''),
                        'url': todo.get('url', '#'),
                        'type': todo.get('type', ''),
                        'priority': todo.get('priority', 'medium'),
                        'deadline': todo.get('deadline'),
                        'is_overdue': todo.get('is_overdue', False),
                        'overdue_days': todo.get('overdue_days', 0),
                        'meta': f'负责人：{subordinate.get_full_name() or subordinate.username}',
                    }
                    all_category_todos.append(todo_item)
            
            # 添加下属协作的待办
            for subordinate in subordinates[:10]:
                sub_collab_todos = get_user_todos(
                    subordinate,
                    filter_department_id=filter_department_id,
                    filter_responsible_person_id=filter_responsible_person_id,
                    filter_start_date=filter_start_date,
                    filter_end_date=filter_end_date
                )
                # 从下属的待办中筛选出协作的（参与者但不是负责人）
                for todo in sub_collab_todos:
                    obj = todo.get('object')
                    if obj:
                        # 如果是计划或目标，检查是否是协作的（参与者但不是负责人）
                        if hasattr(obj, 'participants') and subordinate in obj.participants.all():
                            if hasattr(obj, 'responsible_person') and obj.responsible_person != subordinate:
                                todo_item = {
                                    'title': todo.get('title', ''),
                                    'description': todo.get('description', ''),
                                    'url': todo.get('url', '#'),
                                    'type': todo.get('type', ''),
                                    'priority': todo.get('priority', 'medium'),
                                    'deadline': todo.get('deadline'),
                                    'is_overdue': todo.get('is_overdue', False),
                                    'overdue_days': todo.get('overdue_days', 0),
                                    'meta': f'下属协作：{subordinate.get_full_name() or subordinate.username}',
                                }
                                all_category_todos.append(todo_item)
    # 排序
    priority_order = {'high': 0, 'medium': 1, 'low': 2}
    all_category_todos.sort(key=lambda x: (priority_order.get(x.get('priority', 'low'), 2), x.get('deadline') or timezone.now()))
    
    # 全部分类的我的工作：合并所有相关计划和目标
    all_work_plans = list(my_work.get('my_plans', []))
    all_work_goals = list(my_work.get('my_goals', []))
    all_work_plans_count = my_work.get('my_plans_count', 0)
    all_work_goals_count = my_work.get('my_goals_count', 0)
    
    # 如果筛选了负责人，只显示该负责人的工作，不再添加下属的工作
    # 如果筛选了部门，只显示该部门的工作
    # 如果没有筛选，才添加下属负责的工作
    if not filter_responsible_person_id and not filter_department_id:
        if is_manager and subordinates.exists():
            # 添加下属负责的计划和目标
            for plan in subordinate_responsible_plans_qs.select_related('responsible_person', 'related_goal').order_by('-updated_time')[:5]:
                all_work_plans.append({
                    'title': plan.name,
                    'progress': float(getattr(plan, 'progress', 0) or 0),
                    'progress_status': calculate_plan_progress_status(plan),
                    'url': reverse('plan_pages:plan_detail', args=[plan.id])
                })
            for goal in subordinate_responsible_goals_qs.select_related('responsible_person', 'parent_goal').order_by('-updated_time')[:5]:
                all_work_goals.append({
                    'title': goal.name,
                    'status': goal.get_status_display() if hasattr(goal, 'get_status_display') else str(getattr(goal, 'status', '')),
                    'completion_rate': float(getattr(goal, 'completion_rate', 0) or 0),
                    'url': reverse('plan_pages:strategic_goal_detail', args=[goal.id])
                })
            all_work_plans_count += subordinate_responsible_plans_qs.count()
            all_work_goals_count += subordinate_responsible_goals_qs.count()
    
    # 添加我协作的计划和目标
    for plan in my_collaboration_plans_qs.select_related('responsible_person', 'related_goal').order_by('-updated_time')[:5]:
        all_work_plans.append({
            'title': plan.name,
            'status': plan.get_status_display() if hasattr(plan, 'get_status_display') else str(getattr(plan, 'status', '')),
            'progress': getattr(plan, 'progress', 0) or 0,
            'url': reverse('plan_pages:plan_detail', args=[plan.id])
        })
    for goal in my_collaboration_goals_qs.select_related('responsible_person', 'parent_goal').order_by('-updated_time')[:5]:
        all_work_goals.append({
            'title': goal.name,
            'status': goal.get_status_display() if hasattr(goal, 'get_status_display') else str(getattr(goal, 'status', '')),
            'completion_rate': float(getattr(goal, 'completion_rate', 0) or 0),
            'url': reverse('plan_pages:strategic_goal_detail', args=[goal.id])
        })
    all_work_plans_count += my_collaboration_plans_qs.count()
    all_work_goals_count += my_collaboration_goals_qs.count()
    
    # 如果筛选了负责人，只显示该负责人的工作，不再添加下属的工作
    # 如果筛选了部门，只显示该部门的工作
    # 如果没有筛选，才添加下属协作的工作
    if not filter_responsible_person_id and not filter_department_id:
        if is_manager and subordinates.exists():
            # 添加下属协作的计划和目标
            for plan in subordinate_collaboration_plans_qs.select_related('responsible_person', 'related_goal').order_by('-updated_time')[:5]:
                all_work_plans.append({
                    'title': plan.name,
                    'progress': float(getattr(plan, 'progress', 0) or 0),
                    'progress_status': calculate_plan_progress_status(plan),
                    'url': reverse('plan_pages:plan_detail', args=[plan.id])
                })
            for goal in subordinate_collaboration_goals_qs.select_related('responsible_person', 'parent_goal').order_by('-updated_time')[:5]:
                all_work_goals.append({
                    'title': goal.name,
                    'status': goal.get_status_display() if hasattr(goal, 'get_status_display') else str(getattr(goal, 'status', '')),
                    'completion_rate': float(getattr(goal, 'completion_rate', 0) or 0),
                    'url': reverse('plan_pages:strategic_goal_detail', args=[goal.id])
                })
            all_work_plans_count += subordinate_collaboration_plans_qs.count()
            all_work_goals_count += subordinate_collaboration_goals_qs.count()
    
    all_work = {
        'my_plans': all_work_plans[:5],
        'my_plans_count': all_work_plans_count,
        'my_goals': all_work_goals[:5],
        'my_goals_count': all_work_goals_count,
        'participating_plans': [],
        'participating_plans_count': 0,
    }
    
    category_data['all'] = {
        'plan_status_dist': None,
        'goal_status_dist': None,
        'risk_items': unique_risk_items[:5],
        'todo_items': all_category_todos[:10],
        'my_work': all_work,
        'goal_cards': context.get('all_goal_cards', []),
        'plan_cards': context.get('all_plan_cards', []),
    }
    
    # 2. 我负责的分类的数据
    # 计划状态分布和目标状态分布已清除
    # 我负责的风险项和待办项（只包含我负责的）
    my_responsible_risk_items = get_responsible_risk_items(
        request.user,
        limit=5,
        filter_department_id=filter_department_id,
        filter_responsible_person_id=filter_responsible_person_id,
        filter_start_date=filter_start_date,
        filter_end_date=filter_end_date
    )
    my_responsible_todos_raw = get_responsible_todos(
        request.user,
        filter_department_id=filter_department_id,
        filter_responsible_person_id=filter_responsible_person_id,
        filter_start_date=filter_start_date,
        filter_end_date=filter_end_date
    )
    
    # 处理待办项，添加responsible字段用于显示
    my_responsible_todos = []
    for todo in my_responsible_todos_raw:
        todo_item = {
            'title': todo.get('title', ''),
            'description': todo.get('description', ''),
            'url': todo.get('url', '#'),
            'type': todo.get('type', ''),
            'priority': todo.get('priority', 'medium'),
            'deadline': todo.get('deadline'),
            'is_overdue': todo.get('is_overdue', False),
            'overdue_days': todo.get('overdue_days', 0),
            'meta': todo.get('description', ''),
        }
        if todo.get('object'):
            obj = todo['object']
            if hasattr(obj, 'get_full_name'):
                todo_item['responsible'] = obj.get_full_name() or obj.username
            elif hasattr(obj, 'username'):
                todo_item['responsible'] = obj.username
        my_responsible_todos.append(todo_item)
    
    category_data['mine'] = {
        'plan_status_dist': None,
        'goal_status_dist': None,
        'risk_items': my_responsible_risk_items[:5],
        'todo_items': my_responsible_todos[:10],
        'my_work': my_work,  # 使用现有的我的工作
        'goal_cards': context.get('my_goal_cards', []),
        'plan_cards': context.get('my_plan_cards', []),
    }
    
    # 3. 下属负责的分类的数据（仅部门负责人）
    if is_manager and subordinates.exists():
        # subordinate_responsible_plans_qs 和 subordinate_responsible_goals_qs 已在上面定义
        
        # 计划状态分布和目标状态分布已清除
        # 下属负责的风险项和待办项
        subordinate_responsible_risk_items = get_subordinates_risk_items(
            subordinates,
            limit=5,
            filter_department_id=filter_department_id,
            filter_responsible_person_id=filter_responsible_person_id,
            filter_start_date=filter_start_date,
            filter_end_date=filter_end_date
        )
        
        # 下属负责的待办项（汇总所有下属的待办）
        subordinate_responsible_todos = []
        for subordinate in subordinates[:10]:  # 最多查询10个下属
            sub_todos = get_responsible_todos(
                subordinate,
                filter_department_id=filter_department_id,
                filter_responsible_person_id=filter_responsible_person_id,
                filter_start_date=filter_start_date,
                filter_end_date=filter_end_date
            )
            for todo in sub_todos:
                todo_item = {
                    'title': todo.get('title', ''),
                    'description': todo.get('description', ''),
                    'url': todo.get('url', '#'),
                    'type': todo.get('type', ''),
                    'priority': todo.get('priority', 'medium'),
                    'deadline': todo.get('deadline'),
                    'is_overdue': todo.get('is_overdue', False),
                    'overdue_days': todo.get('overdue_days', 0),
                    'meta': f'负责人：{subordinate.get_full_name() or subordinate.username}',
                }
                subordinate_responsible_todos.append(todo_item)
        
        # 按优先级和时间排序
        priority_order = {'high': 0, 'medium': 1, 'low': 2}
        subordinate_responsible_todos.sort(key=lambda x: (priority_order.get(x['priority'], 2), x.get('deadline') or timezone.now()))
        
        # 下属负责的工作
        subordinate_plans = subordinate_responsible_plans_qs.select_related('responsible_person', 'related_goal').order_by('-updated_time')[:5]
        subordinate_goals = subordinate_responsible_goals_qs.select_related('responsible_person', 'parent_goal').order_by('-updated_time')[:5]
        
        subordinate_work = {
            'my_plans': [{
                'title': p.name,
                'progress': float(getattr(p, 'progress', 0) or 0),
                'progress_status': calculate_plan_progress_status(p),
                'url': reverse('plan_pages:plan_detail', args=[p.id])
            } for p in subordinate_plans],
            'my_plans_count': subordinate_responsible_plans_qs.count(),
            'my_goals': [{
                'title': g.name,
                'target_value': float(g.target_value) if g.target_value else 0,
                'current_value': float(g.current_value) if g.current_value else 0,
                'indicator_unit': g.indicator_unit or '',
                'completion_rate': float(getattr(g, 'completion_rate', 0) or 0),
                'progress_status': calculate_goal_progress_status(g),
                'url': reverse('plan_pages:strategic_goal_detail', args=[g.id])
            } for g in subordinate_goals],
            'my_goals_count': subordinate_responsible_goals_qs.count(),
            'participating_plans': [],
            'participating_plans_count': 0,
        }
        
        category_data['subordinate'] = {
            'plan_status_dist': None,
            'goal_status_dist': None,
            'risk_items': subordinate_responsible_risk_items[:5],
            'todo_items': subordinate_responsible_todos[:10],
            'my_work': subordinate_work,
            'goal_cards': context.get('subordinate_goal_cards', []),
            'plan_cards': context.get('subordinate_plan_cards', []),
        }
    
    # 4. 我协作的分类的数据
    # my_collaboration_plans_qs 和 my_collaboration_goals_qs 已在上面定义
    
    # 计划状态分布和目标状态分布已清除
    # 我协作的风险项和待办项（协作的项目通常不显示风险，因为负责人不同）
    my_collaboration_risk_items = []
    my_collaboration_todos = []
    
    # 我协作的工作
    my_collaboration_plans = my_collaboration_plans_qs.select_related('responsible_person', 'related_goal').order_by('-updated_time')[:5]
    my_collaboration_goals = my_collaboration_goals_qs.select_related('responsible_person', 'parent_goal').order_by('-updated_time')[:5]
    
    my_collaboration_work = {
        'my_plans': [{
            'title': p.name,
            'progress': float(getattr(p, 'progress', 0) or 0),
            'progress_status': calculate_plan_progress_status(p),
            'url': reverse('plan_pages:plan_detail', args=[p.id])
        } for p in my_collaboration_plans],
        'my_plans_count': my_collaboration_plans_qs.count(),
        'my_goals': [{
            'title': g.name,
            'target_value': float(g.target_value) if g.target_value else 0,
            'current_value': float(g.current_value) if g.current_value else 0,
            'indicator_unit': g.indicator_unit or '',
            'completion_rate': float(getattr(g, 'completion_rate', 0) or 0),
            'progress_status': calculate_goal_progress_status(g),
            'url': reverse('plan_pages:strategic_goal_detail', args=[g.id])
        } for g in my_collaboration_goals],
        'my_goals_count': my_collaboration_goals_qs.count(),
        'participating_plans': [],
        'participating_plans_count': 0,
    }
    
    category_data['collaboration'] = {
        'plan_status_dist': None,
        'goal_status_dist': None,
        'risk_items': my_collaboration_risk_items[:5],
        'todo_items': my_collaboration_todos[:10],
        'my_work': my_collaboration_work,
        'goal_cards': context.get('collaboration_goal_cards', []),
        'plan_cards': context.get('collaboration_plan_cards', []),
    }
    
    # 5. 下属协作的分类的数据（仅部门负责人）
    if is_manager and subordinates.exists():
        # subordinate_collaboration_plans_qs 和 subordinate_collaboration_goals_qs 已在上面定义
        
        # 计划状态分布和目标状态分布已清除
        # 下属协作的风险项和待办项
        subordinate_collaboration_risk_items = []
        subordinate_collaboration_todos = []
        
        # 下属协作的工作
        sub_collab_plans = subordinate_collaboration_plans_qs.select_related('responsible_person', 'related_goal').order_by('-updated_time')[:5]
        sub_collab_goals = subordinate_collaboration_goals_qs.select_related('responsible_person', 'parent_goal').order_by('-updated_time')[:5]
        
        subordinate_collaboration_work = {
            'my_plans': [{
                'title': p.name,
                'progress': float(getattr(p, 'progress', 0) or 0),
                'progress_status': calculate_plan_progress_status(p),
                'url': reverse('plan_pages:plan_detail', args=[p.id])
            } for p in sub_collab_plans],
            'my_plans_count': subordinate_collaboration_plans_qs.count(),
            'my_goals': [{
                'title': g.name,
                'target_value': float(g.target_value) if g.target_value else 0,
                'current_value': float(g.current_value) if g.current_value else 0,
                'indicator_unit': g.indicator_unit or '',
                'completion_rate': float(getattr(g, 'completion_rate', 0) or 0),
                'progress_status': calculate_goal_progress_status(g),
                'url': reverse('plan_pages:strategic_goal_detail', args=[g.id])
            } for g in sub_collab_goals],
            'my_goals_count': subordinate_collaboration_goals_qs.count(),
            'participating_plans': [],
            'participating_plans_count': 0,
        }
        
        category_data['subordinate_collaboration'] = {
            'plan_status_dist': None,
            'goal_status_dist': None,
            'risk_items': subordinate_collaboration_risk_items[:5],
            'todo_items': subordinate_collaboration_todos[:10],
            'my_work': subordinate_collaboration_work,
            'goal_cards': context.get('subordinate_collaboration_goal_cards', []),
            'plan_cards': context.get('subordinate_collaboration_plan_cards', []),
        }
    
    context['category_data'] = category_data
    
    # 构建上下文
    page_context = _context(
        page_title="计划管理",
        page_icon="📅",
        description="数据展示中心 - 集中展示计划与目标的关键指标、趋势和风险",
        summary_cards=[],  # 不再使用旧的summary_cards
        sections=[],  # 不再使用旧的sections
        request=request,
    )
    
    # 合并所有数据
    page_context.update(context)
    
    # 添加 sidebar_nav（与左侧栏同源，确保对齐）
    page_context['sidebar_nav'] = _build_plan_management_sidebar_nav(permission_codes, request_path=request.path, active_id='plan_home')
    page_context['sidebar_title'] = '计划管理'
    page_context['sidebar_subtitle'] = 'Plan Management'
    
    return render(request, "plan_management/plan_management_home.html", page_context)


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
    search = request.GET.get('search', '').strip()
    status_filter = request.GET.get('status', '').strip()
    level_filter = request.GET.get('level', '').strip()  # P2-3: 添加 level 过滤
    plan_type_filter = request.GET.get('plan_type', '').strip()
    plan_period_filter = request.GET.get('plan_period', '').strip()
    related_goal_filter = request.GET.get('related_goal', '').strip()
    responsible_id = request.GET.get('responsible_person', '').strip() or request.GET.get('responsible', '').strip()  # 兼容旧参数名
    date_from = request.GET.get('date_from', '').strip()
    date_to = request.GET.get('date_to', '').strip()
    risk_warning = request.GET.get('risk_warning', '').strip()  # 风险预警筛选
    
    # 查询计划
    # 注意：related_goal 现在允许为空（null=True），Django 会自动使用 LEFT OUTER JOIN
    # 注意：related_project 是 CharField，不是关系字段，不能用于 select_related
    plans = Plan.objects.select_related(
        'responsible_person', 'responsible_department', 'related_goal',
        'parent_plan', 'created_by', 'owner'
    ).prefetch_related('participants')
    
    # 根据权限过滤计划（权限通过后台管理系统配置）
    plans = _filter_plans_by_permission(plans, request.user, permission_set)
    
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
    
    # P2-3: level 过滤
    if level_filter:
        plans = plans.filter(level=level_filter)
    
    # 注意：plan_type 字段已在 P2-1 迁移中被 level 字段替代，保留此代码仅为向后兼容
    # 如果 URL 参数中有 plan_type，将其映射到 level
    if plan_type_filter:
        # plan_type 的旧值映射到 level 的新值
        plan_type_to_level_map = {
            'company': 'company',
            'personal': 'personal',
        }
        mapped_level = plan_type_to_level_map.get(plan_type_filter)
        if mapped_level:
            plans = plans.filter(level=mapped_level)
    
    if plan_period_filter:
        plans = plans.filter(plan_period=plan_period_filter)
    
    if related_goal_filter:
        plans = plans.filter(related_goal_id=related_goal_filter)
    
    if responsible_id:
        plans = plans.filter(responsible_person_id=responsible_id)
    
    if date_from:
        plans = plans.filter(start_time__date__gte=date_from)
    
    if date_to:
        plans = plans.filter(end_time__date__lte=date_to)
    
    # 风险预警筛选（逾期周计划）
    if risk_warning == 'overdue':
        plans = plans.filter(
            plan_period='weekly',
            is_overdue=True
        )
    
    # 排序
    plans = plans.order_by('-created_time')
    
    # 分页（每页10条）
    paginator = Paginator(plans, 10)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # 为分页后的计划对象添加can_delete和can_edit属性（只在当前页计算，提高效率）
    can_manage = _permission_granted('plan_management.plan.manage', permission_set)
    # 批量获取待审批决策，提高效率
    plan_ids = [p.id for p in page_obj]
    pending_decision_plan_ids = set(
        PlanDecision.objects.filter(
            plan_id__in=plan_ids, 
            decided_at__isnull=True
        ).values_list('plan_id', flat=True)
    )
    for plan in page_obj:
        # 负责人可以编辑自己负责的草稿计划，或者有管理权限的用户可以编辑
        # 但是如果有待审批的决策，则不允许编辑（提交给领导后不能修改）
        has_pending = plan.id in pending_decision_plan_ids
        plan.can_edit = (
            (plan.responsible_person == request.user or can_manage) and 
            plan.status in ['draft', 'cancelled'] and 
            not has_pending
        )
        plan.can_delete = (
            can_manage and 
            plan.status == 'draft' and 
            plan.get_child_plans_count() == 0 and
            not plan.decisions.filter(decision__isnull=True).exists()
        )
    
    # 统计信息：基于当前权限过滤后的 plans，与列表数据一致
    total_count = plans.count()
    draft_count = plans.filter(status='draft').count()
    in_progress_count = plans.filter(status='in_progress').count()
    completed_count = plans.filter(status='completed').count()
    cancelled_count = plans.filter(status='cancelled').count()
    
    # 风险预警统计（逾期周计划）
    overdue_weekly_plans_count = plans.filter(
        plan_period='weekly',
        is_overdue=True
    ).exclude(status__in=['completed', 'cancelled']).count()
    
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
    context['sidebar_nav'] = _build_plan_management_sidebar_nav(
        permission_set,
        request_path=request.path,
        active_id='plan_list'
    )
    context['sidebar_title'] = '计划管理'
    context['sidebar_subtitle'] = 'Plan Management'
    
    context.update({
        'page_obj': page_obj,
        'total_count': total_count,
        'draft_count': draft_count,
        'in_progress_count': in_progress_count,
        'completed_count': completed_count,
        'cancelled_count': cancelled_count,
        'all_users': all_users,
        'all_goals': all_goals,
        'search': search,
        'status_filter': status_filter,
        'level_filter': level_filter,  # P2-3: 添加 level 过滤
        'plan_type_filter': plan_type_filter,
        'plan_period_filter': plan_period_filter,
        'related_goal_filter': related_goal_filter,
        'responsible_filter': responsible_id,  # 保持向后兼容
        'date_from': date_from,
        'date_to': date_to,
        'risk_warning': risk_warning,
        'overdue_weekly_plans_count': overdue_weekly_plans_count,
        # 用于筛选表单
        'filters': {
            'status': status_filter,
            'responsible_person': responsible_id,
        },
        'status_options': Plan.STATUS_CHOICES,
        'responsible_options': all_users,
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
    level_filter = request.GET.get('level', '')  # P2-2: 添加 level 过滤
    goal_type_filter = request.GET.get('goal_type', '')
    goal_period_filter = request.GET.get('goal_period', '')
    responsible_filter = request.GET.get('responsible', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    # 查询目标
    goals = StrategicGoal.objects.select_related(
        'responsible_person', 'responsible_department', 'parent_goal', 'created_by', 'owner'
    ).prefetch_related('participants')
    
    # 根据权限过滤目标（权限通过后台管理系统配置）
    # 权限级别（从高到低）：
    # 1. view_all: 查看全部目标（包括其他人的个人目标）
    # 2. view_assigned: 查看本人负责或参与的目标，以及所有公司目标
    # 3. manage_goal: 只能查看公司目标和自己负责/参与的个人目标
    has_view_all = _permission_granted('plan_management.goal.view_all', permission_set)
    has_view_assigned = _permission_granted('plan_management.goal.view_assigned', permission_set)
    
    if not has_view_all:
        if has_view_assigned:
            # 只能看到自己负责或参与的目标，以及所有公司目标
            goals = goals.filter(
                Q(responsible_person=request.user) |
                Q(owner=request.user) |
                Q(participants=request.user) |
                Q(level='company')
            ).distinct()
        else:
            # 只有管理权限，只能看到公司目标和自己负责/参与的个人目标
            goals = goals.filter(
                Q(level='company') |
                Q(responsible_person=request.user) |
                Q(owner=request.user) |
                Q(participants=request.user)
            ).distinct()
    
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
    
    # P2-2: level 过滤
    if level_filter:
        goals = goals.filter(level=level_filter)
    
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
    
    # 分页（每页10条）
    paginator = Paginator(goals, 10)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # 为每个目标计算进度状态
    from django.utils import timezone
    from datetime import date
    today = date.today()
    
    for goal in page_obj:
        # 计算完成进度
        completion_progress = float(goal.completion_rate) if goal.completion_rate else 0
        
        # 判断进度状态
        if goal.end_date and goal.end_date < today:
            # 已过期
            if completion_progress >= 100:
                goal.progress_status = 'completed'
                goal.progress_status_label = '已完成'
                goal.progress_status_class = 'bg-success'
            else:
                goal.progress_status = 'overdue'
                goal.progress_status_label = '已逾期'
                goal.progress_status_class = 'bg-danger'
        elif goal.start_date and goal.start_date > today:
            # 未开始
            goal.progress_status = 'not_started'
            goal.progress_status_label = '未开始'
            goal.progress_status_class = 'bg-secondary'
        else:
            # 进行中，计算时间进度并比较完成进度
            if goal.start_date and goal.end_date:
                total_days = (goal.end_date - goal.start_date).days + 1
                if total_days > 0:
                    elapsed_days = max((today - goal.start_date).days + 1, 0)
                    time_progress = min((elapsed_days / total_days) * 100, 100)
                else:
                    time_progress = 0
            else:
                time_progress = 0
            
            # 比较完成进度和时间进度
            progress_diff = completion_progress - time_progress
            if completion_progress >= 100:
                goal.progress_status = 'ahead_completed'
                goal.progress_status_label = '提前完成'
                goal.progress_status_class = 'bg-success'
            elif progress_diff >= 10:
                goal.progress_status = 'ahead'
                goal.progress_status_label = '提前'
                goal.progress_status_class = 'bg-info'
            elif progress_diff >= -10:
                goal.progress_status = 'on_track'
                goal.progress_status_label = '正常'
                goal.progress_status_class = 'bg-primary'
            elif progress_diff >= -20:
                goal.progress_status = 'behind'
                goal.progress_status_label = '滞后'
                goal.progress_status_class = 'bg-warning'
            else:
                goal.progress_status = 'seriously_behind'
                goal.progress_status_label = '严重滞后'
                goal.progress_status_class = 'bg-danger'
    
    # 统计信息（所有状态）
    total_count = StrategicGoal.objects.count()
    draft_count = StrategicGoal.objects.filter(status='draft').count()
    published_count = StrategicGoal.objects.filter(status='published').count()
    in_progress_count = StrategicGoal.objects.filter(status='in_progress').count()
    completed_count = StrategicGoal.objects.filter(status='completed').count()
    cancelled_count = StrategicGoal.objects.filter(status='cancelled').count()
    
    # 获取所有用户（用于筛选）
    all_users = User.objects.filter(is_active=True).order_by('username')
    
    # 获取选择项数据（用于筛选下拉框）
    status_options = StrategicGoal.STATUS_CHOICES
    goal_type_choices = StrategicGoal.GOAL_TYPE_CHOICES
    goal_period_choices = StrategicGoal.GOAL_PERIOD_CHOICES
    level_choices = StrategicGoal.LEVEL_CHOICES
    
    context = _context(
        "目标列表",
        "🎯",
        "查看和管理所有战略目标",
        request=request,
    )
    
    # 生成左侧菜单
    context['sidebar_nav'] = _build_plan_management_sidebar_nav(
        permission_set,
        active_id='strategic_goal_list'
    )
    
    context.update({
        'page_obj': page_obj,  # 使用 page_obj 以匹配新模板
        'total_count': total_count,
        'draft_count': draft_count,
        'published_count': published_count,
        'in_progress_count': in_progress_count,
        'completed_count': completed_count,
        'cancelled_count': cancelled_count,
        'all_users': all_users,
        'search': search,
        'status_filter': status_filter,
        'level_filter': level_filter,  # P2-2
        'goal_type_filter': goal_type_filter,
        'goal_period_filter': goal_period_filter,
        'responsible_filter': responsible_filter,
        'date_from': date_from,
        'date_to': date_to,
        'status_options': status_options,
        'goal_type_choices': goal_type_choices,
        'goal_period_choices': goal_period_choices,
        'level_choices': level_choices,
    })
    
    return render(request, "plan_management/strategic_goal_list.html", context)


# ==================== 其他占位视图函数（待实现） ====================

@login_required
def plan_create(request):
    """计划创建页面"""
    
    permission_set = get_user_permission_codes(request.user)
    
    # 权限检查
    if not _permission_granted('plan_management.plan.create', permission_set):
        messages.error(request, '您没有权限创建计划')
        return redirect('plan_pages:plan_list')
    
    if request.method == 'POST':
        # 检查详细信息表格是否有数据
        formset_prefix = 'planitems'
        total_forms = int(request.POST.get(f'{formset_prefix}-TOTAL_FORMS', 0))
        has_formset_data = False
        for i in range(total_forms):
            # 检查该行是否被删除
            if request.POST.get(f'{formset_prefix}-{i}-DELETE'):
                continue
            # 检查该行是否有任何数据
            name = request.POST.get(f'{formset_prefix}-{i}-name', '').strip()
            goal = request.POST.get(f'{formset_prefix}-{i}-related_goal', '').strip()
            content = request.POST.get(f'{formset_prefix}-{i}-content', '').strip()
            objective = request.POST.get(f'{formset_prefix}-{i}-plan_objective', '').strip()
            start_time = request.POST.get(f'{formset_prefix}-{i}-start_time', '').strip()
            end_time = request.POST.get(f'{formset_prefix}-{i}-end_time', '').strip()
            if name or goal or content or objective or start_time or end_time:
                has_formset_data = True
                break
        
        # 如果详细信息表格有数据，基本信息表单的字段变为非必填
        form = PlanForm(request.POST, user=request.user, has_formset_data=has_formset_data)
        formset = PlanItemFormSet(request.POST, prefix='planitems', form_kwargs={'user': request.user})
        
        # 在表单验证前，先检查周计划的重复创建
        plan_period = request.POST.get('plan_period')
        responsible_person_id = request.POST.get('responsible_person')
        start_time_str = request.POST.get('start_time')
        
        if plan_period == 'weekly' and responsible_person_id and start_time_str:
            plan_period = request.POST.get('plan_period')
            responsible_person_id = request.POST.get('responsible_person')
            start_time_str = request.POST.get('start_time')
            
            if plan_period == 'weekly' and responsible_person_id and start_time_str:
                try:
                    from django.utils.dateparse import parse_date
                    from datetime import datetime as dt
                    
                    responsible_person = User.objects.get(id=int(responsible_person_id))
                    start_date = parse_date(start_time_str)
                    
                    if start_date:
                        # 计算周的开始日期（周一）和结束日期（周日）
                        days_since_monday = start_date.weekday()  # 0=Monday, 6=Sunday
                        week_start = start_date - timedelta(days=days_since_monday)
                        week_end = week_start + timedelta(days=6)
                        
                        # 查询同一用户在同一周内是否已有周计划
                        week_start_dt = timezone.make_aware(dt.combine(week_start, dt.min.time()))
                        week_end_dt = timezone.make_aware(dt.combine(week_end, dt.max.time()))
                        
                        existing_plans = Plan.objects.filter(
                            plan_period='weekly',
                            responsible_person=responsible_person,
                            status__in=['draft', 'published', 'accepted', 'in_progress']
                        ).filter(
                            start_time__lte=week_end_dt,
                            end_time__gte=week_start_dt
                        )
                        
                        if existing_plans.exists():
                            existing_plan = existing_plans.first()
                            # 使用模态框显示错误，而不是 messages
                            error_message = f'您在本周（{week_start.strftime("%Y-%m-%d")} 至 {week_end.strftime("%Y-%m-%d")}）已存在周计划（{existing_plan.name}），不能创建第二条周计划。请先完成或取消现有计划。'
                            # 重新渲染表单
                            context = _context("创建计划", "➕", "创建新的工作计划", request=request)
                            context['sidebar_nav'] = _build_plan_management_sidebar_nav(permission_set, active_id='plan_create')
                            context['form'] = form
                            context['formset'] = formset
                            context['page_title'] = "创建计划"
                            context['submit_text'] = "创建"
                            context['cancel_url_name'] = 'plan_pages:plan_list'
                            context['form_js_file'] = 'js/plan_form_date_calculator.js'
                            context['form_page_subtitle_text'] = '请填写计划基本信息'
                            context['weekly_plan_error'] = error_message  # 传递错误信息给模板
                            # 查询适用于计划的审批流程模板
                            from backend.apps.workflow_engine.models import WorkflowTemplate
                            available_workflows = WorkflowTemplate.objects.filter(
                                status='active',
                                applicable_models__contains=['plan']
                            ).order_by('name')
                            context['available_workflows'] = available_workflows
                            import json
                            context['workflow_details_json'] = json.dumps({str(wf.id): {
                                'name': wf.name,
                                'description': wf.description or '',
                                'allow_withdraw': wf.allow_withdraw,
                                'allow_reject': wf.allow_reject,
                                'allow_transfer': wf.allow_transfer,
                                'timeout_hours': wf.timeout_hours,
                                'timeout_action': wf.get_timeout_action_display() if wf.timeout_hours else None,
                            } for wf in available_workflows})
                            return render(request, "plan_management/plan_form.html", context)
                except (ValueError, User.DoesNotExist, TypeError):
                    # 如果解析失败，继续表单验证
                    pass
        
        # 表单验证
        form_valid = form.is_valid()
        formset_valid = formset.is_valid()
        
        if form_valid and formset_valid:
            # 保存计划列表（详细信息区域的计划项）
            # 注意：没有主计划与子计划的区分，所有计划都是平等的
            created_plans = []
            
            # 基本信息区域只保留所属部门、负责人、表单编号，不再创建计划
            # 所有计划都通过FormSet（详细信息区域）创建
            
            # 获取基本信息表单的默认值（用于 FormSet 中的计划项）
            # 基本信息区域只保留所属部门、负责人、表单编号，从表单中获取默认值
            form_obj = form.save(commit=False)
            default_responsible_person = form_obj.responsible_person or request.user
            default_responsible_department = form_obj.responsible_department or (request.user.responsible_department if hasattr(request.user, 'responsible_department') else None)
            # 从表单数据中获取 plan_period，如果没有则使用默认值
            default_plan_period = form_obj.plan_period or request.POST.get('plan_period') or 'monthly'
            default_level = form_obj.level or 'company'
            
            # 保存详细信息区域的计划列表
            # 先收集所有验证错误，而不是遇到第一个错误就返回
            validation_errors = []
            plan_items_to_save = []
            
            for planitem_form in formset:
                
                # 如果 cleaned_data 不存在，跳过（可能是空行）
                if not planitem_form.cleaned_data:
                    continue
                
                # 检查是否被标记为删除
                if planitem_form.cleaned_data.get('DELETE'):
                    continue
                
                # 检查该行是否有实际数据（不是空行）
                has_data = (
                    planitem_form.cleaned_data.get('name') or
                    planitem_form.cleaned_data.get('related_goal') or
                    planitem_form.cleaned_data.get('content') or
                    planitem_form.cleaned_data.get('plan_objective') or
                    planitem_form.cleaned_data.get('acceptance_criteria') or
                    planitem_form.cleaned_data.get('start_time') or
                    planitem_form.cleaned_data.get('end_time')
                )
                
                # 只有当该行有实际数据时才保存
                if has_data:
                        plan_item = planitem_form.save(commit=False)
                        # 继承基本信息区域的默认值（负责人、部门、周期等）
                        plan_item.responsible_person = default_responsible_person or request.user
                        plan_item.responsible_department = default_responsible_department or (request.user.responsible_department if hasattr(request.user, 'responsible_department') else None)
                        # 确保 plan_period 有值（必填字段）
                        plan_item.plan_period = default_plan_period or 'monthly'
                        plan_item.level = default_level or 'company'
                        # 日计划无须审批，创建即为发布；其他计划默认为草稿
                        if plan_item.plan_period == 'daily':
                            plan_item.status = 'published'
                            # 设置发布时间戳
                            if not plan_item.published_at:
                                from django.utils import timezone
                                plan_item.published_at = timezone.now()
                        else:
                            plan_item.status = 'draft'
                        
                        # 验证必填字段
                        missing_fields = []
                        if not plan_item.name or not plan_item.name.strip():
                            missing_fields.append('计划名称')
                        if not plan_item.content or not plan_item.content.strip():
                            missing_fields.append('计划内容')
                        if not plan_item.start_time:
                            missing_fields.append('计划开始时间')
                        if not plan_item.end_time:
                            missing_fields.append('计划结束时间')
                        if not plan_item.responsible_person:
                            missing_fields.append('计划负责人')
                        
                        if missing_fields:
                            validation_errors.append(f'第 {planitem_form.prefix} 行计划缺少必填字段：{", ".join(missing_fields)}')
                            continue  # 跳过这个计划项，不保存
                        
                        # 检查时间逻辑
                        if plan_item.start_time and plan_item.end_time and plan_item.start_time >= plan_item.end_time:
                            validation_errors.append(f'第 {planitem_form.prefix} 行计划的开始时间必须早于结束时间')
                            continue  # 跳过这个计划项，不保存
                        
                        # 不设置 parent_plan，所有计划都是平等的
                        # 生成计划编号
                        plan_item.plan_number = plan_item.generate_plan_number()
                        plan_item.created_by = request.user
                        plan_items_to_save.append((plan_item, planitem_form))
            
            # 如果有验证错误，在本页展示（不写入 messages，避免累积到登录页等）
            if validation_errors:
                if created_plans:
                    messages.warning(request, '部分计划已创建，但部分计划创建失败，请检查并重新创建。')
                    return redirect('plan_pages:plan_detail', plan_id=created_plans[0].id)
                context = _context("创建计划", "➕", "创建新的工作计划", request=request)
                context['sidebar_nav'] = _build_plan_management_sidebar_nav(permission_set, active_id='plan_create')
                context['form'] = form
                context['formset'] = formset
                context['validation_errors'] = validation_errors
                context['page_title'] = "创建计划"
                context['submit_text'] = "创建"
                context['cancel_url_name'] = 'plan_pages:plan_list'
                context['form_js_file'] = 'js/plan_form_date_calculator.js'
                context['form_page_subtitle_text'] = '请填写计划基本信息'
                from backend.apps.workflow_engine.models import WorkflowTemplate
                available_workflows = WorkflowTemplate.objects.filter(
                    status='active',
                    applicable_models__contains=['plan']
                ).order_by('name')
                context['available_workflows'] = available_workflows
                import json
                context['workflow_details_json'] = json.dumps({str(wf.id): {
                    'name': wf.name,
                    'description': wf.description or '',
                    'allow_withdraw': wf.allow_withdraw,
                    'allow_reject': wf.allow_reject,
                    'allow_transfer': wf.allow_transfer,
                    'timeout_hours': wf.timeout_hours,
                    'timeout_action': wf.get_timeout_action_display() if wf.timeout_hours else None,
                } for wf in available_workflows})
                return render(request, "plan_management/plan_form.html", context)
            
            # 保存所有通过验证的计划项
            for plan_item, planitem_form in plan_items_to_save:
                # 确保 plan_period 有值（数据库约束要求不能为空）
                if not plan_item.plan_period:
                    plan_item.plan_period = default_plan_period or 'monthly'
                
                try:
                    # 保存前记录旧状态（用于日志）
                    old_status = plan_item.status if plan_item.pk else None
                    plan_item.save()
                    
                    # 日计划创建即为发布，需要记录状态变更日志
                    if plan_item.plan_period == 'daily' and plan_item.status == 'published':
                        from .models import PlanStatusLog
                        PlanStatusLog.objects.create(
                            plan=plan_item,
                            old_status=old_status or '',
                            new_status='published',
                            changed_by=request.user,
                            change_reason='日计划创建即为发布（无须审批）'
                        )
                    
                    
                    # 保存多对多关系
                    if 'participants' in planitem_form.cleaned_data and planitem_form.cleaned_data['participants'] is not None:
                        # 确保 participants 是可迭代对象（不能是 None）
                        participants = planitem_form.cleaned_data['participants']
                        if participants:
                            plan_item.participants.set(participants)
                        else:
                            plan_item.participants.clear()
                    created_plans.append(plan_item)
                except Exception as e:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.exception('保存计划项失败: %s', str(e))
                    
                    validation_errors.append(f'第 {planitem_form.prefix} 行计划保存失败：{str(e)}')
                    continue
            
            # 如果保存后有验证错误，在本页展示（不写入 messages）
            if validation_errors:
                if created_plans:
                    messages.warning(request, '部分计划已创建，但部分计划创建失败，请检查并重新创建。')
                    return redirect('plan_pages:plan_detail', plan_id=created_plans[0].id)
                context = _context("创建计划", "➕", "创建新的工作计划", request=request)
                context['sidebar_nav'] = _build_plan_management_sidebar_nav(permission_set, active_id='plan_create')
                context['form'] = form
                context['formset'] = formset
                context['validation_errors'] = validation_errors
                context['page_title'] = "创建计划"
                context['submit_text'] = "创建"
                context['cancel_url_name'] = 'plan_pages:plan_list'
                context['form_js_file'] = 'js/plan_form_date_calculator.js'
                context['form_page_subtitle_text'] = '请填写计划基本信息'
                from backend.apps.workflow_engine.models import WorkflowTemplate
                available_workflows = WorkflowTemplate.objects.filter(
                    status='active',
                    applicable_models__contains=['plan']
                ).order_by('name')
                context['available_workflows'] = available_workflows
                import json
                context['workflow_details_json'] = json.dumps({str(wf.id): {
                    'name': wf.name,
                    'description': wf.description or '',
                    'allow_withdraw': wf.allow_withdraw,
                    'allow_reject': wf.allow_reject,
                    'allow_transfer': wf.allow_transfer,
                    'timeout_hours': wf.timeout_hours,
                    'timeout_action': wf.get_timeout_action_display() if wf.timeout_hours else None,
                } for wf in available_workflows})
                return render(request, "plan_management/plan_form.html", context)
            
            if not created_plans:
                # 如果没有创建任何计划，可能是所有行都是空的（本页展示，不写入 messages）
                context = _context("创建计划", "➕", "创建新的工作计划", request=request)
                context['sidebar_nav'] = _build_plan_management_sidebar_nav(permission_set, active_id='plan_create')
                context['form'] = form
                context['formset'] = formset
                context['form_validation_errors'] = ['请至少填写一个计划的完整信息']
                context['page_title'] = "创建计划"
                context['submit_text'] = "创建"
                context['cancel_url_name'] = 'plan_pages:plan_list'
                context['form_js_file'] = 'js/plan_form_date_calculator.js'
                context['form_page_subtitle_text'] = '请填写计划基本信息'
                from backend.apps.workflow_engine.models import WorkflowTemplate
                available_workflows = WorkflowTemplate.objects.filter(
                    status='active',
                    applicable_models__contains=['plan']
                ).order_by('name')
                context['available_workflows'] = available_workflows
                import json
                context['workflow_details_json'] = json.dumps({str(wf.id): {
                    'name': wf.name,
                    'description': wf.description or '',
                    'allow_withdraw': wf.allow_withdraw,
                    'allow_reject': wf.allow_reject,
                    'allow_transfer': wf.allow_transfer,
                    'timeout_hours': wf.timeout_hours,
                    'timeout_action': wf.get_timeout_action_display() if wf.timeout_hours else None,
                } for wf in available_workflows})
                return render(request, "plan_management/plan_form.html", context)
            
            
            # 创建按钮功能：直接创建计划
            # 日计划无须审批，创建即为发布；其他计划默认为草稿，用户可以在详情页手动提交审批
            daily_plans_count = sum(1 for p in created_plans if p.plan_period == 'daily')
            other_plans_count = len(created_plans) - daily_plans_count
            
            if daily_plans_count > 0:
                messages.success(request, f'成功创建 {daily_plans_count} 个日计划（已自动发布）')
            if other_plans_count > 0:
                messages.info(request, f'成功创建 {other_plans_count} 个计划（草稿状态），您可以在详情页提交审批')
            
            # 跳转到第一个计划的详情页
            # 确保 created_plans 不为空（这应该不会发生，因为上面已经检查过了）
            if created_plans and len(created_plans) > 0:
                
                return redirect('plan_pages:plan_detail', plan_id=created_plans[0].id)
            else:
                # 如果 somehow created_plans 为空，本页展示错误（不写入 messages）
                context = _context("创建计划", "➕", "创建新的工作计划", request=request)
                context['sidebar_nav'] = _build_plan_management_sidebar_nav(permission_set, active_id='plan_create')
                context['form'] = form
                context['formset'] = formset
                context['form_validation_errors'] = ['未能成功创建任何计划，请检查表单数据']
                context['page_title'] = "创建计划"
                context['submit_text'] = "创建"
                context['cancel_url_name'] = 'plan_pages:plan_list'
                context['form_js_file'] = 'js/plan_form_date_calculator.js'
                context['form_page_subtitle_text'] = '请填写计划基本信息'
                from backend.apps.workflow_engine.models import WorkflowTemplate
                available_workflows = WorkflowTemplate.objects.filter(
                    status='active',
                    applicable_models__contains=['plan']
                ).order_by('name')
                context['available_workflows'] = available_workflows
                import json
                context['workflow_details_json'] = json.dumps({str(wf.id): {
                    'name': wf.name,
                    'description': wf.description or '',
                    'allow_withdraw': wf.allow_withdraw,
                    'allow_reject': wf.allow_reject,
                    'allow_transfer': wf.allow_transfer,
                    'timeout_hours': wf.timeout_hours,
                    'timeout_action': wf.get_timeout_action_display() if wf.timeout_hours else None,
                } for wf in available_workflows})
                return render(request, "plan_management/plan_form.html", context)
        else:
            # 表单/FormSet 校验失败：本页展示纯文本错误（不写入 messages，避免累积到登录页；不用 str(errors) 避免 HTML）
            error_messages = []
            if not form.is_valid():
                error_messages.append('基本信息表单验证失败：')
                for field, errors in form.errors.items():
                    error_messages.append(f'  - {field}: {", ".join(str(e) for e in errors)}')
            if not formset.is_valid():
                error_messages.append('详细信息表单验证失败：')
                nf = formset.non_form_errors()
                if nf:
                    error_messages.append(f'  - {", ".join(str(e) for e in nf)}')
                for i, form_item in enumerate(formset):
                    if form_item.errors:
                        error_messages.append(f'  第 {i+1} 行: {_form_errors_plain(form_item)}')
                    if form_item.non_field_errors():
                        error_messages.append(f'  第 {i+1} 行: {", ".join(str(e) for e in form_item.non_field_errors())}')
            if not error_messages:
                error_messages.append('表单验证失败，请检查输入')
            context = _context("创建计划", "➕", "创建新的工作计划", request=request)
            context['sidebar_nav'] = _build_plan_management_sidebar_nav(permission_set, active_id='plan_create')
            context['form'] = form
            context['formset'] = formset
            context['form_validation_errors'] = error_messages
            context['page_title'] = "创建计划"
            context['submit_text'] = "创建"
            context['cancel_url_name'] = 'plan_pages:plan_list'
            context['form_js_file'] = 'js/plan_form_date_calculator.js'
            context['form_page_subtitle_text'] = '请填写计划基本信息'
            return render(request, "plan_management/plan_form.html", context)
    else:
        # GET 请求：从 URL 参数中读取 plan_period（用于待办事项跳转）
        plan_period_from_url = request.GET.get('plan_period', '').strip()
        initial_data = {}
        if plan_period_from_url:
            initial_data['plan_period'] = plan_period_from_url
        
        form = PlanForm(user=request.user, initial=initial_data)
        formset = PlanItemFormSet(prefix='planitems', form_kwargs={'user': request.user})
    
    # 查询适用于计划的审批流程模板
    from backend.apps.workflow_engine.models import WorkflowTemplate
    available_workflows = WorkflowTemplate.objects.filter(
        status='active',
        applicable_models__contains=['plan']
    ).order_by('name')
    
    context = _context("创建计划", "➕", "创建新的工作计划", request=request)
    context['sidebar_nav'] = _build_plan_management_sidebar_nav(permission_set, active_id='plan_create')
    context['form'] = form
    context['formset'] = formset
    context['page_title'] = "创建计划"
    context['submit_text'] = "创建"
    context['cancel_url_name'] = 'plan_pages:plan_list'
    context['form_js_file'] = 'js/plan_form_date_calculator.js'
    context['form_page_subtitle_text'] = '请填写计划基本信息'
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
            'parent_plan', 'created_by', 'owner'
        ).prefetch_related('participants', 'child_plans'),
        id=plan_id
    )
    
    # 权限检查：员工只能查看本人的计划（owner 或 responsible_person）
    # 仅显式 plan_management.plan.view_all 可查看任意计划（不含 __all__）
    has_view_all = 'plan_management.plan.view_all' in permission_set
    if not has_view_all:
        is_owner = plan.owner == request.user
        is_responsible = plan.responsible_person == request.user
        if not (is_owner or is_responsible):
            messages.error(request, '您没有权限查看该计划')
            return redirect('plan_pages:plan_list')
    
    # 获取进度记录
    progress_records = PlanProgressRecord.objects.filter(
        plan=plan
    ).select_related('recorded_by').order_by('-recorded_time')[:10]
    
    # 获取状态日志（显示所有记录，不限制数量）
    status_logs = PlanStatusLog.objects.filter(
        plan=plan
    ).select_related('changed_by').order_by('-changed_time')
    
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
    
    # 获取关联信息（用于关联信息卡片）
    # 关联项目（如果有）
    related_projects = []
    try:
        from backend.apps.production_management.models import Project
        related_projects = Project.objects.filter(related_plan=plan).select_related(
            'project_manager'
        ).order_by('-created_time')[:20]
    except Exception:
        pass
    
    # 获取审计日志（用于审计信息卡片）
    audit_logs = []
    try:
        from backend.apps.system_management.models import AuditLog
        
        # 使用 _meta.label 格式（如 "plan_management.Plan"）
        object_type = Plan._meta.label
        audit_logs = AuditLog.objects.filter(
            object_type=object_type,
            object_id=str(plan.id)
        ).select_related('actor').order_by('-created_time')[:50]
    except Exception:
        # AuditLog 不存在或查询失败，使用空列表
        pass
    
    # 获取审批实例（用于审批信息卡片）
    approval_instances = []
    try:
        from django.contrib.contenttypes.models import ContentType
        from backend.apps.workflow_engine.models import ApprovalInstance
        
        content_type = ContentType.objects.get_for_model(Plan)
        approval_instances = ApprovalInstance.objects.filter(
            content_type=content_type,
            object_id=plan.id
        ).select_related('workflow', 'applicant', 'current_node').prefetch_related(
            'records__node', 'records__approver', 'records__transferred_to'
        ).order_by('-created_time')
        
        # 对每个实例的审批记录进行排序（按节点序号和时间）
        for instance in approval_instances:
            instance.records_sorted = sorted(
                instance.records.all(),
                key=lambda r: (r.node.sequence if r.node else 999, r.approval_time or r.created_time)
            )
    except Exception:
        # ApprovalInstance 不存在或查询失败，使用空列表
        pass
    
    # 获取附件（用于附件与文件信息卡片）
    attachments = []
    try:
        from django.contrib.contenttypes.models import ContentType
        from .models import Attachment
        
        content_type = ContentType.objects.get_for_model(Plan)
        attachments = Attachment.objects.filter(
            content_type=content_type,
            object_id=plan.id
        ).select_related('uploaded_by').order_by('-uploaded_at')
    except Exception:
        # Attachment 不存在或查询失败，使用空列表
        pass
    
    # 计算时间进度
    def _progress_percent(plan):
        if not plan.start_time or not plan.end_time:
            return None
        
        from datetime import date
        from django.utils import timezone
        
        def to_date(v):
            return v.date() if hasattr(v, "date") else v
        
        start = to_date(plan.start_time)
        end = to_date(plan.end_time)
        today = timezone.localdate()
        
        if end <= start:
            return 0
        
        if today <= start:
            return 0
        if today >= end:
            return 100
        
        total = (end - start).days
        passed = (today - start).days
        pct = int(round(passed * 100 / total))
        return max(0, min(100, pct))
    
    progress_percent = _progress_percent(plan)
    
    context = _context(
        f"计划详情 - {plan.name}",
        "📋",
        plan.name,
        request=request,
    )
    context['sidebar_nav'] = _build_plan_management_sidebar_nav(permission_set, active_id='plan_list')
    
    # P1: 权限判断（围绕 decision 的裁决）
    # 检查是否存在 pending 的决策（同时检查审批引擎和 PlanDecision）
    from django.contrib.contenttypes.models import ContentType
    from backend.apps.workflow_engine.models import ApprovalInstance
    from backend.apps.plan_management.services.plan_approval import PlanApprovalService
    
    plan_content_type = ContentType.objects.get_for_model(Plan)
    
    # 检查审批引擎中的待审批实例
    has_pending_start_approval = ApprovalInstance.objects.filter(
        content_type=plan_content_type,
        object_id=plan.id,
        workflow__code=PlanApprovalService.PLAN_START_WORKFLOW_CODE,
        status__in=['pending', 'in_progress']
    ).exists()
    
    has_pending_cancel_approval = ApprovalInstance.objects.filter(
        content_type=plan_content_type,
        object_id=plan.id,
        workflow__code=PlanApprovalService.PLAN_CANCEL_WORKFLOW_CODE,
        status__in=['pending', 'in_progress']
    ).exists()
    
    # 检查 PlanDecision（向后兼容）
    has_pending_start_decision = PlanDecision.objects.filter(plan=plan, request_type='start', decided_at__isnull=True).exists()
    has_pending_cancel_decision = PlanDecision.objects.filter(plan=plan, request_type='cancel', decided_at__isnull=True).exists()
    
    # 合并结果（任一方式有 pending 都算有 pending）
    has_pending_start = has_pending_start_approval or has_pending_start_decision
    has_pending_cancel = has_pending_cancel_approval or has_pending_cancel_decision
    
    # 获取待审批的决策列表（用于审批人）
    # 优先显示审批引擎的审批实例
    pending_approval_instances = ApprovalInstance.objects.filter(
        content_type=plan_content_type,
        object_id=plan.id,
        status__in=['pending', 'in_progress']
    ).order_by('-created_time')
    
    # 向后兼容：也显示 PlanDecision
    pending_decisions = PlanDecision.objects.filter(plan=plan, decided_at__isnull=True).order_by('-requested_at')
    
    can_approve = _permission_granted('plan_management.approve_plan', permission_set) or request.user.is_superuser
    
    # 获取当前用户可以审批的审批实例（用于三栏布局）
    current_approval_instance = None
    if can_approve and pending_approval_instances.exists():
        from backend.apps.workflow_engine.services import ApprovalEngine
        user_pending_approvals = ApprovalEngine.get_pending_approvals(request.user)
        # 找到当前计划中用户可以审批的实例
        for instance in pending_approval_instances:
            if instance in user_pending_approvals:
                current_approval_instance = instance
                break
        # 如果没找到，取第一个待审批实例（用于显示状态）
        if not current_approval_instance and pending_approval_instances.exists():
            current_approval_instance = pending_approval_instances.first()
        
        # 为当前审批实例添加排序后的审批记录
        if current_approval_instance:
            current_approval_instance.records_sorted = sorted(
                current_approval_instance.records.all(),
                key=lambda r: (r.node.sequence if r.node else 999, r.approval_time or r.created_time)
            )
    
    # 获取所有用户列表（用于转交）
    from django.contrib.auth import get_user_model
    User = get_user_model()
    all_users = User.objects.filter(is_active=True).order_by('username')[:100]
    
    # P1: 权限判断（围绕 decision 的裁决）
    # 允许草稿和已取消状态的计划提交审批
    # 检查权限：plan_management.plan.create 或负责人
    has_create_permission = _permission_granted('plan_management.plan.create', permission_set)
    is_responsible = plan.responsible_person == request.user
    is_valid_status = plan.status in ['draft', 'cancelled']
    
    # 计算是否可以提交审批（需要权限、状态正确、无待审批请求）
    # 注意：字段验证已在创建/编辑时完成，这里不再检查数据完整性
    can_submit_approval = (has_create_permission or is_responsible) and is_valid_status and not has_pending_start
    can_request_cancel = (has_create_permission or is_responsible) and plan.status == 'in_progress' and not has_pending_cancel
    
    # 检查是否可以申请调整
    can_manage = _permission_granted('plan_management.plan.manage', permission_set) or request.user.is_superuser
    is_responsible = plan.responsible_person == request.user
    can_request_adjustment = (can_manage or is_responsible) and plan.status == 'in_progress'
    has_pending_adjustment = PlanAdjustment.objects.filter(plan=plan, status='pending').exists()
    
    # P2-3: 接收计划（published → accepted）
    if request.method == 'POST' and 'accept_plan' in request.POST:
        if plan.status == 'published':
            # 检查权限：只有 owner 可以接收个人计划
            if plan.level == 'personal':
                if plan.owner != request.user:
                    messages.error(request, '只有计划所有者可以接收此计划')
                    return redirect('plan_pages:plan_detail', plan_id=plan_id)
            
            try:
                plan.transition_to('accepted', user=request.user)
                
                # P2-4: 通知计划被接收
                from .notifications import notify_plan_accepted
                notify_plan_accepted(plan, request.user)
                
                messages.success(request, '计划已接收')
                return redirect('plan_pages:plan_detail', plan_id=plan_id)
            except ValueError as e:
                messages.error(request, str(e))
        else:
            messages.error(request, '只有已发布状态的计划可以接收')
    
    # P2-3: 开始执行（accepted → in_progress）
    if request.method == 'POST' and 'start_execution' in request.POST:
        # P2-3 补强：禁止未接收计划的开始执行
        if plan.level == 'personal' and plan.status == 'published':
            messages.error(request, '计划尚未接收，不能开始执行。请先接收计划。')
            return redirect('plan_pages:plan_detail', plan_id=plan_id)
        
        if plan.status == 'accepted':
            try:
                plan.transition_to('in_progress', user=request.user)
                messages.success(request, '计划已开始执行')
                return redirect('plan_pages:plan_detail', plan_id=plan_id)
            except ValueError as e:
                messages.error(request, str(e))
        else:
            messages.error(request, '只有已接收状态的计划可以开始执行')
    
    # P2-3: 检查操作权限
    can_accept = False
    if plan.status == 'published':
        if plan.level == 'personal':
            can_accept = plan.owner == request.user
        else:
            # 公司计划：所有用户都可以接收（简化版）
            can_accept = True
    
    can_start_execution = plan.status == 'accepted'
    
    # 确保 attachments 变量已定义（防止在某些代码路径中未定义）
    try:
        # 检查 attachments 是否已定义
        _ = attachments
    except NameError:
        # 如果未定义，则初始化
        attachments = []
        try:
            from django.contrib.contenttypes.models import ContentType
            from .models import Attachment
            
            content_type = ContentType.objects.get_for_model(Plan)
            attachments = Attachment.objects.filter(
                content_type=content_type,
                object_id=plan.id
            ).select_related('uploaded_by').order_by('-uploaded_at')
        except Exception:
            # Attachment 不存在或查询失败，使用空列表
            attachments = []
    
    context.update({
        'plan': plan,
        'object': plan,  # 为 detail_base.html 模板提供 object 变量
        'progress_records': progress_records,
        'status_logs': status_logs,
        'issues': issues,
        'child_plans': child_plans,
        'related_projects': related_projects,  # 关联信息
        'audit_logs': audit_logs,  # 审计信息
        'approval_instances': approval_instances,  # 审批信息
        'attachments': attachments,  # 附件信息
        'inactivity_logs': inactivity_logs,  # P2: 不作为记录
        'progress_percent': progress_percent,  # 时间进度百分比
        'can_edit': (
            (plan.responsible_person == request.user or _permission_granted('plan_management.plan.manage', permission_set)) and 
            plan.status in ['draft', 'cancelled'] and 
            not has_pending_start and 
            not has_pending_cancel
        ),
        'can_delete': (
            _permission_granted('plan_management.plan.manage', permission_set) and 
            plan.status == 'draft' and
            plan.get_child_plans_count() == 0 and
            not pending_decisions.exists() and
            not pending_approval_instances.exists()
        ),
        # P1 新增权限
        'can_submit_approval': can_submit_approval,
        'can_request_cancel': can_request_cancel,
        'pending_decisions': pending_decisions,  # 向后兼容
        'pending_approval_instances': pending_approval_instances,  # 审批引擎的审批实例
        'current_approval_instance': current_approval_instance,  # 当前用户可以审批的实例（用于三栏布局）
        'all_users': all_users,  # 所有用户列表（用于转交）
        'can_approve': can_approve,
        # 计划调整申请权限
        'can_request_adjustment': can_request_adjustment and not has_pending_adjustment,
        # P2-3: 接收和开始执行权限
        'can_accept': can_accept,
        'can_start_execution': can_start_execution,
    })
    
    # 检查是否使用三栏布局模板（可以通过URL参数或设置控制）
    use_three_column = request.GET.get('layout') == 'three_column' or False
    template_name = "plan_management/plan_detail_three_column.html" if use_three_column else "plan_management/plan_detail.html"
    
    return render(request, template_name, context)


@login_required
def plan_edit(request, plan_id):
    """计划编辑页面"""
    permission_set = get_user_permission_codes(request.user)
    
    plan = get_object_or_404(Plan, id=plan_id)
    
    # 检查是否有待审批的决策（提交审批后不能编辑）
    # 同时检查审批引擎和 PlanDecision
    from django.contrib.contenttypes.models import ContentType
    from backend.apps.workflow_engine.models import ApprovalInstance
    from backend.apps.plan_management.services.plan_approval import PlanApprovalService
    
    plan_content_type = ContentType.objects.get_for_model(Plan)
    has_pending_approval = ApprovalInstance.objects.filter(
        content_type=plan_content_type,
        object_id=plan.id,
        status__in=['pending', 'in_progress']
    ).exists()
    has_pending_decision = PlanDecision.objects.filter(plan=plan, decided_at__isnull=True).exists()
    has_pending_decision = has_pending_approval or has_pending_decision
    
    # 检查是否可以编辑：允许草稿和已取消状态的计划编辑
    # 负责人可以编辑自己负责的草稿计划，或者有管理权限的用户可以编辑
    # 但是如果有待审批的决策，则不允许编辑（提交给领导后不能修改）
    can_edit = (
        plan.status in ['draft', 'cancelled'] and 
        not has_pending_decision and
        (plan.responsible_person == request.user or _permission_granted('plan_management.plan.manage', permission_set))
    )
    if not can_edit:
        if has_pending_decision:
            messages.error(request, '计划已提交审批，审批期间不能编辑。请等待审批结果。')
        elif plan.status not in ['draft', 'cancelled']:
            messages.error(request, '只有草稿或已取消状态的计划可以编辑')
        else:
            messages.error(request, '您没有权限编辑此计划（只有负责人或有管理权限的用户可以编辑）')
        return redirect('plan_pages:plan_detail', plan_id=plan_id)
    
    if request.method == 'POST':
        form = PlanForm(request.POST, instance=plan, user=request.user)
        if form.is_valid():
            # 如果计划是已取消状态，编辑后需要恢复为草稿状态并记录日志
            old_status = plan.status
            plan = form.save(commit=False)
            
            # 验证必填字段
            missing_fields = []
            if not plan.name or not plan.name.strip():
                missing_fields.append('计划名称')
            if not plan.content or not plan.content.strip():
                missing_fields.append('计划内容')
            if not plan.start_time:
                missing_fields.append('计划开始时间')
            if not plan.end_time:
                missing_fields.append('计划结束时间')
            if not plan.responsible_person:
                missing_fields.append('计划负责人')
            
            if missing_fields:
                error_msg = f'保存失败：请填写以下必填字段：{", ".join(missing_fields)}'
                # 使用 context 传递错误，不写入 messages
                formset = PlanItemFormSet(prefix='planitems', form_kwargs={'user': request.user})
                context = _context(
                    f"编辑计划 - {plan.name}",
                    "✏️",
                    "编辑工作计划",
                    request=request,
                )
                context['sidebar_nav'] = _build_plan_management_sidebar_nav(permission_set, active_id='plan_list')
                context['form'] = form
                context['formset'] = formset
                context['plan'] = plan
                context['page_title'] = f"编辑计划 - {plan.name}"
                context['submit_text'] = "保存"
                context['cancel_url'] = reverse('plan_pages:plan_detail', args=[plan.id])
                context['form_js_file'] = 'js/plan_form_date_calculator.js'
                context['form_page_subtitle_text'] = '请修改计划信息'
                context['form_validation_errors'] = [error_msg]
                return render(request, "plan_management/plan_form.html", context)
            
            # 检查时间逻辑
            if plan.start_time and plan.end_time and plan.start_time >= plan.end_time:
                error_msg = '保存失败：计划开始时间必须早于结束时间'
                # 使用 context 传递错误，不写入 messages
                formset = PlanItemFormSet(prefix='planitems', form_kwargs={'user': request.user})
                context = _context(
                    f"编辑计划 - {plan.name}",
                    "✏️",
                    "编辑工作计划",
                    request=request,
                )
                context['sidebar_nav'] = _build_plan_management_sidebar_nav(permission_set, active_id='plan_list')
                context['form'] = form
                context['formset'] = formset
                context['plan'] = plan
                context['page_title'] = f"编辑计划 - {plan.name}"
                context['submit_text'] = "保存"
                context['cancel_url'] = reverse('plan_pages:plan_detail', args=[plan.id])
                context['form_js_file'] = 'js/plan_form_date_calculator.js'
                context['form_page_subtitle_text'] = '请修改计划信息'
                context['form_validation_errors'] = [error_msg]
                return render(request, "plan_management/plan_form.html", context)
            
            plan = form.save()
            
            # 如果计划从已取消状态恢复为草稿，记录状态变更日志
            if old_status == 'cancelled':
                from django.db import transaction
                try:
                    with transaction.atomic():
                        plan.status = 'draft'
                        plan.save(update_fields=['status'])
                        
                        # 记录状态变更日志
                        PlanStatusLog.objects.create(
                            plan=plan,
                            old_status=old_status,
                            new_status='draft',
                            changed_by=request.user,
                            change_reason='已取消的计划重新编辑，状态恢复为草稿'
                        )
                except Exception as e:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(f'记录状态变更日志失败: {e}', exc_info=True)
                    messages.error(request, f'状态变更记录失败: {str(e)}')
                    return redirect('plan_pages:plan_detail', plan_id=plan.id)
            
            messages.success(request, f'计划 {plan.name} 更新成功')
            return redirect('plan_pages:plan_detail', plan_id=plan.id)
        else:
            # 使用 context 传递错误，不写入 messages
            # 提取表单错误信息
            error_messages = []
            if form.errors:
                error_messages.append(_form_errors_plain(form))
            if not error_messages:
                error_messages.append('表单验证失败，请检查输入')
            
            # 创建空的 formset（编辑页面不使用 FormSet）
            formset = PlanItemFormSet(prefix='planitems', form_kwargs={'user': request.user})
            # 关键：无效就回渲染，不要 redirect
            context = _context(
                f"编辑计划 - {plan.name}",
                "✏️",
                "编辑工作计划",
                request=request,
            )
            context['sidebar_nav'] = _build_plan_management_sidebar_nav(permission_set, active_id='plan_list')
            context['form'] = form
            context['formset'] = formset
            context['plan'] = plan
            context['page_title'] = f"编辑计划 - {plan.name}"
            context['submit_text'] = "保存"
            context['cancel_url'] = reverse('plan_pages:plan_detail', args=[plan.id])
            context['form_js_file'] = 'js/plan_form_date_calculator.js'
            context['form_page_subtitle_text'] = '请修改计划信息'
            context['form_validation_errors'] = error_messages
            return render(request, "plan_management/plan_form.html", context)
    else:
        form = PlanForm(instance=plan, user=request.user)
        # 创建空的 formset（编辑页面不使用 FormSet）
        formset = PlanItemFormSet(prefix='planitems', form_kwargs={'user': request.user})
    
    context = _context(
        f"编辑计划 - {plan.name}",
        "✏️",
        "编辑工作计划",
        request=request,
    )
    context['sidebar_nav'] = _build_plan_management_sidebar_nav(permission_set, active_id='plan_list')
    context['form'] = form
    context['formset'] = formset
    context['plan'] = plan
    context['page_title'] = f"编辑计划 - {plan.name}"
    context['submit_text'] = "保存"
    context['cancel_url'] = reverse('plan_pages:plan_detail', args=[plan.id])
    context['form_js_file'] = 'js/plan_form_date_calculator.js'
    context['form_page_subtitle_text'] = '请修改计划信息'
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
    search = request.GET.get('search', '').strip()
    status_filter = request.GET.get('status', '')
    level_filter = request.GET.get('level', '')
    plan_type_filter = request.GET.get('plan_type', '')  # 向后兼容
    plan_period_filter = request.GET.get('plan_period', '')
    responsible_filter = request.GET.get('responsible_person', '')
    related_goal_filter = request.GET.get('related_goal', '')
    
    # 查询可分解的计划（排除已取消的计划）
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
    
    # P2-3: level 过滤（优先使用 level）
    if level_filter:
        plans = plans.filter(level=level_filter)
    # 注意：plan_type 字段已在 P2-1 迁移中被 level 字段替代，保留此代码仅为向后兼容
    elif plan_type_filter:
        # plan_type 的旧值映射到 level 的新值
        plan_type_to_level_map = {
            'personal': 'personal',
            'department': 'company',  # 部门计划映射为公司计划
            'company': 'company',
            'project': 'company',  # 项目计划映射为公司计划
        }
        mapped_level = plan_type_to_level_map.get(plan_type_filter)
        if mapped_level:
            plans = plans.filter(level=mapped_level)
    
    if plan_period_filter:
        plans = plans.filter(plan_period=plan_period_filter)
    
    if responsible_filter:
        plans = plans.filter(responsible_person_id=responsible_filter)
    
    if related_goal_filter:
        plans = plans.filter(related_goal_id=related_goal_filter)
    
    # 排序：优先显示已审批和执行中的计划
    plans = plans.order_by('-status', '-created_time')
    
    # 分页
    page_size = request.GET.get('page_size', '10')
    try:
        per_page = int(page_size)
        if per_page not in [10, 20, 50, 100]:
            per_page = 10
    except (ValueError, TypeError):
        per_page = 10
    
    paginator = Paginator(plans, per_page)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # 统计信息（基于原始查询，不受筛选影响）
    base_plans = Plan.objects.exclude(status='cancelled')
    total_count = base_plans.count()
    in_progress_count = base_plans.filter(status='in_progress').count()
    draft_count = base_plans.filter(status='draft').count()
    completed_count = base_plans.filter(status='completed').count()
    
    # 获取所有用户（用于筛选）
    all_users = User.objects.filter(is_active=True).order_by('username')
    
    # 获取所有战略目标（用于筛选）
    all_goals = StrategicGoal.objects.filter(
        status__in=['published', 'in_progress']
    ).order_by('name')
    
    context = _context(
        "计划分解",
        "📊",
        "选择要分解的计划",
        request=request,
    )
    context['sidebar_nav'] = _build_plan_management_sidebar_nav(permission_set, active_id='plan_decompose')
    context.update({
        'page_obj': page_obj,
        'plans': list(page_obj),  # 保持向后兼容
        'all_users': all_users,
        'all_goals': all_goals,
        'search': search,
        'status_filter': status_filter,
        'level_filter': level_filter,
        'plan_type_filter': plan_type_filter,
        'plan_period_filter': plan_period_filter,
        'responsible_filter': responsible_filter,
        'related_goal_filter': related_goal_filter,
        'total_count': total_count,
        'in_progress_count': in_progress_count,
        'draft_count': draft_count,
        'completed_count': completed_count,
        'status_options': Plan.STATUS_CHOICES,
        'level_choices': Plan.LEVEL_CHOICES,
        'plan_period_choices': Plan.PLAN_PERIOD_CHOICES,
    })
    return render(request, "plan_management/plan_decompose_entry.html", context)


@login_required
def plan_track_entry(request):
    """计划跟踪入口页面 - 显示可跟踪的计划列表"""
    permission_set = get_user_permission_codes(request.user)
    
    # 权限检查
    if not _permission_granted('plan_management.view', permission_set):
        messages.error(request, '您没有权限跟踪计划执行')
        return redirect('plan_pages:plan_list')
    
    # 获取筛选参数
    search = request.GET.get('search', '').strip()
    status_filter = request.GET.get('status', '')
    level_filter = request.GET.get('level', '')
    plan_period_filter = request.GET.get('plan_period', '')
    responsible_filter = request.GET.get('responsible_person', '')
    related_goal_filter = request.GET.get('related_goal', '')
    
    # 查询可跟踪的计划（排除已取消的计划）
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
        # 默认显示执行中的计划
        plans = plans.filter(status='in_progress')
    
    if level_filter:
        plans = plans.filter(level=level_filter)
    
    if plan_period_filter:
        plans = plans.filter(plan_period=plan_period_filter)
    
    if responsible_filter:
        plans = plans.filter(responsible_person_id=responsible_filter)
    
    if related_goal_filter:
        plans = plans.filter(related_goal_id=related_goal_filter)
    
    # 排序：优先显示执行中的计划
    plans = plans.order_by('-status', '-created_time')
    
    # 分页
    page_size = request.GET.get('page_size', '10')
    try:
        per_page = int(page_size)
        if per_page not in [10, 20, 50, 100]:
            per_page = 10
    except (ValueError, TypeError):
        per_page = 10
    
    paginator = Paginator(plans, per_page)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # 统计信息
    base_plans = Plan.objects.exclude(status='cancelled')
    total_count = base_plans.count()
    in_progress_count = base_plans.filter(status='in_progress').count()
    draft_count = base_plans.filter(status='draft').count()
    completed_count = base_plans.filter(status='completed').count()
    
    # 获取所有用户（用于筛选）
    all_users = User.objects.filter(is_active=True).order_by('username')
    
    # 获取所有战略目标（用于筛选）
    all_goals = StrategicGoal.objects.filter(
        status__in=['published', 'in_progress']
    ).order_by('name')
    
    context = _context(
        "计划跟踪",
        "📈",
        "选择要跟踪的计划",
        request=request,
    )
    context['sidebar_nav'] = _build_plan_management_sidebar_nav(permission_set, active_id='plan_track')
    context.update({
        'page_obj': page_obj,
        'plans': list(page_obj),
        'all_users': all_users,
        'all_goals': all_goals,
        'search': search,
        'status_filter': status_filter,
        'level_filter': level_filter,
        'plan_period_filter': plan_period_filter,
        'responsible_filter': responsible_filter,
        'related_goal_filter': related_goal_filter,
        'total_count': total_count,
        'in_progress_count': in_progress_count,
        'draft_count': draft_count,
        'completed_count': completed_count,
        'status_options': Plan.STATUS_CHOICES,
        'level_choices': Plan.LEVEL_CHOICES,
        'plan_period_choices': Plan.PLAN_PERIOD_CHOICES,
    })
    return render(request, "plan_management/plan_track_entry.html", context)


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
    context['sidebar_nav'] = _build_plan_management_sidebar_nav(permission_set, active_id='plan_decompose')
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
    context['sidebar_nav'] = _build_plan_management_sidebar_nav(permission_set, active_id='plan_goal_alignment')
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
    展示所有待审批的审批请求（包括审批引擎和 PlanDecision）
    应用公司数据隔离：只显示与当前用户同一公司的计划的审批请求
    """
    permission_set = get_user_permission_codes(request.user)
    can_approve = _permission_granted('plan_management.approve_plan', permission_set) or request.user.is_superuser
    
    # 获取筛选参数
    search = request.GET.get('search', '').strip()
    request_type_filter = request.GET.get('request_type', '')
    status_filter = request.GET.get('status', '')
    requested_by_filter = request.GET.get('requested_by', '')
    date_from = request.GET.get('date_from', '').strip()
    date_to = request.GET.get('date_to', '').strip()
    
    # 获取审批引擎的审批实例
    from django.contrib.contenttypes.models import ContentType
    from backend.apps.workflow_engine.models import ApprovalInstance
    from backend.apps.plan_management.services.plan_approval import PlanApprovalService
    
    plan_content_type = ContentType.objects.get_for_model(Plan)
    
    pending_approval_instances = ApprovalInstance.objects.filter(
        content_type=plan_content_type,
        status__in=['pending', 'in_progress'],
        workflow__code__in=[
            PlanApprovalService.PLAN_START_WORKFLOW_CODE,
            PlanApprovalService.PLAN_CANCEL_WORKFLOW_CODE
        ]
    ).select_related("workflow", "applicant", "current_node")
    
    # 应用公司数据隔离
    if not request.user.is_superuser:
        company_id = None
        try:
            profile = request.user.profile
            if profile:
                company_id = getattr(profile, 'company_id', None)
                if company_id is None and hasattr(profile, 'department') and profile.department:
                    company_id = getattr(profile.department, 'company_id', None)
        except AttributeError:
            pass
        
        if company_id:
            # 过滤只显示同一公司的计划的审批实例
            plan_ids = Plan.objects.filter(
                Q(company_id=company_id) | Q(company__isnull=True)
            ).values_list('id', flat=True)
            pending_approval_instances = pending_approval_instances.filter(object_id__in=plan_ids)
    
    # PlanDecision（向后兼容）
    pending_decisions = (
        PlanDecision.objects
        .filter(decided_at__isnull=True)
        .select_related("plan", "requested_by", "plan__responsible_person", "plan__created_by", "plan__company")
    )
    
    # 应用公司数据隔离：只显示与当前用户同一公司的计划的审批请求
    # 超级管理员可以看到所有审批请求
    if not request.user.is_superuser:
        # 获取用户的公司ID
        company_id = None
        try:
            profile = request.user.profile
            if profile:
                company_id = getattr(profile, 'company_id', None)
                if company_id is None and hasattr(profile, 'department') and profile.department:
                    company_id = getattr(profile.department, 'company_id', None)
        except AttributeError:
            pass
        
        # 如果有公司ID，过滤只显示同一公司的计划审批请求
        # 注意：如果计划的 company 为 null，也会被包含（使用 Q 对象）
        if company_id:
            pending_decisions = pending_decisions.filter(
                Q(plan__company_id=company_id) | Q(plan__company__isnull=True)
            )
    
    # 应用筛选 - 审批引擎的审批实例
    if search:
        # 通过关联的计划进行搜索
        plan_ids = Plan.objects.filter(
            Q(plan_number__icontains=search) |
            Q(name__icontains=search)
        ).values_list('id', flat=True)
        pending_approval_instances = pending_approval_instances.filter(object_id__in=plan_ids)
        
        # 也可以通过申请人搜索
        applicant_ids = User.objects.filter(
            Q(username__icontains=search) |
            Q(full_name__icontains=search)
        ).values_list('id', flat=True)
        pending_approval_instances = pending_approval_instances.filter(applicant_id__in=applicant_ids)
    
    if request_type_filter:
        if request_type_filter == 'start':
            pending_approval_instances = pending_approval_instances.filter(
                workflow__code=PlanApprovalService.PLAN_START_WORKFLOW_CODE
            )
        elif request_type_filter == 'cancel':
            pending_approval_instances = pending_approval_instances.filter(
                workflow__code=PlanApprovalService.PLAN_CANCEL_WORKFLOW_CODE
            )
    
    if status_filter:
        plan_ids = Plan.objects.filter(status=status_filter).values_list('id', flat=True)
        pending_approval_instances = pending_approval_instances.filter(object_id__in=plan_ids)
    
    if requested_by_filter:
        pending_approval_instances = pending_approval_instances.filter(applicant_id=requested_by_filter)
    
    if date_from:
        pending_approval_instances = pending_approval_instances.filter(apply_time__date__gte=date_from)
    
    if date_to:
        pending_approval_instances = pending_approval_instances.filter(apply_time__date__lte=date_to)
    
    # 应用筛选 - PlanDecision（向后兼容）
    if search:
        pending_decisions = pending_decisions.filter(
            Q(plan__plan_number__icontains=search) |
            Q(plan__name__icontains=search) |
            Q(requested_by__username__icontains=search) |
            Q(requested_by__full_name__icontains=search)
        )
    
    if request_type_filter:
        pending_decisions = pending_decisions.filter(request_type=request_type_filter)
    
    if status_filter:
        pending_decisions = pending_decisions.filter(plan__status=status_filter)
    
    if requested_by_filter:
        pending_decisions = pending_decisions.filter(requested_by_id=requested_by_filter)
    
    if date_from:
        pending_decisions = pending_decisions.filter(requested_at__date__gte=date_from)
    
    if date_to:
        pending_decisions = pending_decisions.filter(requested_at__date__lte=date_to)
    
    # 排序
    pending_approval_instances = pending_approval_instances.order_by("-created_time")
    pending_decisions = pending_decisions.order_by("-requested_at")
    
    # 分页 - 合并两种数据源
    # 注意：由于审批引擎和 PlanDecision 是不同的数据源，这里分别处理
    # 在实际应用中，可以优先显示审批引擎的审批实例
    page_size = request.GET.get('page_size', '10')
    try:
        per_page = int(page_size)
        if per_page not in [10, 20, 50, 100]:
            per_page = 10
    except (ValueError, TypeError):
        per_page = 10
    
    # 分别对两种数据源进行分页
    approval_paginator = Paginator(pending_approval_instances, per_page)
    decision_paginator = Paginator(pending_decisions, per_page)
    page_number = request.GET.get('page', 1)
    
    approval_page_obj = approval_paginator.get_page(page_number)
    decision_page_obj = decision_paginator.get_page(page_number)
    
    # 为了向后兼容，保留 page_obj 指向 PlanDecision 的分页
    page_obj = decision_page_obj
    
    # 统计信息（包括审批引擎和 PlanDecision）
    # 审批引擎统计
    approval_stats_base = pending_approval_instances
    approval_start_count = approval_stats_base.filter(workflow__code=PlanApprovalService.PLAN_START_WORKFLOW_CODE).count()
    approval_cancel_count = approval_stats_base.filter(workflow__code=PlanApprovalService.PLAN_CANCEL_WORKFLOW_CODE).count()
    
    # PlanDecision 统计（向后兼容）
    stats_base = PlanDecision.objects.filter(decided_at__isnull=True)
    if not request.user.is_superuser:
        company_id = None
        try:
            profile = request.user.profile
            if profile:
                company_id = getattr(profile, 'company_id', None)
                if company_id is None and hasattr(profile, 'department') and profile.department:
                    company_id = getattr(profile.department, 'company_id', None)
        except AttributeError:
            pass
        if company_id:
            stats_base = stats_base.filter(
                Q(plan__company_id=company_id) | Q(plan__company__isnull=True)
            )
    
    decision_start_count = stats_base.filter(request_type='start').count()
    decision_cancel_count = stats_base.filter(request_type='cancel').count()
    
    # 合并统计
    total_count = approval_stats_base.count() + stats_base.count()
    pending_count = approval_start_count + decision_start_count
    cancel_count = approval_cancel_count + decision_cancel_count
    
    # 获取所有用户（用于筛选）
    approval_user_ids = pending_approval_instances.values_list('applicant_id', flat=True).distinct()
    decision_user_ids = pending_decisions.values_list('requested_by_id', flat=True).distinct()
    all_user_ids = set(approval_user_ids) | set(decision_user_ids)
    all_users = User.objects.filter(id__in=all_user_ids).order_by('username')
    
    context = _context(
        "计划审批列表",
        "✅",
        "待裁决的计划请求",
        request=request,
    )
    context['sidebar_nav'] = _build_plan_management_sidebar_nav(permission_set, active_id='plan_approval')
    context.update({
        "page_obj": page_obj,  # PlanDecision 分页（向后兼容）
        "approval_page_obj": approval_page_obj,  # 审批引擎分页
        "pending_decisions": list(page_obj),  # 保持向后兼容（PlanDecision）
        "pending_approval_instances": list(approval_page_obj),  # 审批引擎的审批实例（分页后）
        "can_approve": can_approve,
        "total_count": total_count,
        "pending_count": pending_count,
        "cancel_count": cancel_count,
        "all_users": all_users,
        "search": search,
        "request_type_filter": request_type_filter,
        "status_filter": status_filter,
        "requested_by_filter": requested_by_filter,
        "date_from": date_from,
        "date_to": date_to,
        "request_type_choices": PlanDecision.REQUEST_TYPES,
        "status_options": Plan.STATUS_CHOICES,
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
        # P2-3 补强：禁止未接收计划的进度更新
        if plan.level == 'personal' and plan.status == 'published':
            messages.error(request, '计划尚未接收，不能更新进度。请先接收计划。')
            return redirect('plan_pages:plan_execution_track', plan_id=plan_id)
        
        # P2-3: 如果计划是 accepted 状态，首次更新进度时自动进入 in_progress
        if plan.status == 'accepted':
            try:
                plan.transition_to('in_progress', user=request.user)
            except ValueError:
                pass  # 如果转换失败，继续更新进度
        
        progress_form = PlanProgressUpdateForm(request.POST, plan=plan)
        if progress_form.is_valid():
            record = progress_form.save(commit=False)
            record.recorded_by = request.user
            record.save()
            
            # 通知上级进度更新
            from .notifications import notify_supervisor_progress_update
            notify_supervisor_progress_update(plan, request.user)
            
            messages.success(request, '进度更新成功')
            return redirect('plan_pages:plan_execution_track', plan_id=plan_id)
    
    # P2-3: 开始执行（accepted → in_progress）
    if request.method == 'POST' and 'start_execution' in request.POST:
        # P2-3 补强：禁止未接收计划的开始执行
        if plan.level == 'personal' and plan.status == 'published':
            messages.error(request, '计划尚未接收，不能开始执行。请先接收计划。')
            return redirect('plan_pages:plan_execution_track', plan_id=plan_id)
        
        if plan.status == 'accepted':
            try:
                plan.transition_to('in_progress', user=request.user)
                messages.success(request, '计划已开始执行')
                return redirect('plan_pages:plan_execution_track', plan_id=plan_id)
            except ValueError as e:
                messages.error(request, str(e))
        else:
            messages.error(request, '只有已接收状态的计划可以开始执行')
    
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
    # 注意：draft -> in_progress 必须通过审批流程，不能直接转换
    if request.method == 'POST' and 'transition_status' in request.POST:
        new_status = request.POST.get('new_status')
        
        # 禁止从 draft 直接转换到 in_progress（必须通过审批）
        if plan.status == 'draft' and new_status == 'in_progress':
            messages.error(request, '计划必须通过审批流程才能进入执行中状态，请先提交审批请求')
            return redirect('plan_pages:plan_detail', plan_id=plan_id)
        
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
    context['sidebar_nav'] = _build_plan_management_sidebar_nav(permission_set, active_id='plan_execution_track')
    context.update({
        'plan': plan,
        'progress_records': progress_records,
        'issues': issues,
        'status_logs': status_logs,
        'progress_trend': progress_trend,
        'progress_form': progress_form,
        'issue_form': issue_form,
        # P2-3 补强：个人计划必须接收后才能更新进度
        'can_update_progress': (
            plan.status in ['accepted', 'in_progress'] if plan.level == 'personal' 
            else plan.status in ['published', 'accepted', 'in_progress']
        ),
        'can_start_execution': plan.status == 'accepted',  # P2-3
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
    
    error_messages = []  # 初始化错误列表
    if request.method == 'POST':
        form = PlanProgressUpdateForm(request.POST, plan=plan)
        if form.is_valid():
            record = form.save(commit=False)
            record.recorded_by = request.user
            record.save()
            messages.success(request, '进度更新成功')
            return redirect('plan_pages:plan_execution_track', plan_id=plan_id)
        else:
            # 使用 context 传递错误，不写入 messages
            if form.errors:
                error_messages.append(_form_errors_plain(form))
            if not error_messages:
                error_messages.append('表单验证失败，请检查输入')
    else:
        form = PlanProgressUpdateForm(plan=plan)
    
    context = _context(
        f"进度更新 - {plan.name}",
        "📈",
        "更新计划执行进度",
        request=request,
    )
    context['sidebar_nav'] = _build_plan_management_sidebar_nav(permission_set, active_id='plan_progress_update')
    context['form'] = form
    context['plan'] = plan
    if error_messages:
        context['form_validation_errors'] = error_messages
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
    
    # 统计信息（所有状态）
    total_count = issues.count()
    open_count = issues.filter(status='open').count()
    in_progress_count = issues.filter(status='in_progress').count()
    resolved_count = issues.filter(status='resolved').count()
    closed_count = issues.filter(status='closed').count()
    
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
    context['sidebar_nav'] = _build_plan_management_sidebar_nav(permission_set, active_id='plan_issue_list')
    context.update({
        'plan': plan,
        'issues': issues,
        'total_count': total_count,
        'open_count': open_count,
        'in_progress_count': in_progress_count,
        'resolved_count': resolved_count,
        'closed_count': closed_count,
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
    context['sidebar_nav'] = _build_plan_management_sidebar_nav(permission_set, active_id='plan_complete')
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
            
            # P2-2: 确保 level 正确设置
            if not goal.level:
                if goal.parent_goal:
                    goal.level = 'personal'
                    # 个人目标的 owner = responsible_person
                    if goal.responsible_person and not goal.owner:
                        goal.owner = goal.responsible_person
                else:
                    goal.level = 'company'
            
            goal.status = 'draft'
            goal.save()
            
            messages.success(request, f'战略目标 {goal.name} 创建成功')
            return redirect('plan_pages:strategic_goal_detail', goal_id=goal.id)
        else:
            # 使用 context 传递错误，不写入 messages
            error_messages = []
            if form.errors:
                error_messages.append(_form_errors_plain(form))
            if not error_messages:
                error_messages.append('表单验证失败，请检查输入')
            
            # 关键：invalid 时回渲染，不要 redirect
            context = _context("创建战略目标", "➕", "创建新的战略目标", request=request)
            context['sidebar_nav'] = _build_plan_management_sidebar_nav(permission_set, active_id='strategic_goal_create')
            context['form'] = form
            context['page_title'] = "创建战略目标"
            context['submit_text'] = "创建"
            context['cancel_url_name'] = 'plan_pages:strategic_goal_list'
            context['form_js_file'] = 'js/goal_form_date_calculator.js'
            context['form_page_subtitle_text'] = '请填写目标基本信息'
            context['create_url_name'] = 'plan_pages:strategic_goal_create'
            context['business_module'] = 'goal'  # 业务模块名称，用于表单编号生成
            context['form_validation_errors'] = error_messages
            return render(request, "goal_management/goal_form.html", context)
    else:
        form = StrategicGoalForm(user=request.user)
    
    context = _context("创建战略目标", "➕", "创建新的战略目标", request=request)
    context['sidebar_nav'] = _build_plan_management_sidebar_nav(permission_set, active_id='strategic_goal_create')
    context['form'] = form
    context['page_title'] = "创建战略目标"
    context['submit_text'] = "创建"
    context['cancel_url_name'] = 'plan_pages:strategic_goal_list'
    context['form_js_file'] = 'js/goal_form_date_calculator.js'
    context['form_page_subtitle_text'] = '请填写目标基本信息'
    context['business_module'] = 'goal'  # 业务模块名称，用于表单编号生成
    return render(request, "goal_management/goal_form.html", context)


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
    
    # 筛选子目标
    status_filter = request.GET.get('status', '')
    responsible_filter = request.GET.get('responsible', '')
    
    if status_filter:
        child_goals = child_goals.filter(status=status_filter)
    
    if responsible_filter:
        child_goals = child_goals.filter(
            Q(responsible_person__username__icontains=responsible_filter) |
            Q(responsible_person__first_name__icontains=responsible_filter) |
            Q(responsible_person__last_name__icontains=responsible_filter)
        )
    
    child_goals = child_goals.order_by('-created_time')
    
    # 获取关联计划数量
    related_plans_count = Plan.objects.filter(related_goal=goal).count()
    
    # 获取关联计划列表（用于关联信息卡片）
    related_plans = Plan.objects.filter(related_goal=goal).select_related(
        'responsible_person', 'responsible_department'
    ).order_by('-created_time')[:20]
    
    # 获取审计日志（用于审计信息卡片）
    audit_logs = []
    try:
        from backend.apps.system_management.models import AuditLog
        
        # 使用 _meta.label 格式（如 "plan_management.StrategicGoal"）
        object_type = StrategicGoal._meta.label
        audit_logs = AuditLog.objects.filter(
            object_type=object_type,
            object_id=str(goal.id)
        ).select_related('actor').order_by('-created_time')[:50]
    except Exception:
        # AuditLog 不存在或查询失败，使用空列表
        pass
    
    # 获取审批实例（用于审批信息卡片）
    approval_instances = []
    try:
        from django.contrib.contenttypes.models import ContentType
        from backend.apps.workflow_engine.models import ApprovalInstance
        
        content_type = ContentType.objects.get_for_model(StrategicGoal)
        approval_instances = ApprovalInstance.objects.filter(
            content_type=content_type,
            object_id=goal.id
        ).select_related('workflow', 'applicant', 'current_node').prefetch_related(
            'records__node', 'records__approver', 'records__transferred_to'
        ).order_by('-created_time')
        
        # 对每个实例的审批记录进行排序（按节点序号和时间）
        for instance in approval_instances:
            instance.records_sorted = sorted(
                instance.records.all(),
                key=lambda r: (r.node.sequence if r.node else 999, r.approval_time or r.created_time)
            )
    except Exception:
        # ApprovalInstance 不存在或查询失败，使用空列表
        pass
    
    # 获取附件（用于附件与文件信息卡片）
    attachments = []
    try:
        from django.contrib.contenttypes.models import ContentType
        from backend.apps.plan_management.models import Attachment
        
        content_type = ContentType.objects.get_for_model(StrategicGoal)
        attachments = Attachment.objects.filter(
            content_type=content_type,
            object_id=goal.id
        ).select_related('uploaded_by').order_by('-uploaded_at')
    except Exception:
        # Attachment 不存在或查询失败，使用空列表
        pass
    
    # 处理状态转换（发布目标）- P2-2
    if request.method == 'POST' and 'publish_goal' in request.POST:
        if goal.status == 'draft':
            try:
                goal.transition_to('published', user=request.user)
                
                # P2-2: 公司目标发布后，通知员工创建个人目标
                if goal.level == 'company':
                    from .notifications import notify_company_goal_published
                    notify_company_goal_published(goal)
                # P2-2: 个人目标发布后，通知目标所有者接收目标
                elif goal.level == 'personal':
                    from .notifications import notify_personal_goal_published
                    notify_personal_goal_published(goal)
                
                messages.success(request, '目标已发布')
                return redirect('plan_pages:strategic_goal_detail', goal_id=goal_id)
            except ValueError as e:
                messages.error(request, str(e))
        else:
            messages.error(request, '只有制定中状态的目标可以发布')
    
    # P2-2: 接收目标（published → accepted）
    if request.method == 'POST' and 'accept_goal' in request.POST:
        if goal.status == 'published':
            # 检查权限：只有 owner 可以接收个人目标
            if goal.level == 'personal':
                if goal.owner != request.user:
                    messages.error(request, '只有目标所有者可以接收此目标')
                    return redirect('plan_pages:strategic_goal_detail', goal_id=goal_id)
            
            try:
                goal.transition_to('accepted', user=request.user)
                
                # P2-4: 通知目标被接收
                from .notifications import notify_goal_accepted
                notify_goal_accepted(goal, request.user)
                
                messages.success(request, '目标已接收')
                return redirect('plan_pages:strategic_goal_detail', goal_id=goal_id)
            except ValueError as e:
                messages.error(request, str(e))
        else:
            messages.error(request, '只有已发布状态的目标可以接收')
    
    # P2-2: 开始执行（accepted → in_progress）
    if request.method == 'POST' and 'start_execution' in request.POST:
        # P2-2 补强：禁止未接收目标的开始执行
        if goal.level == 'personal' and goal.status == 'published':
            messages.error(request, '目标尚未接收，不能开始执行。请先接收目标。')
            return redirect('plan_pages:strategic_goal_detail', goal_id=goal_id)
        
        if goal.status == 'accepted':
            try:
                goal.transition_to('in_progress', user=request.user)
                messages.success(request, '目标已开始执行')
                return redirect('plan_pages:strategic_goal_detail', goal_id=goal_id)
            except ValueError as e:
                messages.error(request, str(e))
        else:
            messages.error(request, '只有已接收状态的目标可以开始执行')
    
    # P2-2: 检查操作权限
    can_publish = (_permission_granted('plan_management.manage_goal', permission_set) 
                   and goal.status == 'draft')
    
    # P2-2: 检查是否可以接收（只有 owner 可以接收个人目标）
    can_accept = False
    if goal.status == 'published':
        if goal.level == 'personal':
            can_accept = goal.owner == request.user
        else:
            # 公司目标：所有用户都可以接收（后续可优化为按部门/角色）
            can_accept = True
    
    # P2-2: 检查是否可以开始执行
    can_start_execution = goal.status == 'accepted'
    
    context = _context(
        f"战略目标详情 - {goal.name}",
        "🎯",
        goal.name,
        request=request,
    )
    context['sidebar_nav'] = _build_plan_management_sidebar_nav(permission_set, active_id='strategic_goal_list')
    context.update({
        'object': goal,  # 用于 detail_base.html
        'goal': goal,
        'progress_records': progress_records,
        'status_logs': status_logs,
        'adjustments': adjustments,
        'child_goals': child_goals,
        'related_plans_count': related_plans_count,
        'related_plans': related_plans,  # 关联信息
        'audit_logs': audit_logs,  # 审计信息
        'approval_instances': approval_instances,  # 审批信息
        'attachments': attachments,  # 附件信息
        'can_edit': _permission_granted('plan_management.manage_goal', permission_set) and goal.status == 'draft',
        'can_delete': _permission_granted('plan_management.manage_goal', permission_set) and goal.status == 'draft' and not goal.has_related_plans(),
        'can_publish': can_publish,
        'can_accept': can_accept,  # P2-2
        'can_start_execution': can_start_execution,  # P2-2
        'valid_transitions': goal.get_valid_transitions(),
        'progress_percent': goal.completion_rate,  # 用于进度条
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
    
    # 检查是否可以编辑（只有草稿状态可以编辑）
    if goal.status != 'draft':
        messages.error(request, '只有制定中状态的目标可以编辑，已发布的目标需要通过调整申请流程进行修改')
        return redirect('plan_pages:strategic_goal_detail', goal_id=goal_id)
    
    if request.method == 'POST':
        form = StrategicGoalForm(request.POST, instance=goal, user=request.user)
        if form.is_valid():
            goal = form.save()
            messages.success(request, f'战略目标 {goal.name} 更新成功')
            return redirect('plan_pages:strategic_goal_detail', goal_id=goal.id)
        else:
            # 使用 context 传递错误，不写入 messages
            error_messages = []
            if form.errors:
                error_messages.append(_form_errors_plain(form))
            if not error_messages:
                error_messages.append('表单验证失败，请检查输入')
            
            # 关键：invalid 时回渲染，不要 redirect
            context = _context(
                f"编辑战略目标 - {goal.name}",
                "✏️",
                "编辑战略目标信息",
                request=request,
            )
            context['sidebar_nav'] = _build_plan_management_sidebar_nav(permission_set, active_id='strategic_goal_create')
            context['form'] = form
            context['goal'] = goal
            context['page_title'] = "编辑战略目标"
            context['submit_text'] = "保存"
            context['create_url_name'] = 'plan_pages:strategic_goal_create'
            context['form_validation_errors'] = error_messages
            return render(request, "goal_management/goal_form.html", context)
    else:
        form = StrategicGoalForm(instance=goal, user=request.user)
    
    context = _context(
        f"编辑战略目标 - {goal.name}",
        "✏️",
        "编辑战略目标信息",
        request=request,
    )
    context['sidebar_nav'] = _build_plan_management_sidebar_nav(permission_set, active_id='strategic_goal_list')
    context['form'] = form
    context['goal'] = goal
    context['page_title'] = "编辑战略目标"
    context['submit_text'] = "保存"
    return render(request, "goal_management/goal_form.html", context)


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
    context['sidebar_nav'] = _build_plan_management_sidebar_nav(permission_set, active_id='strategic_goal_decompose')
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
    
    # 获取筛选参数
    search = request.GET.get('search', '').strip()
    status_filter = request.GET.get('status', '')
    level_filter = request.GET.get('level', '')
    goal_type_filter = request.GET.get('goal_type', '')
    goal_period_filter = request.GET.get('goal_period', '')
    responsible_filter = request.GET.get('responsible', '')
    
    # 获取所有目标（包括制定中的，但标记哪些可以跟踪）
    all_goals = StrategicGoal.objects.select_related(
        'responsible_person', 'responsible_department', 'parent_goal'
    ).order_by('-created_time')
    
    # 如果没有目标，跳转到列表页
    if not all_goals.exists():
        messages.info(request, '暂无战略目标，请先创建目标')
        return redirect('plan_pages:strategic_goal_list')
    
    # 应用筛选
    if search:
        all_goals = all_goals.filter(
            Q(goal_number__icontains=search) |
            Q(name__icontains=search) |
            Q(responsible_person__username__icontains=search) |
            Q(responsible_person__full_name__icontains=search)
        )
    
    if status_filter:
        all_goals = all_goals.filter(status=status_filter)
    
    if level_filter:
        all_goals = all_goals.filter(level=level_filter)
    
    if goal_type_filter:
        all_goals = all_goals.filter(goal_type=goal_type_filter)
    
    if goal_period_filter:
        all_goals = all_goals.filter(goal_period=goal_period_filter)
    
    if responsible_filter:
        all_goals = all_goals.filter(responsible_person_id=responsible_filter)
    
    # P2-2: 筛选可跟踪的目标（已发布、已接收或执行中的目标）
    trackable_goals = all_goals.filter(status__in=['published', 'accepted', 'in_progress'])
    
    # 统计信息（所有状态，基于原始查询）
    total_count = StrategicGoal.objects.count()
    draft_count = StrategicGoal.objects.filter(status='draft').count()
    published_count = StrategicGoal.objects.filter(status='published').count()
    in_progress_count = StrategicGoal.objects.filter(status='in_progress').count()
    completed_count = StrategicGoal.objects.filter(status='completed').count()
    cancelled_count = StrategicGoal.objects.filter(status='cancelled').count()
    
    # 如果只有一个可跟踪的目标，直接跳转到该目标的跟踪页面
    if trackable_goals.count() == 1:
        return redirect('plan_pages:strategic_goal_track', goal_id=trackable_goals.first().id)
    
    # 分页
    page_size = request.GET.get('page_size', '10')
    try:
        per_page = int(page_size)
        if per_page not in [10, 20, 50, 100]:
            per_page = 10
    except (ValueError, TypeError):
        per_page = 10
    
    paginator = Paginator(all_goals, per_page)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # 获取所有用户（用于筛选）
    all_users = User.objects.filter(is_active=True).order_by('username')
    
    # 显示选择页面（显示所有目标，但标记哪些可以跟踪）
    context = _context(
        "目标跟踪",
        "📈",
        "选择要跟踪的战略目标",
        request=request,
    )
    context['sidebar_nav'] = _build_plan_management_sidebar_nav(permission_set, active_id='strategic_goal_track')
    context.update({
        'page_obj': page_obj,
        'goals': list(page_obj),  # 保持向后兼容
        'trackable_goals': trackable_goals,
        'has_trackable_goals': trackable_goals.exists(),
        'total_count': total_count,
        'draft_count': draft_count,
        'published_count': published_count,
        'in_progress_count': in_progress_count,
        'completed_count': completed_count,
        'cancelled_count': cancelled_count,
        'all_users': all_users,
        'search': search,
        'status_filter': status_filter,
        'level_filter': level_filter,
        'goal_type_filter': goal_type_filter,
        'goal_period_filter': goal_period_filter,
        'responsible_filter': responsible_filter,
        'status_options': StrategicGoal.STATUS_CHOICES,
        'level_choices': StrategicGoal.LEVEL_CHOICES,
        'goal_type_choices': StrategicGoal.GOAL_TYPE_CHOICES,
        'goal_period_choices': StrategicGoal.GOAL_PERIOD_CHOICES,
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
    
    # 获取筛选参数
    recorded_by_filter = request.GET.get('recorded_by', '')
    date_from = request.GET.get('date_from', '').strip()
    date_to = request.GET.get('date_to', '').strip()
    
    # 获取所有进度记录
    progress_records = GoalProgressRecord.objects.filter(
        goal=goal
    ).select_related('recorded_by').order_by('-recorded_time')
    
    # 应用筛选
    if recorded_by_filter:
        progress_records = progress_records.filter(recorded_by_id=recorded_by_filter)
    
    if date_from:
        progress_records = progress_records.filter(recorded_time__date__gte=date_from)
    
    if date_to:
        progress_records = progress_records.filter(recorded_time__date__lte=date_to)
    
    # 分页
    from django.core.paginator import Paginator
    page_size = request.GET.get('page_size', '10')
    try:
        per_page = int(page_size)
        if per_page not in [10, 20, 50, 100]:
            per_page = 10
    except (ValueError, TypeError):
        per_page = 10
    
    paginator = Paginator(progress_records, per_page)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # 获取所有用户（用于筛选）
    all_users = User.objects.filter(
        id__in=progress_records.values_list('recorded_by_id', flat=True).distinct()
    ).order_by('username')
    
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
        # P2-2 补强：禁止未接收目标的进度更新
        if goal.level == 'personal' and goal.status == 'published':
            messages.error(request, '目标尚未接收，不能更新进度。请先接收目标。')
            return redirect('plan_pages:strategic_goal_track', goal_id=goal_id)
        
        # P2-2: 如果目标是 accepted 状态，首次更新进度时自动进入 in_progress
        if goal.status == 'accepted':
            try:
                goal.transition_to('in_progress', user=request.user)
            except ValueError:
                pass  # 如果转换失败，继续更新进度
        
        progress_form = GoalProgressUpdateForm(request.POST, goal=goal)
        if progress_form.is_valid():
            record = progress_form.save(commit=False)
            record.recorded_by = request.user
            record.completion_rate = goal.calculate_completion_rate()
            record.save()
            
            # 通知上级进度更新
            from .notifications import notify_supervisor_progress_update
            notify_supervisor_progress_update(goal, request.user)
            
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
    
    # P2-2: 开始执行（accepted → in_progress）
    if request.method == 'POST' and 'start_execution' in request.POST:
        # P2-2 补强：禁止未接收目标的开始执行
        if goal.level == 'personal' and goal.status == 'published':
            messages.error(request, '目标尚未接收，不能开始执行。请先接收目标。')
            return redirect('plan_pages:strategic_goal_track', goal_id=goal_id)
        
        if goal.status == 'accepted':
            try:
                goal.transition_to('in_progress', user=request.user)
                messages.success(request, '目标已开始执行')
                return redirect('plan_pages:strategic_goal_track', goal_id=goal_id)
            except ValueError as e:
                messages.error(request, str(e))
        else:
            messages.error(request, '只有已接收状态的目标可以开始执行')
    
    # 处理目标完成确认
    if request.method == 'POST' and 'complete_goal' in request.POST:
        # P2-2 补强：禁止未接收目标的完成操作
        if goal.level == 'personal' and goal.status == 'published':
            messages.error(request, '目标尚未接收，不能完成。请先接收目标。')
            return redirect('plan_pages:strategic_goal_track', goal_id=goal_id)
        
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
    context['sidebar_nav'] = _build_plan_management_sidebar_nav(permission_set, active_id='strategic_goal_track')
    context.update({
        'goal': goal,
        'page_obj': page_obj,
        'progress_records': list(page_obj),  # 保持向后兼容
        'status_logs': status_logs,
        'adjustments': adjustments,
        'progress_trend': progress_trend,
        'progress_form': progress_form,
        'adjustment_form': adjustment_form,
        'all_users': all_users,
        'recorded_by_filter': recorded_by_filter,
        'date_from': date_from,
        'date_to': date_to,
    })
    
    # P2-2 补强：个人目标必须接收后才能更新进度
    can_update_progress = False
    if goal.level == 'personal':
        can_update_progress = goal.status in ['accepted', 'in_progress']
    else:
        can_update_progress = goal.status in ['published', 'accepted', 'in_progress']
    
    context.update({
        'can_update_progress': can_update_progress,  # P2-2 补强
        'can_start_execution': goal.status == 'accepted',  # P2-2
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
    context['sidebar_nav'] = _build_plan_management_sidebar_nav(permission_set, active_id='strategic_goal_list')
    context['goal'] = goal
    context['can_delete'] = can_delete
    context['delete_warnings'] = delete_warnings
    return render(request, "plan_management/strategic_goal_delete.html", context)


@login_required
def plan_delete(request, plan_id):
    """删除计划"""
    permission_set = get_user_permission_codes(request.user)
    
    # 权限检查
    if not _permission_granted('plan_management.plan.manage', permission_set):
        messages.error(request, '您没有权限删除计划')
        return redirect('plan_pages:plan_list')
    
    plan = get_object_or_404(Plan, id=plan_id)
    
    if request.method == 'POST':
        # POST请求时进行删除前的所有检查
        # 检查是否可以删除
        if plan.status != 'draft':
            messages.error(request, '只有草稿状态的计划可以删除')
            return redirect('plan_pages:plan_detail', plan_id=plan_id)
        
        # 检查是否有下级计划
        if plan.get_child_plans_count() > 0:
            messages.error(request, '该计划有下级计划，无法删除')
            return redirect('plan_pages:plan_detail', plan_id=plan_id)
        
        # 检查是否有待审批的决策请求（decision为null表示待处理）
        from backend.apps.plan_management.models import PlanDecision
        pending_decisions = plan.decisions.filter(decision__isnull=True)
        if pending_decisions.exists():
            messages.error(request, '该计划有待审批的请求，无法删除')
            return redirect('plan_pages:plan_detail', plan_id=plan_id)
        
        # 检查是否有待审批的审批实例（审批引擎）
        from django.contrib.contenttypes.models import ContentType
        from backend.apps.workflow_engine.models import ApprovalInstance
        from backend.apps.plan_management.services.plan_approval import PlanApprovalService
        
        plan_content_type = ContentType.objects.get_for_model(Plan)
        pending_approval_instances = ApprovalInstance.objects.filter(
            content_type=plan_content_type,
            object_id=plan.id,
            status__in=['pending', 'in_progress']
        )
        if pending_approval_instances.exists():
            messages.error(request, '该计划有正在进行的审批流程，无法删除')
            return redirect('plan_pages:plan_detail', plan_id=plan_id)
        
        # 执行删除
        plan_name = plan.name
        plan.delete()
        messages.success(request, f'计划 {plan_name} 已删除')
        return redirect('plan_pages:plan_list')
    
    # GET请求时显示确认页面，但检查是否可以删除（用于显示警告信息）
    can_delete = True
    delete_warnings = []
    
    if plan.status != 'draft':
        can_delete = False
        delete_warnings.append('只有草稿状态的计划可以删除')
    
    if plan.get_child_plans_count() > 0:
        can_delete = False
        delete_warnings.append('该计划有下级计划，无法删除')
    
    # 检查是否有待审批的决策请求（decision为null表示待处理）
    from backend.apps.plan_management.models import PlanDecision
    pending_decisions = plan.decisions.filter(decision__isnull=True)
    if pending_decisions.exists():
        can_delete = False
        delete_warnings.append('该计划有待审批的请求，无法删除')
    
    # 检查是否有待审批的审批实例（审批引擎）
    from django.contrib.contenttypes.models import ContentType
    from backend.apps.workflow_engine.models import ApprovalInstance
    plan_content_type = ContentType.objects.get_for_model(Plan)
    pending_approval_instances = ApprovalInstance.objects.filter(
        content_type=plan_content_type,
        object_id=plan.id,
        status__in=['pending', 'in_progress']
    )
    if pending_approval_instances.exists():
        can_delete = False
        delete_warnings.append('该计划有正在进行的审批流程，无法删除')
    
    context = _context(
        f"删除计划 - {plan.name}",
        "🗑️",
        "确认删除计划",
        request=request,
    )
    context['sidebar_nav'] = _build_plan_management_sidebar_nav(permission_set, active_id='plan_list')
    context['plan'] = plan
    context['can_delete'] = can_delete
    context['delete_warnings'] = delete_warnings
    return render(request, "plan_management/plan_delete.html", context)


@login_required
@require_http_methods(["POST"])
def plan_batch_delete(request):
    """批量删除计划"""
    from backend.apps.plan_management.models import Plan, PlanDecision
    from django.contrib.contenttypes.models import ContentType
    from backend.apps.workflow_engine.models import ApprovalInstance
    
    permission_set = get_user_permission_codes(request.user)
    
    # 权限检查
    if not _permission_granted('plan_management.plan.manage', permission_set):
        return JsonResponse({'success': False, 'message': '您没有权限删除计划'}, status=403)
    
    try:
        # 获取参数
        ids_str = request.POST.get('ids', '')
        
        if not ids_str:
            return JsonResponse({'success': False, 'message': '请选择要删除的计划'}, status=400)
        
        # 解析计划ID列表
        plan_ids = [int(id.strip()) for id in ids_str.split(',') if id.strip()]
        
        if not plan_ids:
            return JsonResponse({'success': False, 'message': '无效的计划ID列表'}, status=400)
        
        # 批量删除（检查删除条件）
        plans = Plan.objects.filter(id__in=plan_ids)
        deleted_count = 0
        failed_plans = []
        plan_content_type = ContentType.objects.get_for_model(Plan)
        
        for plan in plans:
            # 检查是否可以删除
            can_delete = True
            delete_reason = []
            
            # 检查状态
            if plan.status != 'draft':
                can_delete = False
                delete_reason.append('只有草稿状态的计划可以删除')
            
            # 检查是否有下级计划
            if plan.get_child_plans_count() > 0:
                can_delete = False
                delete_reason.append('该计划有下级计划，无法删除')
            
            # 检查是否有待审批的决策请求
            pending_decisions = plan.decisions.filter(decision__isnull=True)
            if pending_decisions.exists():
                can_delete = False
                delete_reason.append('该计划有待审批的请求，无法删除')
            
            # 检查是否有待审批的审批实例
            pending_approval_instances = ApprovalInstance.objects.filter(
                content_type=plan_content_type,
                object_id=plan.id,
                status__in=['pending', 'in_progress']
            )
            if pending_approval_instances.exists():
                can_delete = False
                delete_reason.append('该计划有正在进行的审批流程，无法删除')
            
            if not can_delete:
                failed_plans.append({
                    'name': plan.name,
                    'reason': '; '.join(delete_reason)
                })
                continue
            
            try:
                plan_name = plan.name
                plan.delete()
                deleted_count += 1
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.exception('删除计划失败: %s', str(e))
                failed_plans.append({
                    'name': plan.name,
                    'reason': f'删除失败：{str(e)}'
                })
        
        message = f'成功删除 {deleted_count} 个计划'
        if failed_plans:
            message += f'，{len(failed_plans)} 个计划删除失败'
        
        return JsonResponse({
            'success': True,
            'message': message,
            'deleted_count': deleted_count,
            'failed_count': len(failed_plans),
            'failed_plans': failed_plans
        })
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception('批量删除计划失败: %s', str(e))
        return JsonResponse({'success': False, 'message': f'批量删除失败：{str(e)}'}, status=500)


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
        # P2-2: 创建个人目标，设置 level=personal, owner=responsible_person
        child_goal = StrategicGoal.objects.create(
            name=name,
            level='personal',  # P2-2: 个人目标
            goal_type=parent_goal.goal_type,
            goal_period=parent_goal.goal_period,
            status='draft',
            indicator_name=parent_goal.indicator_name,
            indicator_type=parent_goal.indicator_type,
            indicator_unit=parent_goal.indicator_unit,
            target_value=target_value,
            current_value=Decimal('0'),
            owner_id=responsible_id,  # P2-2: owner = responsible_person
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
    
    # 公司隔离
    from backend.apps.plan_management.utils import apply_company_scope
    plans = apply_company_scope(plans, request.user)
    
    # 权限过滤
    plans = _filter_plans_by_permission(plans, request.user, permission_set)
    
    # 时间筛选
    if date_from:
        plans = plans.filter(start_time__gte=date_from)
    if date_to:
        plans = plans.filter(end_time__lte=date_to)
    
    # 类型筛选（plan_type 字段已在 P2-1 迁移中被 level 字段替代）
    if plan_type:
        # plan_type 的旧值映射到 level 的新值
        plan_type_to_level_map = {
            'personal': 'personal',
            'department': 'company',  # 部门计划映射为公司计划
            'company': 'company',
            'project': 'company',  # 项目计划映射为公司计划
        }
        mapped_level = plan_type_to_level_map.get(plan_type)
        if mapped_level:
            plans = plans.filter(level=mapped_level)
    
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
    
    # 按类型统计（使用 level 字段替代 plan_type）
    type_stats = plans.values('level').annotate(count=Count('id')).order_by('level')
    
    # 按周期统计
    period_stats = plans.values('plan_period').annotate(count=Count('id')).order_by('plan_period')
    
    # 平均进度（使用 Avg 而不是 Sum，更准确）
    avg_progress_result = plans.aggregate(avg=Avg('progress'))['avg']
    if avg_progress_result is not None:
        avg_progress = float(avg_progress_result)
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
    context['sidebar_nav'] = _build_plan_management_sidebar_nav(permission_set, active_id='plan_completion_analysis')
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
    context['sidebar_nav'] = _build_plan_management_sidebar_nav(permission_set, active_id='plan_goal_achievement')
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
    # 注意：plan_type 字段已在 P2-1 迁移中被 level 字段替代
    plan_by_type = plans.values('level').annotate(count=Count('id'))
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
    context['sidebar_nav'] = _build_plan_management_sidebar_nav(permission_set, active_id='plan_statistics')
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

@require_http_methods(["POST"])
@login_required
def plan_submit_approval(request, plan_id):
    """提交计划启动审批（使用通用审批服务）"""
    import logging
    logger = logging.getLogger(__name__)
    permission_set = get_user_permission_codes(request.user)
    plan = get_object_or_404(Plan, id=plan_id)
    
    # 权限检查：plan_management.plan.create 或负责人
    can_submit = _permission_granted('plan_management.plan.create', permission_set) or plan.responsible_person == request.user
    if not can_submit:
        messages.error(request, '您没有权限提交审批')
        return redirect('plan_pages:plan_detail', plan_id=plan_id)
    
    # 检查状态：允许草稿和已取消状态的计划提交审批
    if plan.status not in ['draft', 'cancelled']:
        messages.error(request, f'只有草稿或已取消状态的计划可以提交审批，当前状态：{plan.get_status_display()}')
        return redirect('plan_pages:plan_detail', plan_id=plan_id)
    
    # 检查是否已存在待审批的实例
    from django.contrib.contenttypes.models import ContentType
    from backend.apps.workflow_engine.models import ApprovalInstance
    from backend.apps.plan_management.services.plan_approval_v2 import PlanStartApprovalService
    
    plan_content_type = ContentType.objects.get_for_model(Plan)
    existing_pending_approval = ApprovalInstance.objects.filter(
        content_type=plan_content_type,
        object_id=plan.id,
        workflow__code='plan_start_approval',
        status__in=['pending', 'in_progress']
    ).exists()
    
    if existing_pending_approval:
        messages.warning(request, '该计划已有待处理的启动请求')
        return redirect('plan_pages:plan_detail', plan_id=plan_id)
    
    # 字段验证：检查必填字段是否完整
    is_valid, validation_errors = _validate_plan_fields(plan)
    if not is_valid:
        error_messages = [error['message'] for error in validation_errors]
        messages.error(request, f'提交审批失败：请先完善计划信息。\n' + '\n'.join([f'• {msg}' for msg in error_messages]))
        return redirect('plan_pages:plan_detail', plan_id=plan_id)
    
    # 如果计划是已取消状态，先将其改为草稿状态，并记录状态变更日志
    if plan.status == 'cancelled':
        from django.db import transaction
        old_status = plan.status
        
        try:
            with transaction.atomic():
                plan.status = 'draft'
                plan.save(update_fields=['status'])
                
                # 记录状态变更日志
                PlanStatusLog.objects.create(
                    plan=plan,
                    old_status=old_status,
                    new_status='draft',
                    changed_by=request.user,
                    change_reason='已取消的计划重新提交审批，状态恢复为草稿'
                )
        except Exception as e:
            logger.error(f'记录状态变更日志失败: {e}', exc_info=True)
            messages.error(request, f'状态变更记录失败: {str(e)}')
            return redirect('plan_pages:plan_detail', plan_id=plan_id)
    
    # 使用通用审批服务提交审批
    try:
        # 先检查审批流程模板是否存在
        from backend.apps.workflow_engine.models import WorkflowTemplate
        workflow_template = WorkflowTemplate.objects.filter(
            code='plan_start_approval',
            status='active'
        ).first()
        
        if not workflow_template:
            messages.error(request, '审批流程模板未配置，请联系管理员配置"计划启动审批"流程模板')
            logger.error(f'审批流程模板不存在: plan_start_approval, plan_id={plan_id}')
            return redirect('plan_pages:plan_detail', plan_id=plan_id)
        
        # 检查计划数据完整性（调试用）
        logger.info(f'提交审批前检查计划数据: plan_id={plan_id}, name={plan.name}, content={bool(plan.content)}, start_time={plan.start_time}, end_time={plan.end_time}, status={plan.status}, responsible_person={plan.responsible_person}')
        
        service = PlanStartApprovalService()
        comment = request.POST.get('comment', '')
        
        instance = service.submit_approval(
            obj=plan,
            applicant=request.user,
            comment=comment or f'申请启动计划：{plan.plan_number} - {plan.name}'
        )
        
        if instance:
            # 审批结果走通知中心，不写入 messages，避免出现在登录页等
            logger.info(f'提交审批成功: instance_number={instance.instance_number}, plan_id={plan_id}')
        else:
            messages.error(request, '提交审批失败：审批流程未正确配置，请联系管理员')
            logger.error(f'提交审批失败: 返回None, plan_id={plan_id}, workflow_code=plan_start_approval')
            
    except ValueError as e:
        # 业务规则错误（验证失败）
        error_msg = str(e)
        messages.error(request, f'提交审批失败：{error_msg}')
        logger.warning(f'提交审批请求失败（业务规则验证）: {error_msg}, plan_id={plan_id}, user={request.user.username}, plan_status={plan.status}, plan_name={plan.name}')
    except Exception as e:
        # 其他异常（如数据库错误、审批引擎错误等）
        error_msg = str(e)
        messages.error(request, f'提交审批请求失败：{error_msg}')
        logger.error(f'提交审批请求失败（系统错误）: {error_msg}, plan_id={plan_id}, user={request.user.username}', exc_info=True)
    
    return redirect('plan_pages:plan_detail', plan_id=plan_id)


@login_required
def plan_request_cancel(request, plan_id):
    """发起取消计划请求"""
    permission_set = get_user_permission_codes(request.user)
    plan = get_object_or_404(Plan, id=plan_id)
    
    # 权限检查：plan_management.plan.create 或负责人
    can_request = _permission_granted('plan_management.plan.create', permission_set) or plan.responsible_person == request.user
    if not can_request:
        messages.error(request, '您没有权限发起取消请求')
        return redirect('plan_pages:plan_detail', plan_id=plan_id)
    
    # 检查状态
    if plan.status != 'in_progress':
        messages.error(request, f'只有执行中状态的计划可以申请取消，当前状态：{plan.get_status_display()}')
        return redirect('plan_pages:plan_detail', plan_id=plan_id)
    
    # 检查是否已存在 pending 的 cancel 请求（同时检查审批引擎和 PlanDecision）
    from django.contrib.contenttypes.models import ContentType
    from backend.apps.workflow_engine.models import ApprovalInstance
    from backend.apps.plan_management.services.plan_approval import PlanApprovalService
    
    plan_content_type = ContentType.objects.get_for_model(Plan)
    existing_pending_approval = ApprovalInstance.objects.filter(
        content_type=plan_content_type,
        object_id=plan.id,
        workflow__code=PlanApprovalService.PLAN_CANCEL_WORKFLOW_CODE,
        status__in=['pending', 'in_progress']
    ).exists()
    
    existing_pending_decision = PlanDecision.objects.filter(
        plan=plan,
        request_type='cancel',
        decided_at__isnull=True
    ).exists()
    
    if existing_pending_approval or existing_pending_decision:
        messages.warning(request, '该计划已有待处理的取消请求')
        return redirect('plan_pages:plan_detail', plan_id=plan_id)
    
    # 优先使用审批引擎
    try:
        from backend.apps.plan_management.services.plan_decisions import request_cancel
        decision = request_cancel(plan, request.user, request.POST.get('reason', ''))
        # 审批/取消结果走通知中心，不写入 messages
    except Exception as e:
        messages.error(request, f'发起取消审批请求失败: {str(e)}')
    
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
    
    # 使用服务层的 decide 函数统一处理
    from backend.apps.plan_management.services.plan_decisions import decide, PlanDecisionError
    from django.core.exceptions import PermissionDenied
    
    try:
        # decide() 函数内部已经创建了状态变更日志，这里不需要重复创建
        decision_obj = decide(decision_id, request.user, approve=True, reason=request.POST.get('reason'))
        # 审批结果走通知中心，不写入 messages
    except PermissionDenied as e:
        messages.error(request, str(e))
        return redirect('plan_pages:plan_detail', plan_id=plan.id)
    except PlanDecisionError as e:
        messages.error(request, str(e))
        return redirect('plan_pages:plan_detail', plan_id=plan.id)
    
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
    
    # 使用服务层的 decide 函数统一处理
    from backend.apps.plan_management.services.plan_decisions import decide, PlanDecisionError
    from django.core.exceptions import PermissionDenied
    
    try:
        decision_obj = decide(decision_id, request.user, approve=False, reason=request.POST.get('reason', ''))
        
        # 通过裁决器处理（reject 不改状态，只记录）
        if decision_obj.request_type == 'start':
            result = adjudicate_plan_status(plan, decision='reject', system_facts=None)
        elif decision_obj.request_type == 'cancel':
            result = adjudicate_plan_status(plan, decision='reject_cancel', system_facts=None)
        else:
            messages.error(request, '未知的请求类型')
            return redirect('plan_pages:plan_detail', plan_id=plan.id)
        
        # reject 不改状态，只记录日志；审批结果走通知中心，不写入 messages
    except PermissionDenied as e:
        messages.error(request, str(e))
        return redirect('plan_pages:plan_detail', plan_id=plan.id)
    except PlanDecisionError as e:
        messages.error(request, str(e))
        return redirect('plan_pages:plan_detail', plan_id=plan.id)
    
    return redirect('plan_pages:plan_detail', plan_id=plan.id)


# ==================== 计划调整申请相关视图 ====================

@login_required
def plan_adjustment_create(request, plan_id):
    """创建计划调整申请"""
    permission_set = get_user_permission_codes(request.user)
    plan = get_object_or_404(Plan, id=plan_id)
    
    # 权限检查：计划管理员或计划负责人
    can_manage = _permission_granted('plan_management.plan.manage', permission_set) or request.user.is_superuser
    is_responsible = plan.responsible_person == request.user
    
    if not (can_manage or is_responsible):
        messages.error(request, '您没有权限申请调整该计划')
        return redirect('plan_pages:plan_detail', plan_id=plan_id)
    
    # 检查计划状态：只有执行中的计划可以申请调整
    if plan.status != 'in_progress':
        messages.error(request, '只有执行中的计划可以申请调整')
        return redirect('plan_pages:plan_detail', plan_id=plan_id)
    
    # 检查是否已有待审批的调整申请
    pending_adjustment = PlanAdjustment.objects.filter(
        plan=plan,
        status='pending'
    ).exists()
    
    if pending_adjustment:
        messages.error(request, '该计划已有待审批的调整申请，请等待审批完成后再提交新的申请')
        return redirect('plan_pages:plan_detail', plan_id=plan_id)
    
    if request.method == 'POST':
        form = PlanAdjustmentForm(request.POST, plan=plan)
        if form.is_valid():
            adjustment = form.save(commit=False)
            adjustment.plan = plan
            adjustment.created_by = request.user
            adjustment.original_end_time = plan.end_time
            adjustment.save()
            # 审批相关结果走通知中心，不写入 messages
            return redirect('plan_pages:plan_detail', plan_id=plan_id)
        else:
            # 使用 context 传递错误，不写入 messages
            error_messages = []
            if form.errors:
                error_messages.append(_form_errors_plain(form))
            if not error_messages:
                error_messages.append('表单验证失败，请检查输入')
    else:
        form = PlanAdjustmentForm(plan=plan)
        error_messages = []
    
    context = _context(
        f"申请调整 - {plan.name}",
        "📝",
        "申请调整计划截止时间",
        request=request,
    )
    context['sidebar_nav'] = _build_plan_management_sidebar_nav(permission_set, active_id='plan_list')
    if error_messages:
        context['form_validation_errors'] = error_messages
    context['form'] = form
    context['plan'] = plan
    context['page_title'] = f"申请调整 - {plan.name}"
    context['submit_text'] = "提交申请"
    
    return render(request, "plan_management/plan_adjustment_form.html", context)


@login_required
def plan_adjustment_list(request):
    """计划调整申请列表"""
    permission_set = get_user_permission_codes(request.user)
    
    # 权限检查：至少需要查看权限
    if not _permission_granted('plan_management.view', permission_set):
        messages.error(request, '您没有权限查看调整申请列表')
        return redirect('plan_pages:plan_management_home')
    
    # 获取所有调整申请
    adjustments = PlanAdjustment.objects.select_related(
        'plan', 'created_by', 'approved_by'
    ).order_by('-created_time')
    
    # 权限过滤：普通用户只能看到自己申请的调整
    can_approve = _permission_granted('plan_management.approve_plan', permission_set) or request.user.is_superuser
    if not can_approve:
        adjustments = adjustments.filter(created_by=request.user)
    
    # 状态筛选
    status_filter = request.GET.get('status', '')
    if status_filter:
        adjustments = adjustments.filter(status=status_filter)
    
    # 分页
    paginator = Paginator(adjustments, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # 统计信息
    total_count = adjustments.count()
    pending_count = PlanAdjustment.objects.filter(status='pending').count()
    approved_count = PlanAdjustment.objects.filter(status='approved').count()
    rejected_count = PlanAdjustment.objects.filter(status='rejected').count()
    
    context = _context(
        "计划调整申请",
        "📝",
        "查看和管理计划调整申请",
        request=request,
    )
    context['sidebar_nav'] = _build_plan_management_sidebar_nav(permission_set, active_id='plan_list')
    context['page_obj'] = page_obj
    context['status_filter'] = status_filter
    context['can_approve'] = can_approve
    context['total_count'] = total_count
    context['pending_count'] = pending_count
    context['approved_count'] = approved_count
    context['rejected_count'] = rejected_count
    
    return render(request, "plan_management/plan_adjustment_list.html", context)


@login_required
def plan_adjustment_approve(request, adjustment_id):
    """审批通过调整申请"""
    permission_set = get_user_permission_codes(request.user)
    adjustment = get_object_or_404(PlanAdjustment, id=adjustment_id)
    plan = adjustment.plan
    
    # 权限检查：需要审批权限
    can_approve = _permission_granted('plan_management.approve_plan', permission_set) or request.user.is_superuser
    if not can_approve:
        messages.error(request, '您没有权限审批调整申请')
        return redirect('plan_pages:plan_adjustment_list')
    
    # 检查申请状态
    if adjustment.status != 'pending':
        messages.error(request, '该调整申请已处理，不能重复审批')
        return redirect('plan_pages:plan_adjustment_list')
    
    if request.method == 'POST':
        approval_notes = request.POST.get('approval_notes', '')
        
        # 更新调整申请状态
        adjustment.status = 'approved'
        adjustment.approved_by = request.user
        adjustment.approved_time = timezone.now()
        adjustment.approval_notes = approval_notes
        adjustment.save()
        
        # 更新计划的截止时间
        if adjustment.new_end_time:
            old_end_time = plan.end_time
            plan.end_time = adjustment.new_end_time
            plan.save(update_fields=['end_time'])
            
            # 记录状态日志
            PlanStatusLog.objects.create(
                plan=plan,
                old_status=plan.status,
                new_status=plan.status,
                changed_by=request.user,
                change_reason=f'调整申请已批准：截止时间从 {old_end_time.strftime("%Y-%m-%d %H:%M")} 调整为 {adjustment.new_end_time.strftime("%Y-%m-%d %H:%M")}'
            )
        # 审批结果走通知中心，不写入 messages
        return redirect('plan_pages:plan_adjustment_list')
    
    context = _context(
        f"审批调整申请 - {plan.name}",
        "✅",
        "审批计划调整申请",
        request=request,
    )
    context['sidebar_nav'] = _build_plan_management_sidebar_nav(permission_set, active_id='plan_list')
    context['adjustment'] = adjustment
    context['plan'] = plan
    
    return render(request, "plan_management/plan_adjustment_approve.html", context)


@login_required
def plan_adjustment_reject(request, adjustment_id):
    """审批拒绝调整申请"""
    permission_set = get_user_permission_codes(request.user)
    adjustment = get_object_or_404(PlanAdjustment, id=adjustment_id)
    plan = adjustment.plan
    
    # 权限检查：需要审批权限
    can_approve = _permission_granted('plan_management.approve_plan', permission_set) or request.user.is_superuser
    if not can_approve:
        messages.error(request, '您没有权限审批调整申请')
        return redirect('plan_pages:plan_adjustment_list')
    
    # 检查申请状态
    if adjustment.status != 'pending':
        messages.error(request, '该调整申请已处理，不能重复审批')
        return redirect('plan_pages:plan_adjustment_list')
    
    if request.method == 'POST':
        approval_notes = request.POST.get('approval_notes', '')
        
        # 更新调整申请状态
        adjustment.status = 'rejected'
        adjustment.approved_by = request.user
        adjustment.approved_time = timezone.now()
        adjustment.approval_notes = approval_notes
        adjustment.save()
        # 审批结果走通知中心，不写入 messages
        return redirect('plan_pages:plan_adjustment_list')
    
    context = _context(
        f"拒绝调整申请 - {plan.name}",
        "❌",
        "拒绝计划调整申请",
        request=request,
    )
    context['sidebar_nav'] = _build_plan_management_sidebar_nav(permission_set, active_id='plan_list')
    context['adjustment'] = adjustment
    context['plan'] = plan
    
    return render(request, "plan_management/plan_adjustment_reject.html", context)

