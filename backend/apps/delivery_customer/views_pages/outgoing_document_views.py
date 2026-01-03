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


