"""
发文自动归档管理命令

使用方法：
    python manage.py auto_archive_outgoing_documents
    
建议配置为定时任务（crontab或Celery）：
    # 每天凌晨2点执行
    0 2 * * * cd /path/to/project && python manage.py auto_archive_outgoing_documents
    
    # 或使用Celery Beat
    @periodic_task(run_every=crontab(hour=2, minute=0))
    def auto_archive_task():
        call_command('auto_archive_outgoing_documents')
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
import logging

from backend.apps.delivery_customer.services import OutgoingDocumentArchiveService

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = '自动归档符合条件的发文（已完成且已签收确认超过指定天数）'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=7,
            help='签收确认后多少天自动归档（默认7天）',
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=None,
            help='限制归档数量（用于测试）',
        )
        parser.add_argument(
            '--stats',
            action='store_true',
            help='显示归档统计信息',
        )

    def handle(self, *args, **options):
        days_after_completion = options.get('days', 7)
        limit = options.get('limit', None)
        show_stats = options.get('stats', False)
        
        self.stdout.write(f'开始自动归档发文（时间：{timezone.now()}）...')
        self.stdout.write(f'归档条件：签收确认后超过{days_after_completion}天')
        if limit:
            self.stdout.write(f'限制数量：{limit}')
        
        # 显示统计信息
        if show_stats:
            self.stdout.write('\n归档统计信息：')
            stats = OutgoingDocumentArchiveService.get_archive_statistics()
            self.stdout.write(f"  总归档数：{stats['total_archived']}")
            self.stdout.write(f"  待归档数：{stats['pending_archive']}")
            self.stdout.write(f"  归档率：{stats['archive_rate']}%")
            if stats['recent_archived']:
                self.stdout.write(f"  最近归档（最近30天）：{len(stats['recent_archived'])}个")
        
        # 执行自动归档
        result = OutgoingDocumentArchiveService.auto_archive_eligible_documents(
            days_after_completion=days_after_completion,
            limit=limit
        )
        
        # 输出结果
        self.stdout.write(self.style.SUCCESS(
            f'\n自动归档完成：'
            f'检查={result["total_checked"]}, '
            f'归档={result["archived_count"]}, '
            f'失败={result["failed_count"]}'
        ))
        
        # 输出详细信息
        if result['archived_count'] > 0:
            self.stdout.write(self.style.SUCCESS('\n已归档的发文：'))
            for detail in result['details']:
                if detail['success']:
                    self.stdout.write(
                        f"  ✓ {detail['document_number']}: {detail['message']}"
                    )
        
        if result['failed_count'] > 0:
            self.stdout.write(self.style.WARNING('\n归档失败的发文：'))
            for detail in result['details']:
                if not detail['success']:
                    self.stdout.write(
                        f"  ✗ {detail['document_number']}: {detail['message']}"
                    )

