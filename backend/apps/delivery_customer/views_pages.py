from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.urls import reverse, NoReverseMatch
from django.utils import timezone
from django.db.models import F
from datetime import timedelta
import logging

from backend.apps.system_management.services import get_user_permission_codes
from backend.core.views import HOME_NAV_STRUCTURE, _permission_granted, _build_full_top_nav, _build_scene_groups

logger = logging.getLogger(__name__)


# 使用统一的顶部导航菜单生成函数（已从 backend.core.views 导入）


# ==================== 收发管理模块左侧菜单结构 =====================
DELIVERY_MANAGEMENT_MENU = [
    {
        'id': 'incoming_document',
        'label': '收文管理',
        'icon': '📥',
        'permission': 'delivery_center.view',
        'children': [
            {
                'id': 'incoming_document_list',
                'label': '创建收文',
                'icon': '📋',
                'url_name': 'delivery_pages:incoming_document_list',
                'permission': 'delivery_center.view',
            },
        ]
    },
    {
        'id': 'outgoing_document',
        'label': '发文管理',
        'icon': '📤',
        'permission': 'delivery_center.view',
        'children': [
            {
                'id': 'outgoing_document_list',
                'label': '创建发文',
                'icon': '📋',
                'url_name': 'delivery_pages:outgoing_document_list',
                'permission': 'delivery_center.view',
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
    
    # URL路径到菜单ID的映射
    path_to_id_map = {
        '/incoming-document/': 'incoming_document_list',
        '/outgoing-document/': 'outgoing_document_list',
        '/express-company/': 'express_company_list',
        '/file-category/manage': 'file_category_manage',
        '/file-template/manage': 'file_template_manage',
    }
    
    for path_pattern, menu_id in path_to_id_map.items():
        if path_pattern in request_path:
            return menu_id
    
    return None


def _build_delivery_sidebar_nav(permission_set, request_path=None, active_id=None):
    """
    生成收发管理模块左侧菜单
    
    参数:
        permission_set: 用户权限集合（set）
        request_path: 请求路径（可选，用于推断active_id）
        active_id: 当前激活的菜单项ID（可选，如果提供则优先使用）
    
    返回:
        list: 菜单项列表，每个菜单项包含：
            - id: 菜单项ID
            - label: 菜单项标签
            - icon: 菜单项图标
            - url: 菜单项URL（如果有）
            - active: 是否激活
            - expanded: 是否展开
            - children: 子菜单项列表（如果有）
    """
    # 如果没有提供active_id，尝试从request_path推断
    if active_id is None and request_path:
        active_id = _get_active_id_from_path(request_path)
    
    menu = []
    
    for menu_group in DELIVERY_MANAGEMENT_MENU:
        # 检查父菜单权限
        permission = menu_group.get('permission')
        if permission and not _permission_granted(permission, permission_set):
            continue
        
        # 处理子菜单
        children = []
        for child in menu_group.get('children', []):
            # 检查子菜单权限
            if not _permission_granted(child.get('permission'), permission_set):
                continue
            
            # 获取URL
            url_name = child.get('url_name')
            url = '#'
            if url_name:
                try:
                    url = reverse(url_name)
                except NoReverseMatch:
                    url = '#'
            
            # 判断是否激活
            is_active = child.get('id') == active_id
            
            children.append({
                'id': child.get('id'),
                'label': child.get('label'),
                'icon': child.get('icon'),
                'url': url,
                'active': is_active,
            })
        
        # 如果父菜单没有可见的子菜单，跳过
        if not children:
            continue
        
        # 判断父菜单是否激活（任意子菜单激活则父菜单激活）
        group_active = any(child.get('id') == active_id for child in menu_group.get('children', []))
        
        menu.append({
            'id': menu_group.get('id'),
            'label': menu_group.get('label'),
            'icon': menu_group.get('icon'),
            'active': group_active,
            'expanded': group_active,  # 如果有激活项，默认展开（与商机管理格式一致）
            'children': children,
        })
    
    return menu


def _context(page_title, page_icon, description, summary_cards=None, sections=None, request=None):
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
        # 添加左侧菜单
        context['sidebar_nav'] = _build_delivery_sidebar_nav(permission_set, request.path)
        context['sidebar_title'] = '交付客户'
        context['sidebar_subtitle'] = 'Delivery Customer'
    else:
        context['full_top_nav'] = []
        context['sidebar_nav'] = []
    
    return context


@login_required
def report_delivery(request):
    """收发管理首页 - 新版本：直接跳转到交付记录列表页"""
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
    
    # 添加左侧菜单
    delivery_sidebar_nav = _build_delivery_sidebar_nav(permission_set, request.path)
    
    context = {
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
        "delivery_sidebar_nav": delivery_sidebar_nav,
        "sidebar_nav": delivery_sidebar_nav,  # 添加此变量以兼容模板中的变量检查
    }
    
    # 为所有可能的侧边栏变量设置默认值，避免模板错误
    # 这些变量可能在其他模块的模板中被引用
    context.setdefault('sidebar_nav', [])
    context.setdefault('sidebar_nav', [])
    context.setdefault('sidebar_nav', [])
    context.setdefault('sidebar_nav', [])
    context.setdefault('sidebar_nav', [])
    context.setdefault('sidebar_nav', [])
    context.setdefault('sidebar_nav', [])
    
    return render(request, "delivery_customer/delivery_list.html", context)


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
    delivery_sidebar_nav = _build_delivery_sidebar_nav(permission_set, request.path)
    
    return render(request, "delivery_customer/delivery_create.html", {
        "page_title": "创建交付单",
        "page_icon": "🧾",
        "projects": projects,
        "clients": clients,
        "full_top_nav": _build_full_top_nav(permission_set, request.user),
        "delivery_sidebar_nav": delivery_sidebar_nav,
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
    delivery_sidebar_nav = _build_delivery_sidebar_nav(permission_set, request.path)
    
    return render(request, "delivery_customer/delivery_detail.html", {
        "page_title": "交付详情",
        "page_icon": "📋",
        "delivery": delivery,
        "can_edit": can_edit,
        "can_submit": can_submit,
        "full_top_nav": _build_full_top_nav(permission_set, request.user),
        "delivery_sidebar_nav": delivery_sidebar_nav,
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
    delivery_sidebar_nav = _build_delivery_sidebar_nav(permission_set, request.path)
    
    return render(request, "delivery_customer/delivery_edit.html", {
        "page_title": "编辑交付记录",
        "page_icon": "✏️",
        "delivery": delivery,
        "projects": projects,
        "clients": clients,
        "full_top_nav": _build_full_top_nav(permission_set, request.user),
        "delivery_sidebar_nav": delivery_sidebar_nav,
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
    delivery_sidebar_nav = _build_delivery_sidebar_nav(permission_set, request.path)
    
    return render(request, "delivery_customer/delivery_delete_confirm.html", {
        "page_title": "删除交付记录",
        "page_icon": "🗑️",
        "delivery": delivery,
        "full_top_nav": _build_full_top_nav(permission_set, request.user),
        "delivery_sidebar_nav": delivery_sidebar_nav,
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
    delivery_sidebar_nav = _build_delivery_sidebar_nav(permission_set, request.path)
    
    return render(request, "delivery_customer/delivery_submit_confirm.html", {
        "page_title": "提交交付记录",
        "page_icon": "📤",
        "delivery": delivery,
        "full_top_nav": _build_full_top_nav(permission_set, request.user),
        "delivery_sidebar_nav": delivery_sidebar_nav,
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
    delivery_sidebar_nav = _build_delivery_sidebar_nav(permission_set, request.path)
    
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
        "delivery_sidebar_nav": delivery_sidebar_nav,
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
    delivery_sidebar_nav = _build_delivery_sidebar_nav(permission_set, request.path)
    
    return render(request, "delivery_customer/delivery_warnings.html", {
        "page_title": "风险预警",
        "page_icon": "⚠️",
        "overdue_deliveries": page,
        "risk_level_filter": risk_level,
        "risk_stats": risk_stats,
        "total_overdue": DeliveryRecord.objects.filter(is_overdue=True).count(),
        "full_top_nav": _build_full_top_nav(permission_set, request.user),
        "delivery_sidebar_nav": delivery_sidebar_nav,
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
    delivery_sidebar_nav = _build_delivery_sidebar_nav(permission_set, request.path)
    
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
        "delivery_sidebar_nav": delivery_sidebar_nav,
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
    delivery_sidebar_nav = _build_delivery_sidebar_nav(permission_set, request.path)
    
    return render(request, "delivery_customer/delivery_approval_detail.html", {
        "page_title": "交付审核详情",
        "page_icon": "✅",
        "delivery": delivery,
        "can_approve": can_approve,
        "can_perform_approval": can_perform_approval,
        "approval_history": approval_history,
        "pending_approval": pending_approval,
        "full_top_nav": _build_full_top_nav(permission_set, request.user),
        "delivery_sidebar_nav": delivery_sidebar_nav,
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
    delivery_sidebar_nav = _build_delivery_sidebar_nav(permission_set, request.path)
    
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
        "delivery_sidebar_nav": delivery_sidebar_nav,
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
    delivery_sidebar_nav = _build_delivery_sidebar_nav(permission_set, request.path)
    
    return render(request, "delivery_customer/delivery_email_send.html", {
        "page_title": "发送邮件",
        "page_icon": "📧",
        "delivery": delivery,
        "can_send": can_send,
        "full_top_nav": _build_full_top_nav(permission_set, request.user),
        "delivery_sidebar_nav": delivery_sidebar_nav,
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
    delivery_sidebar_nav = _build_delivery_sidebar_nav(permission_set, request.path)
    
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
        "delivery_sidebar_nav": delivery_sidebar_nav,
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
    delivery_sidebar_nav = _build_delivery_sidebar_nav(permission_set, request.path)
    
    return render(request, "delivery_customer/delivery_express_send.html", {
        "page_title": "寄送快递",
        "page_icon": "📦",
        "delivery": delivery,
        "can_send": can_send,
        "express_companies": express_companies,
        "full_top_nav": _build_full_top_nav(permission_set, request.user),
        "delivery_sidebar_nav": delivery_sidebar_nav,
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
    delivery_sidebar_nav = _build_delivery_sidebar_nav(permission_set, request.path)
    
    return render(request, "delivery_customer/delivery_receipt_list.html", {
        "page_title": "签收确认",
        "page_icon": "✅",
        "receipt_deliveries": page,
        "receipt_status": receipt_status,
        "pending_count": pending_count,
        "received_count": received_count,
        "rejected_count": rejected_count,
        "full_top_nav": _build_full_top_nav(permission_set, request.user),
        "delivery_sidebar_nav": delivery_sidebar_nav,
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
    delivery_sidebar_nav = _build_delivery_sidebar_nav(permission_set, request.path)
    
    return render(request, "delivery_customer/delivery_receipt_confirm.html", {
        "page_title": "签收确认",
        "page_icon": "✅",
        "delivery": delivery,
        "can_confirm": can_confirm,
        "can_reject": can_reject,
        "full_top_nav": _build_full_top_nav(permission_set, request.user),
        "delivery_sidebar_nav": delivery_sidebar_nav,
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
    delivery_sidebar_nav = _build_delivery_sidebar_nav(permission_set, request.path)
    
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
        "delivery_sidebar_nav": delivery_sidebar_nav,
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
    delivery_sidebar_nav = _build_delivery_sidebar_nav(permission_set, request.path)
    
    return render(request, "delivery_customer/delivery_hand_delivery_confirm.html", {
        "page_title": "现场送达确认",
        "page_icon": "🚶",
        "delivery": delivery,
        "can_deliver": can_deliver,
        "users": users,
        "full_top_nav": _build_full_top_nav(permission_set, request.user),
        "delivery_sidebar_nav": delivery_sidebar_nav,
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
    delivery_sidebar_nav = _build_delivery_sidebar_nav(permission_set, request.path)
    
    return render(request, "delivery_customer/delivery_receive_list.html", {
        "page_title": "收件确认",
        "page_icon": "📥",
        "receive_deliveries": page,
        "receive_status": receive_status,
        "pending_count": pending_count,
        "received_count": received_count,
        "full_top_nav": _build_full_top_nav(permission_set, request.user),
        "delivery_sidebar_nav": delivery_sidebar_nav,
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
    delivery_sidebar_nav = _build_delivery_sidebar_nav(permission_set, request.path)
    
    return render(request, "delivery_customer/delivery_receive_confirm.html", {
        "page_title": "收件确认",
        "page_icon": "📥",
        "delivery": delivery,
        "can_confirm": can_confirm,
        "full_top_nav": _build_full_top_nav(permission_set, request.user),
        "delivery_sidebar_nav": delivery_sidebar_nav,
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
    delivery_sidebar_nav = _build_delivery_sidebar_nav(permission_set, request.path)
    
    return render(request, "delivery_customer/delivery_feedback_list.html", {
        "page_title": "客户反馈",
        "page_icon": "💬",
        "feedback_deliveries": page,
        "feedback_status": feedback_status,
        "pending_count": pending_count,
        "received_count": received_count,
        "full_top_nav": _build_full_top_nav(permission_set, request.user),
        "delivery_sidebar_nav": delivery_sidebar_nav,
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
    delivery_sidebar_nav = _build_delivery_sidebar_nav(permission_set, request.path)
    
    return render(request, "delivery_customer/delivery_feedback_create.html", {
        "page_title": "客户反馈",
        "page_icon": "💬",
        "delivery": delivery,
        "can_create_feedback": can_create_feedback,
        "feedback_types": feedback_types,
        "full_top_nav": _build_full_top_nav(permission_set, request.user),
        "delivery_sidebar_nav": delivery_sidebar_nav,
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
    delivery_sidebar_nav = _build_delivery_sidebar_nav(permission_set, request.path)
    
    return render(request, "delivery_customer/delivery_achievement_list.html", {
        "page_title": "成果确认",
        "page_icon": "✅",
        "achievement_deliveries": page,
        "confirmation_status": confirmation_status,
        "pending_count": pending_count,
        "confirmed_count": confirmed_count,
        "rejected_count": rejected_count,
        "full_top_nav": _build_full_top_nav(permission_set, request.user),
        "delivery_sidebar_nav": delivery_sidebar_nav,
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
    delivery_sidebar_nav = _build_delivery_sidebar_nav(permission_set, request.path)
    
    return render(request, "delivery_customer/delivery_achievement_confirm.html", {
        "page_title": "成果确认",
        "page_icon": "✅",
        "delivery": delivery,
        "can_confirm": can_confirm,
        "confirmation_history": confirmation_history,
        "full_top_nav": _build_full_top_nav(permission_set, request.user),
        "delivery_sidebar_nav": delivery_sidebar_nav,
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
    delivery_sidebar_nav = _build_delivery_sidebar_nav(permission_set, request.path)
    
    return render(request, "delivery_customer/delivery_satisfaction_list.html", {
        "page_title": "满意度评价",
        "page_icon": "⭐",
        "satisfaction_deliveries": page,
        "satisfaction_status": satisfaction_status,
        "pending_count": pending_count,
        "rated_count": rated_count,
        "full_top_nav": _build_full_top_nav(permission_set, request.user),
        "delivery_sidebar_nav": delivery_sidebar_nav,
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
    delivery_sidebar_nav = _build_delivery_sidebar_nav(permission_set, request.path)
    
    return render(request, "delivery_customer/delivery_satisfaction_create.html", {
        "page_title": "满意度评价",
        "page_icon": "⭐",
        "delivery": delivery,
        "can_create_satisfaction": can_create_satisfaction,
        "has_rated": has_rated,
        "satisfaction_dimensions": satisfaction_dimensions,
        "full_top_nav": _build_full_top_nav(permission_set, request.user),
        "delivery_sidebar_nav": delivery_sidebar_nav,
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
    delivery_sidebar_nav = _build_delivery_sidebar_nav(permission_set, request.path)
    
    return render(request, "delivery_customer/delivery_satisfaction_statistics.html", {
        "page_title": "满意度统计",
        "page_icon": "📊",
        "total_count": total_count,
        "avg_rating": avg_rating,
        "rating_distribution": rating_distribution,
        "recent_ratings": recent_ratings,
        "full_top_nav": _build_full_top_nav(permission_set, request.user),
        "delivery_sidebar_nav": delivery_sidebar_nav,
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
    delivery_sidebar_nav = _build_delivery_sidebar_nav(permission_set, request.path)
    
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
        "delivery_sidebar_nav": delivery_sidebar_nav,
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
    delivery_sidebar_nav = _build_delivery_sidebar_nav(permission_set, request.path)
    
    return render(request, "delivery_customer/delivery_logistics_detail.html", {
        "page_title": "物流跟踪",
        "page_icon": "🚚",
        "delivery": delivery,
        "tracking_records": tracking_records,
        "logistics_timeline": logistics_timeline,
        "full_top_nav": _build_full_top_nav(permission_set, request.user),
        "delivery_sidebar_nav": delivery_sidebar_nav,
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
    delivery_sidebar_nav = _build_delivery_sidebar_nav(permission_set, request.path)
    
    return render(request, "delivery_customer/delivery_weekly_report_list.html", {
        "page_title": "每周快报",
        "page_icon": "📰",
        "weekly_reports": page,
        "project_id": project_id,
        "week_number": week_number,
        "full_process_projects": full_process_projects,
        "total_count": total_count,
        "full_top_nav": _build_full_top_nav(permission_set, request.user),
        "delivery_sidebar_nav": delivery_sidebar_nav,
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
    delivery_sidebar_nav = _build_delivery_sidebar_nav(permission_set, request.path)
    
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
        "delivery_sidebar_nav": delivery_sidebar_nav,
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
    delivery_sidebar_nav = _build_delivery_sidebar_nav(permission_set, request.path)
    
    return render(request, "delivery_customer/delivery_file_prep_upload.html", {
        "page_title": "上传文件",
        "page_icon": "📝",
        "draft_deliveries": draft_deliveries,
        "projects": projects,
        "full_top_nav": _build_full_top_nav(permission_set, request.user),
        "delivery_sidebar_nav": delivery_sidebar_nav,
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
    delivery_sidebar_nav = _build_delivery_sidebar_nav(permission_set, request.path)
    
    return render(request, "delivery_customer/delivery_weekly_report_create.html", {
        "page_title": "创建每周快报",
        "page_icon": "📰",
        "full_process_projects": full_process_projects,
        "full_top_nav": _build_full_top_nav(permission_set, request.user),
        "delivery_sidebar_nav": delivery_sidebar_nav,
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
    """收文管理首页 - 数据展示中心"""
    from django.db.models import Avg, Count
    from datetime import datetime
    from backend.apps.delivery_customer.models import IncomingDocument
    
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
            'url': reverse('delivery_pages:incoming_document_list'),
            'variant': 'secondary'
        })
        
        # 卡片2：处理中收文
        core_cards.append({
            'label': '处理中收文',
            'icon': '⚡',
            'value': str(processing_documents),
            'subvalue': f'已登记 {registered_documents} | 处理中 {processing_documents}',
            'url': reverse('delivery_pages:incoming_document_list') + '?status=processing',
            'variant': 'dark'
        })
        
        # 卡片3：已完成收文
        core_cards.append({
            'label': '已完成收文',
            'icon': '✅',
            'value': str(completed_documents),
            'subvalue': f'本月完成 {this_month_completed_documents} 个',
            'url': reverse('delivery_pages:incoming_document_list') + '?status=completed',
            'variant': 'secondary'
        })
        
        # 卡片4：待登记收文
        core_cards.append({
            'label': '待登记收文',
            'icon': '📋',
            'value': str(draft_documents),
            'subvalue': f'等待登记',
            'url': reverse('delivery_pages:incoming_document_list') + '?status=draft',
            'variant': 'dark' if draft_documents > 0 else 'secondary'
        })
        
        # 卡片5：已登记收文
        core_cards.append({
            'label': '已登记收文',
            'icon': '📝',
            'value': str(registered_documents),
            'subvalue': f'等待处理',
            'url': reverse('delivery_pages:incoming_document_list') + '?status=registered',
            'variant': 'dark' if registered_documents > 0 else 'secondary'
        })
        
        # 卡片6：本月新增
        core_cards.append({
            'label': '本月新增',
            'icon': '📈',
            'value': str(this_month_documents),
            'subvalue': f'新收文 {this_month_documents} 个',
            'url': reverse('delivery_pages:incoming_document_list'),
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
                'url': reverse('delivery_pages:incoming_document_detail', args=[doc.id])
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
                'url': reverse('delivery_pages:incoming_document_detail', args=[doc.id])
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
                'url': reverse('delivery_pages:incoming_document_detail', args=[doc.id])
            })
        
        context['todo_items'] = todo_items[:10]
        context['pending_approval_count'] = draft_documents + processing_documents
        context['todo_summary_url'] = reverse('delivery_pages:incoming_document_list') + '?status=draft'
        
        # ========== 我的工作 ==========
        my_work = {}
        
        # 我创建的收文
        my_created_documents = all_documents.filter(created_by=request.user).order_by('-created_at')[:3]
        my_work['my_documents'] = [{
            'title': doc.title,
            'status': doc.get_status_display(),
            'url': reverse('delivery_pages:incoming_document_detail', args=[doc.id])
        } for doc in my_created_documents]
        my_work['my_documents_count'] = all_documents.filter(created_by=request.user).count()
        
        # 我处理的收文
        my_handled_documents = all_documents.filter(handler=request.user).order_by('-updated_at')[:3]
        my_work['handled_documents'] = [{
            'title': doc.title,
            'status': doc.get_status_display(),
            'url': reverse('delivery_pages:incoming_document_detail', args=[doc.id])
        } for doc in my_handled_documents]
        my_work['handled_documents_count'] = all_documents.filter(handler=request.user).count()
        
        my_work['summary_url'] = reverse('delivery_pages:incoming_document_list') + f'?created_by={request.user.id}'
        
        context['my_work'] = my_work
        
        # ========== 最近活动 ==========
        recent_activities = {}
        
        # 最近创建的收文
        recent_documents = all_documents.select_related('created_by').order_by('-created_at')[:5]
        recent_activities['recent_documents'] = [{
            'title': doc.title,
            'creator': _format_user_display(doc.created_by),
            'time': doc.created_at,
            'url': reverse('delivery_pages:incoming_document_detail', args=[doc.id])
        } for doc in recent_documents]
        
        # 最近更新的收文（排除创建）
        recent_updates = all_documents.exclude(
            created_at=F('updated_at')
        ).select_related('updated_by').order_by('-updated_at')[:5]
        recent_activities['recent_updates'] = [{
            'title': doc.title,
            'updater': _format_user_display(doc.handler) if doc.handler else '系统',
            'time': doc.updated_at,
            'url': reverse('delivery_pages:incoming_document_detail', args=[doc.id])
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
                'url': reverse('delivery_pages:incoming_document_create'),
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
    
    # 设置侧边栏导航
    delivery_sidebar_nav = _build_delivery_sidebar_nav(permission_set, request.path, active_id='incoming_document_home')
    page_context['sidebar_nav'] = delivery_sidebar_nav
    page_context['sidebar_nav'] = delivery_sidebar_nav
    page_context['sidebar_title'] = '收发管理'
    page_context['sidebar_subtitle'] = 'Delivery Management'
    
    # 合并所有数据
    page_context.update(context)
    
    return render(request, "delivery_customer/incoming_document_home.html", page_context)


@login_required
def incoming_document_list(request):
    """收文列表"""
    from django.core.paginator import Paginator
    from django.db.models import Q
    from backend.apps.delivery_customer.models import IncomingDocument
    
    permission_set = get_user_permission_codes(request.user)
    delivery_sidebar_nav = _build_delivery_sidebar_nav(permission_set, request.path, active_id='incoming_document_list')
    
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
    from backend.apps.delivery_customer.models import FileCategory
    categories = FileCategory.objects.filter(is_active=True).order_by('stage', 'sort_order', 'name')
    categories_by_stage = {}
    for category in categories:
        if category.stage not in categories_by_stage:
            categories_by_stage[category.stage] = []
        categories_by_stage[category.stage].append(category)
    
    # 生成左侧菜单（类似计划管理的 plan_menu）
    context['sidebar_nav'] = delivery_sidebar_nav
    context['sidebar_nav'] = delivery_sidebar_nav  # 兼容模板中的变量名
    context['sidebar_title'] = '收发管理'  # 侧边栏标题
    context['sidebar_subtitle'] = 'Delivery Management'  # 侧边栏副标题
    
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
    delivery_sidebar_nav = _build_delivery_sidebar_nav(permission_set, request.path)
    
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
    
    context["delivery_sidebar_nav"] = delivery_sidebar_nav
    context["sidebar_nav"] = delivery_sidebar_nav  # 兼容模板中的变量名
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
    delivery_sidebar_nav = _build_delivery_sidebar_nav(permission_set, request.path)
    
    document = get_object_or_404(IncomingDocument, id=document_id)
    
    context = _context(
        "收文详情",
        "📥",
        "查看收文详细信息",
        request=request,
    )
    context["delivery_sidebar_nav"] = delivery_sidebar_nav
    context["sidebar_nav"] = delivery_sidebar_nav  # 兼容模板中的变量名
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
    delivery_sidebar_nav = _build_delivery_sidebar_nav(permission_set, request.path)
    
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
    
    context["delivery_sidebar_nav"] = delivery_sidebar_nav
    context["sidebar_nav"] = delivery_sidebar_nav  # 兼容模板中的变量名
    context["document"] = document
    context["status_choices"] = IncomingDocument.STATUS_CHOICES
    context["priority_choices"] = IncomingDocument.PRIORITY_CHOICES
    context["stage_choices"] = IncomingDocument.STAGE_CHOICES
    context["categories"] = categories
    context["categories_by_stage"] = categories_by_stage
    context["users"] = users
    return render(request, "delivery_customer/incoming_document_edit.html", context)


# ==================== 发文管理 ====================

@login_required
def outgoing_document_home(request):
    """发文管理首页 - 数据展示中心"""
    from django.db.models import Avg, Count
    from datetime import datetime
    from backend.apps.delivery_customer.models import OutgoingDocument
    
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
            'url': reverse('delivery_pages:outgoing_document_list'),
            'variant': 'secondary'
        })
        
        # 卡片2：审核中发文
        core_cards.append({
            'label': '审核中发文',
            'icon': '⚡',
            'value': str(reviewing_documents),
            'subvalue': f'等待审核 {reviewing_documents} 个',
            'url': reverse('delivery_pages:outgoing_document_list') + '?status=reviewing',
            'variant': 'dark'
        })
        
        # 卡片3：已完成发文
        core_cards.append({
            'label': '已完成发文',
            'icon': '✅',
            'value': str(completed_documents),
            'subvalue': f'本月完成 {this_month_completed_documents} 个',
            'url': reverse('delivery_pages:outgoing_document_list') + '?status=completed',
            'variant': 'secondary'
        })
        
        # 卡片4：待审核发文
        core_cards.append({
            'label': '待审核发文',
            'icon': '📋',
            'value': str(reviewing_documents),
            'subvalue': f'等待审核',
            'url': reverse('delivery_pages:outgoing_document_list') + '?status=reviewing',
            'variant': 'dark' if reviewing_documents > 0 else 'secondary'
        })
        
        # 卡片5：已批准发文
        core_cards.append({
            'label': '已批准发文',
            'icon': '📝',
            'value': str(approved_documents),
            'subvalue': f'等待发出',
            'url': reverse('delivery_pages:outgoing_document_list') + '?status=approved',
            'variant': 'dark' if approved_documents > 0 else 'secondary'
        })
        
        # 卡片6：本月新增
        core_cards.append({
            'label': '本月新增',
            'icon': '📈',
            'value': str(this_month_documents),
            'subvalue': f'新发文 {this_month_documents} 个',
            'url': reverse('delivery_pages:outgoing_document_list'),
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
                'url': reverse('delivery_pages:outgoing_document_detail', args=[doc.id])
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
                'url': reverse('delivery_pages:outgoing_document_detail', args=[doc.id])
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
                'url': reverse('delivery_pages:outgoing_document_detail', args=[doc.id])
            })
        
        context['todo_items'] = todo_items[:10]
        context['pending_approval_count'] = reviewing_documents + approved_documents
        context['todo_summary_url'] = reverse('delivery_pages:outgoing_document_list') + '?status=reviewing'
        
        # ========== 我的工作 ==========
        my_work = {}
        
        # 我创建的发文
        my_created_documents = all_documents.filter(created_by=request.user).order_by('-created_at')[:3]
        my_work['my_documents'] = [{
            'title': doc.title,
            'status': doc.get_status_display(),
            'url': reverse('delivery_pages:outgoing_document_detail', args=[doc.id])
        } for doc in my_created_documents]
        my_work['my_documents_count'] = all_documents.filter(created_by=request.user).count()
        
        # 我审核的发文
        my_reviewed_documents = all_documents.filter(reviewer=request.user).order_by('-updated_at')[:3]
        my_work['reviewed_documents'] = [{
            'title': doc.title,
            'status': doc.get_status_display(),
            'url': reverse('delivery_pages:outgoing_document_detail', args=[doc.id])
        } for doc in my_reviewed_documents]
        my_work['reviewed_documents_count'] = all_documents.filter(reviewer=request.user).count()
        
        my_work['summary_url'] = reverse('delivery_pages:outgoing_document_list') + f'?created_by={request.user.id}'
        
        context['my_work'] = my_work
        
        # ========== 最近活动 ==========
        recent_activities = {}
        
        # 最近创建的发文
        recent_documents = all_documents.select_related('created_by').order_by('-created_at')[:5]
        recent_activities['recent_documents'] = [{
            'title': doc.title,
            'creator': _format_user_display(doc.created_by),
            'time': doc.created_at,
            'url': reverse('delivery_pages:outgoing_document_detail', args=[doc.id])
        } for doc in recent_documents]
        
        # 最近更新的发文（排除创建）
        recent_updates = all_documents.exclude(
            created_at=F('updated_at')
        ).select_related('reviewer').order_by('-updated_at')[:5]
        recent_activities['recent_updates'] = [{
            'title': doc.title,
            'updater': _format_user_display(doc.reviewer) if doc.reviewer else '系统',
            'time': doc.updated_at,
            'url': reverse('delivery_pages:outgoing_document_detail', args=[doc.id])
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
                'url': reverse('delivery_pages:outgoing_document_create'),
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
    
    # 设置侧边栏导航
    delivery_sidebar_nav = _build_delivery_sidebar_nav(permission_set, request.path, active_id='outgoing_document_home')
    page_context['sidebar_nav'] = delivery_sidebar_nav
    page_context['sidebar_nav'] = delivery_sidebar_nav
    page_context['sidebar_title'] = '收发管理'
    page_context['sidebar_subtitle'] = 'Delivery Management'
    
    # 合并所有数据
    page_context.update(context)
    
    return render(request, "delivery_customer/outgoing_document_home.html", page_context)


@login_required
def outgoing_document_list(request):
    """发文列表"""
    from django.core.paginator import Paginator
    from django.db.models import Q
    from backend.apps.delivery_customer.models import OutgoingDocument
    
    permission_set = get_user_permission_codes(request.user)
    delivery_sidebar_nav = _build_delivery_sidebar_nav(permission_set, request.path, active_id='outgoing_document_list')
    
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
    from backend.apps.delivery_customer.models import FileCategory
    categories = FileCategory.objects.filter(is_active=True).order_by('stage', 'sort_order', 'name')
    categories_by_stage = {}
    for category in categories:
        if category.stage not in categories_by_stage:
            categories_by_stage[category.stage] = []
        categories_by_stage[category.stage].append(category)
    
    # 生成左侧菜单（类似计划管理的 plan_menu）
    context['sidebar_nav'] = delivery_sidebar_nav
    context['sidebar_nav'] = delivery_sidebar_nav  # 兼容模板中的变量名
    context['sidebar_title'] = '收发管理'  # 侧边栏标题
    context['sidebar_subtitle'] = 'Delivery Management'  # 侧边栏副标题
    
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
    return render(request, "delivery_customer/outgoing_document_list.html", context)


@login_required
def outgoing_document_create(request):
    """发文创建"""
    from django.shortcuts import redirect
    from django.contrib import messages
    from django.utils import timezone
    from backend.apps.delivery_customer.models import OutgoingDocument
    
    permission_set = get_user_permission_codes(request.user)
    delivery_sidebar_nav = _build_delivery_sidebar_nav(permission_set, request.path)
    
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
            return redirect('delivery_pages:outgoing_document_detail', document_id=document.id)
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
    
    # 获取项目列表（只显示有项目编号的项目，项目编号来源于业务委托书或合同）
    from backend.apps.production_management.models import Project, BusinessContract
    from backend.apps.customer_management.models import AuthorizationLetter
    from django.db.models import Q
    
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
    context["delivery_sidebar_nav"] = delivery_sidebar_nav
    context["sidebar_nav"] = delivery_sidebar_nav  # 兼容模板中的变量名
    context["status_choices"] = OutgoingDocument.STATUS_CHOICES
    context["priority_choices"] = OutgoingDocument.PRIORITY_CHOICES
    context["stage_choices"] = OutgoingDocument.STAGE_CHOICES
    context["categories"] = categories
    context["categories_by_stage"] = categories_by_stage
    context["users"] = users
    context["projects"] = projects
    return render(request, "delivery_customer/outgoing_document_create.html", context)


@login_required
def outgoing_document_detail(request, document_id):
    """发文详情"""
    from django.shortcuts import get_object_or_404
    from backend.apps.delivery_customer.models import OutgoingDocument
    
    permission_set = get_user_permission_codes(request.user)
    delivery_sidebar_nav = _build_delivery_sidebar_nav(permission_set, request.path)
    
    document = get_object_or_404(OutgoingDocument, id=document_id)
    
    context = _context(
        "发文详情",
        "📤",
        "查看发文详细信息",
        request=request,
    )
    context["delivery_sidebar_nav"] = delivery_sidebar_nav
    context["sidebar_nav"] = delivery_sidebar_nav  # 兼容模板中的变量名
    context["document"] = document
    context["can_edit"] = _permission_granted('delivery_center.create', permission_set)
    return render(request, "delivery_customer/outgoing_document_detail.html", context)


@login_required
def outgoing_document_edit(request, document_id):
    """发文编辑"""
    from django.shortcuts import redirect, get_object_or_404
    from django.contrib import messages
    from backend.apps.delivery_customer.models import OutgoingDocument
    
    permission_set = get_user_permission_codes(request.user)
    delivery_sidebar_nav = _build_delivery_sidebar_nav(permission_set, request.path)
    
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
    
    # 获取项目列表（只显示有项目编号的项目，项目编号来源于业务委托书或合同）
    from backend.apps.production_management.models import Project, BusinessContract
    from backend.apps.customer_management.models import AuthorizationLetter
    from django.db.models import Q
    
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
    
    context["delivery_sidebar_nav"] = delivery_sidebar_nav
    context["sidebar_nav"] = delivery_sidebar_nav  # 兼容模板中的变量名
    context["document"] = document
    context["document"].delivery_methods_list = delivery_methods_list  # 添加属性到document对象
    context["status_choices"] = OutgoingDocument.STATUS_CHOICES
    context["priority_choices"] = OutgoingDocument.PRIORITY_CHOICES
    context["stage_choices"] = OutgoingDocument.STAGE_CHOICES
    context["categories"] = categories
    context["categories_by_stage"] = categories_by_stage
    context["users"] = users
    context["projects"] = projects
    return render(request, "delivery_customer/outgoing_document_edit.html", context)


# ==================== 快递公司管理 ====================

@login_required
def express_company_list(request):
    """快递公司列表"""
    from django.core.paginator import Paginator
    from django.db.models import Q
    from backend.apps.delivery_customer.models import ExpressCompany
    
    permission_set = get_user_permission_codes(request.user)
    delivery_sidebar_nav = _build_delivery_sidebar_nav(permission_set, request.path)
    
    # 获取查询参数
    search_query = request.GET.get('search', '').strip()
    status_filter = request.GET.get('status', 'all')  # all, active, inactive
    page = request.GET.get('page', 1)
    
    # 查询快递公司
    companies = ExpressCompany.objects.all()
    
    # 搜索过滤
    if search_query:
        companies = companies.filter(
            Q(name__icontains=search_query) |
            Q(code__icontains=search_query) |
            Q(alias__icontains=search_query) |
            Q(contact_phone__icontains=search_query)
        )
    
    # 状态过滤
    if status_filter == 'active':
        companies = companies.filter(is_active=True)
    elif status_filter == 'inactive':
        companies = companies.filter(is_active=False)
    
    # 分页
    page_size = request.GET.get('page_size', '10')
    try:
        per_page = int(page_size)
        if per_page not in [10, 20, 50]:
            per_page = 10
    except (ValueError, TypeError):
        per_page = 10
    paginator = Paginator(companies, per_page)
    try:
        companies_page = paginator.page(page)
    except:
        companies_page = paginator.page(1)
    
    context = _context(
        "快递公司列表",
        "🚚",
        "管理快递公司信息",
        request=request,
    )
    context["delivery_sidebar_nav"] = delivery_sidebar_nav
    context["sidebar_nav"] = delivery_sidebar_nav  # 兼容模板中的变量名
    context["companies"] = companies_page
    context["search_query"] = search_query
    context["status_filter"] = status_filter
    context["can_create"] = _permission_granted('delivery_center.create', permission_set)
    return render(request, "delivery_customer/express_company_list.html", context)


@login_required
def express_company_create(request):
    """创建快递公司"""
    from django.shortcuts import redirect
    from django.contrib import messages
    from backend.apps.delivery_customer.models import ExpressCompany
    
    permission_set = get_user_permission_codes(request.user)
    delivery_sidebar_nav = _build_delivery_sidebar_nav(permission_set, request.path)
    
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
    context["delivery_sidebar_nav"] = delivery_sidebar_nav
    context["sidebar_nav"] = delivery_sidebar_nav  # 兼容模板中的变量名
    return render(request, "delivery_customer/express_company_create.html", context)


@login_required
def express_company_detail(request, company_id):
    """快递公司详情"""
    from django.shortcuts import get_object_or_404
    from backend.apps.delivery_customer.models import ExpressCompany, DeliveryRecord
    
    permission_set = get_user_permission_codes(request.user)
    delivery_sidebar_nav = _build_delivery_sidebar_nav(permission_set, request.path)
    
    company = get_object_or_404(ExpressCompany, id=company_id)
    
    # 统计使用次数
    usage_count = DeliveryRecord.objects.filter(express_company=company.name).count()
    
    context = _context(
        "快递公司详情",
        "🚚",
        "查看快递公司详细信息",
        request=request,
    )
    context["delivery_sidebar_nav"] = delivery_sidebar_nav
    context["sidebar_nav"] = delivery_sidebar_nav  # 兼容模板中的变量名
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
    delivery_sidebar_nav = _build_delivery_sidebar_nav(permission_set, request.path)
    
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
    context["delivery_sidebar_nav"] = delivery_sidebar_nav
    context["sidebar_nav"] = delivery_sidebar_nav  # 兼容模板中的变量名
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
    delivery_sidebar_nav = _build_delivery_sidebar_nav(permission_set, request.path)
    
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
    context["delivery_sidebar_nav"] = delivery_sidebar_nav
    context["sidebar_nav"] = delivery_sidebar_nav  # 兼容模板中的变量名
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
    delivery_sidebar_nav = _build_delivery_sidebar_nav(permission_set, request.path)
    
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
    context["delivery_sidebar_nav"] = delivery_sidebar_nav
    context["sidebar_nav"] = delivery_sidebar_nav  # 兼容模板中的变量名
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
    delivery_sidebar_nav = _build_delivery_sidebar_nav(permission_set, request.path)
    
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
    context["delivery_sidebar_nav"] = delivery_sidebar_nav
    context["sidebar_nav"] = delivery_sidebar_nav  # 兼容模板中的变量名
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
    delivery_sidebar_nav = _build_delivery_sidebar_nav(permission_set, request.path)
    
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
    context["delivery_sidebar_nav"] = delivery_sidebar_nav
    context["sidebar_nav"] = delivery_sidebar_nav  # 兼容模板中的变量名
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

