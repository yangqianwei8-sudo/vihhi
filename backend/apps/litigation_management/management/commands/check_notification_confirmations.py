"""
检查未确认的通知并自动升级
"""
import logging
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model

from backend.apps.litigation_management.models import LitigationNotificationConfirmation
from backend.apps.litigation_management.services import LitigationNotificationService
from backend.core.utils.notifications import NotificationMessage, send_email_notification, send_wecom_notification

User = get_user_model()
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = '检查未确认的通知并自动升级通知'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='仅显示将要执行的操作，不实际执行',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        now = timezone.now()
        
        # 1. 检查2小时后未确认的通知（发送二次提醒）
        two_hours_ago = now - timedelta(hours=2)
        unconfirmed_2h = LitigationNotificationConfirmation.objects.filter(
            status__in=['pending', 'read_unconfirmed'],
            sent_at__lte=two_hours_ago,
            escalation_level=0
        ).select_related('case', 'recipient')
        
        count_2h = 0
        for notification in unconfirmed_2h:
            if dry_run:
                self.stdout.write(
                    f"[DRY-RUN] 2小时未确认：{notification.notification_title} - {notification.recipient.username}"
                )
            else:
                self._send_escalation_reminder(notification, level=1)
                count_2h += 1
        
        # 2. 检查4小时后仍未确认的通知（通知上级领导）
        four_hours_ago = now - timedelta(hours=4)
        unconfirmed_4h = LitigationNotificationConfirmation.objects.filter(
            status__in=['pending', 'read_unconfirmed'],
            sent_at__lte=four_hours_ago,
            escalation_level=1
        ).select_related('case', 'recipient')
        
        count_4h = 0
        for notification in unconfirmed_4h:
            if dry_run:
                self.stdout.write(
                    f"[DRY-RUN] 4小时未确认（通知上级）：{notification.notification_title} - {notification.recipient.username}"
                )
            else:
                self._notify_supervisor(notification)
                count_4h += 1
        
        # 3. 检查6小时后仍未确认的紧急通知（电话通知）
        six_hours_ago = now - timedelta(hours=6)
        urgent_unconfirmed = LitigationNotificationConfirmation.objects.filter(
            status__in=['pending', 'read_unconfirmed'],
            sent_at__lte=six_hours_ago,
            escalation_level__lt=3,
            urgency_level__in=['urgent', 'important']
        ).select_related('case', 'recipient')
        
        count_6h = 0
        for notification in urgent_unconfirmed:
            if dry_run:
                self.stdout.write(
                    f"[DRY-RUN] 6小时未确认（电话通知）：{notification.notification_title} - {notification.recipient.username}"
                )
            else:
                self._phone_notification(notification)
                count_6h += 1
        
        if dry_run:
            self.stdout.write(
                self.style.SUCCESS(
                    f'\n[DRY-RUN] 将处理：\n'
                    f'  - 2小时未确认：{unconfirmed_2h.count()} 条\n'
                    f'  - 4小时未确认：{unconfirmed_4h.count()} 条\n'
                    f'  - 6小时紧急未确认：{urgent_unconfirmed.count()} 条'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'\n处理完成：\n'
                    f'  - 2小时未确认二次提醒：{count_2h} 条\n'
                    f'  - 4小时未确认通知上级：{count_4h} 条\n'
                    f'  - 6小时紧急电话通知：{count_6h} 条'
                )
            )
    
    def _send_escalation_reminder(self, notification, level=1):
        """发送升级提醒"""
        try:
            # 升级通知记录
            notification.escalate(level=level)
            
            # 发送二次提醒
            subject = f"【二次提醒】{notification.notification_title}"
            body = f"""
{notification.notification_content}

⚠️ 此通知已发送超过2小时，请尽快确认。
如未及时确认，系统将自动通知您的上级领导。
            """.strip()
            
            # 发送系统通知
            LitigationNotificationService._create_system_notification(
                recipient=notification.recipient,
                title=subject,
                message=body,
                case=notification.case,
                timeline=notification.timeline,
                seal=notification.seal,
                notification_type=notification.notification_type
            )
            
            # 发送邮件提醒
            if notification.recipient.email:
                try:
                    message = NotificationMessage(
                        subject=subject,
                        body=body,
                        to_emails=[notification.recipient.email]
                    )
                    send_email_notification(message)
                except Exception as e:
                    logger.error(f"发送升级邮件失败: {str(e)}")
            
            logger.info(f"已发送二次提醒：{notification.id}")
        except Exception as e:
            logger.error(f"发送升级提醒失败: {str(e)}", exc_info=True)
    
    def _notify_supervisor(self, notification):
        """通知上级领导"""
        try:
            recipient = notification.recipient
            
            # 获取上级领导（这里简化处理，实际应该从组织架构获取）
            supervisor = None
            if hasattr(recipient, 'department') and recipient.department:
                # 尝试获取部门负责人
                if hasattr(recipient.department, 'manager'):
                    supervisor = recipient.department.manager
            
            if not supervisor:
                # 如果没有找到上级，记录日志
                logger.warning(f"未找到用户 {recipient.username} 的上级领导")
                notification.escalate(level=2)
                return
            
            # 升级通知记录
            notification.escalate(escalated_to_user=supervisor, level=2)
            
            # 通知上级
            subject = f"【紧急】下属未确认通知：{notification.notification_title}"
            body = f"""
您的下属 {recipient.username} 收到以下通知但未及时确认：

{notification.notification_content}

案件：{notification.case.case_number} - {notification.case.case_name}
通知时间：{notification.sent_at.strftime('%Y-%m-%d %H:%M')}
未确认时长：超过4小时

请督促相关人员及时处理。
            """.strip()
            
            # 发送系统通知给上级
            LitigationNotificationService._create_system_notification(
                recipient=supervisor,
                title=subject,
                message=body,
                case=notification.case,
                timeline=notification.timeline,
                seal=notification.seal,
                notification_type=notification.notification_type
            )
            
            # 发送邮件给上级
            if supervisor.email:
                try:
                    message = NotificationMessage(
                        subject=subject,
                        body=body,
                        to_emails=[supervisor.email]
                    )
                    send_email_notification(message)
                except Exception as e:
                    logger.error(f"发送上级通知邮件失败: {str(e)}")
            
            logger.info(f"已通知上级领导：{notification.id} -> {supervisor.username}")
        except Exception as e:
            logger.error(f"通知上级领导失败: {str(e)}", exc_info=True)
    
    def _phone_notification(self, notification):
        """电话通知（记录日志，实际项目中应该调用电话服务）"""
        try:
            # 升级通知记录
            notification.escalate(level=3)
            
            # 记录电话通知日志
            logger.warning(
                f"紧急通知需要电话确认："
                f"通知ID={notification.id}, "
                f"接收人={notification.recipient.username}, "
                f"电话={getattr(notification.recipient, 'phone', '未设置')}, "
                f"通知标题={notification.notification_title}"
            )
            
            # 实际项目中应该调用电话通知服务
            # phone_service.call(notification.recipient.phone, notification.notification_content)
            
            logger.info(f"已记录电话通知需求：{notification.id}")
        except Exception as e:
            logger.error(f"电话通知处理失败: {str(e)}", exc_info=True)

