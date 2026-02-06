# 合同管理视图
# 从customer_management迁移而来

from decimal import Decimal, InvalidOperation
import json
import csv
import io
import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum, Q, F
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.urls import reverse, NoReverseMatch

from backend.apps.customer_management.models import (
    ClientType,
    ClientGrade,
    Client,
    ClientContact,
    ClientProject,
    CustomerLead,
    CustomerFiling,
    CustomerRelationship,
    CustomerRelationshipUpgrade,
    BusinessExpenseApplication,
    VisitPlan,
    VisitCheckin,
    VisitReview,
    SalesActivity,
    AuthorizationLetter,
    AuthorizationLetterTemplate,
    ContractNegotiation,
    ContactEducation,
    ContactCareer,
    ContactColleague,
)

# 商机管理相关模型已迁移到opportunity_management
from backend.apps.opportunity_management.models import (
    BusinessOpportunity,
    OpportunityFollowUp,
    OpportunityQuotation,
    BusinessNegotiation,
    BiddingQuotation,
)

# 合同管理相关模型已迁移到contract_management
from backend.apps.contract_management.models import (
    BusinessContract,
    BusinessPaymentPlan,
    ContractParty,
    ResultFileType,
)

from backend.apps.base_data.models import DesignStage, ServiceType
from backend.apps.system_management.services import get_user_permission_codes
from backend.core.views import HOME_NAV_STRUCTURE, _permission_granted, _build_full_top_nav
from backend.apps.permission_management.utils import normalize_permission_code
from backend.apps.customer_management.views_pages import _filter_clients_by_permission


def _check_customer_permission(permission_code, permission_set):
    """检查权限（支持 contract_management.* 等代码经规范化后校验）"""
    normalized = normalize_permission_code(permission_code)
    return _permission_granted(normalized, permission_set)


# 尝试导入统一的侧边栏菜单构建函数
try:
    from backend.core.views import _build_unified_sidebar_nav
except ImportError:
    # Fallback: 如果 _build_unified_sidebar_nav 不存在，提供简单实现
    def _build_unified_sidebar_nav(menu_structure, permission_set, active_id=None):
        """简单的侧边栏菜单构建函数（支持 url_name 转换）"""
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
                        'label': child.get('label', ''),
                        'icon': child.get('icon', ''),
                        'url': child_url,
                        'active': child.get('id') == active_id if active_id else False,
                    })
                nav_item['children'] = children
            
            nav.append(nav_item)
        
        return nav

logger = logging.getLogger(__name__)

def _context(page_title, page_icon, description, summary_cards=None, sections=None, request=None, active_menu_id=None):
    """生成页面上下文（统一格式）"""
    context = {
        "page_title": page_title,
        "page_icon": page_icon,
        "description": description,
        "summary_cards": summary_cards or [],
        "sections": sections or [],
    }
    if request and request.user.is_authenticated:
        permission_set = get_user_permission_codes(request.user)
        context['full_top_nav'] = _build_full_top_nav(permission_set, request.user)
        context['sidebar_module_title'] = '合同管理'
        context['sidebar_module_subtitle'] = 'Contract Management'
        context['sidebar_title'] = '合同管理'
        context['sidebar_subtitle'] = 'Contract Management'
        context['sidebar_nav'] = _build_contract_management_sidebar_nav(
            permission_set, request.path, active_id=active_menu_id
        )
    else:
        context['full_top_nav'] = []
        context['sidebar_nav'] = []
    return context

CONTRACT_MANAGEMENT_MENU = [
    {
        'id': 'contract_home',
        'label': '首页',
        'icon': '🏠',
        'url_name': 'contract_pages:contract_management_home',
        'permission': 'contract_management.contract.view',
    },
    {
        'id': 'authorization_letter',
        'label': '业务委托书',
        'icon': '📋',
        'permission': 'contract_management.client.view',  # 使用客户管理权限（临时）
        'children': [
            {
                'id': 'authorization_letter_list',
                'label': '业务委托书列表',
                'icon': '📋',
                'url_name': 'contract_pages:authorization_letter_list',
                'permission': 'contract_management.client.view',
            },
            {
                'id': 'authorization_letter_template_list',
                'label': '委托书模板管理',
                'icon': '📄',
                'url_name': 'contract_pages:authorization_letter_template_list',
                'permission': 'contract_management.client.view',
            },
        ]
    },
    {
        'id': 'contract_signing',
        'label': '正式合同签署',
        'icon': '✍️',
        'permission': 'contract_management.client.view',  # 使用客户管理权限（临时）
        'children': [
            {
                'id': 'contract_management_list',
                'label': '合同列表',
                'icon': '📄',
                'url_name': 'contract_pages:contract_management_list',
                'permission': 'contract_management.client.view',
            },
            {
                'id': 'contract_negotiation_list',
                'label': '合同洽谈记录',
                'icon': '💬',
                'url_name': 'contract_pages:contract_negotiation_list',
                'permission': 'contract_management.client.view',
            },
            {
                'id': 'contract_negotiation_create',
                'label': '创建合同洽谈记录',
                'icon': '➕',
                'url_name': 'contract_pages:contract_negotiation_create',
                'permission': 'contract_management.client.create',
            },
            {
                'id': 'contract_finalize_list',
                'label': '合同定稿列表',
                'icon': '📋',
                'url_name': 'contract_pages:contract_finalize_list',
                'permission': 'contract_management.client.view',
            },
            {
                'id': 'contract_finalize_create',
                'label': '创建合同定稿',
                'icon': '✅',
                'url_name': 'contract_pages:contract_finalize_create',
                'permission': 'contract_management.client.create',
            },
        ]
    },
    {
        'id': 'contract_execution',
        'label': '合同执行',
        'icon': '📊',
        'permission': 'contract_management.client.view',  # 使用客户管理权限（临时）
        'children': [
            {
                'id': 'contract_performance',
                'label': '履约跟踪',
                'icon': '📋',
                'url_name': 'contract_pages:contract_performance_track',
                'permission': 'contract_management.client.view',
            },
            {
                'id': 'contract_dispute_list',
                'label': '合同争议',
                'icon': '⚖️',
                'url_name': 'contract_pages:contract_dispute_list',
                'permission': 'contract_management.client.view',
            },
        ]
    },
    {
        'id': 'contract_reminder',
        'label': '提醒与警报',
        'icon': '⚠️',
        'permission': 'contract_management.client.view',  # 使用客户管理权限（临时）
        'children': [
            {
                'id': 'contract_expiry_reminder',
                'label': '到期提醒',
                'icon': '📅',
                'url_name': 'contract_pages:contract_expiry_reminder',
                'permission': 'contract_management.client.view',
            },
            {
                'id': 'contract_payment_reminder',
                'label': '付款提醒',
                'icon': '💰',
                'url_name': 'contract_pages:contract_payment_reminder',
                'permission': 'contract_management.client.view',
            },
            {
                'id': 'contract_risk_warning',
                'label': '风险预警',
                'icon': '⚠️',
                'url_name': 'contract_pages:contract_risk_warning',
                'permission': 'contract_management.client.view',
            },
        ]
    },
]


# ==================== 商机管理模块左侧菜单结构 =====================

def _build_contract_management_menu(permission_set, active_id=None):
    """
    生成合同管理模块左侧菜单
    
    参数:
        permission_set: 用户权限集合（set）
        active_id: 当前激活的菜单项ID
    
    返回:
        list: 菜单项列表，每个菜单项包含：
            - id: 菜单项ID
            - label: 菜单项标签
            - icon: 菜单项图标
            - url: 菜单项URL（如果有）
            - permission: 所需权限
            - active: 是否激活
            - children: 子菜单项列表（如果有）
    """
    menu = []
    
    for menu_group in CONTRACT_MANAGEMENT_MENU:
        # 检查父菜单权限
        permission = menu_group.get('permission')
        if permission and not _check_customer_permission(permission, permission_set):
            continue
        
        # 处理子菜单
        children = []
        for child in menu_group.get('children', []):
            # 检查子菜单权限（使用_check_customer_permission以支持权限代码规范化）
            child_permission = child.get('permission')
            if child_permission and not _check_customer_permission(child_permission, permission_set):
                continue
            
            # 获取URL
            url_name = child.get('url_name')
            url = '#'
            if url_name:
                try:
                    url = reverse(url_name)
                except NoReverseMatch:
                    url = '#'
            
            # 判断是否激活
            is_active = child.get('id') == active_id
            
            children.append({
                'id': child.get('id'),
                'label': child.get('label'),
                'icon': child.get('icon'),
                'url': url,
                'active': is_active,
            })
        
        # 如果父菜单没有可见的子菜单，跳过
        if not children:
            continue
        
        # 判断父菜单是否激活（任意子菜单激活则父菜单激活）
        group_active = any(child.get('id') == active_id for child in menu_group.get('children', []))
        
        # 获取父菜单URL（如果有url_name，则使用第一个子菜单的URL作为父菜单URL）
        parent_url = '#'
        if menu_group.get('url_name'):
            try:
                parent_url = reverse(menu_group.get('url_name'))
            except NoReverseMatch:
                parent_url = '#'
        elif children:
            # 如果没有设置url_name，使用第一个子菜单的URL
            parent_url = children[0].get('url', '#')
        
        menu.append({
            'id': menu_group.get('id'),
            'label': menu_group.get('label'),
            'icon': menu_group.get('icon'),
            'url': parent_url,
            'active': group_active,
            'expanded': group_active,  # 如果有激活项，默认展开（与计划管理格式一致）
            'children': children,
        })
    
    return menu



def _build_contract_management_sidebar_nav(permission_set, request_path=None, active_id=None):
    """生成合同管理左侧菜单（统一格式）"""
    return _build_unified_sidebar_nav(CONTRACT_MANAGEMENT_MENU, permission_set, active_id=active_id)


# 使用统一的顶部导航菜单生成函数（已从 backend.core.views 导入）



def _apply_contract_filters(queryset, filters):
    """
    应用合同筛选条件（公共函数）
    
    Args:
        queryset: 合同查询集
        filters: 筛选条件字典，包含：
            - search: 搜索关键词
            - status: 状态筛选
            - contract_type: 合同类型筛选
            - client_id: 客户ID筛选
            - project_id: 项目ID筛选
            - date_from: 开始日期筛选
            - date_to: 结束日期筛选
    
    Returns:
        QuerySet: 应用筛选条件后的查询集
    """
    from django.db.models import Q
    
    if filters.get('search'):
        search = filters['search']
        queryset = queryset.filter(
            Q(project_number__icontains=search) |
            Q(contract_name__icontains=search) |
            Q(client__name__icontains=search) |
            Q(project__project_number__icontains=search) |
            Q(project__name__icontains=search)
        )
    
    if filters.get('status'):
        queryset = queryset.filter(status=filters['status'])
    
    if filters.get('contract_type'):
        queryset = queryset.filter(contract_type=filters['contract_type'])
    
    if filters.get('client_id'):
        queryset = queryset.filter(client_id=filters['client_id'])
    
    if filters.get('project_id'):
        queryset = queryset.filter(project_id=filters['project_id'])
    
    if filters.get('date_from'):
        queryset = queryset.filter(contract_date__gte=filters['date_from'])
    
    if filters.get('date_to'):
        queryset = queryset.filter(contract_date__lte=filters['date_to'])
    
    return queryset

@login_required

def contract_management_home(request):
    """合同管理首页 - 数据展示中心"""
    permission_set = get_user_permission_codes(request.user)
    
    # 权限检查
    if not _permission_granted('contract_management.contract.view', permission_set):
        messages.error(request, '您没有权限访问合同管理')
        return redirect('home')
    
    from django.utils import timezone
    from datetime import timedelta
    from django.db.models import Sum, Count, Q
    from decimal import Decimal
    
    now = timezone.now()
    today = now.date()
    this_month_start = today.replace(day=1)
    seven_days_ago = today - timedelta(days=7)
    
    try:
        # 基础查询集（考虑权限）
        base_queryset = BusinessContract.objects.all()
        
        # 统计信息
        total_contracts = base_queryset.count()
        draft_contracts = base_queryset.filter(status='draft').count()
        pending_contracts = base_queryset.filter(status='pending_review').count()
        signed_contracts = base_queryset.filter(status='signed').count()
        total_amount = base_queryset.filter(status='signed').aggregate(
            total=Sum('total_amount')
        )['total'] or Decimal('0')
        monthly_new = base_queryset.filter(
            created_time__year=now.year,
            created_time__month=now.month
        ).count()
        
        # 状态统计
        status_stats = base_queryset.values('status').annotate(count=Count('id'))
        status_dict = {stat['status']: stat['count'] for stat in status_stats}
        
        # 最近合同
        recent_contracts = base_queryset.select_related('client', 'project', 'created_by').order_by('-created_time')[:10]
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception('获取合同统计信息失败: %s', str(e))
        total_contracts = 0
        draft_contracts = 0
        pending_contracts = 0
        signed_contracts = 0
        total_amount = Decimal('0')
        monthly_new = 0
        status_dict = {}
        recent_contracts = []
    
    # 构建统计卡片
    summary_cards = []
    try:
        summary_cards.append({
            'label': '合同总数',
            'value': total_contracts,
            'url': reverse('contract_pages:contract_management_list'),
            'variant': 'info'
        })
        summary_cards.append({
            'label': '草稿合同',
            'value': draft_contracts,
            'url': reverse('contract_pages:contract_management_list') + '?status=draft',
            'variant': 'warning'
        })
        summary_cards.append({
            'label': '待审核',
            'value': pending_contracts,
            'url': reverse('contract_pages:contract_management_list') + '?status=pending_review',
            'variant': 'warning'
        })
        summary_cards.append({
            'label': '已签署',
            'value': signed_contracts,
            'url': reverse('contract_pages:contract_management_list') + '?status=signed',
            'variant': 'success'
        })
        summary_cards.append({
            'label': '合同总额',
            'value': f'{total_amount:,.0f}',
            'url': reverse('contract_pages:contract_management_list') + '?status=signed',
            'variant': 'primary'
        })
        summary_cards.append({
            'label': '本月新增',
            'value': monthly_new,
            'url': reverse('contract_pages:contract_management_list'),
            'variant': 'info'
        })
    except Exception as e:
        logger.exception('构建统计卡片失败: %s', str(e))
    
    # 转换为core_cards格式（与计划管理一致）
    core_cards = []
    for card in summary_cards:
        core_cards.append({
            'label': card.get('label', ''),
            'icon': '📄',
            'value': str(card.get('value', 0)),
            'subvalue': '',
            'url': card.get('url', '#'),
        })
    
    # 顶部操作栏
    top_actions = []
    if _permission_granted('contract_management.contract.create', permission_set):
        try:
            top_actions.append({
                'label': '创建合同',
                'icon': '➕',
                'url': reverse('contract_pages:contract_create'),
            })
        except NoReverseMatch:
            pass
    
    # 风险预警
    risk_warnings = []
    overdue_contracts_count = 0
    stale_contracts_count = 0
    # TODO: 添加具体的风险预警逻辑
    
    # 待办事项
    todo_items = []
    pending_approval_count = 0
    upcoming_deadline_count = 0
    # TODO: 添加具体的待办事项逻辑
    
    # 我的工作
    my_work = {}
    
    # 最近活动（统一为字典格式，与计划管理一致）
    recent_activities = {}
    # 最近创建的合同
    recent_activities['recent_contracts'] = [{
        'title': contract.contract_name or contract.project_number or f'合同 #{contract.id}',
        'creator': contract.created_by.get_full_name() or contract.created_by.username if contract.created_by else '系统',
        'time': contract.created_time,
        'status': contract.get_status_display(),
        'url': reverse('contract_pages:contract_detail', args=[contract.id]),
    } for contract in recent_contracts[:5]]
    
    # 构建上下文
    context = {
        'page_title': '合同管理',
        'page_icon': '📄',
        'description': '合同全生命周期管理，从起草到签署、执行、变更的全流程数字化管理。',
        'core_cards': core_cards,
        'top_actions': top_actions,
        'risk_warnings': risk_warnings,
        'todo_items': todo_items,
        'my_work': my_work,
        'recent_activities': recent_activities,
        'overdue_contracts_count': overdue_contracts_count,
        'stale_contracts_count': stale_contracts_count,
        'pending_approval_count': pending_approval_count,
        'upcoming_deadline_count': upcoming_deadline_count,
        'todo_summary_url': reverse('contract_pages:contract_management_list'),
        'summary_cards': summary_cards,  # 保持向后兼容
        'sections': [],
        'total_contracts': total_contracts,
        'draft_contracts': draft_contracts,
        'pending_contracts': pending_contracts,
        'signed_contracts': signed_contracts,
        'total_amount': total_amount,
        'monthly_new': monthly_new,
        'status_dict': status_dict,
        'recent_contracts': recent_contracts,
        'sidebar_module_title': '合同管理',
        'sidebar_module_subtitle': 'Contract Management',
    }
    
    if request and request.user.is_authenticated:
        permission_set = get_user_permission_codes(request.user)
        context['full_top_nav'] = _build_full_top_nav(permission_set, request.user)
        context['sidebar_nav'] = _build_contract_management_sidebar_nav(permission_set, request.path, active_id='contract_home')
        context['sidebar_title'] = '合同管理'
        context['sidebar_subtitle'] = 'Contract Management'
    else:
        context['full_top_nav'] = []
        context['sidebar_nav'] = []
    
    return render(request, "contract_management/contract_home.html", context)


@login_required

def contract_management_list(request):
    """
    合同管理列表页面（显示所有状态的合同）
    
    功能：
    - 显示所有状态的合同列表
    - 支持多维度筛选（状态、类型、客户、日期范围）
    - 支持分页显示
    """
    import logging
    from django.core.paginator import Paginator
    
    logger = logging.getLogger(__name__)
    
    # 权限检查
    permission_set = get_user_permission_codes(request.user)
    if not _permission_granted('contract_management.contract.view', permission_set):
        messages.error(request, '您没有权限访问合同管理')
        return redirect('contract_pages:contract_management_home')
    
    # 获取筛选参数
    filters = {
        'search': request.GET.get('search', ''),
        'status': request.GET.get('status', ''),
        'contract_type': request.GET.get('contract_type', ''),
        'client_id': request.GET.get('client_id', ''),
        'project_id': request.GET.get('project_id', ''),
        'date_from': request.GET.get('date_from', ''),
        'date_to': request.GET.get('date_to', ''),
    }
    
    # 获取合同列表
    try:
        contracts = BusinessContract.objects.select_related(
            'client', 'project', 'created_by'
        ).order_by('-created_time')
        
        # 应用筛选条件
        contracts = _apply_contract_filters(contracts, filters)
        
        # 分页
        paginator = Paginator(contracts, 13)
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)
    except Exception as e:
        logger.exception('获取合同列表失败: %s', str(e))
        messages.error(request, f'获取合同列表失败：{str(e)}')
        page_obj = None
    
    # 统计卡片已删除，设置为空列表
    summary_cards = []
    
    # 获取筛选选项
    try:
        clients = Client.objects.filter(is_active=True).order_by('name')[:100]
    except Exception as e:
        logger.exception('获取客户列表失败: %s', str(e))
        clients = []
    
    # 获取项目列表（仅获取有合同的项目）
    projects = []
    try:
        from backend.apps.production_management.models import Project
        contract_project_ids = BusinessContract.objects.filter(
            project__isnull=False
        ).values_list('project_id', flat=True).distinct()[:50]
        
        if contract_project_ids:
            projects = Project.objects.filter(
                id__in=contract_project_ids
            ).order_by('-created_time')[:50]
    except Exception as e:
        logger.exception('获取项目列表失败: %s', str(e))
        projects = []
    
    # 检查创建权限
    can_create = _permission_granted('contract_management.contract.create', permission_set)
    
    context = _context(
        "合同管理",
        "📄",
        "管理所有业务合同",
        summary_cards=summary_cards,
        request=request,
        active_menu_id='contract_management_list',
    )
    
    # 为每个合同对象添加权限属性
    if page_obj:
        for contract in page_obj:
            # 判断是否可以编辑（创建人或具有编辑权限，且状态为草稿）
            contract.can_edit = (
                contract.status == 'draft' and (
                    contract.created_by == request.user or 
                    _permission_granted('contract_management.contract.manage', permission_set)
                )
            )
            # 判断是否可以删除（创建人或具有删除权限，且状态为草稿）
            contract.can_delete = (
                contract.status == 'draft' and (
                    contract.created_by == request.user or 
                    _permission_granted('contract_management.contract.manage', permission_set)
                )
            )
    
    context.update({
        'page_obj': page_obj,
        'search': filters['search'],
        'status': filters['status'],
        'contract_type': filters['contract_type'],
        'client_id': filters['client_id'],
        'project_id': filters['project_id'],
        'date_from': filters['date_from'],
        'date_to': filters['date_to'],
        'clients': clients,
        'projects': projects,
        'status_choices': BusinessContract.CONTRACT_STATUS_CHOICES,
        'type_choices': BusinessContract.CONTRACT_TYPE_CHOICES,
        'can_create': can_create,
        'show_filter_fields_settings_btn': True,
    })
    
    return render(request, "contract_management/contract_management_list.html", context)


@login_required

def contract_detail(request, contract_id):
    """
    合同详情页面
    
    功能：
    - 显示合同完整信息
    - 显示关联数据（回款计划、文件、变更记录、子合同等）
    - 支持状态流转操作
    - 支持文件上传和管理
    - 支持创建变更记录
    - 显示审批流程和记录
    """
    import logging
    logger = logging.getLogger(__name__)
    
    # 权限检查
    permission_set = get_user_permission_codes(request.user)
    if not _permission_granted('contract_management.contract.view', permission_set):
        messages.error(request, '您没有权限查看合同详情')
        return redirect('contract_pages:contract_management_list')
    
    contract = get_object_or_404(
        BusinessContract.objects.select_related(
            'client', 'project', 'parent_contract', 'created_by', 'opportunity', 'opportunity__business_manager', 'opportunity__client'
        ), 
        id=contract_id
    )
    
    # 获取关联数据
    payment_plans = contract.payment_plans.all().order_by('planned_date')
    
    # 获取回款记录（通过回款计划关联）
    payment_records = []
    try:
        from backend.apps.settlement_management.models import PaymentRecord
        # 获取该合同所有回款计划的ID
        payment_plan_ids = list(payment_plans.values_list('id', flat=True))
        if payment_plan_ids:
            payment_records = PaymentRecord.objects.filter(
                payment_plan_type='business',
                payment_plan_id__in=payment_plan_ids
            ).select_related('created_by', 'confirmed_by').order_by('-payment_date', '-created_time')
    except Exception as e:
        logger.warning(f"获取回款记录失败: {str(e)}")
        payment_records = []
    
    files = contract.files.all().order_by('-uploaded_time')
    approvals = contract.approvals.all().order_by('approval_level', '-created_time')
    changes = contract.changes.all().order_by('-created_time')
    sub_contracts = contract.sub_contracts.all().order_by('-created_time')
    status_logs = contract.status_logs.all().order_by('-created_time')
    
    # 获取可流转的状态列表（包含状态代码和标签）
    valid_transition_codes = BusinessContract.get_valid_transitions(contract.status)
    status_choices_dict = dict(BusinessContract.CONTRACT_STATUS_CHOICES)
    valid_transitions = [
        {'code': code, 'label': status_choices_dict.get(code, code)}
        for code in valid_transition_codes
    ]
    
    # 为状态日志添加状态标签
    status_logs_list = []
    for log in status_logs:
        log_dict = {
            'id': log.id,
            'from_status': log.from_status,
            'from_status_label': status_choices_dict.get(log.from_status, log.from_status) if log.from_status else '初始状态',
            'to_status': log.to_status,
            'to_status_label': status_choices_dict.get(log.to_status, log.to_status),
            'actor': log.actor,
            'comment': log.comment,
            'created_time': log.created_time,
        }
        status_logs_list.append(log_dict)
    
    # 权限检查
    permission_set = get_user_permission_codes(request.user)
    can_manage = _check_customer_permission('contract_management.client.edit', permission_set)
    can_edit = can_manage and contract.status == 'draft'  # 只有草稿状态才能编辑
    
    # 获取审批信息
    approval_instance = None
    approval_records = []
    can_submit_approval = False
    try:
        from django.contrib.contenttypes.models import ContentType
        from backend.apps.workflow_engine.models import ApprovalInstance, ApprovalRecord
        
        content_type = ContentType.objects.get_for_model(BusinessContract)
        approval_instance = ApprovalInstance.objects.filter(
            content_type=content_type,
            object_id=contract.id
        ).select_related('workflow', 'applicant', 'current_node').order_by('-created_time').first()
        
        if approval_instance:
            approval_records = ApprovalRecord.objects.filter(
                instance=approval_instance
            ).select_related('node', 'approver', 'transferred_to').order_by('-approval_time')
        
        # 检查是否可以提交审批（有权限且合同状态为草稿、争议或定稿，且没有正在进行的审批）
        can_submit_approval = (
            can_manage and 
            contract.status in ['draft', 'dispute', 'finalized'] and
            (not approval_instance or approval_instance.status not in ['pending', 'in_progress'])
        )
    except Exception:
        pass
    
    # 使用统一的上下文构建函数
    base_context = _context(
        f'合同详情 - {contract.project_number or contract.contract_name or "未命名"}',
        '📃',
        '查看合同详细信息和关联数据',
        request=request,
        active_menu_id='contract_management_list',
    )
    
    # 添加合同详情相关数据
    base_context.update({
        'contract': contract,
        'payment_plans': payment_plans,
        'payment_records': payment_records,
        'files': files,
        'approvals': approvals,
        'changes': changes,
        'sub_contracts': sub_contracts,
        'status_logs': status_logs_list,
        'valid_transitions': valid_transitions,
        'status_choices': status_choices_dict,
        'can_manage': can_manage,
        'can_edit': can_edit,
        'approval_instance': approval_instance,
        'approval_records': approval_records,
        'can_submit_approval': can_submit_approval,
    })
    
    # 调试：确保opportunity被加载
    if hasattr(contract, 'opportunity'):
        logger.info(f"合同 {contract.id} 关联商机: {contract.opportunity}")
    else:
        logger.info(f"合同 {contract.id} 未关联商机")
    
    return render(request, "contract_management/contract_detail.html", base_context)


@login_required

def contract_create(request):
    """
    新建合同页面
    
    功能：
    - 创建新合同
    - 支持从业务委托书转换创建
    - 自动生成合同编号
    - 表单验证和错误处理
    """
    import logging
    logger = logging.getLogger(__name__)
    
    # 权限检查
    permission_set = get_user_permission_codes(request.user)
    if not _permission_granted('contract_management.contract.create', permission_set):
        messages.error(request, '您没有权限创建合同')
        return redirect('contract_pages:contract_management_list')
    
    # 检查是否从业务委托书转换而来
    authorization_letter_id = request.GET.get('authorization_letter')
    authorization_letter = None
    if authorization_letter_id:
        try:
            authorization_letter = AuthorizationLetter.objects.get(id=authorization_letter_id)
            if not authorization_letter.can_convert_to_contract():
                messages.warning(request, '只有已确认状态的委托书可以转换为合同')
                authorization_letter = None
        except AuthorizationLetter.DoesNotExist:
            pass
    
    if request.method == 'POST':
        # 处理表单提交
        try:
            from django.db import transaction
            from .forms import ContractForm
            form = ContractForm(request.POST, user=request.user, permission_set=permission_set)
            if form.is_valid():
                with transaction.atomic():
                    contract = form.save(commit=False)
                    contract.created_by = request.user
                    # 合同状态由系统自动判断，默认为合同草稿
                    if not contract.status:
                        contract.status = 'draft'
                    
                    # 如果是从委托书转换而来，继承项目编号
                    if authorization_letter_id:
                        try:
                            letter = AuthorizationLetter.objects.get(id=authorization_letter_id)
                            # 继承业务委托书的项目编号
                            if letter.project_number:
                                contract.project_number = letter.project_number
                            contract.save()
                            messages.success(request, f'合同创建成功（从委托书转换）。')
                        except AuthorizationLetter.DoesNotExist:
                            contract.save()
                            messages.success(request, f'合同创建成功。')
                    else:
                        contract.save()
                        messages.success(request, f'合同创建成功。')
                    
                    
                    try:
                        from decimal import Decimal
                        import re
                        
                        # 先删除所有旧的结算方案（重新创建）
                        for key, value in request.POST.items():
                            pass
                    except Exception as e:
                        # 如果保存结算方案失败，记录错误但不影响合同创建
                        logger.warning(f'保存结算方案失败: {str(e)}')
                
                return redirect('contract_pages:contract_detail', contract_id=contract.id)
            else:
                messages.error(request, '表单验证失败，请检查输入。')
        except Exception as e:
            logger.exception('创建合同失败: %s', str(e))
            messages.error(request, f'创建合同失败：{str(e)}')
    else:
        from .forms import ContractForm
        # 传递user和permission_set给表单，以便应用权限过滤
        form = ContractForm(user=request.user, permission_set=permission_set)
        
        # 设置责任部门和责任人员（系统自动填充，不可修改）
        if request.user.is_authenticated:
            # 责任部门：当前登录账号对应的部门
            if hasattr(request.user, 'department') and request.user.department:
                form.initial['responsible_department'] = request.user.department.name
            else:
                form.initial['responsible_department'] = '未设置部门'
            # 责任人员：当前登录账号对应的人员姓名
            form.initial['responsible_person'] = request.user.get_full_name() or request.user.username
        
        # 如果是从委托书转换而来，预填充表单
        if authorization_letter:
            # 预填充合同信息
            if authorization_letter.project:
                form.fields['project'].initial = authorization_letter.project
            if authorization_letter.opportunity and authorization_letter.opportunity.client:
                # 尝试找到对应的客户
                try:
                    client = Client.objects.get(name=authorization_letter.client_name)
                    form.fields['client'].initial = client
                except Client.DoesNotExist:
                    pass
            
            # 预填充合同名称
            if not form.initial.get('contract_name'):
                form.initial['contract_name'] = f"{authorization_letter.project_name} - 服务合同"
            
            # 预填充金额
            if authorization_letter.provisional_price:
                form.initial['contract_amount'] = authorization_letter.provisional_price
            
            # 预填充日期
            if authorization_letter.letter_date:
                form.initial['contract_date'] = authorization_letter.letter_date
                form.initial['effective_date'] = authorization_letter.letter_date
                if authorization_letter.start_date:
                    form.initial['start_date'] = authorization_letter.start_date
                if authorization_letter.end_date:
                    form.initial['end_date'] = authorization_letter.end_date
            
            # 预填充签约主体信息
            form.initial['party_a_name'] = authorization_letter.client_name
            form.initial['party_b_name'] = authorization_letter.trustee_name
            
            # 预填充项目编号（继承业务委托书的项目编号）
            if authorization_letter.project_number:
                form.initial['project_number'] = authorization_letter.project_number
    
    # 使用统一的上下文构建函数
    base_context = _context(
        '创建合同草稿',
        '➕',
        '创建新的业务合同',
        request=request,
        active_menu_id='contract_management_list',
    )
    
    from datetime import datetime
    import json
    # 从数据库获取我方单位列表（用于下拉选择）
    from backend.apps.system_management.models import OurCompany
    our_companies = OurCompany.objects.filter(is_active=True).order_by('order', 'id')
    # 如果没有配置，使用默认值（仅用于JavaScript兼容）
    our_units_list = list(our_companies.values_list('company_name', flat=True))
    if not our_units_list:
        our_units_list = [
            '四川维海科技有限公司',
            '重庆维海科技有限公司',
            '云南维海科技有限公司',
            '西安维海科技有限公司',
            '禾间成都建筑设计咨询有限公司',
            '成都宏天升荣科技有限公司',
        ]
    # 转换为JSON字符串供JavaScript使用（兼容旧代码）
    our_units = json.dumps(our_units_list, ensure_ascii=False)
    # 从后台引入服务内容相关选项
    from backend.apps.base_data.models import BusinessType, ServiceType, DesignStage, ServiceProfession
    from backend.apps.production_management.models import SettlementNodeType, AfterSalesNodeType
    business_types = BusinessType.objects.filter(is_active=True).order_by('order', 'id')
    service_types = ServiceType.objects.all().order_by('order', 'id')
    design_stages = DesignStage.objects.filter(is_active=True).order_by('order', 'id')
    service_professions = ServiceProfession.objects.all().order_by('service_type__order', 'order', 'id')
    settlement_node_types = SettlementNodeType.objects.filter(is_active=True).order_by('order', 'id')
    after_sales_node_types = AfterSalesNodeType.objects.filter(is_active=True).order_by('order', 'id')
    
    # 获取成果文件类型（用于服务内容的成果清单）
    result_file_types = ResultFileType.objects.filter(is_active=True).order_by('service_category', 'order', 'id')
    
    # 获取结算方式（用于价款信息）
    from backend.apps.settlement_management.models import SettlementMethod
    settlement_methods = SettlementMethod.objects.filter(is_active=True).order_by('sort_order', 'name')
    
    # 定义约定管辖选项
    GOVERNING_LAW_CHOICES = [
        ('party_a_location', '甲方所在地'),
        ('party_b_location', '乙方所在地'),
        ('project_location', '项目所在地'),
        ('not_specified', '未约定'),
        ('legal_default', '法定管辖'),
    ]
    
    # 获取客户列表（用于自动填充客户方信息）
    from backend.apps.customer_management.models import Client
    clients = Client.objects.filter(is_active=True).select_related('created_by', 'responsible_user', 'responsible_user__department').prefetch_related('contacts')
    # 应用权限过滤
    clients = _filter_clients_by_permission(clients, request.user, permission_set)
    clients = clients.order_by('name')
    
    # 获取项目经理列表
    from backend.apps.system_management.models import User
    project_managers = User.objects.filter(is_active=True).order_by('username')
    
    # 获取商务经理列表
    business_managers = User.objects.filter(is_active=True).order_by('username')
    
    base_context.update({
        'list_url_name': 'contract_pages:contract_management_list',
        'form': form,
        'clients': clients,
        'project_managers': project_managers,
        'business_managers': business_managers,
        'governing_law_choices': GOVERNING_LAW_CHOICES,
        'our_units': our_units,  # JSON字符串，用于JavaScript兼容
        'our_companies': our_companies,  # OurCompany对象列表，用于模板渲染
        'business_types': business_types,
        'service_types': service_types,
        'design_stages': design_stages,
        'service_professions': service_professions,
        'settlement_node_types': settlement_node_types,
        'after_sales_node_types': after_sales_node_types,
        'result_file_types': result_file_types,
        'settlement_methods': settlement_methods,
    })
    
    return render(request, "contract_management/contract_form.html", base_context)


@login_required

def contract_edit(request, contract_id):
    """
    编辑合同页面
    
    功能：
    - 编辑合同信息
    - 仅允许编辑草稿状态的合同
    - 权限检查（创建人或具有编辑权限）
    """
    import logging
    logger = logging.getLogger(__name__)
    
    contract = get_object_or_404(BusinessContract, id=contract_id)
    
    # 权限检查
    permission_set = get_user_permission_codes(request.user)
    can_edit = (
        contract.status == 'draft' and (
            contract.created_by == request.user or 
            _permission_granted('contract_management.contract.manage', permission_set)
        )
    )
    
    if not can_edit:
        messages.error(request, '您没有权限编辑此合同，或合同状态不允许编辑（仅草稿状态可编辑）')
        return redirect('contract_pages:contract_detail', contract_id=contract.id)
    
    if request.method == 'POST':
        # 处理表单提交
        try:
            from django.db import transaction
            from .forms import ContractForm
            form = ContractForm(request.POST, instance=contract, user=request.user, permission_set=permission_set)
            if form.is_valid():
                with transaction.atomic():
                    contract = form.save(commit=False)
                contract.save()
                
                messages.success(request, f'合同 {contract.contract_number} 更新成功。')
                
                messages.success(request, f'合同 {contract.contract_number} 更新成功。')
                return redirect('contract_pages:contract_detail', contract_id=contract.id)
            else:
                messages.error(request, '表单验证失败，请检查输入。')
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.exception('更新合同失败: %s', str(e))
            messages.error(request, f'更新合同失败：{str(e)}')
    else:
        from .forms import ContractForm
        form = ContractForm(instance=contract, user=request.user, permission_set=permission_set)
        
        # 设置责任部门和责任人员（系统自动填充，不可修改）
        if request.user.is_authenticated:
            # 责任部门：当前登录账号对应的部门
            if hasattr(request.user, 'department') and request.user.department:
                form.initial['responsible_department'] = request.user.department.name
            else:
                form.initial['responsible_department'] = '未设置部门'
            # 责任人员：当前登录账号对应的人员姓名
            form.initial['responsible_person'] = request.user.get_full_name() or request.user.username
    
    # 使用统一的上下文构建函数
    base_context = _context(
        f'编辑合同 - {contract.contract_number}',
        '✏️',
        '编辑合同信息',
        request=request,
        active_menu_id='contract_management_list',
    )
    
    from datetime import datetime
    import json
    # 从数据库获取我方单位列表（用于下拉选择）
    from backend.apps.system_management.models import OurCompany
    our_companies = OurCompany.objects.filter(is_active=True).order_by('order', 'id')
    # 如果没有配置，使用默认值（仅用于JavaScript兼容）
    our_units_list = list(our_companies.values_list('company_name', flat=True))
    if not our_units_list:
        our_units_list = [
            '四川维海科技有限公司',
            '重庆维海科技有限公司',
            '云南维海科技有限公司',
            '西安维海科技有限公司',
            '禾间成都建筑设计咨询有限公司',
            '成都宏天升荣科技有限公司',
        ]
    # 转换为JSON字符串供JavaScript使用（兼容旧代码）
    our_units = json.dumps(our_units_list, ensure_ascii=False)
    # 从后台引入服务内容相关选项
    from backend.apps.base_data.models import BusinessType, ServiceType, DesignStage, ServiceProfession
    from backend.apps.production_management.models import SettlementNodeType, AfterSalesNodeType
    business_types = BusinessType.objects.filter(is_active=True).order_by('order', 'id')
    service_types = ServiceType.objects.all().order_by('order', 'id')
    design_stages = DesignStage.objects.filter(is_active=True).order_by('order', 'id')
    service_professions = ServiceProfession.objects.all().order_by('service_type__order', 'order', 'id')
    settlement_node_types = SettlementNodeType.objects.filter(is_active=True).order_by('order', 'id')
    after_sales_node_types = AfterSalesNodeType.objects.filter(is_active=True).order_by('order', 'id')
    
    # 获取成果文件类型（用于服务内容的成果清单）
    result_file_types = ResultFileType.objects.filter(is_active=True).order_by('service_category', 'order', 'id')
    
    # 获取结算方式（用于价款信息）
    from backend.apps.settlement_management.models import SettlementMethod
    settlement_methods = SettlementMethod.objects.filter(is_active=True).order_by('sort_order', 'name')
    
    # 定义约定管辖选项
    GOVERNING_LAW_CHOICES = [
        ('party_a_location', '甲方所在地'),
        ('party_b_location', '乙方所在地'),
        ('project_location', '项目所在地'),
        ('not_specified', '未约定'),
        ('legal_default', '法定管辖'),
    ]
    
    # 获取客户列表（用于自动填充客户方信息）
    from backend.apps.customer_management.models import Client
    clients = Client.objects.filter(is_active=True).select_related('created_by', 'responsible_user', 'responsible_user__department').prefetch_related('contacts')
    # 应用权限过滤
    clients = _filter_clients_by_permission(clients, request.user, permission_set)
    clients = clients.order_by('name')
    
    # 获取项目经理列表
    from backend.apps.system_management.models import User
    project_managers = User.objects.filter(is_active=True).order_by('username')
    
    # 获取商务经理列表
    business_managers = User.objects.filter(is_active=True).order_by('username')
    
    base_context.update({
        'list_url_name': 'contract_pages:contract_management_list',
        'form': form,
        'contract': contract,
        'clients': clients,
        'project_managers': project_managers,
        'business_managers': business_managers,
        'governing_law_choices': GOVERNING_LAW_CHOICES,
        'our_units': our_units,  # JSON字符串，用于JavaScript兼容
        'our_companies': our_companies,  # OurCompany对象列表，用于模板渲染
        'business_types': business_types,
        'service_types': service_types,
        'design_stages': design_stages,
        'service_professions': service_professions,
        'settlement_node_types': settlement_node_types,
        'after_sales_node_types': after_sales_node_types,
        'result_file_types': result_file_types,
        'settlement_methods': settlement_methods,
    })
    
    return render(request, "contract_management/contract_form.html", base_context)


@login_required

def contract_delete(request, contract_id):
    """
    删除合同
    
    功能：
    - 仅允许删除草稿状态的合同
    - 检查关联数据，存在关联数据时不允许删除
    - 删除后重定向到合同管理列表
    """
    import logging
    logger = logging.getLogger(__name__)
    
    contract = get_object_or_404(BusinessContract, id=contract_id)
    
    # 权限检查：需要有合同管理权限
    permission_set = get_user_permission_codes(request.user)
    can_delete = (
        contract.status == 'draft' and (
            contract.created_by == request.user or 
            _permission_granted('contract_management.contract.manage', permission_set)
        )
    )
    
    if not can_delete:
        messages.error(request, '您没有权限删除此合同，或合同状态不允许删除（仅草稿状态可删除）')
        return redirect('contract_pages:contract_detail', contract_id=contract.id)
    
    if request.method == 'POST':
        try:
            # 检查关联关系
            has_sub_contracts = contract.sub_contracts.exists()
            has_payment_plans = contract.payment_plans.exists()
            
            if has_sub_contracts or has_payment_plans:
                error_msg = '无法删除合同，存在以下关联数据：'
                if has_sub_contracts:
                    error_msg += '子合同、'
                if has_payment_plans:
                    error_msg += '回款计划、'
                error_msg = error_msg.rstrip('、')
                messages.error(request, error_msg)
                return redirect('contract_pages:contract_detail', contract_id=contract.id)
            
            contract_number = contract.contract_number
            contract.delete()
            messages.success(request, f'合同 {contract_number} 已删除')
            return redirect('contract_pages:contract_management_list')
        except Exception as e:
            logger.exception('删除合同失败: %s', str(e))
            messages.error(request, f'删除合同失败：{str(e)}')
    
    return redirect('contract_pages:contract_detail', contract_id=contract.id)


@login_required

def contract_submit_approval(request, contract_id):
    """提交合同审批"""
    contract = get_object_or_404(BusinessContract, id=contract_id)
    permission_set = get_user_permission_codes(request.user)
    
    # 权限检查
    if not _check_customer_permission('contract_management.client.edit', permission_set):
        messages.error(request, '您没有权限提交合同审批')
        return redirect('contract_pages:contract_detail', contract_id=contract_id)
    
    # 状态检查：只有草稿或待审核状态的合同才能提交审批
    if contract.status not in ['draft', 'pending_review']:
        messages.error(request, f'合同状态为{contract.get_status_display()}，无法提交审批')
        return redirect('contract_pages:contract_detail', contract_id=contract_id)
    
    if request.method == 'POST':
        try:
            from backend.apps.contract_management.services import ContractApprovalService
            
            # 使用审批服务提交审批
            service = ContractApprovalService()
            comment = request.POST.get('comment', f'申请审批合同：{contract.contract_number} - {contract.contract_name}')
            instance = service.submit_approval(
                obj=contract,
                applicant=request.user,
                comment=comment
            )
            
            if not instance:
                messages.error(request, '合同审批流程未配置，请联系管理员')
                return redirect('contract_pages:contract_detail', contract_id=contract_id)
            
            # 更新合同状态为待审核
            if contract.status == 'draft':
                contract.status = 'pending_review'
                contract.save()
            
            messages.success(request, f'合同审批已提交（审批编号：{instance.instance_number}）')
            return redirect('contract_pages:contract_detail', contract_id=contract_id)
            
        except ValueError as e:
            messages.error(request, f'提交审批失败：{str(e)}')
            return redirect('contract_pages:contract_detail', contract_id=contract_id)
        except Exception as e:
            logger.exception('提交合同审批失败: %s', str(e))
            messages.error(request, f'提交合同审批失败：{str(e)}')
            return redirect('contract_pages:contract_detail', contract_id=contract_id)
    
    # GET 请求，显示提交审批确认页面
    from backend.apps.contract_management.services import ContractApprovalService
    from backend.apps.workflow_engine.models import ApprovalInstance
    
    # 检查是否已有正在进行的审批
    service = ContractApprovalService()
    instance = service.get_approval_instance(contract)
    existing_instance = instance if instance and instance.status in ['pending', 'in_progress'] else None
    
    # 使用统一的上下文构建函数
    base_context = _context(
        f'提交审批 - {contract.contract_number}',
        '📋',
        '提交合同审批流程',
        request=request,
        active_menu_id='contract_management_list',
    )
    
    base_context.update({
        'contract': contract,
        'existing_instance': existing_instance,
    })
    
    return render(request, "contract_management/contract_submit_approval.html", base_context)


@login_required

def contract_dispute_list(request):
    """
    合同争议列表页面
    
    功能：
    - 显示合同争议状态的合同（状态为dispute）
    - 支持筛选和搜索
    - 支持分页显示
    """
    import logging
    from django.core.paginator import Paginator
    
    logger = logging.getLogger(__name__)
    
    # 权限检查
    permission_set = get_user_permission_codes(request.user)
    if not _permission_granted('contract_management.client.view', permission_set):
        messages.error(request, '您没有权限访问合同争议')
        return redirect('contract_pages:contract_management_list')
    
    # 获取筛选参数
    filters = {
        'search': request.GET.get('search', ''),
        'contract_type': request.GET.get('contract_type', ''),
        'client_id': request.GET.get('client_id', ''),
        'project_id': request.GET.get('project_id', ''),
        'date_from': request.GET.get('date_from', ''),
        'date_to': request.GET.get('date_to', ''),
    }
    
    # 获取合同争议状态的合同列表
    try:
        contracts = BusinessContract.objects.filter(
            status='dispute'
        ).select_related('client', 'project', 'created_by').order_by('-created_time')
        
        # 应用筛选条件
        contracts = _apply_contract_filters(contracts, filters)
        
        # 分页
        paginator = Paginator(contracts, 13)
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)
    except Exception as e:
        logger.exception('获取合同争议列表失败: %s', str(e))
        messages.error(request, f'获取合同争议列表失败：{str(e)}')
        page_obj = None
    
    # 统计信息
    try:
        total_count = BusinessContract.objects.filter(status='dispute').count()
        summary_cards = []
    except Exception as e:
        logger.exception('获取统计信息失败: %s', str(e))
        summary_cards = []
    
    # 检查创建权限
    can_create = _permission_granted('contract_management.client.create', permission_set)
    
    # 获取筛选选项
    try:
        clients = Client.objects.filter(is_active=True).order_by('name')[:100]
    except Exception as e:
        logger.exception('获取客户列表失败: %s', str(e))
        clients = []
    
    # 获取项目选项
    try:
        contract_project_ids = BusinessContract.objects.filter(
            status='dispute',
            project__isnull=False
        ).values_list('project_id', flat=True).distinct()[:50]
        projects = Project.objects.filter(id__in=contract_project_ids).order_by('name')[:50]
    except Exception as e:
        logger.exception('获取项目列表失败: %s', str(e))
        projects = []
    
    # 获取类型选项
    try:
        type_choices = BusinessContract.CONTRACT_TYPE_CHOICES
    except AttributeError as e:
        logger.exception('获取合同类型选项失败: %s', str(e))
        type_choices = []
    
    context = _context(
        "合同争议",
        "⚖️",
        "管理处于争议状态的合同",
        summary_cards=summary_cards,
        request=request,
        active_menu_id='contract_dispute_list',
    )
    
    context.update({
        'page_obj': page_obj,
        'clients': clients,
        'projects': projects,
        'type_choices': type_choices,
        'search': filters['search'],
        'selected_type': filters['contract_type'],
        'selected_client_id': filters['client_id'],
        'selected_project_id': filters['project_id'],
        'date_from': filters['date_from'],
        'date_to': filters['date_to'],
        'can_create': can_create,
        'show_filter_fields_settings_btn': True,
    })
    
    return render(request, "contract_management/contract_list.html", context)


@login_required

def contract_finalize_list(request):
    """
    合同定稿列表页面
    
    功能：
    - 显示合同定稿状态的合同（状态为finalized）
    - 支持筛选和搜索
    - 支持分页显示
    """
    import logging
    from django.core.paginator import Paginator
    
    logger = logging.getLogger(__name__)
    
    # 权限检查
    permission_set = get_user_permission_codes(request.user)
    if not _permission_granted('contract_management.client.view', permission_set):
        messages.error(request, '您没有权限访问合同定稿')
        return redirect('contract_pages:contract_management_list')
    
    # 获取筛选参数
    filters = {
        'search': request.GET.get('search', ''),
        'contract_type': request.GET.get('contract_type', ''),
        'client_id': request.GET.get('client_id', ''),
        'project_id': request.GET.get('project_id', ''),
        'date_from': request.GET.get('date_from', ''),
        'date_to': request.GET.get('date_to', ''),
    }
    
    # 获取合同定稿状态的合同列表
    try:
        contracts = BusinessContract.objects.filter(
            status='finalized'
        ).select_related('client', 'project', 'created_by').order_by('-created_time')
        
        # 应用筛选条件
        contracts = _apply_contract_filters(contracts, filters)
        
        # 分页
        paginator = Paginator(contracts, 13)
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)
    except Exception as e:
        logger.exception('获取合同定稿列表失败: %s', str(e))
        messages.error(request, f'获取合同定稿列表失败：{str(e)}')
        page_obj = None
    
    # 统计信息
    try:
        total_count = BusinessContract.objects.filter(status='finalized').count()
        summary_cards = []
    except Exception as e:
        logger.exception('获取统计信息失败: %s', str(e))
        summary_cards = []
    
    # 检查创建权限
    can_create = _permission_granted('contract_management.client.create', permission_set)
    
    # 获取筛选选项
    try:
        clients = Client.objects.filter(is_active=True).order_by('name')[:100]
    except Exception as e:
        logger.exception('获取客户列表失败: %s', str(e))
        clients = []
    
    # 获取项目选项
    try:
        contract_project_ids = BusinessContract.objects.filter(
            status='finalized',
            project__isnull=False
        ).values_list('project_id', flat=True).distinct()[:50]
        projects = Project.objects.filter(id__in=contract_project_ids).order_by('name')[:50]
    except Exception as e:
        logger.exception('获取项目列表失败: %s', str(e))
        projects = []
    
    # 获取类型选项
    try:
        type_choices = BusinessContract.CONTRACT_TYPE_CHOICES
    except AttributeError as e:
        logger.exception('获取合同类型选项失败: %s', str(e))
        type_choices = []
    
    context = _context(
        "合同定稿",
        "📝",
        "管理已定稿的合同（创建流程第三步）",
        summary_cards=summary_cards,
        request=request,
        active_menu_id='contract_finalize_list',
    )
    
    context.update({
        'page_obj': page_obj,
        'clients': clients,
        'projects': projects,
        'type_choices': type_choices,
        'search': filters['search'],
        'selected_type': filters['contract_type'],
        'selected_client_id': filters['client_id'],
        'selected_project_id': filters['project_id'],
        'date_from': filters['date_from'],
        'date_to': filters['date_to'],
        'can_create': can_create,
        'show_filter_fields_settings_btn': True,
    })
    
    return render(request, "contract_management/contract_list.html", context)


@login_required

def contract_negotiation_create(request):
    """
    创建合同洽谈记录页面
    
    功能：
    - 创建新的合同洽谈记录
    - 记录洽谈内容、参与人员、时间等信息
    - 关联到具体合同
    """
    import logging
    from .forms import ContractNegotiationForm
    
    logger = logging.getLogger(__name__)
    
    # 权限检查
    permission_set = get_user_permission_codes(request.user)
    if not _permission_granted('contract_management.client.create', permission_set):
        messages.error(request, '您没有权限创建合同洽谈记录')
        return redirect('contract_pages:contract_management_list')
    
    # 获取关联合同ID（如果从合同详情页跳转）
    contract_id = request.GET.get('contract_id')
    contract = None
    if contract_id:
        try:
            contract = BusinessContract.objects.get(id=contract_id)
        except BusinessContract.DoesNotExist:
            messages.warning(request, '关联的合同不存在')
    
    if request.method == 'POST':
        # 处理表单提交
        try:
            form = ContractNegotiationForm(request.POST, user=request.user)
            if form.is_valid():
                negotiation = form.save(commit=False)
                negotiation.created_by = request.user
                
                # 如果从合同详情页跳转，自动关联合同
                if contract and not negotiation.contract:
                    negotiation.contract = contract
                
                # 如果关联了合同，自动填充客户
                if negotiation.contract and negotiation.contract.client:
                    negotiation.client = negotiation.contract.client
                
                negotiation.save()
                form.save_m2m()  # 保存多对多关系（参与人员）
                
                messages.success(request, '合同洽谈记录创建成功')
                
                # 根据来源决定跳转页面
                if contract:
                    return redirect('contract_pages:contract_detail', contract_id=contract.id)
                else:
                    return redirect('contract_pages:contract_management_list')
            else:
                messages.error(request, '表单验证失败，请检查输入。')
        except Exception as e:
            logger.exception('创建合同洽谈记录失败: %s', str(e))
            messages.error(request, f'创建合同洽谈记录失败：{str(e)}')
    else:
        # GET请求，显示创建页面
        form = ContractNegotiationForm(user=request.user)
        
        # 如果从合同详情页跳转，预填充合同信息
        if contract:
            form.fields['contract'].initial = contract
            if contract.client:
                form.fields['client'].initial = contract.client
            if contract.project:
                form.fields['project'].initial = contract.project
        
        # 默认参与人员包含当前用户
        form.fields['participants'].initial = [request.user.id]
    
    context = _context(
        '创建合同洽谈记录',
        '💬',
        '记录合同洽谈过程中的关键信息',
        request=request,
        active_menu_id='contract_negotiation_create',
    )
    
    context.update({
        'form': form,
        'contract': contract,
    })
    
    return render(request, "contract_management/contract_negotiation_form.html", context)


@login_required

def contract_negotiation_list(request):
    """
    合同洽谈记录列表页面
    
    功能：
    - 显示所有合同洽谈记录
    - 支持筛选和搜索
    - 支持分页显示
    """
    import logging
    from django.core.paginator import Paginator
    from django.db.models import Q
    
    logger = logging.getLogger(__name__)
    
    # 权限检查
    permission_set = get_user_permission_codes(request.user)
    if not _permission_granted('contract_management.client.view', permission_set):
        messages.error(request, '您没有权限访问合同洽谈记录')
        return redirect('contract_pages:contract_management_list')
    
    # 获取筛选参数
    filters = {
        'search': request.GET.get('search', ''),
        'negotiation_type': request.GET.get('negotiation_type', ''),
        'status': request.GET.get('status', ''),
        'client_id': request.GET.get('client_id', ''),
        'contract_id': request.GET.get('contract_id', ''),
        'date_from': request.GET.get('date_from', ''),
        'date_to': request.GET.get('date_to', ''),
    }
    
    # 获取洽谈记录列表
    try:
        negotiations = ContractNegotiation.objects.select_related(
            'contract', 'client', 'project', 'created_by'
        ).prefetch_related('participants').order_by('-negotiation_date', '-created_time')
        
        # 应用筛选条件
        if filters['search']:
            search = filters['search']
            negotiations = negotiations.filter(
                Q(title__icontains=search) |
                Q(content__icontains=search) |
                Q(negotiation_number__icontains=search) |
                Q(client__name__icontains=search) |
                Q(contract__contract_number__icontains=search)
            )
        
        if filters['negotiation_type']:
            negotiations = negotiations.filter(negotiation_type=filters['negotiation_type'])
        
        if filters['status']:
            negotiations = negotiations.filter(status=filters['status'])
        
        if filters['client_id']:
            negotiations = negotiations.filter(client_id=filters['client_id'])
        
        if filters['contract_id']:
            negotiations = negotiations.filter(contract_id=filters['contract_id'])
        
        if filters['date_from']:
            negotiations = negotiations.filter(negotiation_date__gte=filters['date_from'])
        
        if filters['date_to']:
            negotiations = negotiations.filter(negotiation_date__lte=filters['date_to'])
        
        # 分页
        paginator = Paginator(negotiations, 13)
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)
    except Exception as e:
        logger.exception('获取合同洽谈记录列表失败: %s', str(e))
        messages.error(request, f'获取合同洽谈记录列表失败：{str(e)}')
        page_obj = None
    
    # 统计信息
    try:
        total_count = ContractNegotiation.objects.count()
        ongoing_count = ContractNegotiation.objects.filter(status='ongoing').count()
        completed_count = ContractNegotiation.objects.filter(status='completed').count()
        summary_cards = []
    except Exception as e:
        logger.exception('获取统计信息失败: %s', str(e))
        summary_cards = []
    
    # 检查创建权限
    can_create = _permission_granted('contract_management.client.create', permission_set)
    
    # 获取筛选选项
    try:
        clients = Client.objects.filter(is_active=True).order_by('name')[:100]
    except Exception as e:
        logger.exception('获取客户列表失败: %s', str(e))
        clients = []
    
    # 获取合同选项
    contracts = []
    try:
        contract_ids = ContractNegotiation.objects.filter(
            contract__isnull=False
        ).values_list('contract_id', flat=True).distinct()[:50]
        if contract_ids:
            contracts = BusinessContract.objects.filter(
                id__in=contract_ids
            ).order_by('-created_time')[:50]
    except Exception as e:
        logger.exception('获取合同列表失败: %s', str(e))
        contracts = []
    
    # 获取类型选项
    type_choices = ContractNegotiation.NEGOTIATION_TYPE_CHOICES
    status_choices = ContractNegotiation.STATUS_CHOICES
    
    context = _context(
        "合同洽谈记录",
        "💬",
        "管理所有合同洽谈记录",
        summary_cards=summary_cards,
        request=request,
        active_menu_id='contract_negotiation_create',
    )
    
    context.update({
        'page_obj': page_obj,
        'clients': clients,
        'contracts': contracts,
        'type_choices': type_choices,
        'status_choices': status_choices,
        'search': filters['search'],
        'selected_type': filters['negotiation_type'],
        'selected_status': filters['status'],
        'selected_client_id': filters['client_id'],
        'selected_contract_id': filters['contract_id'],
        'date_from': filters['date_from'],
        'date_to': filters['date_to'],
        'can_create': can_create,
        'show_filter_fields_settings_btn': True,
    })
    
    return render(request, "contract_management/contract_negotiation_list.html", context)


@login_required

def contract_negotiation_detail(request, negotiation_id):
    """
    合同洽谈记录详情页面
    """
    import logging
    
    logger = logging.getLogger(__name__)
    
    # 权限检查
    permission_set = get_user_permission_codes(request.user)
    if not _permission_granted('contract_management.client.view', permission_set):
        messages.error(request, '您没有权限查看合同洽谈记录')
        return redirect('contract_pages:contract_negotiation_list')
    
    negotiation = get_object_or_404(
        ContractNegotiation.objects.select_related(
            'contract', 'client', 'project', 'created_by'
        ).prefetch_related('participants'),
        id=negotiation_id
    )
    
    # 检查编辑权限
    can_edit = (
        negotiation.created_by == request.user or
        _permission_granted('contract_management.client.edit', permission_set)
    )
    
    context = _context(
        f'合同洽谈记录详情 - {negotiation.title}',
        '💬',
        '查看合同洽谈记录的详细信息',
        request=request,
        active_menu_id='contract_negotiation_create',
    )
    
    context.update({
        'negotiation': negotiation,
        'can_edit': can_edit,
    })
    
    return render(request, "contract_management/contract_negotiation_detail.html", context)


@login_required

def contract_finalize_create(request):
    """
    创建合同定稿页面
    
    功能：
    - 创建新合同并直接设置为定稿状态
    - 或者从现有合同创建定稿版本
    - 支持从业务委托书转换创建
    """
    import logging
    logger = logging.getLogger(__name__)
    
    # 权限检查
    permission_set = get_user_permission_codes(request.user)
    if not _permission_granted('contract_management.client.create', permission_set):
        messages.error(request, '您没有权限创建合同定稿')
        return redirect('contract_pages:contract_finalize_list')
    
    # 检查是否从业务委托书转换而来
    authorization_letter_id = request.GET.get('authorization_letter')
    authorization_letter = None
    if authorization_letter_id:
        try:
            authorization_letter = AuthorizationLetter.objects.get(id=authorization_letter_id)
            if not authorization_letter.can_convert_to_contract():
                messages.warning(request, '只有已确认状态的委托书可以转换为合同')
                authorization_letter = None
        except AuthorizationLetter.DoesNotExist:
            pass
    
    # 检查是否从现有合同创建定稿
    contract_id = request.GET.get('contract_id')
    source_contract = None
    if contract_id:
        try:
            source_contract = BusinessContract.objects.get(id=contract_id)
        except BusinessContract.DoesNotExist:
            messages.warning(request, '源合同不存在')
    
    if request.method == 'POST':
        # 处理表单提交
        try:
            from django.db import transaction
            from .forms import ContractForm
            form = ContractForm(request.POST, user=request.user, permission_set=permission_set)
            if form.is_valid():
                with transaction.atomic():
                    contract = form.save(commit=False)
                    contract.created_by = request.user
                    
                    # 合同定稿流程：直接设置为定稿状态
                    contract.status = 'finalized'
                
                # 如果是从委托书转换而来，继承项目编号
                if authorization_letter_id:
                    try:
                        letter = AuthorizationLetter.objects.get(id=authorization_letter_id)
                        if letter.project_number:
                            contract.project_number = letter.project_number
                        contract.save()
                        messages.success(request, f'合同定稿创建成功（从委托书转换），已进入定稿状态。')
                    except AuthorizationLetter.DoesNotExist:
                        contract.save()
                        messages.success(request, f'合同定稿创建成功，已进入定稿状态。')
                elif source_contract:
                    # 从现有合同创建定稿版本
                    contract.save()
                    messages.success(request, f'合同定稿创建成功，已进入定稿状态。')
                else:
                    contract.save()
                    messages.success(request, f'合同定稿创建成功，已进入定稿状态。')
                
                try:
                    from decimal import Decimal
                    import re
                    
                    # 先删除所有旧的结算方案（重新创建）
                    for key, value in request.POST.items():
                        pass
                except Exception as e:
                    # 如果保存结算方案失败，记录错误但不影响合同创建
                    logger.warning(f'保存结算方案失败: {str(e)}')
                
                # 创建成功后跳转到合同定稿列表页面
                return redirect('contract_pages:contract_finalize_list')
            else:
                messages.error(request, '表单验证失败，请检查输入。')
        except Exception as e:
            logger.exception('创建合同定稿失败: %s', str(e))
            messages.error(request, f'创建合同定稿失败：{str(e)}')
    else:
        from .forms import ContractForm
        form = ContractForm(user=request.user, permission_set=permission_set)
        
        # 设置责任部门和责任人员（系统自动填充，不可修改）
        if request.user.is_authenticated:
            # 责任部门：当前登录账号对应的部门
            if hasattr(request.user, 'department') and request.user.department:
                form.initial['responsible_department'] = request.user.department.name
            else:
                form.initial['responsible_department'] = '未设置部门'
            # 责任人员：当前登录账号对应的人员姓名
            form.initial['responsible_person'] = request.user.get_full_name() or request.user.username
        
        # 合同定稿流程：默认状态为"合同定稿"
        form.initial['status'] = 'finalized'
        
        # 如果是从委托书转换而来，预填充表单
        if authorization_letter:
            if authorization_letter.project:
                form.fields['project'].initial = authorization_letter.project
            if authorization_letter.opportunity and authorization_letter.opportunity.client:
                try:
                    client = Client.objects.get(name=authorization_letter.client_name)
                    form.fields['client'].initial = client
                except Client.DoesNotExist:
                    pass
            
            if not form.initial.get('contract_name'):
                form.initial['contract_name'] = f"{authorization_letter.project_name} - 服务合同"
            
            if authorization_letter.provisional_price:
                form.initial['contract_amount'] = authorization_letter.provisional_price
            
            if authorization_letter.letter_date:
                form.initial['contract_date'] = authorization_letter.letter_date
                form.initial['effective_date'] = authorization_letter.letter_date
                if authorization_letter.start_date:
                    form.initial['start_date'] = authorization_letter.start_date
                if authorization_letter.end_date:
                    form.initial['end_date'] = authorization_letter.end_date
            
            form.initial['party_a_name'] = authorization_letter.client_name
            form.initial['party_b_name'] = authorization_letter.trustee_name
            
            if authorization_letter.project_number:
                form.initial['project_number'] = authorization_letter.project_number
        
        # 如果是从现有合同创建定稿，预填充表单
        if source_contract:
            form.initial['client'] = source_contract.client
            form.initial['project'] = source_contract.project
            form.initial['contract_name'] = source_contract.contract_name
            form.initial['contract_amount'] = source_contract.contract_amount
            form.initial['contract_date'] = source_contract.contract_date
            form.initial['effective_date'] = source_contract.effective_date
            form.initial['start_date'] = source_contract.start_date
            form.initial['end_date'] = source_contract.end_date
            form.initial['project_number'] = source_contract.project_number
    
    base_context = _context(
        '创建合同定稿',
        '✅',
        '创建新的合同定稿，直接进入定稿状态',
        request=request,
        active_menu_id='contract_finalize_create',
    )
    
    from datetime import datetime
    from backend.apps.system_management.models import OurCompany
    our_units = list(OurCompany.objects.filter(is_active=True).order_by('order', 'id').values_list('company_name', flat=True))
    if not our_units:
        our_units = [
            '四川维海科技有限公司',
            '重庆维海科技有限公司',
            '云南维海科技有限公司',
            '西安维海科技有限公司',
            '禾间成都建筑设计咨询有限公司',
            '成都宏天升荣科技有限公司',
        ]
    
    base_context.update({
        'list_url_name': 'contract_pages:contract_management_list',
        'form': form,
        'authorization_letter': authorization_letter,
        'source_contract': source_contract,
        'is_finalize_create': True,  # 标记这是合同定稿创建页面
        'current_year': datetime.now().year,
        'our_units': our_units,
    })
    
    return render(request, "contract_management/contract_form.html", base_context)


@login_required

def contract_performance_track(request):
    """
    履约跟踪页面
    
    功能：
    - 显示执行中的合同列表
    - 跟踪合同履约情况
    - 显示履约进度和关键指标
    """
    import logging
    from django.core.paginator import Paginator
    from django.db.models import Sum, Q
    from django.utils import timezone
    from datetime import timedelta
    
    logger = logging.getLogger(__name__)
    
    # 权限检查
    permission_set = get_user_permission_codes(request.user)
    if not _permission_granted('contract_management.client.view', permission_set):
        messages.error(request, '您没有权限访问履约跟踪')
        return redirect('contract_pages:contract_management_list')
    
    # 获取筛选参数
    filters = {
        'search': request.GET.get('search', ''),
        'contract_type': request.GET.get('contract_type', ''),
        'client_id': request.GET.get('client_id', ''),
    }
    
    # 获取执行中的合同列表
    try:
        contracts = BusinessContract.objects.filter(
            status__in=['executing', 'effective']
        ).select_related('client', 'project', 'created_by').order_by('-start_date', '-created_time')
        
        # 应用筛选条件
        contracts = _apply_contract_filters(contracts, filters)
        
        # 分页
        paginator = Paginator(contracts, 13)
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)
    except Exception as e:
        logger.exception('获取履约跟踪列表失败: %s', str(e))
        messages.error(request, f'获取履约跟踪列表失败：{str(e)}')
        page_obj = None
    
    # 统计信息
    try:
        executing_count = BusinessContract.objects.filter(status='executing').count()
        effective_count = BusinessContract.objects.filter(status='effective').count()
        total_count = executing_count + effective_count
        
        # 计算履约率（已回款/合同金额）
        total_amount = BusinessContract.objects.filter(
            status__in=['executing', 'effective']
        ).aggregate(total=Sum('contract_amount'))['total'] or 0
        total_payment = BusinessContract.objects.filter(
            status__in=['executing', 'effective']
        ).aggregate(total=Sum('payment_amount'))['total'] or 0
        performance_rate = (total_payment / total_amount * 100) if total_amount > 0 else 0
        
        summary_cards = []
    except Exception as e:
        logger.exception('获取统计信息失败: %s', str(e))
        summary_cards = []
    
    # 检查创建权限
    can_create = _permission_granted('contract_management.client.create', permission_set)
    
    # 获取筛选选项
    try:
        clients = Client.objects.filter(is_active=True).order_by('name')[:100]
    except Exception as e:
        logger.exception('获取客户列表失败: %s', str(e))
        clients = []
    
    # 获取类型选项
    try:
        type_choices = BusinessContract.CONTRACT_TYPE_CHOICES
    except AttributeError as e:
        logger.exception('获取合同类型选项失败: %s', str(e))
        type_choices = []
    
    context = _context(
        "履约跟踪",
        "📋",
        "跟踪合同履约情况和执行进度",
        summary_cards=summary_cards,
        request=request,
        active_menu_id='contract_performance',
    )
    
    context.update({
        'page_obj': page_obj,
        'clients': clients,
        'type_choices': type_choices,
        'search': filters['search'],
        'selected_type': filters['contract_type'],
        'selected_client_id': filters['client_id'],
        'can_create': can_create,
        'show_filter_fields_settings_btn': True,
    })
    
    return render(request, "contract_management/contract_list.html", context)


@login_required

def contract_expiry_reminder(request):
    """
    到期提醒页面
    
    功能：
    - 显示即将到期的合同
    - 支持设置提醒天数
    - 显示到期时间倒计时
    """
    import logging
    from django.core.paginator import Paginator
    from django.utils import timezone
    from datetime import timedelta
    
    logger = logging.getLogger(__name__)
    
    # 权限检查
    permission_set = get_user_permission_codes(request.user)
    if not _permission_granted('contract_management.client.view', permission_set):
        messages.error(request, '您没有权限访问到期提醒')
        return redirect('contract_pages:contract_management_list')
    
    # 获取提醒天数（默认30天）
    days_ahead = int(request.GET.get('days', 30))
    
    # 计算到期日期范围
    today = timezone.now().date()
    expiry_date = today + timedelta(days=days_ahead)
    
    # 获取筛选参数
    filters = {
        'search': request.GET.get('search', ''),
        'contract_type': request.GET.get('contract_type', ''),
    }
    
    # 获取即将到期的合同列表
    try:
        contracts = BusinessContract.objects.filter(
            status__in=['executing', 'effective'],
            end_date__isnull=False,
            end_date__lte=expiry_date,
            end_date__gte=today
        ).select_related('client', 'project', 'created_by').order_by('end_date')
        
        # 应用筛选条件
        contracts = _apply_contract_filters(contracts, filters)
        
        # 分页
        paginator = Paginator(contracts, 13)
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)
    except Exception as e:
        logger.exception('获取到期提醒列表失败: %s', str(e))
        messages.error(request, f'获取到期提醒列表失败：{str(e)}')
        page_obj = None
    
    # 统计信息
    try:
        total_count = BusinessContract.objects.filter(
            status__in=['executing', 'effective'],
            end_date__isnull=False,
            end_date__lte=expiry_date,
            end_date__gte=today
        ).count()
        
        # 按到期时间分组统计
        expired_soon = BusinessContract.objects.filter(
            status__in=['executing', 'effective'],
            end_date__isnull=False,
            end_date__lte=today + timedelta(days=7),
            end_date__gte=today
        ).count()
        
        expired_this_month = BusinessContract.objects.filter(
            status__in=['executing', 'effective'],
            end_date__isnull=False,
            end_date__lte=today + timedelta(days=30),
            end_date__gte=today + timedelta(days=7)
        ).count()
        
        summary_cards = []
    except Exception as e:
        logger.exception('获取统计信息失败: %s', str(e))
        summary_cards = []
    
    # 获取类型选项
    try:
        type_choices = BusinessContract.CONTRACT_TYPE_CHOICES
    except AttributeError as e:
        logger.exception('获取合同类型选项失败: %s', str(e))
        type_choices = []
    
    context = _context(
        "到期提醒",
        "📅",
        f"提醒未来{days_ahead}天内到期的合同",
        summary_cards=summary_cards,
        request=request,
        active_menu_id='contract_expiry_reminder',
    )
    
    context.update({
        'page_obj': page_obj,
        'type_choices': type_choices,
        'search': filters['search'],
        'selected_type': filters['contract_type'],
        'days_ahead': days_ahead,
        'show_filter_fields_settings_btn': True,
    })
    
    return render(request, "contract_management/contract_list.html", context)


@login_required

def contract_payment_reminder(request):
    """
    付款提醒页面
    
    功能：
    - 显示需要付款的合同
    - 跟踪回款进度
    - 显示逾期未回款合同
    """
    import logging
    from django.core.paginator import Paginator
    from django.db.models import Q, F
    from django.utils import timezone
    from datetime import timedelta
    
    logger = logging.getLogger(__name__)
    
    # 权限检查
    permission_set = get_user_permission_codes(request.user)
    if not _permission_granted('contract_management.client.view', permission_set):
        messages.error(request, '您没有权限访问付款提醒')
        return redirect('contract_pages:contract_management_list')
    
    # 获取筛选参数
    filters = {
        'search': request.GET.get('search', ''),
        'contract_type': request.GET.get('contract_type', ''),
        'overdue_only': request.GET.get('overdue_only', ''),
    }
    
    # 获取需要付款的合同列表（有未回款金额的合同）
    try:
        contracts = BusinessContract.objects.filter(
            status__in=['executing', 'effective', 'signed'],
            contract_amount__gt=0
        ).select_related('client', 'project', 'created_by').order_by('-contract_date')
        
        # 计算未回款金额
        contracts = contracts.annotate(
            unpaid=F('contract_amount') - F('payment_amount')
        ).filter(unpaid__gt=0)
        
        # 应用筛选条件
        contracts = _apply_contract_filters(contracts, filters)
        
        # 如果只显示逾期合同
        if filters['overdue_only']:
            # 获取有回款计划的合同，检查是否有逾期
            from backend.apps.production_management.models import BusinessPaymentPlan
            overdue_contract_ids = BusinessPaymentPlan.objects.filter(
                planned_date__lt=timezone.now().date(),
                actual_payment_date__isnull=True
            ).values_list('contract_id', flat=True).distinct()
            contracts = contracts.filter(id__in=overdue_contract_ids)
        
        # 分页
        paginator = Paginator(contracts, 13)
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)
    except Exception as e:
        logger.exception('获取付款提醒列表失败: %s', str(e))
        messages.error(request, f'获取付款提醒列表失败：{str(e)}')
        page_obj = None
    
    # 统计信息
    try:
        from django.db.models import Sum, ExpressionWrapper, DecimalField
        # 计算待回款总额
        contracts_with_unpaid = BusinessContract.objects.filter(
            status__in=['executing', 'effective', 'signed'],
            contract_amount__gt=0
        ).annotate(
            unpaid=ExpressionWrapper(F('contract_amount') - F('payment_amount'), output_field=DecimalField())
        ).filter(unpaid__gt=0)
        
        total_unpaid = contracts_with_unpaid.aggregate(total=Sum('unpaid'))['total'] or 0
        unpaid_count = contracts_with_unpaid.count()
        
        # 计算逾期合同数量
        from backend.apps.production_management.models import BusinessPaymentPlan
        overdue_count = BusinessPaymentPlan.objects.filter(
            planned_date__lt=timezone.now().date(),
            actual_payment_date__isnull=True
        ).values('contract').distinct().count()
        
        summary_cards = []
    except Exception as e:
        logger.exception('获取统计信息失败: %s', str(e))
        summary_cards = []
    
    # 获取类型选项
    try:
        type_choices = BusinessContract.CONTRACT_TYPE_CHOICES
    except AttributeError as e:
        logger.exception('获取合同类型选项失败: %s', str(e))
        type_choices = []
    
    context = _context(
        "付款提醒",
        "💰",
        "跟踪合同回款情况和付款提醒",
        summary_cards=summary_cards,
        request=request,
        active_menu_id='contract_payment_reminder',
    )
    
    context.update({
        'page_obj': page_obj,
        'type_choices': type_choices,
        'search': filters['search'],
        'selected_type': filters['contract_type'],
        'overdue_only': filters['overdue_only'],
        'show_filter_fields_settings_btn': True,
    })
    
    return render(request, "contract_management/contract_list.html", context)


@login_required

def contract_risk_warning(request):
    """
    风险预警页面
    
    功能：
    - 显示有风险的合同
    - 识别各种风险类型（逾期、金额异常、状态异常等）
    - 提供风险等级评估
    """
    import logging
    from django.core.paginator import Paginator
    from django.db.models import Q, F
    from django.utils import timezone
    from datetime import timedelta
    
    logger = logging.getLogger(__name__)
    
    # 权限检查
    permission_set = get_user_permission_codes(request.user)
    if not _permission_granted('contract_management.client.view', permission_set):
        messages.error(request, '您没有权限访问风险预警')
        return redirect('contract_pages:contract_management_list')
    
    # 获取筛选参数
    filters = {
        'search': request.GET.get('search', ''),
        'risk_type': request.GET.get('risk_type', ''),
    }
    
    # 识别有风险的合同
    try:
        today = timezone.now().date()
        
        # 高风险：已到期但未完成
        high_risk = BusinessContract.objects.filter(
            Q(status__in=['executing', 'effective']) &
            Q(end_date__lt=today)
        )
        
        # 中风险：即将到期（30天内）
        medium_risk = BusinessContract.objects.filter(
            Q(status__in=['executing', 'effective']) &
            Q(end_date__gte=today) &
            Q(end_date__lte=today + timedelta(days=30))
        )
        
        # 低风险：回款异常（未回款金额超过合同金额的50%）
        from django.db.models import ExpressionWrapper, DecimalField, Case, When, Value
        low_risk = BusinessContract.objects.filter(
            Q(status__in=['executing', 'effective', 'signed']) &
            Q(contract_amount__gt=0)
        ).annotate(
            unpaid=ExpressionWrapper(F('contract_amount') - F('payment_amount'), output_field=DecimalField()),
            payment_rate=Case(
                When(contract_amount__gt=0, then=ExpressionWrapper(F('payment_amount') * 100 / F('contract_amount'), output_field=DecimalField())),
                default=Value(0),
                output_field=DecimalField()
            )
        ).filter(
            Q(payment_rate__lt=50) | Q(unpaid__gt=F('contract_amount') * 0.5)
        )
        
        # 合并所有风险合同
        risk_contract_ids = set()
        risk_contract_ids.update(high_risk.values_list('id', flat=True))
        risk_contract_ids.update(medium_risk.values_list('id', flat=True))
        risk_contract_ids.update(low_risk.values_list('id', flat=True))
        
        contracts = BusinessContract.objects.filter(
            id__in=risk_contract_ids
        ).select_related('client', 'project', 'created_by').order_by('-end_date', '-created_time')
        
        # 应用筛选条件
        contracts = _apply_contract_filters(contracts, filters)
        
        # 分页
        paginator = Paginator(contracts, 13)
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)
    except Exception as e:
        logger.exception('获取风险预警列表失败: %s', str(e))
        messages.error(request, f'获取风险预警列表失败：{str(e)}')
        page_obj = None
    
    # 统计信息
    try:
        today = timezone.now().date()
        high_risk_count = BusinessContract.objects.filter(
            Q(status__in=['executing', 'effective']) &
            Q(end_date__lt=today)
        ).count()
        
        medium_risk_count = BusinessContract.objects.filter(
            Q(status__in=['executing', 'effective']) &
            Q(end_date__gte=today) &
            Q(end_date__lte=today + timedelta(days=30))
        ).count()
        
        from django.db.models import ExpressionWrapper, DecimalField, Case, When, Value
        low_risk_count = BusinessContract.objects.filter(
            Q(status__in=['executing', 'effective', 'signed']) &
            Q(contract_amount__gt=0)
        ).annotate(
            payment_rate=Case(
                When(contract_amount__gt=0, then=ExpressionWrapper(F('payment_amount') * 100 / F('contract_amount'), output_field=DecimalField())),
                default=Value(0),
                output_field=DecimalField()
            )
        ).filter(payment_rate__lt=50).count()
        
        summary_cards = []
    except Exception as e:
        logger.exception('获取统计信息失败: %s', str(e))
        summary_cards = []
    
    context = _context(
        "风险预警",
        "⚠️",
        "识别和预警合同风险",
        summary_cards=summary_cards,
        request=request,
        active_menu_id='contract_risk_warning',
    )
    
    context.update({
        'page_obj': page_obj,
        'search': filters['search'],
        'selected_risk_type': filters['risk_type'],
        'show_filter_fields_settings_btn': True,
    })
    
    return render(request, "contract_management/contract_list.html", context)


@login_required

def authorization_letter_list(request):
    """业务委托书列表页面"""
    from django.core.paginator import Paginator
    from .forms import AuthorizationLetterForm
    
    permission_set = get_user_permission_codes(request.user)
    if not _permission_granted('contract_management.client.view', permission_set):
        messages.error(request, '您没有权限访问业务委托书列表')
        return redirect('contract_pages:contract_management_home')
    
    # 获取筛选参数
    search = request.GET.get('search', '')
    status = request.GET.get('status', '')
    client_name = request.GET.get('client_name', '')
    opportunity_id = request.GET.get('opportunity_id', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    # 获取委托书列表
    try:
        letters = AuthorizationLetter.objects.select_related('opportunity', 'project', 'created_by').order_by('-created_time')
        
        # 应用筛选条件
        if search:
            letters = letters.filter(
                Q(letter_number__icontains=search) |
                Q(project_name__icontains=search) |
                Q(client_name__icontains=search) |
                Q(trustee_name__icontains=search)
            )
        if status:
            letters = letters.filter(status=status)
        if client_name:
            letters = letters.filter(client_name__icontains=client_name)
        if opportunity_id:
            letters = letters.filter(opportunity_id=opportunity_id)
        if date_from:
            letters = letters.filter(created_time__date__gte=date_from)
        if date_to:
            letters = letters.filter(created_time__date__lte=date_to)
        
        # 分页
        paginator = Paginator(letters, 13)
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)
    except Exception as e:
        import logging
        from django.db import OperationalError, ProgrammingError
        logger = logging.getLogger(__name__)
        logger.exception('获取委托书列表失败: %s', str(e))
        
        # 检查是否是表不存在的错误
        error_msg = str(e)
        if 'does not exist' in error_msg.lower() or 'relation' in error_msg.lower():
            messages.error(
                request, 
                '数据库表不存在，请运行迁移或联系系统管理员。错误详情：表 business_authorization_letter 不存在。'
            )
        else:
            messages.error(request, f'获取委托书列表失败：{error_msg}')
        page_obj = None
    
    # 统计信息（应用当前筛选条件）
    try:
        base_queryset = AuthorizationLetter.objects.all()
        
        # 应用相同的筛选条件到统计查询
        if search:
            base_queryset = base_queryset.filter(
                Q(letter_number__icontains=search) |
                Q(project_name__icontains=search) |
                Q(client_name__icontains=search) |
                Q(trustee_name__icontains=search)
            )
        if status:
            base_queryset = base_queryset.filter(status=status)
        if client_name:
            base_queryset = base_queryset.filter(client_name__icontains=client_name)
        if opportunity_id:
            base_queryset = base_queryset.filter(opportunity_id=opportunity_id)
        if date_from:
            base_queryset = base_queryset.filter(created_time__date__gte=date_from)
        if date_to:
            base_queryset = base_queryset.filter(created_time__date__lte=date_to)
        
        total_count = base_queryset.count()
        confirmed_count = base_queryset.filter(status='confirmed').count()
        submitted_count = base_queryset.filter(status='submitted').count()
        draft_count = base_queryset.filter(status='draft').count()
        
        summary_cards = []
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception('获取统计信息失败: %s', str(e))
        summary_cards = []
    
    # 获取筛选选项
    clients = Client.objects.filter(is_active=True).order_by('name')[:100]  # 限制数量
    opportunities = BusinessOpportunity.objects.filter(
        status__in=['potential', 'initial_contact', 'requirement_confirmed', 'quotation', 'negotiation']
    ).order_by('-created_time')[:100]
    
    # 检查创建权限
    can_create = _permission_granted('contract_management.client.create', permission_set)
    
    context = _context(
        "创建业务委托书",
        "📋",
        "管理业务委托书",
        request=request,
        active_menu_id='authorization_letter_list',
    )
    
    # 为每个委托书对象添加权限属性
    if page_obj:
        for letter in page_obj:
            # 判断是否可以编辑（创建人或具有编辑权限）
            letter.can_edit = (
                letter.created_by == request.user or 
                _permission_granted('contract_management.client.edit', permission_set)
            )
            # 判断是否可以删除（创建人或具有删除权限）
            letter.can_delete = (
                letter.created_by == request.user or 
                _permission_granted('contract_management.client.delete', permission_set)
            )
    
    context.update({
        'page_obj': page_obj,
        'summary_cards': summary_cards,
        'search': search,
        'status': status,
        'client_name': client_name,
        'opportunity_id': opportunity_id,
        'date_from': date_from,
        'date_to': date_to,
        'clients': clients,
        'opportunities': opportunities,
        'status_choices': AuthorizationLetter.STATUS_CHOICES,
        'can_create': can_create,
    })
    
    return render(request, "contract_management/authorization_letter_list.html", context)


@login_required

def authorization_letter_create(request):
    """创建业务委托书"""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        from .forms import AuthorizationLetterForm
        
        permission_set = get_user_permission_codes(request.user)
        if not _permission_granted('contract_management.client.create', permission_set):
            messages.error(request, '您没有权限创建业务委托书')
            return redirect('contract_pages:authorization_letter_list')
        
        if request.method == 'POST':
            form = AuthorizationLetterForm(request.POST)
            if form.is_valid():
                letter = form.save(commit=False)
                letter.created_by = request.user
                letter.save()
                messages.success(request, f'业务委托书 "{letter.project_name}" 创建成功')
                return redirect('contract_pages:authorization_letter_list')
        else:
            form = AuthorizationLetterForm()
        
        context = _context(
            "创建业务委托书",
            "➕",
            "填写业务委托书信息",
            request=request,
            active_menu_id='authorization_letter_create',
        )
        
        context.update({
            'form': form,
            'is_create': True,
        })
        
        return render(request, "contract_management/authorization_letter_form.html", context)
    except Exception as e:
        logger.exception('创建业务委托书页面加载失败: %s', str(e))
        messages.error(request, f'页面加载失败：{str(e)}')
        return redirect('contract_pages:authorization_letter_list')


@login_required

def authorization_letter_detail(request, letter_id):
    """业务委托书详情"""
    permission_set = get_user_permission_codes(request.user)
    letter = get_object_or_404(AuthorizationLetter, id=letter_id)
    
    if not _permission_granted('contract_management.client.view', permission_set):
        messages.error(request, '您没有权限查看此业务委托书')
        return redirect('contract_pages:authorization_letter_list')
    
    context = _context(
        f"业务委托书详情 - {letter.project_name}",
        "📋",
        f"委托书编号：{letter.letter_number}",
        request=request,
        active_menu_id='authorization_letter_list',
    )
    
    context.update({
        'letter': letter,
        'can_edit': letter.can_edit() and _permission_granted('contract_management.client.edit', permission_set),
        'can_delete': letter.can_delete() and _permission_granted('contract_management.client.delete', permission_set),
        'can_convert': letter.can_convert_to_contract() and _permission_granted('contract_management.client.create', permission_set),
    })
    
    return render(request, "contract_management/authorization_letter_detail.html", context)


@login_required

def authorization_letter_edit(request, letter_id):
    """编辑业务委托书"""
    from .forms import AuthorizationLetterForm
    
    permission_set = get_user_permission_codes(request.user)
    letter = get_object_or_404(AuthorizationLetter, id=letter_id)
    
    if not letter.can_edit():
        messages.error(request, '只有草稿状态的委托书可以编辑')
        return redirect('contract_pages:authorization_letter_detail', letter_id=letter_id)
    
    if not _permission_granted('contract_management.client.edit', permission_set):
        messages.error(request, '您没有权限编辑此业务委托书')
        return redirect('contract_pages:authorization_letter_detail', letter_id=letter_id)
    
    if request.method == 'POST':
        form = AuthorizationLetterForm(request.POST, instance=letter)
        if form.is_valid():
            letter = form.save()
            messages.success(request, f'业务委托书 "{letter.project_name}" 更新成功')
            return redirect('contract_pages:authorization_letter_detail', letter_id=letter_id)
    else:
        form = AuthorizationLetterForm(instance=letter)
    
    context = _context(
        f"编辑业务委托书 - {letter.project_name}",
        "✏️",
        f"委托书编号：{letter.letter_number}",
        request=request,
        active_menu_id='authorization_letter_list',
    )
    
    context.update({
        'form': form,
        'letter': letter,
        'is_create': False,
    })
    
    return render(request, "contract_management/authorization_letter_form.html", context)


@login_required

def authorization_letter_delete(request, letter_id):
    """删除业务委托书"""
    permission_set = get_user_permission_codes(request.user)
    letter = get_object_or_404(AuthorizationLetter, id=letter_id)
    
    if not letter.can_delete():
        messages.error(request, '只有草稿状态的委托书可以删除')
        return redirect('contract_pages:authorization_letter_detail', letter_id=letter_id)
    
    if not _permission_granted('contract_management.client.delete', permission_set):
        messages.error(request, '您没有权限删除此业务委托书')
        return redirect('contract_pages:authorization_letter_detail', letter_id=letter_id)
    
    if request.method == 'POST':
        letter_name = letter.project_name
        letter.delete()
        messages.success(request, f'业务委托书 "{letter_name}" 已删除')
        return redirect('contract_pages:authorization_letter_list')
    
    context = _context(
        f"删除业务委托书 - {letter.project_name}",
        "🗑️",
        f"确认删除委托书编号：{letter.letter_number}",
        request=request,
        active_menu_id='authorization_letter_list',
    )
    
    context.update({
        'letter': letter,
    })
    
    return render(request, "contract_management/authorization_letter_delete.html", context)


@login_required

def authorization_letter_status_transition(request, letter_id):
    """业务委托书状态流转"""
    permission_set = get_user_permission_codes(request.user)
    letter = get_object_or_404(AuthorizationLetter, id=letter_id)
    
    if not _permission_granted('contract_management.client.edit', permission_set):
        messages.error(request, '您没有权限操作此业务委托书')
        return redirect('contract_pages:authorization_letter_detail', letter_id=letter_id)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'submit':
            if letter.status == 'draft':
                letter.status = 'submitted'
                letter.save()
                messages.success(request, '委托书已提交')
            else:
                messages.error(request, '只能提交草稿状态的委托书')
        elif action == 'confirm':
            if letter.status == 'submitted':
                letter.status = 'confirmed'
                letter.save()
                messages.success(request, '委托书已确认')
            else:
                messages.error(request, '只能确认已提交状态的委托书')
        elif action == 'cancel':
            if letter.status in ['draft', 'submitted']:
                letter.status = 'cancelled'
                letter.save()
                messages.success(request, '委托书已作废')
            else:
                messages.error(request, '只能作废草稿或已提交状态的委托书')
        else:
            messages.error(request, '无效的操作')
    
    return redirect('contract_pages:authorization_letter_detail', letter_id=letter_id)


# ==================== 业务委托书模板管理 ====================

@login_required

def authorization_letter_template_list(request):
    """业务委托书模板列表页面"""
    from django.core.paginator import Paginator
    from .forms import AuthorizationLetterTemplateForm
    
    permission_set = get_user_permission_codes(request.user)
    if not _permission_granted('contract_management.client.view', permission_set):
        messages.error(request, '您没有权限访问业务委托书模板列表')
        return redirect('contract_pages:authorization_letter_list')
    
    # 获取筛选参数
    search = request.GET.get('search', '')
    template_type = request.GET.get('template_type', '')
    status = request.GET.get('status', '')
    
    # 获取模板列表
    try:
        templates = AuthorizationLetterTemplate.objects.select_related('created_by', 'updated_by').order_by('-created_time')
        
        # 应用筛选条件
        if search:
            templates = templates.filter(
                Q(template_name__icontains=search) |
                Q(category__icontains=search) |
                Q(description__icontains=search)
            )
        if template_type:
            templates = templates.filter(template_type=template_type)
        if status:
            templates = templates.filter(status=status)
        
        # 分页
        paginator = Paginator(templates, 13)
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception('获取模板列表失败: %s', str(e))
        messages.error(request, f'获取模板列表失败：{str(e)}')
        page_obj = None
    
    # 统计信息
    try:
        total_count = AuthorizationLetterTemplate.objects.count()
        active_count = AuthorizationLetterTemplate.objects.filter(status='active').count()
        draft_count = AuthorizationLetterTemplate.objects.filter(status='draft').count()
        total_usage = AuthorizationLetterTemplate.objects.aggregate(total=Sum('usage_count'))['total'] or 0
        
        summary_cards = []
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception('获取统计信息失败: %s', str(e))
        summary_cards = []
    
    context = _context(
        "业务委托书模板列表",
        "📄",
        "管理业务委托书模板，快速创建委托书",
        summary_cards=summary_cards,
        request=request,
        active_menu_id='authorization_letter_template',
    )
    
    context.update({
        'page_obj': page_obj,
        'search': search,
        'template_type': template_type,
        'status': status,
        'template_type_choices': AuthorizationLetterTemplate.TEMPLATE_TYPE_CHOICES,
        'status_choices': AuthorizationLetterTemplate.STATUS_CHOICES,
        'show_filter_fields_settings_btn': True,
    })
    
    return render(request, "contract_management/authorization_letter_template_list.html", context)


@login_required

def authorization_letter_template_create(request):
    """创建业务委托书模板"""
    from .forms import AuthorizationLetterTemplateForm
    
    permission_set = get_user_permission_codes(request.user)
    if not _permission_granted('contract_management.client.create', permission_set):
        messages.error(request, '您没有权限创建业务委托书模板')
        return redirect('contract_pages:authorization_letter_template_list')
    
    if request.method == 'POST':
        import json
        form = AuthorizationLetterTemplateForm(request.POST, request.FILES)
        
        # 处理JSON字段
        if 'template_content' in request.POST:
            try:
                template_content = json.loads(request.POST.get('template_content', '{}'))
                form.data = form.data.copy()
                form.data['template_content'] = template_content
            except json.JSONDecodeError:
                messages.error(request, '模板内容格式错误')
        
        if 'variables' in request.POST:
            try:
                variables = json.loads(request.POST.get('variables', '[]'))
                form.data = form.data.copy()
                form.data['variables'] = variables
            except json.JSONDecodeError:
                messages.error(request, '变量列表格式错误')
        
        if form.is_valid():
            template = form.save(commit=False)
            template.created_by = request.user
            template.save()
            messages.success(request, f'业务委托书模板 "{template.template_name}" 创建成功')
            return redirect('contract_pages:authorization_letter_template_list')
    else:
        form = AuthorizationLetterTemplateForm()
    
    context = _context(
        "创建业务委托书模板",
        "➕",
        "填写模板信息，支持变量占位符",
        request=request,
        active_menu_id='authorization_letter_template',
    )
    
    context.update({
        'form': form,
        'is_create': True,
    })
    
    return render(request, "contract_management/authorization_letter_template_form.html", context)


@login_required

def authorization_letter_template_edit(request, template_id):
    """编辑业务委托书模板"""
    from .forms import AuthorizationLetterTemplateForm
    
    permission_set = get_user_permission_codes(request.user)
    template = get_object_or_404(AuthorizationLetterTemplate, id=template_id)
    
    if not _permission_granted('contract_management.client.edit', permission_set):
        messages.error(request, '您没有权限编辑此业务委托书模板')
        return redirect('contract_pages:authorization_letter_template_list')
    
    if request.method == 'POST':
        import json
        form = AuthorizationLetterTemplateForm(request.POST, request.FILES, instance=template)
        
        # 处理JSON字段
        if 'template_content' in request.POST:
            try:
                template_content = json.loads(request.POST.get('template_content', '{}'))
                form.data = form.data.copy()
                form.data['template_content'] = template_content
            except json.JSONDecodeError:
                messages.error(request, '模板内容格式错误')
        
        if 'variables' in request.POST:
            try:
                variables = json.loads(request.POST.get('variables', '[]'))
                form.data = form.data.copy()
                form.data['variables'] = variables
            except json.JSONDecodeError:
                messages.error(request, '变量列表格式错误')
        
        if form.is_valid():
            template = form.save(commit=False)
            template.updated_by = request.user
            template.save()
            messages.success(request, f'业务委托书模板 "{template.template_name}" 更新成功')
            return redirect('contract_pages:authorization_letter_template_list')
    else:
        form = AuthorizationLetterTemplateForm(instance=template)
    
    context = _context(
        f"编辑业务委托书模板 - {template.template_name}",
        "✏️",
        f"模板类型：{template.get_template_type_display()}",
        request=request,
        active_menu_id='authorization_letter_template',
    )
    
    context.update({
        'form': form,
        'template': template,
        'is_create': False,
    })
    
    return render(request, "contract_management/authorization_letter_template_form.html", context)


@login_required

def authorization_letter_template_delete(request, template_id):
    """删除业务委托书模板"""
    permission_set = get_user_permission_codes(request.user)
    template = get_object_or_404(AuthorizationLetterTemplate, id=template_id)
    
    if not _permission_granted('contract_management.client.delete', permission_set):
        messages.error(request, '您没有权限删除此业务委托书模板')
        return redirect('contract_pages:authorization_letter_template_list')
    
    if request.method == 'POST':
        template_name = template.template_name
        template.delete()
        messages.success(request, f'业务委托书模板 "{template_name}" 已删除')
        return redirect('contract_pages:authorization_letter_template_list')
    
    context = _context(
        f"删除业务委托书模板 - {template.template_name}",
        "🗑️",
        f"确认删除模板：{template.template_name}",
        request=request,
        active_menu_id='authorization_letter_template',
    )
    
    context.update({
        'template': template,
    })
    
    return render(request, "contract_management/authorization_letter_template_delete.html", context)


@login_required

def authorization_letter_create_from_template(request, template_id):
    """从模板创建业务委托书"""
    from .forms import AuthorizationLetterForm
    
    permission_set = get_user_permission_codes(request.user)
    if not _permission_granted('contract_management.client.create', permission_set):
        messages.error(request, '您没有权限创建业务委托书')
        return redirect('contract_pages:authorization_letter_list')
    
    template = get_object_or_404(AuthorizationLetterTemplate, id=template_id)
    
    if request.method == 'POST':
        form = AuthorizationLetterForm(request.POST)
        if form.is_valid():
            letter = form.save(commit=False)
            letter.created_by = request.user
            letter.save()
            
            # 增加模板使用次数
            template.increment_usage()
            
            messages.success(request, f'业务委托书 "{letter.project_name}" 创建成功（来自模板：{template.template_name}）')
            return redirect('contract_pages:authorization_letter_detail', letter_id=letter.id)
    else:
        # 从模板填充表单初始值
        form = AuthorizationLetterForm()
        template_content = template.template_content or {}
        
        # 填充表单字段
        for field_name, field_value in template_content.items():
            if hasattr(form, 'fields') and field_name in form.fields:
                form.initial[field_name] = field_value
    
    context = _context(
        f"从模板创建业务委托书 - {template.template_name}",
        "📄",
        f"模板类型：{template.get_template_type_display()}",
        request=request,
        active_menu_id='authorization_letter_create',
    )
    
    context.update({
        'form': form,
        'template': template,
        'is_create': True,
        'from_template': True,
    })
    
    return render(request, "contract_management/authorization_letter_form.html", context)


@login_required

def authorization_letter_template_file_preview(request, template_id):
    """预览业务委托书模板文件"""
    from django.http import FileResponse, Http404
    import os
    import mimetypes
    
    permission_set = get_user_permission_codes(request.user)
    if not _permission_granted('contract_management.client.view', permission_set):
        messages.error(request, '您没有权限预览模板文件')
        return redirect('contract_pages:authorization_letter_template_list')
    
    template = get_object_or_404(AuthorizationLetterTemplate, id=template_id)
    
    if not template.template_file:
        raise Http404('模板文件不存在')
    
    try:
        # 获取文件名
        if template.template_file_name:
            filename = template.template_file_name
        else:
            filename = os.path.basename(template.template_file.name)
        
        # 根据文件扩展名确定 content_type
        ext = os.path.splitext(filename)[1].lower()
        content_type_map = {
            '.pdf': 'application/pdf',
            '.doc': 'application/msword',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.xls': 'application/vnd.ms-excel',
            '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            '.ppt': 'application/vnd.ms-powerpoint',
            '.pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
        }
        content_type = content_type_map.get(ext, 'application/octet-stream')
        
        response = FileResponse(
            template.template_file.open('rb'),
            content_type=content_type
        )
        # 设置文件名和内联显示
        response['Content-Disposition'] = f'inline; filename="{filename}"'
        return response
    except Exception as e:
        logger.exception('预览模板文件失败: %s', str(e))
        messages.error(request, f'预览文件失败：{str(e)}')
        return redirect('contract_pages:authorization_letter_template_edit', template_id=template_id)


@login_required

def authorization_letter_template_file_download(request, template_id):
    """下载业务委托书模板文件"""
    from django.http import FileResponse, Http404
    
    permission_set = get_user_permission_codes(request.user)
    if not _permission_granted('contract_management.client.view', permission_set):
        messages.error(request, '您没有权限下载模板文件')
        return redirect('contract_pages:authorization_letter_template_list')
    
    template = get_object_or_404(AuthorizationLetterTemplate, id=template_id)
    
    if not template.template_file:
        raise Http404('模板文件不存在')
    
    try:
        response = FileResponse(
            template.template_file.open('rb'),
            content_type='application/octet-stream'
        )
        # 设置下载文件名
        if template.template_file_name:
            response['Content-Disposition'] = f'attachment; filename="{template.template_file_name}"'
        else:
            import os
            filename = os.path.basename(template.template_file.name)
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
    except Exception as e:
        logger.exception('下载模板文件失败: %s', str(e))
        messages.error(request, f'下载文件失败：{str(e)}')
        return redirect('contract_pages:authorization_letter_template_edit', template_id=template_id)


