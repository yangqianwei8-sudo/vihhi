# ==================== 客户公海检查管理命令（按《客户管理详细设计方案 v1.12》实现）====================

from django.core.management.base import BaseCommand
from backend.apps.customer_management.services import auto_move_to_public_sea


class Command(BaseCommand):
    help = '检查并自动将超过90天没有拜访信息的客户移入公海'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='仅显示将要移入公海的客户，不实际执行移入操作',
        )
    
    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)
        
        if dry_run:
            self.stdout.write(self.style.WARNING('运行在模拟模式，不会实际移入客户到公海'))
        
        try:
            if dry_run:
                # 模拟模式：只统计，不实际移入
                from django.utils import timezone
                from datetime import timedelta
                from backend.apps.customer_management.models import Client, CustomerRelationship
                
                cutoff_date = timezone.now() - timedelta(days=90)
                clients = Client.objects.filter(responsible_user__isnull=False)
                
                count = 0
                for client in clients:
                    has_recent_visit = CustomerRelationship.objects.filter(
                        client=client,
                        followup_time__gte=cutoff_date
                    ).exists()
                    
                    if not has_recent_visit:
                        count += 1
                        self.stdout.write(
                            self.style.WARNING(f'  - 客户 "{client.name}" 将被移入公海')
                        )
                
                self.stdout.write(
                    self.style.SUCCESS(f'\n模拟模式：共 {count} 个客户将被移入公海')
                )
            else:
                # 实际执行
                count = auto_move_to_public_sea()
                self.stdout.write(
                    self.style.SUCCESS(f'\n成功将 {count} 个客户移入公海')
                )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'执行失败：{str(e)}')
            )
            raise

