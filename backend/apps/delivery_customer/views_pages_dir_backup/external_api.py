"""
外部API视图模块
包含邮件跟踪、短信回调等外部系统集成功能
"""
import csv
import io
import json
import logging
import re
import traceback

import pandas as pd

from django.contrib import messages
from django.db import transaction
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.views.decorators.csrf import csrf_exempt

from backend.apps.customer_management.models import Client, ClientContact
from backend.apps.delivery_customer.models import FileCategory, OutgoingDocument, OutgoingDocumentTracking
from backend.apps.delivery_customer.tracking_service import EmailTrackingService, SmsTrackingService
from backend.apps.production_management.models import Project
from backend.apps.system_management.services import get_user_permission_codes

logger = logging.getLogger(__name__)

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
    # 获取请求信息用于日志
    client_ip = request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0].strip() or \
                request.META.get('REMOTE_ADDR', 'unknown')
    user_agent = request.META.get('HTTP_USER_AGENT', 'unknown')
    
    # 验证跟踪ID格式
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
            logger.error(f'批量导入失败：{str(e)}\n{traceback.format_exc()}')
            return JsonResponse({'success': False, 'error': f'导入失败：{str(e)}'})
    
    return JsonResponse({'success': False, 'error': '仅支持 POST 请求'})


@login_required
def outgoing_document_import_template(request):
    """下载导入模板"""
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

