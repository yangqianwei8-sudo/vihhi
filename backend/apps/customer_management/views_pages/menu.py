# 客户管理模块左侧菜单结构及构建函数
from django.urls import reverse, NoReverseMatch

from backend.apps.opportunity_management.views_common import (
    _build_opportunity_management_sidebar_nav as _build_opportunity_sidebar_from_opp_module,
)
from backend.apps.system_management.services import get_user_permission_codes
from backend.core.views import _permission_granted, _build_full_top_nav

from .common import _build_unified_sidebar_nav


# ==================== 客户管理模块左侧菜单结构（简化版）====================
# 一级：首页 | 线索与客户 | 联系人 | 拜访与关系
CUSTOMER_MANAGEMENT_MENU = [
    {
        'id': 'customer_home',
        'label': '首页',
        'icon': '🏠',
        'url_name': 'customer_pages:customer_management_home',
        'permission': 'customer_management.client.view',
    },
    {
        'id': 'lead_and_customer',
        'label': '线索与客户',
        'icon': '👥',
        'permission': 'customer_management.client.view',
        'children': [
            {'id': 'customer_lead_list', 'label': '线索列表', 'icon': '📋', 'url_name': 'customer_pages:customer_lead_list', 'permission': 'customer_management.client.view'},
            {'id': 'customer_list', 'label': '客户列表', 'icon': '📋', 'url_name': 'customer_pages:customer_list', 'permission': 'customer_management.client.view'},
            {'id': 'customer_public_sea', 'label': '客户公海', 'icon': '🌊', 'url_name': 'customer_pages:customer_public_sea', 'permission': 'customer_management.public_sea.view'},
        ]
    },
    {
        'id': 'customer_contact',
        'label': '联系人',
        'icon': '👤',
        'permission': 'customer_management.contact.view',
        'children': [
            {'id': 'contact_list', 'label': '联系人列表', 'icon': '📇', 'url_name': 'customer_pages:contact_list', 'permission': 'customer_management.contact.view'},
            {'id': 'contact_relationship_mining', 'label': '关系挖掘', 'icon': '🔍', 'url_name': 'customer_pages:contact_relationship_mining', 'permission': 'customer_management.contact.view'},
        ]
    },
    {
        'id': 'contact_tracking_visit',
        'label': '拜访与关系',
        'icon': '🚶',
        'permission': 'customer_management.relationship.view',
        'children': [
            {'id': 'visit_list', 'label': '客户跟踪', 'icon': '🚪', 'url_name': 'customer_pages:customer_visit', 'permission': 'customer_management.relationship.view'},
            {'id': 'visit_checkin', 'label': '拜访打卡', 'icon': '📍', 'url_name': 'customer_pages:visit_checkin_select', 'permission': 'customer_management.relationship.edit'},
            {'id': 'visit_review', 'label': '拜访复盘', 'icon': '📊', 'url_name': 'customer_pages:visit_review_select', 'permission': 'customer_management.relationship.edit'},
            {'id': 'upgrade_list', 'label': '关系升级', 'icon': '⬆️', 'url_name': 'customer_pages:customer_relationship_upgrade', 'permission': 'customer_management.relationship.view'},
            {'id': 'relationship_collaboration', 'label': '关系协作', 'icon': '🤝', 'url_name': 'customer_pages:customer_relationship_collaboration', 'permission': 'customer_management.relationship.view'},
            {'id': 'business_expense_application', 'label': '业务费申请', 'icon': '💰', 'url_name': 'customer_pages:business_expense_application_list', 'permission': 'customer_management.relationship.view'},
        ]
    },
]


def _build_opportunity_management_menu(permission_set, active_id=None):
    """生成商机管理模块左侧菜单（委托给 opportunity_management）"""
    return _build_opportunity_sidebar_from_opp_module(permission_set, active_id=active_id)


def _check_customer_permission(permission_code, permission_set):
    """检查客户管理权限（支持新旧权限代码自动映射）"""
    from backend.apps.permission_management.utils import normalize_permission_code
    normalized_code = normalize_permission_code(permission_code)
    return _permission_granted(normalized_code, permission_set)


def _filter_clients_by_permission(clients, user, permission_set):
    """根据用户权限过滤客户列表"""
    if not user or not getattr(user, 'is_authenticated', False):
        return clients.none()
    if getattr(user, 'is_superuser', False):
        return clients
    if _check_customer_permission('customer_management.client.view_all', permission_set):
        return clients
    if _check_customer_permission('customer_management.client.view_department', permission_set):
        if user.department:
            from backend.apps.system_management.models import User
            from django.db.models import Q
            department_users = User.objects.filter(department=user.department, is_active=True)
            return clients.filter(Q(responsible_user__in=department_users) | Q(created_by__in=department_users))
        from django.db.models import Q
        return clients.filter(Q(responsible_user=user) | Q(created_by=user))
    if _check_customer_permission('customer_management.client.view_assigned', permission_set):
        from django.db.models import Q
        return clients.filter(Q(responsible_user=user) | Q(created_by=user))
    if _check_customer_permission('customer_management.client.view', permission_set):
        if user.roles.filter(code='general_manager').exists():
            return clients
        if user.department and user.department.leader == user:
            from backend.apps.system_management.models import User
            from django.db.models import Q
            department_users = User.objects.filter(department=user.department, is_active=True)
            return clients.filter(Q(responsible_user__in=department_users) | Q(created_by__in=department_users))
        from django.db.models import Q
        return clients.filter(Q(responsible_user=user) | Q(created_by=user))
    return clients.none()


def _build_customer_management_menu(permission_set, active_id=None):
    """生成客户管理模块左侧菜单"""
    menu = []
    for menu_group in CUSTOMER_MANAGEMENT_MENU:
        permission = menu_group.get('permission')
        if permission and not _check_customer_permission(permission, permission_set):
            continue
        children = []
        for child in menu_group.get('children', []):
            child_permission = child.get('permission')
            if child_permission and not _check_customer_permission(child_permission, permission_set):
                continue
            url_name = child.get('url_name')
            url = '#'
            if url_name:
                try:
                    url = reverse(url_name)
                except NoReverseMatch:
                    url = '#'
            is_active = child.get('id') == active_id
            children.append({
                'id': child.get('id'),
                'label': child.get('label'),
                'icon': child.get('icon'),
                'url': url,
                'active': is_active,
            })
        if not children:
            continue
        group_active = any(child.get('id') == active_id for child in menu_group.get('children', []))
        parent_url = '#'
        if menu_group.get('url_name'):
            try:
                parent_url = reverse(menu_group.get('url_name'))
            except NoReverseMatch:
                parent_url = '#'
        elif children:
            parent_url = children[0].get('url', '#')
        menu.append({
            'id': menu_group.get('id'),
            'label': menu_group.get('label'),
            'icon': menu_group.get('icon'),
            'url': parent_url,
            'active': group_active,
            'expanded': group_active,
            'children': children,
        })
    return menu


def _build_customer_management_sidebar_nav(permission_set, request_path=None, active_id=None):
    """生成客户管理左侧菜单（统一格式）"""
    return _build_unified_sidebar_nav(CUSTOMER_MANAGEMENT_MENU, permission_set, active_id=active_id)


def _build_opportunity_management_sidebar_nav(permission_set, request_path=None, active_id=None):
    """生成商机管理左侧菜单（委托 opportunity_management）"""
    return _build_opportunity_sidebar_from_opp_module(permission_set, request_path, active_id)


def _context(page_title, page_icon, description, summary_cards=None, sections=None, request=None, active_menu_id=None):
    """构建页面上下文（含顶部导航与侧边栏）"""
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
        if request.path and ('/opportunities/' in request.path or '/business/opportunities' in request.path):
            context['sidebar_module_title'] = '商机管理'
            context['sidebar_module_subtitle'] = 'Opportunity Management'
            active_menu_id = None
            if '/evaluation-application' in request.path:
                active_menu_id = 'evaluation_application'
            elif '/drawing-evaluation' in request.path:
                active_menu_id = 'drawing_evaluation'
            elif '/tech-meeting' in request.path:
                active_menu_id = 'tech_meeting'
            elif '/warehouse-list' in request.path or '/warehouse-application' in request.path:
                active_menu_id = 'warehouse_list'
            elif '/bidding-quotation-application' in request.path:
                active_menu_id = 'bidding_quotation_application'
            elif '/bidding-quotation' in request.path and '/bidding-quotation-application' not in request.path:
                active_menu_id = 'bidding_quotation'
            elif '/bidding-document-preparation' in request.path:
                active_menu_id = 'bidding_document_preparation'
            elif '/bidding-document-submission' in request.path:
                active_menu_id = 'bidding_document_submission'
            elif '/business-negotiation' in request.path:
                active_menu_id = 'business_negotiation'
            elif '/forecast' in request.path:
                active_menu_id = 'sales_forecast'
            elif '/win-loss' in request.path:
                active_menu_id = 'win_loss'
            elif '/bid-bond-payment' in request.path:
                active_menu_id = 'bid_bond_payment'
            elif '/tender-fee-payment' in request.path:
                active_menu_id = 'tender_fee_payment'
            elif '/agency-fee-payment' in request.path:
                active_menu_id = 'tender_agent_fee_payment'
            elif request.path.endswith('/opportunities/') or request.path.endswith('/opportunities') or '/opportunities/list' in request.path:
                active_menu_id = 'opportunity_list'
            context['sidebar_nav'] = _build_opportunity_management_sidebar_nav(permission_set, request.path, active_id=active_menu_id)
            context['sidebar_title'] = '商机管理'
            context['sidebar_subtitle'] = 'Opportunity Management'
        elif request.path and ('/contracts/' in request.path or '/authorization-letters' in request.path or '/authorization-letter-templates' in request.path or '/business/authorization-letters' in request.path or '/business/authorization-letter-templates' in request.path or '/business/contracts' in request.path):
            context['sidebar_title'] = '合同管理'
            context['sidebar_subtitle'] = 'Contract Management'
            if active_menu_id is None:
                if '/contracts/home' in request.path or request.path == '/contracts/' or request.path == '/contracts':
                    active_menu_id = 'contract_home'
                elif '/contracts/management' in request.path or '/management/' in request.path:
                    active_menu_id = 'contract_management_list'
                elif '/contracts/dispute' in request.path or '/dispute/' in request.path:
                    active_menu_id = 'contract_dispute_list'
                elif '/contracts/finalize' in request.path or '/finalize/' in request.path:
                    active_menu_id = 'contract_finalize_create' if '/create' in request.path else 'contract_finalize_list'
                elif '/contracts/negotiation' in request.path or '/negotiation/' in request.path:
                    active_menu_id = 'contract_negotiation_create' if '/create' in request.path else 'contract_negotiation_list'
                elif '/contracts/performance' in request.path or '/performance/' in request.path:
                    active_menu_id = 'contract_performance'
                elif '/contracts/expiry-reminder' in request.path or '/expiry-reminder/' in request.path:
                    active_menu_id = 'contract_expiry_reminder'
                elif '/contracts/payment-reminder' in request.path or '/payment-reminder/' in request.path:
                    active_menu_id = 'contract_payment_reminder'
                elif '/contracts/risk-warning' in request.path or '/risk-warning/' in request.path:
                    active_menu_id = 'contract_risk_warning'
                elif '/contracts/create' in request.path or (request.path.endswith('/create/') and '/contracts/' in request.path):
                    active_menu_id = 'contract_management_list'
                elif '/contracts/' in request.path and '/edit' in request.path:
                    active_menu_id = 'contract_management_list'
                elif '/contracts/' in request.path and request.path.count('/') >= 3 and not any(x in request.path for x in ['/edit', '/delete', '/create', '/management', '/dispute', '/finalize', '/negotiation', '/performance', '/expiry-reminder', '/payment-reminder', '/risk-warning', '/home']):
                    active_menu_id = 'contract_management_list'
                elif '/authorization-letters' in request.path and '/authorization-letter-templates' not in request.path:
                    active_menu_id = 'authorization_letter_list'
                elif '/authorization-letter-templates' in request.path:
                    active_menu_id = 'authorization_letter_template_list'
            try:
                from backend.apps.contract_management.views_pages import _build_contract_management_sidebar_nav
                context['sidebar_nav'] = _build_contract_management_sidebar_nav(permission_set, request.path, active_id=active_menu_id)
            except ImportError:
                context['sidebar_nav'] = []
        elif request.path and ('/customers/' in request.path or '/contacts/' in request.path or '/visit-plan/' in request.path or '/customer-visit/' in request.path or '/customer-relationship-' in request.path or '/business-expense-application' in request.path or '/customer-leads/' in request.path or '/customer-filings/' in request.path or request.path.startswith('/business/')):
            context['sidebar_title'] = '客户管理'
            context['sidebar_subtitle'] = 'Customer Management'
            if active_menu_id is None:
                if '/customers/home' in request.path or request.path in ('/customers/', '/customers', '/business/', '/business'):
                    active_menu_id = 'customer_home'
                elif '/customer-leads/' in request.path or '/customer-filings/' in request.path:
                    active_menu_id = 'customer_lead_list'
                elif '/public-sea' in request.path or '/customers/public-sea' in request.path:
                    active_menu_id = 'customer_public_sea'
                elif '/contacts/' in request.path:
                    active_menu_id = 'contact_relationship_mining' if 'relationship-mining' in request.path else ('contact_create' if '/create' in request.path else 'contact_list')
                elif '/first-visit/' in request.path:
                    active_menu_id = 'first_visit_create'
                elif '/visit-plan/' in request.path or '/customer-visit/' in request.path or '/visit-checkin/' in request.path or '/visit-review/' in request.path:
                    active_menu_id = 'visit_create' if '/create' in request.path and 'first-visit' not in request.path else ('visit_checkin' if 'checkin' in request.path else ('visit_review' if 'review' in request.path else 'visit_list'))
                elif '/customer-relationship-upgrade' in request.path:
                    active_menu_id = 'upgrade_list'
                elif '/customer-relationship-collaboration' in request.path:
                    active_menu_id = 'relationship_collaboration'
                elif '/business-expense-application' in request.path:
                    active_menu_id = 'business_expense_application'
                elif '/customers/customers' in request.path or '/business/customers' in request.path:
                    active_menu_id = 'customer_create' if '/create' in request.path else 'customer_list'
            context['sidebar_nav'] = _build_customer_management_sidebar_nav(permission_set, request.path, active_id=active_menu_id)
        elif request.path == '/customers/' or request.path == '/customers' or request.path == '/business/' or request.path == '/business':
            context['sidebar_title'] = '客户管理'
            context['sidebar_subtitle'] = 'Customer Management'
            context['sidebar_nav'] = _build_customer_management_sidebar_nav(permission_set, request.path, active_id='customer_home')
    else:
        context['full_top_nav'] = []
        context['sidebar_nav'] = []
    return context
