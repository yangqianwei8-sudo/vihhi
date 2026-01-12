"""
测试发送提醒给系统管理员

使用方法：
    python manage.py test_send_reminder_to_admin
    python manage.py test_send_reminder_to_admin --type monthly
    python manage.py test_send_reminder_to_admin --type weekly
    python manage.py test_send_reminder_to_admin --type quarterly
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.urls import reverse
import logging
from datetime import datetime, timedelta
from calendar import monthrange

from backend.core.utils.notifications import (
    NotificationMessage,
    send_email_notification,
    send_wecom_notification
)

User = get_user_model()
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = '测试发送提醒给系统管理员'

    def add_arguments(self, parser):
        parser.add_argument(
            '--type',
            type=str,
            choices=['daily', 'weekly', 'monthly', 'quarterly', 'all'],
            default='all',
            help='提醒类型：daily(日), weekly(周), monthly(月度), quarterly(季度), all(全部)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='试运行模式：不实际发送，只显示将要发送的内容',
        )

    def send_daily_reminder(self, admin_user, dry_run=False):
        """发送日提醒"""
        now = timezone.now()
        today = now.date()
        today_str = today.strftime('%Y年%m月%d日')
        
        subject = f'【测试】日工作计划提醒 - {now.strftime("%Y-%m-%d %H:%M:%S")}'
        
        try:
            plan_create_url = reverse('plan_pages:plan_create')
            from django.conf import settings
            base_url = getattr(settings, 'BASE_URL', 'http://localhost:8001')
            if not plan_create_url.startswith('http'):
                plan_create_url = f"{base_url}{plan_create_url}"
        except Exception as e:
            logger.warning(f"无法构建计划创建URL: {str(e)}")
            plan_create_url = '/plan/plans/create/'
        
        body = f"""
【测试消息】日工作计划提醒

尊敬的系统管理员：

这是一条测试消息，用于验证日工作计划提醒功能是否正常工作。

提醒时间：{now.strftime('%Y年%m月%d日 %H:%M:%S')}
提醒类型：日工作计划提醒
今日日期：{today_str}

请及时登录系统，进入"计划管理"模块，点击"新建工作计划"进行编制，计划周期请选择"日计划"。

计划创建地址：{plan_create_url}

维海科技信息化管理平台
        """.strip()
        
        html_body = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <h2 style="color: #1F2A57; border-bottom: 2px solid #1F2A57; padding-bottom: 10px;">
                【测试】日工作计划提醒
            </h2>
            <div style="line-height: 1.8; color: #333;">
                <p>尊敬的系统管理员：</p>
                <p>这是一条<strong style="color: #EF4444;">测试消息</strong>，用于验证日工作计划提醒功能是否正常工作。</p>
                <p><strong>提醒时间：</strong>{now.strftime('%Y年%m月%d日 %H:%M:%S')}</p>
                <p><strong>提醒类型：</strong>日工作计划提醒</p>
                <p><strong>今日日期：</strong>{today_str}</p>
                <p>请及时登录系统，进入"计划管理"模块，点击"新建工作计划"进行编制，计划周期请选择"日计划"。</p>
                <div style="background: #f8f9fa; padding: 15px; border-left: 4px solid #1F2A57; margin: 20px 0;">
                    <p style="margin: 0;"><strong>计划创建地址：</strong></p>
                    <p style="margin: 5px 0 0 0;"><a href="{plan_create_url}" style="color: #1F2A57; text-decoration: none;">{plan_create_url}</a></p>
                </div>
                <p style="margin-top: 30px;">
                    <strong>维海科技信息化管理平台</strong><br>
                    {now.strftime('%Y年%m月%d日')}
                </p>
            </div>
        </div>
        """
        
        return self._send_notification(admin_user, subject, body, html_body, dry_run, "日")

    def send_monthly_reminder(self, admin_user, dry_run=False):
        """发送月度提醒"""
        now = timezone.now()
        next_month = now + timedelta(days=32)
        next_month = next_month.replace(day=1)
        
        subject = f'【测试】月度工作计划提醒 - {now.strftime("%Y-%m-%d %H:%M:%S")}'
        
        try:
            plan_create_url = reverse('plan_pages:plan_create')
            from django.conf import settings
            base_url = getattr(settings, 'BASE_URL', 'http://localhost:8001')
            if not plan_create_url.startswith('http'):
                plan_create_url = f"{base_url}{plan_create_url}"
        except Exception as e:
            logger.warning(f"无法构建计划创建URL: {str(e)}")
            plan_create_url = '/plan/plans/create/'
        
        body = f"""
【测试消息】月度工作计划提醒

尊敬的系统管理员：

这是一条测试消息，用于验证月度工作计划提醒功能是否正常工作。

提醒时间：{now.strftime('%Y年%m月%d日 %H:%M:%S')}
提醒类型：月度工作计划提醒

请及时登录系统，进入"计划管理"模块，点击"新建工作计划"进行编制，计划周期请选择"月计划"。

计划创建地址：{plan_create_url}

维海科技信息化管理平台
        """.strip()
        
        html_body = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <h2 style="color: #1F2A57; border-bottom: 2px solid #1F2A57; padding-bottom: 10px;">
                【测试】月度工作计划提醒
            </h2>
            <div style="line-height: 1.8; color: #333;">
                <p>尊敬的系统管理员：</p>
                <p>这是一条<strong style="color: #EF4444;">测试消息</strong>，用于验证月度工作计划提醒功能是否正常工作。</p>
                <p><strong>提醒时间：</strong>{now.strftime('%Y年%m月%d日 %H:%M:%S')}</p>
                <p><strong>提醒类型：</strong>月度工作计划提醒</p>
                <p>请及时登录系统，进入"计划管理"模块，点击"新建工作计划"进行编制，计划周期请选择"月计划"。</p>
                <div style="background: #f8f9fa; padding: 15px; border-left: 4px solid #1F2A57; margin: 20px 0;">
                    <p style="margin: 0;"><strong>计划创建地址：</strong></p>
                    <p style="margin: 5px 0 0 0;"><a href="{plan_create_url}" style="color: #1F2A57; text-decoration: none;">{plan_create_url}</a></p>
                </div>
                <p style="margin-top: 30px;">
                    <strong>维海科技信息化管理平台</strong><br>
                    {now.strftime('%Y年%m月%d日')}
                </p>
            </div>
        </div>
        """
        
        return self._send_notification(admin_user, subject, body, html_body, dry_run, "月度")

    def send_weekly_reminder(self, admin_user, dry_run=False):
        """发送周提醒"""
        now = timezone.now()
        today = now.date()
        
        days_until_friday = (4 - today.weekday()) % 7
        if days_until_friday == 0 and now.hour < 9:
            this_friday = today
        elif days_until_friday == 0:
            this_friday = today + timedelta(days=7)
        else:
            this_friday = today + timedelta(days=days_until_friday)
        
        next_monday = this_friday + timedelta(days=3)
        next_sunday = next_monday + timedelta(days=6)
        week_str = f"{next_monday.strftime('%Y年%m月%d日')} - {next_sunday.strftime('%m月%d日')}"
        
        subject = f'【测试】周工作计划提醒 - {now.strftime("%Y-%m-%d %H:%M:%S")}'
        
        try:
            plan_create_url = reverse('plan_pages:plan_create')
            from django.conf import settings
            base_url = getattr(settings, 'BASE_URL', 'http://localhost:8001')
            if not plan_create_url.startswith('http'):
                plan_create_url = f"{base_url}{plan_create_url}"
        except Exception as e:
            logger.warning(f"无法构建计划创建URL: {str(e)}")
            plan_create_url = '/plan/plans/create/'
        
        body = f"""
【测试消息】周工作计划提醒

尊敬的系统管理员：

这是一条测试消息，用于验证周工作计划提醒功能是否正常工作。

提醒时间：{now.strftime('%Y年%m月%d日 %H:%M:%S')}
提醒类型：周工作计划提醒
下周日期：{week_str}

请及时登录系统，进入"计划管理"模块，点击"新建工作计划"进行编制，计划周期请选择"周计划"。

计划创建地址：{plan_create_url}

维海科技信息化管理平台
        """.strip()
        
        html_body = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <h2 style="color: #1F2A57; border-bottom: 2px solid #1F2A57; padding-bottom: 10px;">
                【测试】周工作计划提醒
            </h2>
            <div style="line-height: 1.8; color: #333;">
                <p>尊敬的系统管理员：</p>
                <p>这是一条<strong style="color: #EF4444;">测试消息</strong>，用于验证周工作计划提醒功能是否正常工作。</p>
                <p><strong>提醒时间：</strong>{now.strftime('%Y年%m月%d日 %H:%M:%S')}</p>
                <p><strong>提醒类型：</strong>周工作计划提醒</p>
                <p><strong>下周日期：</strong>{week_str}</p>
                <p>请及时登录系统，进入"计划管理"模块，点击"新建工作计划"进行编制，计划周期请选择"周计划"。</p>
                <div style="background: #f8f9fa; padding: 15px; border-left: 4px solid #1F2A57; margin: 20px 0;">
                    <p style="margin: 0;"><strong>计划创建地址：</strong></p>
                    <p style="margin: 5px 0 0 0;"><a href="{plan_create_url}" style="color: #1F2A57; text-decoration: none;">{plan_create_url}</a></p>
                </div>
                <p style="margin-top: 30px;">
                    <strong>维海科技信息化管理平台</strong><br>
                    {now.strftime('%Y年%m月%d日')}
                </p>
            </div>
        </div>
        """
        
        return self._send_notification(admin_user, subject, body, html_body, dry_run, "周")

    def send_quarterly_reminder(self, admin_user, dry_run=False):
        """发送季度提醒"""
        now = timezone.now()
        current_month = now.month
        
        if current_month in [1, 2, 3]:
            next_quarter_start_month = 4
            next_quarter_end_month = 6
            quarter_name = '第二季度'
            current_year = now.year
        elif current_month in [4, 5, 6]:
            next_quarter_start_month = 7
            next_quarter_end_month = 9
            quarter_name = '第三季度'
            current_year = now.year
        elif current_month in [7, 8, 9]:
            next_quarter_start_month = 10
            next_quarter_end_month = 12
            quarter_name = '第四季度'
            current_year = now.year
        else:
            next_quarter_start_month = 1
            next_quarter_end_month = 3
            quarter_name = '第一季度'
            current_year = now.year + 1
        
        next_quarter_start = datetime(current_year, next_quarter_start_month, 1).date()
        last_day = monthrange(current_year, next_quarter_end_month)[1]
        next_quarter_end = datetime(current_year, next_quarter_end_month, last_day).date()
        
        quarter_str = f"{current_year}年{quarter_name}（{next_quarter_start.strftime('%Y年%m月%d日')} - {next_quarter_end.strftime('%Y年%m月%d日')}）"
        
        subject = f'【测试】季度工作计划提醒 - {now.strftime("%Y-%m-%d %H:%M:%S")}'
        
        try:
            plan_create_url = reverse('plan_pages:plan_create')
            from django.conf import settings
            base_url = getattr(settings, 'BASE_URL', 'http://localhost:8001')
            if not plan_create_url.startswith('http'):
                plan_create_url = f"{base_url}{plan_create_url}"
        except Exception as e:
            logger.warning(f"无法构建计划创建URL: {str(e)}")
            plan_create_url = '/plan/plans/create/'
        
        body = f"""
【测试消息】季度工作计划提醒

尊敬的系统管理员：

这是一条测试消息，用于验证季度工作计划提醒功能是否正常工作。

提醒时间：{now.strftime('%Y年%m月%d日 %H:%M:%S')}
提醒类型：季度工作计划提醒
提醒季度：{quarter_str}

请及时登录系统，进入"计划管理"模块，点击"新建工作计划"进行编制，计划周期请选择"季度计划"。

计划创建地址：{plan_create_url}

维海科技信息化管理平台
        """.strip()
        
        html_body = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <h2 style="color: #1F2A57; border-bottom: 2px solid #1F2A57; padding-bottom: 10px;">
                【测试】季度工作计划提醒
            </h2>
            <div style="line-height: 1.8; color: #333;">
                <p>尊敬的系统管理员：</p>
                <p>这是一条<strong style="color: #EF4444;">测试消息</strong>，用于验证季度工作计划提醒功能是否正常工作。</p>
                <p><strong>提醒时间：</strong>{now.strftime('%Y年%m月%d日 %H:%M:%S')}</p>
                <p><strong>提醒类型：</strong>季度工作计划提醒</p>
                <p><strong>提醒季度：</strong>{quarter_str}</p>
                <p>请及时登录系统，进入"计划管理"模块，点击"新建工作计划"进行编制，计划周期请选择"季度计划"。</p>
                <div style="background: #f8f9fa; padding: 15px; border-left: 4px solid #1F2A57; margin: 20px 0;">
                    <p style="margin: 0;"><strong>计划创建地址：</strong></p>
                    <p style="margin: 5px 0 0 0;"><a href="{plan_create_url}" style="color: #1F2A57; text-decoration: none;">{plan_create_url}</a></p>
                </div>
                <p style="margin-top: 30px;">
                    <strong>维海科技信息化管理平台</strong><br>
                    {now.strftime('%Y年%m月%d日')}
                </p>
            </div>
        </div>
        """
        
        return self._send_notification(admin_user, subject, body, html_body, dry_run, "季度")

    def _send_notification(self, user, subject, body, html_body, dry_run, reminder_type):
        """发送通知的通用方法"""
        user_display = user.get_full_name() or user.username
        
        if dry_run:
            self.stdout.write(self.style.NOTICE(f'[试运行] 将发送{reminder_type}提醒给: {user_display} ({user.email or "无邮箱"})'))
            return True
        
        to_emails = []
        to_wecom = []
        
        if user.email:
            to_emails.append(user.email)
        
        if hasattr(user, 'wecom_id') and user.wecom_id:
            to_wecom.append(user.wecom_id)
        
        if not to_emails and not to_wecom:
            self.stdout.write(self.style.WARNING(f'  跳过 {user_display}：没有邮箱和企微ID'))
            return False
        
        message = NotificationMessage(
            subject=subject,
            body=body,
            html_body=html_body,
            to_emails=to_emails,
            to_wecom=to_wecom
        )
        
        email_sent = False
        wecom_sent = False
        
        if to_emails:
            try:
                email_sent = send_email_notification(message)
            except Exception as e:
                logger.error(f"发送邮件给 {user_display} 失败: {str(e)}")
                self.stdout.write(self.style.ERROR(f'  邮件发送失败: {str(e)}'))
        
        if to_wecom:
            try:
                wecom_sent = send_wecom_notification(message)
            except Exception as e:
                logger.error(f"发送企微通知给 {user_display} 失败: {str(e)}")
                self.stdout.write(self.style.ERROR(f'  企微发送失败: {str(e)}'))
        
        if email_sent or wecom_sent:
            methods = []
            if email_sent:
                methods.append('邮件')
            if wecom_sent:
                methods.append('企微')
            self.stdout.write(self.style.SUCCESS(f'  ✓ {reminder_type}提醒已通过{",".join(methods)}发送给 {user_display}'))
            return True
        else:
            self.stdout.write(self.style.ERROR(f'  ✗ {reminder_type}提醒发送失败给 {user_display}'))
            return False

    def handle(self, *args, **options):
        reminder_type = options.get('type', 'all')
        dry_run = options.get('dry_run', False)
        
        # 获取系统管理员（优先选择用户名为admin的，否则选择第一个）
        admins = User.objects.filter(is_superuser=True, is_active=True)
        admin_user = admins.filter(username='admin').first() or admins.first()
        
        if not admin_user:
            self.stdout.write(self.style.ERROR('未找到系统管理员用户'))
            return
        
        self.stdout.write(f'找到系统管理员: {admin_user.username} ({admin_user.get_full_name() or "无姓名"}) - {admin_user.email or "无邮箱"}')
        self.stdout.write('')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('试运行模式：不会实际发送通知'))
            self.stdout.write('')
        
        success_count = 0
        total_count = 0
        
        if reminder_type in ['daily', 'all']:
            total_count += 1
            if self.send_daily_reminder(admin_user, dry_run):
                success_count += 1
            self.stdout.write('')
        
        if reminder_type in ['weekly', 'all']:
            total_count += 1
            if self.send_weekly_reminder(admin_user, dry_run):
                success_count += 1
            self.stdout.write('')
        
        if reminder_type in ['monthly', 'all']:
            total_count += 1
            if self.send_monthly_reminder(admin_user, dry_run):
                success_count += 1
            self.stdout.write('')
        
        if reminder_type in ['quarterly', 'all']:
            total_count += 1
            if self.send_quarterly_reminder(admin_user, dry_run):
                success_count += 1
            self.stdout.write('')
        
        self.stdout.write(self.style.SUCCESS(f'\n测试完成：总计={total_count}, 成功={success_count}, 失败={total_count-success_count}'))
        
        if not dry_run:
            self.stdout.write(self.style.NOTICE(f'\n请检查 {admin_user.email or "管理员邮箱"} 是否收到提醒消息'))

