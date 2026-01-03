"""
通用工具模块
"""
from .notifications import NotificationMessage, send_email_notification, send_wecom_notification

__all__ = ['NotificationMessage', 'send_email_notification', 'send_wecom_notification']

