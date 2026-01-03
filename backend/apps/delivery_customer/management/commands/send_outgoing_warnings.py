"""
发文延迟预警发送管理命令

使用方法：
    python manage.py send_outgoing_warnings
    
建议配置为定时任务（crontab或Celery）：
    # 每天上午9点执行
    0 9 * * * cd /path/to/project && python manage.py send_outgoing_warnings
    
    # 或使用Celery Beat
    @periodic_task(run_every=crontab(hour=9, minute=0))
    def send_warnings_task():
        call_command('send_outgoing_warnings')
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
import logging

from backend.apps.delivery_customer.services import OutgoingDocumentWarningService

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = '发送发文延迟预警通知'

    def add_arguments(self, parser):
        parser.add_argument(
            '--min-delay',
            type=int,
            default=1,
            help='最小延迟天数（小于此天数不发送预警，默认1天）',
        )
        parser.add_argument(
            '--max-delay',
            type=int,
            default=None,
            help='最大延迟天数（用于筛选，默认不限制）',
        )

    def handle(self, *args, **options):
        min_delay_days = options.get('min_delay', 1)
        max_delay_days = options.get('max_delay', None)
        
        self.stdout.write(f'开始发送发文延迟预警（时间：{timezone.now()}）...')
        self.stdout.write(f'最小延迟天数：{min_delay_days}天')
        if max_delay_days:
            self.stdout.write(f'最大延迟天数：{max_delay_days}天')
        
        # 发送预警
        result = OutgoingDocumentWarningService.check_and_send_warnings(
            min_delay_days=min_delay_days,
            max_delay_days=max_delay_days
        )
        
        # 输出结果
        self.stdout.write(self.style.SUCCESS(
            f'\n预警发送完成：'
            f'检查={result["total_checked"]}, '
            f'已发送={result["warnings_sent"]}, '
            f'已预警={result["already_warned"]}'
        ))
        
        # 输出详细信息
        if result['warnings_sent'] > 0:
            self.stdout.write(self.style.SUCCESS('\n已发送的预警：'))
            for detail in result['details']:
                if detail['success']:
                    self.stdout.write(
                        f"  ✓ {detail['document_number']}: 延迟{detail['delay_days']}天 - {detail['message']}"
                    )
        
        if result['already_warned'] > 0:
            self.stdout.write(self.style.WARNING('\n已预警或发送失败的：'))
            for detail in result['details']:
                if not detail['success']:
                    self.stdout.write(
                        f"  ⚠ {detail['document_number']}: {detail['message']}"
                    )

