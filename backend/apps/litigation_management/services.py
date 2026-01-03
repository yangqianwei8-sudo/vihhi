"""
诉讼管理通知服务
实现多方式通知功能：系统通知、邮件通知、短信通知
"""
import logging
from datetime import timedelta
from typing import List, Optional
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings

from backend.core.utils.notifications import (
    NotificationMessage,
    send_email_notification,
    send_wecom_notification
)
from backend.apps.litigation_management.models import (
    LitigationCase, LitigationTimeline, PreservationSeal,
    LitigationNotificationConfirmation
)

User = get_user_model()
logger = logging.getLogger(__name__)


class LitigationNotificationService:
    """诉讼管理通知服务"""
    
    @staticmethod
    def send_trial_notification(timeline: LitigationTimeline, days_before: int):
        """
        发送开庭时间提醒
        必须多方式通知：系统通知 + 邮件通知 + 短信通知同时发送
        提醒时间点：提前7天、提前3天、提前1天、开庭当天（共4次提醒）
        """
        case = timeline.case
        
        # 确定通知对象
        recipients = []
        if case.case_manager:
            recipients.append(case.case_manager)
        if case.registered_by:
            recipients.append(case.registered_by)
        
        # 如果没有指定接收人，跳过
        if not recipients:
            logger.warning(f"案件 {case.case_number} 没有指定负责人，跳过开庭提醒")
            return
        
        # 构建通知内容
        if days_before == 0:
            subject = f"【紧急】开庭提醒：{case.case_number} - {case.case_name} 今天开庭"
            urgency = "紧急"
        elif days_before == 1:
            subject = f"【重要】开庭提醒：{case.case_number} - {case.case_name} 明天开庭"
            urgency = "重要"
        elif days_before == 3:
            subject = f"开庭提醒：{case.case_number} - {case.case_name} 3天后开庭"
            urgency = "一般"
        else:
            subject = f"开庭提醒：{case.case_number} - {case.case_name} {days_before}天后开庭"
            urgency = "一般"
        
        body = f"""
案件编号：{case.case_number}
案件名称：{case.case_name}
开庭时间：{timeline.timeline_date.strftime('%Y年%m月%d日')}
开庭地点：{timeline.description or '待确认'}
提醒级别：{urgency}

请提前做好准备，确保按时出庭。
        """.strip()
        
        html_body = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #142F5B;">{subject}</h2>
            <div style="background: #f5f5f5; padding: 20px; border-radius: 8px; margin: 20px 0;">
                <p><strong>案件编号：</strong>{case.case_number}</p>
                <p><strong>案件名称：</strong>{case.case_name}</p>
                <p><strong>开庭时间：</strong>{timeline.timeline_date.strftime('%Y年%m月%d日')}</p>
                <p><strong>开庭地点：</strong>{timeline.description or '待确认'}</p>
                <p><strong>提醒级别：</strong><span style="color: {'red' if urgency == '紧急' else 'orange' if urgency == '重要' else 'blue'}">{urgency}</span></p>
            </div>
            <p style="color: #666;">请提前做好准备，确保按时出庭。</p>
        </div>
        """
        
        # 发送通知
        for recipient in recipients:
            # 发送通知并记录
            sent_via_email = False
            sent_via_sms = False
            
            # 1. 系统通知（创建通知记录）
            LitigationNotificationService._create_system_notification(
                recipient=recipient,
                title=subject,
                message=body,
                case=case,
                timeline=timeline,
                notification_type='trial_reminder'
            )
            
            # 2. 邮件通知
            if recipient.email:
                try:
                    message = NotificationMessage(
                        subject=subject,
                        body=body,
                        html_body=html_body,
                        to_emails=[recipient.email]
                    )
                    send_email_notification(message)
                    sent_via_email = True
                except Exception as e:
                    logger.error(f"发送邮件通知失败: {str(e)}")
            
            # 3. 短信通知（通过企微或其他渠道）
            if hasattr(recipient, 'wecom_id') and recipient.wecom_id:
                try:
                    message = NotificationMessage(
                        subject=subject,
                        body=body,
                        to_wecom=[recipient.wecom_id]
                    )
                    send_wecom_notification(message)
                    sent_via_sms = True
                except Exception as e:
                    logger.error(f"发送企微通知失败: {str(e)}")
            
            # 4. 创建通知确认记录（法院关键节点必须确认）
            LitigationNotificationConfirmation.objects.create(
                notification_type='trial_reminder',
                notification_title=subject,
                notification_content=body,
                case=case,
                timeline=timeline,
                recipient=recipient,
                status='pending',
                sent_via_system=True,
                sent_via_email=sent_via_email,
                sent_via_sms=sent_via_sms,
                urgency_level='urgent' if urgency == '紧急' else 'important' if urgency == '重要' else 'normal'
            )
    
    @staticmethod
    def send_preservation_renewal_notification(seal: PreservationSeal, days_before: int):
        """
        发送保全续封时间提醒
        必须多方式通知：系统通知 + 邮件通知 + 短信通知同时发送
        提醒时间点：到期前30天、15天、7天、3天、1天、到期当天（共6次提醒）
        未确认的立即电话通知
        """
        case = seal.case
        
        # 确定通知对象
        recipients = []
        if case.case_manager:
            recipients.append(case.case_manager)
        if case.registered_by:
            recipients.append(case.registered_by)
        
        if not recipients:
            logger.warning(f"案件 {case.case_number} 没有指定负责人，跳过保全续封提醒")
            return
        
        # 构建通知内容
        if days_before == 0:
            subject = f"【紧急】保全续封到期提醒：{case.case_number} - {seal.get_seal_type_display()} 今天到期"
            urgency = "紧急"
            risk_warning = "⚠️ 如未及时续封将导致保全失效，造成重大损失！"
        elif days_before == 1:
            subject = f"【紧急】保全续封到期提醒：{case.case_number} - {seal.get_seal_type_display()} 明天到期"
            urgency = "紧急"
            risk_warning = "⚠️ 如未及时续封将导致保全失效，造成重大损失！"
        elif days_before == 3:
            subject = f"【重要】保全续封到期提醒：{case.case_number} - {seal.get_seal_type_display()} 3天后到期"
            urgency = "重要"
            risk_warning = "⚠️ 如未及时续封将导致保全失效，造成重大损失！"
        else:
            subject = f"保全续封到期提醒：{case.case_number} - {seal.get_seal_type_display()} {days_before}天后到期"
            urgency = "一般"
            risk_warning = "请及时处理续封事宜。"
        
        body = f"""
案件编号：{case.case_number}
案件名称：{case.case_name}
保全类型：{seal.get_seal_type_display()}
保全案号：{seal.seal_number or '未设置'}
法院名称：{seal.court_name or '未设置'}
到期时间：{seal.end_date.strftime('%Y年%m月%d日')}
剩余天数：{days_before}天
提醒级别：{urgency}

{risk_warning}
        """.strip()
        
        html_body = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #dc3545;">{subject}</h2>
            <div style="background: #fff3cd; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #ffc107;">
                <p><strong>案件编号：</strong>{case.case_number}</p>
                <p><strong>案件名称：</strong>{case.case_name}</p>
                <p><strong>保全类型：</strong>{seal.get_seal_type_display()}</p>
                <p><strong>保全案号：</strong>{seal.seal_number or '未设置'}</p>
                <p><strong>法院名称：</strong>{seal.court_name or '未设置'}</p>
                <p><strong>到期时间：</strong>{seal.end_date.strftime('%Y年%m月%d日')}</p>
                <p><strong>剩余天数：</strong><span style="color: red; font-weight: bold;">{days_before}天</span></p>
                <p><strong>提醒级别：</strong><span style="color: red;">{urgency}</span></p>
            </div>
            <div style="background: #f8d7da; padding: 15px; border-radius: 8px; margin: 20px 0;">
                <p style="color: #721c24; font-weight: bold; margin: 0;">{risk_warning}</p>
            </div>
        </div>
        """
        
        # 发送通知
        for recipient in recipients:
            sent_via_email = False
            sent_via_sms = False
            
            # 1. 系统通知
            LitigationNotificationService._create_system_notification(
                recipient=recipient,
                title=subject,
                message=body,
                case=case,
                seal=seal,
                notification_type='preservation_renewal'
            )
            
            # 2. 邮件通知
            if recipient.email:
                try:
                    message = NotificationMessage(
                        subject=subject,
                        body=body,
                        html_body=html_body,
                        to_emails=[recipient.email]
                    )
                    send_email_notification(message)
                    sent_via_email = True
                except Exception as e:
                    logger.error(f"发送邮件通知失败: {str(e)}")
            
            # 3. 短信/企微通知
            if hasattr(recipient, 'wecom_id') and recipient.wecom_id:
                try:
                    message = NotificationMessage(
                        subject=subject,
                        body=body,
                        to_wecom=[recipient.wecom_id]
                    )
                    send_wecom_notification(message)
                    sent_via_sms = True
                except Exception as e:
                    logger.error(f"发送企微通知失败: {str(e)}")
            
            # 4. 创建通知确认记录（保全续封必须确认）
            LitigationNotificationConfirmation.objects.create(
                notification_type='preservation_renewal',
                notification_title=subject,
                notification_content=body,
                case=case,
                seal=seal,
                recipient=recipient,
                status='pending',
                sent_via_system=True,
                sent_via_email=sent_via_email,
                sent_via_sms=sent_via_sms,
                urgency_level='urgent' if urgency == '紧急' else 'important'
            )
            
            # 5. 紧急情况（3天内）未确认时电话通知
            if days_before <= 3:
                logger.warning(f"保全续封紧急提醒：{case.case_number}，需要电话通知 {recipient.username}")
    
    @staticmethod
    def send_deadline_notification(timeline: LitigationTimeline, deadline_type: str, days_before: int):
        """
        发送期限提醒（上诉期限、举证期限、答辩期限等）
        必须多方式通知：系统通知 + 邮件通知 + 短信通知同时发送
        """
        case = timeline.case
        
        recipients = []
        if case.case_manager:
            recipients.append(case.case_manager)
        if case.registered_by:
            recipients.append(case.registered_by)
        
        if not recipients:
            return
        
        deadline_names = {
            'appeal': '上诉期限',
            'evidence': '举证期限',
            'defense': '答辩期限',
        }
        
        deadline_name = deadline_names.get(deadline_type, '期限')
        
        if days_before == 0:
            subject = f"【紧急】{deadline_name}到期提醒：{case.case_number} - {case.case_name} 今天到期"
        elif days_before == 1:
            subject = f"【重要】{deadline_name}到期提醒：{case.case_number} - {case.case_name} 明天到期"
        else:
            subject = f"{deadline_name}到期提醒：{case.case_number} - {case.case_name} {days_before}天后到期"
        
        body = f"""
案件编号：{case.case_number}
案件名称：{case.case_name}
{deadline_name}：{timeline.timeline_date.strftime('%Y年%m月%d日')}
剩余天数：{days_before}天

请及时处理相关事宜，避免逾期。
        """.strip()
        
        # 发送通知
        notification_type_map = {
            'appeal': 'appeal_deadline',
            'evidence': 'evidence_deadline',
            'defense': 'defense_deadline',
        }
        notification_type = notification_type_map.get(deadline_type, 'other')
        
        for recipient in recipients:
            sent_via_email = False
            sent_via_sms = False
            
            LitigationNotificationService._create_system_notification(
                recipient=recipient,
                title=subject,
                message=body,
                case=case,
                timeline=timeline,
                notification_type=notification_type
            )
            
            if recipient.email:
                try:
                    message = NotificationMessage(
                        subject=subject,
                        body=body,
                        to_emails=[recipient.email]
                    )
                    send_email_notification(message)
                    sent_via_email = True
                except Exception as e:
                    logger.error(f"发送邮件通知失败: {str(e)}")
            
            if hasattr(recipient, 'wecom_id') and recipient.wecom_id:
                try:
                    message = NotificationMessage(
                        subject=subject,
                        body=body,
                        to_wecom=[recipient.wecom_id]
                    )
                    send_wecom_notification(message)
                    sent_via_sms = True
                except Exception as e:
                    logger.error(f"发送企微通知失败: {str(e)}")
            
            # 创建通知确认记录
            LitigationNotificationConfirmation.objects.create(
                notification_type=notification_type,
                notification_title=subject,
                notification_content=body,
                case=case,
                timeline=timeline,
                recipient=recipient,
                status='pending',
                sent_via_system=True,
                sent_via_email=sent_via_email,
                sent_via_sms=sent_via_sms,
                urgency_level='urgent' if days_before <= 1 else 'important' if days_before <= 3 else 'normal'
            )
    
    @staticmethod
    def _create_system_notification(
        recipient: User,
        title: str,
        message: str,
        case: LitigationCase,
        timeline: Optional[LitigationTimeline] = None,
        seal: Optional[PreservationSeal] = None,
        notification_type: str = 'general'
    ):
        """创建系统通知记录"""
        try:
            from backend.apps.production_management.models import ProjectTeamNotification
            
            action_url = f"/litigation/cases/{case.id}/"
            if timeline:
                action_url = f"/litigation/timelines/{timeline.id}/"
            elif seal:
                action_url = f"/litigation/preservation/{seal.id}/"
            
            ProjectTeamNotification.objects.create(
                recipient=recipient,
                title=title,
                message=message,
                category='quality_alert',  # 使用质量提醒分类
                action_url=action_url,
                context={
                    'case_id': case.id,
                    'case_number': case.case_number,
                    'notification_type': notification_type,
                    'timeline_id': timeline.id if timeline else None,
                    'seal_id': seal.id if seal else None,
                }
            )
        except Exception as e:
            logger.error(f"创建系统通知失败: {e}")


class LitigationReminderService:
    """诉讼管理提醒服务 - 定时检查并发送提醒"""
    
    @staticmethod
    def check_and_send_trial_reminders():
        """检查并发送开庭时间提醒"""
        today = timezone.now().date()
        
        # 检查需要提醒的时间节点（开庭类型）
        timelines = LitigationTimeline.objects.filter(
            timeline_type='trial',
            reminder_enabled=True,
            status__in=['pending', 'in_progress']
        ).select_related('case')
        
        reminder_days = [7, 3, 1, 0]  # 提前7天、3天、1天、当天
        
        for timeline in timelines:
            # timeline_date是DateTimeField，需要转换为date
            timeline_date = timeline.timeline_date.date() if hasattr(timeline.timeline_date, 'date') else timeline.timeline_date
            for days_before in reminder_days:
                reminder_date = timeline_date - timedelta(days=days_before)
                if reminder_date == today:
                    LitigationNotificationService.send_trial_notification(timeline, days_before)
    
    @staticmethod
    def check_and_send_preservation_reminders():
        """检查并发送保全续封提醒"""
        today = timezone.now().date()
        
        # 检查即将到期的保全续封
        seals = PreservationSeal.objects.filter(
            status='active',
            end_date__gte=today
        ).select_related('case')
        
        reminder_days = [30, 15, 7, 3, 1, 0]  # 提前30天、15天、7天、3天、1天、当天
        
        for seal in seals:
            for days_before in reminder_days:
                reminder_date = seal.end_date - timedelta(days=days_before)
                if reminder_date == today:
                    LitigationNotificationService.send_preservation_renewal_notification(seal, days_before)
    
    @staticmethod
    def check_and_send_deadline_reminders():
        """检查并发送期限提醒"""
        today = timezone.now().date()
        
        deadline_types = ['appeal', 'evidence', 'defense']
        reminder_days = [7, 3, 1, 0]
        
        for deadline_type in deadline_types:
            timelines = LitigationTimeline.objects.filter(
                timeline_type=deadline_type,
                reminder_enabled=True,
                status__in=['pending', 'in_progress']
            ).select_related('case')
            
            for timeline in timelines:
                # timeline_date是DateTimeField，需要转换为date
                timeline_date = timeline.timeline_date.date() if hasattr(timeline.timeline_date, 'date') else timeline.timeline_date
                for days_before in reminder_days:
                    reminder_date = timeline_date - timedelta(days=days_before)
                    if reminder_date == today:
                        LitigationNotificationService.send_deadline_notification(
                            timeline, deadline_type, days_before
                        )

