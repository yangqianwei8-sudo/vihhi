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
            nav.append(nav_item)
        return nav

logger = logging.getLogger(__name__)


# ==================== 商机管理模块左侧菜单结构 =====================
OPPORTUNITY_MANAGEMENT_MENU = [
    {
        'id': 'opportunity_home',
        'label': '首页',
        'icon': '🏠',
        'url_name': 'opportunity_pages:opportunity_management_home',
        'permission': 'customer_management.opportunity.view',
    },
    {
        'id': 'basic_info',
        'label': '基本信息',
        'icon': '📋',
        'permission': 'customer_management.opportunity.view',
        'children': [
            {'id': 'opportunity_list', 'label': '商机列表', 'icon': '📋',
             'url_name': 'opportunity_pages:opportunity_management',
             'permission': 'customer_management.opportunity.view'},
            {'id': 'opportunity_import', 'label': '批量导入', 'icon': '📥',
             'url_name': 'opportunity_pages:opportunity_import',
             'permission': 'customer_management.opportunity.view'},
        ]
    },
    {
        'id': 'project_info',
        'label': '项目信息',
        'icon': '🏗️',
        'permission': 'customer_management.opportunity.view',
        'children': [
            {'id': 'evaluation_application', 'label': '评估申请', 'icon': '📝',
             'url_name': 'opportunity_pages:opportunity_evaluation_application',
             'permission': 'customer_management.opportunity.manage'},
            {'id': 'drawing_evaluation', 'label': '图纸评估', 'icon': '📐',
             'url_name': 'opportunity_pages:opportunity_drawing_evaluation',
             'permission': 'customer_management.opportunity.view'},
            {'id': 'tech_meeting', 'label': '技术沟通会', 'icon': '🤝',
             'url_name': 'opportunity_pages:opportunity_tech_meeting',
             'permission': 'customer_management.opportunity.view'},
        ]
    },
    {
        'id': 'amount_info',
        'label': '金额信息',
        'icon': '💰',
        'permission': 'customer_management.opportunity.view',
        'children': [
            {'id': 'bidding_quotation_application', 'label': '投标报价申请', 'icon': '📋',
             'url_name': 'opportunity_pages:opportunity_bidding_quotation_application',
             'permission': 'customer_management.opportunity.view'},
            {'id': 'bidding_quotation', 'label': '投标报价管理', 'icon': '📊',
             'url_name': 'opportunity_pages:opportunity_bidding_quotation',
             'permission': 'customer_management.opportunity.view'},
            {'id': 'warehouse_list', 'label': '创建入库', 'icon': '📥',
             'url_name': 'opportunity_pages:opportunity_warehouse_list',
             'permission': 'customer_management.opportunity.view'},
        ]
    },
    {
        'id': 'time_info',
        'label': '时间信息',
        'icon': '⏰',
        'permission': 'customer_management.opportunity.view',
        'children': [
            {'id': 'bidding_document_preparation', 'label': '编制投标文件', 'icon': '📄',
             'url_name': 'opportunity_pages:opportunity_bidding_document_preparation',
             'permission': 'customer_management.opportunity.manage'},
            {'id': 'bidding_document_submission', 'label': '递交投标文件', 'icon': '📤',
             'url_name': 'opportunity_pages:opportunity_bidding_document_submission',
             'permission': 'customer_management.opportunity.manage'},
            {'id': 'business_negotiation', 'label': '商务洽谈登记', 'icon': '💼',
             'url_name': 'opportunity_pages:opportunity_business_negotiation',
             'permission': 'customer_management.opportunity.view'},
        ]
    },
    {
        'id': 'opportunity_description',
        'label': '商机描述',
        'icon': '📝',
        'permission': 'customer_management.opportunity.view',
        'children': [
            {'id': 'sales_forecast', 'label': '商机预测', 'icon': '📈',
             'url_name': 'opportunity_pages:opportunity_sales_forecast',
             'permission': 'customer_management.opportunity.view'},
            {'id': 'win_loss', 'label': '赢单与输单', 'icon': '✅',
             'url_name': 'opportunity_pages:opportunity_win_loss',
             'permission': 'customer_management.opportunity.manage'},
        ]
    },
    {
        'id': 'payment_management',
        'label': '费用支付',
        'icon': '💳',
        'permission': 'customer_management.opportunity.view',
        'children': [
            {'id': 'bid_bond_payment', 'label': '投标保证金支付', 'icon': '💰',
             'url_name': 'opportunity_pages:opportunity_bid_bond_payment',
             'permission': 'customer_management.opportunity.manage'},
            {'id': 'tender_fee_payment', 'label': '标书费支付', 'icon': '📄',
             'url_name': 'opportunity_pages:opportunity_tender_fee_payment',
             'permission': 'customer_management.opportunity.manage'},
            {'id': 'tender_agent_fee_payment', 'label': '招标代理费支付', 'icon': '🏢',
             'url_name': 'opportunity_pages:opportunity_tender_agent_fee_payment',
             'permission': 'customer_management.opportunity.manage'},
        ]
    },
]


def _build_opportunity_management_sidebar_nav(permission_set, request_path=None, active_id=None):
    """生成商机管理左侧菜单（统一格式）"""
    return _build_unified_sidebar_nav(OPPORTUNITY_MANAGEMENT_MENU, permission_set, active_id=active_id)


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


# ==================== 客户管理模块左侧菜单结构 =====================
CUSTOMER_MANAGEMENT_MENU = [
    {'id': 'customer_home', 'label': '首页', 'icon': '🏠',
     'url_name': 'customer_pages:customer_management_home',
     'permission': 'customer_management.client.view'},
    {
        'id': 'lead_and_public_sea',
        'label': '线索与公海',
        'icon': '🔍',
        'permission': 'customer_management.client.view',
        'children': [
            {'id': 'customer_lead_create', 'label': '创建客户线索', 'icon': '📝',
             'url_name': 'customer_pages:customer_lead_create',
             'permission': 'customer_management.client.create'},
            {'id': 'customer_filing_create', 'label': '创建新客户备案', 'icon': '📋',
             'url_name': 'customer_pages:customer_filing_create',
             'permission': 'customer_management.client.create'},
            {'id': 'first_visit_create', 'label': '创建首次拜访', 'icon': '📅',
             'url_name': 'customer_pages:first_visit_create',
             'permission': 'customer_management.relationship.edit'},
            {'id': 'customer_public_sea', 'label': '客户公海', 'icon': '🌊',
             'url_name': 'customer_pages:customer_public_sea',
             'permission': 'customer_management.public_sea.view'},
        ]
    },
    {
        'id': 'customer_info',
        'label': '客户信息管理',
        'icon': '👥',
        'permission': 'customer_management.client.view',
        'children': [
            {'id': 'customer_list', 'label': '客户列表', 'icon': '📋',
             'url_name': 'customer_pages:customer_list',
             'permission': 'customer_management.client.view'},
            {'id': 'customer_create', 'label': '创建新客户', 'icon': '➕',
             'url_name': 'business_pages:customer_create',
             'permission': 'customer_management.client.create'},
        ]
    },
    {
        'id': 'customer_contact',
        'label': '人员信息管理',
        'icon': '👤',
        'permission': 'customer_management.contact.view',
        'children': [
            {'id': 'contact_list', 'label': '联系人列表', 'icon': '📇',
             'url_name': 'customer_pages:contact_list',
             'permission': 'customer_management.contact.view'},
        ]
    },
]


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
