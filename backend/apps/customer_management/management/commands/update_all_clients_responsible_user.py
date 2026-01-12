from django.core.management.base import BaseCommand
from django.db import transaction
from django.contrib.auth import get_user_model
from django.db.models import Q
from backend.apps.customer_management.models import Client

User = get_user_model()


class Command(BaseCommand):
    help = '将所有客户的负责人更新为田霞'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            default='tianxia',
            help='负责人用户名（默认：tianxia）'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='仅显示将要更新的客户数量，不实际更新'
        )
        parser.add_argument(
            '--only-null',
            action='store_true',
            help='仅更新负责人为空的客户（公海客户）'
        )

    @transaction.atomic
    def handle(self, *args, **options):
        username = options['username']
        dry_run = options['dry_run']
        only_null = options['only_null']
        
        self.stdout.write(self.style.MIGRATE_HEADING('开始更新客户负责人...'))
        
        # 查找田霞用户
        tianxia = User.objects.filter(
            Q(username=username) |
            Q(first_name='田', last_name='霞')
        ).first()
        
        if not tianxia:
            self.stdout.write(
                self.style.ERROR(f'错误：未找到用户（username: {username} 或 姓名: 田霞）')
            )
            self.stdout.write('提示：请确保用户存在，或使用 --username 参数指定正确的用户名')
            return
        
        self.stdout.write(
            self.style.SUCCESS(f'✓ 找到用户：{tianxia.get_full_name()} (username: {tianxia.username})')
        )
        
        # 获取所有客户
        all_clients = Client.objects.all()
        total_count = all_clients.count()
        
        # 根据选项确定要更新的客户
        if only_null:
            # 仅更新负责人为空的客户
            clients_to_update = all_clients.filter(responsible_user__isnull=True)
            self.stdout.write('模式：仅更新负责人为空的客户（公海客户）')
        else:
            # 更新所有负责人不是田霞的客户
            clients_to_update = all_clients.exclude(responsible_user=tianxia)
            self.stdout.write('模式：更新所有负责人不是田霞的客户')
        
        update_count = clients_to_update.count()
        
        self.stdout.write(f'总客户数：{total_count}')
        self.stdout.write(f'需要更新的客户数：{update_count}')
        
        if update_count == 0:
            self.stdout.write(self.style.SUCCESS('所有客户的负责人已经是田霞，无需更新'))
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
                    current_responsible = client.responsible_user.get_full_name() if client.responsible_user else '公海'
                    self.stdout.write(f'  - {client.name} (当前负责人: {current_responsible})')
            return
        
        # 确认操作
        self.stdout.write(self.style.WARNING(f'\n警告：将更新 {update_count} 个客户的负责人为田霞'))
        confirm = input('确定要继续吗？(yes/y/no): ')
        if confirm.lower() not in ('yes', 'y'):
            self.stdout.write('操作已取消')
            return
        
        # 批量更新
        self.stdout.write('正在更新...')
        updated = clients_to_update.update(responsible_user=tianxia)
        
        self.stdout.write(
            self.style.SUCCESS(f'\n✓ 成功更新 {updated} 个客户的负责人为田霞')
        )
        
        # 验证更新结果
        remaining = Client.objects.exclude(responsible_user=tianxia).count()
        if remaining == 0:
            self.stdout.write(
                self.style.SUCCESS('✓ 所有客户的负责人已更新为田霞')
            )
        else:
            self.stdout.write(
                self.style.WARNING(f'注意：仍有 {remaining} 个客户的负责人不是田霞')
            )

