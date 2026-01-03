"""
诉讼管理提醒发送命令
定时检查并发送开庭、保全续封、期限等提醒通知

使用方法：
    python manage.py send_litigation_reminders

建议配置为定时任务（crontab）：
    # 每天上午9点执行
    0 9 * * * cd /path/to/project && python manage.py send_litigation_reminders
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
import logging

from backend.apps.litigation_management.services import LitigationReminderService

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = '发送诉讼管理提醒通知（开庭、保全续封、期限等）'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='仅检查，不实际发送通知',
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)
        
        self.stdout.write(self.style.SUCCESS('开始检查诉讼管理提醒...'))
        
        try:
            # 检查并发送开庭提醒
            self.stdout.write('检查开庭时间提醒...')
            if not dry_run:
                LitigationReminderService.check_and_send_trial_reminders()
            self.stdout.write(self.style.SUCCESS('✓ 开庭提醒检查完成'))
            
            # 检查并发送保全续封提醒
            self.stdout.write('检查保全续封提醒...')
            if not dry_run:
                LitigationReminderService.check_and_send_preservation_reminders()
            self.stdout.write(self.style.SUCCESS('✓ 保全续封提醒检查完成'))
            
            # 检查并发送期限提醒
            self.stdout.write('检查期限提醒...')
            if not dry_run:
                LitigationReminderService.check_and_send_deadline_reminders()
            self.stdout.write(self.style.SUCCESS('✓ 期限提醒检查完成'))
            
            self.stdout.write(self.style.SUCCESS('\n所有提醒检查完成！'))
            
        except Exception as e:
            logger.exception('发送诉讼管理提醒失败')
            self.stdout.write(self.style.ERROR(f'错误：{str(e)}'))
            raise

