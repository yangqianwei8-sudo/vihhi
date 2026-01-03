"""
风险管理模块页面视图
"""
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from django.urls import reverse, NoReverseMatch
import logging

from backend.apps.system_management.services import get_user_permission_codes
from backend.core.views import _permission_granted, _build_full_top_nav, _build_unified_sidebar_nav

logger = logging.getLogger(__name__)


# ==================== 菜单结构定义 ====================

RISK_MANAGEMENT_MENU = [
    {
        'id': 'risk_management_home',
        'label': '风险管理首页',
        'icon': '🏠',
        'url_name': 'risk_management:risk_management_home',
        'permission': 'risk_management.view',
    },
    # 注意：风险管理模块的其他功能待实现，这里预留扩展空间
    # {
    #     'id': 'risk_case',
    #     'label': '风险案例',
    #     'icon': '📋',
    #     'permission': 'risk_management.view',
    #     'children': [
    #         {
    #             'id': 'risk_case_list',
    #             'label': '案例列表',
    #             'icon': '📋',
    #             'url_name': 'risk_management:risk_case_list',
    #             'permission': 'risk_management.view',
    #         },
    #     ]
    # },
]


# ==================== 菜单生成函数 ====================

def _build_risk_management_sidebar_nav(permission_set, request_path=None, active_id=None):
    """生成风险管理左侧菜单（统一格式）"""
    # 使用统一的菜单构建函数
    return _build_unified_sidebar_nav(RISK_MANAGEMENT_MENU, permission_set, active_id=active_id)


def _context(page_title, page_icon, description, summary_cards=None, sections=None, request=None):
    """构建页面上下文"""
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
        context['module_sidebar_nav'] = _build_risk_management_sidebar_nav(permission_set, request.path, active_id=None)
    else:
        context['full_top_nav'] = []
        context['module_sidebar_nav'] = []
    
    return context


@login_required
def risk_management_home(request):
    """风险管理首页"""
    permission_codes = get_user_permission_codes(request.user)
    
    # 权限检查
    if not _permission_granted('risk_management.view', permission_codes):
        messages.error(request, '您没有权限访问风险管理')
        return redirect('admin:index')
    
    # 收集统计数据
    summary_cards = []
    
    # 注意：风险管理模块尚未实现，这里使用占位数据
    try:
        summary_cards.append({
            'label': '风险总数',
            'icon': '⚠️',
            'value': '0',
            'subvalue': '待实现',
            'url': '#',
            'variant': 'info'
        })
    except Exception:
        pass
    
    # 功能模块入口
    module_entries = []
    
    # 构建区域
    sections = []
    
    if module_entries:
        sections.append({
            'title': '功能模块',
            'description': '风险管理的各个功能模块入口',
            'items': module_entries,
            'layout': 'grid'
        })
    
    # 构建上下文
    context = _context(
        page_title="风险管理",
        page_icon="⚠️",
        description="识别和管理项目风险（待实现）",
        summary_cards=summary_cards,
        sections=sections,
        request=request,
    )
    
    return render(request, "risk_management/home.html", context)

