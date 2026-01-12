from django.core.management.base import BaseCommand
from django.db import transaction
from backend.apps.customer_management.models import Client


class Command(BaseCommand):
    help = '将所有客户的来源更新为"老客户推荐"'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='仅显示将要更新的客户数量，不实际更新'
        )
        parser.add_argument(
            '--only-empty',
            action='store_true',
            help='仅更新来源为空的客户'
        )

    @transaction.atomic
    def handle(self, *args, **options):
        dry_run = options['dry_run']
        only_empty = options['only_empty']
        
        # 客户来源值：老客户推荐
        source_value = 'customer_referral'
        source_display = '老客户推荐'
        
        self.stdout.write(self.style.MIGRATE_HEADING('开始更新客户来源...'))
        
        # 获取所有客户
        all_clients = Client.objects.all()
        total_count = all_clients.count()
        
        # 根据选项确定要更新的客户
        if only_empty:
            # 仅更新来源为空的客户
            clients_to_update = all_clients.filter(source='')
            self.stdout.write('模式：仅更新来源为空的客户')
        else:
            # 更新所有来源不是"老客户推荐"的客户
            clients_to_update = all_clients.exclude(source=source_value)
            self.stdout.write('模式：更新所有来源不是"老客户推荐"的客户')
        
        update_count = clients_to_update.count()
        
        self.stdout.write(f'总客户数：{total_count}')
        self.stdout.write(f'需要更新的客户数：{update_count}')
        
        if update_count == 0:
            self.stdout.write(
                self.style.SUCCESS(f'所有客户的来源已经是"{source_display}"，无需更新')
            )
            return
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('这是模拟运行（--dry-run），不会实际更新数据')
            )
            # 显示一些示例客户
            sample_clients = clients_to_update[:5]
            if sample_clients:
                self.stdout.write('\n示例客户（前5个）：')
                for client in sample_clients:
                    current_source = client.get_source_display() if client.source else '未设置'
                    self.stdout.write(f'  - {client.name} (当前来源: {current_source})')
            return
        
        # 确认操作
        self.stdout.write(
            self.style.WARNING(f'\n警告：将更新 {update_count} 个客户的来源为"{source_display}"')
        )
        confirm = input('确定要继续吗？(yes/y/no): ')
        if confirm.lower() not in ('yes', 'y'):
            self.stdout.write('操作已取消')
            return
        
        # 批量更新
        self.stdout.write('正在更新...')
        updated = clients_to_update.update(source=source_value)
        
        self.stdout.write(
            self.style.SUCCESS(f'\n✓ 成功更新 {updated} 个客户的来源为"{source_display}"')
        )
        
        # 验证更新结果
        remaining = Client.objects.exclude(source=source_value).count()
        if remaining == 0:
            self.stdout.write(
                self.style.SUCCESS(f'✓ 所有客户的来源已更新为"{source_display}"')
            )
        else:
            self.stdout.write(
                self.style.WARNING(f'注意：仍有 {remaining} 个客户的来源不是"{source_display}"')
            )

