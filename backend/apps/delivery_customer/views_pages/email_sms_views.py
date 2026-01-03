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


