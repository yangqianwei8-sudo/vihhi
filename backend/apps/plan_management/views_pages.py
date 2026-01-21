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
from decimal import Decimal, InvalidOperation
import logging
from datetime import datetime, timedelta
from backend.apps.system_management.services import get_user_permission_codes
from backend.apps.system_management.models import User, Department

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
)

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
            {'id': 'plan_approval', 'label': '计划审批', 'icon': '✅', 'url_name': 'plan_pages:plan_approval_list', 'permission': 'plan_management.approve'},
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
    1. view_all: 查看全部计划（包括其他人的个人计划）
    2. view_assigned: 查看本人负责或参与的计划，以及所有公司计划
    3. view: 只能查看公司计划和自己负责/参与的个人计划
    
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
    
    # 检查是否有查看全部权限（最高级别）
    if _permission_granted('plan_management.plan.view_all', permission_set):
        return plans
    
    # 检查是否有查看负责计划权限
    if _permission_granted('plan_management.plan.view_assigned', permission_set):
        # 可以查看：自己负责的计划、自己拥有的计划、自己参与的计划、所有公司计划
        return plans.filter(
            Q(responsible_person=user) |
            Q(owner=user) |
            Q(participants=user) |
            Q(level='company')
        ).distinct()
    
    # 如果只有基础 view 权限，只能查看公司计划和自己负责/参与的个人计划
    # 这是默认行为，确保个人计划的隐私性
    return plans.filter(
        Q(level='company') |
        Q(responsible_person=user) |
        Q(owner=user) |
        Q(participants=user)
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
    
    try:
        # ========== P2-5: 导入所有 service ==========
        from backend.apps.plan_management.services.goal_stats_service import get_user_goal_stats, get_company_goal_stats
        from backend.apps.plan_management.services.plan_stats_service import get_user_plan_stats, get_company_plan_stats
        from backend.apps.plan_management.services.todo_service import get_user_todos
        from backend.apps.plan_management.services.risk_query_service import get_user_risk_items
        
        # ========== 第一行：目标中心（个人优先）==========
        goal_stats = get_user_goal_stats(request.user)
        
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
        plan_stats = get_user_plan_stats(request.user)
        
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
        
        # ========== 第三行：待办 & 风险 ==========
        # 我的待办（左）
        user_todos = get_user_todos(request.user)
        context['user_todos'] = user_todos[:5]  # 首页显示前5条
        context['user_todos_count'] = len(user_todos)
        
        # 风险提醒（右）
        risk_items = get_user_risk_items(request.user, limit=5)
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
    
    # ========== 安全字段检查（统一获取，避免重复）==========
    plan_fields = {f.name for f in Plan._meta.get_fields()}
    goal_fields = {f.name for f in StrategicGoal._meta.get_fields()}
    
    # ========== 计划状态分布（用于图表）==========
    plan_filter_kwargs = {}
    if 'level' in plan_fields:
        plan_filter_kwargs['level'] = 'personal'
    if 'owner' in plan_fields:
        plan_filter_kwargs['owner'] = request.user
    
    user_plans_qs = Plan.objects.filter(**plan_filter_kwargs) if plan_filter_kwargs else Plan.objects.none()
    plan_status_rows = user_plans_qs.values('status').annotate(count=Count('id')) if plan_filter_kwargs else []
    
    # 兼容：拿到"状态码 -> 显示名"的映射
    plan_status_label_map = {}
    try:
        # Django choices 常见写法：STATUS_CHOICES = [(code,label),...]
        for code, label in getattr(Plan, 'STATUS_CHOICES', Plan._meta.get_field('status').choices):
            plan_status_label_map[code] = label
    except Exception:
        # 兜底：没有 choices 就用原值
        plan_status_label_map = {}
    
    plan_status_dist = {}
    for row in plan_status_rows:
        code = row['status']
        cnt = row['count']
        plan_status_dist[str(code)] = {
            'label': plan_status_label_map.get(code, str(code)),
            'count': cnt
        }
    context['plan_status_dist'] = plan_status_dist or None
    
    # ========== 目标状态分布（用于图表）==========
    goal_filter_kwargs = {}
    if 'level' in goal_fields:
        goal_filter_kwargs['level'] = 'personal'
    if 'owner' in goal_fields:
        goal_filter_kwargs['owner'] = request.user
    
    user_goals_qs = StrategicGoal.objects.filter(**goal_filter_kwargs) if goal_filter_kwargs else StrategicGoal.objects.none()
    goal_status_rows = user_goals_qs.values('status').annotate(count=Count('id')) if goal_filter_kwargs else []
    
    goal_status_label_map = {}
    try:
        for code, label in getattr(StrategicGoal, 'STATUS_CHOICES', StrategicGoal._meta.get_field('status').choices):
            goal_status_label_map[code] = label
    except Exception:
        goal_status_label_map = {}
    
    goal_status_dist = {}
    for row in goal_status_rows:
        code = row['status']
        cnt = row['count']
        goal_status_dist[str(code)] = {
            'label': goal_status_label_map.get(code, str(code)),
            'count': cnt
        }
    context['goal_status_dist'] = goal_status_dist or None
    
    # ========== 我的工作 ==========
    my_work = {}
    
    # 我负责的计划（安全字段检查）
    plan_related_fields = []
    if 'responsible_person' in plan_fields:
        plan_related_fields.append('responsible_person')
    if 'related_goal' in plan_fields:
        plan_related_fields.append('related_goal')
    
    my_plans_qs = Plan.objects.filter(responsible_person=request.user).order_by('-updated_time') if 'responsible_person' in plan_fields else Plan.objects.none()
    my_plans = my_plans_qs.select_related(*plan_related_fields)[:5] if plan_related_fields and my_plans_qs else []
    my_work['my_plans'] = [{
        'title': p.name,
        'status': p.get_status_display() if hasattr(p, 'get_status_display') else str(getattr(p, 'status', '')),
        'progress': getattr(p, 'progress', 0) or 0,
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
    my_goals = my_goals_qs.select_related(*goal_related_fields)[:5] if goal_related_fields and my_goals_qs else []
    my_work['my_goals'] = [{
        'title': g.name,
        'status': g.get_status_display() if hasattr(g, 'get_status_display') else str(getattr(g, 'status', '')),
        'completion_rate': float(getattr(g, 'completion_rate', 0) or 0),
        'url': reverse('plan_pages:strategic_goal_detail', args=[g.id])
    } for g in my_goals]
    my_work['my_goals_count'] = my_goals_qs.count()
    
    # 我参与的计划（仅当 participants 字段存在才统计，避免 FieldError）
    participating_plans = []
    participating_plans_count = 0
    if 'participants' in plan_fields:
        participating_qs = Plan.objects.filter(participants=request.user).exclude(responsible_person=request.user).distinct().order_by('-updated_time')
        participating_plans = [{
            'title': p.name,
            'role': '参与者',
            'progress': getattr(p, 'progress', 0) or 0,
            'url': reverse('plan_pages:plan_detail', args=[p.id])
        } for p in participating_qs[:5]]
        participating_plans_count = participating_qs.count()
    
    my_work['participating_plans'] = participating_plans
    my_work['participating_plans_count'] = participating_plans_count
    
    context['my_work'] = my_work
    
    # ========== 最近活动 ==========
    recent_activities = {}
    
    # 最近创建的计划（个人计划，安全字段检查）
    plan_filter_kwargs = {}
    if 'level' in plan_fields:
        plan_filter_kwargs['level'] = 'personal'
    if 'owner' in plan_fields:
        plan_filter_kwargs['owner'] = request.user
    
    plan_related_fields = []
    if 'created_by' in plan_fields:
        plan_related_fields.append('created_by')
    if 'responsible_person' in plan_fields:
        plan_related_fields.append('responsible_person')
    
    recent_plans_qs = Plan.objects.filter(**plan_filter_kwargs) if plan_filter_kwargs else Plan.objects.none()
    recent_plans = recent_plans_qs.select_related(*plan_related_fields).order_by('-created_time')[:5] if plan_related_fields and recent_plans_qs else []
    recent_activities['recent_plans'] = [{
        'title': p.name,
        'creator': (p.created_by.get_full_name() if getattr(p, 'created_by', None) else '系统'),
        'time': getattr(p, 'created_time', None),
        'url': reverse('plan_pages:plan_detail', args=[p.id])
    } for p in recent_plans]
    
    # 最近更新的目标（个人目标，安全字段检查）
    goal_filter_kwargs = {}
    if 'level' in goal_fields:
        goal_filter_kwargs['level'] = 'personal'
    if 'owner' in goal_fields:
        goal_filter_kwargs['owner'] = request.user
    
    goal_related_fields = []
    if 'created_by' in goal_fields:
        goal_related_fields.append('created_by')
    if 'responsible_person' in goal_fields:
        goal_related_fields.append('responsible_person')
    if 'parent_goal' in goal_fields:
        goal_related_fields.append('parent_goal')
    
    recent_goals_qs = StrategicGoal.objects.filter(**goal_filter_kwargs) if goal_filter_kwargs else StrategicGoal.objects.none()
    recent_goals = recent_goals_qs.select_related(*goal_related_fields).order_by('-updated_time')[:5] if goal_related_fields and recent_goals_qs else []
    recent_activities['recent_goals'] = [{
        'title': g.name,
        'updater': (
            g.responsible_person.get_full_name() if getattr(g, 'responsible_person', None)
            else (g.created_by.get_full_name() if getattr(g, 'created_by', None) else '系统')
        ),
        'time': getattr(g, 'updated_time', None),
        'completion_rate': float(getattr(g, 'completion_rate', 0) or 0),
        'url': reverse('plan_pages:strategic_goal_detail', args=[g.id])
    } for g in recent_goals]
    
    # 最近审批记录（如果 PlanDecision 存在才查；避免 import/模型不存在直接炸）
    recent_activities['recent_approvals'] = []
    try:
        
        # 检查 plan__created_by 关系是否存在
        has_plan_created_by = 'plan' in decision_fields and hasattr(PlanDecision._meta.get_field('plan'), 'related_model')
        filter_kwargs = {}
        if has_plan_created_by:
            plan_model = PlanDecision._meta.get_field('plan').related_model
            if plan_model and 'created_by' in {f.name for f in plan_model._meta.get_fields()}:
                filter_kwargs['plan__created_by'] = request.user
        
        recent_approvals_qs = PlanDecision.objects.filter(**filter_kwargs) if filter_kwargs else PlanDecision.objects.none()
        recent_approvals = recent_approvals_qs.select_related(*decision_related_fields).order_by('-requested_at')[:5] if decision_related_fields and recent_approvals_qs else []
        
        recent_activities['recent_approvals'] = [{
            'plan_title': (a.plan.name if getattr(a, 'plan', None) else '未知计划'),
            'approver': (a.decided_by.get_full_name() if getattr(a, 'decided_by', None) else '待审批'),
            'result': (a.get_decision_display() if hasattr(a, 'get_decision_display') else str(getattr(a, 'decision', '待审批'))),
            'time': getattr(a, 'decided_at', None) or getattr(a, 'requested_at', None),
            'url': (reverse('plan_pages:plan_detail', args=[a.plan.id]) if getattr(a, 'plan', None) else '#')
        } for a in recent_approvals]
    except Exception:
        # 没有审批模型/不在该 app，就跳过
        pass
    
    context['recent_activities'] = recent_activities
    
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
    
    return render(request, "plan_management/home.html", page_context)


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
    
    # 统计信息（所有状态）
    total_count = Plan.objects.count()
    draft_count = Plan.objects.filter(status='draft').count()
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
        # 检查是否是草稿保存
        is_draft = request.POST.get('action') == 'draft'
        form = PlanForm(request.POST, user=request.user, is_draft=is_draft)
        if form.is_valid():
            plan = form.save(commit=False)
            plan.created_by = request.user
            
            # P2-3: 确保 level 正确设置
            if not plan.level:
                if plan.parent_plan:
                    plan.level = 'personal'
                    # 个人计划的 owner = responsible_person
                    if plan.responsible_person and not plan.owner:
                        plan.owner = plan.responsible_person
                else:
                    plan.level = 'company'
            
            # 如果是草稿保存，设置状态为 draft
            if is_draft:
                plan.status = 'draft'
            
            plan.save()
            
            # 保存多对多关系
            if 'participants' in form.cleaned_data:
                plan.participants.set(form.cleaned_data['participants'])
            
            if is_draft:
                messages.success(request, f'计划 {plan.name} 已暂存为草稿')
            else:
                messages.success(request, f'计划 {plan.name} 创建成功')
            return redirect('plan_pages:plan_detail', plan_id=plan.id)
        else:
            messages.error(request, '表单验证失败，请检查输入')
            # 关键：无效就回渲染，不要 redirect
            context = _context("创建计划", "➕", "创建新的工作计划", request=request)
            context['sidebar_nav'] = _build_plan_management_sidebar_nav(permission_set, active_id='plan_create')
            context['form'] = form
            context['page_title'] = "创建计划"
            context['submit_text'] = "创建"
            context['cancel_url_name'] = 'plan_pages:plan_list'
            context['form_js_file'] = 'js/plan_form_date_calculator.js'
            context['form_page_subtitle_text'] = '请填写计划基本信息'
            return render(request, "plan_management/plan_form.html", context)
    else:
        form = PlanForm(user=request.user)
    
    context = _context("创建计划", "➕", "创建新的工作计划", request=request)
    context['sidebar_nav'] = _build_plan_management_sidebar_nav(permission_set, active_id='plan_create')
    context['form'] = form
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
    
    # 权限检查：根据后台配置的权限判断是否可以查看该计划
    # 个人计划只能由 owner、responsible_person、参与者或有 view_all 权限的用户查看
    has_view_all = _permission_granted('plan_management.plan.view_all', permission_set)
    if plan.level == 'personal':
        if not has_view_all:
            # 检查是否是计划的所有者、负责人或参与者
            is_owner = plan.owner == request.user
            is_responsible = plan.responsible_person == request.user
            is_participant = request.user in plan.participants.all()
            if not (is_owner or is_responsible or is_participant):
                messages.error(request, '您没有权限查看该个人计划')
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
    # 允许草稿和已取消状态的计划提交审批
    can_submit_approval = (_permission_granted('plan_management.plan.create', permission_set) or plan.responsible_person == request.user) and plan.status in ['draft', 'cancelled']
    can_request_cancel = (_permission_granted('plan_management.plan.create', permission_set) or plan.responsible_person == request.user) and plan.status == 'in_progress'
    
    # 检查是否存在 pending 的决策
    has_pending_start = PlanDecision.objects.filter(plan=plan, request_type='start', decided_at__isnull=True).exists()
    has_pending_cancel = PlanDecision.objects.filter(plan=plan, request_type='cancel', decided_at__isnull=True).exists()
    
    # 获取待审批的决策列表（用于审批人）
    pending_decisions = PlanDecision.objects.filter(plan=plan, decided_at__isnull=True).order_by('-requested_at')
    can_approve = _permission_granted('plan_management.approve_plan', permission_set) or request.user.is_superuser
    
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
    
    context.update({
        'plan': plan,
        'object': plan,  # 为 detail_base.html 模板提供 object 变量
        'progress_records': progress_records,
        'status_logs': status_logs,
        'issues': issues,
        'child_plans': child_plans,
        'inactivity_logs': inactivity_logs,  # P2: 不作为记录
        'progress_percent': progress_percent,  # 时间进度百分比
        'can_edit': (
            (plan.responsible_person == request.user or _permission_granted('plan_management.plan.manage', permission_set)) and 
            plan.status in ['draft', 'cancelled'] and 
            not has_pending_start and 
            not has_pending_cancel
        ),
        'can_delete': _permission_granted('plan_management.plan.manage', permission_set) and plan.status == 'draft',
        # P1 新增权限
        'can_submit_approval': can_submit_approval and not has_pending_start,
        'can_request_cancel': can_request_cancel and not has_pending_cancel,
        'pending_decisions': pending_decisions,
        'can_approve': can_approve,
        # 计划调整申请权限
        'can_request_adjustment': can_request_adjustment and not has_pending_adjustment,
        # P2-3: 接收和开始执行权限
        'can_accept': can_accept,
        'can_start_execution': can_start_execution,
    })
    return render(request, "plan_management/plan_detail.html", context)


@login_required
def plan_edit(request, plan_id):
    """计划编辑页面"""
    permission_set = get_user_permission_codes(request.user)
    
    plan = get_object_or_404(Plan, id=plan_id)
    
    # 检查是否有待审批的决策（提交审批后不能编辑）
    has_pending_decision = PlanDecision.objects.filter(plan=plan, decided_at__isnull=True).exists()
    
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
            messages.error(request, '表单验证失败，请检查输入')
            # 关键：无效就回渲染，不要 redirect
            context = _context(
                f"编辑计划 - {plan.name}",
                "✏️",
                "编辑工作计划",
                request=request,
            )
            context['sidebar_nav'] = _build_plan_management_sidebar_nav(permission_set, active_id='plan_list')
            context['form'] = form
            context['plan'] = plan
            context['page_title'] = f"编辑计划 - {plan.name}"
            context['submit_text'] = "保存"
            context['cancel_url'] = reverse('plan_pages:plan_detail', args=[plan.id])
            context['form_js_file'] = 'js/plan_form_date_calculator.js'
            context['form_page_subtitle_text'] = '请修改计划信息'
            return render(request, "plan_management/plan_form.html", context)
    else:
        form = PlanForm(instance=plan, user=request.user)
    
    context = _context(
        f"编辑计划 - {plan.name}",
        "✏️",
        "编辑工作计划",
        request=request,
    )
    context['sidebar_nav'] = _build_plan_management_sidebar_nav(permission_set, active_id='plan_list')
    context['form'] = form
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
    展示所有待裁决 PlanDecision（decided_at is null）
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
    
    # 应用筛选
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
    pending_decisions = pending_decisions.order_by("-requested_at")
    
    # 分页
    page_size = request.GET.get('page_size', '10')
    try:
        per_page = int(page_size)
        if per_page not in [10, 20, 50, 100]:
            per_page = 10
    except (ValueError, TypeError):
        per_page = 10
    
    paginator = Paginator(pending_decisions, per_page)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # 统计信息（基于原始查询，不受筛选影响，但应用公司数据隔离）
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
    
    total_count = stats_base.count()
    pending_count = stats_base.filter(request_type='start').count()
    cancel_count = stats_base.filter(request_type='cancel').count()
    
    # 获取所有用户（用于筛选）
    all_users = User.objects.filter(
        id__in=pending_decisions.values_list('requested_by_id', flat=True).distinct()
    ).order_by('username')
    
    context = _context(
        "计划审批列表",
        "✅",
        "待裁决的计划请求",
        request=request,
    )
    context['sidebar_nav'] = _build_plan_management_sidebar_nav(permission_set, active_id='plan_approval')
    context.update({
        "page_obj": page_obj,
        "pending_decisions": list(page_obj),  # 保持向后兼容
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
    context['sidebar_nav'] = _build_plan_management_sidebar_nav(permission_set, active_id='plan_progress_update')
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
        # 检查是否是草稿保存
        is_draft = request.POST.get('action') == 'draft'
        form = StrategicGoalForm(request.POST, user=request.user, is_draft=is_draft)
        
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
            
            # 如果是草稿保存，设置状态为 draft
            if is_draft:
                goal.status = 'draft'
            
            goal.save()
            
            if is_draft:
                messages.success(request, f'战略目标 {goal.name} 已暂存为草稿')
            else:
                messages.success(request, f'战略目标 {goal.name} 创建成功')
            return redirect('plan_pages:strategic_goal_detail', goal_id=goal.id)
        else:
            messages.error(request, '表单验证失败，请检查输入')
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
        'can_edit': _permission_granted('plan_management.manage_goal', permission_set) and goal.status in ['draft', 'published'],
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

@login_required
def plan_request_start(request, plan_id):
    """发起启动计划请求（提交审批）"""
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
    
    # 检查是否已存在 pending 的 start 请求
    existing_pending = PlanDecision.objects.filter(
        plan=plan,
        request_type='start',
        decided_at__isnull=True
    ).exists()
    
    if existing_pending:
        messages.warning(request, '该计划已有待处理的启动请求')
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
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f'记录状态变更日志失败: {e}', exc_info=True)
            messages.error(request, f'状态变更记录失败: {str(e)}')
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
    
    # 权限检查：plan_management.plan.create 或负责人
    can_request = _permission_granted('plan_management.plan.create', permission_set) or plan.responsible_person == request.user
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
    
    # 使用服务层的 decide 函数统一处理
    from backend.apps.plan_management.services.plan_decisions import decide, PlanDecisionError
    from django.core.exceptions import PermissionDenied
    
    try:
        # decide() 函数内部已经创建了状态变更日志，这里不需要重复创建
        decision_obj = decide(decision_id, request.user, approve=True, reason=request.POST.get('reason'))
        
        messages.success(request, f'审批通过，计划状态已更新为：{plan.get_status_display()}')
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
        
        # reject 不改状态，只记录日志
        messages.success(request, '已驳回请求，计划状态保持不变')
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
            messages.success(request, '调整申请已提交，等待审批')
            return redirect('plan_pages:plan_detail', plan_id=plan_id)
        else:
            messages.error(request, '表单验证失败，请检查输入')
    else:
        form = PlanAdjustmentForm(plan=plan)
    
    context = _context(
        f"申请调整 - {plan.name}",
        "📝",
        "申请调整计划截止时间",
        request=request,
    )
    context['sidebar_nav'] = _build_plan_management_sidebar_nav(permission_set, active_id='plan_list')
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
        
        messages.success(request, '调整申请已批准，计划截止时间已更新')
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
        
        messages.success(request, '调整申请已拒绝')
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

