"""
P0-2: 用户公司字段回填脚本

用法：
    python manage.py backfill_user_company
    
功能：
    1. 输出哪些用户 company 为空（用于手工补齐）
    2. 可选：支持通过用户名/部门批量设置 company（如果部门暂时无 company，就先手工）
"""
from django.core.management.base import BaseCommand
from backend.apps.system_management.models import User, OurCompany


class Command(BaseCommand):
    help = 'P0-2: 回填用户公司字段'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='仅显示统计信息，不实际修改数据',
        )
        parser.add_argument(
            '--company-id',
            type=int,
            help='指定公司ID，用于批量设置',
        )
        parser.add_argument(
            '--default-company',
            type=int,
            help='P0-2补充: 使用默认公司（集团公司）回填所有空值',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        company_id = options.get('company_id')
        default_company_id = options.get('default_company')
        
        # 统计 company 为空的用户
        users_without_company = User.objects.filter(company__isnull=True)
        count = users_without_company.count()
        
        self.stdout.write(f'公司字段为空的用户数量: {count}')
        
        if count > 0:
            self.stdout.write('\n公司字段为空的用户列表:')
            for user in users_without_company[:50]:  # 只显示前50个
                dept_info = f'部门: {user.department.name}' if user.department else '无部门'
                self.stdout.write(f'  - {user.username} ({user.get_full_name() or "无姓名"}) - {dept_info}')
            
            if count > 50:
                self.stdout.write(f'  ... 还有 {count - 50} 个用户未显示')
        
        # P0-2补充: 优先使用 --default-company（集团公司兜底策略）
        if default_company_id:
            company = OurCompany.objects.filter(id=default_company_id).first()
            if not company:
                self.stdout.write(self.style.ERROR(f'默认公司 ID {default_company_id} 不存在'))
                return
            
            if dry_run:
                self.stdout.write(self.style.WARNING(
                    f'[DRY RUN] 将设置 {count} 个用户的 company 为默认公司: {company.company_name} (ID: {company.id})'
                ))
            else:
                updated = users_without_company.update(company=company)
                self.stdout.write(self.style.SUCCESS(
                    f'已设置 {updated} 个用户的 company 为默认公司: {company.company_name} (ID: {company.id})'
                ))
                self.stdout.write(self.style.SUCCESS('提示: 后续可在 Admin 中逐个将员工调整到各自子公司'))
        # 如果指定了 company_id，批量设置
        elif company_id:
            company = OurCompany.objects.filter(id=company_id).first()
            if not company:
                self.stdout.write(self.style.ERROR(f'公司 ID {company_id} 不存在'))
                return
            
            if dry_run:
                self.stdout.write(self.style.WARNING(f'[DRY RUN] 将设置 {count} 个用户的 company 为 {company.company_name}'))
            else:
                updated = users_without_company.update(company=company)
                self.stdout.write(self.style.SUCCESS(f'已设置 {updated} 个用户的 company 为 {company.company_name}'))
        
        if not company_id and not default_company_id and not dry_run:
            self.stdout.write('\n提示: 使用 --default-company <ID> 批量设置用户公司（推荐，使用集团公司兜底）')
            self.stdout.write('示例: python manage.py backfill_user_company --default-company=1')
            self.stdout.write('或使用 --company-id <ID> 指定特定公司')
