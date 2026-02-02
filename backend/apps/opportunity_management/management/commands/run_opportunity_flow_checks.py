"""
在开发库上执行商机 8 项流程验证：自动补齐测试数据并运行全部检查。
"""
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


class Command(BaseCommand):
    help = '商机 8 项流程验证：若无商机则创建一条测试数据后执行全部检查'

    def add_arguments(self, parser):
        parser.add_argument(
            '--no-seed',
            action='store_true',
            help='不自动创建测试商机，无数据时直接跳过',
        )

    def handle(self, *args, **options):
        from backend.apps.customer_management.models import Client
        from backend.apps.opportunity_management.models import BusinessOpportunity
        from backend.apps.opportunity_management.tests.run_flow_checks import run as run_checks

        no_seed = options.get('no_seed', False)
        created_opp = None

        user = User.objects.filter(is_active=True).first()
        if not user:
            self.stdout.write(self.style.ERROR('无活跃用户，无法执行'))
            return
        client = Client.objects.filter(is_active=True).first()
        if not client:
            self.stdout.write(self.style.ERROR('无活跃客户，无法执行'))
            return
        opp = BusinessOpportunity.objects.filter(is_active=True).first()
        if not opp and not no_seed:
            prefix = f'SJ-{timezone.now().strftime("%Y%m%d")}-'
            from django.db.models import Max
            last_num = BusinessOpportunity.objects.filter(
                opportunity_number__startswith=prefix
            ).aggregate(m=Max('opportunity_number'))['m']
            seq = 1
            if last_num:
                try:
                    seq = int(last_num.split('-')[-1]) + 1
                except (ValueError, IndexError, TypeError):
                    pass
            opp = BusinessOpportunity.objects.create(
                opportunity_number=f'{prefix}{seq:04d}',
                name='流程验证用商机',
                client=client,
                business_manager=user,
                created_by=user,
                status='potential',
                estimated_amount=Decimal('100'),
                success_probability=10,
                weighted_amount=Decimal('10'),
                is_active=True,
                approval_status='pending',
            )
            created_opp = opp
            self.stdout.write(self.style.WARNING(f'已创建测试商机 id={opp.id}，名称={opp.name}'))

        if not opp:
            self.stdout.write(self.style.ERROR('无商机数据，跳过 8 项检查（可使用 --no-seed 避免自动创建）'))
            return

        self.stdout.write('执行 8 项流程验证（开发库）：')
        run_checks()
        if created_opp:
            self.stdout.write(self.style.WARNING('提示：测试商机已保留，如需删除可到商机列表操作'))
