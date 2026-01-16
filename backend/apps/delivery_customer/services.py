from django.utils import timezone
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
import logging

from .models import DeliveryRecord, DeliveryTracking, DeliveryFeedback

logger = logging.getLogger(__name__)


class DeliveryEmailService:
    """交付邮件服务"""
    
    @staticmethod
    def send_delivery_email(delivery_record, user=None):
        """
        发送交付邮件
        
        Args:
            delivery_record: DeliveryRecord实例
            user: 发送人（可选，如果提供则使用此用户作为发送人）
            
        Returns:
            bool: 发送是否成功
        """
        try:
            # 准备收件人
            to_emails = [delivery_record.recipient_email]
            cc_emails = []
            bcc_emails = []
            
            if delivery_record.cc_emails:
                cc_emails = [email.strip() for email in delivery_record.cc_emails.split(',') if email.strip()]
            if delivery_record.bcc_emails:
                bcc_emails = [email.strip() for email in delivery_record.bcc_emails.split(',') if email.strip()]
            
            # 准备附件
            attachments = []
            for delivery_file in delivery_record.files.filter(is_deleted=False):
                if delivery_file.file:
                    try:
                        delivery_file.file.seek(0)
                        attachments.append((
                            delivery_file.file_name,
                            delivery_file.file.read(),
                            delivery_file.mime_type or 'application/octet-stream'
                        ))
                    except Exception as e:
                        logger.error(f'读取文件失败: {e}')
            
            # 准备邮件内容
            if delivery_record.use_template and delivery_record.template_name:
                html_content = DeliveryEmailService._render_template(
                    delivery_record.template_name,
                    {'delivery': delivery_record}
                )
            else:
                html_content = delivery_record.email_message
            
            # 创建邮件
            # 强制使用公司对公邮箱作为发件人
            company_email = getattr(settings, 'COMPANY_EMAIL', 'whkj@vihgroup.com.cn')
            email = EmailMultiAlternatives(
                subject=delivery_record.email_subject,
                body=delivery_record.email_message,  # 纯文本版本
                from_email=company_email,
                to=to_emails,
                cc=cc_emails if cc_emails else None,
                bcc=bcc_emails if bcc_emails else None,
            )
            
            # 添加HTML版本
            if html_content:
                email.attach_alternative(html_content, "text/html")
            
            # 添加附件
            for attachment in attachments:
                email.attach(*attachment)
            
            # 发送邮件
            email.send()
            
            # 更新记录状态
            delivery_record.status = 'sent'
            delivery_record.sent_at = timezone.now()
            # sent_by 优先使用传入的user，其次使用已设置的sent_by，最后使用created_by
            if user:
                delivery_record.sent_by = user
            elif not delivery_record.sent_by:
                delivery_record.sent_by = delivery_record.created_by
            delivery_record.error_message = ''
            delivery_record.save()
            
            # 记录跟踪
            operator = delivery_record.sent_by or delivery_record.created_by
            DeliveryTracking.objects.create(
                delivery_record=delivery_record,
                event_type='sent',
                event_description='邮件发送成功',
                operator=operator
            )
            
            return True
            
        except Exception as e:
            logger.error(f'邮件发送失败: {str(e)}', exc_info=True)
            
            # 更新记录状态
            delivery_record.status = 'failed'
            delivery_record.error_message = str(e)
            delivery_record.retry_count += 1
            delivery_record.save()
            
            # 记录跟踪
            DeliveryTracking.objects.create(
                delivery_record=delivery_record,
                event_type='sent',
                event_description=f'邮件发送失败：{str(e)}',
                operator=delivery_record.created_by
            )
            
            return False
    
    @staticmethod
    def _render_template(template_name, context):
        """渲染邮件模板"""
        try:
            template_path = f'delivery_customer/email_templates/{template_name}.html'
            return render_to_string(template_path, context)
        except Exception as e:
            logger.error(f'模板渲染失败: {e}')
            return context.get('delivery', {}).email_message or ''


class DeliveryTrackingService:
    """交付跟踪服务"""
    
    @staticmethod
    def update_tracking(delivery_record, event_type, description, location='', operator=None):
        """更新跟踪记录"""
        tracking = DeliveryTracking.objects.create(
            delivery_record=delivery_record,
            event_type=event_type,
            event_description=description,
            location=location,
            operator=operator
        )
        
        # 根据事件类型更新交付记录状态
        if event_type == 'delivered':
            delivery_record.status = 'delivered'
            delivery_record.delivered_at = timezone.now()
        elif event_type == 'received':
            delivery_record.status = 'received'
            delivery_record.received_at = timezone.now()
        elif event_type == 'confirmed':
            delivery_record.status = 'confirmed'
            delivery_record.confirmed_at = timezone.now()
        
        delivery_record.save()
        return tracking


class DeliveryWarningService:
    """交付风险预警服务"""
    
    @staticmethod
    def check_overdue_deliveries():
        """检查逾期交付记录"""
        now = timezone.now()
        overdue_records = DeliveryRecord.objects.filter(
            deadline__lt=now,
            status__in=['submitted', 'in_transit', 'sent', 'delivered'],
            is_overdue=False
        )
        
        for record in overdue_records:
            record.is_overdue = True
            delta = now - record.deadline
            record.overdue_days = delta.days
            
            # 计算风险等级
            if record.overdue_days <= 3:
                record.risk_level = 'low'
            elif record.overdue_days <= 7:
                record.risk_level = 'medium'
            elif record.overdue_days <= 15:
                record.risk_level = 'high'
            else:
                record.risk_level = 'critical'
            
            record.status = 'overdue'
            record.save()
            
            # 发送预警通知
            DeliveryWarningService.send_warning_notification(record)
    
    @staticmethod
    def send_warning_notification(delivery_record):
        """发送预警通知"""
        if delivery_record.warning_sent:
            return
        
        try:
            # 发送系统通知
            from backend.apps.production_management.models import ProjectTeamNotification
            from django.urls import reverse
            
            # 构建通知内容
            risk_level_display = delivery_record.get_risk_level_display()
            title = f'交付记录逾期预警：{delivery_record.delivery_number}'
            message = (
                f'交付记录《{delivery_record.title}》已逾期 {delivery_record.overdue_days} 天。\n'
                f'风险等级：{risk_level_display}\n'
                f'计划交付时间：{delivery_record.scheduled_delivery_time.strftime("%Y-%m-%d %H:%M") if delivery_record.scheduled_delivery_time else "未设置"}\n'
                f'交付期限：{delivery_record.deadline.strftime("%Y-%m-%d %H:%M") if delivery_record.deadline else "未设置"}'
            )
            
            # 构建跳转链接
            try:
                action_url = reverse('delivery_pages:delivery_detail', args=[delivery_record.id])
            except Exception:
                action_url = ''
            
            # 发送通知给创建人
            if delivery_record.created_by:
                ProjectTeamNotification.objects.create(
                    project=delivery_record.project,
                    recipient=delivery_record.created_by,
                    operator=None,  # 系统自动发送
                    title=title,
                    message=message,
                    category='quality_alert',
                    action_url=action_url,
                    context={
                        'delivery_id': delivery_record.id,
                        'delivery_number': delivery_record.delivery_number,
                        'risk_level': delivery_record.risk_level,
                        'overdue_days': delivery_record.overdue_days,
                    }
                )
            
            # 发送通知给项目负责人（如果项目存在）
            if delivery_record.project:
                from backend.apps.production_management.models import ProjectTeamMember
                project_managers = ProjectTeamMember.objects.filter(
                    project=delivery_record.project,
                    is_active=True,
                    role__name__contains='项目负责人'
                ).exclude(user=delivery_record.created_by)
                
                for manager in project_managers:
                    if manager.user:
                        ProjectTeamNotification.objects.create(
                            project=delivery_record.project,
                            recipient=manager.user,
                            operator=None,
                            title=title,
                            message=message,
                            category='quality_alert',
                            action_url=action_url,
                            context={
                                'delivery_id': delivery_record.id,
                                'delivery_number': delivery_record.delivery_number,
                                'risk_level': delivery_record.risk_level,
                                'overdue_days': delivery_record.overdue_days,
                            }
                        )
            
            # TODO: 发送邮件通知（可选，需要配置邮件服务）
            # TODO: 发送企业微信通知（可选，需要配置企业微信API）
            
        except Exception as e:
            logger.error(f'发送预警通知失败: {str(e)}', exc_info=True)
        
        delivery_record.warning_sent = True
        delivery_record.warning_times += 1
        delivery_record.save()


class DeliveryArchiveService:
    """交付自动归档服务"""
    
    @staticmethod
    def check_and_archive():
        """检查并执行自动归档"""
        records_to_archive = DeliveryRecord.objects.filter(
            auto_archive_enabled=True,
            status__in=['confirmed', 'feedback_received']
        ).exclude(status='archived')
        
        for record in records_to_archive:
            if record.check_auto_archive():
                DeliveryArchiveService.archive_record(record)
    
    @staticmethod
    def archive_record(delivery_record):
        """归档交付记录"""
        delivery_record.status = 'archived'
        delivery_record.archived_at = timezone.now()
        delivery_record.save()
        
        # 记录跟踪
        DeliveryTracking.objects.create(
            delivery_record=delivery_record,
            event_type='archived',
            event_description='自动归档',
            operator=None
        )
