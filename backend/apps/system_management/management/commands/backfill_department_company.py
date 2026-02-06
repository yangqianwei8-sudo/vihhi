"""
P0-3: 部门公司字段回填脚本

用法：
    python manage.py backfill_department_company --default-company=1
    
功能：
    因为现有部门无法推断所属子公司：先全填集团公司
    后续在 admin 里把各子公司部门逐步调整（允许把"财务部/人事部"等复制到各子公司）
"""
from django.core.management.base import BaseCommand
from backend.apps.system_management.models import Department, OurCompany


class Command(BaseCommand):
    help = 'P0-3: 回填部门公司字段'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='仅显示统计信息，不实际修改数据',
        )
        parser.add_argument(
            '--default-company',
            type=int,
            required=True,
            help='默认公司ID（通常是集团公司），用于回填所有空值',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        default_company_id = options.get('default_company')
        
        company = OurCompany.objects.filter(id=default_company_id).first()
        if not company:
            self.stdout.write(self.style.ERROR(f'默认公司 ID {default_company_id} 不存在'))
            return
        
        # 统计 company 为空的部门
        depts_without_company = Department.objects.filter(company__isnull=True)
        count = depts_without_company.count()
        
        self.stdout.write(f'公司字段为空的部门数量: {count}')
        
        if count > 0:
            self.stdout.write('\n公司字段为空的部门列表:')
            for dept in depts_without_company[:50]:  # 只显示前50个
                parent_info = f'上级: {dept.parent.name}' if dept.parent else '无上级'
                self.stdout.write(f'  - {dept.name} (code: {dept.code}) - {parent_info}')
            
            if count > 50:
                self.stdout.write(f'  ... 还有 {count - 50} 个部门未显示')
        
        if dry_run:
            self.stdout.write(self.style.WARNING(
                f'[DRY RUN] 将设置 {count} 个部门的 company 为默认公司: {company.company_name} (ID: {company.id})'
            ))
        else:
            updated = depts_without_company.update(company=company)
            self.stdout.write(self.style.SUCCESS(
                f'已设置 {updated} 个部门的 company 为默认公司: {company.company_name} (ID: {company.id})'
            ))
            self.stdout.write(self.style.SUCCESS('提示: 后续可在 Admin 中逐步将各子公司部门调整到各自公司'))
