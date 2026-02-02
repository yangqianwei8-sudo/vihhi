# 计划管理页面视图 - 公共依赖
from decimal import Decimal, InvalidOperation
import logging
import json
from datetime import datetime, timedelta, date

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

from backend.apps.system_management.services import get_user_permission_codes
from backend.apps.system_management.models import User, Department

try:
    from backend.core.views import _permission_granted, _build_full_top_nav, _build_unified_sidebar_nav
except ImportError:
    from backend.core.views import _permission_granted, _build_full_top_nav
    from django.urls import reverse, NoReverseMatch

    def _build_unified_sidebar_nav(menu_structure, permission_set, active_id=None):
        """Fallback: 简单的侧边栏菜单构建函数（支持 url_name 转换）"""
        nav = []
        for item in menu_structure:
            if item.get('permission'):
                perms = item['permission']
                if isinstance(perms, list):
                    if not any(_permission_granted(p, permission_set) for p in perms):
                        continue
                elif not _permission_granted(perms, permission_set):
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
                        perms = child['permission']
                        if isinstance(perms, list):
                            if not any(_permission_granted(p, permission_set) for p in perms):
                                continue
                        elif not _permission_granted(perms, permission_set):
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
                        'id': child.get('id'),
                        'label': child.get('label', ''),
                        'icon': child.get('icon', ''),
                        'url': child_url,
                        'active': child.get('id') == active_id if active_id else False,
                    })
                if not children:
                    continue
                nav_item['children'] = children
                if nav_item['url'] == '#':
                    nav_item['url'] = children[0].get('url', '#')
                if any(child.get('active') for child in children):
                    nav_item['active'] = True
                    nav_item['expanded'] = True
                elif item.get('expanded', False):
                    nav_item['expanded'] = True
            nav.append(nav_item)
        return nav

from backend.apps.plan_management.models import (
    GoalAdjustment,
    GoalProgressRecord,
    GoalStatusLog,
    Plan,
    PlanAdjustment,
    PlanDecision,
    PlanIssue,
    PlanProgressRecord,
    PlanStatusLog,
    StrategicGoal,
)
from backend.apps.plan_management.forms import (
    StrategicGoalForm,
    GoalProgressUpdateForm,
    GoalAdjustmentForm,
    PlanForm,
    PlanProgressUpdateForm,
    PlanIssueForm,
    PlanAdjustmentForm,
    PlanItemFormSet,
)

logger = logging.getLogger(__name__)
