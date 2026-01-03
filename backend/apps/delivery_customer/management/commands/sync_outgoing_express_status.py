"""
发文快递状态同步管理命令

使用方法：
    python manage.py sync_outgoing_express_status
    
建议配置为定时任务（crontab或Celery）：
    # 每30分钟执行一次
    */30 * * * * cd /path/to/project && python manage.py sync_outgoing_express_status
    
    # 或使用Celery Beat
    @periodic_task(run_every=crontab(minute='*/30'))
    def sync_express_status_task():
        call_command('sync_outgoing_express_status')
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
import logging

from backend.apps.delivery_customer.services import OutgoingDocumentExpressSyncService

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = '同步发文快递状态（查询快递100等API更新快递状态）'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=None,
            help='限制同步数量（用于测试）',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='强制更新（即使最近已更新过）',
        )
        parser.add_argument(
            '--check-delayed',
            action='store_true',
            help='同时检查并标记延迟的发文',
        )

    def handle(self, *args, **options):
        limit = options.get('limit')
        force = options.get('force', False)
        check_delayed = options.get('check_delayed', False)
        
        self.stdout.write(f'开始同步发文快递状态（时间：{timezone.now()}）...')
        
        # 同步快递状态
        result = OutgoingDocumentExpressSyncService.sync_all_pending_documents(
            limit=limit,
            force_update=force
        )
        
        # 输出结果
        self.stdout.write(self.style.SUCCESS(
            f'\n同步完成：'
            f'总数={result["total"]}, '
            f'成功={result["success"]}, '
            f'失败={result["failed"]}, '
            f'跳过={result["skipped"]}'
        ))
        
        # 输出详细信息
        if result['failed'] > 0:
            self.stdout.write(self.style.WARNING('\n失败的同步：'))
            for detail in result['details']:
                if not detail['success'] and '跳过' not in detail['message']:
                    self.stdout.write(
                        f"  - {detail['document_number']}: {detail['message']}"
                    )
        
        # 检查延迟的发文
        if check_delayed:
            self.stdout.write('\n检查延迟的发文...')
            delayed_result = OutgoingDocumentExpressSyncService.check_delayed_documents()
            
            self.stdout.write(self.style.WARNING(
                f'延迟检查完成：检查={delayed_result["total_checked"]}, '
                f'延迟={delayed_result["delayed_count"]}'
            ))
            
            if delayed_result['delayed_documents']:
                self.stdout.write('\n延迟的发文：')
                for doc in delayed_result['delayed_documents']:
                    self.stdout.write(
                        f"  - {doc['document_number']}: 延迟{doc['delay_days']}天"
                    )

