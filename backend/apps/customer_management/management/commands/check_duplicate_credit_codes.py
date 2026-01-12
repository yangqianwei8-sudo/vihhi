from django.core.management.base import BaseCommand
from django.db.models import Count
from backend.apps.customer_management.models import Client


class Command(BaseCommand):
    help = '检查重复的统一信用代码'

    def add_arguments(self, parser):
        parser.add_argument(
            '--fix',
            action='store_true',
            help='自动修复重复数据（保留ID最小的客户，删除其他重复客户）'
        )

    def handle(self, *args, **options):
        fix_mode = options['fix']
        
        self.stdout.write(self.style.MIGRATE_HEADING('检查重复的统一信用代码...'))
        
        # 查找重复的统一信用代码
        duplicates = Client.objects.values('unified_credit_code').annotate(
            count=Count('unified_credit_code')
        ).filter(
            count__gt=1,
            unified_credit_code__isnull=False
        ).exclude(unified_credit_code='').order_by('-count')
        
        if not duplicates.exists():
            self.stdout.write(self.style.SUCCESS('✓ 未发现重复的统一信用代码'))
            return
        
        self.stdout.write(self.style.WARNING(f'\n发现 {duplicates.count()} 个重复的统一信用代码\n'))
        
        total_duplicates = 0
        to_delete = []
        
        for dup in duplicates:
            credit_code = dup['unified_credit_code']
            count = dup['count']
            total_duplicates += (count - 1)  # 每个重复组保留1个，删除其他
            
            self.stdout.write(f'统一信用代码: {credit_code}')
            self.stdout.write(f'  重复 {count} 次:')
            
            clients = Client.objects.filter(unified_credit_code=credit_code).order_by('id')
            keep_client = clients.first()  # 保留ID最小的客户
            
            for client in clients:
                marker = '✓ 保留' if client.id == keep_client.id else '✗ 将删除'
                self.stdout.write(f'    {marker} - ID {client.id}: {client.name}')
                if client.id != keep_client.id:
                    to_delete.append(client)
            
            self.stdout.write('')
        
        if not fix_mode:
            self.stdout.write(self.style.WARNING(f'\n共需要删除 {len(to_delete)} 个重复客户'))
            self.stdout.write('提示：使用 --fix 参数可以自动修复（保留ID最小的客户，删除其他）')
            return
        
        # 修复模式
        if not to_delete:
            self.stdout.write(self.style.SUCCESS('没有需要删除的重复客户'))
            return
        
        self.stdout.write(self.style.WARNING(f'\n警告：将删除 {len(to_delete)} 个重复客户'))
        confirm = input('确定要继续吗？(yes/y/no): ')
        if confirm.lower() not in ('yes', 'y'):
            self.stdout.write('操作已取消')
            return
        
        # 删除重复客户
        deleted_count = 0
        for client in to_delete:
            try:
                client_name = client.name
                client.delete()
                deleted_count += 1
                self.stdout.write(f'  已删除: ID {client.id} - {client_name}')
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'  删除失败: ID {client.id} - {client.name} - {str(e)}')
                )
        
        self.stdout.write(self.style.SUCCESS(f'\n✓ 成功删除 {deleted_count} 个重复客户'))

