from django.core.management.base import BaseCommand
from django.db.models import Q
from backend.apps.customer_management.models import Client, ClientContact


class Command(BaseCommand):
    help = '删除所有没有统一信用代码的客户'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='仅显示将要删除的客户，不实际删除',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='强制删除，即使有关联关系也删除（危险操作）',
        )
    
    def handle(self, *args, **options):
        dry_run = options['dry_run']
        force = options['force']
        
        self.stdout.write('开始查找没有统一信用代码的客户...')
        
        # 查找所有没有统一信用代码的客户
        # unified_credit_code 为空字符串或 None 的客户
        clients_without_credit_code = Client.objects.filter(
            Q(unified_credit_code='') | Q(unified_credit_code__isnull=True)
        )
        
        total_count = clients_without_credit_code.count()
        
        if total_count == 0:
            self.stdout.write(self.style.SUCCESS('✓ 没有找到没有统一信用代码的客户'))
            return
        
        self.stdout.write(self.style.WARNING(f'找到 {total_count} 个没有统一信用代码的客户'))
        
        if dry_run:
            self.stdout.write(self.style.WARNING('\n[DRY RUN模式] 以下客户将被删除：'))
        else:
            self.stdout.write(self.style.WARNING('\n开始删除客户...'))
        
        deleted_count = 0
        skipped_count = 0
        failed_count = 0
        skipped_clients = []
        
        for client in clients_without_credit_code:
            # 检查关联关系
            has_relations = False
            relation_details = []
            
            # 检查项目关联
            try:
                from backend.apps.production_management.models import Project
                project_count = Project.objects.filter(client=client).count()
                if project_count > 0:
                    has_relations = True
                    relation_details.append(f'{project_count} 个项目')
            except Exception:
                pass
            
            # 检查商机关联
            try:
                from backend.apps.customer_management.models import BusinessOpportunity
                opportunity_count = BusinessOpportunity.objects.filter(client=client).count()
                if opportunity_count > 0:
                    has_relations = True
                    relation_details.append(f'{opportunity_count} 个商机')
            except Exception:
                pass
            
            # 检查合同关联
            try:
                from backend.apps.production_management.models import BusinessContract
                contract_count = BusinessContract.objects.filter(client=client).count()
                if contract_count > 0:
                    has_relations = True
                    relation_details.append(f'{contract_count} 个合同')
            except Exception:
                pass
            
            # 检查联系人关联
            try:
                contact_count = ClientContact.objects.filter(client=client).count()
                if contact_count > 0:
                    has_relations = True
                    relation_details.append(f'{contact_count} 个联系人')
            except Exception:
                pass
            
            # 如果有关联关系且不是强制模式，跳过删除
            if has_relations and not force:
                skipped_count += 1
                relation_info = '、'.join(relation_details)
                skipped_clients.append({
                    'name': client.name,
                    'id': client.id,
                    'relations': relation_info
                })
                if dry_run:
                    self.stdout.write(
                        self.style.WARNING(
                            f'  ⚠ 跳过: {client.name} (ID: {client.id}) - 关联了 {relation_info}'
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(
                            f'  ⚠ 跳过: {client.name} (ID: {client.id}) - 关联了 {relation_info}'
                        )
                    )
                continue
            
            # 执行删除
            if not dry_run:
                try:
                    client.delete()
                    deleted_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'  ✓ 已删除: {client.name} (ID: {client.id})')
                    )
                except Exception as e:
                    failed_count += 1
                    self.stdout.write(
                        self.style.ERROR(f'  ✗ 删除失败: {client.name} (ID: {client.id}) - {str(e)}')
                    )
            else:
                deleted_count += 1
                relation_info = f' (关联了 {", ".join(relation_details)})' if has_relations else ''
                self.stdout.write(
                    self.style.WARNING(f'  - {client.name} (ID: {client.id}){relation_info}')
                )
        
        # 显示统计信息
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('删除操作完成！'))
        self.stdout.write('='*60)
        
        if dry_run:
            self.stdout.write(f'[DRY RUN模式] 预计删除: {deleted_count} 个客户')
            if skipped_count > 0:
                self.stdout.write(f'预计跳过: {skipped_count} 个客户（有关联关系）')
        else:
            self.stdout.write(f'成功删除: {deleted_count} 个客户')
            if skipped_count > 0:
                self.stdout.write(f'跳过删除: {skipped_count} 个客户（有关联关系）')
            if failed_count > 0:
                self.stdout.write(self.style.ERROR(f'删除失败: {failed_count} 个客户'))
        
        if skipped_count > 0 and not force:
            self.stdout.write('\n跳过的客户详情：')
            for client_info in skipped_clients:
                self.stdout.write(
                    f'  - {client_info["name"]} (ID: {client_info["id"]}) - 关联了 {client_info["relations"]}'
                )
            self.stdout.write(
                self.style.WARNING(
                    '\n提示: 使用 --force 参数可以强制删除有关联关系的客户（危险操作）'
                )
            )

