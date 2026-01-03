from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.urls import reverse, NoReverseMatch
from django.views.decorators.csrf import csrf_exempt
import logging

from backend.apps.system_management.services import get_user_permission_codes
from backend.core.views import HOME_NAV_STRUCTURE, _permission_granted, _build_full_top_nav, _build_unified_sidebar_nav

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


@login_required
def delivery_customer_home(request):
    """交付客户首页"""
    permission_codes = get_user_permission_codes(request.user)
    today = timezone.now().date()
    this_month_start = today.replace(day=1)
    
    # 权限检查
    if not _permission_granted('delivery_center.view', permission_codes):
        from django.contrib import messages
        messages.error(request, '您没有权限访问交付客户')
        return redirect('admin:index')
    
    # 收集统计数据
    summary_cards = []
    
    try:
        # 收文统计
        if _permission_granted('delivery_center.incoming.view', permission_codes):
            try:
                from backend.apps.delivery_customer.models import IncomingDocument
                total_incoming = IncomingDocument.objects.count()
                pending_incoming = IncomingDocument.objects.filter(
                    status__in=['draft', 'registered', 'processing']
                ).count()
                this_month_incoming = IncomingDocument.objects.filter(
                    created_at__gte=this_month_start
                ).count()
                
                summary_cards.append({
                    'label': '收文管理',
                    'icon': '📥',
                    'value': str(total_incoming),
                    'subvalue': f'待处理 {pending_incoming} 件 · 本月 {this_month_incoming} 件',
                    'url': reverse('delivery_pages:incoming_document_list'),
                    'variant': 'warning' if pending_incoming > 0 else 'success'
                })
            except Exception:
                pass
        
        # 发文统计
        if _permission_granted('delivery_center.outgoing.view', permission_codes):
            try:
                from backend.apps.delivery_customer.models import OutgoingDocument
                total_outgoing = OutgoingDocument.objects.count()
                pending_outgoing = OutgoingDocument.objects.filter(
                    status__in=['draft', 'reviewing']
                ).count()
                this_month_outgoing = OutgoingDocument.objects.filter(
                    created_at__gte=this_month_start
                ).count()
                
                summary_cards.append({
                    'label': '发文管理',
                    'icon': '📤',
                    'value': str(total_outgoing),
                    'subvalue': f'待处理 {pending_outgoing} 件 · 本月 {this_month_outgoing} 件',
                    'url': reverse('delivery_pages:outgoing_document_list'),
                    'variant': 'warning' if pending_outgoing > 0 else 'success'
                })
            except Exception:
                pass
        
        # 交付记录统计
        if _permission_granted('delivery_center.view', permission_codes):
            try:
                from backend.apps.delivery_customer.models import DeliveryRecord
                total_deliveries = DeliveryRecord.objects.count()
                pending_deliveries = DeliveryRecord.objects.filter(
                    status__in=['pending', 'in_transit']
                ).count()
                
                summary_cards.append({
                    'label': '交付记录',
                    'icon': '📦',
                    'value': str(total_deliveries),
                    'subvalue': f'待处理 {pending_deliveries} 件',
                    'url': reverse('delivery_pages:delivery_list'),
                    'variant': 'warning' if pending_deliveries > 0 else 'info'
                })
            except Exception:
                pass
    except Exception as e:
        logger.exception('获取统计数据失败: %s', str(e))
    
    # 功能模块入口
    module_entries = []
    
    if _permission_granted('delivery_center.incoming.view', permission_codes):
        try:
            module_entries.append({
                'label': '收文管理',
                'icon': '📥',
                'description': '管理收到的文件',
                'url': reverse('delivery_pages:incoming_document_list'),
                'link_label': '进入模块 →'
            })
        except Exception:
            pass
    
    if _permission_granted('delivery_center.outgoing.view', permission_codes):
        try:
            module_entries.append({
                'label': '发文管理',
                'icon': '📤',
                'description': '管理发出的文件',
                'url': reverse('delivery_pages:outgoing_document_list'),
                'link_label': '进入模块 →'
            })
        except Exception:
            pass
    
    if _permission_granted('delivery_center.view', permission_codes):
        try:
            module_entries.append({
                'label': '交付记录',
                'icon': '📦',
                'description': '管理交付记录',
                'url': reverse('delivery_pages:delivery_list'),
                'link_label': '进入模块 →'
            })
        except Exception:
            pass
    
    # 构建区域
    sections = []
    
    if module_entries:
        sections.append({
            'title': '功能模块',
            'description': '交付客户的各个功能模块入口',
            'items': module_entries,
            'layout': 'grid'
        })
    
    # 构建上下文
    context = _context(
        page_title="交付客户",
        page_icon="📦",
        description="管理收文、发文和交付业务",
        summary_cards=summary_cards,
        sections=sections,
        request=request,
    )
    
    return render(request, "delivery_customer/home.html", context)


@login_required
def report_delivery(request):
    """收发管理首页 - 新版本：直接跳转到交付记录列表页（保留用于向后兼容）"""
    from django.shortcuts import redirect
    
    permission_set = get_user_permission_codes(request.user)
    
    # 权限检查
    if not _permission_granted('delivery_center.view', permission_set):
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("无权限访问收发管理")
    
    # 新版本：直接跳转到交付记录列表页（首页=交付记录列表）
    return redirect('delivery_pages:delivery_list')
    
    # ==================== 老版本代码（已注释）====================
    # 老版本使用卡片式布局的首页，已改为使用左侧菜单布局
    # from backend.apps.delivery_customer.models import DeliveryRecord
    # from django.db.models import Q
    # 
    # # 构建基础查询
    # queryset = DeliveryRecord.objects.all()
    # if not _permission_granted('delivery_center.view_all', permission_set):
    #     queryset = queryset.filter(
    #         Q(created_by=request.user) | 
    #         Q(project__team_members__user=request.user)
    #     ).distinct()
    # 
    # # 从数据库获取统计数据
    # try:
    #     total_count = queryset.count()
    #     pending_count = queryset.filter(status__in=['draft', 'submitted']).count()
    #     confirmed_count = queryset.filter(status='confirmed').count()
    #     overdue_count = queryset.filter(is_overdue=True).count()
    # except Exception:
    #     # 如果表不存在，使用默认值
    #     total_count = 0
    #     pending_count = 0
    #     confirmed_count = 0
    #     overdue_count = 0
    # 
    # context = _context(
    #     "收发管理",
    #     "📦",
    #     "管理成果交付、上传确认材料，并追踪客户下载与回执情况。支持邮件、快递、送达三种交付方式。",
    #     request=request,
    #     summary_cards=[
    #         {"label": "待交付成果", "value": str(pending_count), "hint": "等待上传或发送的成果文件"},
    #         {"label": "客户回执", "value": str(confirmed_count), "hint": "客户已确认的交付项目"},
    #         {"label": "逾期待发", "value": str(overdue_count), "hint": "超过交付期限仍未完成的任务"},
    #         {"label": "交付总数", "value": str(total_count), "hint": "所有交付记录总数"},
    #     ],
    #     sections=[
    #         {
    #             "title": "交付操作",
    #             "description": "对交付成果进行上传、推送与确认。",
    #             "items": [
    #                 {"label": "创建交付单", "description": "发起新的交付任务。", "url": "/delivery/create/", "icon": "🧾"},
    #                 {"label": "交付记录", "description": "查看历次交付与客户回执。", "url": "/delivery/list/", "icon": "📚"},
    #                 {"label": "交付统计", "description": "交付效率与及时率分析。", "url": "/delivery/statistics/", "icon": "📈"},
    #                 {"label": "风险预警", "description": "查看逾期交付预警。", "url": "/delivery/warnings/", "icon": "⚠️"},
    #             ],
    #         }
    #     ],
    # )
    # return render(request, "shared/center_dashboard.html", context)
    # ==================== 老版本代码结束 ====================


@login_required
def delivery_list(request):
    """交付记录列表页"""
    from backend.apps.delivery_customer.models import DeliveryRecord
    from django.core.paginator import Paginator
    from django.db.models import Q
    
    permission_set = get_user_permission_codes(request.user)
    
    # 权限检查
    if not _permission_granted('delivery_center.view', permission_set):
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("无权限访问收发管理")
    
    # 获取查询参数
    tab = request.GET.get('tab', 'all')
    status = request.GET.get('status', '')
    delivery_method = request.GET.get('delivery_method', '')
    priority = request.GET.get('priority', '')
    project_id = request.GET.get('project_id', '')
    client_id = request.GET.get('client_id', '')
    created_date_from = request.GET.get('created_date_from', '')
    created_date_to = request.GET.get('created_date_to', '')
    scheduled_date_from = request.GET.get('scheduled_date_from', '')
    scheduled_date_to = request.GET.get('scheduled_date_to', '')
    search = request.GET.get('search', '')
    page_num = request.GET.get('page', 1)
    
    # 构建查询
    queryset = DeliveryRecord.objects.all()
    
    # 根据标签页过滤
    if tab == 'my_created':
        # 我创建的
        queryset = queryset.filter(created_by=request.user)
    elif tab == 'my_responsible':
        # 我负责的（我创建或我负责的项目）
        queryset = queryset.filter(
            Q(created_by=request.user) | 
            Q(project__team_members__user=request.user)
        ).distinct()
    elif tab == 'pending':
        # 待处理（草稿、已报送、待审核、审核中）
        queryset = queryset.filter(status__in=['draft', 'submitted', 'pending_approval', 'approving'])
    elif tab == 'overdue':
        # 已逾期
        queryset = queryset.filter(is_overdue=True)
    # else: tab == 'all' 或未指定，显示全部
    
    # 权限过滤：如果没有查看全部权限，只能查看自己创建的或负责项目的
    if not _permission_granted('delivery_center.view_all', permission_set):
        queryset = queryset.filter(
            Q(created_by=request.user) | 
            Q(project__team_members__user=request.user)
        ).distinct()
    
    # 状态筛选
    if status:
        queryset = queryset.filter(status=status)
    
    # 交付方式筛选
    if delivery_method:
        queryset = queryset.filter(delivery_method=delivery_method)
    
    # 优先级筛选
    if priority:
        queryset = queryset.filter(priority=priority)
    
    # 项目筛选
    if project_id:
        try:
            queryset = queryset.filter(project_id=int(project_id))
        except (ValueError, TypeError):
            pass
    
    # 客户筛选
    if client_id:
        try:
            queryset = queryset.filter(client_id=int(client_id))
        except (ValueError, TypeError):
            pass
    
    # 创建时间筛选
    if created_date_from:
        try:
            from datetime import datetime
            queryset = queryset.filter(created_at__gte=datetime.fromisoformat(created_date_from))
        except (ValueError, TypeError):
            pass
    if created_date_to:
        try:
            from datetime import datetime
            queryset = queryset.filter(created_at__lte=datetime.fromisoformat(created_date_to))
        except (ValueError, TypeError):
            pass
    
    # 计划交付时间筛选
    if scheduled_date_from:
        try:
            from datetime import datetime
            queryset = queryset.filter(scheduled_delivery_time__gte=datetime.fromisoformat(scheduled_date_from))
        except (ValueError, TypeError):
            pass
    if scheduled_date_to:
        try:
            from datetime import datetime
            queryset = queryset.filter(scheduled_delivery_time__lte=datetime.fromisoformat(scheduled_date_to))
        except (ValueError, TypeError):
            pass
    
    # 搜索（交付单号、标题、收件人信息）
    if search:
        queryset = queryset.filter(
            Q(delivery_number__icontains=search) |
            Q(title__icontains=search) |
            Q(recipient_name__icontains=search) |
            Q(recipient_email__icontains=search)
        )
    
    # 排序和分页
    # 使用 defer 排除不存在的 total_execution_amount 字段
    queryset = queryset.select_related('project', 'client', 'created_by').defer('client__total_execution_amount').order_by('-created_at')
    paginator = Paginator(queryset, 20)
    page = paginator.get_page(page_num)
    
    # 统计数据
    base_queryset = DeliveryRecord.objects.all()
    if not _permission_granted('delivery_center.view_all', permission_set):
        base_queryset = base_queryset.filter(
            Q(created_by=request.user) | 
            Q(project__team_members__user=request.user)
        ).distinct()
    
    pending_count = base_queryset.filter(status__in=['draft', 'submitted']).count()
    sent_count = base_queryset.filter(status__in=['sent', 'in_transit']).count()
    confirmed_count = base_queryset.filter(status='confirmed').count()
    overdue_count = base_queryset.filter(is_overdue=True).count()
    
    # 获取项目和客户列表（用于筛选下拉框）
    from backend.apps.production_management.models import Project
    from backend.apps.customer_management.models import Client
    
    # 根据权限过滤项目列表
    projects_queryset = Project.objects.all()
    if not _permission_granted('production_management.view_all', permission_set):
        projects_queryset = projects_queryset.filter(
            Q(project_manager=request.user) |
            Q(team_members__user=request.user)
        ).distinct()
    projects = projects_queryset.order_by('-created_time')[:100]  # 限制数量
    
    # 根据权限过滤客户列表
    clients_queryset = Client.objects.all()
    if not _permission_granted('customer_management.client.view', permission_set):
        # 只显示有权限查看的客户
        clients_queryset = clients_queryset.filter(
            Q(created_by=request.user) |
            Q(projects__team_members__user=request.user)
        ).distinct()
    # 只选择需要的字段，避免查询不存在的 total_execution_amount 字段
    clients = clients_queryset.only('id', 'name', 'created_time').order_by('-created_time')[:100]  # 限制数量
    
    # 添加左侧菜单（统一使用module_sidebar_nav变量名）
    module_sidebar_nav = _build_delivery_sidebar_nav(permission_set, request.path)
    
    return render(request, "delivery_customer/delivery_list.html", {
        "page_title": "交付记录",
        "page_icon": "📚",
        "tab": tab,
        "deliveries": page,
        "status_filter": status,
        "method_filter": delivery_method,
        "priority_filter": priority,
        "project_filter": project_id,
        "client_filter": client_id,
        "created_date_from": created_date_from,
        "created_date_to": created_date_to,
        "scheduled_date_from": scheduled_date_from,
        "scheduled_date_to": scheduled_date_to,
        "search_query": search,
        "status_choices": DeliveryRecord.STATUS_CHOICES,
        "priority_choices": DeliveryRecord.PRIORITY_CHOICES,
        "projects": projects,
        "clients": clients,
        "pending_count": pending_count,
        "sent_count": sent_count,
        "confirmed_count": confirmed_count,
        "overdue_count": overdue_count,
        "full_top_nav": _build_full_top_nav(permission_set, request.user),
        "module_sidebar_nav": module_sidebar_nav,
        "delivery_sidebar_nav": module_sidebar_nav,  # 兼容旧模板
    })


@login_required
def delivery_create(request):
    """创建交付记录页"""
    from backend.apps.production_management.models import Project
    from backend.apps.customer_management.models import Client
    from backend.apps.delivery_customer.models import DeliveryRecord, DeliveryFile
    from django.utils import timezone
    from django.contrib import messages
    from django.shortcuts import redirect
    
    permission_set = get_user_permission_codes(request.user)
    
    # 权限检查
    if not _permission_granted('delivery_center.create', permission_set):
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("无权限创建交付记录")
    
    # 处理POST请求
    if request.method == 'POST':
        try:
            # 获取表单数据
            title = request.POST.get('title', '').strip()
            description = request.POST.get('description', '').strip()
            delivery_method = request.POST.get('delivery_method', 'email')
            priority = request.POST.get('priority', 'normal')
            
            # 验证必填字段
            if not title:
                messages.error(request, '交付标题不能为空')
                return redirect('delivery_pages:delivery_create')
            
            # 创建交付记录
            delivery = DeliveryRecord.objects.create(
                title=title,
                description=description,
                delivery_method=delivery_method,
                priority=priority,
                created_by=request.user,
                status='draft'
            )
            
            # 处理项目文件类型
            file_type = request.POST.get('file_type', 'project')
            if file_type == 'project':
                project_id = request.POST.get('project_id')
                if project_id:
                    try:
                        project = Project.objects.get(id=project_id)
                        delivery.project = project
                        # 优先使用项目的客户（权威来源）
                        if project.client:
                            delivery.client = project.client
                        else:
                            # 如果项目没有客户，尝试使用前端提交的客户ID
                            client_id = request.POST.get('client_id')
                            if client_id:
                                try:
                                    client = Client.objects.get(id=client_id)
                                    delivery.client = client
                                except Client.DoesNotExist:
                                    pass
                    except Project.DoesNotExist:
                        pass
            else:
                # 非项目文件
                client_id = request.POST.get('client_id')
                if client_id:
                    try:
                        client = Client.objects.get(id=client_id)
                        delivery.client = client
                    except Client.DoesNotExist:
                        pass
            
            # 收件人信息
            delivery.recipient_name = request.POST.get('recipient_name', '').strip()
            delivery.recipient_phone = request.POST.get('recipient_phone', '').strip()
            delivery.recipient_email = request.POST.get('recipient_email', '').strip()
            delivery.recipient_address = request.POST.get('recipient_address', '').strip()
            
            # 时间设置
            scheduled_delivery_time = request.POST.get('scheduled_delivery_time')
            deadline = request.POST.get('deadline')
            if scheduled_delivery_time:
                try:
                    from datetime import datetime
                    # 处理datetime-local格式的输入
                    delivery.scheduled_delivery_time = datetime.fromisoformat(scheduled_delivery_time)
                    if timezone.is_naive(delivery.scheduled_delivery_time):
                        delivery.scheduled_delivery_time = timezone.make_aware(delivery.scheduled_delivery_time)
                except Exception as e:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(f'解析计划交付时间失败: {e}')
            if deadline:
                try:
                    from datetime import datetime
                    # 处理datetime-local格式的输入
                    delivery.deadline = datetime.fromisoformat(deadline)
                    if timezone.is_naive(delivery.deadline):
                        delivery.deadline = timezone.make_aware(delivery.deadline)
                except Exception as e:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(f'解析交付期限失败: {e}')
            
            # 邮件相关信息
            if delivery_method == 'email':
                delivery.email_subject = request.POST.get('email_subject', '').strip()
                delivery.email_message = request.POST.get('email_message', '').strip()
                delivery.cc_emails = request.POST.get('cc_emails', '').strip()
                delivery.bcc_emails = request.POST.get('bcc_emails', '').strip()
            
            # 快递相关信息
            elif delivery_method == 'express':
                delivery.express_company = request.POST.get('express_company', '').strip()
                delivery.express_number = request.POST.get('express_number', '').strip()
                express_fee = request.POST.get('express_fee')
                if express_fee:
                    try:
                        delivery.express_fee = float(express_fee)
                    except:
                        pass
            
            # 送达相关信息
            elif delivery_method == 'hand_delivery':
                delivery.delivery_notes = request.POST.get('delivery_notes', '').strip()
                delivery_person_id = request.POST.get('delivery_person_id')
                if delivery_person_id:
                    try:
                        from django.contrib.auth import get_user_model
                        User = get_user_model()
                        delivery.delivery_person = User.objects.get(id=delivery_person_id)
                    except:
                        pass
            
            delivery.save()
            
            # 处理文件上传
            files = request.FILES.getlist('files')
            for file in files:
                DeliveryFile.objects.create(
                    delivery_record=delivery,
                    file=file,
                    file_name=file.name,
                    file_size=file.size,
                    uploaded_by=request.user
                )
            
            # 更新文件统计
            delivery.file_count = delivery.files.filter(is_deleted=False).count()
            delivery.total_file_size = sum(f.file_size for f in delivery.files.filter(is_deleted=False))
            delivery.save()
            
            messages.success(request, f'交付单创建成功！交付单号：{delivery.delivery_number}')
            return redirect('delivery_pages:delivery_detail', delivery_id=delivery.id)
            
        except Exception as e:
            messages.error(request, f'创建交付单失败：{str(e)}')
            import traceback
            traceback.print_exc()
    
    # GET请求：获取项目和客户列表（用于下拉选择）
    projects = Project.objects.all().order_by('-created_time')[:100]  # 限制数量
    clients = Client.objects.all().order_by('-created_time')[:100]
    
    # 添加左侧菜单
    module_sidebar_nav = _build_delivery_sidebar_nav(permission_set, request.path)
    delivery_sidebar_nav = module_sidebar_nav  # 兼容旧模板
    
    return render(request, "delivery_customer/delivery_create.html", {
        "page_title": "创建交付单",
        "page_icon": "🧾",
        "projects": projects,
        "clients": clients,
        "full_top_nav": _build_full_top_nav(permission_set, request.user),
        "module_sidebar_nav": module_sidebar_nav,
        "delivery_sidebar_nav": delivery_sidebar_nav,  # 兼容旧模板
    })


@login_required
def delivery_detail(request, delivery_id):
    """交付记录详情页"""
    from backend.apps.delivery_customer.models import DeliveryRecord
    from django.db.models import Q
    
    permission_set = get_user_permission_codes(request.user)
    
    # 权限检查
    if not _permission_granted('delivery_center.view', permission_set):
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("无权限查看交付记录")
    
    try:
        delivery = DeliveryRecord.objects.select_related(
            'project', 'client', 'created_by', 'sent_by', 'delivery_person'
        ).prefetch_related('files', 'tracking_records', 'feedbacks').get(id=delivery_id)
    except DeliveryRecord.DoesNotExist:
        from django.http import Http404
        raise Http404("交付记录不存在")
    
    # 对象级权限检查
    if not _permission_granted('delivery_center.view_all', permission_set):
        if delivery.created_by != request.user and not delivery.project.team_members.filter(user=request.user).exists():
            from django.http import HttpResponseForbidden
            return HttpResponseForbidden("无权限查看此交付记录")
    
    # 检查编辑权限
    can_edit = _permission_granted('delivery_center.edit', permission_set) or \
               (delivery.created_by == request.user and _permission_granted('delivery_center.edit_assigned', permission_set))
    
    # 检查是否可以提交（草稿状态且是创建人）
    can_submit = delivery.status == 'draft' and delivery.created_by == request.user
    
    # 添加左侧菜单
    module_sidebar_nav = _build_delivery_sidebar_nav(permission_set, request.path)
    delivery_sidebar_nav = module_sidebar_nav  # 兼容旧模板
    
    return render(request, "delivery_customer/delivery_detail.html", {
        "page_title": "交付详情",
        "page_icon": "📋",
        "delivery": delivery,
        "can_edit": can_edit,
        "can_submit": can_submit,
        "full_top_nav": _build_full_top_nav(permission_set, request.user),
        "module_sidebar_nav": module_sidebar_nav,
        "delivery_sidebar_nav": delivery_sidebar_nav,  # 兼容旧模板
    })


@login_required
def delivery_edit(request, delivery_id):
    """交付记录编辑页"""
    from backend.apps.delivery_customer.models import DeliveryRecord, DeliveryFile
    from backend.apps.production_management.models import Project
    from backend.apps.customer_management.models import Client
    from django.contrib import messages
    from django.utils import timezone
    from django.shortcuts import redirect
    
    permission_set = get_user_permission_codes(request.user)
    
    # 权限检查
    if not _permission_granted('delivery_center.edit', permission_set):
        # 检查是否有编辑自己创建的权限
        if not _permission_granted('delivery_center.edit_assigned', permission_set):
            from django.http import HttpResponseForbidden
            return HttpResponseForbidden("无权限编辑交付记录")
    
    try:
        delivery = DeliveryRecord.objects.get(id=delivery_id)
    except DeliveryRecord.DoesNotExist:
        from django.http import Http404
        raise Http404("交付记录不存在")
    
    # 检查是否可编辑（仅草稿状态可编辑）
    if delivery.status != 'draft':
        messages.error(request, '只能编辑草稿状态的交付记录')
        return redirect('delivery_pages:delivery_detail', delivery_id=delivery.id)
    
    # 检查编辑权限
    can_edit = _permission_granted('delivery_center.edit', permission_set) or \
               (delivery.created_by == request.user and _permission_granted('delivery_center.edit_assigned', permission_set))
    
    if not can_edit:
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("无权限编辑此交付记录")
    
    # POST请求：保存编辑
    if request.method == 'POST':
        # 更新基本信息
        delivery.title = request.POST.get('title', '').strip()
        delivery.description = request.POST.get('description', '').strip()
        delivery.delivery_method = request.POST.get('delivery_method', 'email')
        delivery.priority = request.POST.get('priority', 'normal')
        
        # 处理项目和客户关联
        # 优先处理项目（如果选择了项目）
        project_id = request.POST.get('project_id')
        if project_id:
            try:
                project = Project.objects.get(id=project_id)
                delivery.project = project
                # 优先使用项目的客户（权威来源）
                if project.client:
                    delivery.client = project.client
                else:
                    # 如果项目没有客户，尝试使用前端提交的客户ID
                    client_id = request.POST.get('client_id')
                    if client_id:
                        try:
                            client = Client.objects.get(id=client_id)
                            delivery.client = client
                        except Client.DoesNotExist:
                            pass
            except Project.DoesNotExist:
                pass
        else:
            # 如果没有选择项目，处理客户ID（非项目文件）
            client_id = request.POST.get('client_id')
            if client_id:
                try:
                    client = Client.objects.get(id=client_id)
                    delivery.client = client
                except Client.DoesNotExist:
                    pass
            # 如果没有项目也没有客户，清空项目关联
            delivery.project = None
        
        # 收件人信息
        delivery.recipient_name = request.POST.get('recipient_name', '').strip()
        delivery.recipient_phone = request.POST.get('recipient_phone', '').strip()
        delivery.recipient_email = request.POST.get('recipient_email', '').strip()
        delivery.recipient_address = request.POST.get('recipient_address', '').strip()
        
        # 时间设置
        scheduled_delivery_time = request.POST.get('scheduled_delivery_time')
        deadline = request.POST.get('deadline')
        if scheduled_delivery_time:
            try:
                from datetime import datetime
                delivery.scheduled_delivery_time = datetime.fromisoformat(scheduled_delivery_time)
                if timezone.is_naive(delivery.scheduled_delivery_time):
                    delivery.scheduled_delivery_time = timezone.make_aware(delivery.scheduled_delivery_time)
            except Exception:
                pass
        if deadline:
            try:
                from datetime import datetime
                delivery.deadline = datetime.fromisoformat(deadline)
                if timezone.is_naive(delivery.deadline):
                    delivery.deadline = timezone.make_aware(delivery.deadline)
            except Exception:
                pass
        
        # 邮件相关信息
        if delivery.delivery_method == 'email':
            delivery.email_subject = request.POST.get('email_subject', '').strip()
            delivery.email_message = request.POST.get('email_message', '').strip()
            delivery.cc_emails = request.POST.get('cc_emails', '').strip()
            delivery.bcc_emails = request.POST.get('bcc_emails', '').strip()
        
        # 快递相关信息
        elif delivery.delivery_method == 'express':
            delivery.express_company = request.POST.get('express_company', '').strip()
            delivery.express_number = request.POST.get('express_number', '').strip()
            express_fee = request.POST.get('express_fee')
            if express_fee:
                try:
                    delivery.express_fee = float(express_fee)
                except:
                    pass
        
        # 送达相关信息
        elif delivery.delivery_method == 'hand_delivery':
            delivery.delivery_notes = request.POST.get('delivery_notes', '').strip()
            delivery_person_id = request.POST.get('delivery_person_id')
            if delivery_person_id:
                try:
                    from django.contrib.auth import get_user_model
                    User = get_user_model()
                    delivery.delivery_person = User.objects.get(id=delivery_person_id)
                except:
                    pass
        
        delivery.save()
        
        # 处理文件上传
        uploaded_files = request.FILES.getlist('files')
        for uploaded_file in uploaded_files:
            DeliveryFile.objects.create(
                delivery_record=delivery,
                file=uploaded_file,
                file_name=uploaded_file.name,
                file_size=uploaded_file.size,
                uploaded_by=request.user
            )
        
        # 更新文件统计
        delivery.file_count = delivery.files.filter(is_deleted=False).count()
        delivery.total_file_size = sum(f.file_size for f in delivery.files.filter(is_deleted=False))
        delivery.save()
        
        messages.success(request, '交付记录已更新')
        return redirect('delivery_pages:delivery_detail', delivery_id=delivery.id)
    
    # GET请求：显示编辑表单
    # 获取项目和客户列表
    projects_queryset = Project.objects.all()
    if not _permission_granted('production_management.view_all', permission_set):
        from django.db.models import Q
        projects_queryset = projects_queryset.filter(
            Q(project_manager=request.user) |
            Q(team_members__user=request.user)
        ).distinct()
    projects = projects_queryset.order_by('-created_time')[:100]
    
    clients_queryset = Client.objects.all()
    if not _permission_granted('customer_management.client.view', permission_set):
        from django.db.models import Q
        clients_queryset = clients_queryset.filter(
            Q(created_by=request.user) |
            Q(projects__team_members__user=request.user)
        ).distinct()
    clients = clients_queryset.order_by('-created_time')[:100]
    
    # 添加左侧菜单
    module_sidebar_nav = _build_delivery_sidebar_nav(permission_set, request.path)
    delivery_sidebar_nav = module_sidebar_nav  # 兼容旧模板
    
    return render(request, "delivery_customer/delivery_edit.html", {
        "page_title": "编辑交付记录",
        "page_icon": "✏️",
        "delivery": delivery,
        "projects": projects,
        "clients": clients,
        "full_top_nav": _build_full_top_nav(permission_set, request.user),
        "module_sidebar_nav": module_sidebar_nav,
        "delivery_sidebar_nav": delivery_sidebar_nav,  # 兼容旧模板
    })


@login_required
def delivery_delete(request, delivery_id):
    """交付记录删除"""
    from backend.apps.delivery_customer.models import DeliveryRecord
    from django.contrib import messages
    from django.shortcuts import redirect
    
    permission_set = get_user_permission_codes(request.user)
    
    # 权限检查（删除权限或编辑权限都可以删除草稿）
    if not _permission_granted('delivery_center.delete', permission_set):
        # 如果没有删除权限，检查是否有编辑权限（可以删除自己创建的草稿）
        can_edit = _permission_granted('delivery_center.edit', permission_set) or \
                   _permission_granted('delivery_center.edit_assigned', permission_set)
        if not can_edit:
            from django.http import HttpResponseForbidden
            return HttpResponseForbidden("无权限删除交付记录")
    
    try:
        delivery = DeliveryRecord.objects.get(id=delivery_id)
    except DeliveryRecord.DoesNotExist:
        from django.http import Http404
        raise Http404("交付记录不存在")
    
    # 检查是否可删除（仅草稿状态可删除）
    if delivery.status != 'draft':
        messages.error(request, '只能删除草稿状态的交付记录')
        return redirect('delivery_pages:delivery_detail', delivery_id=delivery.id)
    
    # POST请求：执行删除
    if request.method == 'POST':
        delete_reason = request.POST.get('delete_reason', '').strip()
        delivery_number = delivery.delivery_number
        
        # 删除交付记录（级联删除相关文件、跟踪记录、反馈）
        delivery.delete()
        
        messages.success(request, f'交付记录 {delivery_number} 已删除')
        return redirect('delivery_pages:delivery_list')
    
    # GET请求：显示删除确认页面
    # 添加左侧菜单
    module_sidebar_nav = _build_delivery_sidebar_nav(permission_set, request.path)
    delivery_sidebar_nav = module_sidebar_nav  # 兼容旧模板
    
    return render(request, "delivery_customer/delivery_delete_confirm.html", {
        "page_title": "删除交付记录",
        "page_icon": "🗑️",
        "delivery": delivery,
        "full_top_nav": _build_full_top_nav(permission_set, request.user),
        "module_sidebar_nav": module_sidebar_nav,
        "delivery_sidebar_nav": delivery_sidebar_nav,  # 兼容旧模板
    })


@login_required
def delivery_submit(request, delivery_id):
    """提交交付记录进行审核"""
    from backend.apps.delivery_customer.models import DeliveryRecord, DeliveryTracking
    from django.contrib import messages
    from django.shortcuts import redirect
    from django.utils import timezone
    
    permission_set = get_user_permission_codes(request.user)
    
    # 权限检查
    if not _permission_granted('delivery_center.create', permission_set):
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("无权限提交交付记录")
    
    try:
        delivery = DeliveryRecord.objects.get(id=delivery_id)
    except DeliveryRecord.DoesNotExist:
        from django.http import Http404
        raise Http404("交付记录不存在")
    
    # 检查是否可以提交（只有创建人可以提交，且必须是草稿状态）
    if delivery.created_by != request.user:
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("只有创建人可以提交交付记录")
    
    if delivery.status != 'draft':
        messages.error(request, '只能提交草稿状态的交付记录')
        return redirect('delivery_pages:delivery_detail', delivery_id=delivery.id)
    
    # POST请求：执行提交
    if request.method == 'POST':
        # 更新状态
        delivery.status = 'submitted'
        delivery.submitted_at = timezone.now()
        delivery.save()
        
        # 创建跟踪记录
        DeliveryTracking.objects.create(
            delivery_record=delivery,
            event_type='submitted',
            event_description='交付记录已报送，等待审核',
            operator=request.user
        )
        
        messages.success(request, f'交付记录 {delivery.delivery_number} 已提交，等待审核')
        return redirect('delivery_pages:delivery_detail', delivery_id=delivery.id)
    
    # GET请求：显示提交确认页面（可选，也可以直接POST提交）
    # 添加左侧菜单
    module_sidebar_nav = _build_delivery_sidebar_nav(permission_set, request.path)
    delivery_sidebar_nav = module_sidebar_nav  # 兼容旧模板
    
    return render(request, "delivery_customer/delivery_submit_confirm.html", {
        "page_title": "提交交付记录",
        "page_icon": "📤",
        "delivery": delivery,
        "full_top_nav": _build_full_top_nav(permission_set, request.user),
        "module_sidebar_nav": module_sidebar_nav,
        "delivery_sidebar_nav": delivery_sidebar_nav,  # 兼容旧模板
    })


@login_required
def delivery_statistics(request):
    """交付统计页"""
    from backend.apps.delivery_customer.models import DeliveryRecord, DeliveryFile
    from django.db.models import Count, Q, Sum
    from django.utils import timezone
    from datetime import timedelta
    
    permission_set = get_user_permission_codes(request.user)
    
    # 权限检查
    if not _permission_granted('delivery_center.view_statistics', permission_set):
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("无权限查看交付统计")
    
    # 构建基础查询
    queryset = DeliveryRecord.objects.all()
    if not _permission_granted('delivery_center.view_all', permission_set):
        queryset = queryset.filter(
            Q(created_by=request.user) | 
            Q(project__team_members__user=request.user)
        ).distinct()
    
    # 基本统计
    total_count = queryset.count()
    status_distribution = {}
    for status_code, status_label in DeliveryRecord.STATUS_CHOICES:
        status_distribution[status_code] = {
            'label': status_label,
            'count': queryset.filter(status=status_code).count()
        }
    
    # 交付方式统计
    method_distribution = {}
    for method_code, method_label in DeliveryRecord.DELIVERY_METHOD_CHOICES:
        method_distribution[method_code] = {
            'label': method_label,
            'count': queryset.filter(delivery_method=method_code).count()
        }
    
    # 文件统计
    file_queryset = DeliveryFile.objects.filter(delivery_record__in=queryset, is_deleted=False)
    total_files = file_queryset.count()
    total_size = queryset.aggregate(total=Sum('total_file_size'))['total'] or 0
    
    # 时间统计
    today = timezone.now().date()
    today_count = queryset.filter(created_at__date=today).count()
    week_ago = today - timedelta(days=7)
    week_count = queryset.filter(created_at__date__gte=week_ago).count()
    month_ago = today - timedelta(days=30)
    month_count = queryset.filter(created_at__date__gte=month_ago).count()
    
    # 逾期统计
    overdue_count = queryset.filter(is_overdue=True).count()
    risk_distribution = {}
    for risk_code, risk_label in [('low', '低风险'), ('medium', '中风险'), ('high', '高风险'), ('critical', '严重风险')]:
        risk_distribution[risk_code] = {
            'label': risk_label,
            'count': queryset.filter(risk_level=risk_code).count()
        }
    
    # 添加左侧菜单
    module_sidebar_nav = _build_delivery_sidebar_nav(permission_set, request.path)
    delivery_sidebar_nav = module_sidebar_nav  # 兼容旧模板
    
    return render(request, "delivery_customer/delivery_statistics.html", {
        "page_title": "交付统计",
        "page_icon": "📈",
        "total_count": total_count,
        "status_distribution": status_distribution,
        "method_distribution": method_distribution,
        "file_statistics": {
            "total_files": total_files,
            "total_size": total_size,
        },
        "time_statistics": {
            "today_count": today_count,
            "week_count": week_count,
            "month_count": month_count,
        },
        "overdue_count": overdue_count,
        "risk_distribution": risk_distribution,
        "full_top_nav": _build_full_top_nav(permission_set, request.user),
        "module_sidebar_nav": module_sidebar_nav,
        "delivery_sidebar_nav": delivery_sidebar_nav,  # 兼容旧模板
    })


@login_required
def delivery_warnings(request):
    """风险预警页"""
    from backend.apps.delivery_customer.models import DeliveryRecord
    from django.core.paginator import Paginator
    from django.db.models import Q
    
    permission_set = get_user_permission_codes(request.user)
    
    # 权限检查
    if not _permission_granted('delivery_center.view', permission_set):
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("无权限查看风险预警")
    
    # 获取查询参数
    risk_level = request.GET.get('risk_level', '')
    page_num = request.GET.get('page', 1)
    
    # 构建查询：只查询逾期的记录
    queryset = DeliveryRecord.objects.filter(is_overdue=True)
    
    # 权限过滤
    if not _permission_granted('delivery_center.view_all', permission_set):
        queryset = queryset.filter(
            Q(created_by=request.user) | 
            Q(project__team_members__user=request.user)
        ).distinct()
    
    # 风险等级筛选
    if risk_level:
        queryset = queryset.filter(risk_level=risk_level)
    
    # 排序和分页
    queryset = queryset.select_related('project', 'client', 'created_by').defer('client__total_execution_amount').order_by('-overdue_days', '-created_at')
    paginator = Paginator(queryset, 20)
    page = paginator.get_page(page_num)
    
    # 风险统计
    risk_stats = {}
    for risk_code, risk_label in [('low', '低风险'), ('medium', '中风险'), ('high', '高风险'), ('critical', '严重风险')]:
        risk_stats[risk_code] = {
            'label': risk_label,
            'count': DeliveryRecord.objects.filter(is_overdue=True, risk_level=risk_code).count()
        }
    
    # 添加左侧菜单
    module_sidebar_nav = _build_delivery_sidebar_nav(permission_set, request.path)
    delivery_sidebar_nav = module_sidebar_nav  # 兼容旧模板
    
    return render(request, "delivery_customer/delivery_warnings.html", {
        "page_title": "风险预警",
        "page_icon": "⚠️",
        "overdue_deliveries": page,
        "risk_level_filter": risk_level,
        "risk_stats": risk_stats,
        "total_overdue": DeliveryRecord.objects.filter(is_overdue=True).count(),
        "full_top_nav": _build_full_top_nav(permission_set, request.user),
        "module_sidebar_nav": module_sidebar_nav,
        "delivery_sidebar_nav": delivery_sidebar_nav,  # 兼容旧模板
    })


@login_required
def delivery_approval_list(request):
    """交付审核列表页"""
    from backend.apps.delivery_customer.models import DeliveryRecord, DeliveryApproval
    from django.core.paginator import Paginator
    from django.db.models import Q, Exists, OuterRef
    
    permission_set = get_user_permission_codes(request.user)
    
    # 权限检查
    if not _permission_granted('delivery_center.view', permission_set):
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("无权限访问交付审核")
    
    # 获取查询参数
    approval_status = request.GET.get('approval_status', 'pending')  # pending, approving, approved, rejected
    page_num = request.GET.get('page', 1)
    
    # 构建查询
    queryset = DeliveryRecord.objects.filter(status__in=['submitted', 'pending_approval', 'approving', 'approved', 'rejected'])
    
    # 权限过滤
    if not _permission_granted('delivery_center.view_all', permission_set):
        queryset = queryset.filter(
            Q(created_by=request.user) | 
            Q(project__team_members__user=request.user) |
            Q(approvals__approver=request.user)
        ).distinct()
    
    # 根据审核状态筛选
    if approval_status == 'pending':
        # 待审核：已报送但还没有审核记录，或者状态为待审核
        queryset = queryset.filter(
            status__in=['submitted', 'pending_approval']
        ).exclude(
            Exists(DeliveryApproval.objects.filter(delivery_record=OuterRef('pk')))
        )
    elif approval_status == 'approving':
        # 审核中：有待审核的审核记录，且当前用户是审核人
        queryset = queryset.filter(
            status__in=['pending_approval', 'approving'],
            approvals__result='pending',
            approvals__approver=request.user
        ).distinct()
    elif approval_status == 'approved':
        # 已审核通过
        queryset = queryset.filter(status='approved')
    elif approval_status == 'rejected':
        # 已审核驳回
        queryset = queryset.filter(status='rejected')
    
    # 排序和分页
    queryset = queryset.select_related('project', 'client', 'created_by').defer('client__total_execution_amount').prefetch_related('approvals').order_by('-created_at')
    paginator = Paginator(queryset, 20)
    page = paginator.get_page(page_num)
    
    # 统计信息
    pending_count = DeliveryRecord.objects.filter(status='submitted').exclude(
        Exists(DeliveryApproval.objects.filter(delivery_record=OuterRef('pk')))
    ).count()
    approving_count = DeliveryRecord.objects.filter(
        status__in=['pending_approval', 'approving'],
        approvals__result='pending',
        approvals__approver=request.user
    ).distinct().count()
    approved_count = DeliveryRecord.objects.filter(status='approved').count()
    rejected_count = DeliveryRecord.objects.filter(status='rejected').count()
    
    # 添加左侧菜单
    module_sidebar_nav = _build_delivery_sidebar_nav(permission_set, request.path)
    delivery_sidebar_nav = module_sidebar_nav  # 兼容旧模板
    
    return render(request, "delivery_customer/delivery_approval_list.html", {
        "page_title": "交付审核",
        "page_icon": "✅",
        "approval_deliveries": page,
        "approval_status": approval_status,
        "pending_count": pending_count,
        "approving_count": approving_count,
        "approved_count": approved_count,
        "rejected_count": rejected_count,
        "full_top_nav": _build_full_top_nav(permission_set, request.user),
        "module_sidebar_nav": module_sidebar_nav,
        "delivery_sidebar_nav": delivery_sidebar_nav,  # 兼容旧模板
    })


@login_required
def delivery_approval_detail(request, delivery_id):
    """交付审核详情页"""
    from backend.apps.delivery_customer.models import DeliveryRecord, DeliveryApproval
    from django.db.models import Q
    
    permission_set = get_user_permission_codes(request.user)
    
    # 权限检查
    if not _permission_granted('delivery_center.view', permission_set):
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("无权限查看交付审核")
    
    try:
        delivery = DeliveryRecord.objects.select_related(
            'project', 'client', 'created_by'
        ).prefetch_related('approvals', 'files').get(id=delivery_id)
    except DeliveryRecord.DoesNotExist:
        from django.http import Http404
        raise Http404("交付记录不存在")
    
    # 检查是否有审核权限
    can_approve = _permission_granted('delivery_center.approve', permission_set)
    
    # 获取审核历史
    approval_history = delivery.approvals.all().order_by('-created_at')
    
    # 检查是否可以审核（状态为待审核或审核中，且用户有审核权限）
    can_perform_approval = False
    if can_approve and delivery.status in ['submitted', 'pending_approval', 'approving']:
        # 检查是否已经有待审核的记录
        pending_approval = delivery.approvals.filter(
            approver=request.user,
            result='pending'
        ).first()
        
        # 如果没有待审核记录，但状态是待审核，也可以审核
        if not pending_approval:
            # 检查是否已经有审核记录
            if not delivery.approvals.exists():
                can_perform_approval = True
            else:
                # 如果已经有审核记录，检查是否都是已完成的
                if not delivery.approvals.filter(result='pending').exists():
                    can_perform_approval = True
        else:
            can_perform_approval = True
    else:
        pending_approval = None
    
    # 添加左侧菜单
    module_sidebar_nav = _build_delivery_sidebar_nav(permission_set, request.path)
    delivery_sidebar_nav = module_sidebar_nav  # 兼容旧模板
    
    return render(request, "delivery_customer/delivery_approval_detail.html", {
        "page_title": "交付审核详情",
        "page_icon": "✅",
        "delivery": delivery,
        "can_approve": can_approve,
        "can_perform_approval": can_perform_approval,
        "approval_history": approval_history,
        "pending_approval": pending_approval,
        "full_top_nav": _build_full_top_nav(permission_set, request.user),
        "module_sidebar_nav": module_sidebar_nav,
        "delivery_sidebar_nav": delivery_sidebar_nav,  # 兼容旧模板
    })


@login_required
def delivery_approval_action(request, delivery_id):
    """交付审核操作"""
    from backend.apps.delivery_customer.models import DeliveryRecord, DeliveryApproval, DeliveryTracking
    from django.contrib import messages
    from django.shortcuts import redirect
    from django.utils import timezone
    
    permission_set = get_user_permission_codes(request.user)
    
    # 权限检查
    if not _permission_granted('delivery_center.approve', permission_set):
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("无权限进行交付审核")
    
    try:
        delivery = DeliveryRecord.objects.get(id=delivery_id)
    except DeliveryRecord.DoesNotExist:
        from django.http import Http404
        raise Http404("交付记录不存在")
    
    if request.method == 'POST':
        action = request.POST.get('action')  # approve, reject
        comment = request.POST.get('comment', '')
        
        if not comment:
            messages.error(request, '审核意见不能为空')
            return redirect('delivery_pages:delivery_approval_detail', delivery_id=delivery.id)
        
        # 检查是否可以审核
        if delivery.status not in ['submitted', 'pending_approval', 'approving']:
            messages.error(request, '该交付记录当前状态不允许审核')
            return redirect('delivery_pages:delivery_approval_detail', delivery_id=delivery.id)
        
        # 检查是否已经有待审核的记录
        pending_approval = delivery.approvals.filter(
            approver=request.user,
            result='pending'
        ).first()
        
        if pending_approval:
            # 更新现有审核记录
            pending_approval.result = 'approved' if action == 'approve' else 'rejected'
            pending_approval.comment = comment
            pending_approval.approval_time = timezone.now()
            pending_approval.save()
            approval = pending_approval
        else:
            # 创建新的审核记录
            approval = DeliveryApproval.objects.create(
                delivery_record=delivery,
                approver=request.user,
                result='approved' if action == 'approve' else 'rejected',
                comment=comment,
                approval_time=timezone.now()
            )
        
        # 更新交付记录状态
        if action == 'approve':
            delivery.status = 'approved'
            messages.success(request, '审核通过')
        else:
            delivery.status = 'rejected'
            messages.success(request, '审核已驳回')
        
        # 如果审核通过，更新提交时间
        if action == 'approve' and not delivery.submitted_at:
            delivery.submitted_at = timezone.now()
        
        delivery.save()
        
        # 创建跟踪记录
        DeliveryTracking.objects.create(
            delivery_record=delivery,
            event_type='submitted',
            event_description=f'审核{approval.get_result_display()}：{comment}',
            operator=request.user
        )
        
        # 发送通知给创建人
        try:
            from backend.apps.production_management.models import ProjectTeamNotification
            from django.urls import reverse
            
            if delivery.created_by:
                title = f'交付记录审核{approval.get_result_display()}：{delivery.delivery_number}'
                message = (
                    f'您的交付记录《{delivery.title}》已被{request.user.get_full_name() or request.user.username}{approval.get_result_display()}。\n'
                    f'审核意见：{comment}\n'
                    f'审核时间：{approval.approval_time.strftime("%Y-%m-%d %H:%M") if approval.approval_time else "未知"}'
                )
                
                # 构建跳转链接
                try:
                    action_url = reverse('delivery_pages:delivery_detail', args=[delivery.id])
                except Exception:
                    action_url = ''
                
                ProjectTeamNotification.objects.create(
                    project=delivery.project,
                    recipient=delivery.created_by,
                    operator=request.user,
                    title=title,
                    message=message,
                    category='approval',
                    action_url=action_url,
                    context={
                        'delivery_id': delivery.id,
                        'delivery_number': delivery.delivery_number,
                        'approval_result': approval.result,
                        'approval_id': approval.id,
                    }
                )
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f'发送审核通知失败: {str(e)}', exc_info=True)
        
        return redirect('delivery_pages:delivery_approval_list')
    
    return redirect('delivery_pages:delivery_approval_detail', delivery_id=delivery.id)


@login_required
def delivery_email_list(request):
    """邮件发送列表页"""
    from backend.apps.delivery_customer.models import DeliveryRecord
    from django.core.paginator import Paginator
    from django.db.models import Q
    
    permission_set = get_user_permission_codes(request.user)
    
    # 权限检查
    if not _permission_granted('delivery_center.view', permission_set):
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("无权限访问邮件发送")
    
    # 获取查询参数
    email_status = request.GET.get('email_status', 'pending')  # pending, sending, sent, failed
    page_num = request.GET.get('page', 1)
    
    # 构建查询：只查询邮件交付方式的记录
    queryset = DeliveryRecord.objects.filter(delivery_method='email')
    
    # 权限过滤
    if not _permission_granted('delivery_center.view_all', permission_set):
        queryset = queryset.filter(
            Q(created_by=request.user) | 
            Q(project__team_members__user=request.user)
        ).distinct()
    
    # 根据邮件状态筛选
    if email_status == 'pending':
        # 待发送：审核通过，但还未发送
        queryset = queryset.filter(status='approved')
    elif email_status == 'sending':
        # 发送中：状态为已发送但时间很近（5分钟内）
        from django.utils import timezone
        from datetime import timedelta
        five_minutes_ago = timezone.now() - timedelta(minutes=5)
        queryset = queryset.filter(
            status='sent',
            sent_at__gte=five_minutes_ago
        )
    elif email_status == 'sent':
        # 已发送：状态为已发送
        queryset = queryset.filter(status='sent')
    elif email_status == 'failed':
        # 发送失败：状态为发送失败
        queryset = queryset.filter(status='failed')
    
    # 排序和分页
    queryset = queryset.select_related('project', 'client', 'created_by', 'sent_by').defer('client__total_execution_amount').prefetch_related('files').order_by('-created_at')
    paginator = Paginator(queryset, 20)
    page = paginator.get_page(page_num)
    
    # 统计信息
    pending_count = DeliveryRecord.objects.filter(delivery_method='email', status='approved').count()
    sending_count = DeliveryRecord.objects.filter(delivery_method='email', status='sent').count()
    sent_count = DeliveryRecord.objects.filter(delivery_method='email', status='sent').count()
    failed_count = DeliveryRecord.objects.filter(delivery_method='email', status='failed').count()
    
    # 添加左侧菜单
    module_sidebar_nav = _build_delivery_sidebar_nav(permission_set, request.path)
    delivery_sidebar_nav = module_sidebar_nav  # 兼容旧模板
    
    return render(request, "delivery_customer/delivery_email_list.html", {
        "page_title": "邮件发送",
        "page_icon": "📧",
        "email_deliveries": page,
        "email_status": email_status,
        "pending_count": pending_count,
        "sending_count": sending_count,
        "sent_count": sent_count,
        "failed_count": failed_count,
        "full_top_nav": _build_full_top_nav(permission_set, request.user),
        "module_sidebar_nav": module_sidebar_nav,
        "delivery_sidebar_nav": delivery_sidebar_nav,  # 兼容旧模板
    })


@login_required
def delivery_email_send(request, delivery_id):
    """邮件发送操作页"""
    from backend.apps.delivery_customer.models import DeliveryRecord
    from django.contrib import messages
    from django.shortcuts import redirect
    from django.db.models import Q
    
    permission_set = get_user_permission_codes(request.user)
    
    # 权限检查
    if not _permission_granted('delivery_center.view', permission_set):
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("无权限访问邮件发送")
    
    try:
        delivery = DeliveryRecord.objects.select_related(
            'project', 'client', 'created_by'
        ).prefetch_related('files').get(id=delivery_id)
    except DeliveryRecord.DoesNotExist:
        from django.http import Http404
        raise Http404("交付记录不存在")
    
    # 检查是否是邮件交付方式
    if delivery.delivery_method != 'email':
        messages.error(request, '该交付记录不是邮件交付方式')
        return redirect('delivery_pages:delivery_list')
    
    # POST请求：发送邮件
    if request.method == 'POST':
        from .services import DeliveryEmailService
        
        # 更新邮件信息（如果用户修改了）
        email_subject = request.POST.get('email_subject', '').strip()
        email_message = request.POST.get('email_message', '').strip()
        cc_emails = request.POST.get('cc_emails', '').strip()
        bcc_emails = request.POST.get('bcc_emails', '').strip()
        
        # 检查是否可以发送
        if delivery.status != 'approved':
            messages.error(request, '只能发送审核通过的交付记录')
            return redirect('delivery_pages:delivery_email_send', delivery_id=delivery.id)
        
        # 检查收件人邮箱
        if not delivery.recipient_email:
            messages.error(request, '收件人邮箱不能为空')
            return redirect('delivery_pages:delivery_email_send', delivery_id=delivery.id)
        
        # 检查邮件主题
        if not email_subject:
            messages.error(request, '邮件主题不能为空')
            return redirect('delivery_pages:delivery_email_send', delivery_id=delivery.id)
        
        # 检查邮件正文
        if not email_message:
            messages.error(request, '邮件正文不能为空')
            return redirect('delivery_pages:delivery_email_send', delivery_id=delivery.id)
        
        if email_subject:
            delivery.email_subject = email_subject
        if email_message:
            delivery.email_message = email_message
        if cc_emails:
            delivery.cc_emails = cc_emails
        if bcc_emails:
            delivery.bcc_emails = bcc_emails
        
        # 设置发送人
        delivery.sent_by = request.user
        delivery.save()
        
        # 发送邮件（传入当前用户作为发送人）
        success = DeliveryEmailService.send_delivery_email(delivery, user=request.user)
        
        if success:
            messages.success(request, '邮件发送成功')
            return redirect('delivery_pages:delivery_email_list')
        else:
            messages.error(request, f'邮件发送失败：{delivery.error_message}')
            return redirect('delivery_pages:delivery_email_send', delivery_id=delivery.id)
    
    # GET请求：显示发送页面
    # 检查是否可以发送（审核通过且未发送）
    can_send = delivery.status == 'approved' and not delivery.sent_at
    
    # 添加左侧菜单
    module_sidebar_nav = _build_delivery_sidebar_nav(permission_set, request.path)
    delivery_sidebar_nav = module_sidebar_nav  # 兼容旧模板
    
    return render(request, "delivery_customer/delivery_email_send.html", {
        "page_title": "发送邮件",
        "page_icon": "📧",
        "delivery": delivery,
        "can_send": can_send,
        "full_top_nav": _build_full_top_nav(permission_set, request.user),
        "module_sidebar_nav": module_sidebar_nav,
        "delivery_sidebar_nav": delivery_sidebar_nav,  # 兼容旧模板
    })


@login_required
def delivery_express_list(request):
    """快递寄送列表页"""
    from backend.apps.delivery_customer.models import DeliveryRecord
    from django.core.paginator import Paginator
    from django.db.models import Q
    
    permission_set = get_user_permission_codes(request.user)
    
    # 权限检查
    if not _permission_granted('delivery_center.view', permission_set):
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("无权限访问快递寄送")
    
    # 获取查询参数
    express_status = request.GET.get('express_status', 'pending')  # pending, in_transit, delivered, failed
    page_num = request.GET.get('page', 1)
    
    # 构建查询：只查询快递交付方式的记录
    queryset = DeliveryRecord.objects.filter(delivery_method='express')
    
    # 权限过滤
    if not _permission_granted('delivery_center.view_all', permission_set):
        queryset = queryset.filter(
            Q(created_by=request.user) | 
            Q(project__team_members__user=request.user)
        ).distinct()
    
    # 根据快递状态筛选
    if express_status == 'pending':
        # 待寄送：审核通过，但还未寄送
        queryset = queryset.filter(status='approved')
    elif express_status == 'in_transit':
        # 寄送中：状态为运输中
        queryset = queryset.filter(status='in_transit')
    elif express_status == 'delivered':
        # 已送达：状态为已送达
        queryset = queryset.filter(status='delivered')
    elif express_status == 'failed':
        # 寄送失败：状态为发送失败
        queryset = queryset.filter(status='failed')
    
    # 排序和分页
    queryset = queryset.select_related('project', 'client', 'created_by', 'sent_by').defer('client__total_execution_amount').prefetch_related('files').order_by('-created_at')
    paginator = Paginator(queryset, 20)
    page = paginator.get_page(page_num)
    
    # 统计信息
    pending_count = DeliveryRecord.objects.filter(delivery_method='express', status='approved').count()
    in_transit_count = DeliveryRecord.objects.filter(delivery_method='express', status='in_transit').count()
    delivered_count = DeliveryRecord.objects.filter(delivery_method='express', status='delivered').count()
    failed_count = DeliveryRecord.objects.filter(delivery_method='express', status='failed').count()
    
    # 添加左侧菜单
    module_sidebar_nav = _build_delivery_sidebar_nav(permission_set, request.path)
    delivery_sidebar_nav = module_sidebar_nav  # 兼容旧模板
    
    return render(request, "delivery_customer/delivery_express_list.html", {
        "page_title": "快递寄送",
        "page_icon": "📦",
        "express_deliveries": page,
        "express_status": express_status,
        "pending_count": pending_count,
        "in_transit_count": in_transit_count,
        "delivered_count": delivered_count,
        "failed_count": failed_count,
        "full_top_nav": _build_full_top_nav(permission_set, request.user),
        "module_sidebar_nav": module_sidebar_nav,
        "delivery_sidebar_nav": delivery_sidebar_nav,  # 兼容旧模板
    })


@login_required
def delivery_express_send(request, delivery_id):
    """快递寄送操作页"""
    from backend.apps.delivery_customer.models import DeliveryRecord, DeliveryTracking
    from django.contrib import messages
    from django.shortcuts import redirect
    from django.utils import timezone
    from django.db.models import Q
    
    permission_set = get_user_permission_codes(request.user)
    
    # 权限检查
    if not _permission_granted('delivery_center.view', permission_set):
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("无权限访问快递寄送")
    
    try:
        delivery = DeliveryRecord.objects.select_related(
            'project', 'client', 'created_by'
        ).prefetch_related('files').get(id=delivery_id)
    except DeliveryRecord.DoesNotExist:
        from django.http import Http404
        raise Http404("交付记录不存在")
    
    # 检查是否是快递交付方式
    if delivery.delivery_method != 'express':
        messages.error(request, '该交付记录不是快递交付方式')
        return redirect('delivery_pages:delivery_list')
    
    # POST请求：寄送快递
    if request.method == 'POST':
        express_company = request.POST.get('express_company', '').strip()
        express_number = request.POST.get('express_number', '').strip()
        express_fee = request.POST.get('express_fee', '').strip()
        
        # 检查是否可以寄送
        if delivery.status != 'approved':
            messages.error(request, '只能寄送审核通过的交付记录')
            return redirect('delivery_pages:delivery_express_send', delivery_id=delivery.id)
        
        # 验证必填字段
        if not express_company:
            messages.error(request, '请选择快递公司')
            return redirect('delivery_pages:delivery_express_send', delivery_id=delivery.id)
        
        if not express_number:
            messages.error(request, '请输入快递单号')
            return redirect('delivery_pages:delivery_express_send', delivery_id=delivery.id)
        
        # 更新快递信息
        delivery.express_company = express_company
        delivery.express_number = express_number
        if express_fee:
            try:
                delivery.express_fee = float(express_fee)
            except ValueError:
                messages.error(request, '快递费用格式不正确')
                return redirect('delivery_pages:delivery_express_send', delivery_id=delivery.id)
        
        # 更新状态
        delivery.status = 'in_transit'
        delivery.sent_at = timezone.now()
        delivery.sent_by = request.user
        delivery.error_message = ''
        delivery.save()
        
        # 创建跟踪记录
        DeliveryTracking.objects.create(
            delivery_record=delivery,
            event_type='sent',
            event_description=f'快递已寄出，快递公司：{express_company}，单号：{express_number}',
            operator=request.user
        )
        
        messages.success(request, '快递寄送信息已保存')
        return redirect('delivery_pages:delivery_express_list')
    
    # GET请求：显示寄送页面
    # 检查是否可以寄送（审核通过且未寄送）
    can_send = delivery.status == 'approved' and not delivery.sent_at
    
    # 快递公司列表
    express_companies = [
        ('顺丰', '顺丰速运'),
        ('圆通', '圆通速递'),
        ('中通', '中通快递'),
        ('申通', '申通快递'),
        ('韵达', '韵达速递'),
        ('EMS', '中国邮政EMS'),
        ('京东', '京东物流'),
        ('德邦', '德邦快递'),
        ('其他', '其他'),
    ]
    
    # 添加左侧菜单
    module_sidebar_nav = _build_delivery_sidebar_nav(permission_set, request.path)
    delivery_sidebar_nav = module_sidebar_nav  # 兼容旧模板
    
    return render(request, "delivery_customer/delivery_express_send.html", {
        "page_title": "寄送快递",
        "page_icon": "📦",
        "delivery": delivery,
        "can_send": can_send,
        "express_companies": express_companies,
        "full_top_nav": _build_full_top_nav(permission_set, request.user),
        "module_sidebar_nav": module_sidebar_nav,
        "delivery_sidebar_nav": delivery_sidebar_nav,  # 兼容旧模板
    })


@login_required
def delivery_receipt_list(request):
    """签收确认列表页"""
    from backend.apps.delivery_customer.models import DeliveryRecord
    from django.core.paginator import Paginator
    from django.db.models import Q
    
    permission_set = get_user_permission_codes(request.user)
    
    # 权限检查
    if not _permission_granted('delivery_center.view', permission_set):
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("无权限访问签收确认")
    
    # 获取查询参数
    receipt_status = request.GET.get('receipt_status', 'pending')  # pending, received, rejected
    page_num = request.GET.get('page', 1)
    
    # 构建查询：查询已送达的记录
    queryset = DeliveryRecord.objects.filter(
        Q(status='delivered') | Q(status='sent') | Q(status='received')
    )
    
    # 权限过滤
    if not _permission_granted('delivery_center.view_all', permission_set):
        queryset = queryset.filter(
            Q(created_by=request.user) | 
            Q(project__team_members__user=request.user)
        ).distinct()
    
    # 根据签收状态筛选
    if receipt_status == 'pending':
        # 待签收：已送达但未确认
        queryset = queryset.filter(
            Q(status='delivered') | Q(status='sent')
        ).filter(confirmed_at__isnull=True)
    elif receipt_status == 'received':
        # 已签收：已确认
        queryset = queryset.filter(status='confirmed')
    elif receipt_status == 'rejected':
        # 拒收：状态为已拒绝或失败
        queryset = queryset.filter(
            Q(status='rejected') | Q(status='failed')
        )
    
    # 排序和分页
    queryset = queryset.select_related('project', 'client', 'created_by', 'sent_by').defer('client__total_execution_amount').prefetch_related('files').order_by('-delivered_at', '-sent_at', '-created_at')
    paginator = Paginator(queryset, 20)
    page = paginator.get_page(page_num)
    
    # 统计信息
    pending_count = DeliveryRecord.objects.filter(
        Q(status='delivered') | Q(status='sent')
    ).filter(confirmed_at__isnull=True).count()
    received_count = DeliveryRecord.objects.filter(status='confirmed').count()
    rejected_count = DeliveryRecord.objects.filter(
        Q(status='rejected') | Q(status='failed')
    ).count()
    
    # 添加左侧菜单
    module_sidebar_nav = _build_delivery_sidebar_nav(permission_set, request.path)
    delivery_sidebar_nav = module_sidebar_nav  # 兼容旧模板
    
    return render(request, "delivery_customer/delivery_receipt_list.html", {
        "page_title": "签收确认",
        "page_icon": "✅",
        "receipt_deliveries": page,
        "receipt_status": receipt_status,
        "pending_count": pending_count,
        "received_count": received_count,
        "rejected_count": rejected_count,
        "full_top_nav": _build_full_top_nav(permission_set, request.user),
        "module_sidebar_nav": module_sidebar_nav,
        "delivery_sidebar_nav": delivery_sidebar_nav,  # 兼容旧模板
    })


@login_required
def delivery_receipt_confirm(request, delivery_id):
    """签收确认操作页"""
    from backend.apps.delivery_customer.models import DeliveryRecord, DeliveryTracking, DeliveryFile
    from django.contrib import messages
    from django.shortcuts import redirect
    from django.utils import timezone
    from django.db.models import Q
    import os
    
    permission_set = get_user_permission_codes(request.user)
    
    # 权限检查
    if not _permission_granted('delivery_center.view', permission_set):
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("无权限访问签收确认")
    
    try:
        delivery = DeliveryRecord.objects.select_related(
            'project', 'client', 'created_by'
        ).prefetch_related('files').get(id=delivery_id)
    except DeliveryRecord.DoesNotExist:
        from django.http import Http404
        raise Http404("交付记录不存在")
    
    # POST请求：签收确认或拒收
    if request.method == 'POST':
        action = request.POST.get('action', '')  # confirm 或 reject
        
        if action == 'confirm':
            # 签收确认
            receipt_name = request.POST.get('receipt_name', '').strip()
            receipt_phone = request.POST.get('receipt_phone', '').strip()
            receipt_notes = request.POST.get('receipt_notes', '').strip()
            
            # 验证必填字段
            if not receipt_name:
                messages.error(request, '签收人姓名不能为空')
                return redirect('delivery_pages:delivery_receipt_confirm', delivery_id=delivery.id)
            
            # 更新状态
            delivery.status = 'confirmed'
            delivery.confirmed_at = timezone.now()
            # 使用反馈字段存储签收人信息
            delivery.feedback_by = receipt_name
            if receipt_phone:
                delivery.feedback_content = f"签收人：{receipt_name}，联系电话：{receipt_phone}"
                if receipt_notes:
                    delivery.feedback_content += f"\n签收备注：{receipt_notes}"
            elif receipt_notes:
                delivery.feedback_content = f"签收人：{receipt_name}\n签收备注：{receipt_notes}"
            else:
                delivery.feedback_content = f"签收人：{receipt_name}"
            delivery.feedback_received = True
            delivery.feedback_time = timezone.now()
            delivery.save()
            
            # 处理签收凭证上传
            receipt_file = request.FILES.get('receipt_file')
            if receipt_file:
                # 保存签收凭证文件
                file_name = receipt_file.name
                file_size = receipt_file.size
                file_ext = os.path.splitext(file_name)[1][1:].lower()
                
                # 创建交付文件记录（标记为签收凭证）
                DeliveryFile.objects.create(
                    delivery_record=delivery,
                    file=receipt_file,
                    file_name=file_name,
                    file_type='image' if file_ext in ['jpg', 'jpeg', 'png', 'gif'] else 'document',
                    file_size=file_size,
                    file_extension=file_ext,
                    description='签收凭证',
                    uploaded_by=request.user
                )
            
            # 创建跟踪记录
            DeliveryTracking.objects.create(
                delivery_record=delivery,
                event_type='confirmed',
                event_description=f'已签收确认，签收人：{receipt_name}',
                operator=request.user
            )
            
            messages.success(request, '签收确认成功')
            return redirect('delivery_pages:delivery_receipt_list')
        
        elif action == 'reject':
            # 拒收处理
            reject_reason = request.POST.get('reject_reason', '').strip()
            
            if not reject_reason:
                messages.error(request, '拒收原因不能为空')
                return redirect('delivery_pages:delivery_receipt_confirm', delivery_id=delivery.id)
            
            # 更新状态
            delivery.status = 'rejected'
            delivery.error_message = f"拒收原因：{reject_reason}"
            delivery.save()
            
            # 创建跟踪记录
            DeliveryTracking.objects.create(
                delivery_record=delivery,
                event_type='rejected',
                event_description=f'已拒收，拒收原因：{reject_reason}',
                operator=request.user
            )
            
            messages.warning(request, '已记录拒收信息')
            return redirect('delivery_pages:delivery_receipt_list')
    
    # GET请求：显示签收确认页面
    # 检查是否可以签收（已送达或已发送，但未确认）
    can_confirm = (delivery.status == 'delivered' or delivery.status == 'sent') and not delivery.confirmed_at
    can_reject = can_confirm  # 可以签收就可以拒收
    
    # 添加左侧菜单
    module_sidebar_nav = _build_delivery_sidebar_nav(permission_set, request.path)
    delivery_sidebar_nav = module_sidebar_nav  # 兼容旧模板
    
    return render(request, "delivery_customer/delivery_receipt_confirm.html", {
        "page_title": "签收确认",
        "page_icon": "✅",
        "delivery": delivery,
        "can_confirm": can_confirm,
        "can_reject": can_reject,
        "full_top_nav": _build_full_top_nav(permission_set, request.user),
        "module_sidebar_nav": module_sidebar_nav,
        "delivery_sidebar_nav": delivery_sidebar_nav,  # 兼容旧模板
    })


@login_required
def delivery_hand_delivery_list(request):
    """现场送达列表页"""
    from backend.apps.delivery_customer.models import DeliveryRecord
    from django.core.paginator import Paginator
    from django.db.models import Q
    
    permission_set = get_user_permission_codes(request.user)
    
    # 权限检查
    if not _permission_granted('delivery_center.view', permission_set):
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("无权限访问现场送达")
    
    # 获取查询参数
    delivery_status = request.GET.get('delivery_status', 'pending')  # pending, in_delivery, delivered, failed
    page_num = request.GET.get('page', 1)
    
    # 构建查询：只查询送达交付方式的记录
    queryset = DeliveryRecord.objects.filter(delivery_method='hand_delivery')
    
    # 权限过滤
    if not _permission_granted('delivery_center.view_all', permission_set):
        queryset = queryset.filter(
            Q(created_by=request.user) | 
            Q(project__team_members__user=request.user) |
            Q(delivery_person=request.user)
        ).distinct()
    
    # 根据送达状态筛选
    if delivery_status == 'pending':
        # 待送达：审核通过，但还未送达
        queryset = queryset.filter(status='approved')
    elif delivery_status == 'in_delivery':
        # 送达中：状态为运输中或已发送
        queryset = queryset.filter(status__in=['in_transit', 'sent'])
    elif delivery_status == 'delivered':
        # 已送达：状态为已送达
        queryset = queryset.filter(status='delivered')
    elif delivery_status == 'failed':
        # 送达失败：状态为发送失败
        queryset = queryset.filter(status='failed')
    
    # 排序和分页
    queryset = queryset.select_related('project', 'client', 'created_by', 'sent_by', 'delivery_person').defer('client__total_execution_amount').prefetch_related('files').order_by('-created_at')
    paginator = Paginator(queryset, 20)
    page = paginator.get_page(page_num)
    
    # 统计信息
    pending_count = DeliveryRecord.objects.filter(delivery_method='hand_delivery', status='approved').count()
    in_delivery_count = DeliveryRecord.objects.filter(delivery_method='hand_delivery', status__in=['in_transit', 'sent']).count()
    delivered_count = DeliveryRecord.objects.filter(delivery_method='hand_delivery', status='delivered').count()
    failed_count = DeliveryRecord.objects.filter(delivery_method='hand_delivery', status='failed').count()
    
    # 添加左侧菜单
    module_sidebar_nav = _build_delivery_sidebar_nav(permission_set, request.path)
    delivery_sidebar_nav = module_sidebar_nav  # 兼容旧模板
    
    return render(request, "delivery_customer/delivery_hand_delivery_list.html", {
        "page_title": "现场送达",
        "page_icon": "🚶",
        "hand_deliveries": page,
        "delivery_status": delivery_status,
        "pending_count": pending_count,
        "in_delivery_count": in_delivery_count,
        "delivered_count": delivered_count,
        "failed_count": failed_count,
        "full_top_nav": _build_full_top_nav(permission_set, request.user),
        "module_sidebar_nav": module_sidebar_nav,
        "delivery_sidebar_nav": delivery_sidebar_nav,  # 兼容旧模板
    })


@login_required
def delivery_hand_delivery_confirm(request, delivery_id):
    """现场送达操作页"""
    from backend.apps.delivery_customer.models import DeliveryRecord, DeliveryTracking, DeliveryFile
    from django.contrib import messages
    from django.shortcuts import redirect
    from django.utils import timezone
    from django.db.models import Q
    from django.contrib.auth import get_user_model
    import os
    
    permission_set = get_user_permission_codes(request.user)
    
    # 权限检查
    if not _permission_granted('delivery_center.view', permission_set):
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("无权限访问现场送达")
    
    try:
        delivery = DeliveryRecord.objects.select_related(
            'project', 'client', 'created_by', 'delivery_person'
        ).prefetch_related('files').get(id=delivery_id)
    except DeliveryRecord.DoesNotExist:
        from django.http import Http404
        raise Http404("交付记录不存在")
    
    # 检查是否是送达交付方式
    if delivery.delivery_method != 'hand_delivery':
        messages.error(request, '该交付记录不是现场送达方式')
        return redirect('delivery_pages:delivery_list')
    
    # POST请求：确认送达或送达失败
    if request.method == 'POST':
        action = request.POST.get('action', '')  # confirm 或 fail
        
        if action == 'confirm':
            # 送达确认
            delivery_person_id = request.POST.get('delivery_person_id', '').strip()
            delivery_notes = request.POST.get('delivery_notes', '').strip()
            
            # 验证必填字段
            if not delivery_person_id:
                messages.error(request, '请选择送达人')
                return redirect('delivery_pages:delivery_hand_delivery_confirm', delivery_id=delivery.id)
            
            try:
                User = get_user_model()
                delivery_person = User.objects.get(id=delivery_person_id)
            except User.DoesNotExist:
                messages.error(request, '送达人不存在')
                return redirect('delivery_pages:delivery_hand_delivery_confirm', delivery_id=delivery.id)
            
            # 更新状态
            delivery.status = 'delivered'
            delivery.delivered_at = timezone.now()
            delivery.delivery_person = delivery_person
            if delivery_notes:
                delivery.delivery_notes = delivery_notes
            delivery.sent_at = delivery.sent_at or timezone.now()
            delivery.sent_by = request.user
            delivery.error_message = ''
            delivery.save()
            
            # 处理送达凭证上传
            delivery_file = request.FILES.get('delivery_file')
            if delivery_file:
                file_name = delivery_file.name
                file_size = delivery_file.size
                file_ext = os.path.splitext(file_name)[1][1:].lower()
                
                # 创建交付文件记录（标记为送达凭证）
                DeliveryFile.objects.create(
                    delivery_record=delivery,
                    file=delivery_file,
                    file_name=file_name,
                    file_type='image' if file_ext in ['jpg', 'jpeg', 'png', 'gif'] else 'document',
                    file_size=file_size,
                    file_extension=file_ext,
                    description='送达凭证',
                    uploaded_by=request.user
                )
            
            # 创建跟踪记录
            DeliveryTracking.objects.create(
                delivery_record=delivery,
                event_type='delivered',
                event_description=f'现场送达完成，送达人：{delivery_person.get_full_name() or delivery_person.username}',
                operator=request.user
            )
            
            messages.success(request, '现场送达确认成功')
            return redirect('delivery_pages:delivery_hand_delivery_list')
        
        elif action == 'fail':
            # 送达失败处理
            fail_reason = request.POST.get('fail_reason', '').strip()
            
            if not fail_reason:
                messages.error(request, '失败原因不能为空')
                return redirect('delivery_pages:delivery_hand_delivery_confirm', delivery_id=delivery.id)
            
            # 更新状态
            delivery.status = 'failed'
            delivery.error_message = f"送达失败原因：{fail_reason}"
            delivery.save()
            
            # 创建跟踪记录
            DeliveryTracking.objects.create(
                delivery_record=delivery,
                event_type='failed',
                event_description=f'送达失败，失败原因：{fail_reason}',
                operator=request.user
            )
            
            messages.warning(request, '已记录送达失败信息')
            return redirect('delivery_pages:delivery_hand_delivery_list')
    
    # GET请求：显示送达确认页面
    # 检查是否可以送达（审核通过且未送达）
    can_deliver = delivery.status == 'approved' and not delivery.delivered_at
    
    # 获取员工列表（用于选择送达人）
    User = get_user_model()
    users = User.objects.filter(is_active=True).order_by('username')
    
    # 添加左侧菜单
    module_sidebar_nav = _build_delivery_sidebar_nav(permission_set, request.path)
    delivery_sidebar_nav = module_sidebar_nav  # 兼容旧模板
    
    return render(request, "delivery_customer/delivery_hand_delivery_confirm.html", {
        "page_title": "现场送达确认",
        "page_icon": "🚶",
        "delivery": delivery,
        "can_deliver": can_deliver,
        "users": users,
        "full_top_nav": _build_full_top_nav(permission_set, request.user),
        "module_sidebar_nav": module_sidebar_nav,
        "delivery_sidebar_nav": delivery_sidebar_nav,  # 兼容旧模板
    })


@login_required
def delivery_receive_list(request):
    """收件确认列表页"""
    from backend.apps.delivery_customer.models import DeliveryRecord
    from django.core.paginator import Paginator
    from django.db.models import Q
    
    permission_set = get_user_permission_codes(request.user)
    
    # 权限检查
    if not _permission_granted('delivery_center.view', permission_set):
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("无权限访问收件确认")
    
    # 获取查询参数
    receive_status = request.GET.get('receive_status', 'pending')  # pending, received
    page_num = request.GET.get('page', 1)
    
    # 构建查询：查询已送达或已发送的记录
    queryset = DeliveryRecord.objects.filter(
        Q(status='delivered') | Q(status='sent')
    )
    
    # 权限过滤
    if not _permission_granted('delivery_center.view_all', permission_set):
        queryset = queryset.filter(
            Q(created_by=request.user) | 
            Q(project__team_members__user=request.user)
        ).distinct()
    
    # 根据收件状态筛选
    if receive_status == 'pending':
        # 待收件：已送达或已发送，但未确认收件
        queryset = queryset.filter(received_at__isnull=True)
    elif receive_status == 'received':
        # 已收件：已确认收件
        queryset = queryset.filter(received_at__isnull=False)
    
    # 排序和分页
    queryset = queryset.select_related('project', 'client', 'created_by', 'sent_by').defer('client__total_execution_amount').prefetch_related('files').order_by('-delivered_at', '-sent_at', '-created_at')
    paginator = Paginator(queryset, 20)
    page = paginator.get_page(page_num)
    
    # 统计信息
    pending_count = DeliveryRecord.objects.filter(
        Q(status='delivered') | Q(status='sent')
    ).filter(received_at__isnull=True).count()
    received_count = DeliveryRecord.objects.filter(
        Q(status='delivered') | Q(status='sent')
    ).filter(received_at__isnull=False).count()
    
    # 添加左侧菜单
    module_sidebar_nav = _build_delivery_sidebar_nav(permission_set, request.path)
    delivery_sidebar_nav = module_sidebar_nav  # 兼容旧模板
    
    return render(request, "delivery_customer/delivery_receive_list.html", {
        "page_title": "收件确认",
        "page_icon": "📥",
        "receive_deliveries": page,
        "receive_status": receive_status,
        "pending_count": pending_count,
        "received_count": received_count,
        "full_top_nav": _build_full_top_nav(permission_set, request.user),
        "module_sidebar_nav": module_sidebar_nav,
        "delivery_sidebar_nav": delivery_sidebar_nav,  # 兼容旧模板
    })


@login_required
def delivery_receive_confirm(request, delivery_id):
    """收件确认操作页"""
    from backend.apps.delivery_customer.models import DeliveryRecord, DeliveryTracking
    from django.contrib import messages
    from django.shortcuts import redirect
    from django.utils import timezone
    from django.db.models import Q
    
    permission_set = get_user_permission_codes(request.user)
    
    # 权限检查
    if not _permission_granted('delivery_center.view', permission_set):
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("无权限访问收件确认")
    
    try:
        delivery = DeliveryRecord.objects.select_related(
            'project', 'client', 'created_by'
        ).prefetch_related('files').get(id=delivery_id)
    except DeliveryRecord.DoesNotExist:
        from django.http import Http404
        raise Http404("交付记录不存在")
    
    # POST请求：收件确认或未收件处理
    if request.method == 'POST':
        action = request.POST.get('action', '')  # confirm 或 not_received
        
        if action == 'confirm':
            # 收件确认
            receiver_name = request.POST.get('receiver_name', '').strip()
            receiver_phone = request.POST.get('receiver_phone', '').strip()
            receive_notes = request.POST.get('receive_notes', '').strip()
            
            # 验证必填字段
            if not receiver_name:
                messages.error(request, '收件人姓名不能为空')
                return redirect('delivery_pages:delivery_receive_confirm', delivery_id=delivery.id)
            
            # 更新状态
            delivery.received_at = timezone.now()
            # 使用反馈字段存储收件人信息
            if not delivery.feedback_by:
                delivery.feedback_by = receiver_name
            if receiver_phone:
                receive_info = f"收件人：{receiver_name}，联系电话：{receiver_phone}"
                if receive_notes:
                    receive_info += f"\n收件备注：{receive_notes}"
                if delivery.feedback_content:
                    delivery.feedback_content = f"{delivery.feedback_content}\n\n{receive_info}"
                else:
                    delivery.feedback_content = receive_info
            elif receive_notes:
                receive_info = f"收件人：{receiver_name}\n收件备注：{receive_notes}"
                if delivery.feedback_content:
                    delivery.feedback_content = f"{delivery.feedback_content}\n\n{receive_info}"
                else:
                    delivery.feedback_content = receive_info
            else:
                if not delivery.feedback_content:
                    delivery.feedback_content = f"收件人：{receiver_name}"
            delivery.save()
            
            # 创建跟踪记录
            DeliveryTracking.objects.create(
                delivery_record=delivery,
                event_type='received',
                event_description=f'已确认收件，收件人：{receiver_name}',
                operator=request.user
            )
            
            messages.success(request, '收件确认成功')
            return redirect('delivery_pages:delivery_receive_list')
        
        elif action == 'not_received':
            # 未收件处理
            not_received_reason = request.POST.get('not_received_reason', '').strip()
            
            if not not_received_reason:
                messages.error(request, '未收件原因不能为空')
                return redirect('delivery_pages:delivery_receive_confirm', delivery_id=delivery.id)
            
            # 更新状态和备注
            delivery.error_message = f"未收件原因：{not_received_reason}"
            if delivery.feedback_content:
                delivery.feedback_content = f"{delivery.feedback_content}\n\n未收件原因：{not_received_reason}"
            else:
                delivery.feedback_content = f"未收件原因：{not_received_reason}"
            delivery.save()
            
            # 创建跟踪记录
            DeliveryTracking.objects.create(
                delivery_record=delivery,
                event_type='not_received',
                event_description=f'未收件，原因：{not_received_reason}',
                operator=request.user
            )
            
            messages.warning(request, '已记录未收件信息')
            return redirect('delivery_pages:delivery_receive_list')
    
    # GET请求：显示收件确认页面
    # 检查是否可以确认收件（已送达或已发送，但未确认收件）
    can_confirm = (delivery.status == 'delivered' or delivery.status == 'sent') and not delivery.received_at
    
    # 添加左侧菜单
    module_sidebar_nav = _build_delivery_sidebar_nav(permission_set, request.path)
    delivery_sidebar_nav = module_sidebar_nav  # 兼容旧模板
    
    return render(request, "delivery_customer/delivery_receive_confirm.html", {
        "page_title": "收件确认",
        "page_icon": "📥",
        "delivery": delivery,
        "can_confirm": can_confirm,
        "full_top_nav": _build_full_top_nav(permission_set, request.user),
        "module_sidebar_nav": module_sidebar_nav,
        "delivery_sidebar_nav": delivery_sidebar_nav,  # 兼容旧模板
    })


@login_required
def delivery_feedback_list(request):
    """客户反馈列表页"""
    from backend.apps.delivery_customer.models import DeliveryRecord, DeliveryFeedback
    from django.core.paginator import Paginator
    from django.db.models import Q
    
    permission_set = get_user_permission_codes(request.user)
    
    # 权限检查
    if not _permission_granted('delivery_center.view', permission_set):
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("无权限访问客户反馈")
    
    # 获取查询参数
    feedback_status = request.GET.get('feedback_status', 'all')  # all, pending, received
    page_num = request.GET.get('page', 1)
    
    # 构建查询：查询已签收或已确认的记录
    queryset = DeliveryRecord.objects.filter(
        Q(status='confirmed') | Q(status='received') | Q(feedback_received=True)
    )
    
    # 权限过滤
    if not _permission_granted('delivery_center.view_all', permission_set):
        queryset = queryset.filter(
            Q(created_by=request.user) | 
            Q(project__team_members__user=request.user)
        ).distinct()
    
    # 根据反馈状态筛选
    if feedback_status == 'pending':
        # 待反馈：已签收或已确认，但未收到反馈
        queryset = queryset.filter(feedback_received=False)
    elif feedback_status == 'received':
        # 已反馈：已收到反馈
        queryset = queryset.filter(feedback_received=True)
    
    # 排序和分页
    queryset = queryset.select_related('project', 'client', 'created_by').defer('client__total_execution_amount').prefetch_related('feedbacks', 'files').order_by('-created_at')
    paginator = Paginator(queryset, 20)
    page = paginator.get_page(page_num)
    
    # 统计信息
    pending_count = DeliveryRecord.objects.filter(
        Q(status='confirmed') | Q(status='received')
    ).filter(feedback_received=False).count()
    received_count = DeliveryRecord.objects.filter(feedback_received=True).count()
    
    # 添加左侧菜单
    module_sidebar_nav = _build_delivery_sidebar_nav(permission_set, request.path)
    delivery_sidebar_nav = module_sidebar_nav  # 兼容旧模板
    
    return render(request, "delivery_customer/delivery_feedback_list.html", {
        "page_title": "客户反馈",
        "page_icon": "💬",
        "feedback_deliveries": page,
        "feedback_status": feedback_status,
        "pending_count": pending_count,
        "received_count": received_count,
        "full_top_nav": _build_full_top_nav(permission_set, request.user),
        "module_sidebar_nav": module_sidebar_nav,
        "delivery_sidebar_nav": delivery_sidebar_nav,  # 兼容旧模板
    })


@login_required
def delivery_feedback_create(request, delivery_id):
    """客户反馈创建页"""
    from backend.apps.delivery_customer.models import DeliveryRecord, DeliveryFeedback, DeliveryTracking
    from django.contrib import messages
    from django.shortcuts import redirect
    from django.utils import timezone
    from django.db.models import Q
    import os
    
    permission_set = get_user_permission_codes(request.user)
    
    # 权限检查
    if not _permission_granted('delivery_center.view', permission_set):
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("无权限访问客户反馈")
    
    try:
        delivery = DeliveryRecord.objects.select_related(
            'project', 'client', 'created_by'
        ).prefetch_related('files', 'feedbacks').get(id=delivery_id)
    except DeliveryRecord.DoesNotExist:
        from django.http import Http404
        raise Http404("交付记录不存在")
    
    # POST请求：创建反馈
    if request.method == 'POST':
        feedback_type = request.POST.get('feedback_type', '').strip()
        feedback_content = request.POST.get('feedback_content', '').strip()
        feedback_by = request.POST.get('feedback_by', '').strip()
        feedback_email = request.POST.get('feedback_email', '').strip()
        feedback_phone = request.POST.get('feedback_phone', '').strip()
        
        # 验证必填字段
        if not feedback_type:
            messages.error(request, '请选择反馈类型')
            return redirect('delivery_pages:delivery_feedback_create', delivery_id=delivery.id)
        
        if not feedback_content:
            messages.error(request, '反馈内容不能为空')
            return redirect('delivery_pages:delivery_feedback_create', delivery_id=delivery.id)
        
        if not feedback_by:
            messages.error(request, '反馈人姓名不能为空')
            return redirect('delivery_pages:delivery_feedback_create', delivery_id=delivery.id)
        
        # 创建反馈记录
        feedback = DeliveryFeedback.objects.create(
            delivery_record=delivery,
            feedback_type=feedback_type,
            content=feedback_content,
            feedback_by=feedback_by,
            feedback_email=feedback_email,
            feedback_phone=feedback_phone,
        )
        
        # 处理反馈附件上传
        feedback_files = request.FILES.getlist('feedback_files')
        if feedback_files:
            from backend.apps.delivery_customer.models import DeliveryFile
            for uploaded_file in feedback_files:
                file_name = uploaded_file.name
                file_size = uploaded_file.size
                file_ext = os.path.splitext(file_name)[1][1:].lower()
                
                DeliveryFile.objects.create(
                    delivery_record=delivery,
                    file=uploaded_file,
                    file_name=file_name,
                    file_type='document' if file_ext in ['pdf', 'doc', 'docx'] else 'other',
                    file_size=file_size,
                    file_extension=file_ext,
                    description=f'反馈附件：{feedback_by}',
                    uploaded_by=request.user
                )
        
        # 更新交付记录状态
        delivery.feedback_received = True
        delivery.feedback_content = feedback_content
        delivery.feedback_by = feedback_by
        delivery.feedback_time = timezone.now()
        delivery.save()
        
        # 创建跟踪记录
        DeliveryTracking.objects.create(
            delivery_record=delivery,
            event_type='feedback',
            event_description=f'收到客户反馈：{feedback.get_feedback_type_display()}',
            operator=request.user
        )
        
        messages.success(request, '客户反馈已提交')
        return redirect('delivery_pages:delivery_feedback_list')
    
    # GET请求：显示反馈创建页面
    # 检查是否可以创建反馈（已签收或已确认）
    can_create_feedback = delivery.status in ['confirmed', 'received'] or delivery.feedback_received
    
    # 反馈类型选项
    feedback_types = DeliveryFeedback.FEEDBACK_TYPE_CHOICES
    
    # 添加左侧菜单
    module_sidebar_nav = _build_delivery_sidebar_nav(permission_set, request.path)
    delivery_sidebar_nav = module_sidebar_nav  # 兼容旧模板
    
    return render(request, "delivery_customer/delivery_feedback_create.html", {
        "page_title": "客户反馈",
        "page_icon": "💬",
        "delivery": delivery,
        "can_create_feedback": can_create_feedback,
        "feedback_types": feedback_types,
        "full_top_nav": _build_full_top_nav(permission_set, request.user),
        "module_sidebar_nav": module_sidebar_nav,
        "delivery_sidebar_nav": delivery_sidebar_nav,  # 兼容旧模板
    })


@login_required
def delivery_achievement_list(request):
    """成果确认列表页"""
    from backend.apps.delivery_customer.models import DeliveryRecord
    from django.core.paginator import Paginator
    from django.db.models import Q
    
    permission_set = get_user_permission_codes(request.user)
    
    # 权限检查
    if not _permission_granted('delivery_center.view', permission_set):
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("无权限访问成果确认")
    
    # 获取查询参数
    confirmation_status = request.GET.get('confirmation_status', 'all')  # all, pending, confirmed, rejected
    page_num = request.GET.get('page', 1)
    
    # 构建查询：查询成果确认函类型的交付记录
    # 注意：这里假设成果确认函的交付类型为 'achievement_confirmation'，或者通过标题/描述筛选
    queryset = DeliveryRecord.objects.filter(
        Q(title__icontains='成果确认函') | 
        Q(title__icontains='确认函') |
        Q(description__icontains='成果确认函')
    )
    
    # 如果模型中有delivery_type字段，可以使用：
    # queryset = DeliveryRecord.objects.filter(delivery_type='achievement_confirmation')
    
    # 权限过滤
    if not _permission_granted('delivery_center.view_all', permission_set):
        queryset = queryset.filter(
            Q(created_by=request.user) | 
            Q(project__team_members__user=request.user)
        ).distinct()
    
    # 根据确认状态筛选
    if confirmation_status == 'pending':
        # 待确认：已送达或已发送，但未确认
        queryset = queryset.filter(
            Q(status='delivered') | Q(status='sent') | Q(status='received')
        ).filter(confirmed_at__isnull=True)
    elif confirmation_status == 'confirmed':
        # 已确认：状态为已确认
        queryset = queryset.filter(status='confirmed')
    elif confirmation_status == 'rejected':
        # 已拒绝：状态为已拒绝
        queryset = queryset.filter(status='rejected')
    
    # 排序和分页
    queryset = queryset.select_related('project', 'client', 'created_by', 'sent_by').defer('client__total_execution_amount').prefetch_related('files').order_by('-created_at')
    paginator = Paginator(queryset, 20)
    page = paginator.get_page(page_num)
    
    # 统计信息
    pending_count = DeliveryRecord.objects.filter(
        Q(title__icontains='成果确认函') | Q(title__icontains='确认函')
    ).filter(
        Q(status='delivered') | Q(status='sent') | Q(status='received')
    ).filter(confirmed_at__isnull=True).count()
    confirmed_count = DeliveryRecord.objects.filter(
        Q(title__icontains='成果确认函') | Q(title__icontains='确认函')
    ).filter(status='confirmed').count()
    rejected_count = DeliveryRecord.objects.filter(
        Q(title__icontains='成果确认函') | Q(title__icontains='确认函')
    ).filter(status='rejected').count()
    
    # 添加左侧菜单
    module_sidebar_nav = _build_delivery_sidebar_nav(permission_set, request.path)
    delivery_sidebar_nav = module_sidebar_nav  # 兼容旧模板
    
    return render(request, "delivery_customer/delivery_achievement_list.html", {
        "page_title": "成果确认",
        "page_icon": "✅",
        "achievement_deliveries": page,
        "confirmation_status": confirmation_status,
        "pending_count": pending_count,
        "confirmed_count": confirmed_count,
        "rejected_count": rejected_count,
        "full_top_nav": _build_full_top_nav(permission_set, request.user),
        "module_sidebar_nav": module_sidebar_nav,
        "delivery_sidebar_nav": delivery_sidebar_nav,  # 兼容旧模板
    })


@login_required
def delivery_achievement_confirm(request, delivery_id):
    """成果确认详情和甲方确认页"""
    from backend.apps.delivery_customer.models import DeliveryRecord, DeliveryTracking
    from django.contrib import messages
    from django.shortcuts import redirect
    from django.utils import timezone
    from django.db.models import Q
    
    permission_set = get_user_permission_codes(request.user)
    
    # 权限检查
    if not _permission_granted('delivery_center.view', permission_set):
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("无权限访问成果确认")
    
    try:
        delivery = DeliveryRecord.objects.select_related(
            'project', 'client', 'created_by'
        ).prefetch_related('files', 'tracking_records').get(id=delivery_id)
    except DeliveryRecord.DoesNotExist:
        from django.http import Http404
        raise Http404("交付记录不存在")
    
    # POST请求：甲方确认或拒绝
    if request.method == 'POST':
        action = request.POST.get('action', '')  # confirm 或 reject
        
        if action == 'confirm':
            # 甲方确认
            confirm_comment = request.POST.get('confirm_comment', '').strip()
            confirm_by = request.POST.get('confirm_by', '').strip()
            
            # 验证必填字段
            if not confirm_by:
                messages.error(request, '确认人姓名不能为空')
                return redirect('delivery_pages:delivery_achievement_confirm', delivery_id=delivery.id)
            
            # 更新状态
            delivery.status = 'confirmed'
            delivery.confirmed_at = timezone.now()
            # 使用反馈字段存储确认信息
            delivery.feedback_by = confirm_by
            if confirm_comment:
                delivery.feedback_content = f"确认人：{confirm_by}\n确认意见：{confirm_comment}"
            else:
                delivery.feedback_content = f"确认人：{confirm_by}"
            delivery.feedback_received = True
            delivery.feedback_time = timezone.now()
            delivery.save()
            
            # 创建跟踪记录
            DeliveryTracking.objects.create(
                delivery_record=delivery,
                event_type='confirmed',
                event_description=f'甲方已确认成果，确认人：{confirm_by}',
                operator=request.user
            )
            
            messages.success(request, '成果确认成功')
            return redirect('delivery_pages:delivery_achievement_list')
        
        elif action == 'reject':
            # 甲方拒绝
            reject_comment = request.POST.get('reject_comment', '').strip()
            reject_by = request.POST.get('reject_by', '').strip()
            
            if not reject_by:
                messages.error(request, '拒绝人姓名不能为空')
                return redirect('delivery_pages:delivery_achievement_confirm', delivery_id=delivery.id)
            
            if not reject_comment:
                messages.error(request, '拒绝原因不能为空')
                return redirect('delivery_pages:delivery_achievement_confirm', delivery_id=delivery.id)
            
            # 更新状态
            delivery.status = 'rejected'
            delivery.error_message = f"拒绝原因：{reject_comment}"
            delivery.feedback_by = reject_by
            delivery.feedback_content = f"拒绝人：{reject_by}\n拒绝原因：{reject_comment}"
            delivery.save()
            
            # 创建跟踪记录
            DeliveryTracking.objects.create(
                delivery_record=delivery,
                event_type='rejected',
                event_description=f'甲方已拒绝成果，拒绝人：{reject_by}，原因：{reject_comment}',
                operator=request.user
            )
            
            messages.warning(request, '已记录拒绝信息')
            return redirect('delivery_pages:delivery_achievement_list')
    
    # GET请求：显示确认页面
    # 检查是否可以确认（已送达、已发送或已接收，但未确认）
    can_confirm = (delivery.status in ['delivered', 'sent', 'received']) and not delivery.confirmed_at
    
    # 获取确认历史（通过跟踪记录）
    confirmation_history = delivery.tracking_records.filter(
        event_type__in=['confirmed', 'rejected']
    ).order_by('-created_at')
    
    # 添加左侧菜单
    module_sidebar_nav = _build_delivery_sidebar_nav(permission_set, request.path)
    delivery_sidebar_nav = module_sidebar_nav  # 兼容旧模板
    
    return render(request, "delivery_customer/delivery_achievement_confirm.html", {
        "page_title": "成果确认",
        "page_icon": "✅",
        "delivery": delivery,
        "can_confirm": can_confirm,
        "confirmation_history": confirmation_history,
        "full_top_nav": _build_full_top_nav(permission_set, request.user),
        "module_sidebar_nav": module_sidebar_nav,
        "delivery_sidebar_nav": delivery_sidebar_nav,  # 兼容旧模板
    })


@login_required
def delivery_satisfaction_list(request):
    """满意度评价列表页"""
    from backend.apps.delivery_customer.models import DeliveryRecord
    from django.core.paginator import Paginator
    from django.db.models import Q
    
    permission_set = get_user_permission_codes(request.user)
    
    # 权限检查
    if not _permission_granted('delivery_center.view', permission_set):
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("无权限访问满意度评价")
    
    # 获取查询参数
    satisfaction_status = request.GET.get('satisfaction_status', 'all')  # all, pending, rated
    page_num = request.GET.get('page', 1)
    
    # 构建查询：查询已签收或已确认的记录
    queryset = DeliveryRecord.objects.filter(
        Q(status='confirmed') | Q(status='received')
    )
    
    # 权限过滤
    if not _permission_granted('delivery_center.view_all', permission_set):
        queryset = queryset.filter(
            Q(created_by=request.user) | 
            Q(project__team_members__user=request.user)
        ).distinct()
    
    # 根据评价状态筛选
    # 注意：这里假设满意度评价通过DeliveryFeedback模型存储，feedback_type='satisfaction'
    # 或者通过其他字段标记是否已评价
    if satisfaction_status == 'pending':
        # 待评价：已签收或已确认，但未评价
        # 这里需要检查是否已有满意度评价记录
        from backend.apps.delivery_customer.models import DeliveryFeedback
        rated_delivery_ids = DeliveryFeedback.objects.filter(
            feedback_type__in=['satisfaction', 'rating']
        ).values_list('delivery_record_id', flat=True)
        queryset = queryset.exclude(id__in=rated_delivery_ids)
    elif satisfaction_status == 'rated':
        # 已评价：已有满意度评价记录
        from backend.apps.delivery_customer.models import DeliveryFeedback
        rated_delivery_ids = DeliveryFeedback.objects.filter(
            feedback_type__in=['satisfaction', 'rating']
        ).values_list('delivery_record_id', flat=True)
        queryset = queryset.filter(id__in=rated_delivery_ids)
    
    # 排序和分页
    queryset = queryset.select_related('project', 'client', 'created_by').defer('client__total_execution_amount').prefetch_related('feedbacks', 'files').order_by('-created_at')
    paginator = Paginator(queryset, 20)
    page = paginator.get_page(page_num)
    
    # 统计信息
    from backend.apps.delivery_customer.models import DeliveryFeedback
    rated_delivery_ids = DeliveryFeedback.objects.filter(
        feedback_type__in=['satisfaction', 'rating']
    ).values_list('delivery_record_id', flat=True)
    pending_count = DeliveryRecord.objects.filter(
        Q(status='confirmed') | Q(status='received')
    ).exclude(id__in=rated_delivery_ids).count()
    rated_count = DeliveryRecord.objects.filter(id__in=rated_delivery_ids).count()
    
    # 添加左侧菜单
    module_sidebar_nav = _build_delivery_sidebar_nav(permission_set, request.path)
    delivery_sidebar_nav = module_sidebar_nav  # 兼容旧模板
    
    return render(request, "delivery_customer/delivery_satisfaction_list.html", {
        "page_title": "满意度评价",
        "page_icon": "⭐",
        "satisfaction_deliveries": page,
        "satisfaction_status": satisfaction_status,
        "pending_count": pending_count,
        "rated_count": rated_count,
        "full_top_nav": _build_full_top_nav(permission_set, request.user),
        "module_sidebar_nav": module_sidebar_nav,
        "delivery_sidebar_nav": delivery_sidebar_nav,  # 兼容旧模板
    })


@login_required
def delivery_satisfaction_create(request, delivery_id):
    """满意度评价创建页"""
    from backend.apps.delivery_customer.models import DeliveryRecord, DeliveryFeedback, DeliveryTracking
    from django.contrib import messages
    from django.shortcuts import redirect
    from django.utils import timezone
    from django.db.models import Q
    
    permission_set = get_user_permission_codes(request.user)
    
    # 权限检查
    if not _permission_granted('delivery_center.view', permission_set):
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("无权限访问满意度评价")
    
    try:
        delivery = DeliveryRecord.objects.select_related(
            'project', 'client', 'created_by'
        ).prefetch_related('files', 'feedbacks').get(id=delivery_id)
    except DeliveryRecord.DoesNotExist:
        from django.http import Http404
        raise Http404("交付记录不存在")
    
    # POST请求：创建满意度评价
    if request.method == 'POST':
        rating = request.POST.get('rating', '').strip()
        satisfaction_content = request.POST.get('satisfaction_content', '').strip()
        satisfaction_by = request.POST.get('satisfaction_by', '').strip()
        satisfaction_dimensions = request.POST.getlist('satisfaction_dimensions')  # 多选
        
        # 验证必填字段
        if not rating:
            messages.error(request, '请选择满意度评分')
            return redirect('delivery_pages:delivery_satisfaction_create', delivery_id=delivery.id)
        
        try:
            rating_value = int(rating)
            if rating_value < 1 or rating_value > 5:
                messages.error(request, '满意度评分必须在1-5星之间')
                return redirect('delivery_pages:delivery_satisfaction_create', delivery_id=delivery.id)
        except ValueError:
            messages.error(request, '满意度评分格式不正确')
            return redirect('delivery_pages:delivery_satisfaction_create', delivery_id=delivery.id)
        
        if not satisfaction_by:
            messages.error(request, '评价人姓名不能为空')
            return redirect('delivery_pages:delivery_satisfaction_create', delivery_id=delivery.id)
        
        # 构建评价内容
        rating_stars = '⭐' * rating_value + '☆' * (5 - rating_value)
        content_parts = [f"满意度评分：{rating_stars} ({rating_value}星)"]
        
        if satisfaction_dimensions:
            dimension_names = {
                'file_quality': '文件质量',
                'delivery_timeliness': '交付及时性',
                'service_attitude': '服务态度',
                'communication': '沟通效率',
                'problem_solving': '问题解决能力',
            }
            dimension_list = [dimension_names.get(dim, dim) for dim in satisfaction_dimensions]
            content_parts.append(f"评价维度：{', '.join(dimension_list)}")
        
        if satisfaction_content:
            content_parts.append(f"评价内容：{satisfaction_content}")
        
        content = "\n".join(content_parts)
        
        # 创建满意度评价记录（使用DeliveryFeedback模型，feedback_type='satisfaction'）
        # 注意：如果DeliveryFeedback模型不支持satisfaction类型，可以使用'confirmed'或其他类型
        # 或者创建新的DeliverySatisfaction模型
        feedback = DeliveryFeedback.objects.create(
            delivery_record=delivery,
            feedback_type='confirmed',  # 使用confirmed类型，在content中存储满意度信息
            content=content,
            feedback_by=satisfaction_by,
        )
        
        # 更新交付记录（标记已评价）
        # 可以在feedback_content中存储满意度评分
        if not delivery.feedback_content:
            delivery.feedback_content = content
        else:
            delivery.feedback_content = f"{delivery.feedback_content}\n\n{content}"
        delivery.feedback_received = True
        delivery.feedback_time = timezone.now()
        if not delivery.feedback_by:
            delivery.feedback_by = satisfaction_by
        delivery.save()
        
        # 创建跟踪记录
        DeliveryTracking.objects.create(
            delivery_record=delivery,
            event_type='feedback',
            event_description=f'收到满意度评价：{rating_stars}',
            operator=request.user
        )
        
        messages.success(request, '满意度评价已提交')
        return redirect('delivery_pages:delivery_satisfaction_list')
    
    # GET请求：显示评价创建页面
    # 检查是否可以创建评价（已签收或已确认）
    can_create_satisfaction = delivery.status in ['confirmed', 'received']
    
    # 检查是否已评价
    from backend.apps.delivery_customer.models import DeliveryFeedback
    has_rated = DeliveryFeedback.objects.filter(
        delivery_record=delivery,
        feedback_type='confirmed',
        content__icontains='满意度评分'
    ).exists()
    
    # 评价维度选项
    satisfaction_dimensions = [
        ('file_quality', '文件质量'),
        ('delivery_timeliness', '交付及时性'),
        ('service_attitude', '服务态度'),
        ('communication', '沟通效率'),
        ('problem_solving', '问题解决能力'),
    ]
    
    # 添加左侧菜单
    module_sidebar_nav = _build_delivery_sidebar_nav(permission_set, request.path)
    delivery_sidebar_nav = module_sidebar_nav  # 兼容旧模板
    
    return render(request, "delivery_customer/delivery_satisfaction_create.html", {
        "page_title": "满意度评价",
        "page_icon": "⭐",
        "delivery": delivery,
        "can_create_satisfaction": can_create_satisfaction,
        "has_rated": has_rated,
        "satisfaction_dimensions": satisfaction_dimensions,
        "full_top_nav": _build_full_top_nav(permission_set, request.user),
        "module_sidebar_nav": module_sidebar_nav,
        "delivery_sidebar_nav": delivery_sidebar_nav,  # 兼容旧模板
    })


@login_required
def delivery_satisfaction_statistics(request):
    """满意度统计分析页"""
    from backend.apps.delivery_customer.models import DeliveryRecord, DeliveryFeedback
    from django.db.models import Q, Avg, Count
    from django.utils import timezone
    from datetime import timedelta
    
    permission_set = get_user_permission_codes(request.user)
    
    # 权限检查
    if not _permission_granted('delivery_center.view_statistics', permission_set):
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("无权限查看满意度统计")
    
    # 获取满意度评价记录
    satisfaction_feedbacks = DeliveryFeedback.objects.filter(
        content__icontains='满意度评分'
    ).select_related('delivery_record', 'delivery_record__project')
    
    # 权限过滤
    if not _permission_granted('delivery_center.view_all', permission_set):
        satisfaction_feedbacks = satisfaction_feedbacks.filter(
            Q(delivery_record__created_by=request.user) | 
            Q(delivery_record__project__team_members__user=request.user)
        ).distinct()
    
    # 解析评分数据
    ratings = []
    for feedback in satisfaction_feedbacks:
        # 从content中提取评分（格式：满意度评分：⭐⭐⭐⭐⭐ (5星)）
        import re
        match = re.search(r'\((\d+)星\)', feedback.content)
        if match:
            rating = int(match.group(1))
            ratings.append({
                'rating': rating,
                'delivery': feedback.delivery_record,
                'feedback': feedback,
                'date': feedback.created_at,
            })
    
    # 统计信息
    total_count = len(ratings)
    if total_count > 0:
        avg_rating = sum(r['rating'] for r in ratings) / total_count
        rating_distribution = {}
        for i in range(1, 6):
            rating_distribution[i] = sum(1 for r in ratings if r['rating'] == i)
    else:
        avg_rating = 0
        rating_distribution = {i: 0 for i in range(1, 6)}
    
    # 时间趋势（最近30天）
    thirty_days_ago = timezone.now() - timedelta(days=30)
    recent_ratings = [r for r in ratings if r['date'] >= thirty_days_ago]
    
    # 添加左侧菜单
    module_sidebar_nav = _build_delivery_sidebar_nav(permission_set, request.path)
    delivery_sidebar_nav = module_sidebar_nav  # 兼容旧模板
    
    return render(request, "delivery_customer/delivery_satisfaction_statistics.html", {
        "page_title": "满意度统计",
        "page_icon": "📊",
        "total_count": total_count,
        "avg_rating": avg_rating,
        "rating_distribution": rating_distribution,
        "recent_ratings": recent_ratings,
        "full_top_nav": _build_full_top_nav(permission_set, request.user),
        "module_sidebar_nav": module_sidebar_nav,
        "delivery_sidebar_nav": delivery_sidebar_nav,  # 兼容旧模板
    })


@login_required
def delivery_logistics_list(request):
    """物流跟踪列表页"""
    from backend.apps.delivery_customer.models import DeliveryRecord, DeliveryTracking
    from django.core.paginator import Paginator
    from django.db.models import Q
    
    permission_set = get_user_permission_codes(request.user)
    
    # 权限检查
    if not _permission_granted('delivery_center.view', permission_set):
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("无权限访问物流跟踪")
    
    # 获取查询参数
    logistics_status = request.GET.get('logistics_status', 'all')  # all, in_transit, delivered, failed
    search_query = request.GET.get('search', '').strip()
    page_num = request.GET.get('page', 1)
    
    # 构建查询：查询快递交付方式的记录
    queryset = DeliveryRecord.objects.filter(delivery_method='express')
    
    # 权限过滤
    if not _permission_granted('delivery_center.view_all', permission_set):
        queryset = queryset.filter(
            Q(created_by=request.user) | 
            Q(project__team_members__user=request.user)
        ).distinct()
    
    # 根据物流状态筛选
    if logistics_status == 'in_transit':
        # 运输中
        queryset = queryset.filter(status='in_transit')
    elif logistics_status == 'delivered':
        # 已送达
        queryset = queryset.filter(status='delivered')
    elif logistics_status == 'failed':
        # 失败
        queryset = queryset.filter(status='failed')
    
    # 搜索
    if search_query:
        queryset = queryset.filter(
            Q(delivery_number__icontains=search_query) |
            Q(express_number__icontains=search_query) |
            Q(title__icontains=search_query) |
            Q(express_company__icontains=search_query)
        )
    
    # 排序和分页
    queryset = queryset.select_related('project', 'client', 'created_by').defer('client__total_execution_amount').prefetch_related('tracking_records', 'files').order_by('-created_at')
    paginator = Paginator(queryset, 20)
    page = paginator.get_page(page_num)
    
    # 统计信息
    in_transit_count = DeliveryRecord.objects.filter(
        delivery_method='express', status='in_transit'
    ).count()
    delivered_count = DeliveryRecord.objects.filter(
        delivery_method='express', status='delivered'
    ).count()
    failed_count = DeliveryRecord.objects.filter(
        delivery_method='express', status='failed'
    ).count()
    total_count = DeliveryRecord.objects.filter(delivery_method='express').count()
    
    # 添加左侧菜单
    module_sidebar_nav = _build_delivery_sidebar_nav(permission_set, request.path)
    delivery_sidebar_nav = module_sidebar_nav  # 兼容旧模板
    
    return render(request, "delivery_customer/delivery_logistics_list.html", {
        "page_title": "物流跟踪",
        "page_icon": "🚚",
        "logistics_deliveries": page,
        "logistics_status": logistics_status,
        "search_query": search_query,
        "in_transit_count": in_transit_count,
        "delivered_count": delivered_count,
        "failed_count": failed_count,
        "total_count": total_count,
        "full_top_nav": _build_full_top_nav(permission_set, request.user),
        "module_sidebar_nav": module_sidebar_nav,
        "delivery_sidebar_nav": delivery_sidebar_nav,  # 兼容旧模板
    })


@login_required
def delivery_logistics_detail(request, delivery_id):
    """物流跟踪详情页"""
    from backend.apps.delivery_customer.models import DeliveryRecord, DeliveryTracking
    from django.contrib import messages
    from django.shortcuts import redirect
    from django.utils import timezone
    
    permission_set = get_user_permission_codes(request.user)
    
    # 权限检查
    if not _permission_granted('delivery_center.view', permission_set):
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("无权限访问物流跟踪")
    
    try:
        delivery = DeliveryRecord.objects.select_related(
            'project', 'client', 'created_by'
        ).prefetch_related('tracking_records', 'files').get(id=delivery_id)
    except DeliveryRecord.DoesNotExist:
        from django.http import Http404
        raise Http404("交付记录不存在")
    
    # POST请求：手动更新物流状态
    if request.method == 'POST':
        action = request.POST.get('action', '')
        
        if action == 'update_tracking':
            # 手动更新物流状态
            tracking_status = request.POST.get('tracking_status', '').strip()
            tracking_location = request.POST.get('tracking_location', '').strip()
            tracking_description = request.POST.get('tracking_description', '').strip()
            
            if not tracking_status:
                messages.error(request, '请选择物流状态')
                return redirect('delivery_pages:delivery_logistics_detail', delivery_id=delivery.id)
            
            # 创建跟踪记录
            DeliveryTracking.objects.create(
                delivery_record=delivery,
                event_type=tracking_status,
                event_description=tracking_description or f'物流状态更新：{tracking_status}',
                location=tracking_location,
                operator=request.user
            )
            
            # 更新交付记录状态（如果状态变化）
            if tracking_status == 'delivered' and delivery.status != 'delivered':
                delivery.status = 'delivered'
                delivery.delivered_at = timezone.now()
                delivery.save()
            elif tracking_status == 'in_transit' and delivery.status not in ['in_transit', 'delivered']:
                delivery.status = 'in_transit'
                delivery.save()
            
            messages.success(request, '物流状态已更新')
            return redirect('delivery_pages:delivery_logistics_detail', delivery_id=delivery.id)
        
        elif action == 'query_logistics':
            # 查询物流信息（调用API）
            if not delivery.express_number:
                messages.error(request, '快递单号不能为空')
                return redirect('delivery_pages:delivery_logistics_detail', delivery_id=delivery.id)
            
            if not delivery.express_company:
                messages.error(request, '快递公司不能为空')
                return redirect('delivery_pages:delivery_logistics_detail', delivery_id=delivery.id)
            
            # 调用快递查询API
            from .express_service import query_express_tracking
            
            success, logistics_data, message = query_express_tracking(
                delivery.express_company,
                delivery.express_number
            )
            
            if success:
                # 查询成功，更新物流跟踪记录
                tracks = logistics_data.get('tracks', [])
                
                # 检查是否有新的物流记录
                existing_times = set(
                    DeliveryTracking.objects.filter(
                        delivery_record=delivery
                    ).values_list('event_time', flat=True)
                )
                
                new_tracks_count = 0
                for track in tracks:
                    # 解析时间
                    track_time_str = track.get('time', '')
                    if track_time_str:
                        try:
                            from datetime import datetime
                            track_time = datetime.strptime(track_time_str, '%Y-%m-%d %H:%M:%S')
                            track_time = timezone.make_aware(track_time)
                            
                            # 检查是否已存在
                            if track_time not in existing_times:
                                # 创建新的跟踪记录
                                event_type = 'in_transit'
                                if '签收' in track.get('context', '') or '已签收' in track.get('context', ''):
                                    event_type = 'delivered'
                                elif '派送' in track.get('context', '') or '派件' in track.get('context', ''):
                                    event_type = 'out_for_delivery'
                                
                                DeliveryTracking.objects.create(
                                    delivery_record=delivery,
                                    event_type=event_type,
                                    event_description=track.get('context', ''),
                                    location=track.get('location', ''),
                                    operator=request.user,
                                    event_time=track_time,
                                )
                                new_tracks_count += 1
                        except Exception as e:
                            logger.error(f"解析物流时间失败: {str(e)}")
                
                # 更新交付记录状态
                status_code = logistics_data.get('status', '0')
                if status_code == '3':  # 已签收
                    if delivery.status != 'delivered':
                        delivery.status = 'delivered'
                        delivery.delivered_at = timezone.now()
                        delivery.save()
                elif status_code in ['0', '1', '5']:  # 在途、揽收、派件
                    if delivery.status != 'in_transit':
                        delivery.status = 'in_transit'
                        delivery.save()
                
                if new_tracks_count > 0:
                    messages.success(request, f'物流查询成功，新增 {new_tracks_count} 条物流记录')
                else:
                    messages.info(request, '物流查询成功，暂无新的物流记录')
            else:
                messages.error(request, f'物流查询失败：{message}')
            
            return redirect('delivery_pages:delivery_logistics_detail', delivery_id=delivery.id)
    
    # GET请求：显示物流跟踪详情
    # 获取物流跟踪记录（按时间排序）
    tracking_records = delivery.tracking_records.all().order_by('event_time', 'created_at')
    
    # 尝试自动查询物流信息（如果快递单号存在且状态为运输中）
    auto_query = request.GET.get('auto_query', 'false') == 'true'
    if auto_query and delivery.express_number and delivery.express_company and delivery.status == 'in_transit':
        from .express_service import query_express_tracking
        success, logistics_data, message = query_express_tracking(
            delivery.express_company,
            delivery.express_number
        )
        if success:
            # 更新物流跟踪记录（与POST请求中的逻辑相同）
            tracks = logistics_data.get('tracks', [])
            existing_times = set(
                DeliveryTracking.objects.filter(
                    delivery_record=delivery
                ).values_list('event_time', flat=True)
            )
            
            for track in tracks:
                track_time_str = track.get('time', '')
                if track_time_str:
                    try:
                        from datetime import datetime
                        track_time = datetime.strptime(track_time_str, '%Y-%m-%d %H:%M:%S')
                        track_time = timezone.make_aware(track_time)
                        
                        if track_time not in existing_times:
                            event_type = 'in_transit'
                            if '签收' in track.get('context', '') or '已签收' in track.get('context', ''):
                                event_type = 'delivered'
                            elif '派送' in track.get('context', '') or '派件' in track.get('context', ''):
                                event_type = 'out_for_delivery'
                            
                            DeliveryTracking.objects.create(
                                delivery_record=delivery,
                                event_type=event_type,
                                event_description=track.get('context', ''),
                                location=track.get('location', ''),
                                operator=request.user,
                                event_time=track_time,
                            )
                    except Exception as e:
                        logger.error(f"解析物流时间失败: {str(e)}")
            
            # 重新获取跟踪记录
            tracking_records = delivery.tracking_records.all().order_by('event_time', 'created_at')
    
    # 构建物流时间线
    logistics_timeline = []
    for tracking in tracking_records:
        logistics_timeline.append({
            'time': tracking.event_time if hasattr(tracking, 'event_time') and tracking.event_time else tracking.created_at,
            'event': tracking.get_event_type_display(),
            'description': tracking.event_description,
            'location': tracking.location,
            'operator': tracking.operator.get_full_name() if tracking.operator else '系统',
        })
    
    # 添加左侧菜单
    module_sidebar_nav = _build_delivery_sidebar_nav(permission_set, request.path)
    delivery_sidebar_nav = module_sidebar_nav  # 兼容旧模板
    
    return render(request, "delivery_customer/delivery_logistics_detail.html", {
        "page_title": "物流跟踪",
        "page_icon": "🚚",
        "delivery": delivery,
        "tracking_records": tracking_records,
        "logistics_timeline": logistics_timeline,
        "full_top_nav": _build_full_top_nav(permission_set, request.user),
        "module_sidebar_nav": module_sidebar_nav,
        "delivery_sidebar_nav": delivery_sidebar_nav,  # 兼容旧模板
    })


@login_required
def delivery_weekly_report_list(request):
    """每周快报列表页"""
    from backend.apps.delivery_customer.models import DeliveryRecord
    from backend.apps.production_management.models import Project
    from django.core.paginator import Paginator
    from django.db.models import Q
    
    permission_set = get_user_permission_codes(request.user)
    
    # 权限检查
    if not _permission_granted('delivery_center.view', permission_set):
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("无权限访问每周快报")
    
    # 获取查询参数
    project_id = request.GET.get('project_id', '')
    week_number = request.GET.get('week_number', '')
    page_num = request.GET.get('page', 1)
    
    # 构建查询：查询每周快报类型的交付记录
    queryset = DeliveryRecord.objects.filter(
        Q(title__icontains='每周快报') | 
        Q(title__icontains='周报') |
        Q(description__icontains='每周快报')
    )
    
    # 权限过滤
    if not _permission_granted('delivery_center.view_all', permission_set):
        queryset = queryset.filter(
            Q(created_by=request.user) | 
            Q(project__team_members__user=request.user)
        ).distinct()
    
    # 项目筛选
    if project_id:
        queryset = queryset.filter(project_id=project_id)
    
    # 周期筛选（从标题或描述中提取周期信息）
    if week_number:
        queryset = queryset.filter(
            Q(title__icontains=f'第{week_number}周') |
            Q(title__icontains=f'第{week_number}期') |
            Q(description__icontains=f'第{week_number}周')
        )
    
    # 排序和分页
    queryset = queryset.select_related('project', 'client', 'created_by').defer('client__total_execution_amount').prefetch_related('files').order_by('-created_at')
    paginator = Paginator(queryset, 20)
    page = paginator.get_page(page_num)
    
    # 获取全过程设计咨询项目列表（用于筛选）
    full_process_projects = Project.objects.filter(
        service_type__name='full_process_consulting'
    ).order_by('-created_at')[:50]  # 限制数量
    
    # 统计信息
    total_count = DeliveryRecord.objects.filter(
        Q(title__icontains='每周快报') | Q(title__icontains='周报')
    ).count()
    
    # 添加左侧菜单
    module_sidebar_nav = _build_delivery_sidebar_nav(permission_set, request.path)
    delivery_sidebar_nav = module_sidebar_nav  # 兼容旧模板
    
    return render(request, "delivery_customer/delivery_weekly_report_list.html", {
        "page_title": "每周快报",
        "page_icon": "📰",
        "weekly_reports": page,
        "project_id": project_id,
        "week_number": week_number,
        "full_process_projects": full_process_projects,
        "total_count": total_count,
        "full_top_nav": _build_full_top_nav(permission_set, request.user),
        "module_sidebar_nav": module_sidebar_nav,
        "delivery_sidebar_nav": delivery_sidebar_nav,  # 兼容旧模板
    })


@login_required
def delivery_file_prep_list(request):
    """文件准备列表页"""
    from backend.apps.delivery_customer.models import DeliveryFile, DeliveryRecord
    from backend.apps.production_management.models import Project
    from django.core.paginator import Paginator
    from django.db.models import Q, Count
    
    permission_set = get_user_permission_codes(request.user)
    
    # 权限检查
    if not _permission_granted('delivery_center.view', permission_set):
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("无权限访问文件准备")
    
    # 获取查询参数
    file_type = request.GET.get('file_type', '')
    file_category = request.GET.get('file_category', '')  # project/non_project
    file_status = request.GET.get('file_status', '')  # pending_review/reviewing/approved/rejected/confirmed
    project_id = request.GET.get('project_id', '')
    search_query = request.GET.get('search', '')
    page_num = request.GET.get('page', 1)
    
    # 构建查询
    queryset = DeliveryFile.objects.filter(is_deleted=False).select_related(
        'delivery_record', 'delivery_record__project', 'delivery_record__client', 'uploaded_by'
    )
    
    # 权限过滤
    if not _permission_granted('delivery_center.view_all', permission_set):
        queryset = queryset.filter(
            Q(uploaded_by=request.user) |
            Q(delivery_record__created_by=request.user) |
            Q(delivery_record__project__team_members__user=request.user)
        ).distinct()
    
    # 文件类型筛选
    if file_type:
        queryset = queryset.filter(file_type=file_type)
    
    # 文件分类筛选（项目文件/非项目文件）
    if file_category == 'project':
        queryset = queryset.filter(delivery_record__project__isnull=False)
    elif file_category == 'non_project':
        queryset = queryset.filter(delivery_record__project__isnull=True)
    
    # 文件状态筛选（基于交付记录状态）
    if file_status:
        if file_status == 'pending_review':
            queryset = queryset.filter(delivery_record__status='draft')
        elif file_status == 'reviewing':
            queryset = queryset.filter(delivery_record__status__in=['submitted', 'pending_approval'])
        elif file_status == 'approved':
            queryset = queryset.filter(delivery_record__status='approved')
        elif file_status == 'rejected':
            queryset = queryset.filter(delivery_record__status='rejected')
        elif file_status == 'confirmed':
            queryset = queryset.filter(delivery_record__status='confirmed')
    
    # 项目筛选
    if project_id:
        queryset = queryset.filter(delivery_record__project_id=project_id)
    
    # 搜索
    if search_query:
        queryset = queryset.filter(
            Q(file_name__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(delivery_record__title__icontains=search_query) |
            Q(delivery_record__delivery_number__icontains=search_query)
        )
    
    # 排序和分页
    queryset = queryset.order_by('-uploaded_at')
    paginator = Paginator(queryset, 20)
    page = paginator.get_page(page_num)
    
    # 获取项目列表（用于筛选）
    projects = Project.objects.all().order_by('-created_time')[:50]
    
    # 统计信息
    total_count = DeliveryFile.objects.filter(is_deleted=False).count()
    total_size = sum(f.file_size for f in DeliveryFile.objects.filter(is_deleted=False))
    
    # 添加左侧菜单
    module_sidebar_nav = _build_delivery_sidebar_nav(permission_set, request.path)
    delivery_sidebar_nav = module_sidebar_nav  # 兼容旧模板
    
    return render(request, "delivery_customer/delivery_file_prep_list.html", {
        "page_title": "文件准备",
        "page_icon": "📝",
        "files": page,
        "file_type": file_type,
        "file_category": file_category,
        "file_status": file_status,
        "project_id": project_id,
        "search_query": search_query,
        "projects": projects,
        "total_count": total_count,
        "total_size": total_size,
        "full_top_nav": _build_full_top_nav(permission_set, request.user),
        "module_sidebar_nav": module_sidebar_nav,
        "delivery_sidebar_nav": delivery_sidebar_nav,  # 兼容旧模板
    })


@login_required
def delivery_file_prep_upload(request):
    """文件准备上传页"""
    from backend.apps.delivery_customer.models import DeliveryFile, DeliveryRecord
    from backend.apps.production_management.models import Project
    from django.contrib import messages
    from django.shortcuts import redirect
    from django.utils import timezone
    import os
    
    permission_set = get_user_permission_codes(request.user)
    
    # 权限检查
    if not _permission_granted('delivery_center.create', permission_set):
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("无权限上传文件")
    
    # POST请求：上传文件
    if request.method == 'POST':
        delivery_id = request.POST.get('delivery_id', '').strip()
        file_category = request.POST.get('file_category', 'project')  # project/non_project
        
        # 验证文件
        if 'files' not in request.FILES:
            messages.error(request, '请选择要上传的文件')
            return redirect('delivery_pages:delivery_file_prep_upload')
        
        uploaded_files = request.FILES.getlist('files')
        if not uploaded_files:
            messages.error(request, '请选择要上传的文件')
            return redirect('delivery_pages:delivery_file_prep_upload')
        
        # 如果指定了交付记录，关联到该记录
        delivery = None
        if delivery_id:
            try:
                delivery = DeliveryRecord.objects.get(id=delivery_id)
            except DeliveryRecord.DoesNotExist:
                messages.error(request, '交付记录不存在')
                return redirect('delivery_pages:delivery_file_prep_upload')
        else:
            # 如果没有指定交付记录，创建一个临时交付记录用于文件准备
            # 这种情况下，文件可以在后续创建交付单时关联
            # 暂时不创建，要求用户先选择或创建交付记录
            messages.error(request, '请先选择或创建交付记录')
            return redirect('delivery_pages:delivery_file_prep_upload')
        
        # 上传文件
        success_count = 0
        error_count = 0
        
        for uploaded_file in uploaded_files:
            try:
                # 获取文件信息
                file_name = uploaded_file.name
                file_size = uploaded_file.size
                file_extension = os.path.splitext(file_name)[1][1:].lower()
                
                # 判断文件类型
                file_type = 'other'
                if file_extension in ['pdf', 'doc', 'docx']:
                    file_type = 'document'
                elif file_extension in ['dwg', 'dgn']:
                    file_type = 'drawing'
                elif file_extension in ['jpg', 'jpeg', 'png']:
                    file_type = 'image'
                elif file_extension in ['xls', 'xlsx']:
                    file_type = 'data'
                
                # 创建文件记录
                DeliveryFile.objects.create(
                    delivery_record=delivery,
                    file=uploaded_file,
                    file_name=file_name,
                    file_type=file_type,
                    file_size=file_size,
                    file_extension=file_extension,
                    uploaded_by=request.user,
                )
                success_count += 1
            except Exception as e:
                error_count += 1
                logger.error(f"文件上传失败: {e}")
        
        # 更新交付记录的文件统计
        if delivery:
            delivery.file_count = delivery.files.filter(is_deleted=False).count()
            delivery.total_file_size = sum(f.file_size for f in delivery.files.filter(is_deleted=False))
            delivery.save()
        
        if success_count > 0:
            messages.success(request, f'成功上传 {success_count} 个文件')
        if error_count > 0:
            messages.warning(request, f'{error_count} 个文件上传失败')
        
        return redirect('delivery_pages:delivery_file_prep_list')
    
    # GET请求：显示上传表单
    # 获取可用的交付记录（草稿状态）
    draft_deliveries = DeliveryRecord.objects.filter(
        status='draft',
        created_by=request.user
    ).order_by('-created_at')[:20]
    
    # 获取项目列表
    projects = Project.objects.all().order_by('-created_time')[:50]
    
    # 添加左侧菜单
    module_sidebar_nav = _build_delivery_sidebar_nav(permission_set, request.path)
    delivery_sidebar_nav = module_sidebar_nav  # 兼容旧模板
    
    return render(request, "delivery_customer/delivery_file_prep_upload.html", {
        "page_title": "上传文件",
        "page_icon": "📝",
        "draft_deliveries": draft_deliveries,
        "projects": projects,
        "full_top_nav": _build_full_top_nav(permission_set, request.user),
        "module_sidebar_nav": module_sidebar_nav,
        "delivery_sidebar_nav": delivery_sidebar_nav,  # 兼容旧模板
    })


@login_required
def delivery_weekly_report_create(request):
    """每周快报创建页"""
    from backend.apps.delivery_customer.models import DeliveryRecord, DeliveryTracking
    from backend.apps.production_management.models import Project
    from django.contrib import messages
    from django.shortcuts import redirect
    from django.utils import timezone
    from django.db.models import Q
    from datetime import datetime, timedelta
    
    permission_set = get_user_permission_codes(request.user)
    
    # 权限检查
    if not _permission_granted('delivery_center.create', permission_set):
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("无权限创建每周快报")
    
    # 获取全过程设计咨询项目列表
    full_process_projects = Project.objects.filter(
        service_type__name='full_process_consulting'
    ).order_by('-created_at')
    
    # POST请求：创建每周快报
    if request.method == 'POST':
        project_id = request.POST.get('project_id', '').strip()
        week_number = request.POST.get('week_number', '').strip()
        design_progress = request.POST.get('design_progress', '').strip()
        optimization_suggestions = request.POST.get('optimization_suggestions', '').strip()
        estimated_savings = request.POST.get('estimated_savings', '').strip()
        drawing_issues = request.POST.get('drawing_issues', '').strip()
        cost_trends = request.POST.get('cost_trends', '').strip()
        pending_decisions = request.POST.get('pending_decisions', '').strip()
        risk_alerts = request.POST.get('risk_alerts', '').strip()
        
        # 验证必填字段
        if not project_id:
            messages.error(request, '请选择关联项目')
            return redirect('delivery_pages:delivery_weekly_report_create')
        
        try:
            project = Project.objects.get(id=project_id)
        except Project.DoesNotExist:
            messages.error(request, '项目不存在')
            return redirect('delivery_pages:delivery_weekly_report_create')
        
        if not week_number:
            messages.error(request, '请输入快报周期（第X周）')
            return redirect('delivery_pages:delivery_weekly_report_create')
        
        # 构建快报标题
        report_title = f"《{project.name}》第{week_number}周快报"
        
        # 构建快报内容
        report_content_parts = []
        if design_progress:
            report_content_parts.append(f"【本周设计进度对标】\n{design_progress}\n")
        if optimization_suggestions:
            report_content_parts.append(f"【本周主要优化建议】\n{optimization_suggestions}\n")
        if estimated_savings:
            report_content_parts.append(f"【预估节省金额】\n{estimated_savings}\n")
        if drawing_issues:
            report_content_parts.append(f"【本周发现的图纸问题及重要性分级】\n{drawing_issues}\n")
        if cost_trends:
            report_content_parts.append(f"【累计成本指标变动趋势】\n{cost_trends}\n")
        if pending_decisions:
            report_content_parts.append(f"【待决策事项】\n{pending_decisions}\n")
        if risk_alerts:
            report_content_parts.append(f"【风险提示】\n{risk_alerts}\n")
        
        report_content = "\n".join(report_content_parts)
        
        # 生成交付单号
        from datetime import datetime
        now = timezone.now()
        delivery_number = f"WB-{now.strftime('%Y%m%d')}-{DeliveryRecord.objects.filter(created_at__date=now.date()).count() + 1:04d}"
        
        # 创建交付记录
        delivery = DeliveryRecord.objects.create(
            delivery_number=delivery_number,
            title=report_title,
            description=report_content,
            delivery_method='email',  # 每周快报默认通过邮件发送
            project=project,
            client=project.client if hasattr(project, 'client') else None,
            recipient_name=project.client.name if project.client else '',
            recipient_email=project.client.contact_email if project.client and hasattr(project.client, 'contact_email') else '',
            email_subject=report_title,
            email_message=report_content,
            status='draft',
            created_by=request.user,
        )
        
        # 记录跟踪
        DeliveryTracking.objects.create(
            delivery_record=delivery,
            event_type='submitted',
            event_description=f'创建每周快报：第{week_number}周',
            operator=request.user
        )
        
        messages.success(request, '每周快报创建成功')
        return redirect('delivery_pages:delivery_weekly_report_list')
    
    # GET请求：显示创建表单
    # 计算当前周数（从项目开始时间计算）
    # 这里简化处理，实际应该根据项目开始时间和当前时间计算
    
    # 添加左侧菜单
    module_sidebar_nav = _build_delivery_sidebar_nav(permission_set, request.path)
    delivery_sidebar_nav = module_sidebar_nav  # 兼容旧模板
    
    return render(request, "delivery_customer/delivery_weekly_report_create.html", {
        "page_title": "创建每周快报",
        "page_icon": "📰",
        "full_process_projects": full_process_projects,
        "full_top_nav": _build_full_top_nav(permission_set, request.user),
        "module_sidebar_nav": module_sidebar_nav,
        "delivery_sidebar_nav": delivery_sidebar_nav,  # 兼容旧模板
    })


@login_required
def customer_collaboration(request):
    """客户协同工作台 - 老版本（已注释，待实现）"""
    # ==================== 老版本代码（已注释）====================
    # 客户协同工作台功能待实现，暂时注释掉老版本代码
    # context = _context(
    #     "客户协同工作台",
    #     "🤝",
    #     "与客户及设计方协同处理意见、确认事项与信息同步。",
    #     request=request,
    #     summary_cards=[
    #         {"label": "活跃协同", "value": "0", "hint": "当前有互动的客户协同专题"},
    #         {"label": "待回复事项", "value": "0", "hint": "等待客户或设计方反馈的事项"},
    #         {"label": "协同会议", "value": "0", "hint": "排期中的客户会议数量"},
    #         {"label": "满意度评分", "value": "--", "hint": "客户反馈满意度"},
    #     ],
    #     sections=[
    #         {
    #             "title": "协同功能",
    #             "description": "围绕客户沟通的关键环节进行管理。",
    #             "items": [
    #                 {"label": "协同专题", "description": "为项目创建协同沟通空间。", "url": "#", "icon": "🗂"},
    #                 {"label": "互动记录", "description": "跟踪客户沟通日志。", "url": "#", "icon": "📝"},
    #                 {"label": "待办提醒", "description": "及时处理客户反馈与任务。", "url": "#", "icon": "⏰"},
    #             ],
    #         }
    #     ],
    # )
    # return render(request, "shared/center_dashboard.html", context)
    # ==================== 老版本代码结束 ====================
    
    # 新版本：暂时返回404或跳转到交付记录列表
    from django.http import Http404
    raise Http404("客户协同工作台功能待实现")


@login_required
def customer_portal(request):
    """客户门户管理 - 老版本（已注释，待实现）"""
    # ==================== 老版本代码（已注释）====================
    # 客户门户管理功能待实现，暂时注释掉老版本代码
    # context = _context(
    #     "客户门户管理",
    #     "🌐",
    #     "配置客户门户账号、权限与界面展示，实现成果在线交付与客户自助服务。",
    #     request=request,
    #     summary_cards=[
    #         {"label": "门户用户", "value": "0", "hint": "已开通的客户门户账号数"},
    #         {"label": "活跃用户", "value": "0", "hint": "近 30 天登录的客户数"},
    #         {"label": "权限模板", "value": "0", "hint": "已配置的门户权限组"},
    #         {"label": "界面主题", "value": "0", "hint": "可选门户主题数量"},
    #     ],
    #     sections=[
    #         {
    #             "title": "门户配置",
    #             "description": "在线配置客户门户资源。",
    #             "items": [
    #                 {"label": "账号管理", "description": "新增或停用客户账号。", "url": "#", "icon": "👤"},
    #                 {"label": "权限设置", "description": "维护门户访问权限。", "url": "#", "icon": "🔐"},
    #                 {"label": "界面定制", "description": "调整门户视觉与栏目。", "url": "#", "icon": "🎨"},
    #             ],
    #         }
    #     ],
    # )
    # return render(request, "shared/center_dashboard.html", context)
    # ==================== 老版本代码结束 ====================
    
    # 新版本：暂时返回404或跳转到交付记录列表
    from django.http import Http404
    raise Http404("客户门户管理功能待实现")


@login_required
def electronic_signature(request):
    """电子签章中心 - 老版本（已注释，待实现）"""
    # ==================== 老版本代码（已注释）====================
    # 电子签章中心功能待实现，暂时注释掉老版本代码
    # context = _context(
    #     "电子签章中心",
    #     "🖋",
    #     "统一管理成果确认函、结算确认单等电子签署流程，确保轨迹可追溯。",
    #     request=request,
    #     summary_cards=[
    #         {"label": "待签文件", "value": "0", "hint": "等待签署的电子文档数量"},
    #         {"label": "已完成签章", "value": "0", "hint": "已完成签署并归档的文件"},
    #         {"label": "签署耗时", "value": "--", "hint": "平均签署完成耗时"},
    #         {"label": "异常记录", "value": "0", "hint": "签署失败或撤回的记录"},
    #     ],
    #     sections=[
    #         {
    #             "title": "签章流程",
    #             "description": "发起、追踪并归档电子签章。",
    #             "items": [
    #                 {"label": "发起签署", "description": "上传文档并选择签署方。", "url": "#", "icon": "📨"},
    #                 {"label": "签署进度", "description": "实时查看签章状态。", "url": "#", "icon": "⏳"},
    #                 {"label": "签署归档", "description": "管理签署完成后的文件。", "url": "#", "icon": "🗄"},
    #             ],
    #         }
    #     ],
    # )
    # return render(request, "shared/center_dashboard.html", context)
    # ==================== 老版本代码结束 ====================
    
    # 新版本：暂时返回404或跳转到交付记录列表
    from django.http import Http404
    raise Http404("电子签章中心功能待实现")


# ==================== 收文管理 ====================

@login_required
def incoming_document_home(request):
    """收文管理首页"""
    from django.utils import timezone
    from django.contrib import messages
    from django.shortcuts import redirect
    from django.urls import reverse
    
    permission_codes = get_user_permission_codes(request.user)
    today = timezone.now().date()
    this_month_start = today.replace(day=1)
    
    # 权限检查
    if not _permission_granted('delivery_center.view', permission_codes):
        messages.error(request, '您没有权限访问收文管理')
        return redirect('core:home')
    
    # 收集统计数据
    summary_cards = []
    
    try:
        from backend.apps.delivery_customer.models import IncomingDocument
        total_documents = IncomingDocument.objects.count()
        draft_documents = IncomingDocument.objects.filter(status='draft').count()
        registered_documents = IncomingDocument.objects.filter(status='registered').count()
        processing_documents = IncomingDocument.objects.filter(status='processing').count()
        completed_documents = IncomingDocument.objects.filter(status='completed').count()
        this_month_documents = IncomingDocument.objects.filter(
            created_at__gte=this_month_start
        ).count()
        
        summary_cards.append({
            'label': '收文总数',
            'icon': '📥',
            'value': str(total_documents),
            'subvalue': f'草稿 {draft_documents} 个 · 已登记 {registered_documents} 个 · 处理中 {processing_documents} 个',
            'url': reverse('delivery_pages:incoming_document_list'),
            'variant': 'info'
        })
        
        summary_cards.append({
            'label': '本月新增',
            'icon': '➕',
            'value': str(this_month_documents),
            'subvalue': '本月创建收文',
            'url': reverse('delivery_pages:incoming_document_list'),
            'variant': 'success'
        })
        
        if completed_documents > 0:
            summary_cards.append({
                'label': '已完成',
                'icon': '✅',
                'value': str(completed_documents),
                'subvalue': '已完成收文',
                'url': reverse('delivery_pages:incoming_document_list') + '?status=completed',
                'variant': 'success'
            })
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception('获取统计数据失败: %s', str(e))
    
    # 快捷操作
    quick_actions = []
    
    if _permission_granted('delivery_center.create', permission_codes):
        try:
            quick_actions.append({
                'label': '新建收文',
                'icon': '➕',
                'description': '创建新的收文记录',
                'url': reverse('delivery_pages:incoming_document_create'),
                'link_label': '创建收文 →'
            })
        except Exception:
            pass
    
    # 功能模块入口
    module_entries = []
    
    try:
        module_entries.append({
            'label': '收文列表',
            'icon': '📋',
            'description': '查看和管理所有收文',
            'url': reverse('delivery_pages:incoming_document_list'),
            'link_label': '进入模块 →'
        })
    except Exception:
        pass
    
    # 构建区域
    sections = []
    
    if quick_actions:
        sections.append({
            'title': '快捷操作',
            'description': '常用的快速操作入口',
            'items': quick_actions,
            'layout': 'grid'
        })
    
    if module_entries:
        sections.append({
            'title': '功能模块',
            'description': '收文管理的各个功能模块入口',
            'items': module_entries,
            'layout': 'grid'
        })
    
    # 构建上下文
    context = _context(
        page_title="收文管理",
        page_icon="📥",
        description="管理所有收文记录、状态和处理流程",
        summary_cards=summary_cards,
        sections=sections,
        request=request,
        active_menu_id='incoming_document_home',
    )
    
    return render(request, "delivery_customer/home.html", context)


@login_required
def incoming_document_list(request):
    """收文列表"""
    from django.core.paginator import Paginator
    from django.db.models import Q
    from backend.apps.delivery_customer.models import IncomingDocument, FileCategory
    
    permission_set = get_user_permission_codes(request.user)
    module_sidebar_nav = _build_delivery_sidebar_nav(permission_set, request.path)
    
    # 获取查询参数
    search_query = request.GET.get('search', '').strip()
    status_filter = request.GET.get('status', 'all')
    priority_filter = request.GET.get('priority', 'all')
    stage_filter = request.GET.get('stage', 'all')
    category_filter = request.GET.get('category', 'all')
    
    # 转换page参数为整数
    try:
        page = int(request.GET.get('page', 1))
    except (ValueError, TypeError):
        page = 1
    
    # 查询收文
    documents = IncomingDocument.objects.all()
    
    # 搜索过滤
    if search_query:
        documents = documents.filter(
            Q(document_number__icontains=search_query) |
            Q(title__icontains=search_query) |
            Q(sender__icontains=search_query) |
            Q(sender_contact__icontains=search_query)
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
        documents = documents.filter(file_category_id=category_filter)
    
    # 排序（按创建时间倒序）
    documents = documents.order_by('-created_at')
    
    # 分页 - 固定每页最多10行
    per_page = 10
    paginator = Paginator(documents, per_page)
    try:
        page_obj = paginator.page(page)
    except:
        page_obj = paginator.page(1)
    
    # 获取文件分类数据
    categories = FileCategory.objects.filter(is_active=True).order_by('stage', 'sort_order', 'name')
    categories_by_stage = {}
    for category in categories:
        if category.stage not in categories_by_stage:
            categories_by_stage[category.stage] = []
        categories_by_stage[category.stage].append(category)
    
    # 构建筛选配置
    # 构建文件分类选项（包含所有分类，前端会通过依赖关系过滤）
    category_options = [{'value': 'all', 'label': '全部'}]
    for category in categories:
        category_options.append({
            'value': str(category.id),
            'label': category.name,
            'data-stage': category.stage  # 用于前端依赖过滤
        })
    
    filter_config = {
        'id': 'incomingDocumentFilter',
        'method': 'form',
        'form_action': request.path,
        'auto_submit': False,  # 列表页关闭自动提交
        'collapsible': True,
        'default_collapsed': False,
        'show_filter_tags': True,  # 显示筛选标签
        'enable_field_settings': True,  # 启用筛选字段设置功能
        'max_enabled_fields': 10,  # 最多可启用的字段数
        'default_enabled_fields': ['status', 'priority', 'stage', 'category'],  # 默认启用的字段
        'required_fields': [],  # 必填字段（不可隐藏）
        'enable_presets': False,  # 可选：启用预设功能
        'enable_history': False,  # 可选：启用历史功能
        'filters': [
            {
                'key': 'status',
                'label': '状态',
                'type': 'select',
                'options': [{'value': 'all', 'label': '全部'}] + [
                    {'value': code, 'label': label}
                    for code, label in IncomingDocument.STATUS_CHOICES
                ],
                'default': status_filter
            },
            {
                'key': 'priority',
                'label': '优先级',
                'type': 'select',
                'options': [{'value': 'all', 'label': '全部'}] + [
                    {'value': code, 'label': label}
                    for code, label in IncomingDocument.PRIORITY_CHOICES
                ],
                'default': priority_filter
            },
            {
                'key': 'stage',
                'label': '阶段',
                'type': 'select',
                'options': [{'value': 'all', 'label': '全部'}] + [
                    {'value': code, 'label': label}
                    for code, label in IncomingDocument.STAGE_CHOICES
                ],
                'default': stage_filter
            },
            {
                'key': 'category',
                'label': '文件分类',
                'type': 'select',
                'options': category_options,
                'default': category_filter,
                'depends_on': 'stage',  # 依赖于阶段字段
                'depends_value': '*'  # 当阶段变化时，需要更新选项
            }
        ]
    }
    
    context = _context(
        "收文列表",
        "📥",
        "管理收到的文件记录",
        request=request,
    )
    context.update({
        "module_sidebar_nav": module_sidebar_nav,
        "delivery_sidebar_nav": module_sidebar_nav,
        "page_obj": page_obj,
        "search": search_query,
        "search_query": search_query,
        "filter_config": filter_config,  # 新增筛选配置
        # 保留旧字段用于向后兼容（如果需要）
        "status_filter": status_filter,
        "priority_filter": priority_filter,
        "stage_filter": stage_filter,
        "category_filter": category_filter,
        "status_choices": IncomingDocument.STATUS_CHOICES,
        "priority_choices": IncomingDocument.PRIORITY_CHOICES,
        "stage_choices": IncomingDocument.STAGE_CHOICES,
        "categories": categories,
        "categories_by_stage": categories_by_stage,
        "can_create": _permission_granted('delivery_center.create', permission_set),
    })
    return render(request, "delivery_customer/incoming_document_list.html", context)


@login_required
def incoming_document_create(request):
    """收文创建"""
    from django.shortcuts import redirect
    from django.contrib import messages
    from django.utils import timezone
    from backend.apps.delivery_customer.models import IncomingDocument
    import uuid
    
    permission_set = get_user_permission_codes(request.user)
    module_sidebar_nav = _build_delivery_sidebar_nav(permission_set, request.path)
    delivery_sidebar_nav = module_sidebar_nav  # 兼容旧模板
    
    if not _permission_granted('delivery_center.create', permission_set):
        messages.error(request, '您没有创建收文的权限')
        return redirect('delivery_pages:incoming_document_list')
    
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
            
            # 判断是保存草稿还是提交审批
            action = request.POST.get('action', '')
            if action == 'submit':
                # 提交审批：状态设为已登记
                status = 'registered'
                success_message = f'收文"{request.POST.get("title", "").strip()}"已提交审批'
            else:
                # 保存草稿：状态设为草稿
                status = 'draft'
                success_message = f'收文"{request.POST.get("title", "").strip()}"已保存为草稿'
            
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
                status=status,
                priority=request.POST.get('priority', 'normal'),
                stage=stage,
                file_category_id=file_category_id,
                handler_id=request.POST.get('handler') or None,
                handle_notes=request.POST.get('handle_notes', '').strip(),
                notes=request.POST.get('notes', '').strip(),
                created_by=request.user,
            )
            
            # 处理附件（支持多文件上传）
            attachment_files = request.FILES.getlist('attachment')
            if attachment_files:
                # 保存第一个附件
                document.attachment = attachment_files[0]
                # 如果有多个附件，将其他附件信息记录到notes中
                if len(attachment_files) > 1:
                    additional_files_info = "\n【其他附件】\n"
                    for idx, additional_file in enumerate(attachment_files[1:], start=2):
                        additional_files_info += f"{idx}. {additional_file.name} ({additional_file.size} 字节)\n"
                    # 将其他附件信息追加到notes
                    if document.notes:
                        document.notes += "\n\n" + additional_files_info
                    else:
                        document.notes = additional_files_info
            
            document.save()
            messages.success(request, success_message)
            return redirect('delivery_pages:incoming_document_detail', document_id=document.id)
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
    from backend.apps.delivery_customer.models import FileCategory
    categories = FileCategory.objects.filter(is_active=True).order_by('stage', 'sort_order', 'name')
    categories_by_stage = {}
    for category in categories:
        if category.stage not in categories_by_stage:
            categories_by_stage[category.stage] = []
        categories_by_stage[category.stage].append(category)
    
    context["module_sidebar_nav"] = module_sidebar_nav
    context["delivery_sidebar_nav"] = module_sidebar_nav  # 兼容旧模板
    context["status_choices"] = IncomingDocument.STATUS_CHOICES
    context["priority_choices"] = IncomingDocument.PRIORITY_CHOICES
    context["stage_choices"] = IncomingDocument.STAGE_CHOICES
    context["categories"] = categories
    context["categories_by_stage"] = categories_by_stage
    context["users"] = users
    return render(request, "delivery_customer/incoming_document_create.html", context)


@login_required
def incoming_document_detail(request, document_id):
    """收文详情"""
    from django.shortcuts import get_object_or_404
    from backend.apps.delivery_customer.models import IncomingDocument
    
    permission_set = get_user_permission_codes(request.user)
    module_sidebar_nav = _build_delivery_sidebar_nav(permission_set, request.path)
    delivery_sidebar_nav = module_sidebar_nav  # 兼容旧模板
    
    document = get_object_or_404(IncomingDocument, id=document_id)
    
    context = _context(
        "收文详情",
        "📥",
        "查看收文详细信息",
        request=request,
    )
    context["module_sidebar_nav"] = module_sidebar_nav
    context["delivery_sidebar_nav"] = module_sidebar_nav  # 兼容旧模板
    context["document"] = document
    context["can_edit"] = _permission_granted('delivery_center.create', permission_set)
    return render(request, "delivery_customer/incoming_document_detail.html", context)


@login_required
def incoming_document_edit(request, document_id):
    """收文编辑"""
    from django.shortcuts import redirect, get_object_or_404
    from django.contrib import messages
    from backend.apps.delivery_customer.models import IncomingDocument
    
    permission_set = get_user_permission_codes(request.user)
    module_sidebar_nav = _build_delivery_sidebar_nav(permission_set, request.path)
    delivery_sidebar_nav = module_sidebar_nav  # 兼容旧模板
    
    if not _permission_granted('delivery_center.create', permission_set):
        messages.error(request, '您没有编辑收文的权限')
        return redirect('delivery_pages:incoming_document_list')
    
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
            return redirect('delivery_pages:incoming_document_detail', document_id=document.id)
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
    from backend.apps.delivery_customer.models import FileCategory
    categories = FileCategory.objects.filter(is_active=True).order_by('stage', 'sort_order', 'name')
    categories_by_stage = {}
    for category in categories:
        if category.stage not in categories_by_stage:
            categories_by_stage[category.stage] = []
        categories_by_stage[category.stage].append(category)
    
    context["module_sidebar_nav"] = module_sidebar_nav
    context["delivery_sidebar_nav"] = module_sidebar_nav  # 兼容旧模板
    context["document"] = document
    context["status_choices"] = IncomingDocument.STATUS_CHOICES
    context["priority_choices"] = IncomingDocument.PRIORITY_CHOICES
    context["stage_choices"] = IncomingDocument.STAGE_CHOICES
    context["categories"] = categories
    context["categories_by_stage"] = categories_by_stage
    context["users"] = users
    return render(request, "delivery_customer/incoming_document_edit.html", context)


@login_required
def incoming_document_delete(request, document_id):
    """收文删除"""
    from django.shortcuts import redirect, get_object_or_404
    from django.contrib import messages
    from backend.apps.delivery_customer.models import IncomingDocument
    
    permission_set = get_user_permission_codes(request.user)
    
    if not _permission_granted('delivery_center.create', permission_set):
        messages.error(request, '您没有删除收文的权限')
        return redirect('delivery_pages:incoming_document_list')
    
    document = get_object_or_404(IncomingDocument, id=document_id)
    
    # 只有草稿状态可以删除
    if document.status != 'draft':
        messages.error(request, '只能删除草稿状态的收文')
        return redirect('delivery_pages:incoming_document_detail', document_id=document_id)
    
    if request.method == 'POST':
        document_number = document.document_number
        document.delete()
        messages.success(request, f'收文 {document_number} 已删除')
        return redirect('delivery_pages:incoming_document_list')
    
    # GET 请求直接删除（使用confirm确认）
    document_number = document.document_number
    document.delete()
    messages.success(request, f'收文 {document_number} 已删除')
    return redirect('delivery_pages:incoming_document_list')


# ==================== 发文管理 ====================

@login_required
def outgoing_document_home(request):
    """发文管理首页"""
    from django.utils import timezone
    from django.contrib import messages
    from django.shortcuts import redirect
    from django.urls import reverse
    
    permission_codes = get_user_permission_codes(request.user)
    today = timezone.now().date()
    this_month_start = today.replace(day=1)
    
    # 权限检查
    if not _permission_granted('delivery_center.view', permission_codes):
        messages.error(request, '您没有权限访问发文管理')
        return redirect('delivery_pages:delivery_customer_home')
    
    # 收集统计数据
    summary_cards = []
    
    try:
        from backend.apps.delivery_customer.models import OutgoingDocument
        total_documents = OutgoingDocument.objects.count()
        draft_documents = OutgoingDocument.objects.filter(status='draft').count()
        reviewing_documents = OutgoingDocument.objects.filter(status='reviewing').count()
        sent_documents = OutgoingDocument.objects.filter(status='sent').count()
        completed_documents = OutgoingDocument.objects.filter(status='completed').count()
        this_month_documents = OutgoingDocument.objects.filter(
            created_at__gte=this_month_start
        ).count()
        
        summary_cards.append({
            'label': '发文总数',
            'icon': '📤',
            'value': str(total_documents),
            'subvalue': f'草稿 {draft_documents} 个 · 审核中 {reviewing_documents} 个 · 已发送 {sent_documents} 个',
            'url': reverse('delivery_pages:outgoing_document_list'),
            'variant': 'info'
        })
        
        summary_cards.append({
            'label': '本月新增',
            'icon': '➕',
            'value': str(this_month_documents),
            'subvalue': '本月创建发文',
            'url': reverse('delivery_pages:outgoing_document_list'),
            'variant': 'success'
        })
        
        if completed_documents > 0:
            summary_cards.append({
                'label': '已完成',
                'icon': '✅',
                'value': str(completed_documents),
                'subvalue': '已完成发文',
                'url': reverse('delivery_pages:outgoing_document_list') + '?status=completed',
                'variant': 'success'
            })
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception('获取统计数据失败: %s', str(e))
    
    # 快捷操作
    quick_actions = []
    
    if _permission_granted('delivery_center.create', permission_codes):
        try:
            quick_actions.append({
                'label': '新建发文',
                'icon': '➕',
                'description': '创建新的发文记录',
                'url': reverse('delivery_pages:outgoing_document_create'),
                'link_label': '创建发文 →'
            })
        except Exception:
            pass
    
    # 功能模块入口
    module_entries = []
    
    try:
        module_entries.append({
            'label': '发文列表',
            'icon': '📋',
            'description': '查看和管理所有发文',
            'url': reverse('delivery_pages:outgoing_document_list'),
            'link_label': '进入模块 →'
        })
        
        if _permission_granted('delivery_center.view', permission_codes):
            module_entries.append({
                'label': '签收确认',
                'icon': '✅',
                'description': '管理发文签收确认',
                'url': reverse('delivery_pages:outgoing_document_receipt_list'),
                'link_label': '进入模块 →'
            })
            
            module_entries.append({
                'label': '效能报告',
                'icon': '📊',
                'description': '查看发文效能报告',
                'url': reverse('delivery_pages:outgoing_document_performance_report'),
                'link_label': '进入模块 →'
            })
            
    except Exception:
        pass
    
    # 构建区域
    sections = []
    
    if quick_actions:
        sections.append({
            'title': '快捷操作',
            'description': '常用的快速操作入口',
            'items': quick_actions,
            'layout': 'grid'
        })
    
    if module_entries:
        sections.append({
            'title': '功能模块',
            'description': '发文管理的各个功能模块入口',
            'items': module_entries,
            'layout': 'grid'
        })
    
    # 构建上下文
    context = _context(
        page_title="发文管理",
        page_icon="📤",
        description="管理所有发文记录、状态和审批流程",
        summary_cards=summary_cards,
        sections=sections,
        request=request,
        active_menu_id='outgoing_document_home',
    )
    
    return render(request, "delivery_customer/home.html", context)


@login_required
def outgoing_document_list(request):
    """发文列表"""
    from django.core.paginator import Paginator
    from django.db.models import Q
    from backend.apps.delivery_customer.models import OutgoingDocument, FileCategory
    
    permission_set = get_user_permission_codes(request.user)
    module_sidebar_nav = _build_delivery_sidebar_nav(permission_set, request.path)
    
    # 获取查询参数
    search_query = request.GET.get('search', '').strip()
    status_filter = request.GET.get('status', 'all')
    priority_filter = request.GET.get('priority', 'all')
    stage_filter = request.GET.get('stage', 'all')
    category_filter = request.GET.get('category', 'all')
    
    # 转换page参数为整数
    try:
        page = int(request.GET.get('page', 1))
    except (ValueError, TypeError):
        page = 1
    
    # 查询发文：显示所有状态的发文（不排除任何状态）
    # 发文列表：显示所有状态的发文，包括草稿、审核中、已批准、已发送、已完成、已归档等
    documents = OutgoingDocument.objects.select_related(
        'created_by', 'reviewer', 'file_category', 'project', 'client'
    )
    
    # 搜索过滤
    if search_query:
        documents = documents.filter(
            Q(document_number__icontains=search_query) |
            Q(title__icontains=search_query) |
            Q(recipient__icontains=search_query) |
            Q(recipient_contact__icontains=search_query) |
            Q(created_by__username__icontains=search_query) |
            Q(created_by__first_name__icontains=search_query) |
            Q(created_by__last_name__icontains=search_query)
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
        documents = documents.filter(file_category_id=category_filter)
    
    # 排序（按创建时间倒序）
    documents = documents.order_by('-created_at')
    
    # 分页 - 固定每页最多10行
    per_page = 10
    paginator = Paginator(documents, per_page)
    try:
        page_obj = paginator.page(page)
    except:
        page_obj = paginator.page(1)
    
    # 获取文件分类数据
    categories = FileCategory.objects.filter(is_active=True).order_by('stage', 'sort_order', 'name')
    categories_by_stage = {}
    for category in categories:
        if category.stage not in categories_by_stage:
            categories_by_stage[category.stage] = []
        categories_by_stage[category.stage].append(category)
    
    # 获取报送方式映射（用于显示报送方式名称）
    from backend.apps.delivery_customer.models import DeliveryMethod
    delivery_methods = DeliveryMethod.objects.filter(is_active=True)
    delivery_methods_map = {method.code: method.name for method in delivery_methods}
    
    # 为每个文档查询当前待审批的人员（审核人）
    from django.contrib.contenttypes.models import ContentType
    from backend.apps.workflow_engine.models import ApprovalInstance, ApprovalRecord
    
    content_type = ContentType.objects.get_for_model(OutgoingDocument)
    document_ids = [doc.id for doc in page_obj]
    
    # 查询审批实例（查询所有状态的审批实例，用于跳转链接）
    approval_instances = ApprovalInstance.objects.filter(
        content_type=content_type,
        object_id__in=document_ids
    ).select_related('current_node').prefetch_related('records__approver')
    
    # 构建文档ID到审批实例的映射
    approval_map = {}
    for instance in approval_instances:
        approval_map[instance.object_id] = instance
    
    # 为每个文档查询当前待审批的人员，并附加到文档对象上
    # 同时处理报送方式显示
    for doc in page_obj:
        doc.current_approvers = []
        doc.approval_instance_id = None  # 审批实例ID，用于跳转链接
        if doc.id in approval_map:
            instance = approval_map[doc.id]
            doc.approval_instance_id = instance.id  # 保存审批实例ID
            if instance.current_node and instance.status == 'pending':
                # 查询当前节点的待审批记录
                pending_records = ApprovalRecord.objects.filter(
                    instance=instance,
                    node=instance.current_node,
                    result='pending'
                ).select_related('approver')
                
                # 获取审批人列表（去重）
                approver_ids = set()
                for record in pending_records:
                    if record.approver.id not in approver_ids:
                        doc.current_approvers.append(record.approver)
                        approver_ids.add(record.approver.id)
        
        # 处理报送方式显示（将逗号分隔的代码转换为名称列表）
        doc.delivery_methods_display = []
        if doc.delivery_methods:
            method_codes = [code.strip() for code in doc.delivery_methods.split(',') if code.strip()]
            for code in method_codes:
                method_name = delivery_methods_map.get(code, code)
                doc.delivery_methods_display.append(method_name)
    
    # 构建筛选配置
    # 构建文件分类选项（包含所有分类，前端会通过依赖关系过滤）
    category_options = [{'value': 'all', 'label': '全部'}]
    for category in categories:
        category_options.append({
            'value': str(category.id),
            'label': category.name,
            'data-stage': category.stage  # 用于前端依赖过滤
        })
    
    filter_config = {
        'id': 'outgoingDocumentFilter',
        'method': 'form',
        'form_action': request.path,
        'auto_submit': False,  # 列表页关闭自动提交
        'collapsible': True,
        'default_collapsed': False,
        'show_filter_tags': True,  # 显示筛选标签
        'enable_field_settings': True,  # 启用筛选字段设置功能
        'max_enabled_fields': 10,  # 最多可启用的字段数
        'default_enabled_fields': ['status', 'priority', 'stage', 'category'],  # 默认启用的字段
        'required_fields': [],  # 必填字段（不可隐藏）
        'enable_presets': False,  # 可选：启用预设功能
        'enable_history': False,  # 可选：启用历史功能
        'filters': [
            {
                'key': 'status',
                'label': '状态',
                'type': 'select',
                'options': [{'value': 'all', 'label': '全部'}] + [
                    {'value': code, 'label': label}
                    for code, label in OutgoingDocument.STATUS_CHOICES
                ],
                'default': status_filter
            },
            {
                'key': 'priority',
                'label': '优先级',
                'type': 'select',
                'options': [{'value': 'all', 'label': '全部'}] + [
                    {'value': code, 'label': label}
                    for code, label in OutgoingDocument.PRIORITY_CHOICES
                ],
                'default': priority_filter
            },
            {
                'key': 'stage',
                'label': '阶段',
                'type': 'select',
                'options': [{'value': 'all', 'label': '全部'}] + [
                    {'value': code, 'label': label}
                    for code, label in OutgoingDocument.STAGE_CHOICES
                ],
                'default': stage_filter
            },
            {
                'key': 'category',
                'label': '文件分类',
                'type': 'select',
                'options': category_options,
                'default': category_filter,
                'depends_on': 'stage',  # 依赖于阶段字段
                'depends_value': '*'  # 当阶段变化时，需要更新选项
            }
        ]
    }
    
    context = _context(
        "发文列表",
        "📤",
        "管理发文记录（发出前的信息）",
        request=request,
    )
    context.update({
        "module_sidebar_nav": module_sidebar_nav,
        "delivery_sidebar_nav": module_sidebar_nav,
        "page_obj": page_obj,
        "search": search_query,
        "search_query": search_query,
        "filter_config": filter_config,  # 新增筛选配置
        # 保留旧字段用于向后兼容（如果需要）
        "status_filter": status_filter,
        "priority_filter": priority_filter,
        "stage_filter": stage_filter,
        "category_filter": category_filter,
        "status_choices": OutgoingDocument.STATUS_CHOICES,
        "priority_choices": OutgoingDocument.PRIORITY_CHOICES,
        "stage_choices": OutgoingDocument.STAGE_CHOICES,
        "categories": categories,
        "categories_by_stage": categories_by_stage,
        "delivery_methods_map": delivery_methods_map,
        "can_create": _permission_granted('delivery_center.create', permission_set),
        "show_batch_import": _permission_granted('delivery_center.create', permission_set),
    })
    return render(request, "delivery_customer/outgoing_document_list.html", context)


@login_required
def outgoing_document_create(request):
    """发文创建"""
    from django.shortcuts import redirect
    from django.contrib import messages
    from django.utils import timezone
    from backend.apps.delivery_customer.models import OutgoingDocument
    
    permission_set = get_user_permission_codes(request.user)
    module_sidebar_nav = _build_delivery_sidebar_nav(permission_set, request.path)
    delivery_sidebar_nav = module_sidebar_nav  # 兼容旧模板
    
    if not _permission_granted('delivery_center.create', permission_set):
        messages.error(request, '您没有创建发文的权限')
        return redirect('delivery_pages:outgoing_document_list')
    
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
            
            # 判断是保存草稿还是提交审批
            action = request.POST.get('action', '')
            submit_for_approval = (action == 'submit')
            
            # 获取报送方式列表
            delivery_methods_list = request.POST.getlist('delivery_methods')
            
            if not delivery_methods_list:
                messages.error(request, '请至少选择一种报送方式')
                return redirect('delivery_pages:outgoing_document_create')
            
            # 解析收件人列表（从JSON中获取）
            import json
            email_recipients_json = request.POST.get('email_recipients_json', '').strip()
            express_recipients_json = request.POST.get('express_recipients_json', '').strip()
            hand_delivery_recipients_json = request.POST.get('hand_delivery_recipients_json', '').strip()
            sms_recipients_json = request.POST.get('sms_recipients_json', '').strip()
            
            # 解析收件人JSON数据
            email_recipients = []
            express_recipients = []
            hand_delivery_recipients = []
            sms_recipients = []
            
            if email_recipients_json:
                try:
                    email_recipients = json.loads(email_recipients_json)
                    if not isinstance(email_recipients, list):
                        email_recipients = []
                except json.JSONDecodeError:
                    email_recipients = []
            
            if express_recipients_json:
                try:
                    express_recipients = json.loads(express_recipients_json)
                    if not isinstance(express_recipients, list):
                        express_recipients = []
                except json.JSONDecodeError:
                    express_recipients = []
            
            if hand_delivery_recipients_json:
                try:
                    hand_delivery_recipients = json.loads(hand_delivery_recipients_json)
                    if not isinstance(hand_delivery_recipients, list):
                        hand_delivery_recipients = []
                except json.JSONDecodeError:
                    hand_delivery_recipients = []
            
            if sms_recipients_json:
                try:
                    sms_recipients = json.loads(sms_recipients_json)
                    if not isinstance(sms_recipients, list):
                        sms_recipients = []
                except json.JSONDecodeError:
                    sms_recipients = []
            
            # 获取收文单位（用于所有发文记录）
            recipient_unit = request.POST.get('recipient', '').strip()
            if not recipient_unit and client_id:
                from backend.apps.customer_management.models import Client
                try:
                    client = Client.objects.get(id=client_id)
                    recipient_unit = client.name or ''
                except Client.DoesNotExist:
                    pass
            
            # 获取其他公共信息
            title = request.POST.get('title', '').strip()
            document_date = request.POST.get('document_date') or None
            document_type = request.POST.get('document_type', '').strip()
            send_date = request.POST.get('send_date') or None
            content = request.POST.get('content', '').strip()
            summary = request.POST.get('summary', '').strip()
            priority = request.POST.get('priority', 'normal')
            notes = request.POST.get('notes', '').strip()
            project_id = request.POST.get('project') or None
            
            # 获取报送方式特定的配置信息
            email_subject = request.POST.get('email_subject', '').strip()
            express_company = request.POST.get('express_company', '').strip()
            express_number = request.POST.get('express_number', '').strip()
            express_fee = request.POST.get('express_fee', '').strip()
            hand_delivery_location = request.POST.get('hand_delivery_location', '').strip()
            hand_delivery_latitude = request.POST.get('hand_delivery_latitude', '').strip()
            hand_delivery_longitude = request.POST.get('hand_delivery_longitude', '').strip()
            hand_delivery_notes = request.POST.get('hand_delivery_notes', '').strip()
            sms_content = request.POST.get('sms_content', '').strip()
            
            # 处理附件（支持多文件上传，必填）
            attachment_files = request.FILES.getlist('attachment')
            if not attachment_files:
                messages.error(request, '请至少上传一个附件')
                return redirect('delivery_pages:outgoing_document_create')
            
            # 验证文件数量和大小
            import os
            MAX_FILES = 10
            MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
            MAX_TOTAL_SIZE = 50 * 1024 * 1024  # 50MB
            ALLOWED_EXTENSIONS = ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
                                '.jpg', '.jpeg', '.png', '.gif', '.txt', '.dwg', '.dgn',
                                '.zip', '.rar', '.7z']
            
            # 验证文件数量
            if len(attachment_files) > MAX_FILES:
                messages.error(request, f'最多只能上传{MAX_FILES}个文件，当前选择了{len(attachment_files)}个文件。')
                return redirect('delivery_pages:outgoing_document_create')
            
            # 验证每个文件
            total_size = 0
            invalid_files = []
            for file in attachment_files:
                total_size += file.size
                
                # 验证文件大小
                if file.size > MAX_FILE_SIZE:
                    size_mb = MAX_FILE_SIZE / 1024 / 1024
                    invalid_files.append(f'{file.name}（文件太大，不能超过{size_mb:.0f}MB）')
                    continue
                
                # 验证文件扩展名
                file_ext = os.path.splitext(file.name)[1].lower()
                if file_ext not in ALLOWED_EXTENSIONS:
                    invalid_files.append(f'{file.name}（不支持的文件类型）')
                    continue
            
            # 验证总大小
            if total_size > MAX_TOTAL_SIZE:
                total_size_mb = MAX_TOTAL_SIZE / 1024 / 1024
                messages.error(request, f'所有文件总大小不能超过{total_size_mb:.0f}MB。')
                return redirect('delivery_pages:outgoing_document_create')
            
            # 如果有无效文件，显示错误
            if invalid_files:
                messages.error(request, '以下文件不符合要求：\n' + '\n'.join(invalid_files))
                return redirect('delivery_pages:outgoing_document_create')
            
            # 第一个附件保存到attachment字段，其他附件信息记录到notes中
            attachment_file = attachment_files[0]  # 第一个附件
            additional_attachments = attachment_files[1:] if len(attachment_files) > 1 else []  # 其他附件
            
            # 为每个（收件人，报送方式）组合创建独立的发文记录
            from backend.apps.delivery_customer.models import OutgoingDocumentTracking, DeliveryMethod
            created_documents = []
            
            for method_code in delivery_methods_list:
                method_code = method_code.strip()
                if not method_code:
                    continue
                
                # 获取该报送方式的收件人列表
                recipients = []
                if method_code == 'email':
                    recipients = email_recipients
                elif method_code == 'express':
                    recipients = express_recipients
                elif method_code == 'hand_delivery':
                    recipients = hand_delivery_recipients
                elif method_code == 'sms':
                    recipients = sms_recipients
                
                # 如果没有收件人，跳过该报送方式
                if not recipients:
                    logger.warning(f"报送方式 {method_code} 没有收件人，跳过创建")
                    continue
                
                # 获取DeliveryMethod对象
                delivery_method = DeliveryMethod.objects.filter(code=method_code, is_active=True).first()
                if not delivery_method:
                    logger.warning(f"报送方式 {method_code} 不存在或已禁用，跳过创建")
                    continue
                
                # 为每个收件人创建独立的发文记录
                for recipient_data in recipients:
                    try:
                        # 提取收件人信息
                        recipient_name = recipient_data.get('name', '').strip()
                        recipient_phone = recipient_data.get('phone', '').strip()
                        recipient_email = recipient_data.get('email', '').strip()
                        recipient_address = recipient_data.get('address', '').strip()
                        
                        # 如果没有姓名，跳过
                        if not recipient_name:
                            continue
                        
                        # 生成独立的发文编号
                        count = OutgoingDocument.objects.filter(
                            document_number__startswith=f'FW{year}'
                        ).count() + 1
                        new_document_number = f'FW{year}{count:04d}'
                        
                        # 确保编号唯一
                        while OutgoingDocument.objects.filter(document_number=new_document_number).exists():
                            count += 1
                            new_document_number = f'FW{year}{count:04d}'
                        
                        # 创建独立的发文记录（每个记录只有一个报送方式）
                        document = OutgoingDocument(
                            document_number=new_document_number,
                            title=title,
                            recipient=recipient_unit,  # 收文单位
                            recipient_contact=recipient_name,  # 收件人姓名
                            recipient_phone=recipient_phone,
                            recipient_email=recipient_email,
                            recipient_address=recipient_address,
                            document_date=document_date,
                            document_type=document_type,
                            send_date=send_date,
                            content=content,
                            summary=summary,
                            status='draft',  # 初始状态为草稿
                            priority=priority,
                            stage=stage,
                            file_category_id=file_category_id,
                            project_id=project_id,
                            client_id=client_id,
                            client_contact_id=client_contact_id,
                            delivery_methods=method_code,  # 只有一个报送方式
                            notes=notes,
                            created_by=request.user,
                            responsible_person=request.user,
                        )
                        
                        # 如果是快递方式，保存快递信息
                        if method_code == 'express':
                            document.express_company = express_company
                            document.express_number = express_number
                        
                        # 处理附件（每个发文记录都保存第一个附件）
                        if attachment_file:
                            # 为每个发文记录保存第一个附件
                            # Django的FileField在保存时会根据upload_to路径保存文件
                            # 每个记录会有独立的文件副本
                            document.attachment = attachment_file
                            
                            # 如果有多个附件，将其他附件信息记录到notes中
                            if additional_attachments:
                                additional_files_info = "\n【其他附件】\n"
                                for idx, additional_file in enumerate(additional_attachments, start=2):
                                    additional_files_info += f"{idx}. {additional_file.name} ({additional_file.size} 字节)\n"
                                # 将其他附件信息追加到notes
                                if document.notes:
                                    document.notes += "\n\n" + additional_files_info
                                else:
                                    document.notes = additional_files_info
                        
                        # 保存发文记录
                        document.save()
                        created_documents.append(document)
                        
                        # 为该发文记录创建唯一的跟踪记录（一对一关系）
                        # 注意：必须设置所有NOT NULL字段，即使是空字符串或默认值
                        tracking_defaults = {
                            'status': 'pending',
                            'created_by': request.user,
                            # 邮件相关字段（NOT NULL，即使不用也要设置）
                            'email_subject': '',
                            'email_to': '',
                            'email_tracking_id': '',
                            'email_message_id': '',
                            # 快递相关字段（NOT NULL，即使不用也要设置）
                            'express_company': '',
                            'express_number': '',
                            'express_status': '',
                            'express_reject_reason': '',
                            'express_reject_detail': '',
                            'express_tracking_data': {},
                            # 现场送达相关字段（NOT NULL，即使不用也要设置）
                            'hand_delivery_location': '',
                            # 易签宝相关字段（NOT NULL，即使不用也要设置）
                            'yisign_contract_id': '',
                            'yisign_contract_url': '',
                            'yisign_status': '',
                            'yisign_signed_by': '',
                            'yisign_callback_data': {},
                            # 短信相关字段（NOT NULL，即使不用也要设置）
                            'sms_phone': '',
                            'sms_content': '',
                            'sms_status': '',
                            'sms_message_id': '',
                            'sms_callback_data': {},
                            # 其他必需字段
                            'notes': '',
                            'error_message': '',
                            'retry_count': 0,
                        }
                        
                        # 根据报送方式设置跟踪记录的特定字段
                        if method_code == 'email':
                            if email_subject:
                                tracking_defaults['email_subject'] = email_subject
                            if recipient_email:
                                tracking_defaults['email_to'] = recipient_email
                        
                        elif method_code == 'express':
                            if express_company:
                                tracking_defaults['express_company'] = express_company
                            if express_number:
                                tracking_defaults['express_number'] = express_number
                            if express_fee:
                                try:
                                    tracking_defaults['express_fee'] = float(express_fee)
                                except ValueError:
                                    pass
                        
                        elif method_code == 'hand_delivery':
                            if hand_delivery_location:
                                tracking_defaults['hand_delivery_location'] = hand_delivery_location
                            if hand_delivery_latitude:
                                try:
                                    tracking_defaults['hand_delivery_latitude'] = float(hand_delivery_latitude)
                                except ValueError:
                                    pass
                            if hand_delivery_longitude:
                                try:
                                    tracking_defaults['hand_delivery_longitude'] = float(hand_delivery_longitude)
                                except ValueError:
                                    pass
                            if hand_delivery_notes:
                                tracking_defaults['notes'] = hand_delivery_notes
                        
                        elif method_code == 'sms':
                            # 短信方式：保存手机号和短信内容
                            if recipient_phone:
                                tracking_defaults['sms_phone'] = recipient_phone
                            if sms_content:
                                tracking_defaults['sms_content'] = sms_content
                        
                        # 创建跟踪记录（一对一关系）
                        tracking = OutgoingDocumentTracking.objects.create(
                            document=document,
                            delivery_method=delivery_method,
                            **tracking_defaults
                        )
                        
                        logger.info(f"创建独立的发文记录 {document.document_number}，收件人：{recipient_name}，报送方式：{delivery_method.name}")
                        
                    except Exception as e:
                        logger.error(f"为收件人 {recipient_data.get('name', '未知')} 创建发文记录失败: {str(e)}", exc_info=True)
                        continue
            
            # 检查是否创建了至少一条发文记录
            if not created_documents:
                messages.error(request, '创建失败：没有有效的收件人信息')
                return redirect('delivery_pages:outgoing_document_create')
            
            # 如果提交审批，为所有创建的发文记录启动审批流程
            if submit_for_approval:
                try:
                    from backend.apps.workflow_engine.models import WorkflowTemplate
                    from backend.apps.workflow_engine.services import ApprovalEngine
                    
                    # 获取发文审批流程模板
                    workflow = WorkflowTemplate.objects.get(code='outgoing_document_approval', status='active')
                    
                    approval_count = 0
                    for document in created_documents:
                        try:
                            # 启动审批流程
                            instance = ApprovalEngine.start_approval(
                                workflow=workflow,
                                content_object=document,
                                applicant=request.user,
                                comment='创建发文并提交审批'
                            )
                            
                            # 更新发文状态为审核中
                            document.transition_to('reviewing', actor=request.user, comment='创建发文并提交审批')
                            
                            # 检查是否成功创建了审批记录
                            from backend.apps.workflow_engine.models import ApprovalRecord
                            has_pending_records = ApprovalRecord.objects.filter(
                                instance=instance,
                                result='pending'
                            ).exists()
                            
                            if has_pending_records:
                                approval_count += 1
                                logger.info(f"发文 {document.document_number} 创建成功并启动审批流程: {instance.instance_number}")
                            else:
                                logger.warning(f"发文 {document.document_number} 审批流程已启动，但未找到审批人")
                        except Exception as e:
                            logger.error(f"为发文 {document.document_number} 启动审批流程失败: {str(e)}", exc_info=True)
            
                    if approval_count > 0:
                        if len(created_documents) == 1:
                            messages.success(request, f'发文"{title}"已提交审批，审批编号：{instance.instance_number}')
                        else:
                            messages.success(request, f'已创建 {len(created_documents)} 条发文记录并提交审批')
                    else:
                        messages.warning(request, f'已创建 {len(created_documents)} 条发文记录，但审批流程启动失败，请检查审批流程配置')
                except WorkflowTemplate.DoesNotExist:
                    messages.warning(request, f'已创建 {len(created_documents)} 条发文记录，但审批流程未配置，请联系管理员配置审批流程')
                    logger.warning(f"发文创建成功，但审批流程未找到: outgoing_document_approval")
                except Exception as e:
                    messages.warning(request, f'已创建 {len(created_documents)} 条发文记录，但启动审批流程失败：{str(e)}')
                    logger.error(f"发文创建成功，但启动审批流程失败: {str(e)}", exc_info=True)
            else:
                # 保存草稿
                if len(created_documents) == 1:
                    messages.success(request, f'发文"{title}"已保存为草稿')
                else:
                    messages.success(request, f'已创建 {len(created_documents)} 条发文记录并保存为草稿')
            
            # 重定向到第一条发文记录的详情页
            if created_documents:
                return redirect('delivery_pages:outgoing_document_detail', document_id=created_documents[0].id)
            else:
                return redirect('delivery_pages:outgoing_document_list')
        except Exception as e:
            logger.error(f"创建发文失败: {str(e)}")
            messages.error(request, f'创建失败：{str(e)}')
    
    # 获取用户列表
    from django.contrib.auth import get_user_model
    User = get_user_model()
    users = User.objects.filter(is_active=True).order_by('username')
    
    # 获取文件分类数据
    from backend.apps.delivery_customer.models import FileCategory
    categories = FileCategory.objects.filter(is_active=True).order_by('stage', 'sort_order', 'name')
    categories_by_stage = {}
    for category in categories:
        if category.stage not in categories_by_stage:
            categories_by_stage[category.stage] = []
        categories_by_stage[category.stage].append(category)
    
    # 获取项目列表（只显示商机管理中状态为"赢单"的商机对应的项目）
    # 商机编号（opportunity_number）即为项目编号，直接使用商机编号匹配项目的project_number
    from backend.apps.production_management.models import Project
    from backend.apps.customer_management.models import BusinessOpportunity
    
    # 从商机管理中获取状态为"赢单"的商机的商机编号（商机编号即为项目编号）
    won_opportunity_numbers = set()
    try:
        won_opportunities = BusinessOpportunity.objects.filter(
            status='won',
            opportunity_number__isnull=False
        ).exclude(opportunity_number='')
        won_opportunity_numbers = set(won_opportunities.values_list('opportunity_number', flat=True).distinct())
        logger.info(f"找到 {len(won_opportunity_numbers)} 个赢单商机编号: {list(won_opportunity_numbers)[:5]}")
    except Exception as e:
        logger.error(f"获取赢单商机编号失败: {str(e)}")
        pass
    
    # 通过商机编号（即项目编号）匹配项目
    if won_opportunity_numbers:
        projects = Project.objects.filter(
            project_number__in=won_opportunity_numbers
        ).filter(
            project_number__isnull=False
        ).exclude(project_number='').order_by('-created_time')[:100]
        logger.info(f"匹配到 {projects.count()} 个项目")
    else:
        # 如果没有赢单商机，返回空列表
        projects = Project.objects.none()
        logger.warning("没有找到赢单商机，项目列表为空")
    
    context = _context(
        "发文创建",
        "➕",
        "创建新的发文记录",
        request=request,
    )
    # 获取客户列表
    from backend.apps.customer_management.models import Client
    clients = Client.objects.filter(is_active=True).order_by('-created_time')[:200]
    
    # 获取报送方式列表（从数据库读取）
    from backend.apps.delivery_customer.models import DeliveryMethod
    delivery_methods = DeliveryMethod.objects.filter(is_active=True).order_by('sort_order', 'name')
    
    # 获取快递公司列表（从数据库读取）
    from backend.apps.delivery_customer.models import ExpressCompany
    express_companies = ExpressCompany.objects.filter(is_active=True).order_by('sort_order', 'name')
    
    context["module_sidebar_nav"] = module_sidebar_nav
    context["delivery_sidebar_nav"] = module_sidebar_nav  # 兼容旧模板
    context["status_choices"] = OutgoingDocument.STATUS_CHOICES
    context["priority_choices"] = OutgoingDocument.PRIORITY_CHOICES
    context["stage_choices"] = OutgoingDocument.STAGE_CHOICES
    context["categories"] = categories
    context["categories_by_stage"] = categories_by_stage
    context["users"] = users
    context["projects"] = projects
    context["clients"] = clients
    context["delivery_methods"] = delivery_methods
    context["express_companies"] = express_companies
    return render(request, "delivery_customer/outgoing_document_create.html", context)


@login_required
def get_recipient_units(request):
    """根据项目ID获取收文单位列表（关联客户、设计单位、人民法院）"""
    from django.http import JsonResponse
    from backend.apps.production_management.models import Project
    from backend.apps.customer_management.models import BusinessOpportunity
    from backend.apps.litigation_management.models import LitigationProcess
    import traceback
    
    project_id = request.GET.get('project_id')
    if not project_id:
        return JsonResponse({'success': False, 'error': '请提供项目ID'})
    
    try:
        # 确保 project_id 是整数
        try:
            project_id = int(project_id)
        except (ValueError, TypeError):
            return JsonResponse({'success': False, 'error': '项目ID格式错误'})
        
        project = Project.objects.get(id=project_id)
        recipient_units = []
        
        # 1. 关联客户 - 从赢单/输单获取
        try:
            # 通过项目编号匹配商机
            if project.project_number:
                opportunities = BusinessOpportunity.objects.filter(
                    opportunity_number=project.project_number
                ).filter(
                    status__in=['won', 'lost']  # 赢单或输单
                )
                for opp in opportunities:
                    if opp.client and opp.client.name:
                        recipient_units.append({
                            'type': 'client',
                            'name': opp.client.name,
                            'label': f'关联客户：{opp.client.name}',
                            'address': opp.client.company_address or ''  # 添加客户地址
                        })
        except Exception as e:
            logger.warning(f"获取关联客户失败: {str(e)}")
        
        # 2. 设计单位 - 从生产管理的项目表中获取
        if project.design_company:
            recipient_units.append({
                'type': 'design_unit',
                'name': project.design_company,
                'label': f'设计单位：{project.design_company}',
                'address': project.design_address or ''  # 添加设计单位地址（如果有）
            })
        
        # 3. 人民法院 - 从立案的项目表中获取
        try:
            # 查找该项目的立案流程
            litigation_cases = project.litigation_cases.all()
            for case in litigation_cases:
                # 查找立案流程（process_type='filing'）
                filing_processes = case.processes.filter(process_type='filing')
                for process in filing_processes:
                    if process.court_name:
                        recipient_units.append({
                            'type': 'court',
                            'name': process.court_name,
                            'label': f'人民法院：{process.court_name}'
                        })
        except Exception as e:
            logger.warning(f"获取人民法院失败: {str(e)}")
        
        # 去重（按名称）
        seen_names = set()
        unique_units = []
        for unit in recipient_units:
            if unit['name'] not in seen_names:
                seen_names.add(unit['name'])
                unique_units.append(unit)
        
        return JsonResponse({
            'success': True,
            'recipient_units': unique_units
        })
        
    except Project.DoesNotExist:
        return JsonResponse({'success': False, 'error': '项目不存在'})
    except Exception as e:
        error_msg = str(e)
        error_trace = traceback.format_exc()
        logger.error(f"获取收文单位列表失败: {error_msg}\n{error_trace}")
        return JsonResponse({
            'success': False, 
            'error': error_msg,
            'trace': error_trace if request.user.is_superuser else None
        })


@login_required
def get_recipient_contacts(request):
    """根据收文单位名称获取联系人列表"""
    from django.http import JsonResponse, HttpResponseServerError
    from django.db import connection
    from backend.apps.customer_management.models import Client, ClientContact
    from backend.apps.production_management.models import Project
    from backend.apps.customer_management.models import BusinessOpportunity
    
    recipient_name = request.GET.get('recipient_name')
    project_id = request.GET.get('project_id')
    
    if not recipient_name:
        return JsonResponse({'success': False, 'error': '请提供收文单位名称'}, status=400)
    
    try:
        # 检查数据库连接
        try:
            connection.ensure_connection()
        except Exception as db_error:
            logger.error(f"数据库连接失败: {str(db_error)}")
            return JsonResponse({
                'success': False, 
                'error': '数据库连接失败，请稍后重试'
            }, status=503)
        
        contacts = []
        client_address = ''  # 用于返回客户地址
        
        # 1. 尝试通过客户名称查找
        try:
            client = Client.objects.filter(name=recipient_name).first()
            if client:
                # 获取客户地址
                client_address = client.company_address or ''
                # 获取该客户的所有联系人（ClientContact模型没有is_active字段）
                client_contacts = ClientContact.objects.filter(client=client).exclude(name__isnull=True).exclude(name='').order_by('name')
                for contact in client_contacts:
                    contacts.append({
                        'id': contact.id,
                        'name': contact.name,
                        'phone': contact.phone or '',
                        'email': contact.email or '',
                        'position': contact.position or '',
                        'label': f'{contact.name}' + (f' - {contact.position}' if contact.position else ''),
                        'address': contact.office_address or client_address  # 优先使用联系人的办公地址，否则使用客户地址
                    })
        except Exception as e:
            logger.warning(f"通过客户名称查找联系人失败: {str(e)}", exc_info=True)
        
        # 2. 如果通过客户名称没找到，尝试通过项目查找
        if not contacts and project_id:
            try:
                # 通过项目ID查找项目，然后查找关联客户
                project = Project.objects.filter(id=project_id).first()
                if project and project.client:
                    # 检查项目关联的客户名称是否匹配收文单位名称
                    if project.client.name == recipient_name:
                        client_address = project.client.company_address or ''
                        client_contacts = ClientContact.objects.filter(client=project.client).exclude(name__isnull=True).exclude(name='').order_by('name')
                        for contact in client_contacts:
                            contacts.append({
                                'id': contact.id,
                                'name': contact.name,
                                'phone': contact.phone or '',
                                'email': contact.email or '',
                                'position': contact.position or '',
                                'label': f'{contact.name}' + (f' - {contact.position}' if contact.position else ''),
                                'address': contact.office_address or client_address  # 优先使用联系人的办公地址，否则使用客户地址
                            })
            except Exception as e:
                logger.warning(f"通过项目查找联系人失败: {str(e)}", exc_info=True)
        
        return JsonResponse({
            'success': True,
            'contacts': contacts,
            'address': client_address  # 返回客户地址，用于自动填充收文地址
        })
        
    except Exception as e:
        logger.error(f"获取收文单位联系人列表失败: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False, 
            'error': f'服务器错误：{str(e)}'
        }, status=500)


@login_required
def outgoing_document_detail(request, document_id):
    """发文详情 - 如果有审批流程则重定向到审批详情页面，否则显示发文详情页面"""
    from django.shortcuts import get_object_or_404, redirect
    from django.contrib.contenttypes.models import ContentType
    from django.utils import timezone
    from backend.apps.delivery_customer.models import OutgoingDocument
    from backend.apps.workflow_engine.models import ApprovalInstance
    
    # 优化查询：预加载关联数据
    document = get_object_or_404(
        OutgoingDocument.objects.select_related(
            'created_by', 'responsible_person', 'reviewer', 'sender',
            'project', 'client', 'client_contact', 'file_category'
        ).prefetch_related(
            'status_logs', 'tracking_records__delivery_method'
        ),
        id=document_id
    )
    
    # 检查是否有审批实例（包括已完成和进行中的）
    content_type = ContentType.objects.get_for_model(OutgoingDocument)
    approval_instance = ApprovalInstance.objects.filter(
        content_type=content_type,
        object_id=document_id
    ).first()
    
    # 如果有审批实例，重定向到审批详情页面
    if approval_instance:
        from django.urls import reverse
        return redirect('workflow_engine:approval_detail', instance_id=approval_instance.id)
    
    # 如果没有审批实例，继续显示发文详情页面（适用于草稿状态等）
    permission_set = get_user_permission_codes(request.user)
    module_sidebar_nav = _build_delivery_sidebar_nav(permission_set, request.path)
    delivery_sidebar_nav = module_sidebar_nav  # 兼容旧模板
    
    # 获取状态流转日志（按时间正序：最早的在前面，用于时间线从上往下显示）
    # 使用 order_by('created_at', 'id') 确保排序稳定，即使时间相同也能保持一致的顺序
    status_logs = document.status_logs.select_related('actor').order_by('created_at', 'id')[:50]
    
    # 获取跟踪记录（按报送方式分组）
    tracking_records = document.tracking_records.select_related('delivery_method', 'created_by', 'hand_delivery_checkin_by').order_by('-created_at')
    
    # 统计跟踪记录信息
    tracking_stats = {
        'total': tracking_records.count(),
        'pending': tracking_records.filter(status='pending').count(),
        'sent': tracking_records.filter(status__in=['sent', 'sending']).count(),
        'delivered': tracking_records.filter(status='delivered').count(),
        'completed': tracking_records.filter(status='completed').count(),
        'failed': tracking_records.filter(status='failed').count(),
    }
    
    # 按报送方式分组跟踪记录
    tracking_by_method = {}
    for tracking in tracking_records:
        method_name = tracking.delivery_method.name if tracking.delivery_method else '未知方式'
        if method_name not in tracking_by_method:
            tracking_by_method[method_name] = []
        tracking_by_method[method_name].append(tracking)
    
    context = _context(
        f"发文详情 - {document.document_number}",
        "📤",
        f"查看发文：{document.title}",
        request=request,
    )
    context["module_sidebar_nav"] = module_sidebar_nav
    context["delivery_sidebar_nav"] = module_sidebar_nav  # 兼容旧模板
    context["document"] = document
    context["status_logs"] = status_logs
    context["tracking_records"] = tracking_records
    context["tracking_stats"] = tracking_stats
    context["tracking_by_method"] = tracking_by_method
    context["can_edit"] = _permission_granted('delivery_center.create', permission_set)
    context["can_review"] = _permission_granted('delivery_center.approve', permission_set)
    
    # 判断可以进行的状态流转操作
    can_actions = {}
    
    # 检查是否有审批流程在进行中
    from django.contrib.contenttypes.models import ContentType
    from backend.apps.workflow_engine.models import ApprovalInstance
    has_approval_workflow = False
    try:
        content_type = ContentType.objects.get_for_model(OutgoingDocument)
        approval_instance = ApprovalInstance.objects.filter(
            content_type=content_type,
            object_id=document.id,
            status='pending'  # 只检查进行中的审批流程
        ).exists()
        has_approval_workflow = approval_instance
    except:
        pass
    
    # 注意：所有发文在创建时就会自动启动审批流程，不需要在详情页再提交审核
    # 因此不显示"提交审核"按钮
    # 如果状态是草稿且没有审批流程，说明创建时启动审批流程失败了，可以手动重新提交
    if document.status == 'draft' and not has_approval_workflow:
        # 只有在创建时审批流程启动失败的情况下，才显示"重新提交审核"按钮
        can_actions['submit_review'] = True
    
    # 不显示直接审核通过按钮，所有发文必须通过审批流程
    # can_actions['approve'] 已移除，只能通过审批流程引擎进行审批
    
    if document.can_transition_to('sent'):
        can_actions['send'] = True
    if document.can_transition_to('completed'):
        can_actions['complete'] = True
    if document.can_transition_to('archived'):
        can_actions['archive'] = True
    context["can_actions"] = can_actions
    
    # 检查是否可以记录补救措施（延迟的发文）
    context["can_record_remedy"] = document.is_delayed and not document.is_receipt_confirmed
    
    # 添加审计追踪链接
    from django.urls import reverse
    try:
        context["audit_trail_url"] = reverse('delivery_pages:outgoing_document_audit_trail', args=[document.id])
    except:
        context["audit_trail_url"] = None
    
    # 如果设置了责任人，添加绩效查看链接和当前发文绩效得分
    if document.responsible_person:
        try:
            context["performance_url"] = reverse('delivery_pages:outgoing_document_performance_detail', args=[document.responsible_person.id])
            from backend.apps.delivery_customer.services import OutgoingDocumentPerformanceService
            context["document_performance"] = OutgoingDocumentPerformanceService.calculate_performance_score(document)
        except:
            context["performance_url"] = None
            context["document_performance"] = None
    else:
        context["performance_url"] = None
        context["document_performance"] = None
    
    # 添加补救措施记录链接（如果是延迟的发文）
    if document.is_delayed:
        try:
            context["remedy_url"] = reverse('delivery_pages:outgoing_document_record_remedy', args=[document.id])
        except:
            context["remedy_url"] = None
    else:
        context["remedy_url"] = None
    
    # 添加审批流程信息（如果存在）
    from django.contrib.contenttypes.models import ContentType
    from backend.apps.workflow_engine.models import ApprovalInstance, ApprovalRecord
    try:
        content_type = ContentType.objects.get_for_model(OutgoingDocument)
        approval_instance = ApprovalInstance.objects.filter(
            content_type=content_type,
            object_id=document.id
        ).select_related('workflow', 'current_node', 'applicant').prefetch_related('records__approver', 'records__node').first()
        
        if approval_instance:
            context["approval_instance"] = approval_instance
            # 获取待审批记录（当前用户）
            if request.user.is_authenticated:
                pending_record = ApprovalRecord.objects.filter(
                    instance=approval_instance,
                    approver=request.user,
                    result='pending'
                ).first()
                context["can_approve_workflow"] = pending_record is not None
            else:
                context["can_approve_workflow"] = False
            
            # 获取审批历史记录（按时间正序：最早的在前面，用于时间线从上往下显示）
            # 使用 order_by('approval_time', 'id') 确保排序稳定，即使时间相同也能保持一致的顺序
            approval_records = approval_instance.records.select_related('approver', 'node').order_by('approval_time', 'id')
            context["approval_records"] = approval_records
            
            # 合并审批历史记录和流程跟踪记录，创建统一的时间线事件列表
            # 将所有事件按时间从早到晚排序
            timeline_events = []
            
            # 添加审批历史记录
            for record in approval_records:
                timeline_events.append({
                    'type': 'approval',
                    'time': record.approval_time,
                    'record': record,
                    'sort_id': record.id,
                })
            
            # 添加流程跟踪记录
            for log in status_logs:
                timeline_events.append({
                    'type': 'status_log',
                    'time': log.created_at,
                    'log': log,
                    'sort_id': log.id,
                })
            
            # 按时间排序（从早到晚），时间相同时按ID排序
            timeline_events.sort(key=lambda x: (x['time'], x['sort_id']))
            context["timeline_events"] = timeline_events
            
            # 重要：详情页加载时，绝对不要自动检查审批状态并显示"审核通过"消息
            # 所有消息都应该由明确的用户操作触发，而不是在页面加载时自动显示
        else:
            context["approval_instance"] = None
            context["can_approve_workflow"] = False
            context["approval_records"] = []
            # 如果没有审批流程，只使用流程跟踪记录作为时间线
            timeline_events = []
            for log in status_logs:
                timeline_events.append({
                    'type': 'status_log',
                    'time': log.created_at,
                    'log': log,
                    'sort_id': log.id,
                })
            timeline_events.sort(key=lambda x: (x['time'], x['sort_id']))
            context["timeline_events"] = timeline_events
    except Exception as e:
        logger.error(f"获取审批流程信息失败: {str(e)}")
        context["approval_instance"] = None
        context["can_approve_workflow"] = False
        context["approval_records"] = []
        # 出错时，只使用流程跟踪记录作为时间线
        timeline_events = []
        for log in status_logs:
            timeline_events.append({
                'type': 'status_log',
                'time': log.created_at,
                'log': log,
                'sort_id': log.id,
            })
        timeline_events.sort(key=lambda x: (x['time'], x['sort_id']))
        context["timeline_events"] = timeline_events
    
    # 添加附件信息
    context["has_attachment"] = bool(document.attachment)
    if document.attachment:
        try:
            import os
            context["attachment_name"] = os.path.basename(document.attachment.name)
            context["attachment_size"] = document.attachment.size
            context["attachment_url"] = document.attachment.url
        except:
            context["attachment_name"] = None
            context["attachment_size"] = None
            context["attachment_url"] = None
    
    # 添加关联项目信息（如果有）
    if document.project:
        try:
            context["project_name"] = document.project.name if hasattr(document.project, 'name') else None
            context["project_number"] = document.project.project_number if hasattr(document.project, 'project_number') else None
            try:
                context["project_detail_url"] = reverse('production_pages:project_detail', args=[document.project.id])
            except:
                context["project_detail_url"] = None
        except Exception as e:
            logger.error(f"获取项目信息失败: {str(e)}")
            context["project_name"] = None
            context["project_number"] = None
            context["project_detail_url"] = None
    else:
        context["project_name"] = None
        context["project_number"] = None
        context["project_detail_url"] = None
    
    # 添加关联客户信息（如果有）
    if document.client:
        context["client_name"] = document.client.name
        try:
            context["client_detail_url"] = reverse('customer_pages:client_detail', args=[document.client.id])
        except:
            context["client_detail_url"] = None
    else:
        context["client_name"] = None
        context["client_detail_url"] = None
    
    # 计算时间统计信息
    time_stats = {}
    if document.created_at:
        time_stats['created_days_ago'] = (timezone.now() - document.created_at).days
    if document.sent_at:
        time_stats['sent_days_ago'] = (timezone.now() - document.sent_at).days
        if document.created_at:
            time_stats['create_to_send_days'] = (document.sent_at - document.created_at).days
    # 使用 confirmed_at 作为完成时间（OutgoingDocument 模型没有 completed_at 字段）
    if document.confirmed_at:
        time_stats['completed_days_ago'] = (timezone.now() - document.confirmed_at).days
        if document.sent_at:
            time_stats['send_to_complete_days'] = (document.confirmed_at - document.sent_at).days
    # OutgoingDocument 模型没有 archived_at 字段，如果状态为已归档，使用 updated_at
    if document.status == 'archived' and document.updated_at:
        time_stats['archived_days_ago'] = (timezone.now() - document.updated_at).days
    context["time_stats"] = time_stats
    
    # 添加编辑和删除链接
    try:
        context["edit_url"] = reverse('delivery_pages:outgoing_document_edit', args=[document.id])
    except:
        context["edit_url"] = None
    
    try:
        context["list_url"] = reverse('delivery_pages:outgoing_document_list')
    except:
        context["list_url"] = None
    
    return render(request, "delivery_customer/outgoing_document_detail.html", context)


@login_required
def outgoing_document_edit(request, document_id):
    """发文编辑"""
    from django.shortcuts import redirect, get_object_or_404
    from django.contrib import messages
    from backend.apps.delivery_customer.models import OutgoingDocument
    
    permission_set = get_user_permission_codes(request.user)
    module_sidebar_nav = _build_delivery_sidebar_nav(permission_set, request.path)
    delivery_sidebar_nav = module_sidebar_nav  # 兼容旧模板
    
    if not _permission_granted('delivery_center.create', permission_set):
        messages.error(request, '您没有编辑发文的权限')
        return redirect('delivery_pages:outgoing_document_list')
    
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
            document.document_type = request.POST.get('document_type', '').strip()
            document.send_date = request.POST.get('send_date') or None
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
            
            # 如果选择了快递报送方式，更新快递信息到文档
            delivery_methods_list = request.POST.getlist('delivery_methods')
            if 'express' in delivery_methods_list:
                express_company = request.POST.get('express_company', '').strip()
                express_number = request.POST.get('express_number', '').strip()
                if express_company:
                    document.express_company = express_company
                if express_number:
                    document.express_number = express_number
            
            # 处理附件
            if 'attachment' in request.FILES:
                document.attachment = request.FILES['attachment']
            
            # 注意：状态流转必须通过审批流程引擎或明确的状态流转操作，不能在这里自动修改状态
            # 删除旧的自动状态更新逻辑，避免自动触发"审核通过"等消息
            
            # 如果状态变为已发出，记录发送时间（这个可以保留，因为发送是明确的操作）
            if document.status == 'sent' and not document.sent_at:
                from django.utils import timezone
                document.sent_at = timezone.now()
            
            # 如果状态变为已完成，记录确认时间（OutgoingDocument 使用 confirmed_at 而不是 completed_at）
            if document.status == 'completed' and not document.confirmed_at:
                from django.utils import timezone
                document.confirmed_at = timezone.now()
            
            document.save()
            messages.success(request, f'发文"{document.title}"更新成功')
            return redirect('delivery_pages:outgoing_document_detail', document_id=document.id)
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
    from backend.apps.delivery_customer.models import FileCategory
    categories = FileCategory.objects.filter(is_active=True).order_by('stage', 'sort_order', 'name')
    categories_by_stage = {}
    for category in categories:
        if category.stage not in categories_by_stage:
            categories_by_stage[category.stage] = []
        categories_by_stage[category.stage].append(category)
    
    # 获取项目列表（只显示商机管理中状态为"赢单"的商机对应的项目）
    # 商机编号（opportunity_number）即为项目编号，直接使用商机编号匹配项目的project_number
    from backend.apps.production_management.models import Project
    from backend.apps.customer_management.models import BusinessOpportunity
    
    # 从商机管理中获取状态为"赢单"的商机的商机编号（商机编号即为项目编号）
    won_opportunity_numbers = set()
    try:
        won_opportunities = BusinessOpportunity.objects.filter(
            status='won',
            opportunity_number__isnull=False
        ).exclude(opportunity_number='')
        won_opportunity_numbers = set(won_opportunities.values_list('opportunity_number', flat=True).distinct())
        logger.info(f"找到 {len(won_opportunity_numbers)} 个赢单商机编号: {list(won_opportunity_numbers)[:5]}")
    except Exception as e:
        logger.error(f"获取赢单商机编号失败: {str(e)}")
        pass
    
    # 通过商机编号（即项目编号）匹配项目
    if won_opportunity_numbers:
        projects = Project.objects.filter(
            project_number__in=won_opportunity_numbers
        ).filter(
            project_number__isnull=False
        ).exclude(project_number='').order_by('-created_time')[:100]
        logger.info(f"匹配到 {projects.count()} 个项目")
    else:
        # 如果没有赢单商机，返回空列表
        projects = Project.objects.none()
        logger.warning("没有找到赢单商机，项目列表为空")
    
    # 处理报送方式列表（用于模板显示）
    delivery_methods_list = []
    if document.delivery_methods:
        delivery_methods_list = [m.strip() for m in document.delivery_methods.split(',') if m.strip()]
    
    # 获取客户列表
    from backend.apps.customer_management.models import Client
    clients = Client.objects.filter(is_active=True).order_by('-created_time')[:200]
    
    context["module_sidebar_nav"] = module_sidebar_nav
    context["delivery_sidebar_nav"] = module_sidebar_nav  # 兼容旧模板
    context["document"] = document
    context["document"].delivery_methods_list = delivery_methods_list  # 添加属性到document对象
    context["status_choices"] = OutgoingDocument.STATUS_CHOICES
    context["priority_choices"] = OutgoingDocument.PRIORITY_CHOICES
    context["stage_choices"] = OutgoingDocument.STAGE_CHOICES
    context["categories"] = categories
    context["categories_by_stage"] = categories_by_stage
    context["users"] = users
    context["projects"] = projects
    context["clients"] = clients
    return render(request, "delivery_customer/outgoing_document_edit.html", context)


@login_required
def outgoing_document_delete(request, document_id):
    """发文删除"""
    from django.shortcuts import redirect, get_object_or_404
    from django.contrib import messages
    from backend.apps.delivery_customer.models import OutgoingDocument
    
    permission_set = get_user_permission_codes(request.user)
    
    if not _permission_granted('delivery_center.create', permission_set):
        messages.error(request, '您没有删除发文的权限')
        return redirect('delivery_pages:outgoing_document_list')
    
    document = get_object_or_404(OutgoingDocument, id=document_id)
    
    # 只有草稿状态可以删除
    if document.status != 'draft':
        messages.error(request, '只能删除草稿状态的发文')
        return redirect('delivery_pages:outgoing_document_detail', document_id=document_id)
    
    if request.method == 'POST':
        document_number = document.document_number
        document.delete()
        messages.success(request, f'发文 {document_number} 已删除')
        return redirect('delivery_pages:outgoing_document_list')
    
    # GET 请求显示确认页面
    context = _context(
        "删除发文",
        "🗑️",
        f"确定要删除发文 {document.document_number} 吗？",
        request=request,
        active_menu_id='outgoing_document_list'
    )
    context.update({
        'document': document,
    })
    return render(request, "delivery_customer/outgoing_document_delete_confirm.html", context)


# ==================== 发文状态流转操作 ====================

@login_required
def outgoing_document_submit_review(request, document_id):
    """提交审核（集成审批流程引擎）"""
    from django.shortcuts import redirect, get_object_or_404
    from django.contrib import messages
    from backend.apps.delivery_customer.models import OutgoingDocument
    from backend.apps.workflow_engine.models import WorkflowTemplate
    from backend.apps.workflow_engine.services import ApprovalEngine
    
    permission_set = get_user_permission_codes(request.user)
    
    document = get_object_or_404(OutgoingDocument, id=document_id)
    
    # 检查当前状态
    if document.status != 'draft':
        messages.error(request, f'只有草稿状态的发文可以提交审核，当前状态：{document.get_status_display()}')
        return redirect('delivery_pages:outgoing_document_detail', document_id=document.id)
    
    if request.method == 'POST':
        try:
            comment = request.POST.get('comment', '').strip()
            
            # 获取发文审批流程模板
            try:
                workflow = WorkflowTemplate.objects.get(code='outgoing_document_approval', status='active')
            except WorkflowTemplate.DoesNotExist:
                messages.error(request, '发文审批流程未配置，请联系管理员配置审批流程')
                logger.error(f"发文审批流程未找到: outgoing_document_approval")
                return redirect('delivery_pages:outgoing_document_detail', document_id=document.id)
            
            # 检查是否已有审批实例
            from django.contrib.contenttypes.models import ContentType
            content_type = ContentType.objects.get_for_model(OutgoingDocument)
            from backend.apps.workflow_engine.models import ApprovalInstance
            existing_instance = ApprovalInstance.objects.filter(
                content_type=content_type,
                object_id=document.id,
                status__in=['pending', 'draft']
            ).first()
            
            if existing_instance:
                messages.warning(request, '该发文已有审批流程在进行中')
                return redirect('delivery_pages:outgoing_document_detail', document_id=document.id)
            
            # 启动审批流程
            instance = ApprovalEngine.start_approval(
                workflow=workflow,
                content_object=document,
                applicant=request.user,
                comment=comment or '提交发文审批'
            )
            
            # 更新发文状态为审核中
            document.transition_to('reviewing', actor=request.user, comment=comment or '提交审核')
            
            # 保存审批实例ID到发文（如果需要）
            # document.approval_instance_id = instance.id  # 如果模型有该字段
            
            messages.success(request, f'发文已提交审核，审批编号：{instance.instance_number}')
            logger.info(f"发文 {document.document_number} 已启动审批流程: {instance.instance_number}")
            
        except ValueError as e:
            messages.error(request, str(e))
        except Exception as e:
            logger.error(f"提交审核失败: {str(e)}", exc_info=True)
            messages.error(request, f'操作失败：{str(e)}')
    
    return redirect('delivery_pages:outgoing_document_detail', document_id=document.id)


@login_required
def outgoing_document_approve(request, document_id):
    """审核通过（仅通过审批流程引擎，不允许直接审核）"""
    from django.shortcuts import redirect, get_object_or_404
    from django.contrib import messages
    from backend.apps.delivery_customer.models import OutgoingDocument
    from backend.apps.workflow_engine.models import ApprovalInstance
    from backend.apps.workflow_engine.services import ApprovalEngine
    from django.contrib.contenttypes.models import ContentType
    
    permission_set = get_user_permission_codes(request.user)
    
    if not _permission_granted('delivery_center.approve', permission_set):
        messages.error(request, '您没有审核权限')
        return redirect('delivery_pages:outgoing_document_detail', document_id=document_id)
    
    document = get_object_or_404(OutgoingDocument, id=document_id)
    
    if request.method == 'POST':
        try:
            comment = request.POST.get('comment', '').strip()
            review_notes = request.POST.get('review_notes', '').strip()
            
            # 查找关联的审批实例
            content_type = ContentType.objects.get_for_model(OutgoingDocument)
            approval_instance = ApprovalInstance.objects.filter(
                content_type=content_type,
                object_id=document.id,
                status='pending'
            ).first()
            
            # 如果找不到审批流程，尝试自动启动（如果状态允许）
            if not approval_instance:
                # 如果发文是草稿状态，提示用户先提交审核
                if document.status == 'draft':
                    messages.error(request, '该发文尚未提交审核，请先提交审核后再进行审批')
                    return redirect('delivery_pages:outgoing_document_detail', document_id=document.id)
                
                # 如果发文是审核中状态但没有审批流程，尝试自动启动审批流程
                if document.status == 'reviewing':
                    try:
                        from backend.apps.workflow_engine.models import WorkflowTemplate
                        workflow = WorkflowTemplate.objects.get(code='outgoing_document_approval', status='active')
                        instance = ApprovalEngine.start_approval(
                            workflow=workflow,
                            content_object=document,
                            applicant=document.created_by or request.user,
                            comment='自动启动审批流程'
                        )
                        approval_instance = instance
                        messages.info(request, f'已自动启动审批流程，审批编号：{instance.instance_number}')
                        logger.info(f"发文 {document.document_number} 自动启动审批流程: {instance.instance_number}")
                    except WorkflowTemplate.DoesNotExist:
                        messages.error(request, '审批流程未配置，请联系管理员配置审批流程')
                        return redirect('delivery_pages:outgoing_document_detail', document_id=document.id)
                    except Exception as e:
                        messages.error(request, f'自动启动审批流程失败：{str(e)}，请联系管理员')
                        logger.error(f"发文 {document.document_number} 自动启动审批流程失败: {str(e)}", exc_info=True)
                        return redirect('delivery_pages:outgoing_document_detail', document_id=document.id)
                else:
                    # 其他状态，根据状态给出不同的提示
                    if document.status == 'approved':
                        messages.info(request, f'该发文已通过审批，当前状态为"{document.get_status_display()}"，无需再次审批。')
                    elif document.status == 'rejected':
                        messages.warning(request, f'该发文已被驳回，当前状态为"{document.get_status_display()}"。如需重新提交，请修改后重新提交审核。')
                    elif document.status in ['sent', 'completed', 'archived']:
                        messages.info(request, f'该发文当前状态为"{document.get_status_display()}"，审批流程已完成。')
                    else:
                        messages.error(request, f'该发文当前状态为"{document.get_status_display()}"，无法进行审批。')
                    return redirect('delivery_pages:outgoing_document_detail', document_id=document.id)
            
            # 检查当前用户是否有审批权限
            from backend.apps.workflow_engine.models import ApprovalRecord
            pending_record = ApprovalRecord.objects.filter(
                instance=approval_instance,
                approver=request.user,
                result='pending'
            ).first()
            
            if not pending_record:
                messages.error(request, '您不是当前节点的审批人，无法进行审批')
                return redirect('delivery_pages:outgoing_document_detail', document_id=document.id)
            
            # 通过审批流程引擎进行审批
            success = ApprovalEngine.approve(
                instance=approval_instance,
                approver=request.user,
                result='approved',
                comment=comment or '审批通过'
            )
            
            if not success:
                messages.error(request, '审批操作失败，请重试')
                return redirect('delivery_pages:outgoing_document_detail', document_id=document.id)
            
            # 刷新审批实例
            approval_instance.refresh_from_db()
            
            # 如果审批流程已完成，更新发文状态为已批准
            if approval_instance.status == 'approved':
                document.review_notes = review_notes
                document.transition_to('approved', actor=request.user, comment=comment or '审批流程完成', reviewer=request.user)
                # 彻底删除"审核通过"相关消息，只显示简单的成功消息
                messages.success(request, '审批流程已完成')
                logger.info(f"发文 {document.document_number} 审批流程完成，状态已更新为已批准")
            else:
                # 审批流程还在进行中，只是当前节点审批完成
                # 彻底删除"审批通过"或"审核通过"相关消息
                messages.success(request, f'当前节点审批完成，流程继续')
                logger.info(f"发文 {document.document_number} 当前节点审批完成，流程继续")
            
        except ValueError as e:
            messages.error(request, str(e))
        except Exception as e:
            logger.error(f"审批操作失败: {str(e)}", exc_info=True)
            messages.error(request, f'操作失败：{str(e)}')
    
    return redirect('delivery_pages:outgoing_document_detail', document_id=document.id)


@login_required
def outgoing_document_reject(request, document_id):
    """审核拒绝（退回草稿，集成审批流程引擎）"""
    from django.shortcuts import redirect, get_object_or_404
    from django.contrib import messages
    from backend.apps.delivery_customer.models import OutgoingDocument
    from backend.apps.workflow_engine.models import ApprovalInstance
    from backend.apps.workflow_engine.services import ApprovalEngine
    from django.contrib.contenttypes.models import ContentType
    
    permission_set = get_user_permission_codes(request.user)
    
    if not _permission_granted('delivery_center.approve', permission_set):
        messages.error(request, '您没有审核权限')
        return redirect('delivery_pages:outgoing_document_detail', document_id=document_id)
    
    document = get_object_or_404(OutgoingDocument, id=document_id)
    
    if request.method == 'POST':
        try:
            # 检查当前状态是否允许退回草稿
            if document.status == 'draft':
                messages.warning(request, '发文已经是草稿状态，无需退回')
                return redirect('delivery_pages:outgoing_document_detail', document_id=document.id)
            
            if not document.can_transition_to('draft'):
                messages.error(request, f'当前状态"{document.get_status_display()}"无法退回草稿，只有审核中的发文可以退回')
                return redirect('delivery_pages:outgoing_document_detail', document_id=document.id)
            
            comment = request.POST.get('comment', '').strip()
            if not comment:
                messages.error(request, '审核意见不能为空')
                return redirect('delivery_pages:outgoing_document_detail', document_id=document.id)
            
            # 查找关联的审批实例
            content_type = ContentType.objects.get_for_model(OutgoingDocument)
            approval_instance = ApprovalInstance.objects.filter(
                content_type=content_type,
                object_id=document.id,
                status='pending'
            ).first()
            
            # 如果找不到审批流程，尝试自动启动（如果状态允许）
            if not approval_instance:
                # 如果发文是草稿状态，提示用户先提交审核
                if document.status == 'draft':
                    messages.error(request, '该发文尚未提交审核，无法进行审批拒绝')
                    return redirect('delivery_pages:outgoing_document_detail', document_id=document.id)
                
                # 如果发文是审核中状态但没有审批流程，尝试自动启动审批流程
                if document.status == 'reviewing':
                    try:
                        from backend.apps.workflow_engine.models import WorkflowTemplate
                        workflow = WorkflowTemplate.objects.get(code='outgoing_document_approval', status='active')
                        instance = ApprovalEngine.start_approval(
                            workflow=workflow,
                            content_object=document,
                            applicant=document.created_by or request.user,
                            comment='自动启动审批流程'
                        )
                        approval_instance = instance
                        messages.info(request, f'已自动启动审批流程，审批编号：{instance.instance_number}')
                        logger.info(f"发文 {document.document_number} 自动启动审批流程: {instance.instance_number}")
                    except WorkflowTemplate.DoesNotExist:
                        messages.error(request, '审批流程未配置，请联系管理员配置审批流程')
                        return redirect('delivery_pages:outgoing_document_detail', document_id=document.id)
                    except Exception as e:
                        messages.error(request, f'自动启动审批流程失败：{str(e)}，请联系管理员')
                        logger.error(f"发文 {document.document_number} 自动启动审批流程失败: {str(e)}", exc_info=True)
                        return redirect('delivery_pages:outgoing_document_detail', document_id=document.id)
                else:
                    # 其他状态，根据状态给出不同的提示
                    if document.status == 'approved':
                        messages.info(request, f'该发文已通过审批，当前状态为"{document.get_status_display()}"，无法进行审批拒绝。')
                    elif document.status == 'rejected':
                        messages.warning(request, f'该发文已被驳回，当前状态为"{document.get_status_display()}"。')
                    elif document.status in ['sent', 'completed', 'archived']:
                        messages.info(request, f'该发文当前状态为"{document.get_status_display()}"，审批流程已完成。')
                    else:
                        messages.error(request, f'该发文当前状态为"{document.get_status_display()}"，无法进行审批拒绝。')
                    return redirect('delivery_pages:outgoing_document_detail', document_id=document.id)
            
            if approval_instance:
                # 检查当前用户是否有审批权限
                from backend.apps.workflow_engine.models import ApprovalRecord
                pending_record = ApprovalRecord.objects.filter(
                    instance=approval_instance,
                    approver=request.user,
                    result='pending'
                ).first()
                
                if pending_record:
                    # 通过审批流程引擎拒绝
                    success = ApprovalEngine.approve(
                        instance=approval_instance,
                        approver=request.user,
                        result='rejected',
                        comment=comment
                    )
                    
                    if not success:
                        messages.error(request, '拒绝操作失败，请重试')
                        return redirect('delivery_pages:outgoing_document_detail', document_id=document.id)
                    
                    logger.info(f"发文 {document.document_number} 审批流程被拒绝: {comment}")
                else:
                    # 用户不是当前审批人，但可能想直接退回（比如管理员操作）
                    logger.warning(f"用户 {request.user.username} 不是当前审批人，但尝试拒绝审批流程")
            
            # 更新发文状态为草稿
            review_notes = request.POST.get('review_notes', '').strip()
            document.review_notes = review_notes
            document.transition_to('draft', actor=request.user, comment=comment, reviewer=request.user)
            messages.success(request, '发文已退回草稿')
            
        except ValueError as e:
            messages.error(request, str(e))
        except Exception as e:
            logger.error(f"审核拒绝失败: {str(e)}", exc_info=True)
            messages.error(request, f'操作失败：{str(e)}')
    
    return redirect('delivery_pages:outgoing_document_detail', document_id=document.id)


@login_required
def outgoing_document_send(request, document_id):
    """发送"""
    from django.shortcuts import redirect, get_object_or_404
    from django.contrib import messages
    from django.utils import timezone
    from backend.apps.delivery_customer.models import OutgoingDocument, OutgoingDocumentTracking, DeliveryMethod
    from backend.apps.delivery_customer.tracking_service import TrackingServiceFactory
    
    permission_set = get_user_permission_codes(request.user)
    
    document = get_object_or_404(OutgoingDocument, id=document_id)
    
    if request.method == 'POST':
        try:
            comment = request.POST.get('comment', '').strip()
            send_method = request.POST.get('send_method', '').strip()
            send_date = request.POST.get('send_date', '').strip()
            
            if send_date:
                from django.utils.dateparse import parse_date
                document.send_date = parse_date(send_date) or timezone.now().date()
            else:
                document.send_date = timezone.now().date()
            
            document.send_method = send_method
            document.sent_at = timezone.now()
            document.save()
            
            # 更新文档状态
            document.transition_to('sent', actor=request.user, comment=comment or '已发送', sender=request.user)
            
            # 处理报送方式，创建跟踪记录并发送
            send_results = []
            if document.delivery_methods:
                delivery_method_codes = [m.strip() for m in document.delivery_methods.split(',') if m.strip()]
                for method_code in delivery_method_codes:
                    try:
                        # 获取报送方式对象
                        delivery_method = DeliveryMethod.objects.filter(code=method_code, is_active=True).first()
                        if not delivery_method:
                            logger.warning(f"报送方式 {method_code} 不存在或已禁用")
                            continue
                        
                        # 创建或获取跟踪记录
                        tracking_defaults = {
                                'status': 'pending',
                                'created_by': request.user,
                            }
                        
                        # 如果是快递方式，从document中同步快递信息
                        if method_code == 'express':
                            if document.express_company:
                                tracking_defaults['express_company'] = document.express_company
                            if document.express_number:
                                tracking_defaults['express_number'] = document.express_number
                        
                        tracking, created = OutgoingDocumentTracking.objects.get_or_create(
                            document=document,
                            delivery_method=delivery_method,
                            defaults=tracking_defaults
                        )
                        
                        # 如果记录已存在且是快递方式，同步快递信息（如果tracking中没有但document中有）
                        if not created and method_code == 'express':
                            update_fields = []
                            if not tracking.express_company and document.express_company:
                                tracking.express_company = document.express_company
                                update_fields.append('express_company')
                            if not tracking.express_number and document.express_number:
                                tracking.express_number = document.express_number
                                update_fields.append('express_number')
                            if update_fields:
                                tracking.save(update_fields=update_fields)
                        
                        # 根据报送方式调用相应的跟踪服务
                        try:
                            service = TrackingServiceFactory.get_service(method_code)
                            
                            if method_code == 'email':
                                # 邮件发送
                                success, message = service.send_email(tracking)
                                if success:
                                    send_results.append(f"{delivery_method.name}: 发送成功")
                                    logger.info(f"发文 {document.document_number} 邮件发送成功: {message}")
                                else:
                                    send_results.append(f"{delivery_method.name}: 发送失败 - {message}")
                                    logger.error(f"发文 {document.document_number} 邮件发送失败: {message}")
                            
                            elif method_code == 'express':
                                # 快递：需要快递单号，这里只创建跟踪记录，不自动查询
                                # 快递单号应该在发送时或发送后填写
                                tracking.status = 'pending'
                                tracking.save()
                                send_results.append(f"{delivery_method.name}: 跟踪记录已创建，请填写快递单号")
                                logger.info(f"发文 {document.document_number} 快递跟踪记录已创建")
                            
                            elif method_code == 'hand_delivery':
                                # 现场送达：需要打卡，这里只创建跟踪记录
                                tracking.status = 'pending'
                                tracking.save()
                                send_results.append(f"{delivery_method.name}: 跟踪记录已创建，请进行现场送达打卡")
                                logger.info(f"发文 {document.document_number} 现场送达跟踪记录已创建")
                            
                            elif method_code == 'yisign':
                                # 易签宝：需要创建合同，这里只创建跟踪记录
                                tracking.status = 'pending'
                                tracking.save()
                                send_results.append(f"{delivery_method.name}: 跟踪记录已创建，请创建易签宝合同")
                                logger.info(f"发文 {document.document_number} 易签宝跟踪记录已创建")
                            
                            else:
                                # 其他报送方式
                                tracking.status = 'pending'
                                tracking.save()
                                send_results.append(f"{delivery_method.name}: 跟踪记录已创建")
                                logger.info(f"发文 {document.document_number} {delivery_method.name} 跟踪记录已创建")
                        
                        except ValueError as e:
                            logger.error(f"不支持的报送方式: {method_code} - {str(e)}")
                            send_results.append(f"{delivery_method.name}: 不支持的报送方式")
                        except Exception as e:
                            logger.error(f"调用跟踪服务失败: {method_code} - {str(e)}", exc_info=True)
                            send_results.append(f"{delivery_method.name}: 处理失败 - {str(e)}")
                    
                    except Exception as e:
                        logger.error(f"处理报送方式 {method_code} 失败: {str(e)}", exc_info=True)
                        send_results.append(f"报送方式 {method_code}: 处理失败 - {str(e)}")
            
            # 显示发送结果
            if send_results:
                result_message = "；".join(send_results)
                messages.success(request, f'发文已标记为已发送。{result_message}')
            else:
                messages.success(request, '发文已标记为已发送')
        
        except ValueError as e:
            messages.error(request, str(e))
        except Exception as e:
            logger.error(f"发送失败: {str(e)}", exc_info=True)
            messages.error(request, f'操作失败：{str(e)}')
    
    return redirect('delivery_pages:outgoing_document_detail', document_id=document.id)


@login_required
def outgoing_document_complete(request, document_id):
    """完成"""
    from django.shortcuts import redirect, get_object_or_404
    from django.contrib import messages
    from backend.apps.delivery_customer.models import OutgoingDocument
    
    permission_set = get_user_permission_codes(request.user)
    
    document = get_object_or_404(OutgoingDocument, id=document_id)
    
    if request.method == 'POST':
        try:
            comment = request.POST.get('comment', '').strip()
            document.transition_to('completed', actor=request.user, comment=comment or '标记为已完成')
            messages.success(request, '发文已标记为已完成')
        except ValueError as e:
            messages.error(request, str(e))
        except Exception as e:
            logger.error(f"完成操作失败: {str(e)}")
            messages.error(request, f'操作失败：{str(e)}')
    
    return redirect('delivery_pages:outgoing_document_detail', document_id=document.id)


@login_required
def outgoing_document_archive(request, document_id):
    """归档"""
    from django.shortcuts import redirect, get_object_or_404
    from django.contrib import messages
    from backend.apps.delivery_customer.models import OutgoingDocument
    
    permission_set = get_user_permission_codes(request.user)
    
    document = get_object_or_404(OutgoingDocument, id=document_id)
    
    if request.method == 'POST':
        try:
            comment = request.POST.get('comment', '').strip()
            document.transition_to('archived', actor=request.user, comment=comment or '已归档')
            messages.success(request, '发文已归档')
        except ValueError as e:
            messages.error(request, str(e))
        except Exception as e:
            logger.error(f"归档失败: {str(e)}")
            messages.error(request, f'操作失败：{str(e)}')
    
    return redirect('delivery_pages:outgoing_document_detail', document_id=document.id)


@login_required
def outgoing_document_record_remedy(request, document_id):
    """记录补救措施"""
    from django.shortcuts import redirect, get_object_or_404
    from django.contrib import messages
    from backend.apps.delivery_customer.models import OutgoingDocument
    from backend.apps.delivery_customer.services import OutgoingDocumentWarningService
    
    permission_set = get_user_permission_codes(request.user)
    
    document = get_object_or_404(OutgoingDocument, id=document_id)
    
    if request.method == 'POST':
        remedy_action = request.POST.get('remedy_action', '').strip()
        
        if not remedy_action:
            messages.error(request, '补救措施不能为空')
            return redirect('delivery_pages:outgoing_document_detail', document_id=document.id)
        
        try:
            success = OutgoingDocumentWarningService.record_remedy_action(
                document=document,
                remedy_action=remedy_action,
                actor=request.user
            )
            
            if success:
                messages.success(request, '补救措施已记录')
            else:
                messages.error(request, '记录补救措施失败')
        except Exception as e:
            logger.error(f"记录补救措施失败: {str(e)}")
            messages.error(request, f'操作失败：{str(e)}')
    
    return redirect('delivery_pages:outgoing_document_detail', document_id=document.id)


# ==================== 发文签收确认功能 ====================

@login_required
def outgoing_document_receipt_list(request):
    """发文跟踪列表 - 显示所有跟踪记录"""
    from django.core.paginator import Paginator
    from django.db.models import Q
    from backend.apps.delivery_customer.models import OutgoingDocumentTracking, OutgoingDocument, DeliveryMethod
    
    permission_set = get_user_permission_codes(request.user)
    
    # 权限检查
    if not _permission_granted('delivery_center.view', permission_set):
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("无权限访问发文跟踪")
    
    # 获取查询参数（只获取该页面实际使用的参数，忽略无关参数如stage、priority、category等）
    status_filter = request.GET.get('status', '')  # 跟踪状态筛选
    delivery_method_filter = request.GET.get('delivery_method', '')  # 报送方式筛选
    search = request.GET.get('search', '').strip()  # 搜索参数（新模板使用）
    document_number = request.GET.get('document_number', '').strip() or search  # 兼容旧的 document_number 参数
    page_num = request.GET.get('page', 1)
    
    # 检查是否有无关参数（该页面不使用的参数），如果有则重定向到清理后的URL
    allowed_params = {'status', 'delivery_method', 'search', 'document_number', 'page'}
    current_params = set(request.GET.keys())
    unwanted_params = current_params - allowed_params
    
    if unwanted_params:
        # 构建只包含允许参数的URL
        from django.http import HttpResponseRedirect
        from urllib.parse import urlencode
        clean_params = {}
        if status_filter:
            clean_params['status'] = status_filter
        if delivery_method_filter:
            clean_params['delivery_method'] = delivery_method_filter
        if search:
            clean_params['search'] = search
        if page_num and str(page_num) != '1':
            clean_params['page'] = page_num
        
        clean_url = request.path
        if clean_params:
            clean_url += '?' + urlencode(clean_params)
        
        return HttpResponseRedirect(clean_url)
    
    # 基础查询：显示已批准及发出后状态的跟踪记录（含批准和发出）
    # 发文跟踪：显示已批准（可报送）、已发出、已完成、已归档的发文跟踪记录
    queryset = OutgoingDocumentTracking.objects.select_related(
        'document', 'delivery_method', 'created_by', 'hand_delivery_checkin_by'
    ).prefetch_related('document__project', 'document__client').filter(
        document__status__in=['approved', 'sent', 'completed', 'archived']  # 显示已批准、已发出、已完成、已归档的发文跟踪记录
    )
    
    # 状态筛选
    if status_filter:
        queryset = queryset.filter(status=status_filter)
    
    # 报送方式筛选
    if delivery_method_filter:
        queryset = queryset.filter(delivery_method__code=delivery_method_filter)
    
    # 发文编号搜索（支持 search 和 document_number 参数）
    if document_number:
        queryset = queryset.filter(document__document_number__icontains=document_number)
    
    # 排序和分页 - 固定每页最多10行
    queryset = queryset.order_by('-created_at')
    per_page = 10
    paginator = Paginator(queryset, per_page)
    page = paginator.get_page(page_num)
    
    # 获取所有报送方式（用于筛选）
    delivery_methods = DeliveryMethod.objects.filter(is_active=True).order_by('sort_order', 'name')
    
    # 先构建左侧菜单（确保菜单一定存在）
    module_sidebar_nav = _build_delivery_sidebar_nav(permission_set, request.path, active_id='outgoing_document_receipt_list_item')
    
    # 构建上下文（_context函数会自动生成左侧菜单，但我们已经手动构建了，所以会覆盖）
    context = _context(
        "发文跟踪列表",
        "📋",
        "发文跟踪列表",
        request=request,
        active_menu_id='outgoing_document_receipt_list_item',  # 传入正确的active_menu_id
    )
    # 确保左侧菜单已正确设置（使用我们手动构建的菜单，确保一定存在）
    context['module_sidebar_nav'] = module_sidebar_nav
    context["delivery_sidebar_nav"] = module_sidebar_nav  # 兼容旧模板
    
    # 新模板使用 page_obj
    context["page_obj"] = page
    context["tracking_records"] = page  # 保留兼容性，用于遍历
    
    # 搜索参数处理（模板使用 search 参数）
    context["search"] = search or document_number  # 使用 search 或 document_number
    
    context["status_filter"] = status_filter
    context["delivery_method_filter"] = delivery_method_filter
    context["document_number"] = document_number  # 保留兼容性
    context["delivery_methods"] = delivery_methods
    context["can_create"] = False  # 跟踪列表不需要创建按钮
    
    # 添加快递公司列表（用于报送模态框）
    from backend.apps.delivery_customer.models import ExpressCompany
    context["express_companies"] = ExpressCompany.objects.filter(is_active=True).order_by('sort_order', 'name')
    
    # 为每个跟踪记录添加是否可以报送的判断，并同步状态
    status_updated_count = 0
    for tracking in page:
        document = tracking.document
        # 根据时间字段自动同步状态（保存到数据库）
        if tracking.sync_status_from_timestamps(save=True):
            status_updated_count += 1
        # 判断是否可以报送：
        # 1. 发文状态必须是已批准
        # 2. 文档可以流转到已发送状态
        # 3. 跟踪记录状态必须是待发送、发送中或发送失败（允许重新报送）
        #    如果已经是已发送或更高状态，则不能再次报送
        tracking.can_send = (
            document.status == 'approved' and 
            document.can_transition_to('sent') and
            tracking.status in ['pending', 'sending', 'failed']
        )
        
        # 判断报送状态：用于显示"已报送"或"报送失败"
        # 只有真正报送过（有sent_at时间戳）才显示"已报送"
        # 如果跟踪记录状态是已发送或更高，且有发送时间，说明已报送成功
        if tracking.status in ['sent', 'in_transit', 'delivered', 'received', 'completed'] and tracking.sent_at:
            tracking.send_status = 'success'
        # 如果跟踪记录状态是失败，说明报送失败
        elif tracking.status == 'failed':
            tracking.send_status = 'failed'
        # 如果文档状态是已发送，且有发送时间，也认为已报送成功（兼容旧数据）
        elif document.status == 'sent' and document.sent_at:
            tracking.send_status = 'success'
        else:
            tracking.send_status = None
    
    # 如果更新了状态，记录日志
    if status_updated_count > 0:
        logger.info(f"跟踪列表页面自动同步了 {status_updated_count} 条记录的状态")
    
    return render(request, "delivery_customer/outgoing_document_tracking_list.html", context)


@login_required
def outgoing_document_send_from_tracking(request, tracking_id):
    """从跟踪记录直接报送发文（通过模态框提交）"""
    from django.shortcuts import redirect, get_object_or_404
    from django.contrib import messages
    from django.utils import timezone
    from django.http import JsonResponse
    from backend.apps.delivery_customer.models import OutgoingDocumentTracking, OutgoingDocument, DeliveryMethod
    from backend.apps.delivery_customer.tracking_service import TrackingServiceFactory
    import json
    import re
    
    permission_set = get_user_permission_codes(request.user)
    
    # 获取跟踪记录
    tracking = get_object_or_404(
        OutgoingDocumentTracking.objects.select_related('document', 'delivery_method'),
        id=tracking_id
    )
    
    document = tracking.document
    
    # 检查权限
    if not _permission_granted('delivery_center.create', permission_set):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'status': 'error', 'message': '您没有权限报送发文'}, status=403)
        messages.error(request, '您没有权限报送发文')
        return redirect('delivery_pages:outgoing_document_receipt_list')
    
    # 检查发文状态是否可以发送
    if document.status != 'approved':
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'status': 'error', 'message': f'发文状态为"{document.get_status_display()}"，只有已批准的发文才能报送'}, status=400)
        messages.error(request, f'发文状态为"{document.get_status_display()}"，只有已批准的发文才能报送')
        return redirect('delivery_pages:outgoing_document_receipt_list')
    
    if not document.can_transition_to('sent'):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'status': 'error', 'message': '发文当前状态不允许发送'}, status=400)
        messages.error(request, '发文当前状态不允许发送')
        return redirect('delivery_pages:outgoing_document_receipt_list')
    
    # 如果已经发送过，检查是否需要重新发送
    if document.status == 'sent' and tracking.status in ['sent', 'delivered', 'confirmed', 'completed']:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'status': 'warning', 'message': '该发文已经报送过了'}, status=400)
        messages.warning(request, '该发文已经报送过了')
        return redirect('delivery_pages:outgoing_document_receipt_list')
    
    try:
        method_code = tracking.delivery_method.code
        
        # 根据报送方式处理不同的字段
        if method_code == 'email':
            # 邮件：更新邮件主题
            email_subject = request.POST.get('email_subject', '').strip()
            if email_subject:
                tracking.email_subject = email_subject
                tracking.save(update_fields=['email_subject'])
        
        elif method_code == 'express':
            # 快递：更新快递信息
            express_company = request.POST.get('express_company', '').strip()
            express_number = request.POST.get('express_number', '').strip()
            express_fee = request.POST.get('express_fee', '').strip()
            
            if not express_number:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'status': 'error', 'message': '请输入快递单号'}, status=400)
                messages.error(request, '请输入快递单号')
                return redirect('delivery_pages:outgoing_document_receipt_list')
            
            tracking.express_company = express_company
            tracking.express_number = express_number
            
            # 快递费用保存到notes中（如果模型没有express_fee字段）
            if express_fee:
                try:
                    fee_value = float(express_fee)
                    if tracking.notes:
                        tracking.notes += f"\n快递费用: {fee_value:.2f}"
                    else:
                        tracking.notes = f"快递费用: {fee_value:.2f}"
                except ValueError:
                    pass
            
            tracking.save(update_fields=['express_company', 'express_number', 'notes'])
            
            # 调用快递跟踪服务更新信息并查询状态
            from backend.apps.delivery_customer.tracking_service import ExpressTrackingService
            ExpressTrackingService.update_express_info(tracking, express_company, express_number)
        
        elif method_code == 'hand_delivery':
            # 现场送达：更新送达信息
            location = request.POST.get('hand_delivery_location', '').strip()
            latitude = request.POST.get('hand_delivery_latitude', '').strip()
            longitude = request.POST.get('hand_delivery_longitude', '').strip()
            photo = request.FILES.get('hand_delivery_photo')
            
            if not location:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'status': 'error', 'message': '请输入送达地点'}, status=400)
                messages.error(request, '请输入送达地点')
                return redirect('delivery_pages:outgoing_document_receipt_list')
            
            tracking.hand_delivery_location = location
            if latitude:
                try:
                    tracking.hand_delivery_latitude = float(latitude)
                except ValueError:
                    pass
            if longitude:
                try:
                    tracking.hand_delivery_longitude = float(longitude)
                except ValueError:
                    pass
            if photo:
                tracking.hand_delivery_photo = photo
            
            # 调用现场送达服务打卡
            from backend.apps.delivery_customer.tracking_service import HandDeliveryTrackingService
            HandDeliveryTrackingService.checkin(
                tracking, 
                location, 
                tracking.hand_delivery_latitude, 
                tracking.hand_delivery_longitude, 
                photo, 
                request.user
            )
        
        elif method_code == 'sms':
            # 短信：更新短信内容和手机号
            sms_content = request.POST.get('sms_content', '').strip()
            sms_phone = request.POST.get('sms_phone', '').strip()
            
            if not sms_phone:
                # 如果表单中没有手机号，尝试从跟踪记录中获取
                if not tracking.sms_phone:
                    # 如果跟踪记录中也没有，尝试从文档中获取
                    if document.recipient_phone:
                        sms_phone = document.recipient_phone
                    else:
                        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                            return JsonResponse({'status': 'error', 'message': '收件人手机号不能为空'}, status=400)
                        messages.error(request, '收件人手机号不能为空')
                        return redirect('delivery_pages:outgoing_document_receipt_list')
            
            if not sms_content:
                # 如果没有内容，使用默认格式
                sms_content = f"【发文通知】发文编号：{document.document_number}，文件标题：{document.title}。详情请查看邮件或联系我司。"
            
            tracking.sms_phone = sms_phone
            tracking.sms_content = sms_content
            tracking.save(update_fields=['sms_phone', 'sms_content'])
        
        # 重要：只更新当前跟踪记录的状态，不要更新整个文档的状态
        # 因为一个文档可能有多个报送方式，每个报送方式应该独立处理
        # 只有当所有报送方式都发送完成后，文档状态才应该变为 'sent'
        # 注意：只有在确认报送且系统判断为报送成功后，才设置sent_at和状态为sent
        
        # 根据报送方式调用相应的跟踪服务
        service = TrackingServiceFactory.get_service(method_code)
        send_success = False
        send_message = ''
        
        if method_code == 'email':
            # 邮件发送
            success, message = service.send_email(tracking)
            if success:
                # 只有发送成功才设置sent_at和状态
                tracking.status = 'sent'
                tracking.sent_at = timezone.now()
                tracking.save(update_fields=['status', 'sent_at'])
                send_success = True
                send_message = f'发文已通过{tracking.delivery_method.name}报送成功：{message}'
                logger.info(f"从跟踪列表报送发文 {document.document_number} 邮件发送成功: {message}")
            else:
                # 发送失败，不设置sent_at，只更新状态为failed
                tracking.status = 'failed'
                tracking.error_message = message
                tracking.save(update_fields=['status', 'error_message'])
                send_message = f'{tracking.delivery_method.name}发送失败：{message}'
                logger.error(f"从跟踪列表报送发文 {document.document_number} 邮件发送失败: {message}")
        
        elif method_code == 'express':
            # 快递：验证数据完整性，只有验证通过才认为报送成功
            if not tracking.express_number:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'status': 'error', 'message': '快递单号不能为空'}, status=400)
                messages.error(request, '快递单号不能为空')
                return redirect('delivery_pages:outgoing_document_receipt_list')
            
            if not tracking.express_company:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'status': 'error', 'message': '快递公司不能为空'}, status=400)
                messages.error(request, '快递公司不能为空')
                return redirect('delivery_pages:outgoing_document_receipt_list')
            
            # 数据验证通过，认为报送成功
            tracking.status = 'sent'
            tracking.sent_at = timezone.now()
            tracking.save(update_fields=['status', 'sent_at'])
            send_success = True
            send_message = f'发文已通过{tracking.delivery_method.name}报送成功，快递单号：{tracking.express_number}'
            logger.info(f"从跟踪列表报送发文 {document.document_number} 快递跟踪记录已创建，单号：{tracking.express_number}")
        
        elif method_code == 'hand_delivery':
            # 现场送达：checkin方法已经更新了status和received_at
            # 检查checkin是否成功（status应该是delivered）
            if tracking.status == 'delivered' and tracking.hand_delivery_location:
                # 打卡成功，设置sent_at
                tracking.sent_at = timezone.now()
                tracking.save(update_fields=['sent_at'])
                send_success = True
                send_message = f'发文已通过{tracking.delivery_method.name}报送成功，送达地点：{tracking.hand_delivery_location}'
                logger.info(f"从跟踪列表报送发文 {document.document_number} 现场送达跟踪记录已创建，地点：{tracking.hand_delivery_location}")
            else:
                # 打卡失败，不设置sent_at
                tracking.status = 'failed'
                tracking.error_message = '现场送达打卡失败'
                tracking.save(update_fields=['status', 'error_message'])
                send_message = f'{tracking.delivery_method.name}打卡失败，请重试'
                logger.error(f"从跟踪列表报送发文 {document.document_number} 现场送达打卡失败")
        
        elif method_code == 'sms':
            # 短信发送
            if not tracking.sms_phone:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'status': 'error', 'message': '收件人手机号不能为空'}, status=400)
                messages.error(request, '收件人手机号不能为空')
                return redirect('delivery_pages:outgoing_document_receipt_list')
            
            if not tracking.sms_content:
                # 如果没有内容，使用默认格式
                tracking.sms_content = f"【发文通知】发文编号：{document.document_number}，文件标题：{document.title}。详情请查看邮件或联系我司。"
                tracking.save(update_fields=['sms_content'])
            
            # 调用短信发送服务
            success, message = service.send_sms(tracking)
            if success:
                # 只有发送成功才设置sent_at和状态
                tracking.status = 'sent'
                tracking.sent_at = timezone.now()
                tracking.save(update_fields=['status', 'sent_at', 'sms_sent_at'])
                send_success = True
                send_message = f'发文已通过{tracking.delivery_method.name}报送成功：{message}'
                logger.info(f"从跟踪列表报送发文 {document.document_number} 短信发送成功: {message}")
            else:
                # 发送失败，不设置sent_at，只更新状态为failed
                tracking.status = 'failed'
                tracking.error_message = message
                tracking.save(update_fields=['status', 'error_message'])
                send_message = f'{tracking.delivery_method.name}发送失败：{message}'
                logger.error(f"从跟踪列表报送发文 {document.document_number} 短信发送失败: {message}")
        
        elif method_code == 'yisign':
            # 易签宝：更新跟踪记录状态，等待创建合同
            # 易签宝方式认为报送成功（因为只需要标记为已发送）
            tracking.status = 'pending'
            tracking.sent_at = timezone.now()
            tracking.save(update_fields=['status', 'sent_at'])
            send_success = True
            send_message = f'发文已标记为已发送，请创建{tracking.delivery_method.name}合同'
            logger.info(f"从跟踪列表报送发文 {document.document_number} 易签宝跟踪记录已创建")
        
        else:
            # 其他报送方式：默认认为报送成功
            tracking.status = 'pending'
            tracking.sent_at = timezone.now()
            tracking.save(update_fields=['status', 'sent_at'])
            send_success = True
            send_message = f'发文已标记为已发送，{tracking.delivery_method.name}跟踪记录已创建'
            logger.info(f"从跟踪列表报送发文 {document.document_number} {tracking.delivery_method.name} 跟踪记录已创建")
        
        # 根据报送结果返回响应
        if send_success:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'status': 'success', 'message': send_message})
            messages.success(request, send_message)
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'status': 'warning', 'message': send_message}, status=400)
            messages.warning(request, send_message)
            return redirect('delivery_pages:outgoing_document_receipt_list')
        
        # 检查是否所有报送方式都已发送，如果是，则更新文档状态
        # 只有当所有跟踪记录都已发送（status为sent、delivered、confirmed、completed）时，文档状态才变为sent
        all_tracking_records = document.tracking_records.all()
        if all_tracking_records.exists():
            all_sent = all(
                t.status in ['sent', 'delivered', 'confirmed', 'completed', 'in_transit'] 
                for t in all_tracking_records
            )
            if all_sent and document.status != 'sent':
                # 只有当所有报送方式都已发送时，才更新文档状态
                document.send_date = timezone.now().date()
                document.send_method = ', '.join([t.delivery_method.name for t in all_tracking_records])
                document.sent_at = timezone.now()
                document.save(update_fields=['send_date', 'send_method', 'sent_at'])
                # 注意：这里不调用transition_to，因为可能已经发送过了
                logger.info(f"所有报送方式已发送，文档 {document.document_number} 状态已更新")
    
    except ValueError as e:
        logger.error(f"不支持的报送方式: {method_code} - {str(e)}")
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'status': 'error', 'message': f'不支持的报送方式：{str(e)}'}, status=400)
        messages.error(request, f'不支持的报送方式：{str(e)}')
    except Exception as e:
        logger.error(f"从跟踪列表报送发文失败: {str(e)}", exc_info=True)
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'status': 'error', 'message': f'报送失败：{str(e)}'}, status=500)
        messages.error(request, f'报送失败：{str(e)}')
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'status': 'success', 'message': '报送成功'})
    return redirect('delivery_pages:outgoing_document_receipt_list')


@login_required
def get_tracking_recipients(request, tracking_id):
    """获取跟踪记录的详细信息（用于模态框显示和填充）"""
    from django.shortcuts import get_object_or_404
    from django.http import JsonResponse
    from backend.apps.delivery_customer.models import OutgoingDocumentTracking
    import json
    import re
    
    permission_set = get_user_permission_codes(request.user)
    
    # 检查权限
    if not _permission_granted('delivery_center.view', permission_set):
        return JsonResponse({'status': 'error', 'message': '您没有权限查看跟踪记录信息'}, status=403)
    
    # 获取跟踪记录
    tracking = get_object_or_404(
        OutgoingDocumentTracking.objects.select_related('document', 'delivery_method'),
        id=tracking_id
    )
    
    result = {
        'email_recipients': [],
        'express_recipients': [],
        'sms_recipients': [],
        'email_subject': tracking.email_subject or '',
        'express_company': tracking.express_company or '',
        'express_number': tracking.express_number or '',
        'express_fee': '',
        'hand_delivery_location': tracking.hand_delivery_location or '',
        'hand_delivery_latitude': str(tracking.hand_delivery_latitude) if tracking.hand_delivery_latitude else '',
        'hand_delivery_longitude': str(tracking.hand_delivery_longitude) if tracking.hand_delivery_longitude else '',
        'sms_phone': tracking.sms_phone or '',
        'sms_content': tracking.sms_content or '',
    }
    
    # 解析邮件收件人
    if tracking.notes and 'EMAIL_RECIPIENTS_JSON:' in tracking.notes:
        email_json_match = re.search(r'EMAIL_RECIPIENTS_JSON:\s*(\[.*?\])', tracking.notes, re.DOTALL)
        if email_json_match:
            json_part = email_json_match.group(1)
            try:
                result['email_recipients'] = json.loads(json_part)
            except (json.JSONDecodeError, ValueError):
                pass
    
    # 解析快递收件人
    if tracking.notes and 'EXPRESS_RECIPIENTS_JSON:' in tracking.notes:
        express_json_match = re.search(r'EXPRESS_RECIPIENTS_JSON:\s*(\[.*?\])', tracking.notes, re.DOTALL)
        if express_json_match:
            json_part = express_json_match.group(1)
            try:
                result['express_recipients'] = json.loads(json_part)
            except (json.JSONDecodeError, ValueError):
                pass
    
    # 从notes中解析快递费用（如果模型没有express_fee字段）
    if tracking.notes and '快递费用:' in tracking.notes:
        fee_match = re.search(r'快递费用:\s*([\d.]+)', tracking.notes)
        if fee_match:
            result['express_fee'] = fee_match.group(1)
    
    # 解析短信收件人（如果notes中有SMS_RECIPIENTS_JSON）
    if tracking.notes and 'SMS_RECIPIENTS_JSON:' in tracking.notes:
        sms_json_match = re.search(r'SMS_RECIPIENTS_JSON:\s*(\[.*?\])', tracking.notes, re.DOTALL)
        if sms_json_match:
            json_part = sms_json_match.group(1)
            try:
                result['sms_recipients'] = json.loads(json_part)
            except (json.JSONDecodeError, ValueError):
                pass
    elif tracking.sms_phone:
        # 如果有单个手机号，直接返回
        result['sms_phone'] = tracking.sms_phone
        # 尝试从文档中获取收件人姓名
        if tracking.document:
            result['sms_recipients'] = [{
                'name': tracking.document.recipient_contact or tracking.document.recipient or '',
                'phone': tracking.sms_phone
            }]
    
    return JsonResponse(result)


@login_required
def outgoing_document_tracking_detail(request, tracking_id):
    """发文跟踪详情"""
    from django.shortcuts import get_object_or_404
    from backend.apps.delivery_customer.models import OutgoingDocumentTracking
    from backend.apps.delivery_customer.tracking_service import TrackingServiceFactory
    
    permission_set = get_user_permission_codes(request.user)
    
    # 权限检查
    if not _permission_granted('delivery_center.view', permission_set):
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("无权限访问发文跟踪详情")
    
    # 获取跟踪记录
    tracking = get_object_or_404(
        OutgoingDocumentTracking.objects.select_related(
            'document', 'delivery_method', 'created_by', 'hand_delivery_checkin_by'
        ).prefetch_related('document__project', 'document__client'),
        id=tracking_id
    )
    
    # 如果是快递方式，自动同步快递信息（如果tracking中没有但document中有）
    if tracking.delivery_method and tracking.delivery_method.code == 'express':
        update_fields = []
        document = tracking.document
        if document:
            if not tracking.express_company and document.express_company:
                tracking.express_company = document.express_company
                update_fields.append('express_company')
            if not tracking.express_number and document.express_number:
                tracking.express_number = document.express_number
                update_fields.append('express_number')
            if update_fields:
                tracking.save(update_fields=update_fields)
                logger.info(f"自动同步快递信息到跟踪记录: tracking_id={tracking.id}, 字段={update_fields}")
    
    # 根据报送方式获取跟踪服务
    tracking_service = None
    try:
        tracking_service = TrackingServiceFactory.get_service(tracking.delivery_method.code)
    except ValueError:
        pass
    
    # 先构建左侧菜单（确保菜单一定存在）
    module_sidebar_nav = _build_delivery_sidebar_nav(permission_set, request.path, active_id='outgoing_document_receipt_list_item')
    
    # 构建上下文（_context函数会自动生成左侧菜单，但我们已经手动构建了，所以会覆盖）
    context = _context(
        "发文跟踪详情",
        "📋",
        f"{tracking.document.document_number} - {tracking.delivery_method.name}",
        request=request,
        active_menu_id='outgoing_document_receipt_list_item',  # 传入正确的active_menu_id
    )
    # 确保左侧菜单已正确设置（使用我们手动构建的菜单，确保一定存在）
    context['module_sidebar_nav'] = module_sidebar_nav
    context["delivery_sidebar_nav"] = module_sidebar_nav
    context["tracking"] = tracking
    context["document"] = tracking.document  # 明确传递 document 变量，方便模板使用
    context["tracking_service"] = tracking_service
    
    # 清理备注：移除技术性的 JSON 数据，只保留用户输入的备注
    if tracking.notes:
        import re
        cleaned_notes = tracking.notes
        # 移除 EXPRESS_RECIPIENTS_JSON 部分
        cleaned_notes = re.sub(r'EXPRESS_RECIPIENTS_JSON:\s*\[.*?\]\s*', '', cleaned_notes, flags=re.DOTALL)
        # 移除 EMAIL_RECIPIENTS_JSON 部分
        cleaned_notes = re.sub(r'EMAIL_RECIPIENTS_JSON:\s*\[.*?\]\s*', '', cleaned_notes, flags=re.DOTALL)
        # 移除 EMAIL_RECIPIENTS 部分（旧格式）
        cleaned_notes = re.sub(r'EMAIL_RECIPIENTS:\s*[^\n]+\s*', '', cleaned_notes)
        # 清理多余的空白行
        cleaned_notes = cleaned_notes.strip()
        context["tracking_notes_cleaned"] = cleaned_notes if cleaned_notes else None
    else:
        context["tracking_notes_cleaned"] = None
    
    # 获取启用的快递公司列表（用于下拉选择）
    from backend.apps.delivery_customer.models import ExpressCompany
    express_companies = ExpressCompany.objects.filter(is_active=True).order_by('sort_order', 'name')
    context["express_companies"] = express_companies
    
    # 判断当前快递公司是否在列表中（用于模板判断是否选择"其他"）
    current_express_company = tracking.express_company or (tracking.document.express_company if tracking.document else '')
    context["is_express_company_in_list"] = current_express_company and express_companies.filter(name=current_express_company).exists()
    context["current_express_company"] = current_express_company
    
    return render(request, "delivery_customer/outgoing_document_tracking_detail.html", context)


@login_required
def update_tracking_express_info(request, tracking_id):
    """更新跟踪记录的快递信息"""
    from django.shortcuts import get_object_or_404, redirect
    from django.contrib import messages
    from backend.apps.delivery_customer.models import OutgoingDocumentTracking
    from backend.apps.delivery_customer.tracking_service import ExpressTrackingService
    
    permission_set = get_user_permission_codes(request.user)
    
    # 权限检查
    if not _permission_granted('delivery_center.view', permission_set):
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("无权限访问")
    
    # 获取跟踪记录
    tracking = get_object_or_404(
        OutgoingDocumentTracking.objects.select_related('document', 'delivery_method'),
        id=tracking_id
    )
    
    # 检查是否为快递方式
    if not tracking.delivery_method or tracking.delivery_method.code != 'express':
        messages.error(request, '此跟踪记录不是快递方式，无法更新快递信息')
        return redirect('delivery_pages:outgoing_document_tracking_detail', tracking_id=tracking_id)
    
    if request.method == 'POST':
        # 优先使用手动输入的快递公司名称，如果没有则使用下拉选择的值
        # 如果选择了"其他"选项，JavaScript会将手动输入的值放在 express_company 字段中
        express_company = request.POST.get('express_company', '').strip()
        # 如果 express_company 是 __other__，说明应该使用 express_company_other 的值
        if express_company == '__other__':
            express_company = request.POST.get('express_company_other', '').strip()
        express_number = request.POST.get('express_number', '').strip()
        
        if not express_number:
            messages.error(request, '请输入快递单号')
            return redirect('delivery_pages:outgoing_document_tracking_detail', tracking_id=tracking_id)
        
        try:
            # 更新快递信息
            success, message = ExpressTrackingService.update_express_info(
                tracking, express_company, express_number
            )
            
            if success:
                messages.success(request, f'快递信息已更新：{message}')
                # 同时更新到文档（如果文档中没有）
                document = tracking.document
                if document:
                    update_fields = []
                    if not document.express_company and express_company:
                        document.express_company = express_company
                        update_fields.append('express_company')
                    if not document.express_number and express_number:
                        document.express_number = express_number
                        update_fields.append('express_number')
                    if update_fields:
                        document.save(update_fields=update_fields)
                        logger.info(f"同步快递信息到文档: document_id={document.id}, 字段={update_fields}")
            else:
                messages.warning(request, f'快递信息已保存，但查询状态失败：{message}')
            
            logger.info(f"更新跟踪记录快递信息: tracking_id={tracking_id}, 快递公司={express_company}, 快递单号={express_number}")
            
        except Exception as e:
            logger.error(f"更新跟踪记录快递信息失败: {str(e)}", exc_info=True)
            messages.error(request, f'更新失败：{str(e)}')
    
    return redirect('delivery_pages:outgoing_document_tracking_detail', tracking_id=tracking_id)


@login_required
def hand_delivery_checkin(request, tracking_id):
    """现场送达打卡API"""
    from django.shortcuts import get_object_or_404
    from django.http import JsonResponse
    from backend.apps.delivery_customer.models import OutgoingDocumentTracking
    from backend.apps.delivery_customer.tracking_service import HandDeliveryTrackingService
    import json
    import logging
    
    logger = logging.getLogger(__name__)
    
    # 权限检查
    permission_set = get_user_permission_codes(request.user)
    if not _permission_granted('delivery_center.view', permission_set):
        return JsonResponse({'success': False, 'message': '无权限操作'}, status=403)
    
    # 获取跟踪记录
    tracking = get_object_or_404(
        OutgoingDocumentTracking.objects.select_related('delivery_method'),
        id=tracking_id
    )
    
    # 检查是否是现场送达方式
    if tracking.delivery_method.code != 'hand_delivery':
        return JsonResponse({'success': False, 'message': '该跟踪记录不是现场送达方式'}, status=400)
    
    # 只接受POST请求
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': '只支持POST请求'}, status=405)
    
    try:
        # 获取参数
        location = request.POST.get('location', '').strip()
        latitude = request.POST.get('latitude', '').strip()
        longitude = request.POST.get('longitude', '').strip()
        photo = request.FILES.get('photo')
        
        # 验证必填字段
        if not location:
            return JsonResponse({'success': False, 'message': '请填写送达地点'}, status=400)
        
        if not latitude or not longitude:
            return JsonResponse({'success': False, 'message': '请获取GPS定位'}, status=400)
        
        try:
            latitude = float(latitude)
            longitude = float(longitude)
        except ValueError:
            return JsonResponse({'success': False, 'message': '经纬度格式不正确'}, status=400)
        
        # 调用打卡服务
        success, message = HandDeliveryTrackingService.checkin(
            tracking=tracking,
            location=location,
            latitude=latitude,
            longitude=longitude,
            photo=photo,
            user=request.user
        )
        
        if success:
            return JsonResponse({
                'success': True,
                'message': message,
                'data': {
                    'location': tracking.hand_delivery_location,
                    'latitude': str(tracking.hand_delivery_latitude),
                    'longitude': str(tracking.hand_delivery_longitude),
                    'checkin_at': tracking.hand_delivery_checkin_at.isoformat() if tracking.hand_delivery_checkin_at else None,
                    'checkin_by': tracking.hand_delivery_checkin_by.username if tracking.hand_delivery_checkin_by else None,
                    'status': tracking.status,
                }
            })
        else:
            return JsonResponse({'success': False, 'message': message}, status=400)
            
    except Exception as e:
        logger.error(f"现场送达打卡失败: {str(e)}", exc_info=True)
        return JsonResponse({'success': False, 'message': f'打卡失败：{str(e)}'}, status=500)


@login_required
def outgoing_document_receipt_confirm(request, document_id):
    """发文签收确认操作"""
    from django.shortcuts import redirect, get_object_or_404
    from django.contrib import messages
    from django.utils import timezone
    from backend.apps.delivery_customer.models import OutgoingDocument
    
    permission_set = get_user_permission_codes(request.user)
    
    # 权限检查
    if not _permission_granted('delivery_center.view', permission_set):
        messages.error(request, '您没有签收确认的权限')
        return redirect('delivery_pages:outgoing_document_receipt_list')
    
    document = get_object_or_404(OutgoingDocument, id=document_id)
    
    # GET请求：显示签收确认页面
    if request.method == 'GET':
        module_sidebar_nav = _build_delivery_sidebar_nav(permission_set, request.path)
        delivery_sidebar_nav = module_sidebar_nav  # 兼容旧模板
        
        context = _context(
            "发文签收确认",
            "✅",
            "确认发文签收",
            request=request,
        )
        context["module_sidebar_nav"] = module_sidebar_nav
        context["delivery_sidebar_nav"] = module_sidebar_nav  # 兼容旧模板
        context["document"] = document
        context["can_confirm"] = not document.is_receipt_confirmed and document.status in ['sent', 'completed']
        
        return render(request, "delivery_customer/outgoing_document_receipt_confirm.html", context)
    
    # POST请求：执行签收确认
    if request.method == 'POST':
        action = request.POST.get('action', '')  # confirm 或 reject
        
        if action == 'confirm':
            try:
                # 签收确认信息
                receipt_method = request.POST.get('receipt_method', '').strip()
                receipt_by = request.POST.get('receipt_by', '').strip()
                receipt_phone = request.POST.get('receipt_phone', '').strip()
                receipt_email = request.POST.get('receipt_email', '').strip()
                receipt_comment = request.POST.get('receipt_comment', '').strip()
                receipt_date = request.POST.get('receipt_date', '').strip()
                
                # 处理签收凭证
                receipt_signature = request.FILES.get('receipt_signature', None)
                
                # 验证必填字段
                if not receipt_by:
                    messages.error(request, '签收人姓名不能为空')
                    return redirect('delivery_pages:outgoing_document_receipt_confirm', document_id=document.id)
                
                # 更新签收信息
                document.receipt_method = receipt_method or '纸质签收'
                document.receipt_by = receipt_by
                document.receipt_phone = receipt_phone
                document.receipt_email = receipt_email
                document.receipt_comment = receipt_comment
                
                if receipt_signature:
                    document.receipt_signature = receipt_signature
                
                # 设置签收时间
                if receipt_date:
                    from django.utils.dateparse import parse_datetime, parse_date
                    import datetime
                    receipt_datetime = parse_datetime(receipt_date) or parse_date(receipt_date)
                    if receipt_datetime:
                        if isinstance(receipt_datetime, datetime.datetime):
                            document.received_at = receipt_datetime
                            document.confirmed_at = receipt_datetime
                        else:
                            dt = datetime.datetime.combine(receipt_datetime, datetime.datetime.min.time())
                            document.received_at = timezone.make_aware(dt) if timezone.is_naive(dt) else dt
                            document.confirmed_at = timezone.make_aware(dt) if timezone.is_naive(dt) else dt
                else:
                    now = timezone.now()
                    if not document.received_at:
                        document.received_at = now
                    document.confirmed_at = now
                
                # 标记为已签收
                document.is_receipt_confirmed = True
                document.receipt_confirmed_by = request.user
                document.save()
                
                # 记录状态流转日志
                try:
                    document.transition_to('completed', actor=request.user, comment=f'签收确认：{receipt_comment or "无备注"}')
                except ValueError:
                    # 如果状态流转失败（如已经是completed），只记录日志但不改变状态
                    pass
                
                # 记录签收确认到状态日志
                from django.apps import apps
                try:
                    StatusLog = apps.get_model('delivery_customer', 'OutgoingDocumentStatusLog')
                    StatusLog.objects.create(
                        document=document,
                        from_status=document.status,
                        to_status=document.status,  # 状态不变，只是记录签收确认
                        actor=request.user,
                        comment=f'签收确认 - 签收人：{receipt_by}，签收方式：{receipt_method or "纸质签收"}',
                    )
                except Exception:
                    pass
                
                messages.success(request, '发文签收确认成功')
                return redirect('delivery_pages:outgoing_document_receipt_list')
                
            except Exception as e:
                logger.error(f"签收确认失败: {str(e)}")
                messages.error(request, f'签收确认失败：{str(e)}')
                return redirect('delivery_pages:outgoing_document_receipt_confirm', document_id=document.id)
        
        elif action == 'reject':
            # 拒收处理（可选功能）
            reject_reason = request.POST.get('reject_reason', '').strip()
            if not reject_reason:
                messages.error(request, '拒收原因不能为空')
                return redirect('delivery_pages:outgoing_document_receipt_confirm', document_id=document.id)
            
            document.receipt_comment = f'拒收原因：{reject_reason}'
            document.save()
            
            messages.warning(request, '已标记为拒收')
            return redirect('delivery_pages:outgoing_document_receipt_list')
    
    return redirect('delivery_pages:outgoing_document_receipt_list')


# ==================== 发文效能报告 ====================

@login_required
def outgoing_document_performance_report(request):
    """发文效能报告"""
    from django.utils.dateparse import parse_date
    from backend.apps.delivery_customer.services import OutgoingDocumentReportService
    from backend.apps.delivery_customer.models import OutgoingDocument
    
    permission_set = get_user_permission_codes(request.user)
    
    # 权限检查
    if not _permission_granted('delivery_center.view', permission_set):
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("无权限查看效能报告")
    
    # 获取查询参数
    start_date_str = request.GET.get('start_date', '')
    end_date_str = request.GET.get('end_date', '')
    responsible_person_id = request.GET.get('responsible_person', '')
    
    # 解析日期
    start_date = parse_date(start_date_str) if start_date_str else None
    end_date = parse_date(end_date_str) if end_date_str else None
    
    # 解析责任人ID
    responsible_person_id = int(responsible_person_id) if responsible_person_id else None
    
    # 获取责任人列表（用于筛选）
    from django.contrib.auth import get_user_model
    User = get_user_model()
    responsible_persons = User.objects.filter(
        responsible_outgoing_documents__isnull=False
    ).distinct().order_by('username')
    
    # 生成报告
    report_data = OutgoingDocumentReportService.generate_performance_report(
        start_date=start_date,
        end_date=end_date,
        responsible_person_id=responsible_person_id
    )
    
    # 格式化状态和优先级显示
    status_labels = dict(OutgoingDocument.STATUS_CHOICES)
    priority_labels = dict(OutgoingDocument.PRIORITY_CHOICES)
    
    # 格式化报告数据中的状态和优先级
    formatted_by_status = {}
    for status_code, count in report_data['summary']['by_status'].items():
        formatted_by_status[status_labels.get(status_code, status_code)] = count
    
    formatted_by_priority = {}
    for priority_code, count in report_data['summary']['by_priority'].items():
        formatted_by_priority[priority_labels.get(priority_code, priority_code)] = count
    
    # 添加左侧菜单
    module_sidebar_nav = _build_delivery_sidebar_nav(permission_set, request.path)
    delivery_sidebar_nav = module_sidebar_nav  # 兼容旧模板
    
    context = _context(
        "发文效能报告",
        "📊",
        "查看发文效能统计分析报告",
        request=request,
    )
    context["module_sidebar_nav"] = module_sidebar_nav
    context["delivery_sidebar_nav"] = module_sidebar_nav  # 兼容旧模板
    context["report_data"] = report_data
    context["formatted_by_status"] = formatted_by_status
    context["formatted_by_priority"] = formatted_by_priority
    context["responsible_persons"] = responsible_persons
    context["start_date"] = start_date_str
    context["end_date"] = end_date_str
    context["selected_responsible_person_id"] = responsible_person_id
    
    return render(request, "delivery_customer/outgoing_document_performance_report.html", context)


@login_required
def outgoing_document_audit_trail(request, document_id):
    """发文审计追踪详情"""
    from django.shortcuts import get_object_or_404
    from backend.apps.delivery_customer.models import OutgoingDocument
    from backend.apps.delivery_customer.services import OutgoingDocumentAuditService
    
    permission_set = get_user_permission_codes(request.user)
    
    # 权限检查
    if not _permission_granted('delivery_center.view', permission_set):
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("无权限查看审计追踪")
    
    document = get_object_or_404(OutgoingDocument, id=document_id)
    
    # 获取审计追踪记录和时间线
    audit_trail = OutgoingDocumentAuditService.get_document_audit_trail(document)
    timeline_data = OutgoingDocumentAuditService.get_document_timeline(document)
    
    # 添加左侧菜单
    module_sidebar_nav = _build_delivery_sidebar_nav(permission_set, request.path)
    delivery_sidebar_nav = module_sidebar_nav  # 兼容旧模板
    
    context = _context(
        f"发文审计追踪 - {document.document_number}",
        "🔍",
        f"查看发文 {document.document_number} 的完整审计追踪记录",
        request=request,
    )
    context["module_sidebar_nav"] = module_sidebar_nav
    context["delivery_sidebar_nav"] = module_sidebar_nav  # 兼容旧模板
    context["document"] = document
    context["audit_trail"] = audit_trail
    context["timeline_data"] = timeline_data
    
    return render(request, "delivery_customer/outgoing_document_audit_trail.html", context)


@login_required
def outgoing_document_audit_query(request):
    """发文审计日志查询"""
    from django.utils.dateparse import parse_date
    from backend.apps.delivery_customer.services import OutgoingDocumentAuditService
    from django.contrib.auth import get_user_model
    
    User = get_user_model()
    
    permission_set = get_user_permission_codes(request.user)
    
    # 权限检查
    if not _permission_granted('delivery_center.view', permission_set):
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("无权限查看审计日志")
    
    # 获取查询参数
    document_number = request.GET.get('document_number', '').strip()
    actor_id = request.GET.get('actor', '')
    action_type = request.GET.get('action_type', '')
    start_date_str = request.GET.get('start_date', '')
    end_date_str = request.GET.get('end_date', '')
    
    # 解析参数
    actor_id = int(actor_id) if actor_id else None
    start_date = parse_date(start_date_str) if start_date_str else None
    end_date = parse_date(end_date_str) if end_date_str else None
    
    # 获取所有用户（用于筛选）
    users = User.objects.all().order_by('username')
    
    # 查询审计日志
    audit_logs = []
    if request.GET:  # 只有在有查询参数时才执行查询
        audit_logs = OutgoingDocumentAuditService.query_audit_logs(
            document_number=document_number if document_number else None,
            actor_id=actor_id,
            action_type=action_type if action_type else None,
            start_date=start_date,
            end_date=end_date,
            limit=100  # 限制返回100条
        )
    
    # 添加左侧菜单
    module_sidebar_nav = _build_delivery_sidebar_nav(permission_set, request.path)
    delivery_sidebar_nav = module_sidebar_nav  # 兼容旧模板
    
    context = _context(
        "发文审计日志查询",
        "📋",
        "多维度查询发文审计日志",
        request=request,
    )
    context["module_sidebar_nav"] = module_sidebar_nav
    context["delivery_sidebar_nav"] = module_sidebar_nav  # 兼容旧模板
    context["audit_logs"] = audit_logs
    context["users"] = users
    context["document_number"] = document_number
    context["selected_actor_id"] = actor_id
    context["selected_action_type"] = action_type
    context["start_date"] = start_date_str
    context["end_date"] = end_date_str
    
    # 操作类型选项
    context["action_types"] = [
        ('status_change', '状态变更'),
        ('receipt', '签收确认'),
        ('warning', '延迟预警'),
        ('remedy', '补救措施'),
        ('archive', '归档'),
        ('create', '创建'),
    ]
    
    return render(request, "delivery_customer/outgoing_document_audit_query.html", context)


@login_required
def outgoing_document_performance_list(request):
    """发文责任人绩效统计"""
    from django.utils.dateparse import parse_date
    from backend.apps.delivery_customer.services import OutgoingDocumentPerformanceService
    from django.contrib.auth import get_user_model
    
    User = get_user_model()
    
    permission_set = get_user_permission_codes(request.user)
    
    # 权限检查
    if not _permission_granted('delivery_center.view', permission_set):
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("无权限查看绩效统计")
    
    # 获取查询参数
    start_date_str = request.GET.get('start_date', '')
    end_date_str = request.GET.get('end_date', '')
    user_id = request.GET.get('user_id', '')
    
    # 解析参数
    start_date = parse_date(start_date_str) if start_date_str else None
    end_date = parse_date(end_date_str) if end_date_str else None
    user_id = int(user_id) if user_id else None
    
    # 获取所有有发文的责任人（用于筛选）
    from backend.apps.delivery_customer.models import OutgoingDocument
    responsible_persons = User.objects.filter(
        responsible_outgoing_documents__isnull=False
    ).distinct().order_by('username')
    
    # 获取绩效数据
    if user_id:
        # 查看特定责任人的绩效
        performance_data = OutgoingDocumentPerformanceService.get_responsible_person_performance(
            user_id=user_id,
            start_date=start_date,
            end_date=end_date
        )
        performance_list = [performance_data]  # 单个用户，转为列表格式
    else:
        # 查看所有责任人的绩效排名
        performance_list = OutgoingDocumentPerformanceService.get_all_responsible_persons_performance(
            start_date=start_date,
            end_date=end_date,
            limit=50  # 限制显示前50名
        )
    
    # 添加左侧菜单
    module_sidebar_nav = _build_delivery_sidebar_nav(permission_set, request.path)
    delivery_sidebar_nav = module_sidebar_nav  # 兼容旧模板
    
    context = _context(
        "发文责任人绩效统计",
        "📈",
        "查看发文责任人的绩效统计和排名",
        request=request,
    )
    context["module_sidebar_nav"] = module_sidebar_nav
    context["delivery_sidebar_nav"] = module_sidebar_nav  # 兼容旧模板
    context["performance_list"] = performance_list
    context["responsible_persons"] = responsible_persons
    context["start_date"] = start_date_str
    context["end_date"] = end_date_str
    context["selected_user_id"] = user_id
    
    return render(request, "delivery_customer/outgoing_document_performance_list.html", context)


@login_required
def outgoing_document_performance_detail(request, user_id):
    """发文责任人绩效详情"""
    from django.utils.dateparse import parse_date
    from django.contrib.auth import get_user_model
    from backend.apps.delivery_customer.services import OutgoingDocumentPerformanceService
    
    User = get_user_model()
    
    permission_set = get_user_permission_codes(request.user)
    
    # 权限检查
    if not _permission_granted('delivery_center.view', permission_set):
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("无权限查看绩效详情")
    
    # 获取查询参数
    start_date_str = request.GET.get('start_date', '')
    end_date_str = request.GET.get('end_date', '')
    
    # 解析参数
    start_date = parse_date(start_date_str) if start_date_str else None
    end_date = parse_date(end_date_str) if end_date_str else None
    
    # 获取用户信息
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        from django.http import Http404
        raise Http404("用户不存在")
    
    # 获取绩效数据
    performance_data = OutgoingDocumentPerformanceService.get_responsible_person_performance(
        user_id=user_id,
        start_date=start_date,
        end_date=end_date
    )
    
    # 添加左侧菜单
    module_sidebar_nav = _build_delivery_sidebar_nav(permission_set, request.path)
    delivery_sidebar_nav = module_sidebar_nav  # 兼容旧模板
    
    context = _context(
        f"绩效详情 - {performance_data['user_name']}",
        "📊",
        f"查看 {performance_data['user_name']} 的发文绩效详情",
        request=request,
    )
    context["module_sidebar_nav"] = module_sidebar_nav
    context["delivery_sidebar_nav"] = module_sidebar_nav  # 兼容旧模板
    context["performance_data"] = performance_data
    context["user"] = user
    context["start_date"] = start_date_str
    context["end_date"] = end_date_str
    
    return render(request, "delivery_customer/outgoing_document_performance_detail.html", context)


# ==================== 快递公司管理 ====================

@login_required
def express_company_list(request):
    """快递公司列表"""
    from django.core.paginator import Paginator
    from django.db.models import Q
    from backend.apps.delivery_customer.models import ExpressCompany
    
    permission_set = get_user_permission_codes(request.user)
    
    # 获取查询参数
    search = request.GET.get('search', '').strip()
    status_filter = request.GET.get('status', '')  # 空字符串表示全部
    
    # 查询快递公司
    companies = ExpressCompany.objects.all().order_by('sort_order', 'name')
    
    # 搜索过滤
    if search:
        companies = companies.filter(
            Q(name__icontains=search) |
            Q(code__icontains=search) |
            Q(alias__icontains=search) |
            Q(contact_phone__icontains=search)
        )
    
    # 状态过滤
    if status_filter == 'active':
        companies = companies.filter(is_active=True)
    elif status_filter == 'inactive':
        companies = companies.filter(is_active=False)
    
    # 分页（固定为每页 10 条，符合 list_page_base.html 模板规定）
    per_page = 10
    paginator = Paginator(companies, per_page)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # 构建上下文（符合 list_page_base.html 模板要求）
    context = _context(
        "快递公司列表",
        "🚚",
        "管理快递公司信息",
        request=request,
        active_menu_id='express_company_list',
    )
    # 列表模板必需字段
    context.update({
        'page_obj': page_obj,  # 分页对象，包含 object_list
        'page_title': '快递公司列表',  # 页面标题
        'search': search,  # 搜索关键词
        'selected_status': status_filter,  # 选中的状态
        'status_choices': [('', '全部状态'), ('active', '启用'), ('inactive', '禁用')],  # 状态选项
    })
    
    return render(request, "delivery_customer/express_company_list.html", context)


@login_required
def express_company_create(request):
    """创建快递公司"""
    from django.shortcuts import redirect
    from django.contrib import messages
    from backend.apps.delivery_customer.models import ExpressCompany
    
    permission_set = get_user_permission_codes(request.user)
    module_sidebar_nav = _build_delivery_sidebar_nav(permission_set, request.path)
    delivery_sidebar_nav = module_sidebar_nav  # 兼容旧模板
    
    if not _permission_granted('delivery_center.create', permission_set):
        messages.error(request, '您没有创建快递公司的权限')
        return redirect('delivery_pages:express_company_list')
    
    if request.method == 'POST':
        try:
            name = request.POST.get('name', '').strip()
            if not name:
                messages.error(request, '快递公司名称不能为空')
            elif ExpressCompany.objects.filter(name=name).exists():
                messages.error(request, f'快递公司"{name}"已存在')
            else:
                company = ExpressCompany(
                    name=name,
                    code=request.POST.get('code', '').strip(),
                    alias=request.POST.get('alias', '').strip(),
                    contact_phone=request.POST.get('contact_phone', '').strip(),
                    contact_email=request.POST.get('contact_email', '').strip(),
                    website=request.POST.get('website', '').strip(),
                    is_active=request.POST.get('is_active') == 'on',
                    is_default=request.POST.get('is_default') == 'on',
                    sort_order=int(request.POST.get('sort_order', 0) or 0),
                    notes=request.POST.get('notes', '').strip(),
                    created_by=request.user,
                )
                company.save()
                
                # 如果设为默认，取消其他默认设置
                if company.is_default:
                    ExpressCompany.objects.filter(is_default=True).exclude(id=company.id).update(is_default=False)
                
                messages.success(request, f'快递公司"{name}"创建成功')
                return redirect('delivery_pages:express_company_detail', company_id=company.id)
        except Exception as e:
            logger.error(f"创建快递公司失败: {str(e)}")
            messages.error(request, f'创建失败：{str(e)}')
    
    context = _context(
        "创建快递公司",
        "➕",
        "添加新的快递公司",
        request=request,
    )
    context["module_sidebar_nav"] = module_sidebar_nav
    context["delivery_sidebar_nav"] = module_sidebar_nav  # 兼容旧模板
    return render(request, "delivery_customer/express_company_create.html", context)


@login_required
def express_company_detail(request, company_id):
    """快递公司详情"""
    from django.shortcuts import get_object_or_404
    from backend.apps.delivery_customer.models import ExpressCompany, DeliveryRecord
    
    permission_set = get_user_permission_codes(request.user)
    module_sidebar_nav = _build_delivery_sidebar_nav(permission_set, request.path)
    delivery_sidebar_nav = module_sidebar_nav  # 兼容旧模板
    
    company = get_object_or_404(ExpressCompany, id=company_id)
    
    # 统计使用次数
    usage_count = DeliveryRecord.objects.filter(express_company=company.name).count()
    
    context = _context(
        "快递公司详情",
        "🚚",
        "查看快递公司详细信息",
        request=request,
    )
    context["module_sidebar_nav"] = module_sidebar_nav
    context["delivery_sidebar_nav"] = module_sidebar_nav  # 兼容旧模板
    context["company"] = company
    context["usage_count"] = usage_count
    context["can_edit"] = _permission_granted('delivery_center.create', permission_set)
    return render(request, "delivery_customer/express_company_detail.html", context)


@login_required
def express_company_edit(request, company_id):
    """快递公司编辑"""
    from django.shortcuts import redirect, get_object_or_404
    from django.contrib import messages
    from backend.apps.delivery_customer.models import ExpressCompany
    
    permission_set = get_user_permission_codes(request.user)
    module_sidebar_nav = _build_delivery_sidebar_nav(permission_set, request.path)
    delivery_sidebar_nav = module_sidebar_nav  # 兼容旧模板
    
    if not _permission_granted('delivery_center.create', permission_set):
        messages.error(request, '您没有编辑快递公司的权限')
        return redirect('delivery_pages:express_company_list')
    
    company = get_object_or_404(ExpressCompany, id=company_id)
    
    if request.method == 'POST':
        try:
            name = request.POST.get('name', '').strip()
            if not name:
                messages.error(request, '快递公司名称不能为空')
            elif ExpressCompany.objects.filter(name=name).exclude(id=company.id).exists():
                messages.error(request, f'快递公司"{name}"已存在')
            else:
                company.name = name
                company.code = request.POST.get('code', '').strip()
                company.alias = request.POST.get('alias', '').strip()
                company.contact_phone = request.POST.get('contact_phone', '').strip()
                company.contact_email = request.POST.get('contact_email', '').strip()
                company.website = request.POST.get('website', '').strip()
                company.is_active = request.POST.get('is_active') == 'on'
                is_default = request.POST.get('is_default') == 'on'
                company.sort_order = int(request.POST.get('sort_order', 0) or 0)
                company.notes = request.POST.get('notes', '').strip()
                company.save()
                
                # 如果设为默认，取消其他默认设置
                if is_default and not company.is_default:
                    ExpressCompany.objects.filter(is_default=True).exclude(id=company.id).update(is_default=False)
                    company.is_default = True
                    company.save()
                elif not is_default and company.is_default:
                    company.is_default = False
                    company.save()
                
                messages.success(request, f'快递公司"{name}"更新成功')
                return redirect('delivery_pages:express_company_detail', company_id=company.id)
        except Exception as e:
            logger.error(f"编辑快递公司失败: {str(e)}")
            messages.error(request, f'更新失败：{str(e)}')
    
    context = _context(
        "快递公司编辑",
        "✏️",
        "编辑快递公司信息",
        request=request,
    )
    context["module_sidebar_nav"] = module_sidebar_nav
    context["delivery_sidebar_nav"] = module_sidebar_nav  # 兼容旧模板
    context["company"] = company
    return render(request, "delivery_customer/express_company_edit.html", context)


@login_required
def express_company_delete(request, company_id):
    """快递公司删除"""
    from django.shortcuts import redirect, get_object_or_404
    from django.contrib import messages
    from backend.apps.delivery_customer.models import ExpressCompany, DeliveryRecord
    
    permission_set = get_user_permission_codes(request.user)
    
    if not _permission_granted('delivery_center.create', permission_set):
        messages.error(request, '您没有删除快递公司的权限')
        return redirect('delivery_pages:express_company_list')
    
    company = get_object_or_404(ExpressCompany, id=company_id)
    
    # 检查是否被使用
    usage_count = DeliveryRecord.objects.filter(express_company=company.name).count()
    if usage_count > 0:
        messages.error(request, f'无法删除：该快递公司已被 {usage_count} 条交付记录使用')
        return redirect('delivery_pages:express_company_detail', company_id=company.id)
    
    company_name = company.name
    company.delete()
    messages.success(request, f'快递公司"{company_name}"已删除')
    return redirect('delivery_pages:express_company_list')


# ==================== 文件分类维护 ====================

# 阶段配置映射
FILE_CATEGORY_STAGES = {
    'conversion': '转化阶段',
    'contract': '合同阶段',
    'production': '生产阶段',
    'settlement': '结算阶段',
    'payment': '回款阶段',
    'after_sales': '售后阶段',
    'litigation': '诉讼阶段',
}

@login_required
def file_category_manage(request):
    """文件分类维护 - 统一管理页面（包含阶段选择、列表和新增功能）"""
    from django.shortcuts import redirect
    from django.core.paginator import Paginator
    from django.db.models import Q
    from django.contrib import messages
    from backend.apps.delivery_customer.models import FileCategory
    
    permission_set = get_user_permission_codes(request.user)
    module_sidebar_nav = _build_delivery_sidebar_nav(permission_set, request.path)
    delivery_sidebar_nav = module_sidebar_nav  # 兼容旧模板
    
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
                    return redirect(f'{reverse("delivery_pages:file_category_manage")}?stage={stage_code}')
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
    context["module_sidebar_nav"] = module_sidebar_nav
    context["delivery_sidebar_nav"] = module_sidebar_nav  # 兼容旧模板
    context["stage_code"] = selected_stage if not show_all else 'all'
    context["stage_name"] = stage_name
    context["show_all"] = show_all
    context["stages"] = FILE_CATEGORY_STAGES
    context["categories"] = page
    context["search_keyword"] = search_keyword
    context["status_filter"] = status_filter
    context["can_create"] = _permission_granted('delivery_center.create', permission_set)
    
    return render(request, "delivery_customer/file_category_manage.html", context)


@login_required
def file_category_list(request, stage_code):
    """文件分类维护 - 列表页（统一视图，通过stage_code参数区分阶段）"""
    from django.core.paginator import Paginator
    from django.db.models import Q
    from django.http import Http404
    from backend.apps.delivery_customer.models import FileCategory
    
    if stage_code not in FILE_CATEGORY_STAGES:
        raise Http404("阶段不存在")
    
    stage_name = FILE_CATEGORY_STAGES[stage_code]
    
    permission_set = get_user_permission_codes(request.user)
    module_sidebar_nav = _build_delivery_sidebar_nav(permission_set, request.path)
    delivery_sidebar_nav = module_sidebar_nav  # 兼容旧模板
    
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
    context["module_sidebar_nav"] = module_sidebar_nav
    context["delivery_sidebar_nav"] = module_sidebar_nav  # 兼容旧模板
    context["stage_code"] = stage_code
    context["stage_name"] = stage_name
    context["categories"] = page
    context["search_keyword"] = search_keyword
    context["status_filter"] = status_filter
    context["can_create"] = _permission_granted('delivery_center.create', permission_set)
    
    return render(request, "delivery_customer/file_category_list.html", context)


@login_required
def file_category_create(request, stage_code):
    """文件分类维护 - 新增（统一视图，通过stage_code参数区分阶段）"""
    from django.shortcuts import redirect
    from django.contrib import messages
    from django.http import Http404
    from backend.apps.delivery_customer.models import FileCategory
    
    if stage_code not in FILE_CATEGORY_STAGES:
        raise Http404("阶段不存在")
    
    stage_name = FILE_CATEGORY_STAGES[stage_code]
    
    permission_set = get_user_permission_codes(request.user)
    module_sidebar_nav = _build_delivery_sidebar_nav(permission_set, request.path)
    delivery_sidebar_nav = module_sidebar_nav  # 兼容旧模板
    
    if not _permission_granted('delivery_center.create', permission_set):
        messages.error(request, '您没有创建文件分类的权限')
        return redirect('delivery_pages:file_category_list', stage_code=stage_code)
    
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
                    return redirect('delivery_pages:file_category_list', stage_code=stage_code)
        except Exception as e:
            logger.error(f"创建文件分类失败: {str(e)}")
            messages.error(request, f'创建失败：{str(e)}')
    
    context = _context(
        f"新增文件分类 - {stage_name}",
        "➕",
        f"为{stage_name}新增文件分类",
        request=request,
    )
    context["module_sidebar_nav"] = module_sidebar_nav
    context["delivery_sidebar_nav"] = module_sidebar_nav  # 兼容旧模板
    context["stage_code"] = stage_code
    context["stage_name"] = stage_name
    
    return render(request, "delivery_customer/file_category_create.html", context)


# ==================== 文件模板维护 ====================

@login_required
def file_template_manage(request):
    """文件模板维护 - 统一管理页面（包含阶段选择、列表和新增功能）"""
    from django.shortcuts import redirect
    from django.core.paginator import Paginator
    from django.db.models import Q
    from django.contrib import messages
    from backend.apps.delivery_customer.models import FileTemplate, FileCategory
    
    permission_set = get_user_permission_codes(request.user)
    module_sidebar_nav = _build_delivery_sidebar_nav(permission_set, request.path)
    delivery_sidebar_nav = module_sidebar_nav  # 兼容旧模板
    
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
                    return redirect(f'{reverse("delivery_pages:file_template_manage")}?stage={stage_code}')
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
    context["module_sidebar_nav"] = module_sidebar_nav
    context["delivery_sidebar_nav"] = module_sidebar_nav  # 兼容旧模板
    context["stage_code"] = selected_stage if not show_all else 'all'
    context["stage_name"] = stage_name
    context["show_all"] = show_all
    context["stages"] = FILE_CATEGORY_STAGES
    context["templates"] = page
    context["search_keyword"] = search_keyword
    context["status_filter"] = status_filter
    context["can_create"] = _permission_granted('delivery_center.create', permission_set)
    context["categories_by_stage"] = categories_by_stage
    
    return render(request, "delivery_customer/file_template_manage.html", context)


@csrf_exempt
def email_tracking_pixel(request, tracking_id):
    """
    邮件跟踪像素视图
    当收件人打开邮件时，邮件客户端会加载这个1x1的透明图片
    从而触发这个视图，记录邮件已被读取
    
    注意：此视图不需要登录验证和CSRF验证，因为：
    1. 外部收件人需要能够访问此URL
    2. 邮件客户端加载图片时不会发送CSRF token
    
    增强功能：
    - 记录访问日志（IP、User-Agent、Referer等）
    - 验证跟踪ID格式
    - 优化响应性能
    - 防止异常访问（记录但不阻止）
    """
    from django.http import HttpResponse
    from backend.apps.delivery_customer.tracking_service import EmailTrackingService
    import logging
    import re
    
    logger = logging.getLogger(__name__)
    
    # 获取请求信息用于日志记录
    client_ip = request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0].strip() or \
                request.META.get('REMOTE_ADDR', 'unknown')
    user_agent = request.META.get('HTTP_USER_AGENT', 'unknown')
    referer = request.META.get('HTTP_REFERER', '')
    
    # 验证跟踪ID格式（基本格式检查，防止明显的恶意请求）
    if not tracking_id or len(tracking_id) < 10 or not re.match(r'^[A-Za-z0-9_-]+$', tracking_id):
        logger.warning(f"邮件跟踪像素：无效的跟踪ID格式: tracking_id={tracking_id}, IP={client_ip}, UA={user_agent[:100]}")
        # 仍然返回图片，避免暴露错误信息
        transparent_gif = b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\x00\x00\x00\x21\xF9\x04\x01\x00\x00\x00\x00\x2C\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x04\x01\x00\x3B'
        response = HttpResponse(transparent_gif, content_type='image/gif')
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'
        return response
    
    try:
        # 记录访问信息（用于统计和分析）
        logger.debug(f"邮件跟踪像素访问: tracking_id={tracking_id}, IP={client_ip}, UA={user_agent[:100]}, Referer={referer[:100]}")
        
        # 标记邮件为已读
        success, message = EmailTrackingService.mark_email_as_read(tracking_id)
        
        if success:
            logger.info(f"✅ 邮件跟踪像素触发成功: tracking_id={tracking_id}, IP={client_ip}, message={message}")
        else:
            logger.warning(f"⚠️ 邮件跟踪像素触发失败: tracking_id={tracking_id}, IP={client_ip}, message={message}")
    except Exception as e:
        logger.error(f"❌ 邮件跟踪像素处理异常: tracking_id={tracking_id}, IP={client_ip}, error={str(e)}", exc_info=True)
    
    # 返回1x1透明GIF图片
    # 这是一个标准的1x1透明GIF图片的base64编码
    transparent_gif = b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\x00\x00\x00\x21\xF9\x04\x01\x00\x00\x00\x00\x2C\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x04\x01\x00\x3B'
    
    response = HttpResponse(transparent_gif, content_type='image/gif')
    # 设置缓存头，防止浏览器缓存（确保每次访问都能触发）
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    # 添加CORS头，允许跨域访问（邮件客户端可能需要）
    response['Access-Control-Allow-Origin'] = '*'
    response['Access-Control-Allow-Methods'] = 'GET, HEAD, OPTIONS'
    response['Access-Control-Allow-Headers'] = '*'
    
    return response


@csrf_exempt
def email_receipt_confirm(request, tracking_id):
    """
    邮件确认收取视图
    收件人点击邮件中的"确认收取"链接后，跳转到此页面
    确认后记录确认时间并显示完整的邮件内容
    """
    from django.shortcuts import render, get_object_or_404
    from django.utils import timezone
    from backend.apps.delivery_customer.models import OutgoingDocumentTracking
    from backend.apps.delivery_customer.tracking_service import EmailTrackingService
    import logging
    
    logger = logging.getLogger(__name__)
    
    # 获取请求信息用于日志
    client_ip = request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0].strip() or \
                request.META.get('REMOTE_ADDR', 'unknown')
    user_agent = request.META.get('HTTP_USER_AGENT', 'unknown')
    
    # 验证跟踪ID格式
    import re
    if not tracking_id or len(tracking_id) < 10 or not re.match(r'^[A-Za-z0-9_-]+$', tracking_id):
        logger.warning(f"邮件确认收取：无效的跟踪ID格式: tracking_id={tracking_id}, IP={client_ip}")
        return render(request, 'delivery_customer/email_receipt_error.html', {
            'error_message': '无效的确认链接，请检查链接是否正确。'
        }, status=400)
    
    try:
        # 查找跟踪记录
        tracking = OutgoingDocumentTracking.objects.filter(
            email_tracking_id=tracking_id
        ).select_related('document', 'delivery_method').first()
        
        if not tracking:
            # 尝试通过文档查找
            from backend.apps.delivery_customer.models import OutgoingDocument
            document = OutgoingDocument.objects.filter(email_tracking_id=tracking_id).first()
            if document:
                tracking = OutgoingDocumentTracking.objects.filter(document=document).select_related('document', 'delivery_method').first()
                if tracking:
                    tracking.email_tracking_id = tracking_id
                    tracking.save(update_fields=['email_tracking_id'])
        
        if not tracking:
            logger.warning(f"邮件确认收取：未找到跟踪记录: tracking_id={tracking_id}, IP={client_ip}")
            return render(request, 'delivery_customer/email_receipt_error.html', {
                'error_message': '未找到对应的跟踪记录，请确认链接是否正确。'
            }, status=404)
        
        # 检查是否为邮件方式
        if not tracking.delivery_method or tracking.delivery_method.code != 'email':
            logger.warning(f"邮件确认收取：跟踪记录不是邮件方式: tracking_id={tracking_id}, IP={client_ip}")
            return render(request, 'delivery_customer/email_receipt_error.html', {
                'error_message': '此跟踪记录不是邮件方式，无法确认收取。'
            }, status=400)
        
        document = tracking.document
        if not document:
            logger.error(f"邮件确认收取：跟踪记录没有关联的文档: tracking_id={tracking_id}, IP={client_ip}")
            return render(request, 'delivery_customer/email_receipt_error.html', {
                'error_message': '系统错误：未找到关联的文档信息。'
            }, status=500)
        
        # 处理确认操作（POST请求）
        if request.method == 'POST':
            from django.db import transaction
            
            with transaction.atomic():
                # 重新获取跟踪记录（使用select_for_update防止并发）
                tracking = OutgoingDocumentTracking.objects.select_for_update().filter(
                    id=tracking.id
                ).select_related('document', 'delivery_method').first()
                
                # 如果已经确认过，直接返回成功
                if tracking.received_at:
                    logger.info(f"邮件确认收取：已确认过，跳过重复确认: tracking_id={tracking_id}, IP={client_ip}")
                else:
                    # 记录确认时间
                    confirm_time = timezone.now()
                    tracking.received_at = confirm_time
                    tracking.status = 'received'
                    tracking.save(update_fields=['received_at', 'status'])
                    
                    # 同步到文档
                    document.received_at = confirm_time
                    document.save(update_fields=['received_at'])
                    
                    # 标记邮件为已读（如果还未标记）
                    if not tracking.email_read_at:
                        success, message = EmailTrackingService.mark_email_as_read(tracking_id)
                        if success:
                            logger.info(f"邮件确认收取：同时标记为已读: tracking_id={tracking_id}, IP={client_ip}")
                    
                    logger.info(f"✅ 邮件确认收取成功: tracking_id={tracking_id}, 文档={document.document_number}, IP={client_ip}")
        
        # 检查是否已确认
        is_confirmed = tracking.received_at is not None
        
        # 准备上下文数据
        context = {
            'tracking': tracking,
            'document': document,
            'is_confirmed': is_confirmed,
            'confirm_time': tracking.received_at,
            'tracking_id': tracking_id,
        }
        
        return render(request, 'delivery_customer/email_receipt_confirm.html', context)
        
    except Exception as e:
        logger.error(f"❌ 邮件确认收取异常: tracking_id={tracking_id}, IP={client_ip}, error={str(e)}", exc_info=True)
        return render(request, 'delivery_customer/email_receipt_error.html', {
            'error_message': f'系统错误：{str(e)}'
        }, status=500)


@login_required
def outgoing_document_batch_import(request):
    """发文批量导入"""
    from django.http import JsonResponse, HttpResponse
    from django.shortcuts import redirect
    from django.contrib import messages
    from django.db import transaction
    from django.utils import timezone
    from django.utils.dateparse import parse_date
    import io
    import csv
    from backend.apps.delivery_customer.models import OutgoingDocument, FileCategory
    from backend.apps.production_management.models import Project
    from backend.apps.customer_management.models import Client, ClientContact
    
    permission_set = get_user_permission_codes(request.user)
    
    if not _permission_granted('delivery_center.create', permission_set):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': '您没有创建发文的权限'}, status=403)
        messages.error(request, '您没有创建发文的权限')
        return redirect('delivery_pages:outgoing_document_list')
    
    if request.method == 'POST':
        try:
            # 获取上传的文件
            if 'file' not in request.FILES:
                return JsonResponse({'success': False, 'error': '请选择要导入的文件'})
            
            upload = request.FILES['file']
            filename = upload.name
            mode = request.POST.get('mode', 'create')  # create, update, replace
            
            # 检查文件大小（10MB限制）
            if upload.size > 10 * 1024 * 1024:
                return JsonResponse({'success': False, 'error': '文件大小不能超过 10MB'})
            
            # 检查文件格式
            is_excel = filename.endswith(('.xlsx', '.xls'))
            is_csv = filename.endswith('.csv')
            
            if not (is_excel or is_csv):
                return JsonResponse({'success': False, 'error': '仅支持 Excel (.xlsx, .xls) 或 CSV (.csv) 格式'})
            
            # 解析文件
            if is_excel:
                try:
                    import pandas as pd
                    df = pd.read_excel(upload, engine='openpyxl' if filename.endswith('.xlsx') else None)
                    csv_buffer = io.StringIO()
                    df.to_csv(csv_buffer, index=False, encoding='utf-8')
                    decoded_text = csv_buffer.getvalue()
                except ImportError:
                    return JsonResponse({'success': False, 'error': '系统未安装 pandas 库，无法处理 Excel 文件。请使用 CSV 格式。'})
                except Exception as e:
                    return JsonResponse({'success': False, 'error': f'Excel 文件解析失败：{str(e)}'})
            else:
                # 处理CSV文件
                raw_bytes = upload.read()
                decoded_text = None
                for enc in ('utf-8-sig', 'utf-8', 'gbk', 'gb2312'):
                    try:
                        decoded_text = raw_bytes.decode(enc)
                        break
                    except UnicodeDecodeError:
                        continue
                
                if decoded_text is None:
                    return JsonResponse({'success': False, 'error': '文件解析失败，请确认编码为 UTF-8 或 GBK'})
            
            # 解析CSV数据
            text_io = io.StringIO(decoded_text)
            reader = csv.DictReader(text_io)
            
            # 字段映射（支持多种列名）
            field_aliases = {
                'document_number': {'发文编号', '编号', 'document_number'},
                'title': {'文件标题', '标题', 'title'},
                'recipient': {'收文单位', '收文', 'recipient'},
                'recipient_contact': {'联系人', 'recipient_contact'},
                'recipient_phone': {'联系电话', '电话', 'recipient_phone'},
                'recipient_email': {'联系邮箱', '邮箱', 'recipient_email'},
                'recipient_address': {'收文地址', '地址', 'recipient_address'},
                'priority': {'优先级', 'priority'},
                'stage': {'阶段', 'stage'},
                'file_category': {'文件分类', '分类', 'file_category'},
                'document_date': {'文件日期', '日期', 'document_date'},
                'content': {'文件内容', '内容', 'content'},
                'summary': {'摘要', 'summary'},
                'notes': {'备注', 'notes'},
            }
            
            # 状态和优先级映射
            priority_map = {
                '低': 'low', 'low': 'low',
                '普通': 'normal', 'normal': 'normal',
                '高': 'high', 'high': 'high',
                '紧急': 'urgent', 'urgent': 'urgent',
            }
            
            stage_map = {
                '转化阶段': 'conversion', 'conversion': 'conversion',
                '合同阶段': 'contract', 'contract': 'contract',
                '生产阶段': 'production', 'production': 'production',
                '结算阶段': 'settlement', 'settlement': 'settlement',
                '回款阶段': 'payment', 'payment': 'payment',
                '售后阶段': 'after_sales', 'after_sales': 'after_sales',
                '诉讼阶段': 'litigation', 'litigation': 'litigation',
            }
            
            def get_value(row, field):
                """从行数据中获取字段值"""
                for alias in field_aliases.get(field, set()):
                    if alias in row and row[alias] is not None:
                        value = str(row.get(alias, '')).strip()
                        if value:
                            return value
                return ''
            
            results = []
            success_count = 0
            failure_count = 0
            
            # 获取文件分类映射
            categories = FileCategory.objects.filter(is_active=True)
            category_name_map = {cat.name: cat for cat in categories}
            
            for row_index, row in enumerate(reader, start=2):
                row_result = {'row': row_index, 'status': 'success', 'message': ''}
                try:
                    with transaction.atomic():
                        # 获取必填字段
                        title = get_value(row, 'title')
                        if not title:
                            raise ValueError('文件标题不能为空')
                        
                        recipient = get_value(row, 'recipient')
                        if not recipient:
                            raise ValueError('收文单位不能为空')
                        
                        # 处理发文编号
                        document_number = get_value(row, 'document_number')
                        if document_number:
                            # 如果提供了编号，检查是否已存在
                            if OutgoingDocument.objects.filter(document_number=document_number).exists():
                                if mode == 'create':
                                    raise ValueError(f'发文编号已存在：{document_number}')
                                elif mode == 'update':
                                    # 更新模式：更新已存在的记录
                                    document = OutgoingDocument.objects.get(document_number=document_number)
                                    if document.status != 'draft':
                                        raise ValueError(f'只能更新草稿状态的发文：{document_number}')
                                else:
                                    # replace模式：删除旧记录
                                    OutgoingDocument.objects.filter(document_number=document_number).delete()
                                    document = None
                            else:
                                document = None
                        else:
                            # 自动生成编号
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
                            document = None
                        
                        # 创建或更新发文记录
                        if document is None:
                            document = OutgoingDocument(
                                document_number=document_number,
                                title=title,
                                recipient=recipient,
                                status='draft',  # 导入的发文默认为草稿状态
                                created_by=request.user,
                            )
                        
                        # 更新字段
                        document.recipient_contact = get_value(row, 'recipient_contact') or ''
                        document.recipient_phone = get_value(row, 'recipient_phone') or ''
                        document.recipient_email = get_value(row, 'recipient_email') or ''
                        document.recipient_address = get_value(row, 'recipient_address') or ''
                        document.content = get_value(row, 'content') or ''
                        document.summary = get_value(row, 'summary') or ''
                        document.notes = get_value(row, 'notes') or ''
                        
                        # 处理优先级
                        priority_raw = get_value(row, 'priority')
                        if priority_raw:
                            priority = priority_map.get(priority_raw, 'normal')
                            document.priority = priority
                        
                        # 处理阶段
                        stage_raw = get_value(row, 'stage')
                        if stage_raw:
                            stage = stage_map.get(stage_raw)
                            if stage:
                                document.stage = stage
                        
                        # 处理文件分类
                        category_raw = get_value(row, 'file_category')
                        if category_raw:
                            category = category_name_map.get(category_raw)
                            if category:
                                document.file_category = category
                        
                        # 处理日期
                        document_date_raw = get_value(row, 'document_date')
                        if document_date_raw:
                            try:
                                document_date = parse_date(document_date_raw)
                                if document_date:
                                    document.document_date = document_date
                            except:
                                pass
                        
                        document.save()
                        success_count += 1
                        row_result['message'] = f'成功导入：{document_number}'
                        
                except Exception as e:
                    failure_count += 1
                    row_result['status'] = 'error'
                    row_result['message'] = str(e)
                
                results.append(row_result)
            
            # 返回结果
            return JsonResponse({
                'success': True,
                'total': len(results),
                'success_count': success_count,
                'failure_count': failure_count,
                'results': results[:100],  # 限制返回前100条结果
                'message': f'导入完成：成功 {success_count} 条，失败 {failure_count} 条'
            })
            
        except Exception as e:
            import traceback
            logger.error(f'批量导入失败：{str(e)}\n{traceback.format_exc()}')
            return JsonResponse({'success': False, 'error': f'导入失败：{str(e)}'})
    
    return JsonResponse({'success': False, 'error': '仅支持 POST 请求'})


@login_required
def outgoing_document_import_template(request):
    """下载导入模板"""
    from django.http import HttpResponse
    from django.shortcuts import redirect
    from django.contrib import messages
    import csv
    import io
    
    permission_set = get_user_permission_codes(request.user)
    
    if not _permission_granted('delivery_center.create', permission_set):
        messages.error(request, '您没有创建发文的权限')
        return redirect('delivery_pages:outgoing_document_list')
    
    # 创建CSV模板
    output = io.StringIO()
    writer = csv.writer(output)
    
    # 写入表头
    headers = [
        '发文编号（可留空自动生成）',
        '文件标题（必填）',
        '收文单位（必填）',
        '联系人',
        '联系电话',
        '联系邮箱',
        '收文地址',
        '优先级（低/普通/高/紧急）',
        '阶段（转化阶段/合同阶段/生产阶段/结算阶段/回款阶段/售后阶段/诉讼阶段）',
        '文件分类',
        '文件日期（YYYY-MM-DD）',
        '文件内容',
        '摘要',
        '备注',
    ]
    writer.writerow(headers)
    
    # 写入示例数据
    example_row = [
        '',  # 发文编号（留空自动生成）
        '示例发文标题',
        '示例收文单位',
        '张三',
        '13800138000',
        'example@example.com',
        '示例地址',
        '普通',
        '合同阶段',
        '',
        '2024-01-01',
        '示例内容',
        '示例摘要',
        '示例备注',
    ]
    writer.writerow(example_row)
    
    # 返回文件
    response = HttpResponse(output.getvalue().encode('utf-8-sig'), content_type='text/csv; charset=utf-8-sig')
    response['Content-Disposition'] = 'attachment; filename="outgoing_document_import_template.csv"'
    return response


@login_required
def mark_tracking_email_read(request, tracking_id):
    """
    标记单个邮件跟踪记录为已读
    用于在跟踪像素未触发时（如邮件客户端阻止图片加载）手动更新状态
    """
    from django.http import JsonResponse
    from django.shortcuts import get_object_or_404
    from backend.apps.delivery_customer.models import OutgoingDocumentTracking
    from backend.apps.delivery_customer.tracking_service import EmailTrackingService
    import logging
    
    logger = logging.getLogger(__name__)
    
    permission_set = get_user_permission_codes(request.user)
    
    # 检查权限
    if not _permission_granted('delivery_center.view', permission_set):
        return JsonResponse({'status': 'error', 'message': '您没有权限执行此操作'}, status=403)
    
    tracking = get_object_or_404(
        OutgoingDocumentTracking.objects.select_related('document', 'delivery_method'),
        id=tracking_id
    )
    
    # 检查是否为邮件方式
    if not tracking.delivery_method or tracking.delivery_method.code != 'email':
        return JsonResponse({'status': 'error', 'message': '此跟踪记录不是邮件方式，无法标记为已读'}, status=400)
    
    try:
        # 使用服务类来标记邮件为已读
        if tracking.email_tracking_id:
            success, message = EmailTrackingService.mark_email_as_read(tracking.email_tracking_id)
            if success:
                logger.info(f"手动标记邮件为已读成功: tracking_id={tracking_id}, email_tracking_id={tracking.email_tracking_id}, 操作人={request.user.username}")
                return JsonResponse({'status': 'success', 'message': message})
            else:
                logger.warning(f"手动标记邮件为已读失败: tracking_id={tracking_id}, email_tracking_id={tracking.email_tracking_id}, 原因={message}")
                return JsonResponse({'status': 'error', 'message': message}, status=400)
        else:
            # 如果没有 tracking_id，直接更新时间戳（兼容旧数据）
            from django.utils import timezone
            if tracking.email_read_at is None:
                tracking.email_read_at = timezone.now()
                tracking.received_at = tracking.email_read_at
                tracking.status = 'read'
                tracking.save(update_fields=['email_read_at', 'received_at', 'status'])
                logger.info(f"手动标记邮件为已读（无tracking_id）: tracking_id={tracking_id}, 操作人={request.user.username}")
            return JsonResponse({'status': 'success', 'message': '邮件已标记为已读'})
    except Exception as e:
        logger.error(f"手动标记邮件为已读异常: tracking_id={tracking_id}, error={str(e)}", exc_info=True)
        return JsonResponse({'status': 'error', 'message': f'操作失败：{str(e)}'}, status=500)


@login_required
def batch_mark_tracking_email_read(request):
    """
    批量标记邮件跟踪记录为已读
    用于批量更新多个跟踪记录的邮件已读状态
    """
    from django.http import JsonResponse
    from backend.apps.delivery_customer.models import OutgoingDocumentTracking
    from backend.apps.delivery_customer.tracking_service import EmailTrackingService
    import logging
    
    logger = logging.getLogger(__name__)
    
    permission_set = get_user_permission_codes(request.user)
    
    # 检查权限
    if not _permission_granted('delivery_center.view', permission_set):
        return JsonResponse({'status': 'error', 'message': '您没有权限执行此操作'}, status=403)
    
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': '仅支持POST请求'}, status=405)
    
    # 获取跟踪记录ID列表
    tracking_ids = request.POST.getlist('tracking_ids[]') or request.POST.getlist('tracking_ids')
    if not tracking_ids:
        return JsonResponse({'status': 'error', 'message': '请选择要标记的跟踪记录'}, status=400)
    
    try:
        # 获取跟踪记录（只获取邮件方式的记录）
        trackings = OutgoingDocumentTracking.objects.filter(
            id__in=tracking_ids,
            delivery_method__code='email'
        ).select_related('document', 'delivery_method')
        
        success_count = 0
        failed_count = 0
        skipped_count = 0
        details = []
        
        for tracking in trackings:
            try:
                # 如果已经标记为已读，跳过
                if tracking.email_read_at:
                    skipped_count += 1
                    details.append({
                        'tracking_id': tracking.id,
                        'document_number': tracking.document.document_number if tracking.document else 'N/A',
                        'status': 'skipped',
                        'message': '已标记为已读，跳过'
                    })
                    continue
                
                # 标记为已读
                if tracking.email_tracking_id:
                    success, message = EmailTrackingService.mark_email_as_read(tracking.email_tracking_id)
                    if success:
                        success_count += 1
                        details.append({
                            'tracking_id': tracking.id,
                            'document_number': tracking.document.document_number if tracking.document else 'N/A',
                            'status': 'success',
                            'message': message
                        })
                    else:
                        failed_count += 1
                        details.append({
                            'tracking_id': tracking.id,
                            'document_number': tracking.document.document_number if tracking.document else 'N/A',
                            'status': 'failed',
                            'message': message
                        })
                else:
                    # 如果没有 tracking_id，直接更新时间戳
                    from django.utils import timezone
                    tracking.email_read_at = timezone.now()
                    tracking.received_at = tracking.email_read_at
                    tracking.status = 'read'
                    tracking.save(update_fields=['email_read_at', 'received_at', 'status'])
                    success_count += 1
                    details.append({
                        'tracking_id': tracking.id,
                        'document_number': tracking.document.document_number if tracking.document else 'N/A',
                        'status': 'success',
                        'message': '邮件已标记为已读'
                    })
            except Exception as e:
                failed_count += 1
                logger.error(f"批量标记邮件为已读失败: tracking_id={tracking.id}, error={str(e)}", exc_info=True)
                details.append({
                    'tracking_id': tracking.id,
                    'document_number': tracking.document.document_number if tracking.document else 'N/A',
                    'status': 'failed',
                    'message': f'处理失败：{str(e)}'
                })
        
        logger.info(f"批量标记邮件为已读完成: 总数={len(tracking_ids)}, 成功={success_count}, 失败={failed_count}, 跳过={skipped_count}, 操作人={request.user.username}")
        
        return JsonResponse({
            'status': 'success',
            'message': f'批量标记完成：成功 {success_count} 条，失败 {failed_count} 条，跳过 {skipped_count} 条',
            'summary': {
                'total': len(tracking_ids),
                'success': success_count,
                'failed': failed_count,
                'skipped': skipped_count
            },
            'details': details
        })
        
    except Exception as e:
        logger.error(f"批量标记邮件为已读异常: error={str(e)}", exc_info=True)
        return JsonResponse({'status': 'error', 'message': f'批量操作失败：{str(e)}'}, status=500)


@login_required
def confirm_email_received(request, tracking_id):
    """
    确认邮件已接收（邮件报送方式专用）
    需要上传能够证明收件人已收到的附件
    """
    from django.shortcuts import get_object_or_404, redirect
    from django.http import JsonResponse
    from django.utils import timezone
    from django.contrib import messages
    from backend.apps.delivery_customer.models import OutgoingDocumentTracking
    import logging
    
    logger = logging.getLogger(__name__)
    
    permission_set = get_user_permission_codes(request.user)
    
    # 检查权限
    if not _permission_granted('delivery_center.view', permission_set):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'status': 'error', 'message': '您没有权限执行此操作'}, status=403)
        messages.error(request, '您没有权限执行此操作')
        return redirect('delivery_pages:outgoing_document_tracking_detail', tracking_id=tracking_id)
    
    # 获取跟踪记录
    tracking = get_object_or_404(
        OutgoingDocumentTracking.objects.select_related('document', 'delivery_method'),
        id=tracking_id
    )
    
    # 检查是否为邮件方式
    if not tracking.delivery_method or tracking.delivery_method.code != 'email':
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'status': 'error', 'message': '此跟踪记录不是邮件方式'}, status=400)
        messages.error(request, '此跟踪记录不是邮件方式')
        return redirect('delivery_pages:outgoing_document_tracking_detail', tracking_id=tracking_id)
    
    # 检查是否已经确认接收
    if tracking.email_received_attachment:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'status': 'error', 'message': '该邮件已经确认接收过了'}, status=400)
        messages.warning(request, '该邮件已经确认接收过了')
        return redirect('delivery_pages:outgoing_document_tracking_detail', tracking_id=tracking_id)
    
    # 只接受POST请求
    if request.method != 'POST':
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'status': 'error', 'message': '只支持POST请求'}, status=405)
        messages.error(request, '只支持POST请求')
        return redirect('delivery_pages:outgoing_document_tracking_detail', tracking_id=tracking_id)
    
    try:
        # 获取上传的附件
        received_attachment = request.FILES.get('received_attachment')
        if not received_attachment:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'status': 'error', 'message': '请上传接收确认附件'}, status=400)
            messages.error(request, '请上传接收确认附件')
            return redirect('delivery_pages:outgoing_document_tracking_detail', tracking_id=tracking_id)
        
        # 验证文件类型
        allowed_extensions = ['.pdf', '.doc', '.docx', '.jpg', '.jpeg', '.png', '.gif', '.bmp']
        file_extension = received_attachment.name.lower().split('.')[-1] if '.' in received_attachment.name else ''
        if file_extension not in [ext.lstrip('.') for ext in allowed_extensions]:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'status': 'error', 'message': f'不支持的文件格式，请上传 {", ".join(allowed_extensions)} 格式的文件'}, status=400)
            messages.error(request, f'不支持的文件格式，请上传 {", ".join(allowed_extensions)} 格式的文件')
            return redirect('delivery_pages:outgoing_document_tracking_detail', tracking_id=tracking_id)
        
        # 验证文件大小（限制为10MB）
        max_size = 10 * 1024 * 1024  # 10MB
        if received_attachment.size > max_size:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'status': 'error', 'message': '文件大小不能超过10MB'}, status=400)
            messages.error(request, '文件大小不能超过10MB')
            return redirect('delivery_pages:outgoing_document_tracking_detail', tracking_id=tracking_id)
        
        # 获取备注
        notes = request.POST.get('notes', '').strip()
        
        # 更新跟踪记录
        now = timezone.now()
        tracking.email_received_attachment = received_attachment
        tracking.email_received_confirmed_by = request.user
        tracking.email_received_confirmed_at = now
        tracking.received_at = now
        tracking.completed_at = now
        tracking.status = 'completed'
        
        # 如果有备注，追加到 notes 字段
        if notes:
            if tracking.notes:
                tracking.notes += f"\n\n【接收确认】{now.strftime('%Y-%m-%d %H:%M:%S')} - {request.user.get_full_name() or request.user.username}：\n{notes}"
            else:
                tracking.notes = f"【接收确认】{now.strftime('%Y-%m-%d %H:%M:%S')} - {request.user.get_full_name() or request.user.username}：\n{notes}"
        
        tracking.save(update_fields=[
            'email_received_attachment',
            'email_received_confirmed_by',
            'email_received_confirmed_at',
            'received_at',
            'completed_at',
            'status',
            'notes',
            'updated_at'
        ])
        
        # 同步到文档
        document = tracking.document
        if document:
            if not document.received_at:
                document.received_at = now
            if not document.is_receipt_confirmed:
                document.is_receipt_confirmed = True
            document.save(update_fields=['received_at', 'is_receipt_confirmed'])
        
        logger.info(f"邮件接收确认成功: tracking_id={tracking_id}, 附件={received_attachment.name}, 操作人={request.user.username}")
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'success',
                'message': '邮件接收确认成功，已更新为已完成状态'
            })
        
        messages.success(request, '邮件接收确认成功，已更新为已完成状态')
        return redirect('delivery_pages:outgoing_document_tracking_detail', tracking_id=tracking_id)
        
    except Exception as e:
        logger.error(f"确认邮件接收失败: tracking_id={tracking_id}, error={str(e)}", exc_info=True)
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'status': 'error', 'message': f'操作失败：{str(e)}'}, status=500)
        messages.error(request, f'操作失败：{str(e)}')
        return redirect('delivery_pages:outgoing_document_tracking_detail', tracking_id=tracking_id)


@csrf_exempt
def sms_callback(request):
    """
    短信送达状态回调接口（阿里云短信服务回调）
    
    注意：此接口不需要登录验证和CSRF验证，因为：
    1. 阿里云服务器需要能够访问此URL
    2. 阿里云回调时不会发送CSRF token
    
    阿里云短信服务支持两种回执接收模式：
    1. 轻量消息队列（MNS）消费模式
    2. HTTP批量推送模式（本接口支持此模式）
    
    回调数据格式（根据阿里云文档）：
    {
        "phone_number": "13800138000",
        "send_date": "20231231",
        "send_time": "123456",
        "report_time": "20231231123456",
        "success": true,
        "err_code": "DELIVERED",
        "err_msg": "用户接收成功",
        "sms_size": 1,
        "biz_id": "942913167158057960^0",
        "out_id": "your-out-id"  # 可选，发送时传入的OutId
    }
    """
    from django.http import HttpResponse, JsonResponse
    from django.utils import timezone
    from backend.apps.delivery_customer.models import OutgoingDocumentTracking
    from backend.apps.delivery_customer.tracking_service import SmsTrackingService
    import json
    import logging
    
    logger = logging.getLogger(__name__)
    
    # 获取客户端IP用于日志
    client_ip = request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0].strip() or \
                request.META.get('REMOTE_ADDR', 'unknown')
    
    # 只接受POST请求
    if request.method != 'POST':
        logger.warning(f"短信回调：收到非POST请求: method={request.method}, IP={client_ip}")
        return HttpResponse('Method Not Allowed', status=405)
    
    try:
        # 解析回调数据
        if request.content_type == 'application/json':
            callback_data = json.loads(request.body)
        else:
            # 兼容表单格式
            callback_data = request.POST.dict()
        
        logger.info(f"收到短信回调: IP={client_ip}, data={callback_data}")
        
        # 从回调数据中提取关键信息
        biz_id = callback_data.get('biz_id') or callback_data.get('bizId')
        phone_number = callback_data.get('phone_number') or callback_data.get('phoneNumber')
        success = callback_data.get('success', False)
        err_code = callback_data.get('err_code') or callback_data.get('errCode', '')
        err_msg = callback_data.get('err_msg') or callback_data.get('errMsg', '')
        
        if not biz_id:
            logger.warning(f"短信回调：缺少biz_id: data={callback_data}")
            return JsonResponse({'status': 'error', 'message': '缺少biz_id'}, status=400)
        
        # 根据biz_id查找跟踪记录
        # biz_id格式可能是：942913167158057960^0 或 942913167158057960
        biz_id_clean = biz_id.split('^')[0]  # 去掉^0后缀
        
        # 查找匹配的跟踪记录（通过sms_message_id）
        tracking = OutgoingDocumentTracking.objects.filter(
            sms_message_id__startswith=biz_id_clean,
            delivery_method__code='sms'
        ).first()
        
        if not tracking:
            logger.warning(f"短信回调：未找到匹配的跟踪记录: biz_id={biz_id}, biz_id_clean={biz_id_clean}")
            # 仍然返回成功，避免阿里云重复推送
            return JsonResponse({'status': 'ok', 'message': '未找到匹配记录，但已接收'})
        
        # 构建标准化的回调数据
        standardized_data = {
            'biz_id': biz_id,
            'phone_number': phone_number,
            'success': success,
            'err_code': err_code,
            'err_msg': err_msg,
            'raw_data': callback_data,
            'callback_time': timezone.now().isoformat(),
        }
        
        # 根据success和err_code判断状态
        if success or err_code in ['DELIVERED', 'SUCCESS']:
            standardized_data['status'] = 'delivered'
        elif err_code in ['FAIL', 'REJECTED', 'BLACK']:
            standardized_data['status'] = 'failed'
        else:
            standardized_data['status'] = 'unknown'
        
        # 调用服务类处理回调
        success_result, message = SmsTrackingService.handle_callback(tracking, standardized_data)
        
        if success_result:
            logger.info(f"短信回调处理成功: tracking_id={tracking.id}, biz_id={biz_id}, status={standardized_data.get('status')}")
            return JsonResponse({'status': 'ok', 'message': '回调处理成功'})
        else:
            logger.error(f"短信回调处理失败: tracking_id={tracking.id}, biz_id={biz_id}, message={message}")
            return JsonResponse({'status': 'error', 'message': message}, status=500)
            
    except json.JSONDecodeError as e:
        logger.error(f"短信回调：JSON解析失败: error={str(e)}, body={request.body[:200]}")
        return JsonResponse({'status': 'error', 'message': 'JSON解析失败'}, status=400)
    except Exception as e:
        logger.error(f"短信回调处理异常: error={str(e)}", exc_info=True)
        return JsonResponse({'status': 'error', 'message': f'处理失败：{str(e)}'}, status=500)

