"""
定时任务：自动更新发文跟踪状态
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from backend.apps.delivery_customer.models import OutgoingDocumentTracking
from backend.apps.delivery_customer.tracking_service import TrackingServiceFactory
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = '自动更新发文跟踪状态（邮件、快递等）'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=50,
            help='每次更新的记录数量限制（默认50）',
        )

    def handle(self, *args, **options):
        limit = options['limit']
        
        self.stdout.write(f'开始更新跟踪状态（限制：{limit}条）...')
        
        # 需要更新的跟踪记录
        # 1. 快递：状态为in_transit或sent的，需要查询快递100 API
        express_trackings = OutgoingDocumentTracking.objects.filter(
            delivery_method__code='express',
            status__in=['sent', 'in_transit'],
            express_number__isnull=False
        ).exclude(express_number='')[:limit]
        
        # 2. 邮件：状态为sent的，需要检查邮件读取状态（如果支持）
        email_trackings = OutgoingDocumentTracking.objects.filter(
            delivery_method__code='email',
            status='sent',
            email_message_id__isnull=False
        ).exclude(email_message_id='')[:limit]
        
        updated_count = 0
        error_count = 0
        
        # 更新快递状态
        for tracking in express_trackings:
            try:
                service = TrackingServiceFactory.get_service('express')
                success, message = service.query_express_status(tracking)
                if success:
                    updated_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'✓ 更新快递跟踪：{tracking.document.document_number} - {tracking.express_number}')
                    )
                else:
                    error_count += 1
                    self.stdout.write(
                        self.style.WARNING(f'⚠ 更新失败：{tracking.document.document_number} - {message}')
                    )
            except Exception as e:
                error_count += 1
                logger.error(f"更新快递跟踪失败 {tracking.id}: {str(e)}")
                self.stdout.write(
                    self.style.ERROR(f'✗ 更新失败：{tracking.document.document_number} - {str(e)}')
                )
        
        # 更新邮件状态（如果支持）
        for tracking in email_trackings:
            try:
                service = TrackingServiceFactory.get_service('email')
                success, message = service.check_email_status(tracking)
                if success:
                    updated_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'✓ 更新邮件跟踪：{tracking.document.document_number}')
                    )
            except Exception as e:
                logger.error(f"更新邮件跟踪失败 {tracking.id}: {str(e)}")
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n更新完成：成功 {updated_count} 条，失败 {error_count} 条'
            )
        )
