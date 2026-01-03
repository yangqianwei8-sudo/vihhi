"""
同步被执行记录管理命令

用法:
    python manage.py sync_execution_records --client-id <客户ID>
    python manage.py sync_execution_records --all  # 同步所有客户
    python manage.py sync_execution_records --client-id <客户ID> --dry-run  # 仅显示，不实际同步
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Sum
from backend.apps.customer_management.models import Client, ExecutionRecord
from backend.apps.customer_management.services import get_service
from datetime import datetime
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = '同步客户的被执行记录（从启信宝API）'

    def add_arguments(self, parser):
        parser.add_argument(
            '--client-id',
            type=int,
            help='要同步的客户ID'
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='同步所有客户（谨慎使用）'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='仅显示将要同步的内容，不实际执行'
        )

    def handle(self, *args, **options):
        client_id = options.get('client_id')
        sync_all = options.get('all', False)
        dry_run = options.get('dry_run', False)

        if dry_run:
            self.stdout.write(self.style.WARNING('⚠️  干运行模式：不会实际同步数据'))

        if not client_id and not sync_all:
            self.stdout.write(self.style.ERROR('请指定 --client-id 或 --all'))
            return

        try:
            qixinbao_service = get_service()
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'获取启信宝服务失败: {str(e)}'))
            return

        if client_id:
            # 同步单个客户
            try:
                client = Client.objects.get(id=client_id)
                self.sync_client(client, qixinbao_service, dry_run)
            except Client.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'客户ID {client_id} 不存在'))
        elif sync_all:
            # 同步所有客户
            clients = Client.objects.filter(is_active=True)
            total = clients.count()
            self.stdout.write(self.style.SUCCESS(f'开始同步 {total} 个客户的被执行记录...'))
            
            synced_count = 0
            failed_count = 0
            
            for i, client in enumerate(clients, 1):
                self.stdout.write(f'\n[{i}/{total}] 处理客户: {client.name} (ID: {client.id})')
                try:
                    result = self.sync_client(client, qixinbao_service, dry_run)
                    if result:
                        synced_count += 1
                    else:
                        failed_count += 1
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'  同步失败: {str(e)}'))
                    failed_count += 1
            
            self.stdout.write(self.style.SUCCESS(
                f'\n同步完成！成功: {synced_count}, 失败: {failed_count}, 总计: {total}'
            ))

    def sync_client(self, client, qixinbao_service, dry_run=False):
        """同步单个客户的被执行记录"""
        self.stdout.write(f'  客户: {client.name}')
        self.stdout.write(f'  统一信用代码: {client.unified_credit_code or "未填写"}')
        
        # 准备查询参数
        company_name = client.name
        credit_code = client.unified_credit_code
        
        if not company_name and not credit_code:
            self.stdout.write(self.style.WARNING('  跳过：客户名称和统一信用代码都为空'))
            return False
        
        # 调用启信宝API
        try:
            records = qixinbao_service.get_execution_records(
                credit_code=credit_code,
                company_name=company_name
            )
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  API调用失败: {str(e)}'))
            return False
        
        if not records:
            self.stdout.write(self.style.WARNING('  未获取到被执行记录（可能该企业没有记录，或API尚未实现）'))
            return True
        
        self.stdout.write(f'  获取到 {len(records)} 条记录')
        
        if dry_run:
            # 仅显示，不实际保存
            for i, record in enumerate(records, 1):
                self.stdout.write(f'    [{i}] 案号: {record.get("case_number", "未填写")}')
                self.stdout.write(f'        立案日期: {record.get("filing_date", "未填写")}')
                self.stdout.write(f'        执行状态: {record.get("execution_status", "未填写")}')
                self.stdout.write(f'        执行法院: {record.get("execution_court", "未填写")}')
                self.stdout.write(f'        执行金额: {record.get("execution_amount", "0")}')
            return True
        
        # 实际保存记录
        synced_count = 0
        with transaction.atomic():
            for record_data in records:
                # 检查是否已存在（根据案号判断）
                case_number = record_data.get('case_number', '').strip()
                if case_number:
                    existing = ExecutionRecord.objects.filter(
                        client=client,
                        case_number=case_number
                    ).first()
                    if existing:
                        # 更新现有记录
                        if record_data.get('filing_date'):
                            try:
                                existing.filing_date = datetime.strptime(record_data['filing_date'], '%Y-%m-%d').date()
                            except:
                                pass
                        existing.execution_status = record_data.get('execution_status', 'unknown')
                        existing.execution_court = record_data.get('execution_court', '')
                        try:
                            existing.execution_amount = Decimal(str(record_data.get('execution_amount', 0) or 0))
                        except (ValueError, TypeError):
                            existing.execution_amount = Decimal('0')
                        existing.source = 'qixinbao'
                        existing.save()
                        synced_count += 1
                        continue
                
                # 创建新记录
                filing_date = None
                if record_data.get('filing_date'):
                    try:
                        filing_date = datetime.strptime(record_data['filing_date'], '%Y-%m-%d').date()
                    except:
                        pass
                
                try:
                    execution_amount = Decimal(str(record_data.get('execution_amount', 0) or 0))
                except (ValueError, TypeError):
                    execution_amount = Decimal('0')
                
                ExecutionRecord.objects.create(
                    client=client,
                    filing_date=filing_date,
                    case_number=record_data.get('case_number', ''),
                    execution_status=record_data.get('execution_status', 'unknown'),
                    execution_court=record_data.get('execution_court', ''),
                    execution_amount=execution_amount,
                    source='qixinbao'
                )
                synced_count += 1
        
        # 更新客户的总执行金额
        client.total_execution_amount = ExecutionRecord.objects.filter(client=client).aggregate(
            total=Sum('execution_amount')
        )['total'] or Decimal('0')
        client.save()
        
        total_count = ExecutionRecord.objects.filter(client=client).count()
        self.stdout.write(self.style.SUCCESS(
            f'  ✓ 同步成功！新增/更新 {synced_count} 条记录，当前共有 {total_count} 条记录'
            f'\n  执行总金额: ¥{client.total_execution_amount}'
        ))
        return True

