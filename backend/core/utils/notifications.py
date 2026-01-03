"""
通用通知工具模块
提供邮件通知、企业微信通知等功能
"""
import logging
from typing import List, Optional
from django.core.mail import send_mail
from django.conf import settings

logger = logging.getLogger(__name__)


class NotificationMessage:
    """通知消息类"""
    def __init__(self, subject: str, body: str, html_body: Optional[str] = None,
                 to_emails: Optional[List[str]] = None,
                 to_wecom: Optional[List[str]] = None):
        self.subject = subject
        self.body = body
        self.html_body = html_body
        self.to_emails = to_emails or []
        self.to_wecom = to_wecom or []


def send_email_notification(message: NotificationMessage):
    """发送邮件通知"""
    if not message.to_emails:
        logger.warning("邮件通知：没有指定收件人")
        return False
    
    try:
        from_email = getattr(settings, 'COMPANY_EMAIL', getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@example.com'))
        
        if message.html_body:
            from django.core.mail import EmailMultiAlternatives
            email = EmailMultiAlternatives(
                subject=message.subject,
                body=message.body,
                from_email=from_email,
                to=message.to_emails,
            )
            email.attach_alternative(message.html_body, "text/html")
            email.send()
        else:
            send_mail(
                subject=message.subject,
                message=message.body,
                from_email=from_email,
                recipient_list=message.to_emails,
                fail_silently=False,
            )
        logger.info(f"邮件通知发送成功：{message.subject} -> {message.to_emails}")
        return True
    except Exception as e:
        logger.error(f"发送邮件通知失败: {str(e)}", exc_info=True)
        return False


def send_wecom_notification(message: NotificationMessage):
    """发送企业微信通知"""
    if not message.to_wecom:
        logger.warning("企微通知：没有指定接收人")
        return False
    
    try:
        # 企业微信配置
        agent_id = getattr(settings, 'WECOM_AGENT_ID', None)
        corp_id = getattr(settings, 'WECOM_CORP_ID', None)
        agent_secret = getattr(settings, 'WECOM_AGENT_SECRET', None)
        
        if not all([agent_id, corp_id, agent_secret]):
            logger.warning("企业微信配置不完整，跳过企微通知")
            return False
        
        # 这里可以集成企业微信API
        # 暂时只记录日志
        logger.info(f"企微通知（模拟）：{message.subject} -> {message.to_wecom}")
        return True
    except Exception as e:
        logger.error(f"发送企微通知失败: {str(e)}", exc_info=True)
        return False

