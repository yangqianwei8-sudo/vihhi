from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.urls import reverse, NoReverseMatch
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.utils import timezone
from django.contrib import messages
import logging

from backend.apps.system_management.services import get_user_permission_codes
from backend.core.views import HOME_NAV_STRUCTURE, _permission_granted, _build_full_top_nav, _build_unified_sidebar_nav
from .common import _context, _build_delivery_sidebar_nav

logger = logging.getLogger(__name__)


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


