from django.core.management.base import BaseCommand
from django.db import transaction
from backend.apps.customer_management.models import Client
from backend.apps.customer_management.services import get_service
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = '批量填充所有客户的联系电话和邮箱（从启信宝API获取）'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='仅显示将要更新的客户数量，不实际更新'
        )
        parser.add_argument(
            '--only-empty',
            action='store_true',
            help='仅填充字段为空的客户'
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=50,
            help='每批处理的客户数量（默认：50）'
        )
        parser.add_argument(
            '--fields',
            type=str,
            default='phone,email',
            help='要填充的字段，用逗号分隔（默认：phone,email，可选：address,phone,email）'
        )

    @transaction.atomic
    def handle(self, *args, **options):
        dry_run = options['dry_run']
        only_empty = options['only_empty']
        batch_size = options['batch_size']
        fields_str = options['fields']
        
        # 解析要填充的字段
        fields_to_fill = [f.strip() for f in fields_str.split(',')]
        fill_address = 'address' in fields_to_fill
        fill_phone = 'phone' in fields_to_fill
        fill_email = 'email' in fields_to_fill
        
        self.stdout.write(self.style.MIGRATE_HEADING('开始批量填充客户信息...'))
        self.stdout.write(f'将填充字段：{", ".join(fields_to_fill)}')
        
        # 获取启信宝服务
        try:
            qixinbao_service = get_service()
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'获取启信宝服务失败: {str(e)}')
            )
            return
        
        # 检查API配置
        if not qixinbao_service.app_key or not qixinbao_service.app_secret:
            self.stdout.write(
                self.style.ERROR('启信宝API未配置，请联系管理员配置')
            )
            return
        
        # 获取所有客户
        if only_empty:
            # 仅填充所有字段都为空的客户
            from django.db.models import Q
            query = Q()
            if fill_address:
                query |= Q(company_address='')
            if fill_phone:
                query |= Q(company_phone='')
            if fill_email:
                query |= Q(company_email='')
            clients = Client.objects.filter(query).order_by('id')
            self.stdout.write('模式：仅填充字段为空的客户')
        else:
            clients = Client.objects.all().order_by('id')
            self.stdout.write('模式：填充所有客户（已有字段将被跳过）')
        
        total_count = clients.count()
        
        if total_count == 0:
            self.stdout.write(
                self.style.SUCCESS('没有需要处理的客户')
            )
            return
        
        self.stdout.write(f'总客户数：{total_count}')
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('这是模拟运行（--dry-run），不会实际更新数据')
            )
            # 显示一些示例客户
            sample_clients = clients[:5]
            if sample_clients:
                self.stdout.write('\n示例客户（前5个）：')
                for client in sample_clients:
                    info_parts = []
                    if fill_address:
                        addr = client.company_address if client.company_address else '未设置'
                        info_parts.append(f'地址: {addr}')
                    if fill_phone:
                        phone = client.company_phone if client.company_phone else '未设置'
                        info_parts.append(f'电话: {phone}')
                    if fill_email:
                        email = client.company_email if client.company_email else '未设置'
                        info_parts.append(f'邮箱: {email}')
                    self.stdout.write(f'  - {client.name} ({", ".join(info_parts)})')
            return
        
        # 确认操作
        self.stdout.write(
            self.style.WARNING(f'\n警告：将处理 {total_count} 个客户的信息')
        )
        confirm = input('确定要继续吗？(yes/y/no): ')
        if confirm.lower() not in ('yes', 'y'):
            self.stdout.write('操作已取消')
            return
        
        # 批量处理
        self.stdout.write('开始处理...')
        success_count = 0
        failed_count = 0
        skipped_count = 0
        failed_clients = []
        updated_fields_count = {'address': 0, 'phone': 0, 'email': 0}
        
        # 分批处理，避免内存问题
        for i in range(0, total_count, batch_size):
            batch_clients = clients[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (total_count + batch_size - 1) // batch_size
            
            self.stdout.write(f'\n处理第 {batch_num}/{total_batches} 批（{len(batch_clients)} 个客户）...')
            
            for client in batch_clients:
                try:
                    # 检查是否需要跳过（如果不是只处理空字段，且所有要填充的字段都已存在）
                    if not only_empty:
                        should_skip = True
                        if fill_address and not client.company_address:
                            should_skip = False
                        if fill_phone and not client.company_phone:
                            should_skip = False
                        if fill_email and not client.company_email:
                            should_skip = False
                        if should_skip:
                            skipped_count += 1
                            continue
                    
                    # 检查客户名称
                    if not client.name or len(client.name.strip()) < 2:
                        failed_count += 1
                        failed_clients.append({'name': client.name or '未知', 'reason': '客户名称为空或过短'})
                        continue
                    
                    # 优先使用统一信用代码查询（更准确）
                    company_info = None
                    if client.unified_credit_code:
                        # 如果有统一信用代码，使用信用代码查询
                        company_info = qixinbao_service.get_company_detail(
                            credit_code=client.unified_credit_code,
                            company_name=client.name.strip()
                        )
                    else:
                        # 如果没有统一信用代码，使用公司名称查询
                        company_info = qixinbao_service.get_company_info_by_name(client.name.strip())
                    
                    if not company_info:
                        failed_count += 1
                        failed_clients.append({'name': client.name, 'reason': '启信宝API未找到匹配的企业信息'})
                        continue
                    
                    # 更新字段
                    updated_fields = []
                    fields_to_save = []
                    has_update = False
                    
                    # 更新注册地址
                    if fill_address and company_info.get('address') and not client.company_address:
                        client.company_address = company_info.get('address', '')
                        updated_fields.append('注册地址')
                        fields_to_save.append('company_address')
                        updated_fields_count['address'] += 1
                        has_update = True
                    
                    # 更新联系电话
                    if fill_phone and company_info.get('phone') and not client.company_phone:
                        client.company_phone = company_info.get('phone', '')
                        updated_fields.append('联系电话')
                        fields_to_save.append('company_phone')
                        updated_fields_count['phone'] += 1
                        has_update = True
                    
                    # 更新邮箱
                    if fill_email and company_info.get('email') and not client.company_email:
                        client.company_email = company_info.get('email', '')
                        updated_fields.append('邮箱')
                        fields_to_save.append('company_email')
                        updated_fields_count['email'] += 1
                        has_update = True
                    
                    # 保存更新
                    if has_update:
                        client.save(update_fields=fields_to_save)
                        success_count += 1
                        if success_count % 10 == 0:
                            self.stdout.write(f'  已成功填充 {success_count} 个客户的信息...')
                    else:
                        skipped_count += 1
                        # 如果所有要填充的字段都已存在，跳过
                        
                except Exception as e:
                    logger.exception(f'处理客户 {client.name} 失败: {str(e)}')
                    failed_count += 1
                    failed_clients.append({'name': client.name, 'reason': f'处理失败: {str(e)}'})
        
        # 显示结果
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(self.style.SUCCESS(f'\n✓ 处理完成！'))
        self.stdout.write(f'总客户数：{total_count}')
        self.stdout.write(self.style.SUCCESS(f'✓ 成功：{success_count} 个'))
        
        # 显示各字段更新统计
        if fill_address and updated_fields_count['address'] > 0:
            self.stdout.write(f'  - 注册地址：{updated_fields_count["address"]} 个')
        if fill_phone and updated_fields_count['phone'] > 0:
            self.stdout.write(f'  - 联系电话：{updated_fields_count["phone"]} 个')
        if fill_email and updated_fields_count['email'] > 0:
            self.stdout.write(f'  - 邮箱：{updated_fields_count["email"]} 个')
        
        if skipped_count > 0:
            self.stdout.write(self.style.WARNING(f'○ 跳过：{skipped_count} 个（字段已存在）'))
        if failed_count > 0:
            self.stdout.write(self.style.ERROR(f'✗ 失败：{failed_count} 个'))
            if failed_clients:
                self.stdout.write('\n失败详情（前10个）：')
                for item in failed_clients[:10]:
                    self.stdout.write(f'  - {item["name"]}: {item["reason"]}')
                if len(failed_clients) > 10:
                    self.stdout.write(f'  ... 还有 {len(failed_clients) - 10} 个失败')
        
        self.stdout.write('\n' + '=' * 60)

