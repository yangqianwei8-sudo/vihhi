from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Iterable, Optional

from django.conf import settings
from django.core import mail
from django.core.mail import EmailMultiAlternatives

try:
    from wechatpy.enterprise import WeChatClient  # type: ignore
except ImportError:
    WeChatClient = None  # type: ignore


logger = logging.getLogger(__name__)


@dataclass
class NotificationMessage:
    subject: str
    body: str
    html_body: Optional[str] = None
    to_emails: Optional[Iterable[str]] = None
    to_wecom: Optional[Iterable[str]] = None


def send_email_notification(message: NotificationMessage) -> bool:
    if not message.to_emails:
        return False
    email = EmailMultiAlternatives(
        subject=message.subject,
        body=message.body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=list(message.to_emails),
    )
    if message.html_body:
        email.attach_alternative(message.html_body, "text/html")
    try:
        response = email.send()
        logger.info("Sent email notification to %s, response %s", message.to_emails, response)
        return True
    except Exception as exc:  # noqa: BLE001
        logger.exception("Failed to send email notification: %s", exc)
        return False


def send_wecom_notification(message: NotificationMessage) -> bool:
    if not message.to_wecom or not settings.WECOM_CORP_ID or not settings.WECOM_AGENT_SECRET:
        return False
    if WeChatClient is None:
        logger.warning("wechatpy not installed; skip WeCom notification.")
        return False
    try:
        client = WeChatClient(
            corp_id=settings.WECOM_CORP_ID,
            secret=settings.WECOM_AGENT_SECRET,
        )
        agent_id = settings.WECOM_AGENT_ID
        to_user = "|".join(message.to_wecom) if isinstance(message.to_wecom, Iterable) else message.to_wecom
        if not to_user:
            return False
        client.message.send_text(
            agent_id=agent_id,
            user_ids=to_user,
            content=f"{message.subject}\n{message.body}",
        )
        logger.info("Sent WeCom notification to %s", to_user)
        return True
    except Exception as exc:  # noqa: BLE001
        logger.exception("Failed to send WeCom notification: %s", exc)
        return False

