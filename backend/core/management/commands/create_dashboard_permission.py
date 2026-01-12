"""
创建总工作台权限的管理命令
"""
from django.core.management.base import BaseCommand
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import Permission
from django.db import transaction


class Command(BaseCommand):
    help = "创建 core.view_dashboard 权限（总工作台访问权限）"

    def handle(self, *args, **options):
        with transaction.atomic():
            # 创建或获取 ContentType（使用一个虚拟的模型名称）
            # 由于 core 不是模型，我们使用一个代理 ContentType
            ct, created = ContentType.objects.get_or_create(
                app_label='core',
                model='dashboard',
                defaults={'app_label': 'core', 'model': 'dashboard'}
            )
            
            if created:
                self.stdout.write(self.style.SUCCESS(f"✓ 创建 ContentType: core.dashboard"))
            else:
                self.stdout.write(f"  - ContentType 已存在: core.dashboard")

            # 创建或获取权限
            perm, created = Permission.objects.get_or_create(
                content_type=ct,
                codename='view_dashboard',
                defaults={
                    'name': '可以访问总工作台',
                    'content_type': ct,
                    'codename': 'view_dashboard'
                }
            )
            
            if created:
                self.stdout.write(self.style.SUCCESS(f"✓ 创建权限: core.view_dashboard"))
            else:
                self.stdout.write(f"  - 权限已存在: core.view_dashboard")

        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(self.style.SUCCESS("完成！"))
        self.stdout.write("=" * 60)
        self.stdout.write("\n提示：")
        self.stdout.write("  1. 权限已创建：core.view_dashboard")
        self.stdout.write("  2. 可以通过 Django Admin 将权限分配给用户或组")
        self.stdout.write("  3. 或使用 grant_customer_permissions 命令将权限添加到 INTERNAL_ZJL 组")

