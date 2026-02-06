"""
P0-2补充: 输出所有公司信息（用于回填与约束）

用法：
    python manage.py dump_companies
    
输出：
    所有 OurCompany：id / company_name / credit_code / is_active / created_time / order
"""
from django.core.management.base import BaseCommand
from backend.apps.system_management.models import OurCompany


class Command(BaseCommand):
    help = 'P0-2补充: 输出所有公司信息（用于回填与约束）'

    def handle(self, *args, **options):
        companies = OurCompany.objects.all().order_by('order', 'id')
        
        if not companies.exists():
            self.stdout.write(self.style.WARNING('系统中暂无公司记录'))
            return
        
        self.stdout.write(self.style.SUCCESS(f'共 {companies.count()} 家公司：\n'))
        self.stdout.write('=' * 100)
        self.stdout.write(f'{"ID":<6} | {"公司名称":<30} | {"统一社会信用代码":<25} | {"启用":<6} | {"创建时间":<20} | {"排序":<6}')
        self.stdout.write('=' * 100)
        
        for company in companies:
            status = '✓' if company.is_active else '✗'
            created_time = company.created_time.strftime('%Y-%m-%d %H:%M:%S') if company.created_time else 'N/A'
            self.stdout.write(
                f'{company.id:<6} | {company.company_name:<30} | {company.credit_code or "N/A":<25} | '
                f'{status:<6} | {created_time:<20} | {company.order:<6}'
            )
        
        self.stdout.write('=' * 100)
        self.stdout.write('\n提示: 使用这些 ID 进行数据回填，例如：')
        self.stdout.write('  python manage.py backfill_user_company --default-company=1')
