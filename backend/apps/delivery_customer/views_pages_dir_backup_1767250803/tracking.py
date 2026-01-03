"""
跟踪功能视图模块
包含发文跟踪、邮件跟踪、快递跟踪、手递跟踪等功能
"""
import json
import logging
import re
from datetime import datetime
from urllib.parse import urlencode

from django.apps import apps
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import Http404, HttpResponse, HttpResponseForbidden, HttpResponseRedirect, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.utils.dateparse import parse_date, parse_datetime

from backend.apps.delivery_customer.models import (
    DeliveryMethod,
    ExpressCompany,
    OutgoingDocument,
    OutgoingDocumentTracking,
)
from backend.apps.delivery_customer.services import (
    OutgoingDocumentAuditService,
    OutgoingDocumentPerformanceService,
    OutgoingDocumentReportService,
)
from backend.apps.delivery_customer.tracking_service import (
    ExpressTrackingService,
    HandDeliveryTrackingService,
    TrackingServiceFactory,
)
from backend.apps.system_management.services import get_user_permission_codes
from backend.core.views import _permission_granted, _build_full_top_nav

from .common import _context, _build_delivery_sidebar_nav

logger = logging.getLogger(__name__)


@login_required
def outgoing_document_receipt_list(request):
    """发文跟踪列表 - 显示所有跟踪记录"""
    permission_set = get_user_permission_codes(request.user)
    
    # 权限检查
    if not _permission_granted('delivery_center.view', permission_set):
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
    permission_set = get_user_permission_codes(request.user)
    
    # 权限检查
    if not _permission_granted('delivery_center.view', permission_set):
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
    permission_set = get_user_permission_codes(request.user)
    
    # 权限检查
    if not _permission_granted('delivery_center.view', permission_set):
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
                    receipt_datetime = parse_datetime(receipt_date) or parse_date(receipt_date)
                    if receipt_datetime:
                        if isinstance(receipt_datetime, datetime):
                            document.received_at = receipt_datetime
                            document.confirmed_at = receipt_datetime
                        else:
                            dt = datetime.combine(receipt_datetime, datetime.min.time())
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
    permission_set = get_user_permission_codes(request.user)
    
    # 权限检查
    if not _permission_granted('delivery_center.view', permission_set):
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
    permission_set = get_user_permission_codes(request.user)
    
    # 权限检查
    if not _permission_granted('delivery_center.view', permission_set):
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
    User = get_user_model()
    
    permission_set = get_user_permission_codes(request.user)
    
    # 权限检查
    if not _permission_granted('delivery_center.view', permission_set):
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
    User = get_user_model()
    
    permission_set = get_user_permission_codes(request.user)
    
    # 权限检查
    if not _permission_granted('delivery_center.view', permission_set):
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
    User = get_user_model()
    
    permission_set = get_user_permission_codes(request.user)
    
    # 权限检查
    if not _permission_granted('delivery_center.view', permission_set):
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


