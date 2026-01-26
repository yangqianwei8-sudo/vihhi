"""
诊断脚本：检查 Plan 模型中 responsible_person 字段的问题

使用方法：
    python manage.py diagnose_responsible_person
    python manage.py diagnose_responsible_person --check-db  # 检查数据库中的实际数据
    python manage.py diagnose_responsible_person --check-form  # 检查表单处理逻辑
"""

from django.core.management.base import BaseCommand
from django.db import models
from django.apps import apps
from django.contrib.auth import get_user_model
from backend.apps.plan_management.models import Plan
from backend.apps.plan_management.forms import PlanForm
import inspect

User = get_user_model()


class Command(BaseCommand):
    help = '诊断 Plan 模型中 responsible_person 字段的问题'

    def add_arguments(self, parser):
        parser.add_argument(
            '--check-db',
            action='store_true',
            help='检查数据库中的实际数据',
        )
        parser.add_argument(
            '--check-form',
            action='store_true',
            help='检查表单处理逻辑',
        )
        parser.add_argument(
            '--check-model',
            action='store_true',
            help='检查模型定义',
        )
        parser.add_argument(
            '--check-views',
            action='store_true',
            help='检查视图处理逻辑',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=' * 80))
        self.stdout.write(self.style.SUCCESS('Plan responsible_person 字段诊断工具'))
        self.stdout.write(self.style.SUCCESS('=' * 80))
        self.stdout.write('')

        # 默认检查所有项
        check_all = not any([
            options['check_db'],
            options['check_form'],
            options['check_model'],
            options['check_views']
        ])

        if check_all or options['check_model']:
            self.check_model_definition()

        if check_all or options['check_form']:
            self.check_form_logic()

        if check_all or options['check_views']:
            self.check_views_logic()

        if check_all or options['check_db']:
            self.check_database()

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 80))
        self.stdout.write(self.style.SUCCESS('诊断完成'))
        self.stdout.write(self.style.SUCCESS('=' * 80))

    def check_model_definition(self):
        """检查模型定义"""
        self.stdout.write(self.style.WARNING('\n[1] 检查模型定义'))
        self.stdout.write('-' * 80)

        try:
            # 获取 responsible_person 字段
            field = Plan._meta.get_field('responsible_person')
            self.stdout.write(f'✓ 字段名称: {field.name}')
            self.stdout.write(f'✓ 字段类型: {type(field).__name__}')
            self.stdout.write(f'✓ null 允许: {field.null}')
            self.stdout.write(f'✓ blank 允许: {field.blank}')
            self.stdout.write(f'✓ 必填字段: {not field.null and not field.blank}')

            if field.null or field.blank:
                self.stdout.write(self.style.ERROR('  ⚠ 警告: responsible_person 允许为空，但模型要求必填！'))
            else:
                self.stdout.write(self.style.SUCCESS('  ✓ responsible_person 是必填字段'))

            # 检查 save 方法
            if hasattr(Plan, 'save'):
                save_method = inspect.getsource(Plan.save)
                if 'responsible_person' in save_method:
                    self.stdout.write(self.style.SUCCESS('  ✓ Plan.save() 方法中包含 responsible_person 检查'))
                else:
                    self.stdout.write(self.style.WARNING('  ⚠ Plan.save() 方法中未找到 responsible_person 检查'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  ✗ 检查模型定义时出错: {e}'))

    def check_form_logic(self):
        """检查表单处理逻辑"""
        self.stdout.write(self.style.WARNING('\n[2] 检查表单处理逻辑'))
        self.stdout.write('-' * 80)

        try:
            # 检查 PlanForm
            form_source = inspect.getsource(PlanForm)
            
            # 检查 clean 方法
            if 'def clean' in form_source:
                clean_source = self.extract_method_source(form_source, 'def clean')
                if 'responsible_person' in clean_source:
                    self.stdout.write(self.style.SUCCESS('  ✓ PlanForm.clean() 中包含 responsible_person 处理'))
                else:
                    self.stdout.write(self.style.WARNING('  ⚠ PlanForm.clean() 中未找到 responsible_person 处理'))

            # 检查 save 方法
            if 'def save' in form_source:
                save_source = self.extract_method_source(form_source, 'def save')
                if 'responsible_person' in save_source:
                    self.stdout.write(self.style.SUCCESS('  ✓ PlanForm.save() 中包含 responsible_person 处理'))
                else:
                    self.stdout.write(self.style.WARNING('  ⚠ PlanForm.save() 中未找到 responsible_person 处理'))

            # 检查 __init__ 方法
            if 'def __init__' in form_source:
                init_source = self.extract_method_source(form_source, 'def __init__')
                if 'responsible_person' in init_source:
                    self.stdout.write(self.style.SUCCESS('  ✓ PlanForm.__init__() 中包含 responsible_person 初始化'))
                else:
                    self.stdout.write(self.style.WARNING('  ⚠ PlanForm.__init__() 中未找到 responsible_person 初始化'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  ✗ 检查表单逻辑时出错: {e}'))

    def check_views_logic(self):
        """检查视图处理逻辑"""
        self.stdout.write(self.style.WARNING('\n[3] 检查视图处理逻辑'))
        self.stdout.write('-' * 80)

        try:
            from backend.apps.plan_management import views_pages
            view_source = inspect.getsource(views_pages.plan_create)
            
            # 检查 responsible_person 的处理
            responsible_person_checks = [
                'responsible_person' in view_source,
                'form.cleaned_data.get(\'responsible_person\')' in view_source or 
                'form.cleaned_data.get("responsible_person")' in view_source,
                'plan.responsible_person' in view_source,
            ]

            if all(responsible_person_checks):
                self.stdout.write(self.style.SUCCESS('  ✓ plan_create 视图中包含 responsible_person 处理'))
            else:
                self.stdout.write(self.style.WARNING('  ⚠ plan_create 视图中 responsible_person 处理可能不完整'))

            # 检查草稿模式处理
            if 'is_draft' in view_source and 'responsible_person' in view_source:
                self.stdout.write(self.style.SUCCESS('  ✓ 草稿模式下包含 responsible_person 处理'))
            else:
                self.stdout.write(self.style.WARNING('  ⚠ 草稿模式下可能缺少 responsible_person 处理'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  ✗ 检查视图逻辑时出错: {e}'))

    def check_database(self):
        """检查数据库中的实际数据"""
        self.stdout.write(self.style.WARNING('\n[4] 检查数据库中的实际数据'))
        self.stdout.write('-' * 80)

        try:
            # 检查是否有 responsible_person 为 None 的记录
            plans_without_responsible = Plan.objects.filter(responsible_person__isnull=True)
            count = plans_without_responsible.count()
            
            if count > 0:
                self.stdout.write(self.style.ERROR(f'  ✗ 发现 {count} 个 Plan 记录的 responsible_person 为 NULL'))
                self.stdout.write(self.style.WARNING('  这些记录可能导致 RelatedObjectDoesNotExist 错误'))
                
                # 显示前5个有问题的记录
                for plan in plans_without_responsible[:5]:
                    self.stdout.write(f'    - Plan ID: {plan.id}, 编号: {plan.plan_number}, 名称: {plan.name}')
            else:
                self.stdout.write(self.style.SUCCESS('  ✓ 所有 Plan 记录都有 responsible_person'))

            # 检查最近的计划
            recent_plans = Plan.objects.select_related('responsible_person', 'created_by').order_by('-created_time')[:5]
            self.stdout.write(f'\n  最近创建的 5 个计划:')
            for plan in recent_plans:
                responsible = plan.responsible_person.username if plan.responsible_person else 'None'
                created_by = plan.created_by.username if plan.created_by else 'None'
                self.stdout.write(f'    - ID: {plan.id}, 负责人: {responsible}, 创建人: {created_by}, 状态: {plan.status}')

            # 检查草稿状态的计划
            draft_plans = Plan.objects.filter(status='draft').select_related('responsible_person')
            draft_without_responsible = draft_plans.filter(responsible_person__isnull=True).count()
            if draft_without_responsible > 0:
                self.stdout.write(self.style.WARNING(f'\n  ⚠ 发现 {draft_without_responsible} 个草稿状态的计划没有负责人'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  ✗ 检查数据库时出错: {e}'))
            import traceback
            self.stdout.write(traceback.format_exc())

    def extract_method_source(self, source, method_name):
        """从源代码中提取方法内容"""
        try:
            lines = source.split('\n')
            in_method = False
            method_lines = []
            indent_level = None

            for line in lines:
                if method_name in line and not in_method:
                    in_method = True
                    indent_level = len(line) - len(line.lstrip())
                    method_lines.append(line)
                elif in_method:
                    if line.strip() == '':
                        method_lines.append(line)
                    elif len(line) - len(line.lstrip()) > indent_level:
                        method_lines.append(line)
                    else:
                        break

            return '\n'.join(method_lines)
        except:
            return ''

