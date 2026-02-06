"""
P0-4: 角色公司字段回填脚本

用法：
    python manage.py backfill_role_company
    
功能：
    现有 Role 默认设为 company=NULL（全局角色）
    只有明确要"子公司独立的角色"时，才创建 company=某子公司的 role
"""
from django.core.management.base import BaseCommand
from backend.apps.system_management.models import Role


class Command(BaseCommand):
    help = 'P0-4: 回填角色公司字段（设为全局角色）'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='仅显示统计信息，不实际修改数据',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        # 统计所有角色（company 可能为空或已设置）
        all_roles = Role.objects.all()
        roles_with_null_company = all_roles.filter(company__isnull=True)
        roles_with_company = all_roles.filter(company__isnull=False)
        
        self.stdout.write(f'总角色数: {all_roles.count()}')
        self.stdout.write(f'  全局角色 (company=NULL): {roles_with_null_company.count()}')
        self.stdout.write(f'  公司角色 (company已设置): {roles_with_company.count()}')
        
        if roles_with_null_company.exists():
            self.stdout.write('\n全局角色列表:')
            for role in roles_with_null_company[:50]:
                self.stdout.write(f'  - {role.name} (code: {role.code})')
            
            if roles_with_null_company.count() > 50:
                self.stdout.write(f'  ... 还有 {roles_with_null_company.count() - 50} 个角色未显示')
        
        if roles_with_company.exists():
            self.stdout.write('\n公司角色列表:')
            for role in roles_with_company[:20]:
                company_name = role.company.company_name if role.company else 'N/A'
                self.stdout.write(f'  - {role.name} (code: {role.code}) - 公司: {company_name}')
        
        self.stdout.write('\n提示: 现有角色保持 company=NULL（全局角色）')
        self.stdout.write('如需创建子公司独立角色，请在 Admin 中创建新角色并指定 company')
