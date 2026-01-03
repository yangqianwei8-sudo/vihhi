"""
发文管理服务模块
提供发文相关的业务逻辑服务
"""
import logging
from django.utils import timezone
from datetime import timedelta, date
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class OutgoingDocumentExpressSyncService:
    """发文快递状态同步服务"""
    
    @staticmethod
    def sync_express_status(document, force_update: bool = False) -> Tuple[bool, str, Dict]:
        """
        同步单个发文的快递状态
        
        Args:
            document: OutgoingDocument实例
            force_update: 是否强制更新（即使最近已更新过）
            
        Returns:
            (success, message, status_data)
        """
        from backend.apps.delivery_customer.models import OutgoingDocument
        from backend.apps.delivery_customer.express_service import query_express_tracking
        
        # 检查是否有快递信息
        if not document.express_number or not document.express_company:
            return False, "缺少快递信息（快递公司或快递单号）", {}
        
        # 如果不是强制更新，检查是否需要更新（避免频繁查询）
        if not force_update and document.express_last_update:
            # 如果1小时内已更新过，跳过
            if timezone.now() - document.express_last_update < timedelta(hours=1):
                return False, "最近已更新过，跳过", {}
        
        try:
            # 查询快递状态
            success, logistics_data, message = query_express_tracking(
                company_name=document.express_company,
                tracking_number=document.express_number
            )
            
            if not success:
                logger.warning(f"发文 {document.document_number} 快递查询失败: {message}")
                return False, message, {}
            
            # 更新快递状态
            old_status = document.express_status
            document.express_status = logistics_data.get('status_text', '')
            document.express_last_update = timezone.now()
            document.save(update_fields=['express_status', 'express_last_update'])
            
            # 如果快递已签收，且发文还未确认签收，自动更新状态
            status_code = logistics_data.get('status', '')
            if status_code == '3':  # 已签收
                if not document.is_receipt_confirmed:
                    # 记录到状态日志
                    from django.apps import apps
                    try:
                        StatusLog = apps.get_model('delivery_customer', 'OutgoingDocumentStatusLog')
                        StatusLog.objects.create(
                            document=document,
                            from_status=document.status,
                            to_status=document.status,
                            actor=None,  # 自动同步，无操作人
                            comment=f'快递状态自动同步：已签收（快递单号：{document.express_number}）',
                        )
                    except Exception as e:
                        logger.error(f"记录状态日志失败: {str(e)}")
            
            logger.info(f"发文 {document.document_number} 快递状态已同步：{old_status} -> {document.express_status}")
            
            return True, "同步成功", logistics_data
            
        except Exception as e:
            logger.error(f"同步发文 {document.document_number} 快递状态失败: {str(e)}", exc_info=True)
            return False, f"同步失败：{str(e)}", {}
    
    @staticmethod
    def sync_all_pending_documents(limit: Optional[int] = None, force_update: bool = False) -> Dict:
        """
        同步所有待同步的发文快递状态
        
        Args:
            limit: 限制同步数量，None表示不限制
            force_update: 是否强制更新
            
        Returns:
            {
                'total': int,  # 总数量
                'success': int,  # 成功数量
                'failed': int,  # 失败数量
                'skipped': int,  # 跳过数量
                'details': List[Dict]  # 详细信息
            }
        """
        from backend.apps.delivery_customer.models import OutgoingDocument
        
        # 查询需要同步的发文（已发送且有快递单号）
        queryset = OutgoingDocument.objects.filter(
            status__in=['sent', 'completed'],
            express_number__isnull=False,
            express_company__isnull=False,
        ).exclude(
            express_number=''
        ).exclude(
            express_company=''
        )
        
        if limit:
            queryset = queryset[:limit]
        
        total = queryset.count()
        success_count = 0
        failed_count = 0
        skipped_count = 0
        details = []
        
        for document in queryset:
            success, message, status_data = OutgoingDocumentExpressSyncService.sync_express_status(
                document, force_update=force_update
            )
            
            if success:
                success_count += 1
            elif '跳过' in message:
                skipped_count += 1
            else:
                failed_count += 1
            
            details.append({
                'document_number': document.document_number,
                'title': document.title,
                'express_company': document.express_company,
                'express_number': document.express_number,
                'success': success,
                'message': message,
                'status': document.express_status,
            })
        
        result = {
            'total': total,
            'success': success_count,
            'failed': failed_count,
            'skipped': skipped_count,
            'details': details,
        }
        
        logger.info(f"快递状态同步完成：总数={total}, 成功={success_count}, 失败={failed_count}, 跳过={skipped_count}")
        
        return result
    
    @staticmethod
    def check_delayed_documents() -> Dict:
        """
        检查延迟的发文并标记
        
        Returns:
            {
                'total_checked': int,
                'delayed_count': int,
                'delayed_documents': List[Dict]
            }
        """
        from backend.apps.delivery_customer.models import OutgoingDocument
        from django.db.models import Q
        
        # 查询已发送但超过预期时间未签收的发文
        now = timezone.now().date()
        delayed_documents = OutgoingDocument.objects.filter(
            status__in=['sent', 'completed'],
            is_receipt_confirmed=False,
            expected_confirm_date__isnull=False,
        ).filter(
            Q(expected_confirm_date__lt=now) | Q(expected_receive_date__lt=now)
        )
        
        delayed_list = []
        for document in delayed_documents:
            # 计算延迟天数
            expected_date = document.expected_confirm_date or document.expected_receive_date
            if expected_date:
                delay_days = (now - expected_date).days
                
                # 如果还未标记为延迟，则标记
                if not document.is_delayed:
                    document.is_delayed = True
                    document.delay_days = delay_days
                    document.save(update_fields=['is_delayed', 'delay_days'])
                
                delayed_list.append({
                    'document_number': document.document_number,
                    'title': document.title,
                    'send_date': document.send_date,
                    'expected_confirm_date': document.expected_confirm_date,
                    'delay_days': delay_days,
                    'express_number': document.express_number,
                })
        
        result = {
            'total_checked': delayed_documents.count(),
            'delayed_count': len(delayed_list),
            'delayed_documents': delayed_list,
        }
        
        logger.info(f"延迟检查完成：检查={result['total_checked']}, 延迟={result['delayed_count']}")
        
        return result


class OutgoingDocumentWarningService:
    """发文延迟预警服务"""
    
    @staticmethod
    def send_delay_warning(document, delay_days: int) -> Tuple[bool, str]:
        """
        发送延迟预警通知
        
        Args:
            document: OutgoingDocument实例
            delay_days: 延迟天数
            
        Returns:
            (success, message)
        """
        from backend.apps.delivery_customer.models import OutgoingDocument
        from django.contrib.auth import get_user_model
        
        User = get_user_model()
        
        # 确定通知对象
        recipients = []
        
        # 优先通知责任人
        if document.responsible_person:
            recipients.append(document.responsible_person)
        
        # 通知创建人
        if document.created_by and document.created_by not in recipients:
            recipients.append(document.created_by)
        
        # 通知发送人
        if document.sender and document.sender not in recipients:
            recipients.append(document.sender)
        
        # 如果没有通知对象，记录日志
        if not recipients:
            logger.warning(f"发文 {document.document_number} 没有可通知的责任人")
            return False, "没有可通知的责任人"
        
        # 构建通知内容
        subject = f"【发文延迟预警】{document.document_number} - {document.title}"
        
        urgency = "紧急" if delay_days >= 7 else ("重要" if delay_days >= 3 else "提醒")
        urgency_color = "#dc3545" if delay_days >= 7 else ("#ffc107" if delay_days >= 3 else "#17a2b8")
        
        body = f"""
发文延迟预警通知

发文编号：{document.document_number}
文件标题：{document.title}
收文单位：{document.recipient}
发送日期：{document.send_date}
预期签收日期：{document.expected_confirm_date or document.expected_receive_date or '未设置'}
延迟天数：{delay_days} 天
严重程度：{urgency}

请及时跟进并采取补救措施。

详情请登录系统查看：系统发文管理模块
        """.strip()
        
        html_body = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #333;">发文延迟预警通知</h2>
            <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
                <p><strong>发文编号：</strong>{document.document_number}</p>
                <p><strong>文件标题：</strong>{document.title}</p>
                <p><strong>收文单位：</strong>{document.recipient}</p>
                <p><strong>发送日期：</strong>{document.send_date}</p>
                <p><strong>预期签收日期：</strong>{document.expected_confirm_date or document.expected_receive_date or '未设置'}</p>
                <p><strong>延迟天数：</strong><span style="color: {urgency_color}; font-weight: bold;">{delay_days} 天</span></p>
                <p><strong>严重程度：</strong><span style="background-color: {urgency_color}; color: white; padding: 3px 8px; border-radius: 3px;">{urgency}</span></p>
            </div>
            <p style="color: #666;">请及时跟进并采取补救措施。</p>
            <p><a href="#" style="background-color: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block;">查看详情</a></p>
        </div>
        """
        
        # 发送通知
        success_count = 0
        for recipient in recipients:
            try:
                # 尝试发送邮件通知
                try:
                    from backend.core.utils.notifications import (
                        NotificationMessage,
                        send_email_notification
                    )
                    
                    if recipient.email:
                        message = NotificationMessage(
                            subject=subject,
                            body=body,
                            html_body=html_body,
                            to_emails=[recipient.email]
                        )
                        send_email_notification(message)
                        logger.info(f"已发送延迟预警邮件给 {recipient.username} ({recipient.email})")
                except ImportError:
                    # 如果没有通知工具，使用Django默认邮件
                    try:
                        from django.core.mail import send_mail
                        from django.conf import settings
                        send_mail(
                            subject=subject,
                            message=body,
                            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@example.com'),
                            recipient_list=[recipient.email],
                            html_message=html_body,
                            fail_silently=False,
                        )
                        logger.info(f"已发送延迟预警邮件给 {recipient.username} ({recipient.email})")
                    except Exception as e:
                        logger.error(f"发送邮件失败: {str(e)}")
                except Exception as e:
                    logger.error(f"发送邮件通知失败: {str(e)}")
                
                success_count += 1
            except Exception as e:
                logger.error(f"发送预警通知给 {recipient.username} 失败: {str(e)}")
        
        # 更新预警发送记录
        document.warning_sent = True
        document.warning_sent_at = timezone.now()
        document.save(update_fields=['warning_sent', 'warning_sent_at'])
        
        # 记录状态日志
        from django.apps import apps
        try:
            StatusLog = apps.get_model('delivery_customer', 'OutgoingDocumentStatusLog')
            StatusLog.objects.create(
                document=document,
                from_status=document.status,
                to_status=document.status,
                actor=None,  # 自动预警，无操作人
                comment=f'延迟预警已发送：延迟{delay_days}天（通知{success_count}人）',
            )
        except Exception as e:
            logger.error(f"记录状态日志失败: {str(e)}")
        
        return True, f"预警已发送给 {success_count} 个责任人"
    
    @staticmethod
    def check_and_send_warnings(min_delay_days: int = 1, max_delay_days: Optional[int] = None) -> Dict:
        """
        检查延迟的发文并发送预警
        
        Args:
            min_delay_days: 最小延迟天数（小于此天数不发送预警）
            max_delay_days: 最大延迟天数（用于筛选，None表示不限制）
            
        Returns:
            {
                'total_checked': int,
                'warnings_sent': int,
                'already_warned': int,
                'details': List[Dict]
            }
        """
        from backend.apps.delivery_customer.models import OutgoingDocument
        from django.db.models import Q
        
        # 查询延迟且未发送预警的发文
        now = timezone.now().date()
        delayed_documents = OutgoingDocument.objects.filter(
            status__in=['sent', 'completed'],
            is_receipt_confirmed=False,
            is_delayed=True,  # 已标记为延迟
            warning_sent=False,  # 未发送预警
            expected_confirm_date__isnull=False,
        )
        
        # 计算延迟天数并筛选
        warnings_sent_count = 0
        already_warned_count = 0
        details = []
        
        for document in delayed_documents:
            expected_date = document.expected_confirm_date or document.expected_receive_date
            if not expected_date:
                continue
            
            delay_days = (now - expected_date).days
            
            # 检查延迟天数是否满足条件
            if delay_days < min_delay_days:
                continue
            
            if max_delay_days and delay_days > max_delay_days:
                continue
            
            # 发送预警
            success, message = OutgoingDocumentWarningService.send_delay_warning(
                document, delay_days
            )
            
            if success:
                warnings_sent_count += 1
            else:
                already_warned_count += 1
            
            details.append({
                'document_number': document.document_number,
                'title': document.title,
                'delay_days': delay_days,
                'success': success,
                'message': message,
            })
        
        result = {
            'total_checked': delayed_documents.count(),
            'warnings_sent': warnings_sent_count,
            'already_warned': already_warned_count,
            'details': details,
        }
        
        logger.info(
            f"延迟预警检查完成：检查={result['total_checked']}, "
            f"已发送={warnings_sent_count}, 已预警={already_warned_count}"
        )
        
        return result
    
    @staticmethod
    def record_remedy_action(document, remedy_action: str, actor) -> bool:
        """
        记录补救措施
        
        Args:
            document: OutgoingDocument实例
            remedy_action: 补救措施描述
            actor: 执行人（User实例）
            
        Returns:
            bool: 是否成功
        """
        try:
            document.remedy_action = remedy_action
            document.remedy_action_by = actor
            document.remedy_action_at = timezone.now()
            document.save(update_fields=['remedy_action', 'remedy_action_by', 'remedy_action_at'])
            
            # 记录状态日志
            from django.apps import apps
            try:
                StatusLog = apps.get_model('delivery_customer', 'OutgoingDocumentStatusLog')
                StatusLog.objects.create(
                    document=document,
                    from_status=document.status,
                    to_status=document.status,
                    actor=actor,
                    comment=f'补救措施：{remedy_action}',
                )
            except Exception as e:
                logger.error(f"记录状态日志失败: {str(e)}")
            
            logger.info(f"已记录发文 {document.document_number} 的补救措施")
            return True
            
        except Exception as e:
            logger.error(f"记录补救措施失败: {str(e)}", exc_info=True)
            return False


class OutgoingDocumentReportService:
    """发文效能报告服务"""
    
    @staticmethod
    def generate_performance_report(start_date=None, end_date=None, responsible_person_id=None) -> Dict:
        """
        生成发文效能报告
        
        Args:
            start_date: 开始日期（可选）
            end_date: 结束日期（可选）
            responsible_person_id: 责任人ID（可选，用于筛选特定责任人的报告）
            
        Returns:
            {
                'period': {'start': date, 'end': date},
                'summary': {
                    'total_documents': int,  # 总发文数
                    'by_status': Dict,  # 按状态统计
                    'by_priority': Dict,  # 按优先级统计
                },
                'efficiency': {
                    'avg_response_time': float,  # 平均响应时效（小时）
                    'avg_review_time': float,  # 平均审核时间（小时）
                    'avg_send_time': float,  # 平均发送时间（小时）
                    'avg_receipt_time': float,  # 平均签收时间（小时）
                    'completion_rate': float,  # 完成率（%）
                },
                'receipt_stats': {
                    'receipt_rate': float,  # 签收率（%）
                    'avg_receipt_days': float,  # 平均签收天数
                    'delayed_count': int,  # 延迟数量
                    'delayed_rate': float,  # 延迟率（%）
                },
                'rejection_stats': {
                    'rejection_count': int,  # 退回/拒绝数量
                    'rejection_rate': float,  # 退回率（%）
                },
                'top_responsible_persons': List[Dict],  # 责任人排名
                'trend_data': Dict,  # 趋势数据
            }
        """
        from backend.apps.delivery_customer.models import OutgoingDocument
        from django.db.models import Count, Avg, Q, F, DurationField, Case, When, IntegerField
        from django.utils import timezone
        from datetime import timedelta
        from django.db.models.functions import Extract
        
        # 设置默认日期范围（最近30天）
        if not end_date:
            end_date = timezone.now().date()
        if not start_date:
            start_date = end_date - timedelta(days=30)
        
        # 基础查询
        queryset = OutgoingDocument.objects.filter(
            created_at__date__gte=start_date,
            created_at__date__lte=end_date
        )
        
        if responsible_person_id:
            queryset = queryset.filter(responsible_person_id=responsible_person_id)
        
        # 总发文数
        total_documents = queryset.count()
        
        # 按状态统计
        by_status = dict(queryset.values('status').annotate(
            count=Count('id')
        ).values_list('status', 'count'))
        
        # 按优先级统计
        by_priority = dict(queryset.values('priority').annotate(
            count=Count('id')
        ).values_list('priority', 'count'))
        
        # 效率指标 - 响应时效（从创建到发送的平均时间）
        sent_documents = queryset.filter(sent_at__isnull=False)
        response_times = []
        for doc in sent_documents:
            if doc.created_at and doc.sent_at:
                delta = doc.sent_at - doc.created_at
                response_times.append(delta.total_seconds() / 3600)  # 转换为小时
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        # 平均审核时间
        reviewed_documents = queryset.filter(reviewed_at__isnull=False)
        review_times = []
        for doc in reviewed_documents:
            # 假设提交审核到审核完成的时间
            # 这里简化处理，使用created_at到reviewed_at的时间
            if doc.created_at and doc.reviewed_at:
                delta = doc.reviewed_at - doc.created_at
                review_times.append(delta.total_seconds() / 3600)
        avg_review_time = sum(review_times) / len(review_times) if review_times else 0
        
        # 平均签收时间（从发送到签收）
        receipt_times = []
        receipt_confirmed = queryset.filter(
            is_receipt_confirmed=True,
            sent_at__isnull=False,
            confirmed_at__isnull=False
        )
        for doc in receipt_confirmed:
            if doc.sent_at and doc.confirmed_at:
                delta = doc.confirmed_at - doc.sent_at
                receipt_times.append(delta.total_seconds() / 3600 / 24)  # 转换为天
        avg_receipt_time = sum(receipt_times) / len(receipt_times) if receipt_times else 0
        
        # 完成率（已归档的发文占比）
        completed_count = queryset.filter(status='archived').count()
        completion_rate = (completed_count / total_documents * 100) if total_documents > 0 else 0
        
        # 签收统计
        receipt_confirmed_count = queryset.filter(is_receipt_confirmed=True).count()
        receipt_rate = (receipt_confirmed_count / total_documents * 100) if total_documents > 0 else 0
        
        # 延迟统计
        delayed_count = queryset.filter(is_delayed=True).count()
        delayed_rate = (delayed_count / total_documents * 100) if total_documents > 0 else 0
        
        # 退回/拒绝统计（审核被退回的次数）
        rejection_count = queryset.filter(status='draft', reviewed_at__isnull=False).count()
        rejection_rate = (rejection_count / total_documents * 100) if total_documents > 0 else 0
        
        # 责任人排名（按发文数量和签收率）
        responsible_person_stats = queryset.filter(
            responsible_person__isnull=False
        ).values(
            'responsible_person_id',
            'responsible_person__username',
            'responsible_person__first_name',
            'responsible_person__last_name'
        ).annotate(
            total_count=Count('id'),
            receipt_count=Count('id', filter=Q(is_receipt_confirmed=True)),
        ).order_by('-total_count')[:10]
        
        top_responsible_persons = []
        for stat in responsible_person_stats:
            receipt_rate_person = (stat['receipt_count'] / stat['total_count'] * 100) if stat['total_count'] > 0 else 0
            top_responsible_persons.append({
                'person_id': stat['responsible_person_id'],
                'person_name': f"{stat['responsible_person__last_name'] or ''}{stat['responsible_person__first_name'] or ''}" or stat['responsible_person__username'],
                'total_count': stat['total_count'],
                'receipt_count': stat['receipt_count'],
                'receipt_rate': receipt_rate_person,
            })
        
        # 趋势数据（按日期统计）
        trend_data = {}
        current_date = start_date
        while current_date <= end_date:
            day_docs = queryset.filter(created_at__date=current_date).count()
            day_receipt = queryset.filter(
                confirmed_at__date=current_date,
                is_receipt_confirmed=True
            ).count()
            trend_data[str(current_date)] = {
                'created': day_docs,
                'receipt': day_receipt,
            }
            current_date += timedelta(days=1)
        
        result = {
            'period': {
                'start': start_date,
                'end': end_date,
            },
            'summary': {
                'total_documents': total_documents,
                'by_status': by_status,
                'by_priority': by_priority,
            },
            'efficiency': {
                'avg_response_time': round(avg_response_time, 2),
                'avg_review_time': round(avg_review_time, 2),
                'avg_send_time': round(avg_response_time, 2),  # 与响应时间相同
                'avg_receipt_time': round(avg_receipt_time, 2),
                'completion_rate': round(completion_rate, 2),
            },
            'receipt_stats': {
                'receipt_rate': round(receipt_rate, 2),
                'avg_receipt_days': round(avg_receipt_time, 2),
                'delayed_count': delayed_count,
                'delayed_rate': round(delayed_rate, 2),
            },
            'rejection_stats': {
                'rejection_count': rejection_count,
                'rejection_rate': round(rejection_rate, 2),
            },
            'top_responsible_persons': top_responsible_persons,
            'trend_data': trend_data,
        }
        
        logger.info(f"生成发文效能报告：期间={start_date}至{end_date}, 总发文数={total_documents}")
        
        return result


class OutgoingDocumentArchiveService:
    """发文自动归档服务"""
    
    @staticmethod
    def can_auto_archive(document) -> Tuple[bool, str]:
        """
        判断发文是否可以自动归档
        
        Args:
            document: OutgoingDocument实例
            
        Returns:
            (can_archive: bool, reason: str)
        """
        # 必须已签收确认
        if not document.is_receipt_confirmed:
            return False, "尚未签收确认"
        
        # 必须已完成状态
        if document.status != 'completed':
            return False, f"当前状态为{document.get_status_display()}，无法归档"
        
        # 检查是否已经归档（避免重复归档）
        if document.status == 'archived':
            return False, "已归档"
        
        return True, "可以归档"
    
    @staticmethod
    def auto_archive_document(document, actor=None, comment: str = None) -> Tuple[bool, str]:
        """
        自动归档单个发文
        
        Args:
            document: OutgoingDocument实例
            actor: 操作人（可选，None表示系统自动归档）
            comment: 归档备注（可选）
            
        Returns:
            (success: bool, message: str)
        """
        can_archive, reason = OutgoingDocumentArchiveService.can_auto_archive(document)
        if not can_archive:
            return False, reason
        
        try:
            # 执行状态流转到归档
            document.transition_to('archived', actor=actor, comment=comment or '自动归档：已签收确认且已完成')
            
            # 设置归档时间（如果模型有archived_at字段）
            if hasattr(document, 'archived_at'):
                from django.utils import timezone
                document.archived_at = timezone.now()
                document.save(update_fields=['archived_at'])
            
            logger.info(f"发文 {document.document_number} 已自动归档")
            return True, "归档成功"
            
        except ValueError as e:
            return False, f"状态流转失败：{str(e)}"
        except Exception as e:
            logger.error(f"自动归档发文 {document.document_number} 失败: {str(e)}", exc_info=True)
            return False, f"归档失败：{str(e)}"
    
    @staticmethod
    def auto_archive_eligible_documents(days_after_completion: int = 7, limit: Optional[int] = None) -> Dict:
        """
        自动归档符合条件的发文
        
        归档条件：
        - 状态为已完成(completed)
        - 已签收确认(is_receipt_confirmed=True)
        - 完成时间超过指定天数（默认7天）
        
        Args:
            days_after_completion: 完成后多少天自动归档（默认7天）
            limit: 限制归档数量（可选，用于测试）
            
        Returns:
            {
                'total_checked': int,  # 检查总数
                'archived_count': int,  # 归档数量
                'failed_count': int,  # 失败数量
                'details': List[Dict]  # 详细信息
            }
        """
        from backend.apps.delivery_customer.models import OutgoingDocument
        from django.utils import timezone
        from datetime import timedelta
        
        # 计算归档日期阈值
        archive_threshold = timezone.now() - timedelta(days=days_after_completion)
        
        # 查询符合条件的发文
        queryset = OutgoingDocument.objects.filter(
            status='completed',
            is_receipt_confirmed=True,
            confirmed_at__lte=archive_threshold,  # 签收确认时间超过阈值
        ).exclude(
            status='archived'  # 排除已归档的
        )
        
        if limit:
            queryset = queryset[:limit]
        
        total_checked = queryset.count()
        archived_count = 0
        failed_count = 0
        details = []
        
        for document in queryset:
            success, message = OutgoingDocumentArchiveService.auto_archive_document(
                document, 
                actor=None,  # 系统自动归档
                comment=f'自动归档：签收确认后已超过{days_after_completion}天'
            )
            
            if success:
                archived_count += 1
            else:
                failed_count += 1
            
            details.append({
                'document_number': document.document_number,
                'title': document.title,
                'confirmed_at': document.confirmed_at,
                'success': success,
                'message': message,
            })
        
        result = {
            'total_checked': total_checked,
            'archived_count': archived_count,
            'failed_count': failed_count,
            'details': details,
        }
        
        logger.info(
            f"自动归档任务完成：检查={total_checked}, "
            f"归档={archived_count}, 失败={failed_count}"
        )
        
        return result
    
    @staticmethod
    def get_archive_statistics() -> Dict:
        """
        获取归档统计信息
        
        Returns:
            {
                'total_archived': int,  # 总归档数
                'pending_archive': int,  # 待归档数（已完成且已签收）
                'archive_rate': float,  # 归档率（%）
                'recent_archived': List[Dict],  # 最近归档的发文
            }
        """
        from backend.apps.delivery_customer.models import OutgoingDocument
        from django.utils import timezone
        from datetime import timedelta
        
        # 总归档数
        total_archived = OutgoingDocument.objects.filter(status='archived').count()
        
        # 待归档数（已完成且已签收）
        pending_archive = OutgoingDocument.objects.filter(
            status='completed',
            is_receipt_confirmed=True
        ).exclude(
            status='archived'
        ).count()
        
        # 总完成数（用于计算归档率）
        total_completed = OutgoingDocument.objects.filter(
            is_receipt_confirmed=True
        ).count()
        
        archive_rate = (total_archived / total_completed * 100) if total_completed > 0 else 0
        
        # 最近归档的发文（最近30天）
        recent_threshold = timezone.now() - timedelta(days=30)
        recent_archived = OutgoingDocument.objects.filter(
            status='archived',
            updated_at__gte=recent_threshold
        ).order_by('-updated_at')[:10]
        
        recent_archived_list = []
        for doc in recent_archived:
            recent_archived_list.append({
                'document_number': doc.document_number,
                'title': doc.title,
                'archived_at': doc.updated_at,  # 使用updated_at作为归档时间
                'confirmed_at': doc.confirmed_at,
            })
        
        return {
            'total_archived': total_archived,
            'pending_archive': pending_archive,
            'archive_rate': round(archive_rate, 2),
            'recent_archived': recent_archived_list,
        }


class OutgoingDocumentAuditService:
    """发文审计追踪服务"""
    
    @staticmethod
    def get_document_audit_trail(document) -> List[Dict]:
        """
        获取发文的完整审计追踪记录
        
        Args:
            document: OutgoingDocument实例
            
        Returns:
            List[Dict]: 审计追踪记录列表，按时间倒序
            [
                {
                    'type': str,  # 记录类型：status_change, field_change, receipt, warning, remedy, archive
                    'timestamp': datetime,
                    'actor': User or None,
                    'action': str,  # 操作描述
                    'details': Dict,  # 详细信息
                    'comment': str,  # 备注
                }
            ]
        """
        from backend.apps.delivery_customer.models import OutgoingDocumentStatusLog
        from django.contrib.auth import get_user_model
        
        User = get_user_model()
        audit_trail = []
        
        # 1. 状态流转日志
        status_logs = document.status_logs.all().order_by('created_at')
        for log in status_logs:
            audit_trail.append({
                'type': 'status_change',
                'timestamp': log.created_at,
                'actor': log.actor,
                'action': f'状态变更：{log.get_from_status_display()} → {log.get_to_status_display()}',
                'details': {
                    'from_status': log.from_status,
                    'to_status': log.to_status,
                    'from_status_display': log.get_from_status_display(),
                    'to_status_display': log.get_to_status_display(),
                },
                'comment': log.comment,
            })
        
        # 2. 创建记录
        if document.created_at and document.created_by:
            audit_trail.append({
                'type': 'create',
                'timestamp': document.created_at,
                'actor': document.created_by,
                'action': '创建发文',
                'details': {
                    'document_number': document.document_number,
                    'title': document.title,
                },
                'comment': f'创建发文：{document.document_number}',
            })
        
        # 3. 签收确认记录
        if document.is_receipt_confirmed and document.confirmed_at:
            audit_trail.append({
                'type': 'receipt',
                'timestamp': document.confirmed_at,
                'actor': document.receipt_confirmed_by,
                'action': '签收确认',
                'details': {
                    'receipt_method': document.receipt_method,
                    'receipt_by': document.receipt_by,
                    'receipt_phone': document.receipt_phone,
                    'receipt_email': document.receipt_email,
                },
                'comment': document.receipt_comment or '签收确认',
            })
        
        # 4. 预警记录
        if document.warning_sent and document.warning_sent_at:
            audit_trail.append({
                'type': 'warning',
                'timestamp': document.warning_sent_at,
                'actor': None,  # 系统自动发送
                'action': '延迟预警',
                'details': {
                    'delay_days': document.delay_days,
                    'is_delayed': document.is_delayed,
                },
                'comment': f'延迟预警：延迟{document.delay_days}天',
            })
        
        # 5. 补救措施记录
        if document.remedy_action and document.remedy_action_at:
            audit_trail.append({
                'type': 'remedy',
                'timestamp': document.remedy_action_at,
                'actor': document.remedy_action_by,
                'action': '记录补救措施',
                'details': {
                    'remedy_action': document.remedy_action,
                },
                'comment': document.remedy_action,
            })
        
        # 6. 归档记录（如果已归档）
        if document.status == 'archived':
            # 从状态日志中查找归档记录
            archive_log = document.status_logs.filter(to_status='archived').first()
            if archive_log:
                audit_trail.append({
                    'type': 'archive',
                    'timestamp': archive_log.created_at,
                    'actor': archive_log.actor,
                    'action': '归档',
                    'details': {},
                    'comment': archive_log.comment or '归档',
                })
        
        # 按时间排序（从早到晚）
        audit_trail.sort(key=lambda x: x['timestamp'])
        
        return audit_trail
    
    @staticmethod
    def query_audit_logs(
        document_number: Optional[str] = None,
        actor_id: Optional[int] = None,
        action_type: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        limit: Optional[int] = None
    ) -> List[Dict]:
        """
        多维度查询审计日志
        
        Args:
            document_number: 发文编号（可选）
            actor_id: 操作人ID（可选）
            action_type: 操作类型（可选：status_change, receipt, warning, remedy, archive, create）
            start_date: 开始日期（可选）
            end_date: 结束日期（可选）
            limit: 限制返回数量（可选）
            
        Returns:
            List[Dict]: 审计日志列表
        """
        from backend.apps.delivery_customer.models import OutgoingDocument, OutgoingDocumentStatusLog
        from django.db.models import Q
        from django.contrib.auth import get_user_model
        
        User = get_user_model()
        
        # 查询所有相关的发文
        documents_query = OutgoingDocument.objects.all()
        
        if document_number:
            documents_query = documents_query.filter(document_number__icontains=document_number)
        
        # 查询状态日志
        status_logs = OutgoingDocumentStatusLog.objects.filter(
            document__in=documents_query
        ).select_related('document', 'actor').order_by('-created_at')
        
        # 过滤操作人
        if actor_id:
            status_logs = status_logs.filter(actor_id=actor_id)
        
        # 过滤日期范围
        if start_date:
            status_logs = status_logs.filter(created_at__date__gte=start_date)
        if end_date:
            status_logs = status_logs.filter(created_at__date__lte=end_date)
        
        # 转换为审计日志格式
        audit_logs = []
        for log in status_logs:
            audit_logs.append({
                'document_number': log.document.document_number,
                'document_title': log.document.title,
                'type': 'status_change',
                'timestamp': log.created_at,
                'actor': log.actor.username if log.actor else '系统',
                'actor_id': log.actor_id,
                'action': f'状态变更：{log.get_from_status_display()} → {log.get_to_status_display()}',
                'details': {
                    'from_status': log.from_status,
                    'to_status': log.to_status,
                },
                'comment': log.comment,
            })
        
        # 如果指定了action_type，进行过滤
        if action_type:
            # 这里可以根据action_type进行更细粒度的过滤
            # 当前主要基于状态日志，可以扩展查询其他类型的记录
            pass
        
        # 限制返回数量
        if limit:
            audit_logs = audit_logs[:limit]
        
        return audit_logs
    
    @staticmethod
    def get_user_action_statistics(user_id: int, start_date: Optional[date] = None, end_date: Optional[date] = None) -> Dict:
        """
        获取用户操作统计
        
        Args:
            user_id: 用户ID
            start_date: 开始日期（可选）
            end_date: 结束日期（可选）
            
        Returns:
            {
                'total_actions': int,
                'by_action_type': Dict,
                'by_status_change': Dict,
                'recent_actions': List[Dict],
            }
        """
        from backend.apps.delivery_customer.models import OutgoingDocumentStatusLog
        from django.db.models import Count, Q
        
        queryset = OutgoingDocumentStatusLog.objects.filter(actor_id=user_id)
        
        if start_date:
            queryset = queryset.filter(created_at__date__gte=start_date)
        if end_date:
            queryset = queryset.filter(created_at__date__lte=end_date)
        
        # 总操作数
        total_actions = queryset.count()
        
        # 按状态变更类型统计
        by_status_change = dict(
            queryset.values('to_status').annotate(
                count=Count('id')
            ).values_list('to_status', 'count')
        )
        
        # 最近的操作
        recent_actions = queryset.order_by('-created_at')[:10]
        recent_actions_list = []
        for action in recent_actions:
            recent_actions_list.append({
                'document_number': action.document.document_number,
                'action': f'{action.get_from_status_display()} → {action.get_to_status_display()}',
                'timestamp': action.created_at,
                'comment': action.comment,
            })
        
        return {
            'total_actions': total_actions,
            'by_status_change': by_status_change,
            'recent_actions': recent_actions_list,
        }
    
    @staticmethod
    def get_document_timeline(document) -> Dict:
        """
        获取发文的完整时间线
        
        Args:
            document: OutgoingDocument实例
            
        Returns:
            {
                'timeline': List[Dict],  # 时间线事件
                'duration_stats': Dict,  # 时长统计
            }
        """
        audit_trail = OutgoingDocumentAuditService.get_document_audit_trail(document)
        
        # 计算各阶段时长
        duration_stats = {}
        
        # 创建到发送的时长
        if document.created_at and document.sent_at:
            duration = document.sent_at - document.created_at
            duration_stats['creation_to_send'] = {
                'days': duration.days,
                'hours': duration.total_seconds() / 3600,
            }
        
        # 发送到签收的时长
        if document.sent_at and document.confirmed_at:
            duration = document.confirmed_at - document.sent_at
            duration_stats['send_to_receipt'] = {
                'days': duration.days,
                'hours': duration.total_seconds() / 3600,
            }
        
        # 创建到签收的总时长
        if document.created_at and document.confirmed_at:
            duration = document.confirmed_at - document.created_at
            duration_stats['creation_to_receipt'] = {
                'days': duration.days,
                'hours': duration.total_seconds() / 3600,
            }
        
        return {
            'timeline': audit_trail,
            'duration_stats': duration_stats,
        }


class OutgoingDocumentPerformanceService:
    """发文责任人绩效服务"""
    
    @staticmethod
    def calculate_performance_score(document) -> Dict:
        """
        计算单个发文的绩效得分
        
        Args:
            document: OutgoingDocument实例
            
        Returns:
            {
                'total_score': float,  # 总分（0-100）
                'scores': Dict,  # 各项得分
                'details': Dict,  # 详细说明
            }
        """
        scores = {}
        details = {}
        total_score = 0.0
        
        # 1. 响应时效得分（30分）
        # 从创建到发送的时间，越快得分越高
        if document.created_at and document.sent_at:
            response_hours = (document.sent_at - document.created_at).total_seconds() / 3600
            # 理想时间：24小时内（30分），48小时内（20分），72小时内（10分），超过72小时（0分）
            if response_hours <= 24:
                response_score = 30
            elif response_hours <= 48:
                response_score = 20
            elif response_hours <= 72:
                response_score = 10
            else:
                response_score = 0
            scores['response_time'] = response_score
            details['response_time'] = f'响应时间：{response_hours:.1f}小时，得分：{response_score}分'
        else:
            scores['response_time'] = 0
            details['response_time'] = '未发送，无响应时间'
        
        # 2. 签收及时性得分（30分）
        # 从发送到签收的时间，越快得分越高
        if document.sent_at and document.confirmed_at:
            receipt_hours = (document.confirmed_at - document.sent_at).total_seconds() / 3600
            receipt_days = receipt_hours / 24
            # 理想时间：3天内（30分），5天内（20分），7天内（10分），超过7天（0分）
            if receipt_days <= 3:
                receipt_score = 30
            elif receipt_days <= 5:
                receipt_score = 20
            elif receipt_days <= 7:
                receipt_score = 10
            else:
                receipt_score = 0
            scores['receipt_time'] = receipt_score
            details['receipt_time'] = f'签收时间：{receipt_days:.1f}天，得分：{receipt_score}分'
        elif document.is_receipt_confirmed:
            # 已签收但无时间记录，给基础分
            scores['receipt_time'] = 15
            details['receipt_time'] = '已签收，但无时间记录'
        else:
            scores['receipt_time'] = 0
            details['receipt_time'] = '未签收'
        
        # 3. 签收率得分（20分）
        # 是否成功签收
        if document.is_receipt_confirmed:
            scores['receipt_rate'] = 20
            details['receipt_rate'] = '已签收确认，得分：20分'
        else:
            scores['receipt_rate'] = 0
            details['receipt_rate'] = '未签收确认'
        
        # 4. 延迟情况得分（20分）
        # 是否延迟，延迟扣分
        if document.is_delayed:
            # 延迟天数越多，扣分越多
            delay_days = document.delay_days or 0
            if delay_days <= 3:
                delay_score = 10  # 轻微延迟
            elif delay_days <= 7:
                delay_score = 5   # 中度延迟
            else:
                delay_score = 0   # 严重延迟
            scores['delay'] = delay_score
            details['delay'] = f'延迟{delay_days}天，得分：{delay_score}分'
        else:
            scores['delay'] = 20
            details['delay'] = '未延迟，得分：20分'
        
        # 计算总分
        total_score = sum(scores.values())
        
        return {
            'total_score': round(total_score, 2),
            'scores': scores,
            'details': details,
        }
    
    @staticmethod
    def get_responsible_person_performance(
        user_id: int,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict:
        """
        获取责任人的绩效统计
        
        Args:
            user_id: 责任人用户ID
            start_date: 开始日期（可选）
            end_date: 结束日期（可选）
            
        Returns:
            {
                'user_id': int,
                'user_name': str,
                'period': {'start': date, 'end': date},
                'summary': {
                    'total_documents': int,  # 总发文数
                    'sent_documents': int,  # 已发送数
                    'receipt_confirmed': int,  # 已签收数
                    'delayed_count': int,  # 延迟数
                },
                'performance': {
                    'avg_score': float,  # 平均得分
                    'total_score': float,  # 总得分
                    'score_distribution': Dict,  # 得分分布
                },
                'efficiency': {
                    'avg_response_time': float,  # 平均响应时间（小时）
                    'avg_receipt_time': float,  # 平均签收时间（天）
                    'receipt_rate': float,  # 签收率（%）
                    'delay_rate': float,  # 延迟率（%）
                },
                'documents': List[Dict],  # 发文列表（带绩效得分）
            }
        """
        from backend.apps.delivery_customer.models import OutgoingDocument
        from django.contrib.auth import get_user_model
        
        User = get_user_model()
        
        # 设置默认日期范围（最近30天）
        if not end_date:
            end_date = timezone.now().date()
        if not start_date:
            start_date = end_date - timedelta(days=30)
        
        # 查询该责任人的发文
        queryset = OutgoingDocument.objects.filter(
            responsible_person_id=user_id,
            created_at__date__gte=start_date,
            created_at__date__lte=end_date
        )
        
        # 获取用户信息
        try:
            user = User.objects.get(id=user_id)
            user_name = f"{user.last_name or ''}{user.first_name or ''}".strip() or user.username
        except User.DoesNotExist:
            user_name = f"用户ID:{user_id}"
        
        # 基础统计
        total_documents = queryset.count()
        sent_documents = queryset.filter(status__in=['sent', 'completed', 'archived']).count()
        receipt_confirmed = queryset.filter(is_receipt_confirmed=True).count()
        delayed_count = queryset.filter(is_delayed=True).count()
        
        # 计算每个发文的绩效得分
        documents_list = []
        total_score = 0.0
        score_distribution = {'excellent': 0, 'good': 0, 'average': 0, 'poor': 0}  # 优秀(80+), 良好(60+), 一般(40+), 较差(<40)
        response_times = []
        receipt_times = []
        
        for doc in queryset:
            performance = OutgoingDocumentPerformanceService.calculate_performance_score(doc)
            score = performance['total_score']
            total_score += score
            
            # 得分分布统计
            if score >= 80:
                score_distribution['excellent'] += 1
            elif score >= 60:
                score_distribution['good'] += 1
            elif score >= 40:
                score_distribution['average'] += 1
            else:
                score_distribution['poor'] += 1
            
            # 收集响应时间和签收时间
            if doc.created_at and doc.sent_at:
                response_times.append((doc.sent_at - doc.created_at).total_seconds() / 3600)
            if doc.sent_at and doc.confirmed_at:
                receipt_times.append((doc.confirmed_at - doc.sent_at).total_seconds() / 3600 / 24)
            
            documents_list.append({
                'document_id': doc.id,
                'document_number': doc.document_number,
                'title': doc.title,
                'status': doc.status,
                'is_receipt_confirmed': doc.is_receipt_confirmed,
                'is_delayed': doc.is_delayed,
                'score': score,
                'performance_details': performance,
            })
        
        # 计算平均得分
        avg_score = total_score / total_documents if total_documents > 0 else 0
        
        # 计算效率指标
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        avg_receipt_time = sum(receipt_times) / len(receipt_times) if receipt_times else 0
        receipt_rate = (receipt_confirmed / total_documents * 100) if total_documents > 0 else 0
        delay_rate = (delayed_count / total_documents * 100) if total_documents > 0 else 0
        
        return {
            'user_id': user_id,
            'user_name': user_name,
            'period': {
                'start': start_date,
                'end': end_date,
            },
            'summary': {
                'total_documents': total_documents,
                'sent_documents': sent_documents,
                'receipt_confirmed': receipt_confirmed,
                'delayed_count': delayed_count,
            },
            'performance': {
                'avg_score': round(avg_score, 2),
                'total_score': round(total_score, 2),
                'score_distribution': score_distribution,
            },
            'efficiency': {
                'avg_response_time': round(avg_response_time, 2),
                'avg_receipt_time': round(avg_receipt_time, 2),
                'receipt_rate': round(receipt_rate, 2),
                'delay_rate': round(delay_rate, 2),
            },
            'documents': documents_list,
        }
    
    @staticmethod
    def get_all_responsible_persons_performance(
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        limit: Optional[int] = None
    ) -> List[Dict]:
        """
        获取所有责任人的绩效排名
        
        Args:
            start_date: 开始日期（可选）
            end_date: 结束日期（可选）
            limit: 限制返回数量（可选，用于Top N排名）
            
        Returns:
            List[Dict]: 责任人绩效列表，按平均得分降序排列
        """
        from backend.apps.delivery_customer.models import OutgoingDocument
        from django.contrib.auth import get_user_model
        
        User = get_user_model()
        
        # 设置默认日期范围（最近30天）
        if not end_date:
            end_date = timezone.now().date()
        if not start_date:
            start_date = end_date - timedelta(days=30)
        
        # 查询所有有发文的责任人
        responsible_person_ids = OutgoingDocument.objects.filter(
            responsible_person__isnull=False,
            created_at__date__gte=start_date,
            created_at__date__lte=end_date
        ).values_list('responsible_person_id', flat=True).distinct()
        
        # 计算每个责任人的绩效
        performances = []
        for user_id in responsible_person_ids:
            performance = OutgoingDocumentPerformanceService.get_responsible_person_performance(
                user_id=user_id,
                start_date=start_date,
                end_date=end_date
            )
            performances.append(performance)
        
        # 按平均得分降序排序
        performances.sort(key=lambda x: x['performance']['avg_score'], reverse=True)
        
        # 限制返回数量
        if limit:
            performances = performances[:limit]
        
        return performances
