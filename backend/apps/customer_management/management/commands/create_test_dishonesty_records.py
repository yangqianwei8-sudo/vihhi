"""
创建测试被执行记录管理命令

用于测试被执行信息卡片功能

用法:
    python manage.py create_test_execution_records --client-id <客户ID>
"""
from django.core.management.base import BaseCommand
from django.db.models import Sum
from backend.apps.customer_management.models import Client, ExecutionRecord
from datetime import date, timedelta
from decimal import Decimal
import random


class Command(BaseCommand):
    help = '为指定客户创建测试被执行记录'

    def add_arguments(self, parser):
        parser.add_argument(
            '--client-id',
            type=int,
            required=True,
            help='要创建测试记录的客户ID'
        )
        parser.add_argument(
            '--count',
            type=int,
            default=3,
            help='要创建的记录数量（默认3条）'
        )

    def handle(self, *args, **options):
        client_id = options.get('client_id')
        count = options.get('count', 3)

        try:
            client = Client.objects.get(id=client_id)
        except Client.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'客户ID {client_id} 不存在'))
            return

        self.stdout.write(f'为客户 "{client.name}" 创建 {count} 条测试被执行记录...')

        courts = [
            '北京市第一中级人民法院',
            '上海市第二中级人民法院',
            '广东省深圳市中级人民法院',
            '江苏省南京市中级人民法院',
            '浙江省杭州市中级人民法院',
        ]
        
        execution_statuses = ['pending', 'executing', 'completed', 'terminated', 'unknown']

        created_count = 0
        total_amount = Decimal('0')
        for i in range(count):
            # 生成随机日期（过去1-5年）
            days_ago = random.randint(365, 1825)
            filing_date = date.today() - timedelta(days=days_ago)
            
            # 生成案号
            case_number = f'(京){random.randint(2020, 2024)}执{random.randint(1000, 9999)}号'
            
            # 生成执行金额（10万-1000万）
            execution_amount = Decimal(str(random.randint(100000, 10000000)))
            total_amount += execution_amount
            
            record = ExecutionRecord.objects.create(
                client=client,
                filing_date=filing_date,
                case_number=case_number,
                execution_status=random.choice(execution_statuses),
                execution_court=random.choice(courts),
                execution_amount=execution_amount,
                source='manual'
            )
            created_count += 1
            self.stdout.write(f'  [{i+1}/{count}] 创建记录: {case_number} - {record.execution_court} - ¥{execution_amount}')

        # 更新客户的总执行金额
        client.total_execution_amount = ExecutionRecord.objects.filter(client=client).aggregate(
            total=Sum('execution_amount')
        )['total'] or Decimal('0')
        client.save()

        total_count = ExecutionRecord.objects.filter(client=client).count()
        self.stdout.write(self.style.SUCCESS(
            f'\n✓ 成功创建 {created_count} 条测试记录！'
            f'\n  客户 "{client.name}" 当前共有 {total_count} 条被执行记录'
            f'\n  执行总金额: ¥{client.total_execution_amount}'
        ))

