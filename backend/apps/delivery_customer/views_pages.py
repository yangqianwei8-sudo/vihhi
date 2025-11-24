from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.urls import reverse, NoReverseMatch

from backend.apps.system_management.services import get_user_permission_codes
from backend.core.views import HOME_NAV_STRUCTURE, _permission_granted


def _build_full_top_nav(permission_set, user):
    """生成完整的顶部导航菜单，直接对应home页左侧菜单项（平铺结构，不再按中心分组）"""
    full_nav = []
    
    for menu_item in HOME_NAV_STRUCTURE:
        # 检查权限
        permission = menu_item.get("permission")
        if permission and not _permission_granted(permission, permission_set):
            continue
        
        # 获取URL
        url_name = menu_item.get("url_name")
        url = '#'
        if url_name and url_name != '#':
            try:
                url = reverse(url_name)
            except NoReverseMatch:
                # URL反向解析失败，使用默认值
                url = '#'
        elif url_name == '#':
            # 明确标记为无链接
            url = '#'
        
        # 特殊处理：新建项目仅对商务经理可见
        if url_name == 'project_pages:project_create':
            if user and not user.roles.filter(code='business_manager').exists():
                continue
        
        # 添加到导航（每个菜单项作为独立的导航项）
        full_nav.append({
            'label': menu_item.get("label", ""),
            'icon': menu_item.get("icon", ""),
            'url': url,
        })
    
    return full_nav


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
    else:
        context['full_top_nav'] = []
    
    return context


@login_required
def report_delivery(request):
    """交付管理首页"""
    from .models import DeliveryRecord
    from django.db.models import Q
    
    permission_set = get_user_permission_codes(request.user)
    
    # 权限检查
    if not _permission_granted('delivery_center.view', permission_set):
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("无权限访问交付管理")
    
    # 构建基础查询
    queryset = DeliveryRecord.objects.all()
    if not _permission_granted('delivery_center.view_all', permission_set):
        queryset = queryset.filter(
            Q(created_by=request.user) | 
            Q(project__team_members__user=request.user)
        ).distinct()
    
    # 从数据库获取统计数据
    try:
        total_count = queryset.count()
        pending_count = queryset.filter(status__in=['draft', 'submitted']).count()
        confirmed_count = queryset.filter(status='confirmed').count()
        overdue_count = queryset.filter(is_overdue=True).count()
    except Exception:
        # 如果表不存在，使用默认值
        total_count = 0
        pending_count = 0
        confirmed_count = 0
        overdue_count = 0
    
    context = _context(
        "交付管理",
        "📦",
        "管理成果交付、上传确认材料，并追踪客户下载与回执情况。支持邮件、快递、送达三种交付方式。",
        request=request,
        summary_cards=[
            {"label": "待交付成果", "value": str(pending_count), "hint": "等待上传或发送的成果文件"},
            {"label": "客户回执", "value": str(confirmed_count), "hint": "客户已确认的交付项目"},
            {"label": "逾期待发", "value": str(overdue_count), "hint": "超过交付期限仍未完成的任务"},
            {"label": "交付总数", "value": str(total_count), "hint": "所有交付记录总数"},
        ],
        sections=[
            {
                "title": "交付操作",
                "description": "对交付成果进行上传、推送与确认。",
                "items": [
                    {"label": "创建交付单", "description": "发起新的交付任务。", "url": "/delivery/create/", "icon": "🧾"},
                    {"label": "交付记录", "description": "查看历次交付与客户回执。", "url": "/delivery/list/", "icon": "📚"},
                    {"label": "交付统计", "description": "交付效率与及时率分析。", "url": "/delivery/statistics/", "icon": "📈"},
                    {"label": "风险预警", "description": "查看逾期交付预警。", "url": "/delivery/warnings/", "icon": "⚠️"},
                ],
            }
        ],
    )
    return render(request, "shared/center_dashboard.html", context)


@login_required
def delivery_list(request):
    """交付记录列表页"""
    from .models import DeliveryRecord
    from django.core.paginator import Paginator
    from django.db.models import Q
    
    permission_set = get_user_permission_codes(request.user)
    
    # 权限检查
    if not _permission_granted('delivery_center.view', permission_set):
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("无权限访问交付管理")
    
    # 获取查询参数
    status = request.GET.get('status', '')
    delivery_method = request.GET.get('delivery_method', '')
    search = request.GET.get('search', '')
    page_num = request.GET.get('page', 1)
    
    # 构建查询
    queryset = DeliveryRecord.objects.all()
    
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
    
    # 搜索
    if search:
        queryset = queryset.filter(
            Q(delivery_number__icontains=search) |
            Q(title__icontains=search) |
            Q(recipient_name__icontains=search) |
            Q(recipient_email__icontains=search)
        )
    
    # 排序和分页
    queryset = queryset.select_related('project', 'client', 'created_by').order_by('-created_at')
    paginator = Paginator(queryset, 20)
    page = paginator.get_page(page_num)
    
    return render(request, "delivery_customer/delivery_list.html", {
        "page_title": "交付记录",
        "page_icon": "📚",
        "deliveries": page,
        "status_filter": status,
        "method_filter": delivery_method,
        "search_query": search,
        "full_top_nav": _build_full_top_nav(permission_set, request.user),
    })


@login_required
def delivery_create(request):
    """创建交付记录页"""
    from backend.apps.project_center.models import Project
    from backend.apps.customer_success.models import Client
    
    permission_set = get_user_permission_codes(request.user)
    
    # 权限检查
    if not _permission_granted('delivery_center.create', permission_set):
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("无权限创建交付记录")
    
    # 获取项目和客户列表（用于下拉选择）
    projects = Project.objects.all().order_by('-created_at')[:100]  # 限制数量
    clients = Client.objects.all().order_by('-created_at')[:100]
    
    return render(request, "delivery_customer/delivery_create.html", {
        "page_title": "创建交付单",
        "page_icon": "🧾",
        "projects": projects,
        "clients": clients,
        "full_top_nav": _build_full_top_nav(permission_set, request.user),
    })


@login_required
def delivery_detail(request, delivery_id):
    """交付记录详情页"""
    from .models import DeliveryRecord
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
    
    return render(request, "delivery_customer/delivery_detail.html", {
        "page_title": "交付详情",
        "page_icon": "📋",
        "delivery": delivery,
        "can_edit": can_edit,
        "full_top_nav": _build_full_top_nav(permission_set, request.user),
    })


@login_required
def delivery_statistics(request):
    """交付统计页"""
    from .models import DeliveryRecord, DeliveryFile
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
    })


@login_required
def delivery_warnings(request):
    """风险预警页"""
    from .models import DeliveryRecord
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
    queryset = queryset.select_related('project', 'client', 'created_by').order_by('-overdue_days', '-created_at')
    paginator = Paginator(queryset, 20)
    page = paginator.get_page(page_num)
    
    # 风险统计
    risk_stats = {}
    for risk_code, risk_label in [('low', '低风险'), ('medium', '中风险'), ('high', '高风险'), ('critical', '严重风险')]:
        risk_stats[risk_code] = {
            'label': risk_label,
            'count': DeliveryRecord.objects.filter(is_overdue=True, risk_level=risk_code).count()
        }
    
    return render(request, "delivery_customer/delivery_warnings.html", {
        "page_title": "风险预警",
        "page_icon": "⚠️",
        "overdue_deliveries": page,
        "risk_level_filter": risk_level,
        "risk_stats": risk_stats,
        "total_overdue": DeliveryRecord.objects.filter(is_overdue=True).count(),
        "full_top_nav": _build_full_top_nav(permission_set, request.user),
    })


@login_required
def customer_collaboration(request):
    context = _context(
        "客户协同工作台",
        "🤝",
        "与客户及设计方协同处理意见、确认事项与信息同步。",
        request=request,
        summary_cards=[
            {"label": "活跃协同", "value": "0", "hint": "当前有互动的客户协同专题"},
            {"label": "待回复事项", "value": "0", "hint": "等待客户或设计方反馈的事项"},
            {"label": "协同会议", "value": "0", "hint": "排期中的客户会议数量"},
            {"label": "满意度评分", "value": "--", "hint": "客户反馈满意度"},
        ],
        sections=[
            {
                "title": "协同功能",
                "description": "围绕客户沟通的关键环节进行管理。",
                "items": [
                    {"label": "协同专题", "description": "为项目创建协同沟通空间。", "url": "#", "icon": "🗂"},
                    {"label": "互动记录", "description": "跟踪客户沟通日志。", "url": "#", "icon": "📝"},
                    {"label": "待办提醒", "description": "及时处理客户反馈与任务。", "url": "#", "icon": "⏰"},
                ],
            }
        ],
    )
    return render(request, "shared/center_dashboard.html", context)


@login_required
def customer_portal(request):
    context = _context(
        "客户门户管理",
        "🌐",
        "配置客户门户账号、权限与界面展示，实现成果在线交付与客户自助服务。",
        request=request,
        summary_cards=[
            {"label": "门户用户", "value": "0", "hint": "已开通的客户门户账号数"},
            {"label": "活跃用户", "value": "0", "hint": "近 30 天登录的客户数"},
            {"label": "权限模板", "value": "0", "hint": "已配置的门户权限组"},
            {"label": "界面主题", "value": "0", "hint": "可选门户主题数量"},
        ],
        sections=[
            {
                "title": "门户配置",
                "description": "在线配置客户门户资源。",
                "items": [
                    {"label": "账号管理", "description": "新增或停用客户账号。", "url": "#", "icon": "👤"},
                    {"label": "权限设置", "description": "维护门户访问权限。", "url": "#", "icon": "🔐"},
                    {"label": "界面定制", "description": "调整门户视觉与栏目。", "url": "#", "icon": "🎨"},
                ],
            }
        ],
    )
    return render(request, "shared/center_dashboard.html", context)


@login_required
def electronic_signature(request):
    context = _context(
        "电子签章中心",
        "🖋",
        "统一管理成果确认函、结算确认单等电子签署流程，确保轨迹可追溯。",
        request=request,
        summary_cards=[
            {"label": "待签文件", "value": "0", "hint": "等待签署的电子文档数量"},
            {"label": "已完成签章", "value": "0", "hint": "已完成签署并归档的文件"},
            {"label": "签署耗时", "value": "--", "hint": "平均签署完成耗时"},
            {"label": "异常记录", "value": "0", "hint": "签署失败或撤回的记录"},
        ],
        sections=[
            {
                "title": "签章流程",
                "description": "发起、追踪并归档电子签章。",
                "items": [
                    {"label": "发起签署", "description": "上传文档并选择签署方。", "url": "#", "icon": "📨"},
                    {"label": "签署进度", "description": "实时查看签章状态。", "url": "#", "icon": "⏳"},
                    {"label": "签署归档", "description": "管理签署完成后的文件。", "url": "#", "icon": "🗄"},
                ],
            }
        ],
    )
    return render(request, "shared/center_dashboard.html", context)

