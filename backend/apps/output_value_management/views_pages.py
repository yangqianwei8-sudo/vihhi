# 产值管理视图（V1 收敛：仅首页 + 旧入口 410 Gone）
# 入口 /output-value/；权威计算见 services.calculator_v1，API 见 GET /api/output/v1/opportunity/<id>/

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from decimal import Decimal
from django.http import HttpResponse
from backend.apps.system_management.services import get_user_permission_codes
from backend.core.views import _permission_granted, _build_full_top_nav
from django.urls import reverse, NoReverseMatch
import logging

logger = logging.getLogger(__name__)


# ==================== 产值管理模块左侧菜单结构（V1 收敛：仅保留首页，旧模板/记录/统计已收敛至 API）=====================
OUTPUT_VALUE_MENU_STRUCTURE = [
    {
        'id': 'output_value_management_home',
        'label': '产值管理首页',
        'icon': '🏠',
        'url_name': 'output_value_pages:output_value_management_home',
        'permission': ['output_value_management.view'],
    },
]


def _build_output_value_sidebar_nav(permission_set, request_path=None, active_id=None):
    """生成产值管理模块左侧菜单"""
    try:
        from backend.core.views import _build_unified_sidebar_nav
        return _build_unified_sidebar_nav(OUTPUT_VALUE_MENU_STRUCTURE, permission_set, active_id=active_id)
    except ImportError:
        # Fallback实现：如果 _build_unified_sidebar_nav 不存在，提供简单实现
        nav = []
        for item in OUTPUT_VALUE_MENU_STRUCTURE:
            if item.get('permission') and not _permission_granted(item['permission'], permission_set):
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
                        'label': child.get('label', ''),
                        'icon': child.get('icon', ''),
                        'url': child_url,
                        'active': child.get('id') == active_id if active_id else False,
                    })
                
                nav_item['children'] = children
            
            nav.append(nav_item)
        
        return nav


def _context(page_title, page_icon, description, summary_cards=None, sections=None, request=None, active_menu_id=None):
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
        
        # 设置产值管理侧边栏
        context['sidebar_nav'] = _build_output_value_sidebar_nav(permission_set, request.path, active_id=active_menu_id)
        context['module_sidebar_nav'] = context['sidebar_nav']
        context['sidebar_title'] = '产值管理'
        context['sidebar_subtitle'] = 'Output Value Management'
    else:
        context['full_top_nav'] = []
        context['sidebar_nav'] = []
        context['module_sidebar_nav'] = []
        context['sidebar_title'] = '产值管理'
        context['sidebar_subtitle'] = 'Output Value Management'
    
    return context


def _output_value_v1_home_context(request):
    """V1 收敛后首页上下文：仅展示 API 说明，不依赖旧产值记录。"""
    permission_set = get_user_permission_codes(request.user)
    core_cards = [
        {
            'label': '动态产值 API（V1）',
            'icon': '📡',
            'value': 'GET /api/output/v1/opportunity/{id}/',
            'subvalue': '返回 dynamic_output、milestone_weight、confidence、stage、milestone',
            'url': None,
            'variant': 'primary',
        },
    ]
    page_context = _context(
        "产值管理 V1",
        "📊",
        "判断系统：按冻结文档实时计算动态产值，请通过 API 查询。接口文档见 backend/docs/output_value_v1_api.md",
        request=request,
        active_menu_id='output_value_management_home',
    )
    page_context['core_cards'] = core_cards
    page_context['todo_items'] = []
    page_context['pending_confirm_count'] = 0
    page_context['todo_summary_url'] = None
    page_context['my_work'] = {'my_records': [], 'my_records_count': 0, 'my_total_value': Decimal('0'), 'summary_url': None}
    page_context['recent_activities'] = {'recent_records': [], 'recent_confirmed': []}
    page_context['top_actions'] = []
    return page_context


@login_required
def output_value_management_home(request):
    """产值管理首页（V1 收敛）：仅展示 API 说明，不依赖旧产值记录。"""
    permission_set = get_user_permission_codes(request.user)
    has_permission = _permission_granted('output_value_management.view', permission_set)
    if not has_permission:
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("无权限访问产值管理")
    page_context = _output_value_v1_home_context(request)
    return render(request, "output_value_management/output_value_management_home.html", page_context)


@login_required
def output_value_410_gone(request, *args, **kwargs):
    """旧产值模板/记录/统计/项目维度入口：已废弃，返回 410 Gone。不得重定向。"""
    return HttpResponse(status=410, content_type='text/plain', content='Gone: 产值记录/模板/统计已废弃，请使用 GET /api/output/v1/opportunity/{id}/')




