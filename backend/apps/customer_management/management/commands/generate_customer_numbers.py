from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Q
from backend.apps.customer_management.models import Client
from datetime import date
import re


class Command(BaseCommand):
    help = '为所有没有客户编号的客户批量生成编号（格式：KH-YYYYMMDD-NNNN）'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='仅预览，不实际生成编号',
        )
        parser.add_argument(
            '--date',
            type=str,
            help='指定日期（格式：YYYYMMDD），默认使用今天',
        )
    
    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)
        date_str = options.get('date')
        
        # 确定日期
        if date_str:
            try:
                today = date(int(date_str[:4]), int(date_str[4:6]), int(date_str[6:8]))
            except (ValueError, IndexError):
                self.stdout.write(self.style.ERROR(f'日期格式错误：{date_str}，应使用 YYYYMMDD 格式'))
                return
        else:
            today = date.today()
        
        date_prefix = today.strftime('%Y%m%d')
        prefix = f'KH-{date_prefix}-'
        
        # 查找所有没有客户编号的客户
        clients_without_number = Client.objects.filter(
            Q(customer_number__isnull=True) | 
            Q(customer_number='')
        ).order_by('id')
        
        count = clients_without_number.count()
        
        if count == 0:
            self.stdout.write(self.style.SUCCESS('所有客户都已拥有客户编号！'))
            return
        
        self.stdout.write(f'找到 {count} 个没有客户编号的客户')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('=== 预览模式（不会实际生成编号）==='))
        
        # 使用数据库事务确保一致性
        with transaction.atomic():
            # 查询所有以KH-开头的客户编号，获取最大的序号
            all_numbers = Client.objects.filter(
                customer_number__isnull=False
            ).exclude(customer_number='').filter(
                customer_number__startswith='KH-'
            ).select_for_update().values_list('customer_number', flat=True)
            
            max_num = 0
            # 从所有编号中提取序号部分（最后4位数字）
            for number in all_numbers:
                if number and '-' in number:
                    try:
                        # 提取最后一个-后面的数字部分
                        num_part = number.split('-')[-1]
                        if re.match(r'^\d{1,4}$', num_part):  # 确保是1-4位数字
                            num_value = int(num_part)
                            if num_value > max_num:
                                max_num = num_value
                    except (ValueError, IndexError):
                        continue
            
            # 下一个序号
            next_num = max_num + 1
            
            # 检查是否会超过最大值
            if next_num + count - 1 > 9999:
                self.stdout.write(self.style.ERROR(
                    f'错误：生成 {count} 个编号后，序号将超过最大值9999（当前最大序号：{max_num}）'
                ))
                return
            
            # 批量生成编号
            updated_count = 0
            for client in clients_without_number:
                customer_number = f'{prefix}{str(next_num).zfill(4)}'
                
                # 再次检查是否已存在（防止并发冲突）
                attempt_count = 0
                while Client.objects.filter(customer_number=customer_number).exists() and attempt_count < 100:
                    next_num += 1
                    if next_num > 9999:
                        self.stdout.write(self.style.ERROR(
                            f'错误：客户 {client.id} ({client.name}) 无法生成编号，已达到最大值9999'
                        ))
                        break
                    customer_number = f'{prefix}{str(next_num).zfill(4)}'
                    attempt_count += 1
                
                if attempt_count >= 100:
                    self.stdout.write(self.style.ERROR(
                        f'错误：客户 {client.id} ({client.name}) 无法生成唯一编号，已尝试100次'
                    ))
                    continue
                
                if dry_run:
                    self.stdout.write(f'  [{client.id}] {client.name} -> {customer_number}')
                else:
                    client.customer_number = customer_number
                    client.save(update_fields=['customer_number'])
                    self.stdout.write(self.style.SUCCESS(
                        f'✓ [{client.id}] {client.name} -> {customer_number}'
                    ))
                
                updated_count += 1
                next_num += 1
            
            if not dry_run:
                self.stdout.write(self.style.SUCCESS(
                    f'\n成功为 {updated_count} 个客户生成了编号！'
                ))
                self.stdout.write(f'编号范围：{prefix}{str(max_num + 1).zfill(4)} - {prefix}{str(next_num - 1).zfill(4)}')
            else:
                self.stdout.write(self.style.WARNING(
                    f'\n预览完成：将为 {updated_count} 个客户生成编号'
                ))
                self.stdout.write(f'编号范围：{prefix}{str(max_num + 1).zfill(4)} - {prefix}{str(next_num - 1).zfill(4)}')
                self.stdout.write(self.style.WARNING('使用 --dry-run=false 或直接运行命令来实际生成编号'))
