"""
管理命令：统一计划管理查看权限

将 plan_management.plan.view 权限统一替换为 plan_management.view
从所有角色中移除 plan_management.plan.view，确保只使用 plan_management.view
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from backend.apps.permission_management.models import PermissionItem
from backend.apps.system_management.models import Role


class Command(BaseCommand):
    help = '统一计划管理查看权限，移除冗余的 plan_management.plan.view'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='仅显示将要执行的操作，不实际执行',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='跳过确认提示，直接执行',
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)
        force = options.get('force', False)

        if dry_run:
            self.stdout.write(self.style.WARNING('🔍 模拟运行模式，不会实际修改数据'))

        self.stdout.write(self.style.WARNING('=' * 70))
        self.stdout.write(self.style.WARNING('统一计划管理查看权限'))
        self.stdout.write(self.style.WARNING('=' * 70))
        self.stdout.write('')

        try:
            # 获取权限
            plan_view_perm = PermissionItem.objects.filter(code='plan_management.plan.view').first()
            main_view_perm = PermissionItem.objects.filter(code='plan_management.view').first()

            if not plan_view_perm:
                self.stdout.write(self.style.SUCCESS('✓ plan_management.plan.view 权限不存在，无需处理'))
                return

            if not main_view_perm:
                self.stdout.write(self.style.ERROR('✗ plan_management.view 权限不存在，请先运行 seed_permissions'))
                return

            # 查找使用 plan_management.plan.view 的角色
            roles_with_plan_view = Role.objects.filter(custom_permissions=plan_view_perm).distinct()
            roles_with_main_view = Role.objects.filter(custom_permissions=main_view_perm).distinct()

            self.stdout.write(f'找到 {roles_with_plan_view.count()} 个角色使用 plan_management.plan.view')
            self.stdout.write(f'找到 {roles_with_main_view.count()} 个角色使用 plan_management.view')
            self.stdout.write('')

            if roles_with_plan_view.exists():
                self.stdout.write('需要处理的角色：')
                for role in roles_with_plan_view:
                    has_main_view = role in roles_with_main_view
                    status = '✓' if has_main_view else '⚠'
                    self.stdout.write(f'  {status} {role.name} (code: {role.code})')
                    if not has_main_view:
                        self.stdout.write(f'      → 将添加 plan_management.view 权限')
                    self.stdout.write(f'      → 将移除 plan_management.plan.view 权限')
            else:
                self.stdout.write(self.style.SUCCESS('✓ 没有角色使用 plan_management.plan.view，无需处理'))
                return

            self.stdout.write('')
            self.stdout.write('注意：')
            self.stdout.write('  - plan_management.view 是更宽泛的权限，包含 plan_management.plan.view 的功能')
            self.stdout.write('  - 权限检查函数已支持兼容，移除 plan_management.plan.view 不会影响功能')
            self.stdout.write('  - 建议统一使用 plan_management.view 作为计划管理模块的查看权限')
            self.stdout.write('')

            if not force and not dry_run:
                confirm = input('确认执行统一操作？输入 "YES" 继续：')
                if confirm != 'YES':
                    self.stdout.write(self.style.ERROR('操作已取消'))
                    return

            with transaction.atomic():
                if dry_run:
                    self.stdout.write(self.style.SUCCESS('  ✓ 将统一权限（模拟）'))
                else:
                    # 为没有 plan_management.view 的角色添加该权限
                    for role in roles_with_plan_view:
                        if role not in roles_with_main_view:
                            role.custom_permissions.add(main_view_perm)
                            self.stdout.write(self.style.SUCCESS(f'  ✓ 为角色 {role.name} 添加 plan_management.view'))
                        
                        # 移除 plan_management.plan.view
                        role.custom_permissions.remove(plan_view_perm)
                        self.stdout.write(self.style.SUCCESS(f'  ✓ 从角色 {role.name} 移除 plan_management.plan.view'))

                    # 停用 plan_management.plan.view 权限（不删除，保留兼容性）
                    plan_view_perm.is_active = False
                    plan_view_perm.save()
                    self.stdout.write(self.style.SUCCESS(f'  ✓ 已停用 plan_management.plan.view 权限'))

                if not dry_run:
                    self.stdout.write('')
                    self.stdout.write(self.style.SUCCESS('=' * 70))
                    self.stdout.write(self.style.SUCCESS('权限统一完成！'))
                    self.stdout.write(self.style.SUCCESS('=' * 70))
                    self.stdout.write('')
                    self.stdout.write('现在所有角色都使用 plan_management.view 权限')
                    self.stdout.write('plan_management.plan.view 权限已停用，但保留在数据库中以确保兼容性')

        except Exception as e:
            self.stdout.write('')
            self.stdout.write(self.style.ERROR('=' * 70))
            self.stdout.write(self.style.ERROR('权限统一失败！'))
            self.stdout.write(self.style.ERROR('=' * 70))
            self.stdout.write(self.style.ERROR(f'错误信息：{str(e)}'))
            import traceback
            self.stdout.write(self.style.ERROR(traceback.format_exc()))
            raise

