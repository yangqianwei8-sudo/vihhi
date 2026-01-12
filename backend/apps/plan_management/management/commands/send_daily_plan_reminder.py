"""
日工作计划提醒管理命令

使用方法：
    python manage.py send_daily_plan_reminder
    
建议配置为定时任务（crontab）：
    # 每天9点执行
    0 9 * * * cd /path/to/project && /path/to/venv/bin/python manage.py send_daily_plan_reminder
    
    # 或使用Celery Beat
    @periodic_task(run_every=crontab(hour=9, minute=0))
    def send_daily_plan_reminder_task():
        call_command('send_daily_plan_reminder')
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.urls import reverse
import logging
from datetime import datetime, timedelta

from backend.core.utils.notifications import (
    NotificationMessage,
    send_email_notification,
    send_wecom_notification
)

User = get_user_model()
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = '发送日工作计划编制提醒给所有员工'

    def add_arguments(self, parser):
        parser.add_argument(
            '--test',
            action='store_true',
            help='测试模式：只发送给前5个用户',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='试运行模式：不实际发送，只显示将要发送的内容',
        )

    def handle(self, *args, **options):
        test_mode = options.get('test', False)
        dry_run = options.get('dry_run', False)
        
        self.stdout.write(f'开始发送日工作计划提醒（时间：{timezone.now()}）...')
        
        # 获取所有激活的员工
        users = User.objects.filter(is_active=True)
        
        if test_mode:
            users = users[:5]
            self.stdout.write(self.style.WARNING(f'测试模式：只发送给前{users.count()}个用户'))
        
        if not users.exists():
            self.stdout.write(self.style.ERROR('没有找到激活的用户'))
            return
        
        self.stdout.write(f'找到 {users.count()} 个激活用户')
        
        # 获取今天的日期信息
        now = timezone.now()
        today = now.date()
        today_str = today.strftime('%Y年%m月%d日')
        
        # 构建通知内容
        subject = f'【日工作计划提醒】请及时编制今日工作计划（{today_str}）'
        
        # 获取计划创建页面的URL（需要构建完整URL）
        try:
            plan_create_url = reverse('plan_pages:plan_create')
            # 如果是相对路径，需要构建完整URL
            from django.conf import settings
            base_url = getattr(settings, 'BASE_URL', 'http://localhost:8001')
            if not plan_create_url.startswith('http'):
                plan_create_url = f"{base_url}{plan_create_url}"
        except Exception as e:
            logger.warning(f"无法构建计划创建URL: {str(e)}")
            plan_create_url = '/plan/plans/create/'
        
        body = f"""
尊敬的同仁：

您好！

根据工作计划管理制度，请每天上午9点前完成当日工作计划的编制工作。

本次提醒：请及时编制今日（{today_str}）的工作计划。

请及时登录系统，进入"计划管理"模块，点击"新建工作计划"进行编制，计划周期请选择"日计划"。

计划创建地址：{plan_create_url}

如有疑问，请联系系统管理员。

此致
敬礼！

维海科技信息化管理平台
{now.strftime('%Y年%m月%d日')}
        """.strip()
        
        html_body = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <h2 style="color: #1F2A57; border-bottom: 2px solid #1F2A57; padding-bottom: 10px;">
                日工作计划提醒
            </h2>
            <div style="line-height: 1.8; color: #333;">
                <p>尊敬的同仁：</p>
                <p>您好！</p>
                <p>根据工作计划管理制度，请在<strong style="color: #EF4444;">每天上午9点前</strong>完成当日工作计划的编制工作。</p>
                <p>本次提醒：请及时编制<strong>今日（{today_str}）</strong>的工作计划。</p>
                <p>请及时登录系统，进入"计划管理"模块，点击"新建工作计划"进行编制，<strong>计划周期请选择"日计划"</strong>。</p>
                <div style="background: #f8f9fa; padding: 15px; border-left: 4px solid #1F2A57; margin: 20px 0;">
                    <p style="margin: 0;"><strong>计划创建地址：</strong></p>
                    <p style="margin: 5px 0 0 0;"><a href="{plan_create_url}" style="color: #1F2A57; text-decoration: none;">{plan_create_url}</a></p>
                </div>
                <p>如有疑问，请联系系统管理员。</p>
                <p>此致<br>敬礼！</p>
                <p style="margin-top: 30px;">
                    <strong>维海科技信息化管理平台</strong><br>
                    {now.strftime('%Y年%m月%d日')}
                </p>
            </div>
        </div>
        """
        
        # 统计信息
        success_count = 0
        fail_count = 0
        
        # 发送通知给每个用户
        for user in users:
            user_display = user.get_full_name() or user.username
            
            if dry_run:
                self.stdout.write(f'[试运行] 将发送给: {user_display} ({user.email or "无邮箱"})')
                success_count += 1
                continue
            
            # 准备收件人列表
            to_emails = []
            to_wecom = []
            
            if user.email:
                to_emails.append(user.email)
            
            if hasattr(user, 'wecom_id') and user.wecom_id:
                to_wecom.append(user.wecom_id)
            
            if not to_emails and not to_wecom:
                self.stdout.write(self.style.WARNING(f'  跳过 {user_display}：没有邮箱和企微ID'))
                fail_count += 1
                continue
            
            # 创建通知消息
            message = NotificationMessage(
                subject=subject,
                body=body,
                html_body=html_body,
                to_emails=to_emails,
                to_wecom=to_wecom
            )
            
            # 发送通知
            email_sent = False
            wecom_sent = False
            
            if to_emails:
                try:
                    email_sent = send_email_notification(message)
                except Exception as e:
                    logger.error(f"发送邮件给 {user_display} 失败: {str(e)}")
            
            if to_wecom:
                try:
                    wecom_sent = send_wecom_notification(message)
                except Exception as e:
                    logger.error(f"发送企微通知给 {user_display} 失败: {str(e)}")
            
            if email_sent or wecom_sent:
                success_count += 1
                methods = []
                if email_sent:
                    methods.append('邮件')
                if wecom_sent:
                    methods.append('企微')
                self.stdout.write(self.style.SUCCESS(f'  ✓ {user_display}: 已通过{",".join(methods)}发送'))
            else:
                fail_count += 1
                self.stdout.write(self.style.ERROR(f'  ✗ {user_display}: 发送失败'))
        
        # 输出统计结果
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(
            f'\n提醒发送完成：'
            f'总计={users.count()}, '
            f'成功={success_count}, '
            f'失败={fail_count}'
        ))
        
        if dry_run:
            self.stdout.write(self.style.WARNING('\n这是试运行模式，未实际发送通知'))







