# _legacy 视图函数依赖：从包内子模块导入，避免与已拆出的 redirects/menu/home 重复
from decimal import Decimal, InvalidOperation
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum, Q, F
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.urls import reverse, NoReverseMatch

from .common import (
    login_required as _login_required_from_common,
    get_user_permission_codes,
    _permission_granted,
    Client,
    ClientContact,
    ClientType,
    ClientGrade,
    CustomerLead,
    CustomerFiling,
    CustomerRelationship,
    VisitPlan,
    BusinessOpportunity,
    opportunity_can_view,
    opportunity_can_view_all,
    opportunity_can_create,
    opportunity_can_edit,
    opportunity_can_delete,
    opportunity_can_access_detail,
    opportunity_can_access_edit,
    logger,
)
from .menu import (
    _context,
    _build_customer_management_sidebar_nav,
    _build_opportunity_management_sidebar_nav,
    _check_customer_permission,
    _filter_clients_by_permission,
)
from .home import _get_opportunities_safely

# 保持与旧单文件一致的名称
login_required = _login_required_from_common
