"""
每日通知定时任务

执行时间：每天上午9点

使用方法：
    python manage.py send_daily_notifications
    
建议配置为定时任务（crontab）：
    # 每天上午9点执行
    0 9 * * * cd /path/to/project && /path/to/venv/bin/python manage.py send_daily_notifications
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model
import logging

from backend.apps.plan_management.services.daily_notification_service import generate_daily_notification_content
from backend.apps.plan_management.notifications import safe_approval_notification

User = get_user_model()
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = '发送每日通知（昨日战报、今日战场、风险预警）'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='试运行模式：不实际发送，只显示将要发送的内容',
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)
        
        self.stdout.write(f'开始发送每日通知（时间：{timezone.now()}）...')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('【DRY RUN 模式】仅显示，不发送'))
        
        try:
            # 获取所有活跃员工
            users = User.objects.filter(is_active=True)
            
            self.stdout.write(f'找到 {users.count()} 个活跃用户')
            
            success_count = 0
            fail_count = 0
            skipped_count = 0
            
            for user in users:
                try:
                    # 生成通知内容
                    content = generate_daily_notification_content(user)
                    
                    # 如果内容为空或只有默认消息，跳过
                    if not content or content == "今日暂无通知内容。":
                        skipped_count += 1
                        continue
                    
                    if dry_run:
                        self.stdout.write(f'  [DRY RUN] 将为用户 {user.username} 发送每日通知')
                        self.stdout.write(f'    内容预览：{content[:100]}...')
                        success_count += 1
                    else:
                        # 发送系统通知
                        safe_approval_notification(
                            user=user,
                            title='【每日通知】昨日战报 & 今日战场 & 风险预警',
                            content=content,
                            object_type='notification',
                            object_id='daily',
                            event='daily_notification',
                            is_read=False
                        )
                        success_count += 1
                        self.stdout.write(self.style.SUCCESS(f'  ✓ {user.username}: 每日通知已发送'))
                        
                except Exception as e:
                    logger.error(f"为用户 {user.username} 发送每日通知失败: {str(e)}", exc_info=True)
                    fail_count += 1
                    self.stdout.write(self.style.ERROR(f'  ✗ {user.username}: {str(e)}'))
            
            self.stdout.write('')
            self.stdout.write(self.style.SUCCESS(
                f'发送完成：总计={users.count()}, 成功={success_count}, 跳过={skipped_count}, 失败={fail_count}'
            ))
            
            if dry_run:
                self.stdout.write(self.style.WARNING('\n这是试运行模式，未实际发送通知'))
            
        except Exception as e:
            logger.error(f"发送每日通知失败: {str(e)}", exc_info=True)
            self.stdout.write(self.style.ERROR(f'发送失败：{str(e)}'))
