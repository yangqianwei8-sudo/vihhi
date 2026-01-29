"""
Django 管理命令：验证目标跟踪模板
运行此命令可以自动验证 tracking_base.html 模板的所有功能
"""
from django.core.management.base import BaseCommand
from django.test import TestCase
from django.test.utils import get_runner
from django.conf import settings
import sys


class Command(BaseCommand):
    help = '验证目标跟踪模板的所有功能是否完整实现'

    def add_arguments(self, parser):
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='显示详细输出',
        )
        parser.add_argument(
            '--keepdb',
            action='store_true',
            help='保留测试数据库（加快测试速度）',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('开始验证目标跟踪模板...'))
        
        try:
            # 运行测试
            TestRunner = get_runner(settings)
            test_runner = TestRunner(
                verbosity=2 if options['verbose'] else 1,
                interactive=False,
                keepdb=options.get('keepdb', False)
            )
            
            # 运行模板测试（使用完整的应用路径）
            test_labels = [
                'backend.apps.system_management.tests.test_tracking_template',
                'backend.apps.system_management.tests.test_tracking_template_validation',
            ]
            
            failures = test_runner.run_tests(test_labels)
            
            if failures:
                self.stdout.write(
                    self.style.ERROR(f'\n验证失败：发现 {failures} 个问题')
                )
                sys.exit(1)
            else:
                self.stdout.write(
                    self.style.SUCCESS('\n✅ 所有验证通过！模板功能完整。')
                )
        except ValueError as e:
            error_msg = str(e)
            if 'permission_management' in error_msg or 'isn\'t installed' in error_msg:
                self.stdout.write(
                    self.style.ERROR('\n❌ 数据库迁移错误：应用配置问题')
                )
                self.stdout.write(
                    self.style.WARNING('\n可能的原因：')
                )
                self.stdout.write('  1. permission_management 应用未正确安装')
                self.stdout.write('  2. 数据库迁移文件存在依赖问题')
                self.stdout.write('  3. INSTALLED_APPS 配置不完整')
                self.stdout.write(
                    self.style.WARNING('\n解决方案：')
                )
                self.stdout.write('  1. 确保所有应用已正确安装：')
                self.stdout.write('     python manage.py migrate')
                self.stdout.write('  2. 或者直接使用 Django test 命令：')
                self.stdout.write(
                    '     python manage.py test backend.apps.system_management.tests.test_tracking_template'
                )
                self.stdout.write('  3. 检查 settings.py 中的 INSTALLED_APPS 配置')
                self.stdout.write(
                    self.style.ERROR(f'\n详细错误信息：\n{error_msg}')
                )
                sys.exit(1)
            else:
                raise
