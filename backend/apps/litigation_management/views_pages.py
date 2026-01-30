"""
诉讼管理模块页面视图
"""
import logging
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count, Sum, Avg
from django.utils import timezone
from django.urls import reverse, NoReverseMatch
from datetime import datetime, timedelta
from decimal import Decimal

from backend.apps.system_management.services import get_user_permission_codes
from backend.core.views import HOME_NAV_STRUCTURE, _permission_granted, _build_full_top_nav
from backend.apps.litigation_management.models import (
    LitigationCase, LitigationProcess, LitigationDocument,
    LitigationExpense, LitigationPerson, LitigationTimeline,
    PreservationSeal
)
from .forms import (
    LitigationCaseForm, LitigationProcessForm, LitigationDocumentForm,
    LitigationExpenseForm, LitigationPersonForm, LitigationTimelineForm,
    PreservationSealForm
)
from .services_approval import LitigationApprovalService
from backend.apps.production_management.models import Project
from backend.apps.customer_management.models import Client
from backend.apps.contract_management.models import BusinessContract

logger = logging.getLogger(__name__)


# 使用统一的顶部导航菜单生成函数
from backend.core.views import _build_full_top_nav


def _build_litigation_sidebar_nav(permission_set, request_path=None, active_id=None):
    """生成诉讼管理左侧菜单"""
    nav_items = []
    
    # 诉讼管理首页
    try:
        home_url = reverse('litigation_pages:litigation_management_home')
        is_home_active = (
            request_path == home_url or
            request_path == reverse('litigation_pages:litigation_home') or
            active_id == 'litigation_home'
        )
        nav_items.append({
            'label': '案件管理',
            'icon': '📋',
            'url': home_url,
            'active': is_home_active,
            'is_home': True,
        })
    except NoReverseMatch:
        pass
    
    # 案件管理分组
    case_items = []
    
    # 基础权限检查：只要有诉讼管理查看权限就可以看到案件列表
    if _permission_granted('litigation_management.view', permission_set) or _permission_granted('litigation_management.case.view', permission_set):
        try:
            case_list_url = reverse('litigation_pages:case_list')
            case_items.append({
                'label': '案件列表',
                'icon': '📋',
                'url': case_list_url,
                'active': request_path == case_list_url or (request_path and '/cases/' in request_path),
            })
        except NoReverseMatch:
            pass
    
    if _permission_granted('litigation_management.case.create', permission_set) or _permission_granted('litigation_management.view', permission_set):
        try:
            create_url = reverse('litigation_pages:case_create')
            case_items.append({
                'label': '案件登记',
                'icon': '➕',
                'url': create_url,
                'active': request_path == create_url,
            })
        except NoReverseMatch:
            pass
    
    if case_items:
        has_active = any(item.get('active') for item in case_items)
        nav_items.append({
            'label': '案件管理',
            'icon': '📋',
            'children': case_items,  # 使用 children 而不是 items
            'expanded': has_active,  # 如果有激活项，默认展开
            'active': has_active,
        })
    
    # 诉讼流程分组 - 指向案件列表页面（通过process_type筛选）
    process_items = []
    
    if _permission_granted('litigation_management.process.manage', permission_set) or _permission_granted('litigation_management.view', permission_set):
        try:
            filing_url = reverse('litigation_pages:case_list') + '?process_type=filing'
            process_items.append({
                'label': '立案管理',
                'icon': '📄',
                'url': filing_url,
                'active': request_path and ('process_type=filing' in request_path or '/processes/' in request_path),
            })
        except NoReverseMatch:
            pass
        
        try:
            trial_url = reverse('litigation_pages:case_list') + '?process_type=trial'
            process_items.append({
                'label': '庭审管理',
                'icon': '⚖️',
                'url': trial_url,
                'active': request_path and ('process_type=trial' in request_path or '/processes/' in request_path),
            })
        except NoReverseMatch:
            pass
        
        try:
            judgment_url = reverse('litigation_pages:case_list') + '?process_type=judgment'
            process_items.append({
                'label': '判决管理',
                'icon': '📜',
                'url': judgment_url,
                'active': request_path and ('process_type=judgment' in request_path or '/processes/' in request_path),
            })
        except NoReverseMatch:
            pass
        
        try:
            execution_url = reverse('litigation_pages:case_list') + '?process_type=execution'
            process_items.append({
                'label': '执行管理',
                'icon': '⚡',
                'url': execution_url,
                'active': request_path and ('process_type=execution' in request_path or '/processes/' in request_path),
            })
        except NoReverseMatch:
            pass
    
    if process_items:
        has_active = any(item.get('active') for item in process_items)
        nav_items.append({
            'label': '诉讼流程',
            'icon': '⚖️',
            'children': process_items,  # 使用 children 而不是 items
            'expanded': has_active,  # 如果有激活项，默认展开
            'active': has_active,
        })
    
    # 保全续封分组（⚠️ 极高优先级）- 指向全局保全续封列表页面
    preservation_items = []
    
    if _permission_granted('litigation_management.process.manage', permission_set) or _permission_granted('litigation_management.view', permission_set):
        try:
            preservation_url = reverse('litigation_pages:preservation_list_all')
            preservation_items.append({
                'label': '保全续封',
                'icon': '🔒',
                'url': preservation_url,
                'active': request_path and '/preservation/' in request_path and '/cases/' not in request_path,
            })
        except NoReverseMatch:
            pass
        
        try:
            expiring_url = reverse('litigation_pages:preservation_list_all') + '?expiring=1'
            preservation_items.append({
                'label': '即将到期',
                'icon': '⚠️',
                'url': expiring_url,
                'active': request_path and ('/preservation/' in request_path and 'expiring=1' in request_path or '/preservation/' in request_path),
            })
        except NoReverseMatch:
            pass
    
    if preservation_items:
        has_active = any(item.get('active') for item in preservation_items)
        nav_items.append({
            'label': '保全续封',
            'icon': '🔒',
            'children': preservation_items,  # 使用 children 而不是 items
            'expanded': has_active,  # 如果有激活项，默认展开
            'active': has_active,
        })
    
    # 诉讼文档分组 - 指向全局文档列表页面
    document_items = []
    
    if _permission_granted('litigation_management.document.view', permission_set) or _permission_granted('litigation_management.view', permission_set):
        try:
            document_list_url = reverse('litigation_pages:document_list_all')
            document_items.append({
                'label': '文档管理',
                'icon': '📄',
                'url': document_list_url,
                'active': request_path and '/documents/' in request_path and '/cases/' not in request_path,
            })
        except NoReverseMatch:
            pass
        
        try:
            evidence_url = reverse('litigation_pages:document_list_all') + '?type=evidence'
            document_items.append({
                'label': '证据管理',
                'icon': '🔍',
                'url': evidence_url,
                'active': request_path and '/documents/' in request_path and 'type=evidence' in request_path,
            })
        except NoReverseMatch:
            pass
        
        try:
            legal_doc_url = reverse('litigation_pages:document_list_all') + '?type=legal_document'
            document_items.append({
                'label': '文书管理',
                'icon': '📝',
                'url': legal_doc_url,
                'active': request_path and '/documents/' in request_path and 'type=legal_document' in request_path,
            })
        except NoReverseMatch:
            pass
    
    if document_items:
        has_active = any(item.get('active') for item in document_items)
        nav_items.append({
            'label': '诉讼文档',
            'icon': '📄',
            'children': document_items,  # 使用 children 而不是 items
            'expanded': has_active,  # 如果有激活项，默认展开
            'active': has_active,
        })
    
    # 费用管理分组 - 指向全局费用列表页面
    expense_items = []
    
    if _permission_granted('litigation_management.expense.view', permission_set) or _permission_granted('litigation_management.view', permission_set):
        try:
            expense_list_url = reverse('litigation_pages:expense_list_all')
            expense_items.append({
                'label': '费用登记',
                'icon': '💰',
                'url': expense_list_url,
                'active': request_path and '/expenses/' in request_path and '/cases/' not in request_path and '/reimburse' not in request_path,
            })
        except NoReverseMatch:
            pass
        
        try:
            expense_stats_url = reverse('litigation_pages:expense_statistics')
            expense_items.append({
                'label': '费用统计',
                'icon': '📊',
                'url': expense_stats_url,
                'active': request_path == expense_stats_url or (request_path and '/statistics/expenses' in request_path),
            })
        except NoReverseMatch:
            pass
        
        try:
            expense_reimburse_url = reverse('litigation_pages:expense_reimburse_list')
            expense_items.append({
                'label': '费用报销',
                'icon': '💳',
                'url': expense_reimburse_url,
                'active': request_path and '/expenses/reimburse' in request_path,
            })
        except NoReverseMatch:
            pass
    
    if expense_items:
        has_active = any(item.get('active') for item in expense_items)
        nav_items.append({
            'label': '费用管理',
            'icon': '💰',
            'children': expense_items,  # 使用 children 而不是 items
            'expanded': has_active,  # 如果有激活项，默认展开
            'active': has_active,
        })
    
    # 人员管理分组 - 指向全局人员列表页面
    person_items = []
    
    if _permission_granted('litigation_management.person.manage', permission_set) or _permission_granted('litigation_management.view', permission_set):
        try:
            person_list_url = reverse('litigation_pages:person_list_all') + '?type=lawyer'
            person_items.append({
                'label': '律师管理',
                'icon': '👨‍⚖️',
                'url': person_list_url,
                'active': request_path and '/persons/' in request_path and '/cases/' not in request_path and 'type=lawyer' in request_path,
            })
        except NoReverseMatch:
            pass
        
        try:
            judge_url = reverse('litigation_pages:person_list_all') + '?type=judge'
            person_items.append({
                'label': '法官管理',
                'icon': '⚖️',
                'url': judge_url,
                'active': request_path and '/persons/' in request_path and '/cases/' not in request_path and 'type=judge' in request_path,
            })
        except NoReverseMatch:
            pass
        
        try:
            party_url = reverse('litigation_pages:person_list_all') + '?type=party'
            person_items.append({
                'label': '当事人管理',
                'icon': '👥',
                'url': party_url,
                'active': request_path and '/persons/' in request_path and '/cases/' not in request_path and 'type=party' in request_path,
            })
        except NoReverseMatch:
            pass
    
    if person_items:
        has_active = any(item.get('active') for item in person_items)
        nav_items.append({
            'label': '人员管理',
            'icon': '👥',
            'children': person_items,  # 使用 children 而不是 items
            'expanded': has_active,  # 如果有激活项，默认展开
            'active': has_active,
        })
    
    # 时间管理分组 - 指向全局时间节点列表页面或日历视图
    timeline_items = []
    
    if _permission_granted('litigation_management.timeline.manage', permission_set) or _permission_granted('litigation_management.view', permission_set):
        try:
            timeline_list_url = reverse('litigation_pages:timeline_list_all')
            timeline_items.append({
                'label': '时间节点',
                'icon': '📅',
                'url': timeline_list_url,
                'active': request_path and '/timelines/' in request_path and '/cases/' not in request_path and '/calendar/' not in request_path,
            })
        except NoReverseMatch:
            pass
        
        try:
            reminder_url = reverse('litigation_pages:timeline_list_all') + '?reminder=1'
            timeline_items.append({
                'label': '提醒设置',
                'icon': '🔔',
                'url': reminder_url,
                'active': request_path and '/timelines/' in request_path and 'reminder=1' in request_path,
            })
        except NoReverseMatch:
            pass
        
        try:
            calendar_url = reverse('litigation_pages:timeline_calendar')
            timeline_items.append({
                'label': '日历视图',
                'icon': '📆',
                'url': calendar_url,
                'active': request_path == calendar_url or '/timelines/calendar' in request_path,
            })
        except NoReverseMatch:
            pass
    
    if timeline_items:
        has_active = any(item.get('active') for item in timeline_items)
        nav_items.append({
            'label': '时间管理',
            'icon': '📅',
            'children': timeline_items,  # 使用 children 而不是 items
            'expanded': has_active,  # 如果有激活项，默认展开
            'active': has_active,
        })
    
    # 案件统计
    if _permission_granted('litigation_management.statistics.view', permission_set):
        try:
            stats_url = reverse('litigation_pages:case_statistics')
            nav_items.append({
                'label': '案件统计',
                'icon': '📊',
                'url': stats_url,
                'active': request_path == stats_url or (request_path and '/statistics/' in request_path),
            })
        except NoReverseMatch:
            pass
    
    return nav_items


def _context(page_title, page_icon, description, summary_cards=None, sections=None, request=None):
    """构建页面上下文"""
    context = {
        "page_title": page_title,
        "page_icon": page_icon,
        "description": description,
        "summary_cards": summary_cards or [],
        "sections": sections or [],
    }
    
    # 添加顶部导航菜单
    if request and request.user.is_authenticated:
        permission_set = get_user_permission_codes(request.user)
        context['full_top_nav'] = _build_full_top_nav(permission_set, request.user)
        
        # 添加左侧菜单
        request_path = request.path
        context['sidebar_nav'] = _build_litigation_sidebar_nav(permission_set, request_path)
    else:
        context['full_top_nav'] = []
        context['sidebar_nav'] = []
    
    # 为所有可能的侧边栏变量设置默认值，避免模板错误
    # 这些变量可能在其他模块的模板中被引用
    context.setdefault('plan_menu', [])
    context.setdefault('module_sidebar_nav', [])
    context.setdefault('sidebar_nav', [])
    context.setdefault('customer_menu', [])
    context.setdefault('sidebar_nav', [])
    context.setdefault('sidebar_nav', [])
    context.setdefault('sidebar_nav', [])
    context.setdefault('sidebar_nav', [])
    context.setdefault('sidebar_nav', [])
    context.setdefault('sidebar_nav', [])
    
    return context


# ==================== 诉讼管理首页 ====================

def _format_user_display(user, default='—'):
    """格式化用户显示名称"""
    if not user:
        return default
    if hasattr(user, 'get_full_name') and user.get_full_name():
        return user.get_full_name()
    return user.username if hasattr(user, 'username') else str(user)


@login_required
def litigation_home(request):
    """诉讼管理首页 - 数据展示中心"""
    permission_codes = get_user_permission_codes(request.user)
    
    # 检查权限
    if not _permission_granted('litigation_management.view', permission_codes):
        messages.error(request, '您没有权限访问诉讼管理')
        return redirect('admin:index')
    
    now = timezone.now()
    today = now.date()
    this_month_start = today.replace(day=1)
    seven_days_ago = today - timedelta(days=7)
    
    context = {}
    
    try:
        # 获取案件列表
        cases = LitigationCase.objects.select_related(
            'project', 'client', 'contract', 'case_manager', 'registered_by'
        ).all()
        
        # 权限过滤
        if not _permission_granted('litigation_management.case.view_all', permission_codes):
            cases = cases.filter(Q(case_manager=request.user) | Q(registered_by=request.user))
        
        # ========== 核心指标卡片 ==========
        core_cards = []
        
        # 案件统计
        total_cases = cases.count()
        pending_filing = cases.filter(status='pending_filing').count()
        filed = cases.filter(status='filed').count()
        trial = cases.filter(status='trial').count()
        judged = cases.filter(status='judged').count()
        executing = cases.filter(status='executing').count()
        closed = cases.filter(status='closed').count()
        this_month_cases = cases.filter(created_at__gte=this_month_start).count()
        
        # 检查即将到期的时间节点和保全续封
        today_start = timezone.make_aware(datetime.combine(today, datetime.min.time()))
        today_end = timezone.make_aware(datetime.combine(today + timedelta(days=7), datetime.max.time()))
        expiring_timelines = LitigationTimeline.objects.filter(
            case__in=cases,
            reminder_enabled=True,
            timeline_date__lte=today_end,
            timeline_date__gte=today_start,
            status__in=['pending', 'in_progress']
        ).count()
        
        expiring_seals = PreservationSeal.objects.filter(
            case__in=cases,
            status='active',
            end_date__lte=today + timedelta(days=7),
            end_date__gte=today
        ).count()
        
        urgent_count = expiring_timelines + expiring_seals
        
        # 费用统计
        total_expenses = LitigationExpense.objects.filter(case__in=cases).aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0')
        
        # 卡片1：案件总数
        core_cards.append({
            'label': '案件总数',
            'icon': '⚖️',
            'value': str(total_cases),
            'subvalue': f'待立案 {pending_filing} | 审理中 {trial} | 已结案 {closed}',
            'url': reverse('litigation_pages:case_list'),
            'variant': 'secondary'
        })
        
        # 卡片2：待立案案件
        core_cards.append({
            'label': '待立案案件',
            'icon': '📋',
            'value': str(pending_filing),
            'subvalue': f'等待立案审批',
            'url': reverse('litigation_pages:case_list') + '?status=pending_filing',
            'variant': 'dark' if pending_filing > 0 else 'secondary'
        })
        
        # 卡片3：审理中案件
        core_cards.append({
            'label': '审理中案件',
            'icon': '⚖️',
            'value': str(trial),
            'subvalue': f'正在审理中',
            'url': reverse('litigation_pages:case_list') + '?status=trial',
            'variant': 'secondary'
        })
        
        # 卡片4：紧急事项
        core_cards.append({
            'label': '紧急事项',
            'icon': '⚠️',
            'value': str(urgent_count),
            'subvalue': f'即将到期的时间节点 {expiring_timelines} | 保全续封 {expiring_seals}',
            'url': reverse('litigation_pages:case_list') + '?urgent=1',
            'variant': 'dark' if urgent_count > 0 else 'secondary'
        })
        
        # 卡片5：诉讼费用
        core_cards.append({
            'label': '诉讼费用',
            'icon': '💰',
            'value': f'{total_expenses:,.0f}',
            'subvalue': f'累计费用总额',
            'url': reverse('litigation_pages:expense_list_all'),
            'variant': 'secondary'
        })
        
        # 卡片6：已结案
        core_cards.append({
            'label': '已结案',
            'icon': '✅',
            'value': str(closed),
            'subvalue': f'本月结案 {this_month_cases} 个',
            'url': reverse('litigation_pages:case_list') + '?status=closed',
            'variant': 'secondary'
        })
        
        context['core_cards'] = core_cards
        
        # ========== 风险预警 ==========
        risk_warnings = []
        
        # 即将到期的时间节点
        upcoming_timelines = LitigationTimeline.objects.filter(
            case__in=cases,
            reminder_enabled=True,
            timeline_date__lte=today_end,
            timeline_date__gte=today_start,
            status__in=['pending', 'in_progress']
        ).select_related('case', 'case__case_manager')[:5]
        
        for timeline in upcoming_timelines:
            days_until = (timeline.timeline_date.date() - today).days
            manager_name = _format_user_display(timeline.case.case_manager) if timeline.case.case_manager else '未知'
            risk_warnings.append({
                'type': 'timeline',
                'title': f'{timeline.case.case_number} - {timeline.timeline_name}',
                'responsible': manager_name,
                'days': days_until,
                'url': reverse('litigation_pages:case_detail', args=[timeline.case.id])
            })
        
        # 即将到期的保全续封
        upcoming_seals = PreservationSeal.objects.filter(
            case__in=cases,
            status='active',
            end_date__lte=today + timedelta(days=7),
            end_date__gte=today
        ).select_related('case', 'case__case_manager')[:5]
        
        for seal in upcoming_seals:
            days_until = (seal.end_date - today).days
            manager_name = _format_user_display(seal.case.case_manager) if seal.case.case_manager else '未知'
            risk_warnings.append({
                'type': 'seal',
                'title': f'{seal.case.case_number} - {seal.get_seal_type_display()}',
                'responsible': manager_name,
                'days': days_until,
                'url': reverse('litigation_pages:case_detail', args=[seal.case.id])
            })
        
        context['risk_warnings'] = risk_warnings[:5]
        context['expiring_timelines_count'] = expiring_timelines
        context['expiring_seals_count'] = expiring_seals
        
        # ========== 待办事项 ==========
        todo_items = []
        
        # 待立案案件
        pending_filing_cases = cases.filter(status='pending_filing').select_related('registered_by')[:5]
        for case in pending_filing_cases:
            registered_by_name = _format_user_display(case.registered_by) if case.registered_by else '未知'
            todo_items.append({
                'type': 'filing',
                'title': case.case_number,
                'case_number': case.case_number,
                'responsible': registered_by_name,
                'url': reverse('litigation_pages:case_detail', args=[case.id])
            })
        
        # 待处理的时间节点
        pending_timelines = LitigationTimeline.objects.filter(
            case__in=cases,
            status='pending',
            timeline_date__lte=today_end
        ).select_related('case', 'case__case_manager')[:5]
        
        for timeline in pending_timelines:
            manager_name = _format_user_display(timeline.case.case_manager) if timeline.case.case_manager else '未知'
            todo_items.append({
                'type': 'timeline',
                'title': f'{timeline.case.case_number} - {timeline.timeline_name}',
                'case_number': timeline.case.case_number,
                'responsible': manager_name,
                'url': reverse('litigation_pages:case_detail', args=[timeline.case.id])
            })
        
        context['todo_items'] = todo_items[:10]
        context['pending_approval_count'] = pending_filing + len(pending_timelines)
        context['todo_summary_url'] = reverse('litigation_pages:case_list') + '?status=pending_filing'
        
        # ========== 我的工作 ==========
        my_work = {}
        
        # 我负责的案件
        my_cases = cases.filter(case_manager=request.user).order_by('-created_at')[:3]
        my_work['my_cases'] = [{
            'title': case.case_number,
            'status': case.get_status_display(),
            'url': reverse('litigation_pages:case_detail', args=[case.id])
        } for case in my_cases]
        my_work['my_cases_count'] = cases.filter(case_manager=request.user).count()
        
        # 我登记的案件
        my_registered_cases = cases.filter(registered_by=request.user).order_by('-created_at')[:3]
        my_work['my_registered_cases'] = [{
            'title': case.case_number,
            'status': case.get_status_display(),
            'url': reverse('litigation_pages:case_detail', args=[case.id])
        } for case in my_registered_cases]
        my_work['my_registered_cases_count'] = cases.filter(registered_by=request.user).count()
        
        my_work['summary_url'] = reverse('litigation_pages:case_list')
        
        context['my_work'] = my_work
        
        # ========== 最近活动 ==========
        recent_activities = {}
        
        # 最近创建的案件
        recent_cases = cases.select_related('registered_by').order_by('-created_at')[:5]
        recent_activities['recent_cases'] = [{
            'title': case.case_number,
            'creator': _format_user_display(case.registered_by),
            'time': case.created_at,
            'url': reverse('litigation_pages:case_detail', args=[case.id])
        } for case in recent_cases]
        
        # 最近更新的案件
        recent_updated_cases = cases.select_related('case_manager').order_by('-updated_at')[:5]
        recent_activities['recent_updates'] = [{
            'title': case.case_number,
            'creator': _format_user_display(case.case_manager),
            'time': case.updated_at,
            'url': reverse('litigation_pages:case_detail', args=[case.id])
        } for case in recent_updated_cases]
        
        context['recent_activities'] = recent_activities
        
    except Exception as e:
        logger.exception('获取诉讼管理统计数据失败: %s', str(e))
        context.setdefault('core_cards', [])
        context.setdefault('risk_warnings', [])
        context.setdefault('todo_items', [])
        context.setdefault('my_work', {})
        context.setdefault('recent_activities', {})
    
    # 顶部操作栏
    top_actions = []
    if _permission_granted('litigation_management.case.create', permission_codes):
        try:
            top_actions.append({
                'label': '登记案件',
                'url': reverse('litigation_pages:case_create'),
                'icon': '➕'
            })
        except Exception:
            pass
    
    context['top_actions'] = top_actions
    
    # 构建上下文
    page_context = _context(
        "诉讼管理",
        "⚖️",
        "数据展示中心 - 集中展示诉讼关键指标、状态与风险",
        request=request,
    )
    
    # 设置侧边栏导航
    litigation_sidebar_nav = _build_litigation_sidebar_nav(permission_codes, request.path, active_id='litigation_home')
    page_context['sidebar_nav'] = litigation_sidebar_nav
    page_context['sidebar_title'] = '诉讼管理'
    page_context['sidebar_subtitle'] = 'Litigation Management'
    
    # 合并所有数据
    page_context.update(context)
    
    return render(request, "litigation_management/litigation_management_home.html", page_context)


# ==================== 案件管理 ====================

@login_required
def case_list(request):
    """案件列表页面"""
    permission_codes = get_user_permission_codes(request.user)
    
    # 检查权限
    if not _permission_granted('litigation_management.case.view', permission_codes):
        messages.error(request, '您没有权限查看诉讼案件')
        return redirect('admin:index')
    
    # 获取筛选参数
    search = request.GET.get('search', '')
    case_type = request.GET.get('case_type', '')
    case_nature = request.GET.get('case_nature', '')
    status = request.GET.get('status', '')
    priority = request.GET.get('priority', '')
    process_type = request.GET.get('process_type', '')
    preservation = request.GET.get('preservation', '')
    preservation_expiring = request.GET.get('preservation_expiring', '')
    urgent = request.GET.get('urgent', '')
    tab = request.GET.get('tab', '')
    
    # 获取案件列表（用于统计，在筛选之前）
    base_cases = LitigationCase.objects.select_related(
        'project', 'client', 'contract', 'case_manager', 'registered_by', 'registered_department'
    ).all()
    
    # 权限过滤：普通用户只能查看自己负责的案件
    if not _permission_granted('litigation_management.case.view_all', permission_codes):
        base_cases = base_cases.filter(Q(case_manager=request.user) | Q(registered_by=request.user))
    
    # 统计数据（在过滤之前获取，显示全部数据统计）
    total_count = base_cases.count()
    pending_filing_count = base_cases.filter(status='pending_filing').count()
    filed_count = base_cases.filter(status='filed').count()
    trial_count = base_cases.filter(status='trial').count()
    judged_count = base_cases.filter(status='judged').count()
    executing_count = base_cases.filter(status='executing').count()
    closed_count = base_cases.filter(status='closed').count()
    
    # 应用筛选
    cases = base_cases
    
    if search:
        cases = cases.filter(
            Q(case_number__icontains=search) |
            Q(case_name__icontains=search) |
            Q(description__icontains=search) |
            Q(project__name__icontains=search) |
            Q(project__project_number__icontains=search) |
            Q(client__name__icontains=search) |
            Q(contract__contract_number__icontains=search)
        )
    
    if case_type:
        cases = cases.filter(case_type=case_type)
    
    if case_nature:
        cases = cases.filter(case_nature=case_nature)
    
    if status:
        cases = cases.filter(status=status)
    
    if priority:
        cases = cases.filter(priority=priority)
    
    if urgent == '1':
        cases = cases.filter(priority='urgent')
    
    # 按流程类型筛选
    if process_type:
        cases = cases.filter(processes__process_type=process_type).distinct()
    
    # 保全续封筛选
    if preservation == '1':
        cases = cases.filter(preservation_seals__isnull=False).distinct()
    
    if preservation_expiring == '1':
        today = timezone.now().date()
        cases = cases.filter(
            preservation_seals__status='active',
            preservation_seals__end_date__lte=today + timedelta(days=7),
            preservation_seals__end_date__gte=today
        ).distinct()
    
    # 排序
    sort_by = request.GET.get('sort', '-registration_date')
    cases = cases.order_by(sort_by)
    
    # 分页（每页20条）
    paginator = Paginator(cases, 20)
    page_number = request.GET.get('page', 1)
    try:
        page_obj = paginator.get_page(page_number)
    except:
        page_obj = paginator.get_page(1)
    
    # 统计信息（用于筛选显示）
    stats_by_type = cases.values('case_type').annotate(count=Count('id'))
    stats_by_status = cases.values('status').annotate(count=Count('id'))
    stats_by_nature = cases.values('case_nature').annotate(count=Count('id'))
    
    # 生成左侧菜单
    litigation_sidebar_nav = _build_litigation_sidebar_nav(permission_codes, request.path)
    
    context = _context(
        "案件列表",
        "📋",
        "管理所有诉讼案件",
        request=request
    )
    
    # 获取选项数据（用于弹窗表单）
    projects = Project.objects.filter(status__in=['in_progress', 'suspended', 'waiting_start']).order_by('-created_time')[:100]
    clients = Client.objects.filter(is_active=True).order_by('name')[:100]
    contracts = BusinessContract.objects.filter(status__in=['signed', 'executing']).order_by('-contract_date')[:100]
    
    # 获取案件负责人选项（有权限的用户或所有活跃用户）
    from backend.apps.system_management.models import User
    try:
        # 尝试获取有权限的用户
        case_managers = User.objects.filter(is_active=True).distinct().order_by('first_name', 'last_name', 'username')[:50]
    except:
        # 如果查询失败，使用所有活跃用户
        case_managers = User.objects.filter(is_active=True).order_by('first_name', 'last_name', 'username')[:50]
    
    context.update({
        'cases': page_obj,
        'page': page_obj,  # 兼容模板中的变量名
        'search': search,
        'case_type': case_type,
        'case_nature': case_nature,
        'status': status,
        'status_filter': status,  # 兼容模板中的变量名
        'priority': priority,
        'priority_filter': priority,  # 兼容模板中的变量名
        'process_type': process_type,
        'preservation': preservation,
        'preservation_expiring': preservation_expiring,
        'urgent': urgent,
        'tab': tab,
        'sort': sort_by,
        'stats_by_type': stats_by_type,
        'stats_by_status': stats_by_status,
        'stats_by_nature': stats_by_nature,
        'projects': projects,
        'clients': clients,
        'contracts': contracts,
        'case_managers': case_managers,
        'total_count': total_count,
        'pending_filing_count': pending_filing_count,
        'filed_count': filed_count,
        'trial_count': trial_count,
        'judged_count': judged_count,
        'executing_count': executing_count,
        'closed_count': closed_count,
        'litigation_sidebar_nav': litigation_sidebar_nav,
        'module_sidebar_nav': litigation_sidebar_nav,  # 兼容模板中的变量名
        'sidebar_title': '诉讼管理',  # 侧边栏标题
        'sidebar_subtitle': 'Litigation Management',  # 侧边栏副标题
        'case_type_choices': LitigationCase.CASE_TYPE_CHOICES,
        'case_nature_choices': LitigationCase.CASE_NATURE_CHOICES,
        'status_choices': LitigationCase.STATUS_CHOICES,
        'priority_choices': LitigationCase.PRIORITY_CHOICES,
    })
    
    return render(request, 'litigation_management/case_list.html', context)


@login_required
def case_create(request):
    """创建案件页面"""
    permission_codes = get_user_permission_codes(request.user)
    
    # 检查权限
    if not _permission_granted('litigation_management.case.create', permission_codes):
        messages.error(request, '您没有权限创建诉讼案件')
        return redirect('litigation_pages:case_list')
    
    if request.method == 'POST':
        form = LitigationCaseForm(request.POST)
        if form.is_valid():
            try:
                case = form.save(commit=False)
                case.registered_by = request.user
                if hasattr(request.user, 'department'):
                    case.registered_department = request.user.department
                case.save()
                logger.info(f'用户 {request.user.username} 创建了案件 {case.case_number}')
                
                # 检查是否需要审批
                try:
                    approval_instance = LitigationApprovalService.submit_case_for_approval(
                        case=case,
                        applicant=request.user,
                        comment=f'案件登记：{case.case_number} - {case.case_name}'
                    )
                    
                    if approval_instance:
                        messages.success(request, f'案件创建成功！案件编号：{case.case_number}。已提交审批，审批实例：{approval_instance.instance_number}')
                    else:
                        messages.success(request, f'案件创建成功！案件编号：{case.case_number}')
                except Exception as approval_error:
                    logger.warning(f'提交案件审批失败: {str(approval_error)}')
                    messages.success(request, f'案件创建成功！案件编号：{case.case_number}（审批流程未配置）')
                
                return redirect('litigation_pages:case_detail', case_id=case.id)
            except Exception as e:
                logger.error(f'创建案件失败: {str(e)}', exc_info=True)
                messages.error(request, f'案件创建失败：{str(e)}')
        else:
            logger.warning(f'案件表单验证失败: {form.errors}')
            messages.error(request, '表单验证失败，请检查输入信息')
    else:
        form = LitigationCaseForm()
    
    # 获取选项数据
    projects = Project.objects.filter(status__in=['in_progress', 'suspended', 'waiting_start']).order_by('-created_time')[:100]
    clients = Client.objects.filter(is_active=True).order_by('name')[:100]
    contracts = BusinessContract.objects.filter(status__in=['signed', 'executing']).order_by('-contract_date')[:100]
    
    context = _context(
        "创建案件",
        "➕",
        "登记新的诉讼案件",
        request=request
    )
    
    context.update({
        'form': form,
        'projects': projects,
        'clients': clients,
        'contracts': contracts,
    })
    
    # 如果是AJAX请求（弹窗提交），返回JSON响应
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        from django.http import JsonResponse
        if form.is_valid():
            try:
                case = form.save(commit=False)
                case.registered_by = request.user
                if hasattr(request.user, 'department'):
                    case.registered_department = request.user.department
                case.save()
                logger.info(f'用户 {request.user.username} 创建了案件 {case.case_number}')
                
                # 检查是否需要审批
                try:
                    approval_instance = LitigationApprovalService.submit_case_for_approval(
                        case=case,
                        applicant=request.user,
                        comment=f'案件登记：{case.case_number} - {case.case_name}'
                    )
                    
                    if approval_instance:
                        return JsonResponse({
                            'success': True,
                            'message': f'案件创建成功！案件编号：{case.case_number}。已提交审批，审批实例：{approval_instance.instance_number}',
                            'redirect_url': reverse('litigation_pages:case_detail', args=[case.id])
                        })
                    else:
                        return JsonResponse({
                            'success': True,
                            'message': f'案件创建成功！案件编号：{case.case_number}',
                            'redirect_url': reverse('litigation_pages:case_detail', args=[case.id])
                        })
                except Exception as approval_error:
                    logger.warning(f'提交案件审批失败: {str(approval_error)}')
                    return JsonResponse({
                        'success': True,
                        'message': f'案件创建成功！案件编号：{case.case_number}（审批流程未配置）',
                        'redirect_url': reverse('litigation_pages:case_detail', args=[case.id])
                    })
            except Exception as e:
                logger.error(f'创建案件失败: {str(e)}', exc_info=True)
                return JsonResponse({
                    'success': False,
                    'message': f'案件创建失败：{str(e)}',
                    'errors': form.errors
                }, status=400)
        else:
            return JsonResponse({
                'success': False,
                'message': '表单验证失败，请检查输入信息',
                'errors': form.errors
            }, status=400)
    
    return render(request, 'litigation_management/case_form.html', context)


@login_required
def case_detail(request, case_id):
    """案件详情页面"""
    permission_codes = get_user_permission_codes(request.user)
    
    # 检查权限
    if not _permission_granted('litigation_management.case.view', permission_codes):
        messages.error(request, '您没有权限查看此案件')
        return redirect('litigation_pages:case_list')
    
    case = get_object_or_404(
        LitigationCase.objects.select_related(
            'project', 'client', 'contract', 'case_manager',
            'registered_by', 'registered_department'
        ),
        id=case_id
    )
    
    # 权限检查：普通用户只能查看自己负责的案件
    if not _permission_granted('litigation_management.case.view_all', permission_codes):
        if case.case_manager != request.user and case.registered_by != request.user:
            messages.error(request, '您没有权限查看此案件')
            return redirect('litigation_pages:case_list')
    
    # 获取关联数据
    processes = case.processes.all().order_by('-process_date')
    documents = case.documents.all().order_by('-uploaded_at')
    expenses = case.expenses.all().order_by('-expense_date')
    persons = case.persons.all().order_by('person_type', 'name')
    timelines = case.timelines.all().order_by('timeline_date')
    preservation_seals = case.preservation_seals.all().order_by('-end_date')
    
    # 获取审批实例
    approval_instance = LitigationApprovalService.get_case_approval_instance(case)
    approval_status = LitigationApprovalService.check_approval_status(approval_instance)
    
    context = _context(
        f"案件详情 - {case.case_number}",
        "📋",
        case.case_name,
        request=request
    )
    
    context.update({
        'case': case,
        'processes': processes,
        'documents': documents,
        'expenses': expenses,
        'persons': persons,
        'timelines': timelines,
        'preservation_seals': preservation_seals,
        'approval_instance': approval_instance,
        'approval_status': approval_status,
    })
    
    return render(request, 'litigation_management/case_detail.html', context)


@login_required
def case_edit(request, case_id):
    """编辑案件页面"""
    permission_codes = get_user_permission_codes(request.user)
    
    # 检查权限
    if not _permission_granted('litigation_management.case.edit', permission_codes):
        messages.error(request, '您没有权限编辑此案件')
        return redirect('litigation_pages:case_detail', case_id=case_id)
    
    case = get_object_or_404(LitigationCase, id=case_id)
    
    # 权限检查：普通用户只能编辑自己负责的案件
    if not _permission_granted('litigation_management.case.view_all', permission_codes):
        if case.case_manager != request.user and case.registered_by != request.user:
            messages.error(request, '您没有权限编辑此案件')
            return redirect('litigation_pages:case_detail', case_id=case_id)
    
    if request.method == 'POST':
        form = LitigationCaseForm(request.POST, instance=case)
        if form.is_valid():
            try:
                form.save()
                logger.info(f'用户 {request.user.username} 更新了案件 {case.case_number}')
                messages.success(request, '案件信息更新成功！')
                return redirect('litigation_pages:case_detail', case_id=case.id)
            except Exception as e:
                logger.error(f'更新案件失败: {str(e)}', exc_info=True)
                messages.error(request, f'案件更新失败：{str(e)}')
        else:
            logger.warning(f'案件表单验证失败: {form.errors}')
            messages.error(request, '表单验证失败，请检查输入信息')
    else:
        form = LitigationCaseForm(instance=case)
    
    # 获取选项数据
    projects = Project.objects.filter(status__in=['in_progress', 'suspended', 'waiting_start']).order_by('-created_time')[:100]
    clients = Client.objects.filter(is_active=True).order_by('name')[:100]
    contracts = BusinessContract.objects.filter(status__in=['signed', 'executing']).order_by('-contract_date')[:100]
    
    context = _context(
        f"编辑案件 - {case.case_number}",
        "✏️",
        case.case_name,
        request=request
    )
    
    context.update({
        'case': case,
        'form': form,
        'projects': projects,
        'clients': clients,
        'contracts': contracts,
    })
    
    return render(request, 'litigation_management/case_form.html', context)


@login_required
def case_delete(request, case_id):
    """删除案件"""
    permission_codes = get_user_permission_codes(request.user)
    
    # 检查权限
    if not _permission_granted('litigation_management.case.delete', permission_codes):
        messages.error(request, '您没有权限删除此案件')
        return redirect('litigation_pages:case_detail', case_id=case_id)
    
    case = get_object_or_404(LitigationCase, id=case_id)
    
    if request.method == 'POST':
        try:
            case_number = case.case_number
            case.delete()
            logger.info(f'用户 {request.user.username} 删除了案件 {case_number}')
            messages.success(request, f'案件 {case_number} 已删除')
            return redirect('litigation_pages:case_list')
        except Exception as e:
            logger.error(f'删除案件失败: {str(e)}', exc_info=True)
            messages.error(request, f'删除案件失败：{str(e)}')
            return redirect('litigation_pages:case_detail', case_id=case_id)
    
    context = _context(
        f"删除案件 - {case.case_number}",
        "🗑️",
        f"确认删除案件：{case.case_name}",
        request=request
    )
    
    context.update({
        'case': case,
    })
    
    return render(request, 'litigation_management/case_delete.html', context)


# ==================== 诉讼流程管理 ====================

@login_required
def process_list(request, case_id):
    """流程列表页面"""
    permission_codes = get_user_permission_codes(request.user)
    
    if not _permission_granted('litigation_management.process.manage', permission_codes):
        messages.error(request, '您没有权限查看诉讼流程')
        return redirect('litigation_pages:case_detail', case_id=case_id)
    
    case = get_object_or_404(LitigationCase, id=case_id)
    processes = case.processes.all().order_by('-process_date')
    
    context = _context(
        f"诉讼流程 - {case.case_number}",
        "⚖️",
        case.case_name,
        request=request
    )
    
    context.update({
        'case': case,
        'processes': processes,
    })
    
    return render(request, 'litigation_management/process_list.html', context)


@login_required
def process_create(request, case_id):
    """创建流程记录"""
    permission_codes = get_user_permission_codes(request.user)
    
    if not _permission_granted('litigation_management.process.manage', permission_codes):
        messages.error(request, '您没有权限创建流程记录')
        return redirect('litigation_pages:case_detail', case_id=case_id)
    
    case = get_object_or_404(LitigationCase, id=case_id)
    
    if request.method == 'POST':
        form = LitigationProcessForm(request.POST)
        if form.is_valid():
            try:
                process = form.save(commit=False)
                process.case = case
                process.created_by = request.user
                process.save()
                logger.info(f'用户 {request.user.username} 创建了流程记录 {process.get_process_type_display()} (案件: {case.case_number})')
                messages.success(request, '流程记录创建成功！')
                return redirect('litigation_pages:process_detail', process_id=process.id)
            except Exception as e:
                logger.error(f'创建流程记录失败: {str(e)}', exc_info=True)
                messages.error(request, f'流程记录创建失败：{str(e)}')
        else:
            logger.warning(f'流程表单验证失败: {form.errors}')
            messages.error(request, '表单验证失败，请检查输入信息')
    else:
        form = LitigationProcessForm(initial={'case': case})
    
    context = _context(
        f"创建流程记录 - {case.case_number}",
        "➕",
        case.case_name,
        request=request
    )
    
    context.update({
        'case': case,
        'form': form,
    })
    
    return render(request, 'litigation_management/process_form.html', context)


@login_required
def process_detail(request, process_id):
    """流程详情页面"""
    permission_codes = get_user_permission_codes(request.user)
    
    if not _permission_granted('litigation_management.process.manage', permission_codes):
        messages.error(request, '您没有权限查看流程记录')
        return redirect('litigation_pages:case_list')
    
    process = get_object_or_404(
        LitigationProcess.objects.select_related('case', 'created_by'),
        id=process_id
    )
    
    context = _context(
        f"流程详情 - {process.get_process_type_display()}",
        "⚖️",
        process.case.case_name,
        request=request
    )
    
    context.update({
        'process': process,
        'case': process.case,
    })
    
    return render(request, 'litigation_management/process_detail.html', context)


@login_required
def process_edit(request, process_id):
    """编辑流程记录"""
    permission_codes = get_user_permission_codes(request.user)
    
    if not _permission_granted('litigation_management.process.manage', permission_codes):
        messages.error(request, '您没有权限编辑流程记录')
        return redirect('litigation_pages:process_detail', process_id=process_id)
    
    process = get_object_or_404(LitigationProcess, id=process_id)
    
    if request.method == 'POST':
        form = LitigationProcessForm(request.POST, instance=process)
        if form.is_valid():
            try:
                form.save()
                logger.info(f'用户 {request.user.username} 更新了流程记录 {process.get_process_type_display()} (案件: {process.case.case_number})')
                messages.success(request, '流程记录更新成功！')
                return redirect('litigation_pages:process_detail', process_id=process.id)
            except Exception as e:
                logger.error(f'更新流程记录失败: {str(e)}', exc_info=True)
                messages.error(request, f'流程记录更新失败：{str(e)}')
        else:
            logger.warning(f'流程表单验证失败: {form.errors}')
            messages.error(request, '表单验证失败，请检查输入信息')
    else:
        form = LitigationProcessForm(instance=process)
    
    context = _context(
        f"编辑流程记录 - {process.get_process_type_display()}",
        "✏️",
        process.case.case_name,
        request=request
    )
    
    context.update({
        'process': process,
        'case': process.case,
        'form': form,
    })
    
    return render(request, 'litigation_management/process_form.html', context)


# ==================== 保全续封管理 ====================

@login_required
def preservation_list(request, case_id):
    """保全续封列表"""
    permission_codes = get_user_permission_codes(request.user)
    
    if not _permission_granted('litigation_management.process.manage', permission_codes):
        messages.error(request, '您没有权限查看保全续封')
        return redirect('litigation_pages:case_detail', case_id=case_id)
    
    case = get_object_or_404(LitigationCase, id=case_id)
    seals = case.preservation_seals.all().order_by('-end_date')
    
    # 检查即将到期的保全
    today = timezone.now().date()
    expiring_soon = seals.filter(end_date__lte=today + timedelta(days=7), status='active')
    
    context = _context(
        f"保全续封 - {case.case_number}",
        "🔒",
        case.case_name,
        request=request
    )
    
    context.update({
        'case': case,
        'seals': seals,
        'expiring_soon': expiring_soon,
        'today': today,
    })
    
    return render(request, 'litigation_management/preservation_list.html', context)


@login_required
def preservation_create(request, case_id):
    """创建保全续封"""
    permission_codes = get_user_permission_codes(request.user)
    
    if not _permission_granted('litigation_management.process.manage', permission_codes):
        messages.error(request, '您没有权限创建保全续封')
        return redirect('litigation_pages:case_detail', case_id=case_id)
    
    case = get_object_or_404(LitigationCase, id=case_id)
    
    if request.method == 'POST':
        form = PreservationSealForm(request.POST)
        if form.is_valid():
            try:
                seal = form.save(commit=False)
                seal.case = case
                seal.created_by = request.user
                seal.save()
                logger.info(f'用户 {request.user.username} 创建了保全续封 {seal.get_seal_type_display()} (案件: {case.case_number})')
                messages.success(request, '保全续封创建成功！')
                return redirect('litigation_pages:preservation_detail', seal_id=seal.id)
            except Exception as e:
                logger.error(f'创建保全续封失败: {str(e)}', exc_info=True)
                messages.error(request, f'保全续封创建失败：{str(e)}')
        else:
            logger.warning(f'保全续封表单验证失败: {form.errors}')
            messages.error(request, '表单验证失败，请检查输入信息')
    else:
        form = PreservationSealForm(initial={'case': case})
    
    context = _context(
        f"创建保全续封 - {case.case_number}",
        "➕",
        case.case_name,
        request=request
    )
    
    context.update({
        'case': case,
        'form': form,
    })
    
    return render(request, 'litigation_management/preservation_form.html', context)


@login_required
def preservation_detail(request, seal_id):
    """保全续封详情"""
    permission_codes = get_user_permission_codes(request.user)
    
    if not _permission_granted('litigation_management.process.manage', permission_codes):
        messages.error(request, '您没有权限查看保全续封')
        return redirect('litigation_pages:case_list')
    
    seal = get_object_or_404(
        PreservationSeal.objects.select_related('case', 'created_by'),
        id=seal_id
    )
    
    # 检查是否即将到期
    today = timezone.now().date()
    days_until_expiry = (seal.end_date - today).days if seal.end_date > today else 0
    
    context = _context(
        f"保全续封详情 - {seal.get_seal_type_display()}",
        "🔒",
        seal.case.case_name,
        request=request
    )
    
    context.update({
        'seal': seal,
        'case': seal.case,
        'days_until_expiry': days_until_expiry,
        'is_expiring_soon': days_until_expiry <= 7 and seal.status == 'active',
    })
    
    return render(request, 'litigation_management/preservation_detail.html', context)


@login_required
def preservation_edit(request, seal_id):
    """编辑保全续封"""
    permission_codes = get_user_permission_codes(request.user)
    
    if not _permission_granted('litigation_management.process.manage', permission_codes):
        messages.error(request, '您没有权限编辑保全续封')
        return redirect('litigation_pages:preservation_detail', seal_id=seal_id)
    
    seal = get_object_or_404(PreservationSeal, id=seal_id)
    
    if request.method == 'POST':
        form = PreservationSealForm(request.POST, instance=seal)
        if form.is_valid():
            try:
                form.save()
                logger.info(f'用户 {request.user.username} 更新了保全续封 {seal.get_seal_type_display()} (案件: {seal.case.case_number})')
                messages.success(request, '保全续封更新成功！')
                return redirect('litigation_pages:preservation_detail', seal_id=seal.id)
            except Exception as e:
                logger.error(f'更新保全续封失败: {str(e)}', exc_info=True)
                messages.error(request, f'保全续封更新失败：{str(e)}')
        else:
            logger.warning(f'保全续封表单验证失败: {form.errors}')
            messages.error(request, '表单验证失败，请检查输入信息')
    else:
        form = PreservationSealForm(instance=seal)
    
    context = _context(
        f"编辑保全续封 - {seal.get_seal_type_display()}",
        "✏️",
        seal.case.case_name,
        request=request
    )
    
    context.update({
        'seal': seal,
        'case': seal.case,
        'form': form,
    })
    
    return render(request, 'litigation_management/preservation_form.html', context)


@login_required
def preservation_renew(request, seal_id):
    """续封申请"""
    permission_codes = get_user_permission_codes(request.user)
    
    if not _permission_granted('litigation_management.process.manage', permission_codes):
        messages.error(request, '您没有权限申请续封')
        return redirect('litigation_pages:preservation_detail', seal_id=seal_id)
    
    seal = get_object_or_404(PreservationSeal, id=seal_id)
    
    if request.method == 'POST':
        try:
            renewal_date_str = request.POST.get('renewal_date')
            if not renewal_date_str:
                messages.error(request, '请选择续封后的到期日期')
            else:
                from datetime import datetime
                renewal_date = datetime.strptime(renewal_date_str, '%Y-%m-%d').date()
                
                # 检查续封日期是否晚于当前到期日期
                if renewal_date <= seal.end_date:
                    messages.error(request, '续封后的到期日期必须晚于当前到期日期')
                else:
                    seal.renewal_applied = True
                    seal.renewal_date = renewal_date
                    # 续封申请提交后，状态仍保持active，等待审批
                    seal.save()
                    logger.info(f'用户 {request.user.username} 提交了续封申请 (保全: {seal.get_seal_type_display()}, 案件: {seal.case.case_number})')
                    messages.success(request, '续封申请提交成功！请等待审批。')
                    return redirect('litigation_pages:preservation_detail', seal_id=seal.id)
        except ValueError:
            logger.warning(f'续封申请日期格式错误: {request.POST.get("renewal_date")}')
            messages.error(request, '日期格式错误')
        except Exception as e:
            logger.error(f'续封申请失败: {str(e)}', exc_info=True)
            messages.error(request, f'续封申请失败：{str(e)}')
    
    context = _context(
        f"续封申请 - {seal.get_seal_type_display()}",
        "🔄",
        seal.case.case_name,
        request=request
    )
    
    context.update({
        'seal': seal,
        'case': seal.case,
    })
    
    return render(request, 'litigation_management/preservation_renew.html', context)


# ==================== 文档管理 ====================

@login_required
def document_list(request, case_id):
    """文档列表"""
    permission_codes = get_user_permission_codes(request.user)
    
    if not _permission_granted('litigation_management.document.view', permission_codes):
        messages.error(request, '您没有权限查看文档')
        return redirect('litigation_pages:case_detail', case_id=case_id)
    
    case = get_object_or_404(LitigationCase, id=case_id)
    documents = case.documents.all().order_by('-uploaded_at')
    
    # 按类型筛选
    doc_type = request.GET.get('type', '')
    if doc_type:
        documents = documents.filter(document_type=doc_type)
    
    context = _context(
        f"诉讼文档 - {case.case_number}",
        "📄",
        case.case_name,
        request=request
    )
    
    context.update({
        'case': case,
        'documents': documents,
        'doc_type': doc_type,
    })
    
    return render(request, 'litigation_management/document_list.html', context)


@login_required
def document_upload(request, case_id):
    """上传文档"""
    permission_codes = get_user_permission_codes(request.user)
    
    if not _permission_granted('litigation_management.document.manage', permission_codes):
        messages.error(request, '您没有权限上传文档')
        return redirect('litigation_pages:case_detail', case_id=case_id)
    
    case = get_object_or_404(LitigationCase, id=case_id)
    
    if request.method == 'POST':
        form = LitigationDocumentForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                document = form.save(commit=False)
                document.case = case
                document.uploaded_by = request.user
                document.save()
                logger.info(f'用户 {request.user.username} 上传了文档 {document.document_name} (案件: {case.case_number})')
                messages.success(request, '文档上传成功！')
                return redirect('litigation_pages:document_detail', document_id=document.id)
            except Exception as e:
                logger.error(f'上传文档失败: {str(e)}', exc_info=True)
                messages.error(request, f'文档上传失败：{str(e)}')
        else:
            logger.warning(f'文档表单验证失败: {form.errors}')
            messages.error(request, '表单验证失败，请检查输入信息')
    else:
        form = LitigationDocumentForm(initial={'case': case})
    
    processes = case.processes.all().order_by('-process_date')
    
    context = _context(
        f"上传文档 - {case.case_number}",
        "📤",
        case.case_name,
        request=request
    )
    
    context.update({
        'case': case,
        'form': form,
        'processes': processes,
    })
    
    return render(request, 'litigation_management/document_upload.html', context)


@login_required
def document_detail(request, document_id):
    """文档详情"""
    permission_codes = get_user_permission_codes(request.user)
    
    if not _permission_granted('litigation_management.document.view', permission_codes):
        messages.error(request, '您没有权限查看文档')
        return redirect('litigation_pages:case_list')
    
    document = get_object_or_404(
        LitigationDocument.objects.select_related('case', 'process', 'uploaded_by'),
        id=document_id
    )
    
    context = _context(
        f"文档详情 - {document.document_name}",
        "📄",
        document.case.case_name,
        request=request
    )
    
    context.update({
        'document': document,
        'case': document.case,
    })
    
    return render(request, 'litigation_management/document_detail.html', context)


@login_required
def document_delete(request, document_id):
    """删除文档"""
    permission_codes = get_user_permission_codes(request.user)
    
    if not _permission_granted('litigation_management.document.manage', permission_codes):
        messages.error(request, '您没有权限删除文档')
        return redirect('litigation_pages:document_detail', document_id=document_id)
    
    document = get_object_or_404(LitigationDocument, id=document_id)
    case_id = document.case.id
    
    if request.method == 'POST':
        try:
            document_name = document.document_name
            case_number = document.case.case_number
            document.delete()
            logger.info(f'用户 {request.user.username} 删除了文档 {document_name} (案件: {case_number})')
            messages.success(request, f'文档 {document_name} 已删除')
            return redirect('litigation_pages:document_list', case_id=case_id)
        except Exception as e:
            logger.error(f'删除文档失败: {str(e)}', exc_info=True)
            messages.error(request, f'删除文档失败：{str(e)}')
            return redirect('litigation_pages:document_detail', document_id=document_id)
    
    context = _context(
        f"删除文档 - {document.document_name}",
        "🗑️",
        f"确认删除文档：{document.document_name}",
        request=request
    )
    
    context.update({
        'document': document,
        'case': document.case,
    })
    
    return render(request, 'litigation_management/document_delete.html', context)


# ==================== 费用管理 ====================

@login_required
def expense_list(request, case_id):
    """费用列表"""
    permission_codes = get_user_permission_codes(request.user)
    
    if not _permission_granted('litigation_management.expense.view', permission_codes):
        messages.error(request, '您没有权限查看费用')
        return redirect('litigation_pages:case_detail', case_id=case_id)
    
    case = get_object_or_404(LitigationCase, id=case_id)
    expenses = case.expenses.all().order_by('-expense_date')
    
    # 按状态筛选
    status_filter = request.GET.get('status', '')
    if status_filter:
        expenses = expenses.filter(payment_status=status_filter)
    
    # 统计
    total_amount = expenses.aggregate(Sum('amount'))['amount__sum'] or Decimal('0')
    paid_amount = expenses.filter(payment_status='paid').aggregate(Sum('amount'))['amount__sum'] or Decimal('0')
    pending_amount = total_amount - paid_amount
    
    context = _context(
        f"诉讼费用 - {case.case_number}",
        "💰",
        case.case_name,
        request=request
    )
    
    context.update({
        'case': case,
        'expenses': expenses,
        'status_filter': status_filter,
        'total_amount': total_amount,
        'paid_amount': paid_amount,
        'pending_amount': pending_amount,
    })
    
    return render(request, 'litigation_management/expense_list.html', context)


@login_required
def expense_create(request, case_id):
    """创建费用记录"""
    permission_codes = get_user_permission_codes(request.user)
    
    if not _permission_granted('litigation_management.expense.manage', permission_codes):
        messages.error(request, '您没有权限创建费用记录')
        return redirect('litigation_pages:case_detail', case_id=case_id)
    
    case = get_object_or_404(LitigationCase, id=case_id)
    
    if request.method == 'POST':
        form = LitigationExpenseForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                expense = form.save(commit=False)
                expense.case = case
                expense.created_by = request.user
                expense.save()
                logger.info(f'用户 {request.user.username} 创建了费用记录 {expense.expense_name} ¥{expense.amount} (案件: {case.case_number})')
                messages.success(request, '费用记录创建成功！')
                return redirect('litigation_pages:expense_detail', expense_id=expense.id)
            except Exception as e:
                logger.error(f'创建费用记录失败: {str(e)}', exc_info=True)
                messages.error(request, f'费用记录创建失败：{str(e)}')
        else:
            logger.warning(f'费用表单验证失败: {form.errors}')
            messages.error(request, '表单验证失败，请检查输入信息')
    else:
        form = LitigationExpenseForm(initial={'case': case})
    
    projects = Project.objects.filter(status__in=['in_progress', 'suspended', 'waiting_start']).order_by('-created_time')[:100]
    
    context = _context(
        f"创建费用记录 - {case.case_number}",
        "➕",
        case.case_name,
        request=request
    )
    
    context.update({
        'case': case,
        'form': form,
        'projects': projects,
    })
    
    return render(request, 'litigation_management/expense_form.html', context)


@login_required
def expense_detail(request, expense_id):
    """费用详情"""
    permission_codes = get_user_permission_codes(request.user)
    
    if not _permission_granted('litigation_management.expense.view', permission_codes):
        messages.error(request, '您没有权限查看费用')
        return redirect('litigation_pages:case_list')
    
    expense = get_object_or_404(
        LitigationExpense.objects.select_related('case', 'project', 'created_by'),
        id=expense_id
    )
    
    # 获取审批实例
    approval_instance = LitigationApprovalService.get_expense_approval_instance(expense)
    approval_status = LitigationApprovalService.check_approval_status(approval_instance)
    
    context = _context(
        f"费用详情 - {expense.expense_name}",
        "💰",
        expense.case.case_name,
        request=request
    )
    
    context.update({
        'expense': expense,
        'case': expense.case,
        'approval_instance': approval_instance,
        'approval_status': approval_status,
    })
    
    return render(request, 'litigation_management/expense_detail.html', context)


@login_required
def expense_edit(request, expense_id):
    """编辑费用记录"""
    permission_codes = get_user_permission_codes(request.user)
    
    if not _permission_granted('litigation_management.expense.manage', permission_codes):
        messages.error(request, '您没有权限编辑费用记录')
        return redirect('litigation_pages:expense_detail', expense_id=expense_id)
    
    expense = get_object_or_404(LitigationExpense, id=expense_id)
    
    if request.method == 'POST':
        form = LitigationExpenseForm(request.POST, request.FILES, instance=expense)
        if form.is_valid():
            try:
                form.save()
                logger.info(f'用户 {request.user.username} 更新了费用记录 {expense.expense_name} (案件: {expense.case.case_number})')
                messages.success(request, '费用记录更新成功！')
                return redirect('litigation_pages:expense_detail', expense_id=expense.id)
            except Exception as e:
                logger.error(f'更新费用记录失败: {str(e)}', exc_info=True)
                messages.error(request, f'费用记录更新失败：{str(e)}')
        else:
            logger.warning(f'费用表单验证失败: {form.errors}')
            messages.error(request, '表单验证失败，请检查输入信息')
    else:
        form = LitigationExpenseForm(instance=expense)
    
    projects = Project.objects.filter(status__in=['in_progress', 'suspended', 'waiting_start']).order_by('-created_time')[:100]
    
    context = _context(
        f"编辑费用记录 - {expense.expense_name}",
        "✏️",
        expense.case.case_name,
        request=request
    )
    
    context.update({
        'expense': expense,
        'case': expense.case,
        'form': form,
        'projects': projects,
    })
    
    return render(request, 'litigation_management/expense_form.html', context)


@login_required
def expense_reimburse(request, expense_id):
    """费用报销"""
    permission_codes = get_user_permission_codes(request.user)
    
    if not _permission_granted('litigation_management.expense.manage', permission_codes):
        messages.error(request, '您没有权限申请费用报销')
        return redirect('litigation_pages:expense_detail', expense_id=expense_id)
    
    expense = get_object_or_404(LitigationExpense, id=expense_id)
    
    if request.method == 'POST':
        try:
            expense.reimbursement_applied = True
            expense.reimbursement_status = 'pending'
            expense.save()
            logger.info(f'用户 {request.user.username} 提交了费用报销申请 {expense.expense_name} ¥{expense.amount} (案件: {expense.case.case_number})')
            messages.success(request, '费用报销申请提交成功！')
            return redirect('litigation_pages:expense_detail', expense_id=expense.id)
        except Exception as e:
            logger.error(f'费用报销申请失败: {str(e)}', exc_info=True)
            messages.error(request, f'费用报销申请失败：{str(e)}')
    
    context = _context(
        f"费用报销 - {expense.expense_name}",
        "💳",
        expense.case.case_name,
        request=request
    )
    
    context.update({
        'expense': expense,
        'case': expense.case,
    })
    
    return render(request, 'litigation_management/expense_reimburse.html', context)


# ==================== 人员管理 ====================

@login_required
def person_list(request, case_id):
    """人员列表"""
    permission_codes = get_user_permission_codes(request.user)
    
    if not _permission_granted('litigation_management.person.manage', permission_codes):
        messages.error(request, '您没有权限查看人员')
        return redirect('litigation_pages:case_detail', case_id=case_id)
    
    case = get_object_or_404(LitigationCase, id=case_id)
    persons = case.persons.all().order_by('person_type', 'name')
    
    # 按类型筛选
    person_type = request.GET.get('type', '')
    if person_type:
        persons = persons.filter(person_type=person_type)
    
    context = _context(
        f"诉讼人员 - {case.case_number}",
        "👥",
        case.case_name,
        request=request
    )
    
    context.update({
        'case': case,
        'persons': persons,
        'person_type': person_type,
    })
    
    return render(request, 'litigation_management/person_list.html', context)


@login_required
def person_create(request, case_id):
    """创建人员信息"""
    permission_codes = get_user_permission_codes(request.user)
    
    if not _permission_granted('litigation_management.person.manage', permission_codes):
        messages.error(request, '您没有权限创建人员信息')
        return redirect('litigation_pages:case_detail', case_id=case_id)
    
    case = get_object_or_404(LitigationCase, id=case_id)
    
    if request.method == 'POST':
        form = LitigationPersonForm(request.POST)
        if form.is_valid():
            try:
                person = form.save(commit=False)
                person.case = case
                person.save()
                logger.info(f'用户 {request.user.username} 创建了人员信息 {person.name} ({person.get_person_type_display()}) (案件: {case.case_number})')
                messages.success(request, '人员信息创建成功！')
                return redirect('litigation_pages:person_detail', person_id=person.id)
            except Exception as e:
                logger.error(f'创建人员信息失败: {str(e)}', exc_info=True)
                messages.error(request, f'人员信息创建失败：{str(e)}')
        else:
            logger.warning(f'人员表单验证失败: {form.errors}')
            messages.error(request, '表单验证失败，请检查输入信息')
    else:
        form = LitigationPersonForm(initial={'case': case})
    
    context = _context(
        f"创建人员信息 - {case.case_number}",
        "➕",
        case.case_name,
        request=request
    )
    
    context.update({
        'case': case,
        'form': form,
    })
    
    return render(request, 'litigation_management/person_form.html', context)


@login_required
def person_detail(request, person_id):
    """人员详情"""
    permission_codes = get_user_permission_codes(request.user)
    
    if not _permission_granted('litigation_management.person.manage', permission_codes):
        messages.error(request, '您没有权限查看人员信息')
        return redirect('litigation_pages:case_list')
    
    person = get_object_or_404(
        LitigationPerson.objects.select_related('case'),
        id=person_id
    )
    
    context = _context(
        f"人员详情 - {person.name}",
        "👥",
        person.case.case_name,
        request=request
    )
    
    context.update({
        'person': person,
        'case': person.case,
    })
    
    return render(request, 'litigation_management/person_detail.html', context)


@login_required
def person_edit(request, person_id):
    """编辑人员信息"""
    permission_codes = get_user_permission_codes(request.user)
    
    if not _permission_granted('litigation_management.person.manage', permission_codes):
        messages.error(request, '您没有权限编辑人员信息')
        return redirect('litigation_pages:person_detail', person_id=person_id)
    
    person = get_object_or_404(LitigationPerson, id=person_id)
    
    if request.method == 'POST':
        form = LitigationPersonForm(request.POST, instance=person)
        if form.is_valid():
            try:
                form.save()
                logger.info(f'用户 {request.user.username} 更新了人员信息 {person.name} (案件: {person.case.case_number})')
                messages.success(request, '人员信息更新成功！')
                return redirect('litigation_pages:person_detail', person_id=person.id)
            except Exception as e:
                logger.error(f'更新人员信息失败: {str(e)}', exc_info=True)
                messages.error(request, f'人员信息更新失败：{str(e)}')
        else:
            logger.warning(f'人员表单验证失败: {form.errors}')
            messages.error(request, '表单验证失败，请检查输入信息')
    else:
        form = LitigationPersonForm(instance=person)
    
    context = _context(
        f"编辑人员信息 - {person.name}",
        "✏️",
        person.case.case_name,
        request=request
    )
    
    context.update({
        'person': person,
        'case': person.case,
        'form': form,
    })
    
    return render(request, 'litigation_management/person_form.html', context)


# ==================== 时间管理 ====================

@login_required
def timeline_list(request, case_id):
    """时间节点列表"""
    permission_codes = get_user_permission_codes(request.user)
    
    if not _permission_granted('litigation_management.timeline.manage', permission_codes):
        messages.error(request, '您没有权限查看时间节点')
        return redirect('litigation_pages:case_detail', case_id=case_id)
    
    case = get_object_or_404(LitigationCase, id=case_id)
    timelines = case.timelines.all().order_by('timeline_date')
    
    # 按类型筛选
    timeline_type = request.GET.get('type', '')
    if timeline_type:
        timelines = timelines.filter(timeline_type=timeline_type)
    
    # 按状态筛选
    status_filter = request.GET.get('status', '')
    if status_filter:
        timelines = timelines.filter(status=status_filter)
    
    # 检查提醒
    reminder_filter = request.GET.get('reminder', '')
    if reminder_filter == '1':
        timelines = timelines.filter(reminder_enabled=True)
    
    context = _context(
        f"时间节点 - {case.case_number}",
        "📅",
        case.case_name,
        request=request
    )
    
    today = timezone.now().date()
    warning_date = today + timedelta(days=7)  # 7天后为警告日期
    
    context.update({
        'case': case,
        'timelines': timelines,
        'timeline_type': timeline_type,
        'status_filter': status_filter,
        'reminder_filter': reminder_filter,
        'today': today,
        'warning_date': warning_date,
    })
    
    return render(request, 'litigation_management/timeline_list.html', context)


@login_required
def timeline_create(request, case_id):
    """创建时间节点"""
    permission_codes = get_user_permission_codes(request.user)
    
    if not _permission_granted('litigation_management.timeline.manage', permission_codes):
        messages.error(request, '您没有权限创建时间节点')
        return redirect('litigation_pages:case_detail', case_id=case_id)
    
    case = get_object_or_404(LitigationCase, id=case_id)
    
    if request.method == 'POST':
        form = LitigationTimelineForm(request.POST)
        if form.is_valid():
            try:
                timeline = form.save(commit=False)
                timeline.case = case
                timeline.created_by = request.user
                timeline.save()
                logger.info(f'用户 {request.user.username} 创建了时间节点 {timeline.timeline_name} (案件: {case.case_number})')
                messages.success(request, '时间节点创建成功！')
                return redirect('litigation_pages:timeline_detail', timeline_id=timeline.id)
            except Exception as e:
                logger.error(f'创建时间节点失败: {str(e)}', exc_info=True)
                messages.error(request, f'时间节点创建失败：{str(e)}')
        else:
            logger.warning(f'时间节点表单验证失败: {form.errors}')
            messages.error(request, '表单验证失败，请检查输入信息')
    else:
        form = LitigationTimelineForm(initial={'case': case})
    
    context = _context(
        f"创建时间节点 - {case.case_number}",
        "➕",
        case.case_name,
        request=request
    )
    
    context.update({
        'case': case,
        'form': form,
    })
    
    return render(request, 'litigation_management/timeline_form.html', context)


@login_required
def timeline_detail(request, timeline_id):
    """时间节点详情"""
    permission_codes = get_user_permission_codes(request.user)
    
    if not _permission_granted('litigation_management.timeline.manage', permission_codes):
        messages.error(request, '您没有权限查看时间节点')
        return redirect('litigation_pages:case_list')
    
    timeline = get_object_or_404(
        LitigationTimeline.objects.select_related('case', 'confirmed_by', 'created_by'),
        id=timeline_id
    )
    
    context = _context(
        f"时间节点详情 - {timeline.timeline_name}",
        "📅",
        timeline.case.case_name,
        request=request
    )
    
    context.update({
        'timeline': timeline,
        'case': timeline.case,
    })
    
    return render(request, 'litigation_management/timeline_detail.html', context)


@login_required
def timeline_edit(request, timeline_id):
    """编辑时间节点"""
    permission_codes = get_user_permission_codes(request.user)
    
    if not _permission_granted('litigation_management.timeline.manage', permission_codes):
        messages.error(request, '您没有权限编辑时间节点')
        return redirect('litigation_pages:timeline_detail', timeline_id=timeline_id)
    
    timeline = get_object_or_404(LitigationTimeline, id=timeline_id)
    
    if request.method == 'POST':
        form = LitigationTimelineForm(request.POST, instance=timeline)
        if form.is_valid():
            try:
                form.save()
                logger.info(f'用户 {request.user.username} 更新了时间节点 {timeline.timeline_name} (案件: {timeline.case.case_number})')
                messages.success(request, '时间节点更新成功！')
                return redirect('litigation_pages:timeline_detail', timeline_id=timeline.id)
            except Exception as e:
                logger.error(f'更新时间节点失败: {str(e)}', exc_info=True)
                messages.error(request, f'时间节点更新失败：{str(e)}')
        else:
            logger.warning(f'时间节点表单验证失败: {form.errors}')
            messages.error(request, '表单验证失败，请检查输入信息')
    else:
        form = LitigationTimelineForm(instance=timeline)
    
    context = _context(
        f"编辑时间节点 - {timeline.timeline_name}",
        "✏️",
        timeline.case.case_name,
        request=request
    )
    
    context.update({
        'timeline': timeline,
        'case': timeline.case,
        'form': form,
    })
    
    return render(request, 'litigation_management/timeline_form.html', context)


@login_required
def timeline_confirm(request, timeline_id):
    """确认时间节点"""
    permission_codes = get_user_permission_codes(request.user)
    
    if not _permission_granted('litigation_management.timeline.manage', permission_codes):
        messages.error(request, '您没有权限确认时间节点')
        return redirect('litigation_pages:timeline_detail', timeline_id=timeline_id)
    
    timeline = get_object_or_404(LitigationTimeline, id=timeline_id)
    
    if request.method == 'POST':
        try:
            timeline.confirmed_by = request.user
            timeline.confirmed_at = timezone.now()
            timeline.status = 'completed'
            timeline.save()
            logger.info(f'用户 {request.user.username} 确认了时间节点 {timeline.timeline_name} (案件: {timeline.case.case_number})')
            messages.success(request, '时间节点确认成功！')
            return redirect('litigation_pages:timeline_detail', timeline_id=timeline.id)
        except Exception as e:
            logger.error(f'确认时间节点失败: {str(e)}', exc_info=True)
            messages.error(request, f'时间节点确认失败：{str(e)}')
    
    context = _context(
        f"确认时间节点 - {timeline.timeline_name}",
        "✅",
        timeline.case.case_name,
        request=request
    )
    
    context.update({
        'timeline': timeline,
        'case': timeline.case,
    })
    
    return render(request, 'litigation_management/timeline_confirm.html', context)


@login_required
def timeline_calendar(request):
    """时间节点日历视图"""
    permission_codes = get_user_permission_codes(request.user)
    
    if not _permission_granted('litigation_management.timeline.manage', permission_codes):
        messages.error(request, '您没有权限查看日历')
        return redirect('litigation_pages:case_list')
    
    # 获取筛选参数
    case_id = request.GET.get('case_id', '')
    timeline_type = request.GET.get('type', '')
    
    # 获取时间节点
    timelines = LitigationTimeline.objects.select_related('case').all()
    
    # 权限过滤
    if not _permission_granted('litigation_management.case.view_all', permission_codes):
        cases = LitigationCase.objects.filter(
            Q(case_manager=request.user) | Q(registered_by=request.user)
        )
        timelines = timelines.filter(case__in=cases)
    
    # 应用筛选
    if case_id:
        timelines = timelines.filter(case_id=case_id)
    
    if timeline_type:
        timelines = timelines.filter(timeline_type=timeline_type)
    
    # 按月份分组
    timelines_by_month = {}
    for timeline in timelines:
        month_key = timeline.timeline_date.strftime('%Y-%m')
        if month_key not in timelines_by_month:
            timelines_by_month[month_key] = []
        timelines_by_month[month_key].append(timeline)
    
    # 对每个月份的时间节点按日期排序
    for month_key in timelines_by_month:
        timelines_by_month[month_key].sort(key=lambda x: x.timeline_date)
    
    # 获取案件列表（用于筛选）
    cases = LitigationCase.objects.all()
    if not _permission_granted('litigation_management.case.view_all', permission_codes):
        cases = cases.filter(Q(case_manager=request.user) | Q(registered_by=request.user))
    
    context = _context(
        "时间节点日历",
        "📆",
        "查看所有时间节点的日历视图",
        request=request
    )
    
    today = timezone.now().date()
    warning_date = today + timedelta(days=7)
    
    context.update({
        'timelines_by_month': timelines_by_month,
        'cases': cases,
        'case_id': case_id,
        'timeline_type': timeline_type,
        'today': today,
        'warning_date': warning_date,
    })
    
    return render(request, 'litigation_management/timeline_calendar.html', context)


# ==================== 案件统计 ====================

@login_required
def case_statistics(request):
    """案件统计"""
    permission_codes = get_user_permission_codes(request.user)
    
    if not _permission_granted('litigation_management.statistics.view', permission_codes):
        messages.error(request, '您没有权限查看统计')
        return redirect('litigation_pages:case_list')
    
    # 获取筛选参数
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    # 获取案件列表
    cases = LitigationCase.objects.all()
    
    # 权限过滤
    if not _permission_granted('litigation_management.case.view_all', permission_codes):
        cases = cases.filter(Q(case_manager=request.user) | Q(registered_by=request.user))
    
    # 时间筛选
    if date_from:
        cases = cases.filter(registration_date__gte=date_from)
    if date_to:
        cases = cases.filter(registration_date__lte=date_to)
    
    # 统计
    total_cases = cases.count()
    stats_by_type = cases.values('case_type').annotate(count=Count('id'))
    stats_by_status = cases.values('status').annotate(count=Count('id'))
    stats_by_nature = cases.values('case_nature').annotate(count=Count('id'))
    stats_by_priority = cases.values('priority').annotate(count=Count('id'))
    
    # 金额统计
    total_litigation_amount = cases.aggregate(Sum('litigation_amount'))['litigation_amount__sum'] or Decimal('0')
    total_dispute_amount = cases.aggregate(Sum('dispute_amount'))['dispute_amount__sum'] or Decimal('0')
    
    # 周期统计
    closed_cases = cases.filter(status='closed')
    avg_cycle = None
    if closed_cases.exists():
        cycles = []
        for case in closed_cases:
            if case.registration_date and case.closing_date:
                cycle = (case.closing_date - case.registration_date).days
                cycles.append(cycle)
        if cycles:
            avg_cycle = sum(cycles) / len(cycles)
    
    summary_cards = []
    
    context = _context(
        "案件统计",
        "📊",
        "诉讼案件统计分析",
        summary_cards=summary_cards,
        request=request
    )
    
    context.update({
        'stats_by_type': stats_by_type,
        'stats_by_status': stats_by_status,
        'stats_by_nature': stats_by_nature,
        'stats_by_priority': stats_by_priority,
        'total_litigation_amount': total_litigation_amount,
        'total_dispute_amount': total_dispute_amount,
        'avg_cycle': avg_cycle,
        'date_from': date_from,
        'date_to': date_to,
    })
    
    return render(request, 'litigation_management/case_statistics.html', context)


@login_required
def expense_statistics(request):
    """费用统计"""
    permission_codes = get_user_permission_codes(request.user)
    
    if not _permission_granted('litigation_management.statistics.view', permission_codes):
        messages.error(request, '您没有权限查看费用统计')
        return redirect('litigation_pages:case_list')
    
    # 获取筛选参数
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    case_id = request.GET.get('case_id', '')
    
    # 获取费用列表
    expenses = LitigationExpense.objects.select_related('case', 'project').all()
    
    # 权限过滤
    if not _permission_granted('litigation_management.case.view_all', permission_codes):
        cases = LitigationCase.objects.filter(
            Q(case_manager=request.user) | Q(registered_by=request.user)
        )
        expenses = expenses.filter(case__in=cases)
    
    # 应用筛选
    if date_from:
        expenses = expenses.filter(expense_date__gte=date_from)
    if date_to:
        expenses = expenses.filter(expense_date__lte=date_to)
    if case_id:
        expenses = expenses.filter(case_id=case_id)
    
    # 统计
    total_amount = expenses.aggregate(Sum('amount'))['amount__sum'] or Decimal('0')
    stats_by_type = expenses.values('expense_type').annotate(
        count=Count('id'),
        total=Sum('amount')
    )
    stats_by_case = expenses.values('case__case_number', 'case__case_name').annotate(
        count=Count('id'),
        total=Sum('amount')
    ).order_by('-total')[:10]
    stats_by_status = expenses.values('payment_status').annotate(
        count=Count('id'),
        total=Sum('amount')
    )
    
    # 时间统计
    stats_by_month = expenses.values('expense_date__year', 'expense_date__month').annotate(
        count=Count('id'),
        total=Sum('amount')
    ).order_by('expense_date__year', 'expense_date__month')
    
    summary_cards = []
    
    # 获取案件列表（用于筛选）
    cases = LitigationCase.objects.all()
    if not _permission_granted('litigation_management.case.view_all', permission_codes):
        cases = cases.filter(Q(case_manager=request.user) | Q(registered_by=request.user))
    
    context = _context(
        "费用统计",
        "💰",
        "诉讼费用统计分析",
        summary_cards=summary_cards,
        request=request
    )
    
    context.update({
        'stats_by_type': stats_by_type,
        'stats_by_case': stats_by_case,
        'stats_by_status': stats_by_status,
        'stats_by_month': stats_by_month,
        'total_amount': total_amount,
        'cases': cases,
        'date_from': date_from,
        'date_to': date_to,
        'case_id': case_id,
    })
    
    return render(request, 'litigation_management/expense_statistics.html', context)


@login_required
def result_statistics(request):
    """结果统计"""
    permission_codes = get_user_permission_codes(request.user)
    
    if not _permission_granted('litigation_management.statistics.view', permission_codes):
        messages.error(request, '您没有权限查看结果统计')
        return redirect('litigation_pages:case_list')
    
    # 获取筛选参数
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    # 获取已结案案件
    cases = LitigationCase.objects.filter(status__in=['closed', 'withdrawn', 'settled'])
    
    # 权限过滤
    if not _permission_granted('litigation_management.case.view_all', permission_codes):
        cases = cases.filter(Q(case_manager=request.user) | Q(registered_by=request.user))
    
    # 时间筛选
    if date_from:
        cases = cases.filter(closing_date__gte=date_from)
    if date_to:
        cases = cases.filter(closing_date__lte=date_to)
    
    # 结果统计
    won_cases = cases.filter(status='closed')  # 假设closed为胜诉，实际需要根据判决结果判断
    lost_cases = cases.filter(status='closed')  # 需要根据实际情况判断
    settled_cases = cases.filter(status='settled')
    withdrawn_cases = cases.filter(status='withdrawn')
    
    # 金额统计
    won_amount = won_cases.aggregate(Sum('litigation_amount'))['litigation_amount__sum'] or Decimal('0')
    lost_amount = lost_cases.aggregate(Sum('litigation_amount'))['litigation_amount__sum'] or Decimal('0')
    settled_amount = settled_cases.aggregate(Sum('litigation_amount'))['litigation_amount__sum'] or Decimal('0')
    withdrawn_amount = withdrawn_cases.aggregate(Sum('litigation_amount'))['litigation_amount__sum'] or Decimal('0')
    
    # 周期统计
    won_cycles = []
    for case in won_cases:
        if case.registration_date and case.closing_date:
            cycle = (case.closing_date - case.registration_date).days
            won_cycles.append(cycle)
    
    avg_won_cycle = sum(won_cycles) / len(won_cycles) if won_cycles else None
    
    summary_cards = []
    
    context = _context(
        "结果统计",
        "📊",
        "诉讼结果统计分析",
        summary_cards=summary_cards,
        request=request
    )
    
    context.update({
        'won_cases': won_cases.count(),
        'lost_cases': lost_cases.count(),
        'settled_cases': settled_cases.count(),
        'withdrawn_cases': withdrawn_cases.count(),
        'won_amount': won_amount,
        'lost_amount': lost_amount,
        'settled_amount': settled_amount,
        'withdrawn_amount': withdrawn_amount,
        'avg_won_cycle': avg_won_cycle,
        'date_from': date_from,
        'date_to': date_to,
    })
    
    return render(request, 'litigation_management/result_statistics.html', context)


# ==================== 全局列表页面（不需要case_id）====================

@login_required
def preservation_list_all(request):
    """所有案件的保全续封列表"""
    permission_codes = get_user_permission_codes(request.user)
    
    if not _permission_granted('litigation_management.process.manage', permission_codes):
        messages.error(request, '您没有权限查看保全续封')
        return redirect('litigation_pages:case_list')
    
    # 获取所有保全续封
    seals = PreservationSeal.objects.select_related('case').all()
    
    # 权限过滤
    if not _permission_granted('litigation_management.case.view_all', permission_codes):
        cases = LitigationCase.objects.filter(
            Q(case_manager=request.user) | Q(registered_by=request.user)
        )
        seals = seals.filter(case__in=cases)
    
    # 按状态筛选
    status_filter = request.GET.get('status', '')
    if status_filter:
        seals = seals.filter(status=status_filter)
    
    # 检查即将到期的保全
    expiring_filter = request.GET.get('expiring', '')
    today = timezone.now().date()
    if expiring_filter == '1':
        seals = seals.filter(
            status='active',
            end_date__lte=today + timedelta(days=7),
            end_date__gte=today
        )
    
    # 排序
    seals = seals.order_by('-end_date')
    
    # 分页
    page_size = request.GET.get('page_size', '10')
    try:
        per_page = int(page_size)
        if per_page not in [10, 20, 50]:
            per_page = 10
    except (ValueError, TypeError):
        per_page = 10
    paginator = Paginator(seals, per_page)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    expiring_soon = seals.filter(end_date__lte=today + timedelta(days=7), status='active').count()
    
    summary_cards = []
    
    context = _context(
        "保全续封管理",
        "🔒",
        "管理所有案件的保全续封记录",
        summary_cards=summary_cards,
        request=request
    )
    
    warning_date = today + timedelta(days=7)
    context.update({
        'seals': page_obj,
        'status_filter': status_filter,
        'expiring_filter': expiring_filter,
        'today': today,
        'warning_date': warning_date,
    })
    
    return render(request, 'litigation_management/preservation_list_all.html', context)


@login_required
def document_list_all(request):
    """所有案件的文档列表"""
    permission_codes = get_user_permission_codes(request.user)
    
    if not _permission_granted('litigation_management.document.view', permission_codes):
        messages.error(request, '您没有权限查看文档')
        return redirect('litigation_pages:case_list')
    
    # 获取所有文档
    documents = LitigationDocument.objects.select_related('case', 'uploaded_by').all()
    
    # 权限过滤
    if not _permission_granted('litigation_management.case.view_all', permission_codes):
        cases = LitigationCase.objects.filter(
            Q(case_manager=request.user) | Q(registered_by=request.user)
        )
        documents = documents.filter(case__in=cases)
    
    # 按类型筛选
    doc_type = request.GET.get('type', '')
    if doc_type:
        documents = documents.filter(document_type=doc_type)
    
    # 排序
    documents = documents.order_by('-uploaded_at')
    
    # 分页
    page_size = request.GET.get('page_size', '10')
    try:
        per_page = int(page_size)
        if per_page not in [10, 20, 50]:
            per_page = 10
    except (ValueError, TypeError):
        per_page = 10
    paginator = Paginator(documents, per_page)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    summary_cards = []
    
    context = _context(
        "诉讼文档管理",
        "📄",
        "管理所有案件的诉讼文档",
        summary_cards=summary_cards,
        request=request
    )
    
    context.update({
        'documents': page_obj,
        'doc_type': doc_type,
    })
    
    return render(request, 'litigation_management/document_list_all.html', context)


@login_required
def expense_list_all(request):
    """所有案件的费用列表"""
    permission_codes = get_user_permission_codes(request.user)
    
    if not _permission_granted('litigation_management.expense.view', permission_codes):
        messages.error(request, '您没有权限查看费用')
        return redirect('litigation_pages:case_list')
    
    # 获取所有费用
    expenses = LitigationExpense.objects.select_related('case', 'project').all()
    
    # 权限过滤
    if not _permission_granted('litigation_management.case.view_all', permission_codes):
        cases = LitigationCase.objects.filter(
            Q(case_manager=request.user) | Q(registered_by=request.user)
        )
        expenses = expenses.filter(case__in=cases)
    
    # 按状态筛选
    status_filter = request.GET.get('status', '')
    if status_filter:
        expenses = expenses.filter(payment_status=status_filter)
    
    # 排序
    expenses = expenses.order_by('-expense_date')
    
    # 分页
    page_size = request.GET.get('page_size', '10')
    try:
        per_page = int(page_size)
        if per_page not in [10, 20, 50]:
            per_page = 10
    except (ValueError, TypeError):
        per_page = 10
    paginator = Paginator(expenses, per_page)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # 统计
    total_amount = expenses.aggregate(Sum('amount'))['amount__sum'] or Decimal('0')
    paid_amount = expenses.filter(payment_status='paid').aggregate(Sum('amount'))['amount__sum'] or Decimal('0')
    pending_amount = total_amount - paid_amount
    
    summary_cards = []
    
    context = _context(
        "费用管理",
        "💰",
        "管理所有案件的诉讼费用",
        summary_cards=summary_cards,
        request=request
    )
    
    context.update({
        'expenses': page_obj,
        'status_filter': status_filter,
        'total_amount': total_amount,
        'paid_amount': paid_amount,
        'pending_amount': pending_amount,
    })
    
    return render(request, 'litigation_management/expense_list_all.html', context)


@login_required
def expense_reimburse_list(request):
    """费用报销列表（待报销和已报销的费用）"""
    permission_codes = get_user_permission_codes(request.user)
    
    if not _permission_granted('litigation_management.expense.view', permission_codes):
        messages.error(request, '您没有权限查看费用报销')
        return redirect('litigation_pages:case_list')
    
    # 获取所有费用
    expenses = LitigationExpense.objects.select_related('case', 'project').all()
    
    # 权限过滤
    if not _permission_granted('litigation_management.case.view_all', permission_codes):
        cases = LitigationCase.objects.filter(
            Q(case_manager=request.user) | Q(registered_by=request.user)
        )
        expenses = expenses.filter(case__in=cases)
    
    # 只显示已申请报销或已报销的费用
    expenses = expenses.filter(reimbursement_applied=True)
    
    # 按报销状态筛选
    reimbursement_status_filter = request.GET.get('status', '')
    if reimbursement_status_filter:
        expenses = expenses.filter(reimbursement_status=reimbursement_status_filter)
    
    # 排序
    expenses = expenses.order_by('-expense_date')
    
    # 分页
    page_size = request.GET.get('page_size', '10')
    try:
        per_page = int(page_size)
        if per_page not in [10, 20, 50]:
            per_page = 10
    except (ValueError, TypeError):
        per_page = 10
    paginator = Paginator(expenses, per_page)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # 统计
    total_amount = expenses.aggregate(Sum('amount'))['amount__sum'] or Decimal('0')
    pending_amount = expenses.filter(reimbursement_status='pending').aggregate(Sum('amount'))['amount__sum'] or Decimal('0')
    approved_amount = expenses.filter(reimbursement_status='approved').aggregate(Sum('amount'))['amount__sum'] or Decimal('0')
    rejected_amount = expenses.filter(reimbursement_status='rejected').aggregate(Sum('amount'))['amount__sum'] or Decimal('0')
    
    summary_cards = []
    
    context = _context(
        "费用报销管理",
        "💳",
        "管理所有案件的费用报销申请",
        summary_cards=summary_cards,
        request=request
    )
    
    context.update({
        'expenses': page_obj,
        'reimbursement_status_filter': reimbursement_status_filter,
        'total_amount': total_amount,
        'pending_amount': pending_amount,
        'approved_amount': approved_amount,
        'rejected_amount': rejected_amount,
    })
    
    return render(request, 'litigation_management/expense_reimburse_list.html', context)


@login_required
def person_list_all(request):
    """所有案件的人员列表"""
    permission_codes = get_user_permission_codes(request.user)
    
    if not _permission_granted('litigation_management.person.manage', permission_codes):
        messages.error(request, '您没有权限查看人员')
        return redirect('litigation_pages:case_list')
    
    # 获取所有人员
    persons = LitigationPerson.objects.select_related('case').all()
    
    # 权限过滤
    if not _permission_granted('litigation_management.case.view_all', permission_codes):
        cases = LitigationCase.objects.filter(
            Q(case_manager=request.user) | Q(registered_by=request.user)
        )
        persons = persons.filter(case__in=cases)
    
    # 按类型筛选
    person_type = request.GET.get('type', '')
    if person_type:
        persons = persons.filter(person_type=person_type)
    
    # 排序
    persons = persons.order_by('person_type', 'name')
    
    # 分页
    page_size = request.GET.get('page_size', '10')
    try:
        per_page = int(page_size)
        if per_page not in [10, 20, 50]:
            per_page = 10
    except (ValueError, TypeError):
        per_page = 10
    paginator = Paginator(persons, per_page)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    summary_cards = []
    
    context = _context(
        "人员管理",
        "👥",
        "管理所有案件的相关人员",
        summary_cards=summary_cards,
        request=request
    )
    
    context.update({
        'persons': page_obj,
        'person_type': person_type,
    })
    
    return render(request, 'litigation_management/person_list_all.html', context)


@login_required
def timeline_list_all(request):
    """所有案件的时间节点列表"""
    permission_codes = get_user_permission_codes(request.user)
    
    if not _permission_granted('litigation_management.timeline.manage', permission_codes):
        messages.error(request, '您没有权限查看时间节点')
        return redirect('litigation_pages:case_list')
    
    # 获取所有时间节点
    timelines = LitigationTimeline.objects.select_related('case').all()
    
    # 权限过滤
    if not _permission_granted('litigation_management.case.view_all', permission_codes):
        cases = LitigationCase.objects.filter(
            Q(case_manager=request.user) | Q(registered_by=request.user)
        )
        timelines = timelines.filter(case__in=cases)
    
    # 按类型筛选
    timeline_type = request.GET.get('type', '')
    if timeline_type:
        timelines = timelines.filter(timeline_type=timeline_type)
    
    # 按状态筛选
    status_filter = request.GET.get('status', '')
    if status_filter:
        timelines = timelines.filter(status=status_filter)
    
    # 检查提醒
    reminder_filter = request.GET.get('reminder', '')
    if reminder_filter == '1':
        timelines = timelines.filter(reminder_enabled=True)
    
    # 排序
    timelines = timelines.order_by('timeline_date')
    
    # 分页
    page_size = request.GET.get('page_size', '10')
    try:
        per_page = int(page_size)
        if per_page not in [10, 20, 50]:
            per_page = 10
    except (ValueError, TypeError):
        per_page = 10
    paginator = Paginator(timelines, per_page)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # timeline_date是DateTimeField，需要转换为datetime范围进行比较
    today = timezone.now().date()
    warning_date = today + timedelta(days=7)
    warning_datetime = timezone.make_aware(datetime.combine(warning_date, datetime.max.time()))
    
    summary_cards = []
    
    context = _context(
        "时间节点管理",
        "📅",
        "管理所有案件的时间节点",
        summary_cards=summary_cards,
        request=request
    )
    
    context.update({
        'timelines': page_obj,
        'timeline_type': timeline_type,
        'status_filter': status_filter,
        'reminder_filter': reminder_filter,
        'today': today,
        'warning_date': warning_date,
        'warning_datetime': warning_datetime,
    })
    
    return render(request, 'litigation_management/timeline_list_all.html', context)
