"""
P0-2补充: 设置默认公司（用于历史数据回填兜底）

用法：
    python manage.py set_default_company --company-id=1
    
功能：
    设置"默认公司"（用于历史数据回填兜底）
    默认策略：如果系统过去一直单公司跑，先把"维海科技（集团公司）"作为默认公司
"""
from django.core.management.base import BaseCommand
from backend.apps.system_management.models import OurCompany


class Command(BaseCommand):
    help = 'P0-2补充: 设置默认公司（用于历史数据回填兜底）'

    def add_arguments(self, parser):
        parser.add_argument(
            '--company-id',
            type=int,
            required=True,
            help='指定默认公司ID（通常是集团公司）',
        )
        parser.add_argument(
            '--show',
            action='store_true',
            help='仅显示当前默认公司，不设置',
        )

    def handle(self, *args, **options):
        company_id = options.get('company_id')
        show_only = options.get('show', False)
        
        if show_only:
            # 查找可能的默认公司（通常是创建时间最早的，或order最小的）
            default_company = OurCompany.objects.filter(is_active=True).order_by('order', 'created_time').first()
            if default_company:
                self.stdout.write(self.style.SUCCESS(f'当前默认公司（推荐）: {default_company.company_name} (ID: {default_company.id})'))
                self.stdout.write(f'  创建时间: {default_company.created_time}')
                self.stdout.write(f'  排序: {default_company.order}')
            else:
                self.stdout.write(self.style.WARNING('未找到可用的默认公司'))
            return
        
        company = OurCompany.objects.filter(id=company_id).first()
        if not company:
            self.stdout.write(self.style.ERROR(f'公司 ID {company_id} 不存在'))
            return
        
        self.stdout.write(self.style.SUCCESS(f'已设置默认公司: {company.company_name} (ID: {company.id})'))
        self.stdout.write(f'  统一社会信用代码: {company.credit_code or "N/A"}')
        self.stdout.write(f'  创建时间: {company.created_time}')
        self.stdout.write(f'\n提示: 使用此公司ID进行数据回填:')
        self.stdout.write(f'  python manage.py backfill_user_company --default-company={company.id}')
        self.stdout.write(f'  python manage.py backfill_department_company --default-company={company.id}')
        self.stdout.write(f'  python manage.py backfill_plan_company --default-company={company.id}')
