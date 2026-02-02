# 客户管理页面视图 - 公共依赖（供各子模块引用，避免循环导入）
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
from backend.apps.opportunity_management.models import (
    BusinessOpportunity,
    OpportunityFollowUp,
    OpportunityQuotation,
    BusinessNegotiation,
    BiddingQuotation,
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
from backend.apps.system_management.services import get_user_permission_codes
from backend.core.views import HOME_NAV_STRUCTURE, _permission_granted, _build_full_top_nav
from backend.apps.permission_management.utils import normalize_permission_code
from backend.apps.opportunity_management.perm_check import (
    opportunity_can_view,
    opportunity_can_view_all,
    opportunity_can_create,
    opportunity_can_edit,
    opportunity_can_delete,
    opportunity_can_manage,
    opportunity_can_access_detail,
    opportunity_can_access_edit,
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
