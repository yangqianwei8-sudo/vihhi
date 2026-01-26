"""
测试脚本：模拟 Plan 创建过程，检查 responsible_person 是否正确设置

使用方法：
    python manage.py test_plan_creation
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.test import RequestFactory
from backend.apps.plan_management.forms import PlanForm
from backend.apps.plan_management.models import Plan, StrategicGoal
from django.utils import timezone
from datetime import timedelta

User = get_user_model()


class Command(BaseCommand):
    help = '测试 Plan 创建过程，检查 responsible_person 是否正确设置'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user',
            type=str,
            help='指定测试用户（用户名）',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=' * 80))
        self.stdout.write(self.style.SUCCESS('Plan 创建测试工具'))
        self.stdout.write(self.style.SUCCESS('=' * 80))
        self.stdout.write('')

        # 获取测试用户
        if options['user']:
            try:
                user = User.objects.get(username=options['user'])
            except User.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'用户 {options["user"]} 不存在'))
                return
        else:
            user = User.objects.filter(is_active=True).first()
            if not user:
                self.stdout.write(self.style.ERROR('没有可用的活跃用户'))
                return

        self.stdout.write(f'使用测试用户: {user.username} (ID: {user.id})')
        self.stdout.write('')

        # 测试正常模式
        self.stdout.write(self.style.WARNING('[1] 测试正常创建模式'))
        self.test_normal_creation(user)

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 80))
        self.stdout.write(self.style.SUCCESS('测试完成'))
        self.stdout.write(self.style.SUCCESS('=' * 80))

    def test_normal_creation(self, user):
        """测试正常创建模式"""
        self.stdout.write('-' * 80)

        try:
            # 获取一个战略目标
            goal = StrategicGoal.objects.filter(status__in=['published', 'in_progress']).first()
            if not goal:
                self.stdout.write(self.style.WARNING('  ⚠ 没有可用的战略目标，跳过测试'))
                return

            # 创建表单数据
            form_data = {
                'name': f'测试计划 - {timezone.now().strftime("%Y%m%d%H%M%S")}',
                'content': '这是一个测试计划',
                'plan_objective': '测试目标',
                'plan_period': 'monthly',
                'level': 'company',
                'related_goal': goal.id,
                'start_time': (timezone.now() + timedelta(days=1)).strftime('%Y-%m-%d'),
                'responsible_person': user.id,
            }

            # 创建表单实例
            form = PlanForm(data=form_data, user=user)
            
            self.stdout.write('  检查表单验证...')
            if form.is_valid():
                self.stdout.write(self.style.SUCCESS('  ✓ 表单验证通过'))
                
                # 检查 cleaned_data
                if 'responsible_person' in form.cleaned_data:
                    self.stdout.write(self.style.SUCCESS(f'  ✓ cleaned_data 中包含 responsible_person: {form.cleaned_data["responsible_person"]}'))
                else:
                    self.stdout.write(self.style.ERROR('  ✗ cleaned_data 中缺少 responsible_person'))
                    return

                # 测试 save(commit=False)
                self.stdout.write('  测试 form.save(commit=False)...')
                plan = form.save(commit=False)
                
                if plan.responsible_person:
                    self.stdout.write(self.style.SUCCESS(f'  ✓ plan.responsible_person 已设置: {plan.responsible_person.username}'))
                else:
                    self.stdout.write(self.style.ERROR('  ✗ plan.responsible_person 为 None'))
                    return

                # 不实际保存到数据库
                self.stdout.write(self.style.SUCCESS('  ✓ 正常模式测试通过（未实际保存）'))

            else:
                self.stdout.write(self.style.ERROR('  ✗ 表单验证失败'))
                for field, errors in form.errors.items():
                    self.stdout.write(f'    - {field}: {errors}')

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  ✗ 测试失败: {e}'))
            import traceback
            self.stdout.write(traceback.format_exc())

