# 商机管理 - 共享配置与工具函数

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
    ContactEducation,
    ContactCareer,
    ContactColleague,
)

try:
    from backend.apps.customer_management.models import (
        CommunicationChecklistQuestion,
        CommunicationChecklistAnswer,
        CustomerCommunicationChecklist,
    )
    HAS_COMMUNICATION_CHECKLIST_MODELS = True
except ImportError:
    HAS_COMMUNICATION_CHECKLIST_MODELS = False

from backend.apps.contract_management.models import BusinessContract, BusinessPaymentPlan
from backend.apps.base_data.models import DesignStage, ServiceType

from backend.apps.opportunity_management.models import (
    BusinessOpportunity,
    OpportunityFollowUp,
    OpportunityQuotation,
    OpportunityApproval,
    OpportunityStatusLog,
    QuotationRule,
    BusinessNegotiation,
    OpportunityFiling,
    BiddingQuotation,
    CustomerRequirementCommunication,
)

from backend.apps.system_management.services import get_user_permission_codes
from backend.core.views import HOME_NAV_STRUCTURE, _permission_granted, _build_full_top_nav
from backend.apps.permission_management.utils import normalize_permission_code
from .perm_check import (
    opportunity_sidebar_permission,
    expand_permission_set_for_nav,
)

try:
    from backend.core.views import _build_unified_sidebar_nav
except ImportError:

    def _build_unified_sidebar_nav(menu_structure, permission_set, active_id=None):
        """简单的侧边栏菜单构建函数（支持 url_name 转换）"""
        nav = []
        for item in menu_structure:
            if item.get('permission'):
                if not _permission_granted(item['permission'], permission_set):
                    continue

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
                'children': [],
                'badge': item.get('badge') or '',
                'expanded': item.get('expanded', False),
            }

            if 'children' in item:
                children = []
                for child in item['children']:
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
                # 有子菜单时根据 active 自动展开
                nav_item['expanded'] = any(c.get('active') for c in children) or nav_item.get('expanded', False)
            nav.append(nav_item)
        return nav

logger = logging.getLogger(__name__)


# ==================== 商机管理模块左侧菜单结构（二级菜单） =====================
# 按业务域分组：首页 | 商机与列表 | 项目与投标 | 商务与费用
# 权限码统一使用 opportunity_management.opportunity.*（兼容 customer_management.* 由 perm_check 处理）
OPPORTUNITY_MANAGEMENT_MENU = [
    # 一级：首页
    {
        'id': 'opportunity_home',
        'label': '首页',
        'icon': '🏠',
        'url_name': 'opportunity_pages:opportunity_management_home',
        'permission': opportunity_sidebar_permission('view'),
    },
    # 一级：商机与列表（新建、列表、预测、赢单输单；批量导入入口在商机列表页内）
    {
        'id': 'opportunity_and_list',
        'label': '商机与列表',
        'icon': '📋',
        'permission': opportunity_sidebar_permission('view'),
        'children': [
            {'id': 'opportunity_create', 'label': '新建商机', 'icon': '➕',
             'url_name': 'opportunity_pages:opportunity_create',
             'url': '/opportunities/create/',  # 回退地址，避免 reverse 失败时链接为 #
             'permission': opportunity_sidebar_permission('create')},
            {'id': 'opportunity_list', 'label': '商机列表', 'icon': '📋',
             'url_name': 'opportunity_pages:opportunity_management',
             'permission': opportunity_sidebar_permission('view')},
            {'id': 'sales_forecast', 'label': '商机预测', 'icon': '📈',
             'url_name': 'opportunity_pages:opportunity_sales_forecast',
             'permission': opportunity_sidebar_permission('view')},
            {'id': 'win_loss', 'label': '赢单与输单', 'icon': '✅',
             'url_name': 'opportunity_pages:opportunity_win_loss',
             'permission': opportunity_sidebar_permission('manage')},
        ]
    },
    # 一级：项目与投标（评估、图纸、技术会、报价、投标文件）
    {
        'id': 'project_and_bidding',
        'label': '项目与投标',
        'icon': '🏗️',
        'permission': opportunity_sidebar_permission('view'),
        'children': [
            {'id': 'evaluation_application', 'label': '评估申请', 'icon': '📝',
             'url_name': 'opportunity_pages:opportunity_evaluation_application',
             'permission': opportunity_sidebar_permission('manage')},
            {'id': 'drawing_evaluation', 'label': '图纸评估', 'icon': '📐',
             'url_name': 'opportunity_pages:opportunity_drawing_evaluation',
             'permission': opportunity_sidebar_permission('view')},
            {'id': 'tech_meeting', 'label': '技术沟通会', 'icon': '🤝',
             'url_name': 'opportunity_pages:opportunity_tech_meeting',
             'permission': opportunity_sidebar_permission('view')},
            {'id': 'bidding_quotation_application', 'label': '投标报价申请', 'icon': '📋',
             'url_name': 'opportunity_pages:opportunity_bidding_quotation_application',
             'permission': opportunity_sidebar_permission('view')},
            {'id': 'bidding_quotation', 'label': '投标报价管理', 'icon': '📊',
             'url_name': 'opportunity_pages:opportunity_bidding_quotation',
             'permission': opportunity_sidebar_permission('view')},
            {'id': 'bidding_document_preparation', 'label': '编制投标文件', 'icon': '📄',
             'url_name': 'opportunity_pages:opportunity_bidding_document_preparation',
             'permission': opportunity_sidebar_permission('manage')},
            {'id': 'bidding_document_submission', 'label': '递交投标文件', 'icon': '📤',
             'url_name': 'opportunity_pages:opportunity_bidding_document_submission',
             'permission': opportunity_sidebar_permission('manage')},
        ]
    },
    # 一级：商务与费用（洽谈、各类支付、入库）
    {
        'id': 'business_and_fee',
        'label': '商务与费用',
        'icon': '💼',
        'permission': opportunity_sidebar_permission('view'),
        'children': [
            {'id': 'business_negotiation', 'label': '商务洽谈登记', 'icon': '🤝',
             'url_name': 'opportunity_pages:opportunity_business_negotiation',
             'permission': opportunity_sidebar_permission('view')},
            {'id': 'bid_bond_payment', 'label': '投标保证金支付', 'icon': '💰',
             'url_name': 'opportunity_pages:opportunity_bid_bond_payment',
             'permission': opportunity_sidebar_permission('manage')},
            {'id': 'tender_fee_payment', 'label': '标书费支付', 'icon': '📄',
             'url_name': 'opportunity_pages:opportunity_tender_fee_payment',
             'permission': opportunity_sidebar_permission('manage')},
            {'id': 'tender_agent_fee_payment', 'label': '招标代理费支付', 'icon': '🏢',
             'url_name': 'opportunity_pages:opportunity_agency_fee_payment',
             'permission': opportunity_sidebar_permission('manage')},
            {'id': 'warehouse_list', 'label': '创建入库', 'icon': '📥',
             'url_name': 'opportunity_pages:opportunity_warehouse_list',
             'permission': opportunity_sidebar_permission('view')},
        ]
    },
]


def _build_opportunity_management_sidebar_nav(permission_set, request_path=None, active_id=None):
    """生成商机管理左侧菜单（统一格式，兼容 customer_management.opportunity.* 权限）"""
    expanded = expand_permission_set_for_nav(permission_set)
    return _build_unified_sidebar_nav(OPPORTUNITY_MANAGEMENT_MENU, expanded, active_id=active_id)


def _context(page_title, page_icon, description, summary_cards=None, sections=None, request=None, active_menu_id=None):
    """构建页面上下文（简化版，专门用于商机管理）"""
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
        context['sidebar_module_title'] = '商机管理'
        context['sidebar_module_subtitle'] = 'Opportunity Management'
        context['sidebar_title'] = '商机管理'
        context['sidebar_subtitle'] = 'Opportunity Management'
        context['sidebar_nav'] = _build_opportunity_management_sidebar_nav(
            permission_set, request.path, active_id=active_menu_id)
    else:
        context['full_top_nav'] = []
        context['sidebar_nav'] = []
    return context


# 客户管理菜单：以 customer_management.views_pages.CUSTOMER_MANAGEMENT_MENU 为准，此处不再维护副本


def _get_opportunities_safely(queryset, permission_set, user):
    """安全获取商机列表，处理新字段可能不存在的情况"""
    from django.db import connection
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT column_name FROM information_schema.columns
                WHERE table_name = 'business_opportunity' AND column_name = 'opportunity_type'
            """)
            has_new_fields = cursor.fetchone() is not None
    except Exception:
        has_new_fields = False
    if has_new_fields:
        return queryset
    try:
        return queryset.defer('opportunity_type', 'service_type')
    except Exception:
        return queryset.values('id', 'name', 'client_id', 'client__name', 'business_manager_id')
