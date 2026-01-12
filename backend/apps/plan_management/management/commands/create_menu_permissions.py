"""
创建计划管理菜单所需的权限项
菜单使用 plan_management.view_plan 和 plan_management.view_strategicgoal
但实际权限项可能是 plan_management.plan.view 和 plan_management.goal.view
创建这两个权限项以确保菜单能正常工作
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

        # 需要创建的权限项
        permissions_to_create = [
            {
                'code': 'plan_management.view_plan',
                'module': '计划管理',
                'action': 'view_plan',
                'name': '计划管理-查看计划',
                'description': '查看计划列表和详情（菜单权限）',
            },
            {
                'code': 'plan_management.view_strategicgoal',
                'module': '计划管理',
                'action': 'view_strategicgoal',
                'name': '计划管理-查看目标',
                'description': '查看战略目标（菜单权限）',
            },
        ]

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

