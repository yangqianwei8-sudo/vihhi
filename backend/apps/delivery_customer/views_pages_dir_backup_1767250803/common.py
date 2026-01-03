"""
公共函数和配置模块 - 交付客户模块视图
包含菜单定义、上下文构建等公共功能
"""
import logging

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.urls import NoReverseMatch, reverse

from backend.apps.system_management.services import get_user_permission_codes
from backend.core.views import (
    HOME_NAV_STRUCTURE,
    _build_full_top_nav,
    _build_unified_sidebar_nav,
    _permission_granted,
)

logger = logging.getLogger(__name__)


# 使用统一的顶部导航菜单生成函数（已从 backend.core.views 导入）


# ==================== 收发管理模块左侧菜单结构 =====================
DELIVERY_MANAGEMENT_MENU = [
    {
        'id': 'incoming_document_home',
        'label': '收文管理首页',
        'icon': '🏠',
        'url_name': 'delivery_pages:incoming_document_home',
        'permission': 'delivery_center.view',
    },
    {
        'id': 'incoming_document',
        'label': '收文管理',
        'icon': '📥',
        'permission': 'delivery_center.view',
        'children': [
            {
                'id': 'incoming_document_list',
                'label': '收文列表',
                'icon': '📋',
                'url_name': 'delivery_pages:incoming_document_list',
                'permission': 'delivery_center.view',
            },
            {
                'id': 'incoming_document_create',
                'label': '创建收文',
                'icon': '➕',
                'url_name': 'delivery_pages:incoming_document_create',
                'permission': 'delivery_center.create',
            },
        ]
    },
    {
        'id': 'outgoing_document_home',
        'label': '发文管理首页',
        'icon': '🏠',
        'url_name': 'delivery_pages:outgoing_document_home',
        'permission': 'delivery_center.view',
    },
    {
        'id': 'outgoing_document',
        'label': '新建发文',
        'icon': '📤',
        'permission': 'delivery_center.view',
        'children': [
            {
                'id': 'outgoing_document_list',
                'label': '发文列表',
                'icon': '📋',
                'url_name': 'delivery_pages:outgoing_document_list',
                'permission': 'delivery_center.view',
            },
            {
                'id': 'outgoing_document_create',
                'label': '创建发文',
                'icon': '➕',
                'url_name': 'delivery_pages:outgoing_document_create',
                'permission': 'delivery_center.create',
            },
            {
                'id': 'outgoing_document_performance_report',
                'label': '效能报告',
                'icon': '📊',
                'url_name': 'delivery_pages:outgoing_document_performance_report',
                'permission': 'delivery_center.view',
            },
        ]
    },
    {
        'id': 'outgoing_document_receipt_list',
        'label': '发出跟踪',
        'icon': '✅',
        'permission': 'delivery_center.view',
        'children': [
            {
                'id': 'outgoing_document_receipt_list_item',
                'label': '跟踪列表',
                'icon': '📋',
                'url_name': 'delivery_pages:outgoing_document_receipt_list',
                'permission': 'delivery_center.view',
            },
            {
                'id': 'outgoing_document_receipt_create',
                'label': '新建报送',
                'icon': '➕',
                'url_name': 'delivery_pages:outgoing_document_create',
                'permission': 'delivery_center.create',
            },
        ]
    },
    {
        'id': 'express_company',
        'label': '快递公司管理',
        'icon': '🚚',
        'permission': 'delivery_center.view',
        'children': [
            {
                'id': 'express_company_list',
                'label': '快递公司列表',
                'icon': '📋',
                'url_name': 'delivery_pages:express_company_list',
                'permission': 'delivery_center.view',
            },
            {
                'id': 'express_company_create',
                'label': '新建快递公司',
                'icon': '➕',
                'url_name': 'delivery_pages:express_company_create',
                'permission': 'delivery_center.view',
            },
        ]
    },
    {
        'id': 'file_maintenance',
        'label': '文件维护',
        'icon': '📂',
        'permission': 'delivery_center.view',
        'children': [
            {
                'id': 'file_category_manage',
                'label': '创建文件分类',
                'icon': '➕',
                'url_name': 'delivery_pages:file_category_manage',
                'permission': 'delivery_center.view',
            },
            {
                'id': 'file_template_manage',
                'label': '文件模板维护',
                'icon': '📄',
                'url_name': 'delivery_pages:file_template_manage',
                'permission': 'delivery_center.view',
            },
        ]
    },
]


def _get_active_id_from_path(request_path):
    """
    从请求路径推断激活的菜单项ID
    
    参数:
        request_path: 请求路径
    
    返回:
        str: 激活的菜单项ID，如果无法推断则返回None
    """
    if not request_path:
        return None
    
    # URL路径到菜单ID的映射（按优先级从具体到一般排序）
    path_to_id_map = [
        ('/incoming-document/create', 'incoming_document_create'),
        ('/incoming-document/', 'incoming_document_home'),  # 首页
        ('/incoming-document/list/', 'incoming_document_list'),  # 列表
        ('/outgoing-document/home', 'outgoing_document_home'),
        ('/outgoing-document/create', 'outgoing_document_create'),
        ('/outgoing-document/receipt', 'outgoing_document_receipt_list_item'),  # 跟踪列表
        ('/outgoing-document/tracking', 'outgoing_document_receipt_list_item'),  # 跟踪详情
        ('/outgoing-document/performance-report', 'outgoing_document_performance_report'),
        ('/outgoing-document/', 'outgoing_document_list'),  # 包括列表、详情、编辑等
        ('/express-company/create', 'express_company_create'),  # 新建快递公司
        ('/express-company/', 'express_company_list'),
        ('/file-category/manage', 'file_category_manage'),
        ('/file-template/manage', 'file_template_manage'),
    ]
    
    for path_pattern, menu_id in path_to_id_map:
        if path_pattern in request_path:
            return menu_id
    
    return None


def _build_delivery_sidebar_nav(permission_set, request_path=None, active_id=None):
    """
    生成收发管理模块左侧菜单（统一格式）
    
    参数:
        permission_set: 用户权限集合（set）
        request_path: 请求路径（可选，用于推断active_id，已废弃，保留兼容）
        active_id: 当前激活的菜单项ID（优先使用）
    
    返回:
        list: 菜单项列表（统一格式）
    """
    # 如果没有提供active_id，尝试从request_path推断（兼容旧代码）
    if active_id is None and request_path:
        active_id = _get_active_id_from_path(request_path)
    
    # 根据路径判断应该显示哪些菜单组（保留此逻辑，因为收文和发文是不同模块）
    # 默认不显示任何菜单，必须明确匹配路径
    filtered_menu_groups = []
    if request_path:
        if '/incoming-document' in request_path:
            # 只显示收文管理相关的菜单
            filtered_menu_groups = [
                menu_group for menu_group in DELIVERY_MANAGEMENT_MENU
                if menu_group.get('id') in ['incoming_document_home', 'incoming_document']
            ]
        elif '/outgoing-document' in request_path or '/express-company' in request_path or '/file-category' in request_path or '/file-template' in request_path:
            # 只显示发文管理相关的菜单（包括首页、发出跟踪、快递公司管理、文件维护）
            # 明确排除收文管理菜单
            # 注意：快递公司管理和文件维护虽然URL路径不包含/outgoing-document，但它们属于发文管理模块
            filtered_menu_groups = [
                menu_group for menu_group in DELIVERY_MANAGEMENT_MENU
                if menu_group.get('id') in ['outgoing_document_home', 'outgoing_document', 'outgoing_document_receipt_list', 'express_company', 'file_maintenance']
            ]
    
    # 使用统一的菜单构建函数
    return _build_unified_sidebar_nav(filtered_menu_groups, permission_set, active_id=active_id)


def _context(page_title, page_icon, description, summary_cards=None, sections=None, request=None, active_menu_id=None):
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
        
        # 如果是发文管理相关页面，自动生成左侧菜单（与商机管理设计一致）
        # 注意：快递公司管理和文件维护虽然URL路径不包含/outgoing-document，但它们属于发文管理模块
        if request.path and ('/outgoing-document' in request.path or '/express-company' in request.path or '/file-category' in request.path or '/file-template' in request.path):
            # 根据路径确定激活的菜单项（与商机管理逻辑一致，优先使用路径判断）
            # 如果传入了active_menu_id参数，优先使用（允许视图函数覆盖）
            if active_menu_id is None:
                if '/outgoing-document/home' in request.path:
                    active_menu_id = 'outgoing_document_home'
                elif '/outgoing-document/create' in request.path:
                    active_menu_id = 'outgoing_document_create'
                elif '/outgoing-document/receipt' in request.path or '/outgoing-document/tracking' in request.path:
                    active_menu_id = 'outgoing_document_receipt_list_item'
                elif '/outgoing-document/performance-report' in request.path:
                    active_menu_id = 'outgoing_document_performance_report'
                elif '/outgoing-document/' in request.path:
                    active_menu_id = 'outgoing_document_list'
                elif '/express-company/create' in request.path:
                    active_menu_id = 'express_company_create'
                elif '/express-company/' in request.path:
                    active_menu_id = 'express_company_list'
                elif '/file-category/manage' in request.path:
                    active_menu_id = 'file_category_manage'
                elif '/file-template/manage' in request.path:
                    active_menu_id = 'file_template_manage'
            
            context['module_sidebar_nav'] = _build_delivery_sidebar_nav(permission_set, request.path, active_id=active_menu_id)
            context['delivery_sidebar_nav'] = context['module_sidebar_nav']  # 保留兼容
        # 如果是收文管理相关页面，自动生成左侧菜单
        elif request.path and '/incoming-document' in request.path:
            # 根据路径确定激活的菜单项（与商机管理逻辑一致）
            active_menu_id = None
            if '/incoming-document/home' in request.path or (request.path == '/delivery/incoming-document/' or request.path == '/delivery/incoming-document'):
                active_menu_id = 'incoming_document_home'
            elif '/incoming-document/create' in request.path:
                active_menu_id = 'incoming_document_create'
            elif '/incoming-document/list' in request.path:
                active_menu_id = 'incoming_document_list'
            elif '/incoming-document/' in request.path:
                # 详情页或编辑页，激活列表菜单
                active_menu_id = 'incoming_document_list'
            
            context['module_sidebar_nav'] = _build_delivery_sidebar_nav(permission_set, request.path, active_id=active_menu_id)
            context['delivery_sidebar_nav'] = context['module_sidebar_nav']  # 保留兼容
        else:
            # 其他情况，使用默认菜单生成逻辑
            context['module_sidebar_nav'] = _build_delivery_sidebar_nav(permission_set, request.path, active_id=active_menu_id)
            context['delivery_sidebar_nav'] = context['module_sidebar_nav']  # 保留兼容
    else:
        context['full_top_nav'] = []
        context['module_sidebar_nav'] = []
        context['delivery_sidebar_nav'] = []
    
    return context


