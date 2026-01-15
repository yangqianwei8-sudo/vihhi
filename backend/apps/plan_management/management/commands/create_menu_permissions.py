"""
创建计划管理菜单所需的权限项

注意：此命令已废弃，菜单系统使用 plan_management.view 权限
业务权限应使用：
- plan_management.plan.view（查看计划）
- plan_management.goal.view（查看目标）

这些权限在 seed_permissions.py 中已定义，无需单独创建。
"""
from django.core.management.base import BaseCommand
from backend.apps.permission_management.models import PermissionItem


class Command(BaseCommand):
    help = '创建计划管理菜单所需的权限项'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='仅显示将要执行的操作，不实际执行'
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)

        if dry_run:
            self.stdout.write(self.style.WARNING('🔍 模拟运行模式，不会实际修改数据'))

        self.stdout.write('开始创建计划管理菜单权限项...\n')

        # 注意：此命令已废弃
        # 菜单系统使用 plan_management.view 权限
        # 业务权限使用 plan_management.plan.view 和 plan_management.goal.view
        # 这些权限在 seed_permissions.py 中已定义
        
        self.stdout.write(self.style.WARNING('⚠️  此命令已废弃'))
        self.stdout.write('菜单系统使用 plan_management.view 权限')
        self.stdout.write('业务权限应使用：')
        self.stdout.write('  - plan_management.plan.view（查看计划）')
        self.stdout.write('  - plan_management.goal.view（查看目标）')
        self.stdout.write('这些权限在 seed_permissions.py 中已定义，无需单独创建。')
        self.stdout.write('')
        self.stdout.write('如需创建权限，请运行：python manage.py seed_permissions')
        return
        
        # 以下代码已废弃，保留仅用于参考
        permissions_to_create = []

        created_count = 0
        for perm_data in permissions_to_create:
            try:
                perm = PermissionItem.objects.get(code=perm_data['code'])
                self.stdout.write(f'  - 权限已存在：{perm_data["code"]} ({perm.name})')
            except PermissionItem.DoesNotExist:
                if not dry_run:
                    perm = PermissionItem.objects.create(
                        code=perm_data['code'],
                        module=perm_data['module'],
                        action=perm_data['action'],
                        name=perm_data['name'],
                        description=perm_data['description'],
                        is_active=True,
                    )
                    self.stdout.write(self.style.SUCCESS(f'  ✓ 创建权限：{perm_data["code"]} ({perm.name})'))
                    created_count += 1
                else:
                    self.stdout.write(self.style.SUCCESS(f'  ✓ 将创建权限：{perm_data["code"]} ({perm_data["name"]})'))
                    created_count += 1

        if dry_run:
            self.stdout.write(f'\n将创建 {created_count} 个权限项（模拟）')
        else:
            self.stdout.write(f'\n✓ 完成！创建了 {created_count} 个权限项')

