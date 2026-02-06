"""
P0-5补充: 计划公司字段回填脚本

用法：
    python manage.py backfill_plan_company --default-company=1
    
功能：
    所有 company 为空的 Plan → 填默认公司（集团公司）
    优先保证系统不崩，再逐步精细化
"""
from django.core.management.base import BaseCommand
from backend.apps.plan_management.models import Plan
from backend.apps.system_management.models import OurCompany


class Command(BaseCommand):
    help = 'P0-5补充: 回填计划公司字段'

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
        
        # 统计 company 为空的计划
        plans_without_company = Plan.objects.filter(company__isnull=True)
        count = plans_without_company.count()
        
        self.stdout.write(f'公司字段为空的计划数量: {count}')
        
        if count > 0:
            self.stdout.write('\n公司字段为空的计划列表（前20个）:')
            for plan in plans_without_company[:20]:
                owner_info = f'负责人: {plan.responsible_person.username}' if plan.responsible_person else '无负责人'
                self.stdout.write(f'  - {plan.plan_number} - {plan.name} - {owner_info}')
            
            if count > 20:
                self.stdout.write(f'  ... 还有 {count - 20} 个计划未显示')
        
        if dry_run:
            self.stdout.write(self.style.WARNING(
                f'[DRY RUN] 将设置 {count} 个计划的 company 为默认公司: {company.company_name} (ID: {company.id})'
            ))
        else:
            updated = plans_without_company.update(company=company)
            self.stdout.write(self.style.SUCCESS(
                f'已设置 {updated} 个计划的 company 为默认公司: {company.company_name} (ID: {company.id})'
            ))
            self.stdout.write(self.style.SUCCESS('提示: 后续可根据实际情况调整计划的 company 归属'))
