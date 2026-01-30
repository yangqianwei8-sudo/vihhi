# 文档管理视图（收文管理与发文管理）
# 从delivery_customer迁移而来

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.urls import reverse, NoReverseMatch
from django.utils import timezone
from django.db.models import F
from datetime import timedelta
import logging

from backend.apps.system_management.services import get_user_permission_codes
from backend.core.views import HOME_NAV_STRUCTURE, _permission_granted, _build_full_top_nav, _build_scene_groups
from backend.apps.production_management.models import Project

# Fallback: 如果 _build_unified_sidebar_nav 不存在，提供简单实现
try:
    from backend.core.views import _build_unified_sidebar_nav
except ImportError:
    def _build_unified_sidebar_nav(menu_structure, permission_set, active_id=None):
        """简单的侧边栏导航构建函数（fallback）"""
        nav = []
        for item in menu_structure:
            if item.get('permission') and not _permission_granted(item['permission'], permission_set):
                continue
            nav_item = {
                'label': item.get('label', ''),
                'url': reverse(item['url_name']) if item.get('url_name') else '#',
                'active': item.get('id') == active_id,
            }
            if item.get('children'):
                nav_item['children'] = []
                for child in item['children']:
                    if child.get('permission') and not _permission_granted(child['permission'], permission_set):
                        continue
                    nav_item['children'].append({
                        'label': child.get('label', ''),
                        'url': reverse(child['url_name']) if child.get('url_name') else '#',
                        'active': child.get('id') == active_id,
                    })
            nav.append(nav_item)
        return nav

logger = logging.getLogger(__name__)

def _context(page_title, page_icon, description, summary_cards=None, sections=None, request=None, active_menu_id=None):
    """
    构建页面上下文
    
    参数:
        page_title: 页面标题
        page_icon: 页面图标
        description: 页面描述
        summary_cards: 摘要卡片列表
        sections: 章节列表
        request: 请求对象
        active_menu_id: 激活的菜单项ID（可选，如果提供则优先使用）
    
    返回:
        dict: 页面上下文
    """
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
        
        # 根据路径自动选择收文或发文菜单
        if request.path:
            if '/incoming' in request.path or '/documents/incoming' in request.path:
                # 收文管理菜单
                context['sidebar_nav'] = _build_incoming_document_sidebar_nav(permission_set, request.path, active_id=active_menu_id)
                context['module_sidebar_nav'] = context['sidebar_nav']  # 兼容变量
                context['sidebar_title'] = '收文管理'
                context['sidebar_subtitle'] = 'Incoming Document'
            elif '/outgoing' in request.path or '/documents/outgoing' in request.path or '/file-category' in request.path or '/file-template' in request.path or '/documents/file-category' in request.path or '/documents/file-template' in request.path:
                # 发文管理菜单
                context['sidebar_nav'] = _build_outgoing_document_sidebar_nav(permission_set, request.path, active_id=active_menu_id)
                context['module_sidebar_nav'] = context['sidebar_nav']  # 兼容变量
                context['sidebar_title'] = '发文管理'
                context['sidebar_subtitle'] = 'Outgoing Document'
            else:
                # 其他路径，使用兼容函数（向后兼容）
                context['sidebar_nav'] = _build_delivery_sidebar_nav(permission_set, request.path, active_id=active_menu_id)
                context['module_sidebar_nav'] = context['sidebar_nav']  # 兼容变量
                context['sidebar_title'] = '文档管理'
                context['sidebar_subtitle'] = 'Document Management'
        else:
            context['sidebar_nav'] = []
            context['module_sidebar_nav'] = []
            context['sidebar_title'] = '文档管理'
            context['sidebar_subtitle'] = 'Document Management'
    else:
        context['full_top_nav'] = []
        context['sidebar_nav'] = []
        context['module_sidebar_nav'] = []
        context['sidebar_title'] = '文档管理'
        context['sidebar_subtitle'] = 'Document Management'
    
    return context

def _format_user_display(user):
    """格式化用户显示名称"""
    if not user:
        return '系统'
    return user.get_full_name() or user.username

# ========== INCOMING_DOCUMENT_MENU_STRUCTURE ==========
INCOMING_DOCUMENT_MENU_STRUCTURE = [
    {
        'id': 'incoming_document_home',
        'label': '收文管理首页',
        'icon': '🏠',
        'url_name': 'document_pages:incoming_document_home',
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
                'url_name': 'document_pages:incoming_document_list',
                'permission': 'delivery_center.view',
            },
            {
                'id': 'incoming_document_create',
                'label': '创建收文',
                'icon': '➕',
                'url_name': 'document_pages:incoming_document_create',
                'permission': 'delivery_center.create',
            },
        ]
    },
]

# ========== OUTGOING_DOCUMENT_MENU_STRUCTURE ==========
OUTGOING_DOCUMENT_MENU_STRUCTURE = [
    {
        'id': 'outgoing_document_home',
        'label': '发文管理首页',
        'icon': '🏠',
        'url_name': 'document_pages:outgoing_document_home',
        'permission': 'delivery_center.view',
    },
    {
        'id': 'outgoing_document',
        'label': '发文管理',
        'icon': '📤',
        'permission': 'delivery_center.view',
        'children': [
            {
                'id': 'outgoing_document_list',
                'label': '发文列表',
                'icon': '📋',
                'url_name': 'document_pages:outgoing_document_list',
                'permission': 'delivery_center.view',
            },
            {
                'id': 'outgoing_document_create',
                'label': '创建发文',
                'icon': '➕',
                'url_name': 'document_pages:outgoing_document_create',
                'permission': 'delivery_center.create',
            },
            # 效能报告功能待实现
            # {
            #     'id': 'outgoing_document_performance_report',
            #     'label': '效能报告',
            #     'icon': '📊',
            #     'url_name': 'document_pages:outgoing_document_performance_report',
            #     'permission': 'delivery_center.view',
            # },
        ]
    },
    # 发出跟踪功能待实现
    # {
    #     'id': 'outgoing_document_receipt',
    #     'label': '发出跟踪',
    #     'icon': '✅',
    #     'permission': 'delivery_center.view',
    #     'children': [
    #         {
    #             'id': 'outgoing_document_receipt_list',
    #             'label': '跟踪列表',
    #             'icon': '📋',
    #             'url_name': 'document_pages:outgoing_document_receipt_list',
    #             'permission': 'delivery_center.view',
    #         },
    #     ]
    # },
    # 注意：快递公司管理已保留在 delivery_customer 模块中，不在此处
    # 如需访问快递公司管理，请使用 delivery_pages:express_company_list
    {
        'id': 'file_maintenance',
        'label': '文件维护',
        'icon': '📂',
        'permission': 'delivery_center.view',
        'children': [
            {
                'id': 'file_category_manage',
                'label': '文件分类管理',
                'icon': '📁',
                'url_name': 'document_pages:file_category_manage',
                'permission': 'delivery_center.view',
            },
            {
                'id': 'file_template_manage',
                'label': '文件模板维护',
                'icon': '📄',
                'url_name': 'document_pages:file_template_manage',
                'permission': 'delivery_center.view',
            },
        ]
    },
]

# ========== _get_active_id_from_path ==========
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
    
    # URL路径到菜单ID的映射（收文管理）
    # 注意：实际URL路径是 /documents/incoming/...，但这里只匹配相对路径
    incoming_path_to_id_map = {
        '/documents/incoming/home': 'incoming_document_home',
        '/documents/incoming/create': 'incoming_document_create',
        '/documents/incoming/': 'incoming_document_list',
        '/documents/incoming': 'incoming_document_list',  # 兼容不带斜杠的路径
        '/incoming/home': 'incoming_document_home',  # 兼容相对路径
        '/incoming/create': 'incoming_document_create',
        '/incoming/': 'incoming_document_list',
        '/incoming': 'incoming_document_list',
    }
    
    # URL路径到菜单ID的映射（发文管理）
    outgoing_path_to_id_map = {
        '/documents/outgoing/home': 'outgoing_document_home',
        '/documents/outgoing/create': 'outgoing_document_create',
        '/documents/outgoing/': 'outgoing_document_list',
        '/documents/outgoing': 'outgoing_document_list',  # 兼容不带斜杠的路径
        '/outgoing/home': 'outgoing_document_home',  # 兼容相对路径
        '/outgoing/create': 'outgoing_document_create',
        '/outgoing/': 'outgoing_document_list',
        '/outgoing': 'outgoing_document_list',
        '/documents/file-category/manage': 'file_category_manage',
        '/documents/file-category/': 'file_category_manage',
        '/file-category/manage': 'file_category_manage',
        '/file-category/': 'file_category_manage',
        '/documents/file-template/manage': 'file_template_manage',
        '/documents/file-template/': 'file_template_manage',
        '/file-template/manage': 'file_template_manage',
        '/file-template/': 'file_template_manage',
    }
    
    # 先检查收文管理路径
    for path_pattern, menu_id in incoming_path_to_id_map.items():
        if path_pattern in request_path:
            return menu_id
    
    # 再检查发文管理路径
    for path_pattern, menu_id in outgoing_path_to_id_map.items():
        if path_pattern in request_path:
            return menu_id
    
    return None

# ========== _build_incoming_document_sidebar_nav ==========
def _build_incoming_document_sidebar_nav(permission_set, request_path=None, active_id=None):
    """
    生成收文管理模块左侧菜单（独立菜单）
    
    参数:
        permission_set: 用户权限集合（set）
        request_path: 请求路径（可选，用于推断active_id）
        active_id: 当前激活的菜单项ID（可选，如果提供则优先使用）
    
    返回:
        list: 菜单项列表（统一格式）
    """
    # 如果没有提供active_id，尝试从request_path推断
    if active_id is None and request_path:
        active_id = _get_active_id_from_path(request_path)
    
    # 使用统一的菜单构建函数
    return _build_unified_sidebar_nav(INCOMING_DOCUMENT_MENU_STRUCTURE, permission_set, active_id=active_id)

# ========== _build_outgoing_document_sidebar_nav ==========
def _build_outgoing_document_sidebar_nav(permission_set, request_path=None, active_id=None):
    """
    生成发文管理模块左侧菜单（独立菜单）
    
    参数:
        permission_set: 用户权限集合（set）
        request_path: 请求路径（可选，用于推断active_id）
        active_id: 当前激活的菜单项ID（可选，如果提供则优先使用）
    
    返回:
        list: 菜单项列表（统一格式）
    """
    # 如果没有提供active_id，尝试从request_path推断
    if active_id is None and request_path:
        active_id = _get_active_id_from_path(request_path)
    
    # 使用统一的菜单构建函数
    return _build_unified_sidebar_nav(OUTGOING_DOCUMENT_MENU_STRUCTURE, permission_set, active_id=active_id)

# ========== _build_delivery_sidebar_nav ==========
def _build_delivery_sidebar_nav(permission_set, request_path=None, active_id=None):
    """
    生成收发管理模块左侧菜单（兼容函数，根据路径自动选择收文或发文菜单）
    
    注意：此函数已废弃，建议直接使用 _build_incoming_document_sidebar_nav 或 _build_outgoing_document_sidebar_nav
    
    参数:
        permission_set: 用户权限集合（set）
        request_path: 请求路径（可选，用于推断active_id和选择菜单类型）
        active_id: 当前激活的菜单项ID（可选，如果提供则优先使用）
    
    返回:
        list: 菜单项列表
    """
    # 根据路径自动选择收文或发文菜单
    if request_path:
        if '/incoming' in request_path or '/documents/incoming' in request_path:
            return _build_incoming_document_sidebar_nav(permission_set, request_path, active_id)
        elif '/outgoing' in request_path or '/documents/outgoing' in request_path or '/file-category' in request_path or '/file-template' in request_path or '/documents/file-category' in request_path or '/documents/file-template' in request_path:
            return _build_outgoing_document_sidebar_nav(permission_set, request_path, active_id)
    
    # 默认返回空菜单（如果无法判断路径）
    return []

# ========== incoming_document_home ==========
@login_required
def incoming_document_home(request):
    """收文管理首页 - 数据展示中心"""
    from django.db.models import Avg, Count
    from datetime import datetime
    from backend.apps.document_management.models import IncomingDocument
    
    permission_set = get_user_permission_codes(request.user)
    if not _permission_granted('delivery_center.view', permission_set):
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("无权限访问收文管理")
    
    now = timezone.now()
    today = now.date()
    this_month_start = today.replace(day=1)
    seven_days_ago = today - timedelta(days=7)
    
    all_documents = IncomingDocument.objects.all()
    
    context = {}
    
    try:
        # ========== 核心指标卡片 ==========
        core_cards = []
        
        # 收文统计
        total_documents = all_documents.count()
        draft_documents = all_documents.filter(status='draft').count()
        registered_documents = all_documents.filter(status='registered').count()
        processing_documents = all_documents.filter(status='processing').count()
        completed_documents = all_documents.filter(status='completed').count()
        archived_documents = all_documents.filter(status='archived').count()
        this_month_documents = all_documents.filter(created_at__gte=this_month_start).count()
        this_month_completed_documents = all_documents.filter(
            status='completed',
            completed_at__gte=this_month_start
        ).count()
        
        # 卡片1：收文总数
        core_cards.append({
            'label': '收文总数',
            'icon': '📥',
            'value': str(total_documents),
            'subvalue': f'草稿 {draft_documents} | 处理中 {processing_documents} | 已完成 {completed_documents} | 已归档 {archived_documents}',
            'url': reverse('document_pages:incoming_document_list'),
            'variant': 'secondary'
        })
        
        # 卡片2：处理中收文
        core_cards.append({
            'label': '处理中收文',
            'icon': '⚡',
            'value': str(processing_documents),
            'subvalue': f'已登记 {registered_documents} | 处理中 {processing_documents}',
            'url': reverse('document_pages:incoming_document_list') + '?status=processing',
            'variant': 'dark'
        })
        
        # 卡片3：已完成收文
        core_cards.append({
            'label': '已完成收文',
            'icon': '✅',
            'value': str(completed_documents),
            'subvalue': f'本月完成 {this_month_completed_documents} 个',
            'url': reverse('document_pages:incoming_document_list') + '?status=completed',
            'variant': 'secondary'
        })
        
        # 卡片4：待登记收文
        core_cards.append({
            'label': '待登记收文',
            'icon': '📋',
            'value': str(draft_documents),
            'subvalue': f'等待登记',
            'url': reverse('document_pages:incoming_document_list') + '?status=draft',
            'variant': 'dark' if draft_documents > 0 else 'secondary'
        })
        
        # 卡片5：已登记收文
        core_cards.append({
            'label': '已登记收文',
            'icon': '📝',
            'value': str(registered_documents),
            'subvalue': f'等待处理',
            'url': reverse('document_pages:incoming_document_list') + '?status=registered',
            'variant': 'dark' if registered_documents > 0 else 'secondary'
        })
        
        # 卡片6：本月新增
        core_cards.append({
            'label': '本月新增',
            'icon': '📈',
            'value': str(this_month_documents),
            'subvalue': f'新收文 {this_month_documents} 个',
            'url': reverse('document_pages:incoming_document_list'),
            'variant': 'secondary'
        })
        
        context['core_cards'] = core_cards
        
        # ========== 风险预警 ==========
        risk_warnings = []
        
        # 7天未处理收文
        stale_documents = all_documents.filter(
            status__in=['registered', 'processing'],
            updated_at__lt=timezone.make_aware(datetime.combine(seven_days_ago, datetime.min.time()))
        ).select_related('handler', 'created_by')[:5]
        
        for doc in stale_documents:
            days_since_update = (today - doc.updated_at.date()).days
            handler_name = _format_user_display(doc.handler) if doc.handler else '未分配'
            risk_warnings.append({
                'type': 'stale',
                'title': doc.title,
                'responsible': handler_name,
                'days': days_since_update,
                'url': reverse('document_pages:incoming_document_detail', args=[doc.id])
            })
        
        context['risk_warnings'] = risk_warnings[:5]
        context['stale_documents_count'] = all_documents.filter(
            status__in=['registered', 'processing'],
            updated_at__lt=timezone.make_aware(datetime.combine(seven_days_ago, datetime.min.time()))
        ).count()
        context['overdue_documents_count'] = 0
        
        # ========== 待办事项 ==========
        todo_items = []
        
        # 待登记收文
        draft_list = all_documents.filter(status='draft').select_related('created_by')[:5]
        for doc in draft_list:
            creator_name = _format_user_display(doc.created_by) if doc.created_by else '系统'
            todo_items.append({
                'type': 'register',
                'title': doc.title,
                'document_number': doc.document_number,
                'responsible': creator_name,
                'url': reverse('document_pages:incoming_document_detail', args=[doc.id])
            })
        
        # 待处理收文
        processing_list = all_documents.filter(status='processing').select_related('handler')[:5]
        for doc in processing_list:
            handler_name = _format_user_display(doc.handler) if doc.handler else '未分配'
            todo_items.append({
                'type': 'process',
                'title': doc.title,
                'document_number': doc.document_number,
                'responsible': handler_name,
                'url': reverse('document_pages:incoming_document_detail', args=[doc.id])
            })
        
        context['todo_items'] = todo_items[:10]
        context['pending_approval_count'] = draft_documents + processing_documents
        context['todo_summary_url'] = reverse('document_pages:incoming_document_list') + '?status=draft'
        
        # ========== 我的工作 ==========
        my_work = {}
        
        # 我创建的收文
        my_created_documents = all_documents.filter(created_by=request.user).order_by('-created_at')[:3]
        my_work['my_documents'] = [{
            'title': doc.title,
            'status': doc.get_status_display(),
            'url': reverse('document_pages:incoming_document_detail', args=[doc.id])
        } for doc in my_created_documents]
        my_work['my_documents_count'] = all_documents.filter(created_by=request.user).count()
        
        # 我处理的收文
        my_handled_documents = all_documents.filter(handler=request.user).order_by('-updated_at')[:3]
        my_work['handled_documents'] = [{
            'title': doc.title,
            'status': doc.get_status_display(),
            'url': reverse('document_pages:incoming_document_detail', args=[doc.id])
        } for doc in my_handled_documents]
        my_work['handled_documents_count'] = all_documents.filter(handler=request.user).count()
        
        my_work['summary_url'] = reverse('document_pages:incoming_document_list') + f'?created_by={request.user.id}'
        
        context['my_work'] = my_work
        
        # ========== 最近活动 ==========
        recent_activities = {}
        
        # 最近创建的收文
        recent_documents = all_documents.select_related('created_by').order_by('-created_at')[:5]
        recent_activities['recent_documents'] = [{
            'title': doc.title,
            'creator': _format_user_display(doc.created_by),
            'time': doc.created_at,
            'url': reverse('document_pages:incoming_document_detail', args=[doc.id])
        } for doc in recent_documents]
        
        # 最近更新的收文（排除创建）
        recent_updates = all_documents.exclude(
            created_at=F('updated_at')
        ).select_related('updated_by').order_by('-updated_at')[:5]
        recent_activities['recent_updates'] = [{
            'title': doc.title,
            'updater': _format_user_display(doc.handler) if doc.handler else '系统',
            'time': doc.updated_at,
            'url': reverse('document_pages:incoming_document_detail', args=[doc.id])
        } for doc in recent_updates]
        
        context['recent_activities'] = recent_activities
        
    except Exception as e:
        logger.exception('获取收文管理统计数据失败: %s', str(e))
        context.setdefault('core_cards', [])
        context.setdefault('risk_warnings', [])
        context.setdefault('todo_items', [])
        context.setdefault('my_work', {})
        context.setdefault('recent_activities', {})
    
    # 顶部操作栏
    top_actions = []
    if _permission_granted('delivery_center.create', permission_set):
        try:
            top_actions.append({
                'label': '创建收文',
                'url': reverse('document_pages:incoming_document_create'),
                'icon': '➕'
            })
        except Exception:
            pass
    
    context['top_actions'] = top_actions
    
    # 构建上下文
    page_context = _context(
        "收文管理",
        "📥",
        "数据展示中心 - 集中展示收文关键指标、状态与风险",
        request=request,
    )
    
    # 设置侧边栏导航（使用收文管理独立菜单）
    document_sidebar_nav = _build_incoming_document_sidebar_nav(permission_set, request.path, active_id='incoming_document_home')
    page_context['sidebar_nav'] = document_sidebar_nav
    page_context['module_sidebar_nav'] = document_sidebar_nav
    page_context['sidebar_title'] = '收文管理'
    page_context['sidebar_subtitle'] = 'Incoming Document'
    
    # 合并所有数据
    page_context.update(context)
    
    return render(request, "document_management/incoming_document_home.html", page_context)

# ========== incoming_document_list ==========
@login_required
def incoming_document_list(request):
    """收文列表"""
    from django.core.paginator import Paginator
    from django.db.models import Q
    from backend.apps.document_management.models import IncomingDocument
    
    permission_set = get_user_permission_codes(request.user)
    document_sidebar_nav = _build_incoming_document_sidebar_nav(permission_set, request.path, active_id='incoming_document_list')
    
    # 获取查询参数
    search = request.GET.get('search', '').strip()
    status_filter = request.GET.get('status', '').strip()
    if not status_filter:
        status_filter = 'all'
    priority_filter = request.GET.get('priority', '').strip()
    if not priority_filter:
        priority_filter = 'all'
    stage_filter = request.GET.get('stage', '').strip()
    if not stage_filter:
        stage_filter = 'all'
    category_filter = request.GET.get('category', '').strip()
    if not category_filter:
        category_filter = 'all'
    
    # 统计数据（在过滤之前获取，显示全部数据统计）
    all_documents = IncomingDocument.objects.all()
    total_count = all_documents.count()
    draft_count = all_documents.filter(status='draft').count()
    registered_count = all_documents.filter(status='registered').count()
    processing_count = all_documents.filter(status='processing').count()
    completed_count = all_documents.filter(status='completed').count()
    archived_count = all_documents.filter(status='archived').count()
    
    # 查询收文
    documents = IncomingDocument.objects.all()
    
    # 搜索过滤
    if search:
        documents = documents.filter(
            Q(document_number__icontains=search) |
            Q(title__icontains=search) |
            Q(sender__icontains=search) |
            Q(sender_contact__icontains=search)
        )
    
    # 状态过滤
    if status_filter != 'all':
        documents = documents.filter(status=status_filter)
    
    # 优先级过滤
    if priority_filter != 'all':
        documents = documents.filter(priority=priority_filter)
    
    # 阶段过滤
    if stage_filter != 'all':
        documents = documents.filter(stage=stage_filter)
    
    # 文件分类过滤
    if category_filter != 'all':
        try:
            category_id = int(category_filter)
            documents = documents.filter(file_category_id=category_id)
        except (ValueError, TypeError):
            pass
    
    # 排序
    documents = documents.order_by('-receive_date', '-created_at')
    
    # 分页（每页20条）
    paginator = Paginator(documents, 20)
    page_number = request.GET.get('page', 1)
    try:
        documents_page = paginator.page(page_number)
    except:
        documents_page = paginator.page(1)
    
    context = _context(
        "收文列表",
        "📥",
        "管理收到的文件记录",
        request=request,
    )
    
    # 获取文件分类数据（用于下拉选择）
    from backend.apps.document_management.models import FileCategory
    categories = FileCategory.objects.filter(is_active=True).order_by('stage', 'sort_order', 'name')
    categories_by_stage = {}
    for category in categories:
        if category.stage not in categories_by_stage:
            categories_by_stage[category.stage] = []
        categories_by_stage[category.stage].append(category)
    
    # 生成左侧菜单（类似计划管理的 plan_menu）
    context['sidebar_nav'] = document_sidebar_nav
    context['module_sidebar_nav'] = document_sidebar_nav  # 兼容模板中的变量名
    context['sidebar_title'] = '收文管理'  # 侧边栏标题
    context['sidebar_subtitle'] = 'Incoming Document'  # 侧边栏副标题
    
    context.update({
        'documents': documents_page,
        'search': search,
        'search_query': search,  # 保持向后兼容
        'status_filter': status_filter,
        'priority_filter': priority_filter,
        'stage_filter': stage_filter,
        'category_filter': category_filter,
        'status_choices': IncomingDocument.STATUS_CHOICES,
        'priority_choices': IncomingDocument.PRIORITY_CHOICES,
        'stage_choices': IncomingDocument.STAGE_CHOICES,
        'categories': categories,
        'categories_by_stage': categories_by_stage,
        'can_create': _permission_granted('delivery_center.create', permission_set),
        'total_count': total_count,
        'draft_count': draft_count,
        'registered_count': registered_count,
        'processing_count': processing_count,
        'completed_count': completed_count,
        'archived_count': archived_count,
    })
    return render(request, "document_management/incoming_document_list.html", context)

# ========== incoming_document_create ==========
@login_required
def incoming_document_create(request):
    """收文创建"""
    from django.shortcuts import redirect
    from django.contrib import messages
    from django.utils import timezone
    from backend.apps.document_management.models import IncomingDocument
    
    permission_set = get_user_permission_codes(request.user)
    document_sidebar_nav = _build_incoming_document_sidebar_nav(permission_set, request.path)
    
    if not _permission_granted('delivery_center.create', permission_set):
        messages.error(request, '您没有创建收文的权限')
        return redirect('document_pages:incoming_document_list')
    
    if request.method == 'POST':
        try:
            # 生成收文编号
            today = timezone.now().date()
            year = today.strftime('%Y')
            count = IncomingDocument.objects.filter(
                document_number__startswith=f'SW{year}'
            ).count() + 1
            document_number = f'SW{year}{count:04d}'
            
            # 确保编号唯一
            while IncomingDocument.objects.filter(document_number=document_number).exists():
                count += 1
                document_number = f'SW{year}{count:04d}'
            
            # 处理阶段和文件分类
            stage = request.POST.get('stage', '').strip() or None
            file_category_id = request.POST.get('file_category', '').strip() or None
            
            document = IncomingDocument(
                document_number=document_number,
                title=request.POST.get('title', '').strip(),
                sender=request.POST.get('sender', '').strip(),
                sender_contact=request.POST.get('sender_contact', '').strip(),
                sender_phone=request.POST.get('sender_phone', '').strip(),
                document_date=request.POST.get('document_date') or None,
                receive_date=request.POST.get('receive_date') or None,
                document_type=request.POST.get('document_type', '').strip(),
                content=request.POST.get('content', '').strip(),
                summary=request.POST.get('summary', '').strip(),
                status=request.POST.get('status', 'draft'),
                priority=request.POST.get('priority', 'normal'),
                stage=stage,
                file_category_id=file_category_id,
                handler_id=request.POST.get('handler') or None,
                handle_notes=request.POST.get('handle_notes', '').strip(),
                notes=request.POST.get('notes', '').strip(),
                created_by=request.user,
            )
            
            # 处理附件
            if 'attachment' in request.FILES:
                document.attachment = request.FILES['attachment']
            
            document.save()
            messages.success(request, f'收文"{document.title}"创建成功')
            return redirect('document_pages:incoming_document_detail', document_id=document.id)
        except Exception as e:
            logger.error(f"创建收文失败: {str(e)}")
            messages.error(request, f'创建失败：{str(e)}')
    
    # 获取用户列表（用于选择处理人）
    from django.contrib.auth import get_user_model
    User = get_user_model()
    users = User.objects.filter(is_active=True).order_by('username')
    
    context = _context(
        "收文创建",
        "➕",
        "创建新的收文记录",
        request=request,
    )
    # 获取文件分类数据
    from backend.apps.document_management.models import FileCategory
    categories = FileCategory.objects.filter(is_active=True).order_by('stage', 'sort_order', 'name')
    categories_by_stage = {}
    for category in categories:
        if category.stage not in categories_by_stage:
            categories_by_stage[category.stage] = []
        categories_by_stage[category.stage].append(category)
    
    context["document_sidebar_nav"] = document_sidebar_nav
    context["sidebar_nav"] = document_sidebar_nav  # 兼容模板中的变量名
    context["module_sidebar_nav"] = document_sidebar_nav
    context["status_choices"] = IncomingDocument.STATUS_CHOICES
    context["priority_choices"] = IncomingDocument.PRIORITY_CHOICES
    context["stage_choices"] = IncomingDocument.STAGE_CHOICES
    context["categories"] = categories
    context["categories_by_stage"] = categories_by_stage
    context["users"] = users
    return render(request, "document_management/incoming_document_create.html", context)

# ========== incoming_document_detail ==========
@login_required
def incoming_document_detail(request, document_id):
    """收文详情"""
    from django.shortcuts import get_object_or_404
    from backend.apps.document_management.models import IncomingDocument
    
    permission_set = get_user_permission_codes(request.user)
    document_sidebar_nav = _build_incoming_document_sidebar_nav(permission_set, request.path)
    
    document = get_object_or_404(IncomingDocument, id=document_id)
    
    context = _context(
        "收文详情",
        "📥",
        "查看收文详细信息",
        request=request,
    )
    context["document_sidebar_nav"] = document_sidebar_nav
    context["sidebar_nav"] = document_sidebar_nav  # 兼容模板中的变量名
    context["module_sidebar_nav"] = document_sidebar_nav
    context["document"] = document
    context["can_edit"] = _permission_granted('delivery_center.create', permission_set)
    return render(request, "document_management/incoming_document_detail.html", context)

# ========== incoming_document_edit ==========
@login_required
def incoming_document_edit(request, document_id):
    """收文编辑"""
    from django.shortcuts import redirect, get_object_or_404
    from django.contrib import messages
    from backend.apps.document_management.models import IncomingDocument
    
    permission_set = get_user_permission_codes(request.user)
    document_sidebar_nav = _build_incoming_document_sidebar_nav(permission_set, request.path)
    
    if not _permission_granted('delivery_center.create', permission_set):
        messages.error(request, '您没有编辑收文的权限')
        return redirect('document_pages:incoming_document_list')
    
    document = get_object_or_404(IncomingDocument, id=document_id)
    
    if request.method == 'POST':
        try:
            document.title = request.POST.get('title', '').strip()
            document.sender = request.POST.get('sender', '').strip()
            document.sender_contact = request.POST.get('sender_contact', '').strip()
            document.sender_phone = request.POST.get('sender_phone', '').strip()
            document.document_date = request.POST.get('document_date') or None
            document.receive_date = request.POST.get('receive_date') or None
            document.document_type = request.POST.get('document_type', '').strip()
            document.content = request.POST.get('content', '').strip()
            document.summary = request.POST.get('summary', '').strip()
            document.status = request.POST.get('status', 'draft')
            document.priority = request.POST.get('priority', 'normal')
            document.stage = request.POST.get('stage', '').strip() or None
            document.file_category_id = request.POST.get('file_category', '').strip() or None
            document.handler_id = request.POST.get('handler') or None
            document.handle_notes = request.POST.get('handle_notes', '').strip()
            document.notes = request.POST.get('notes', '').strip()
            
            # 处理附件
            if 'attachment' in request.FILES:
                document.attachment = request.FILES['attachment']
            
            # 如果状态变为已完成，记录完成时间
            if document.status == 'completed' and not document.completed_at:
                from django.utils import timezone
                document.completed_at = timezone.now()
            
            document.save()
            messages.success(request, f'收文"{document.title}"更新成功')
            return redirect('document_pages:incoming_document_detail', document_id=document.id)
        except Exception as e:
            logger.error(f"编辑收文失败: {str(e)}")
            messages.error(request, f'更新失败：{str(e)}')
    
    # 获取用户列表
    from django.contrib.auth import get_user_model
    User = get_user_model()
    users = User.objects.filter(is_active=True).order_by('username')
    
    context = _context(
        "收文编辑",
        "✏️",
        "编辑收文记录",
        request=request,
    )
    # 获取文件分类数据
    from backend.apps.document_management.models import FileCategory
    categories = FileCategory.objects.filter(is_active=True).order_by('stage', 'sort_order', 'name')
    categories_by_stage = {}
    for category in categories:
        if category.stage not in categories_by_stage:
            categories_by_stage[category.stage] = []
        categories_by_stage[category.stage].append(category)
    
    context["document_sidebar_nav"] = document_sidebar_nav
    context["sidebar_nav"] = document_sidebar_nav  # 兼容模板中的变量名
    context["module_sidebar_nav"] = document_sidebar_nav
    context["document"] = document
    context["status_choices"] = IncomingDocument.STATUS_CHOICES
    context["priority_choices"] = IncomingDocument.PRIORITY_CHOICES
    context["stage_choices"] = IncomingDocument.STAGE_CHOICES
    context["categories"] = categories
    context["categories_by_stage"] = categories_by_stage
    context["users"] = users
    return render(request, "document_management/incoming_document_edit.html", context)

# ========== outgoing_document_home ==========
@login_required
def outgoing_document_home(request):
    """发文管理首页 - 数据展示中心"""
    from django.db.models import Avg, Count
    from datetime import datetime
    from backend.apps.document_management.models import OutgoingDocument
    
    permission_set = get_user_permission_codes(request.user)
    if not _permission_granted('delivery_center.view', permission_set):
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("无权限访问发文管理")
    
    now = timezone.now()
    today = now.date()
    this_month_start = today.replace(day=1)
    seven_days_ago = today - timedelta(days=7)
    
    all_documents = OutgoingDocument.objects.all()
    
    context = {}
    
    try:
        # ========== 核心指标卡片 ==========
        core_cards = []
        
        # 发文统计
        total_documents = all_documents.count()
        draft_documents = all_documents.filter(status='draft').count()
        reviewing_documents = all_documents.filter(status='reviewing').count()
        approved_documents = all_documents.filter(status='approved').count()
        sent_documents = all_documents.filter(status='sent').count()
        completed_documents = all_documents.filter(status='completed').count()
        archived_documents = all_documents.filter(status='archived').count()
        this_month_documents = all_documents.filter(created_at__gte=this_month_start).count()
        this_month_completed_documents = all_documents.filter(
            status='completed',
            completed_at__gte=this_month_start
        ).count()
        
        # 卡片1：发文总数
        core_cards.append({
            'label': '发文总数',
            'icon': '📤',
            'value': str(total_documents),
            'subvalue': f'草稿 {draft_documents} | 审核中 {reviewing_documents} | 已发出 {sent_documents} | 已完成 {completed_documents}',
            'url': reverse('document_pages:outgoing_document_list'),
            'variant': 'secondary'
        })
        
        # 卡片2：审核中发文
        core_cards.append({
            'label': '审核中发文',
            'icon': '⚡',
            'value': str(reviewing_documents),
            'subvalue': f'等待审核 {reviewing_documents} 个',
            'url': reverse('document_pages:outgoing_document_list') + '?status=reviewing',
            'variant': 'dark'
        })
        
        # 卡片3：已完成发文
        core_cards.append({
            'label': '已完成发文',
            'icon': '✅',
            'value': str(completed_documents),
            'subvalue': f'本月完成 {this_month_completed_documents} 个',
            'url': reverse('document_pages:outgoing_document_list') + '?status=completed',
            'variant': 'secondary'
        })
        
        # 卡片4：待审核发文
        core_cards.append({
            'label': '待审核发文',
            'icon': '📋',
            'value': str(reviewing_documents),
            'subvalue': f'等待审核',
            'url': reverse('document_pages:outgoing_document_list') + '?status=reviewing',
            'variant': 'dark' if reviewing_documents > 0 else 'secondary'
        })
        
        # 卡片5：已批准发文
        core_cards.append({
            'label': '已批准发文',
            'icon': '📝',
            'value': str(approved_documents),
            'subvalue': f'等待发出',
            'url': reverse('document_pages:outgoing_document_list') + '?status=approved',
            'variant': 'dark' if approved_documents > 0 else 'secondary'
        })
        
        # 卡片6：本月新增
        core_cards.append({
            'label': '本月新增',
            'icon': '📈',
            'value': str(this_month_documents),
            'subvalue': f'新发文 {this_month_documents} 个',
            'url': reverse('document_pages:outgoing_document_list'),
            'variant': 'secondary'
        })
        
        context['core_cards'] = core_cards
        
        # ========== 风险预警 ==========
        risk_warnings = []
        
        # 7天未处理发文
        stale_documents = all_documents.filter(
            status__in=['reviewing', 'approved'],
            updated_at__lt=timezone.make_aware(datetime.combine(seven_days_ago, datetime.min.time()))
        ).select_related('reviewer', 'created_by')[:5]
        
        for doc in stale_documents:
            days_since_update = (today - doc.updated_at.date()).days
            reviewer_name = _format_user_display(doc.reviewer) if doc.reviewer else '未分配'
            risk_warnings.append({
                'type': 'stale',
                'title': doc.title,
                'responsible': reviewer_name,
                'days': days_since_update,
                'url': reverse('document_pages:outgoing_document_detail', args=[doc.id])
            })
        
        context['risk_warnings'] = risk_warnings[:5]
        context['stale_documents_count'] = all_documents.filter(
            status__in=['reviewing', 'approved'],
            updated_at__lt=timezone.make_aware(datetime.combine(seven_days_ago, datetime.min.time()))
        ).count()
        context['overdue_documents_count'] = 0
        
        # ========== 待办事项 ==========
        todo_items = []
        
        # 待审核发文
        reviewing_list = all_documents.filter(status='reviewing').select_related('reviewer')[:5]
        for doc in reviewing_list:
            reviewer_name = _format_user_display(doc.reviewer) if doc.reviewer else '未分配'
            todo_items.append({
                'type': 'review',
                'title': doc.title,
                'document_number': doc.document_number,
                'responsible': reviewer_name,
                'url': reverse('document_pages:outgoing_document_detail', args=[doc.id])
            })
        
        # 已批准待发出
        approved_list = all_documents.filter(status='approved').select_related('created_by')[:5]
        for doc in approved_list:
            creator_name = _format_user_display(doc.created_by) if doc.created_by else '系统'
            todo_items.append({
                'type': 'send',
                'title': doc.title,
                'document_number': doc.document_number,
                'responsible': creator_name,
                'url': reverse('document_pages:outgoing_document_detail', args=[doc.id])
            })
        
        context['todo_items'] = todo_items[:10]
        context['pending_approval_count'] = reviewing_documents + approved_documents
        context['todo_summary_url'] = reverse('document_pages:outgoing_document_list') + '?status=reviewing'
        
        # ========== 我的工作 ==========
        my_work = {}
        
        # 我创建的发文
        my_created_documents = all_documents.filter(created_by=request.user).order_by('-created_at')[:3]
        my_work['my_documents'] = [{
            'title': doc.title,
            'status': doc.get_status_display(),
            'url': reverse('document_pages:outgoing_document_detail', args=[doc.id])
        } for doc in my_created_documents]
        my_work['my_documents_count'] = all_documents.filter(created_by=request.user).count()
        
        # 我审核的发文
        my_reviewed_documents = all_documents.filter(reviewer=request.user).order_by('-updated_at')[:3]
        my_work['reviewed_documents'] = [{
            'title': doc.title,
            'status': doc.get_status_display(),
            'url': reverse('document_pages:outgoing_document_detail', args=[doc.id])
        } for doc in my_reviewed_documents]
        my_work['reviewed_documents_count'] = all_documents.filter(reviewer=request.user).count()
        
        my_work['summary_url'] = reverse('document_pages:outgoing_document_list') + f'?created_by={request.user.id}'
        
        context['my_work'] = my_work
        
        # ========== 最近活动 ==========
        recent_activities = {}
        
        # 最近创建的发文
        recent_documents = all_documents.select_related('created_by').order_by('-created_at')[:5]
        recent_activities['recent_documents'] = [{
            'title': doc.title,
            'creator': _format_user_display(doc.created_by),
            'time': doc.created_at,
            'url': reverse('document_pages:outgoing_document_detail', args=[doc.id])
        } for doc in recent_documents]
        
        # 最近更新的发文（排除创建）
        recent_updates = all_documents.exclude(
            created_at=F('updated_at')
        ).select_related('reviewer').order_by('-updated_at')[:5]
        recent_activities['recent_updates'] = [{
            'title': doc.title,
            'updater': _format_user_display(doc.reviewer) if doc.reviewer else '系统',
            'time': doc.updated_at,
            'url': reverse('document_pages:outgoing_document_detail', args=[doc.id])
        } for doc in recent_updates]
        
        context['recent_activities'] = recent_activities
        
    except Exception as e:
        logger.exception('获取发文管理统计数据失败: %s', str(e))
        context.setdefault('core_cards', [])
        context.setdefault('risk_warnings', [])
        context.setdefault('todo_items', [])
        context.setdefault('my_work', {})
        context.setdefault('recent_activities', {})
    
    # 顶部操作栏
    top_actions = []
    if _permission_granted('delivery_center.create', permission_set):
        try:
            top_actions.append({
                'label': '创建发文',
                'url': reverse('document_pages:outgoing_document_create'),
                'icon': '➕'
            })
        except Exception:
            pass
    
    context['top_actions'] = top_actions
    
    # 构建上下文
    page_context = _context(
        "发文管理",
        "📤",
        "数据展示中心 - 集中展示发文关键指标、状态与风险",
        request=request,
    )
    
    # 设置侧边栏导航（使用发文管理独立菜单）
    document_sidebar_nav = _build_outgoing_document_sidebar_nav(permission_set, request.path, active_id='outgoing_document_home')
    page_context['sidebar_nav'] = document_sidebar_nav
    page_context['module_sidebar_nav'] = document_sidebar_nav
    page_context['sidebar_title'] = '发文管理'
    page_context['sidebar_subtitle'] = 'Outgoing Document'
    
    # 合并所有数据
    page_context.update(context)
    
    return render(request, "document_management/outgoing_document_home.html", page_context)

# ========== outgoing_document_list ==========
@login_required
def outgoing_document_list(request):
    """发文列表"""
    from django.core.paginator import Paginator
    from django.db.models import Q
    from backend.apps.document_management.models import OutgoingDocument
    
    permission_set = get_user_permission_codes(request.user)
    document_sidebar_nav = _build_outgoing_document_sidebar_nav(permission_set, request.path, active_id='outgoing_document_list')
    
    # 获取查询参数
    search = request.GET.get('search', '').strip()
    status_filter = request.GET.get('status', '').strip()
    if not status_filter:
        status_filter = 'all'
    priority_filter = request.GET.get('priority', '').strip()
    if not priority_filter:
        priority_filter = 'all'
    stage_filter = request.GET.get('stage', '').strip()
    if not stage_filter:
        stage_filter = 'all'
    category_filter = request.GET.get('category', '').strip()
    if not category_filter:
        category_filter = 'all'
    
    # 统计数据（在过滤之前获取，显示全部数据统计）
    all_documents = OutgoingDocument.objects.all()
    total_count = all_documents.count()
    draft_count = all_documents.filter(status='draft').count()
    reviewing_count = all_documents.filter(status='reviewing').count()
    approved_count = all_documents.filter(status='approved').count()
    sent_count = all_documents.filter(status='sent').count()
    completed_count = all_documents.filter(status='completed').count()
    archived_count = all_documents.filter(status='archived').count()
    
    # 查询发文
    documents = OutgoingDocument.objects.all()
    
    # 搜索过滤
    if search:
        documents = documents.filter(
            Q(document_number__icontains=search) |
            Q(title__icontains=search) |
            Q(recipient__icontains=search) |
            Q(recipient_contact__icontains=search)
        )
    
    # 状态过滤
    if status_filter != 'all':
        documents = documents.filter(status=status_filter)
    
    # 优先级过滤
    if priority_filter != 'all':
        documents = documents.filter(priority=priority_filter)
    
    # 阶段过滤
    if stage_filter != 'all':
        documents = documents.filter(stage=stage_filter)
    
    # 文件分类过滤
    if category_filter != 'all':
        try:
            category_id = int(category_filter)
            documents = documents.filter(file_category_id=category_id)
        except (ValueError, TypeError):
            pass
    
    # 排序
    documents = documents.order_by('-created_at')
    
    # 分页（每页20条）
    paginator = Paginator(documents, 20)
    page_number = request.GET.get('page', 1)
    try:
        documents_page = paginator.page(page_number)
    except:
        documents_page = paginator.page(1)
    
    context = _context(
        "发文列表",
        "📤",
        "管理发出的文件记录",
        request=request,
    )
    # 获取文件分类数据（用于下拉选择）
    from backend.apps.document_management.models import FileCategory
    categories = FileCategory.objects.filter(is_active=True).order_by('stage', 'sort_order', 'name')
    categories_by_stage = {}
    for category in categories:
        if category.stage not in categories_by_stage:
            categories_by_stage[category.stage] = []
        categories_by_stage[category.stage].append(category)
    
    # 生成左侧菜单（类似计划管理的 plan_menu）
    context['sidebar_nav'] = document_sidebar_nav
    context['module_sidebar_nav'] = document_sidebar_nav  # 兼容模板中的变量名
    context['sidebar_title'] = '发文管理'  # 侧边栏标题
    context['sidebar_subtitle'] = 'Outgoing Document'  # 侧边栏副标题
    
    context.update({
        'documents': documents_page,
        'search': search,
        'search_query': search,  # 保持向后兼容
        'status_filter': status_filter,
        'priority_filter': priority_filter,
        'stage_filter': stage_filter,
        'category_filter': category_filter,
        'status_choices': OutgoingDocument.STATUS_CHOICES,
        'priority_choices': OutgoingDocument.PRIORITY_CHOICES,
        'stage_choices': OutgoingDocument.STAGE_CHOICES,
        'categories': categories,
        'categories_by_stage': categories_by_stage,
        'can_create': _permission_granted('delivery_center.create', permission_set),
        'total_count': total_count,
        'draft_count': draft_count,
        'reviewing_count': reviewing_count,
        'approved_count': approved_count,
        'sent_count': sent_count,
        'completed_count': completed_count,
        'archived_count': archived_count,
    })
    return render(request, "document_management/outgoing_document_list.html", context)

# ========== outgoing_document_create ==========
@login_required
def outgoing_document_create(request):
    """发文创建"""
    from django.shortcuts import redirect
    from django.contrib import messages
    from django.utils import timezone
    from backend.apps.document_management.models import OutgoingDocument
    
    permission_set = get_user_permission_codes(request.user)
    document_sidebar_nav = _build_outgoing_document_sidebar_nav(permission_set, request.path)
    
    if not _permission_granted('delivery_center.create', permission_set):
        messages.error(request, '您没有创建发文的权限')
        return redirect('document_pages:outgoing_document_list')
    
    if request.method == 'POST':
        try:
            # 生成发文编号
            today = timezone.now().date()
            year = today.strftime('%Y')
            count = OutgoingDocument.objects.filter(
                document_number__startswith=f'FW{year}'
            ).count() + 1
            document_number = f'FW{year}{count:04d}'
            
            # 确保编号唯一
            while OutgoingDocument.objects.filter(document_number=document_number).exists():
                count += 1
                document_number = f'FW{year}{count:04d}'
            
            # 处理阶段和文件分类
            stage = request.POST.get('stage', '').strip() or None
            file_category_id = request.POST.get('file_category', '').strip() or None
            
            # 处理客户和客户联系人
            client_id = request.POST.get('client', '').strip() or None
            client_contact_id = request.POST.get('client_contact', '').strip() or None
            
            document = OutgoingDocument(
                document_number=document_number,
                title=request.POST.get('title', '').strip(),
                recipient=request.POST.get('recipient', '').strip(),
                recipient_contact=request.POST.get('recipient_contact', '').strip(),
                recipient_phone=request.POST.get('recipient_phone', '').strip(),
                recipient_email=request.POST.get('recipient_email', '').strip(),
                recipient_address=request.POST.get('recipient_address', '').strip(),
                document_date=request.POST.get('document_date') or None,
                content=request.POST.get('content', '').strip(),
                summary=request.POST.get('summary', '').strip(),
                status=request.POST.get('status', 'draft'),
                priority=request.POST.get('priority', 'normal'),
                stage=stage,
                file_category_id=file_category_id,
                project_id=request.POST.get('project') or None,
                client_id=client_id,
                client_contact_id=client_contact_id,
                delivery_methods=','.join(request.POST.getlist('delivery_methods')),
                notes=request.POST.get('notes', '').strip(),
                created_by=request.user,
            )
            
            # 处理附件
            if 'attachment' in request.FILES:
                document.attachment = request.FILES['attachment']
            
            # save方法会自动填充字段
            document.save()
            messages.success(request, f'发文"{document.title}"创建成功')
            return redirect('document_pages:outgoing_document_detail', document_id=document.id)
        except Exception as e:
            logger.error(f"创建发文失败: {str(e)}")
            messages.error(request, f'创建失败：{str(e)}')
    
    # 获取用户列表
    from django.contrib.auth import get_user_model
    User = get_user_model()
    users = User.objects.filter(is_active=True).order_by('username')
    
    # 获取文件分类数据
    from backend.apps.document_management.models import FileCategory
    categories = FileCategory.objects.filter(is_active=True).order_by('stage', 'sort_order', 'name')
    categories_by_stage = {}
    for category in categories:
        if category.stage not in categories_by_stage:
            categories_by_stage[category.stage] = []
        categories_by_stage[category.stage].append(category)
    
    # 获取项目列表（只显示有项目编号的项目，项目编号来源于业务委托书或合同）
    from backend.apps.contract_management.models import BusinessContract
    from backend.apps.customer_management.models import AuthorizationLetter
    from django.db.models import Q
    # Project 已在文件顶部导入
    
    # 从业务委托书中获取有项目编号的记录
    auth_project_numbers = set()
    try:
        auth_project_numbers = set(AuthorizationLetter.objects.filter(
            project_number__isnull=False
        ).exclude(project_number='').values_list('project_number', flat=True).distinct())
    except Exception:
        pass
    
    # 从业务委托书和合同中获取关联的项目ID
    project_ids_from_auth = set()
    project_ids_from_contract = set()
    
    try:
        # 从业务委托书中获取关联的项目ID
        project_ids_from_auth = set(AuthorizationLetter.objects.filter(
            project_id__isnull=False
        ).values_list('project_id', flat=True).distinct())
    except Exception:
        pass
    
    try:
        # 从合同中获取关联的项目ID
        project_ids_from_contract = set(BusinessContract.objects.filter(
            project_id__isnull=False
        ).values_list('project_id', flat=True).distinct())
    except Exception:
        pass
    
    # 合并所有项目ID
    all_project_ids = project_ids_from_auth | project_ids_from_contract
    
    # 查找对应的项目：优先通过项目编号匹配，如果没有则通过项目ID匹配，但只显示有项目编号的项目
    if auth_project_numbers:
        # 如果有项目编号，优先使用项目编号匹配
        projects = Project.objects.filter(
            Q(project_number__in=auth_project_numbers) | Q(id__in=all_project_ids)
        ).filter(
            project_number__isnull=False
        ).exclude(project_number='').order_by('-created_time')[:100]
    elif all_project_ids:
        # 如果没有项目编号，使用项目ID匹配，但只显示有项目编号的项目
        projects = Project.objects.filter(
            id__in=all_project_ids
        ).filter(
            project_number__isnull=False
        ).exclude(project_number='').order_by('-created_time')[:100]
    else:
        # 如果都没有，显示所有有项目编号的项目（项目编号来源于业务委托书或合同创建时生成）
        projects = Project.objects.filter(
            project_number__isnull=False
        ).exclude(project_number='').order_by('-created_time')[:100]
    
    context = _context(
        "发文创建",
        "➕",
        "创建新的发文记录",
        request=request,
    )
    context["document_sidebar_nav"] = document_sidebar_nav
    context["sidebar_nav"] = document_sidebar_nav  # 兼容模板中的变量名
    context["module_sidebar_nav"] = document_sidebar_nav
    context["status_choices"] = OutgoingDocument.STATUS_CHOICES
    context["priority_choices"] = OutgoingDocument.PRIORITY_CHOICES
    context["stage_choices"] = OutgoingDocument.STAGE_CHOICES
    context["categories"] = categories
    context["categories_by_stage"] = categories_by_stage
    context["users"] = users
    context["projects"] = projects
    return render(request, "document_management/outgoing_document_create.html", context)

# ========== outgoing_document_detail ==========
@login_required
def outgoing_document_detail(request, document_id):
    """发文详情"""
    from django.shortcuts import get_object_or_404
    from backend.apps.document_management.models import OutgoingDocument
    
    permission_set = get_user_permission_codes(request.user)
    document_sidebar_nav = _build_outgoing_document_sidebar_nav(permission_set, request.path)
    
    document = get_object_or_404(OutgoingDocument, id=document_id)
    
    context = _context(
        "发文详情",
        "📤",
        "查看发文详细信息",
        request=request,
    )
    context["document_sidebar_nav"] = document_sidebar_nav
    context["sidebar_nav"] = document_sidebar_nav  # 兼容模板中的变量名
    context["module_sidebar_nav"] = document_sidebar_nav
    context["document"] = document
    context["can_edit"] = _permission_granted('delivery_center.create', permission_set)
    return render(request, "document_management/outgoing_document_detail.html", context)

# ========== outgoing_document_edit ==========
@login_required
def outgoing_document_edit(request, document_id):
    """发文编辑"""
    from django.shortcuts import redirect, get_object_or_404
    from django.contrib import messages
    from backend.apps.document_management.models import OutgoingDocument
    
    permission_set = get_user_permission_codes(request.user)
    document_sidebar_nav = _build_outgoing_document_sidebar_nav(permission_set, request.path)
    
    if not _permission_granted('delivery_center.create', permission_set):
        messages.error(request, '您没有编辑发文的权限')
        return redirect('document_pages:outgoing_document_list')
    
    document = get_object_or_404(OutgoingDocument, id=document_id)
    
    if request.method == 'POST':
        try:
            document.title = request.POST.get('title', '').strip()
            document.recipient = request.POST.get('recipient', '').strip()
            document.recipient_contact = request.POST.get('recipient_contact', '').strip()
            document.recipient_phone = request.POST.get('recipient_phone', '').strip()
            document.recipient_email = request.POST.get('recipient_email', '').strip()
            document.recipient_address = request.POST.get('recipient_address', '').strip()
            document.document_date = request.POST.get('document_date') or None
            document.content = request.POST.get('content', '').strip()
            document.summary = request.POST.get('summary', '').strip()
            document.status = request.POST.get('status', 'draft')
            document.priority = request.POST.get('priority', 'normal')
            document.stage = request.POST.get('stage', '').strip() or None
            document.file_category_id = request.POST.get('file_category', '').strip() or None
            document.project_id = request.POST.get('project') or None
            
            # 处理客户和客户联系人
            client_id = request.POST.get('client', '').strip() or None
            client_contact_id = request.POST.get('client_contact', '').strip() or None
            document.client_id = client_id
            document.client_contact_id = client_contact_id
            
            document.delivery_methods = ','.join(request.POST.getlist('delivery_methods'))
            document.notes = request.POST.get('notes', '').strip()
            
            # 处理附件
            if 'attachment' in request.FILES:
                document.attachment = request.FILES['attachment']
            
            # 如果状态变为已审核，记录审核时间
            if document.status == 'approved' and not document.reviewed_at:
                from django.utils import timezone
                document.reviewed_at = timezone.now()
            
            # 如果状态变为已发出，记录发送时间
            if document.status == 'sent' and not document.sent_at:
                from django.utils import timezone
                document.sent_at = timezone.now()
            
            document.save()
            messages.success(request, f'发文"{document.title}"更新成功')
            return redirect('document_pages:outgoing_document_detail', document_id=document.id)
        except Exception as e:
            logger.error(f"编辑发文失败: {str(e)}")
            messages.error(request, f'更新失败：{str(e)}')
    
    # 获取用户列表
    from django.contrib.auth import get_user_model
    User = get_user_model()
    users = User.objects.filter(is_active=True).order_by('username')
    
    context = _context(
        "发文编辑",
        "✏️",
        "编辑发文记录",
        request=request,
    )
    # 获取文件分类数据
    from backend.apps.document_management.models import FileCategory
    categories = FileCategory.objects.filter(is_active=True).order_by('stage', 'sort_order', 'name')
    categories_by_stage = {}
    for category in categories:
        if category.stage not in categories_by_stage:
            categories_by_stage[category.stage] = []
        categories_by_stage[category.stage].append(category)
    
    # 获取项目列表（只显示有项目编号的项目，项目编号来源于业务委托书或合同）
    from backend.apps.contract_management.models import BusinessContract
    from backend.apps.customer_management.models import AuthorizationLetter
    from django.db.models import Q
    # Project 已在文件顶部导入
    
    # 从业务委托书中获取有项目编号的记录
    auth_project_numbers = set()
    try:
        auth_project_numbers = set(AuthorizationLetter.objects.filter(
            project_number__isnull=False
        ).exclude(project_number='').values_list('project_number', flat=True).distinct())
    except Exception:
        pass
    
    # 从业务委托书和合同中获取关联的项目ID
    project_ids_from_auth = set()
    project_ids_from_contract = set()
    
    try:
        # 从业务委托书中获取关联的项目ID
        project_ids_from_auth = set(AuthorizationLetter.objects.filter(
            project_id__isnull=False
        ).values_list('project_id', flat=True).distinct())
    except Exception:
        pass
    
    try:
        # 从合同中获取关联的项目ID
        project_ids_from_contract = set(BusinessContract.objects.filter(
            project_id__isnull=False
        ).values_list('project_id', flat=True).distinct())
    except Exception:
        pass
    
    # 合并所有项目ID
    all_project_ids = project_ids_from_auth | project_ids_from_contract
    
    # 查找对应的项目：优先通过项目编号匹配，如果没有则通过项目ID匹配，但只显示有项目编号的项目
    if auth_project_numbers:
        # 如果有项目编号，优先使用项目编号匹配
        projects = Project.objects.filter(
            Q(project_number__in=auth_project_numbers) | Q(id__in=all_project_ids)
        ).filter(
            project_number__isnull=False
        ).exclude(project_number='').order_by('-created_time')[:100]
    elif all_project_ids:
        # 如果没有项目编号，使用项目ID匹配，但只显示有项目编号的项目
        projects = Project.objects.filter(
            id__in=all_project_ids
        ).filter(
            project_number__isnull=False
        ).exclude(project_number='').order_by('-created_time')[:100]
    else:
        # 如果都没有，显示所有有项目编号的项目（项目编号来源于业务委托书或合同创建时生成）
        projects = Project.objects.filter(
            project_number__isnull=False
        ).exclude(project_number='').order_by('-created_time')[:100]
    
    # 处理报送方式列表（用于模板显示）
    delivery_methods_list = []
    if document.delivery_methods:
        delivery_methods_list = [m.strip() for m in document.delivery_methods.split(',') if m.strip()]
    
    context["document_sidebar_nav"] = document_sidebar_nav
    context["sidebar_nav"] = document_sidebar_nav  # 兼容模板中的变量名
    context["module_sidebar_nav"] = document_sidebar_nav
    context["document"] = document
    context["document"].delivery_methods_list = delivery_methods_list  # 添加属性到document对象
    context["status_choices"] = OutgoingDocument.STATUS_CHOICES
    context["priority_choices"] = OutgoingDocument.PRIORITY_CHOICES
    context["stage_choices"] = OutgoingDocument.STAGE_CHOICES
    context["categories"] = categories
    context["categories_by_stage"] = categories_by_stage
    context["users"] = users
    context["projects"] = projects
    return render(request, "document_management/outgoing_document_edit.html", context)

# ========== FILE_CATEGORY_STAGES ==========
FILE_CATEGORY_STAGES = {
    'conversion': '转化阶段',
    'contract': '合同阶段',
    'production': '生产阶段',
    'settlement': '结算阶段',
    'payment': '回款阶段',
    'after_sales': '售后阶段',
    'litigation': '诉讼阶段',
}

# ========== file_category_manage ==========
@login_required
def file_category_manage(request):
    """文件分类维护 - 统一管理页面（包含阶段选择、列表和新增功能）"""
    from django.shortcuts import redirect
    from django.core.paginator import Paginator
    from django.db.models import Q
    from django.contrib import messages
    from backend.apps.document_management.models import FileCategory
    
    permission_set = get_user_permission_codes(request.user)
    document_sidebar_nav = _build_outgoing_document_sidebar_nav(permission_set, request.path)
    
    if not _permission_granted('delivery_center.view', permission_set):
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("无权限访问文件分类维护")
    
    # 获取选中的阶段（支持"全部"选项，默认为"全部"）
    selected_stage = request.GET.get('stage', 'all')
    show_all = False
    
    if selected_stage == 'all' or selected_stage == '':
        show_all = True
        selected_stage = 'all'
        stage_name = '全部阶段'
    elif selected_stage not in FILE_CATEGORY_STAGES:
        selected_stage = 'all'
        show_all = True
        stage_name = '全部阶段'
    else:
        stage_name = FILE_CATEGORY_STAGES[selected_stage]
    
    # 处理新增分类（POST请求）
    if request.method == 'POST' and _permission_granted('delivery_center.create', permission_set):
        try:
            # 分类名称从下拉选择获取（实际上是阶段代码）
            stage_code = request.POST.get('name', '').strip()
            category_name = request.POST.get('category_name', '').strip()
            
            if not stage_code or stage_code not in FILE_CATEGORY_STAGES:
                messages.error(request, '请选择阶段')
            elif not category_name:
                messages.error(request, '请输入分类名称')
            else:
                # 检查同一阶段内是否已存在同名分类
                if FileCategory.objects.filter(stage=stage_code, name=category_name).exists():
                    messages.error(request, f'该阶段已存在名为"{category_name}"的分类')
                else:
                    # 自动生成分类代码：阶段代码_序号（如：conversion_001）
                    stage_prefix = stage_code.upper()
                    # 获取该阶段已有的分类数量
                    existing_count = FileCategory.objects.filter(stage=stage_code).count()
                    # 生成代码：阶段代码_3位序号
                    category_code = f"{stage_prefix}_{existing_count + 1:03d}"
                    
                    # 确保代码唯一
                    while FileCategory.objects.filter(code=category_code).exists():
                        existing_count += 1
                        category_code = f"{stage_prefix}_{existing_count + 1:03d}"
                    
                    category = FileCategory(
                        name=category_name,
                        code=category_code,
                        stage=stage_code,
                        description=request.POST.get('description', '').strip(),
                        sort_order=int(request.POST.get('sort_order', 0) or 0),
                        is_active=request.POST.get('is_active') == 'on',
                        created_by=request.user,
                    )
                    category.save()
                    messages.success(request, f'文件分类"{category_name}"创建成功，代码：{category_code}')
                    # 刷新页面，显示新创建的分类
                    from django.urls import reverse
                    return redirect(f'{reverse("document_pages:file_category_manage")}?stage={stage_code}')
        except Exception as e:
            logger.error(f"创建文件分类失败: {str(e)}")
            messages.error(request, f'创建失败：{str(e)}')
    
    # 获取文件分类（如果选择"全部"则显示所有阶段）
    if show_all:
        queryset = FileCategory.objects.all().order_by('stage', 'sort_order', 'name')
    else:
        queryset = FileCategory.objects.filter(stage=selected_stage).order_by('sort_order', 'name')
    
    # 搜索功能
    search_keyword = request.GET.get('search', '').strip()
    if search_keyword:
        queryset = queryset.filter(
            Q(name__icontains=search_keyword) |
            Q(code__icontains=search_keyword) |
            Q(description__icontains=search_keyword)
        )
    
    # 状态筛选
    status_filter = request.GET.get('status', '')
    if status_filter == 'active':
        queryset = queryset.filter(is_active=True)
    elif status_filter == 'inactive':
        queryset = queryset.filter(is_active=False)
    
    # 分页
    paginator = Paginator(queryset, 20)
    page_num = request.GET.get('page', 1)
    try:
        page = paginator.get_page(page_num)
    except:
        page = paginator.get_page(1)
    
    context = _context(
        "创建文件分类",
        "➕",
        "管理各阶段的文件分类",
        request=request,
    )
    context["document_sidebar_nav"] = document_sidebar_nav
    context["sidebar_nav"] = document_sidebar_nav  # 兼容模板中的变量名
    context["module_sidebar_nav"] = document_sidebar_nav
    context["stage_code"] = selected_stage if not show_all else 'all'
    context["stage_name"] = stage_name
    context["show_all"] = show_all
    context["stages"] = FILE_CATEGORY_STAGES
    context["categories"] = page
    context["search_keyword"] = search_keyword
    context["status_filter"] = status_filter
    context["can_create"] = _permission_granted('delivery_center.create', permission_set)
    
    return render(request, "document_management/file_category_manage.html", context)

# ========== file_category_list ==========
@login_required
def file_category_list(request, stage_code):
    """文件分类维护 - 列表页（统一视图，通过stage_code参数区分阶段）"""
    from django.core.paginator import Paginator
    from django.db.models import Q
    from django.http import Http404
    from backend.apps.document_management.models import FileCategory
    
    if stage_code not in FILE_CATEGORY_STAGES:
        raise Http404("阶段不存在")
    
    stage_name = FILE_CATEGORY_STAGES[stage_code]
    
    permission_set = get_user_permission_codes(request.user)
    document_sidebar_nav = _build_outgoing_document_sidebar_nav(permission_set, request.path)
    
    if not _permission_granted('delivery_center.view', permission_set):
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("无权限访问文件分类维护")
    
    # 获取该阶段的所有文件分类
    queryset = FileCategory.objects.filter(stage=stage_code).order_by('sort_order', 'name')
    
    # 搜索功能
    search_keyword = request.GET.get('search', '').strip()
    if search_keyword:
        queryset = queryset.filter(
            Q(name__icontains=search_keyword) |
            Q(code__icontains=search_keyword) |
            Q(description__icontains=search_keyword)
        )
    
    # 状态筛选
    status_filter = request.GET.get('status', '')
    if status_filter == 'active':
        queryset = queryset.filter(is_active=True)
    elif status_filter == 'inactive':
        queryset = queryset.filter(is_active=False)
    
    # 分页
    paginator = Paginator(queryset, 20)
    page_num = request.GET.get('page', 1)
    try:
        page = paginator.get_page(page_num)
    except:
        page = paginator.get_page(1)
    
    context = _context(
        f"文件分类维护 - {stage_name}",
        "📂",
        f"管理{stage_name}的文件分类",
        request=request,
    )
    context["document_sidebar_nav"] = document_sidebar_nav
    context["sidebar_nav"] = document_sidebar_nav  # 兼容模板中的变量名
    context["module_sidebar_nav"] = document_sidebar_nav
    context["stage_code"] = stage_code
    context["stage_name"] = stage_name
    context["categories"] = page
    context["search_keyword"] = search_keyword
    context["status_filter"] = status_filter
    context["can_create"] = _permission_granted('delivery_center.create', permission_set)
    
    return render(request, "document_management/file_category_list.html", context)

# ========== file_category_create ==========
@login_required
def file_category_create(request, stage_code):
    """文件分类维护 - 新增（统一视图，通过stage_code参数区分阶段）"""
    from django.shortcuts import redirect
    from django.contrib import messages
    from django.http import Http404
    from backend.apps.document_management.models import FileCategory
    
    if stage_code not in FILE_CATEGORY_STAGES:
        raise Http404("阶段不存在")
    
    stage_name = FILE_CATEGORY_STAGES[stage_code]
    
    permission_set = get_user_permission_codes(request.user)
    document_sidebar_nav = _build_outgoing_document_sidebar_nav(permission_set, request.path)
    
    if not _permission_granted('delivery_center.create', permission_set):
        messages.error(request, '您没有创建文件分类的权限')
        return redirect('document_pages:file_category_list', stage_code=stage_code)
    
    if request.method == 'POST':
        try:
            name = request.POST.get('name', '').strip()
            if not name:
                messages.error(request, '分类名称不能为空')
            else:
                # 检查同一阶段内是否已存在同名分类
                if FileCategory.objects.filter(stage=stage_code, name=name).exists():
                    messages.error(request, f'该阶段已存在名为"{name}"的分类')
                else:
                    category = FileCategory(
                        name=name,
                        code=request.POST.get('code', '').strip(),
                        stage=stage_code,
                        description=request.POST.get('description', '').strip(),
                        sort_order=int(request.POST.get('sort_order', 0) or 0),
                        is_active=request.POST.get('is_active') == 'on',
                        created_by=request.user,
                    )
                    category.save()
                    messages.success(request, f'文件分类"{name}"创建成功')
                    return redirect('document_pages:file_category_list', stage_code=stage_code)
        except Exception as e:
            logger.error(f"创建文件分类失败: {str(e)}")
            messages.error(request, f'创建失败：{str(e)}')
    
    context = _context(
        f"新增文件分类 - {stage_name}",
        "➕",
        f"为{stage_name}新增文件分类",
        request=request,
    )
    context["document_sidebar_nav"] = document_sidebar_nav
    context["sidebar_nav"] = document_sidebar_nav  # 兼容模板中的变量名
    context["module_sidebar_nav"] = document_sidebar_nav
    context["stage_code"] = stage_code
    context["stage_name"] = stage_name
    
    return render(request, "document_management/file_category_create.html", context)

# ========== file_template_manage ==========
@login_required
def file_template_manage(request):
    """文件模板维护 - 统一管理页面（包含阶段选择、列表和新增功能）"""
    from django.shortcuts import redirect
    from django.core.paginator import Paginator
    from django.db.models import Q
    from django.contrib import messages
    from backend.apps.document_management.models import FileTemplate, FileCategory
    
    permission_set = get_user_permission_codes(request.user)
    document_sidebar_nav = _build_outgoing_document_sidebar_nav(permission_set, request.path)
    
    if not _permission_granted('delivery_center.view', permission_set):
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("无权限访问文件模板维护")
    
    # 获取选中的阶段（支持"全部"选项，默认为"全部"）
    selected_stage = request.GET.get('stage', 'all')
    show_all = False
    
    if selected_stage == 'all' or selected_stage == '':
        show_all = True
        selected_stage = 'all'
        stage_name = '全部阶段'
    elif selected_stage not in FILE_CATEGORY_STAGES:
        selected_stage = 'all'
        show_all = True
        stage_name = '全部阶段'
    else:
        stage_name = FILE_CATEGORY_STAGES[selected_stage]
    
    # 处理新增模板（POST请求）
    if request.method == 'POST' and _permission_granted('delivery_center.create', permission_set):
        try:
            stage_code = request.POST.get('stage', '').strip()
            template_name = request.POST.get('template_name', '').strip()
            
            if not stage_code or stage_code not in FILE_CATEGORY_STAGES:
                messages.error(request, '请选择阶段')
            elif not template_name:
                messages.error(request, '请输入模板名称')
            else:
                # 检查同一阶段内是否已存在同名模板
                if FileTemplate.objects.filter(stage=stage_code, name=template_name).exists():
                    messages.error(request, f'该阶段已存在名为"{template_name}"的模板')
                else:
                    # 自动生成模板代码：阶段代码_序号（如：conversion_001）
                    stage_prefix = stage_code.upper()
                    # 获取该阶段已有的模板数量
                    existing_count = FileTemplate.objects.filter(stage=stage_code).count()
                    # 生成代码：阶段代码_3位序号
                    template_code = f"{stage_prefix}_TEMPLATE_{existing_count + 1:03d}"
                    
                    # 确保代码唯一
                    while FileTemplate.objects.filter(code=template_code).exists():
                        existing_count += 1
                        template_code = f"{stage_prefix}_TEMPLATE_{existing_count + 1:03d}"
                    
                    # 获取关联的分类（如果提供）
                    category_id = request.POST.get('category', '').strip()
                    category = None
                    if category_id:
                        try:
                            category = FileCategory.objects.get(id=category_id, stage=stage_code)
                        except FileCategory.DoesNotExist:
                            pass
                    
                    template = FileTemplate(
                        name=template_name,
                        code=template_code,
                        stage=stage_code,
                        category=category,
                        description=request.POST.get('description', '').strip(),
                        sort_order=int(request.POST.get('sort_order', 0) or 0),
                        is_active=request.POST.get('is_active') == 'on',
                        created_by=request.user,
                    )
                    
                    # 处理文件上传
                    if 'template_file' in request.FILES:
                        template.template_file = request.FILES['template_file']
                    
                    template.save()
                    messages.success(request, f'文件模板"{template_name}"创建成功，代码：{template_code}')
                    # 刷新页面，显示新创建的模板
                    from django.urls import reverse
                    return redirect(f'{reverse("document_pages:file_template_manage")}?stage={stage_code}')
        except Exception as e:
            logger.error(f"创建文件模板失败: {str(e)}")
            messages.error(request, f'创建失败：{str(e)}')
    
    # 获取文件模板（如果选择"全部"则显示所有阶段）
    if show_all:
        queryset = FileTemplate.objects.all().order_by('stage', 'sort_order', 'name')
    else:
        queryset = FileTemplate.objects.filter(stage=selected_stage).order_by('sort_order', 'name')
    
    # 搜索功能
    search_keyword = request.GET.get('search', '').strip()
    if search_keyword:
        queryset = queryset.filter(
            Q(name__icontains=search_keyword) |
            Q(code__icontains=search_keyword) |
            Q(description__icontains=search_keyword)
        )
    
    # 状态筛选
    status_filter = request.GET.get('status', '')
    if status_filter == 'active':
        queryset = queryset.filter(is_active=True)
    elif status_filter == 'inactive':
        queryset = queryset.filter(is_active=False)
    
    # 分页
    paginator = Paginator(queryset, 20)
    page_number = request.GET.get('page', 1)
    try:
        page = paginator.get_page(page_number)
    except:
        page = paginator.get_page(1)
    
    # 获取各阶段的文件分类（用于下拉选择）
    categories_by_stage = {}
    for stage_code in FILE_CATEGORY_STAGES.keys():
        categories_by_stage[stage_code] = FileCategory.objects.filter(
            stage=stage_code, 
            is_active=True
        ).order_by('sort_order', 'name')
    
    context = _context(
        "文件模板维护",
        "📄",
        "管理各阶段的文件模板",
        request=request,
    )
    context["document_sidebar_nav"] = document_sidebar_nav
    context["sidebar_nav"] = document_sidebar_nav  # 兼容模板中的变量名
    context["module_sidebar_nav"] = document_sidebar_nav
    context["stage_code"] = selected_stage if not show_all else 'all'
    context["stage_name"] = stage_name
    context["show_all"] = show_all
    context["stages"] = FILE_CATEGORY_STAGES
    context["templates"] = page
    context["search_keyword"] = search_keyword
    context["status_filter"] = status_filter
    context["can_create"] = _permission_granted('delivery_center.create', permission_set)
    context["categories_by_stage"] = categories_by_stage
    
    return render(request, "document_management/file_template_manage.html", context)
