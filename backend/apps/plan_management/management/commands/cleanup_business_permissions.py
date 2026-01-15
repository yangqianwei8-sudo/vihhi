"""
管理命令：清理业务权限表中的冗余权限项

删除业务权限表（PermissionItem）中的冗余权限：
- plan_management.view_plan（应使用 plan_management.plan.view）
- plan_management.view_strategicgoal（应使用 plan_management.goal.view）

这些权限项是在 create_menu_permissions.py 中创建的，现在应该删除。
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from backend.apps.permission_management.models import PermissionItem


class Command(BaseCommand):
    help = '清理业务权限表中的冗余权限项（view_plan 和 view_strategicgoal）'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='仅显示将要执行的操作，不实际执行',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='跳过确认提示，直接删除',
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)
        force = options.get('force', False)

        if dry_run:
            self.stdout.write(self.style.WARNING('🔍 模拟运行模式，不会实际修改数据'))

        # 查找要删除的冗余权限项
        redundant_perms = PermissionItem.objects.filter(
            code__in=['plan_management.view_plan', 'plan_management.view_strategicgoal']
        )

        perm_count = redundant_perms.count()

        self.stdout.write(self.style.WARNING('=' * 70))
        self.stdout.write(self.style.WARNING('清理业务权限表中的冗余权限项'))
        self.stdout.write(self.style.WARNING('=' * 70))
        self.stdout.write('')
        self.stdout.write('将删除的权限项：')
        
        if perm_count > 0:
            for perm in redundant_perms:
                self.stdout.write(f'  - {perm.code}: {perm.name}')
        else:
            self.stdout.write('  （没有找到需要删除的权限项）')
        
        self.stdout.write('')
        self.stdout.write('注意：')
        self.stdout.write('  - 这些是冗余的业务权限项')
        self.stdout.write('  - 应使用标准业务权限：plan_management.plan.view 和 plan_management.goal.view')
        self.stdout.write('  - 删除后不会影响系统功能')
        self.stdout.write('')

        if perm_count == 0:
            self.stdout.write(self.style.SUCCESS('✓ 没有找到需要删除的权限项'))
            return

        if not force and not dry_run:
            confirm = input('确认删除这些权限项？输入 "YES" 继续：')
            if confirm != 'YES':
                self.stdout.write(self.style.ERROR('操作已取消'))
                return

        try:
            with transaction.atomic():
                # 检查是否有角色在使用这些权限
                from backend.apps.system_management.models import Role
                roles_with_perms = Role.objects.filter(custom_permissions__in=redundant_perms).distinct()
                
                if roles_with_perms.exists():
                    self.stdout.write(self.style.WARNING('  ⚠ 发现以下角色正在使用这些权限：'))
                    for role in roles_with_perms:
                        self.stdout.write(f'      • 角色: {role.name}')
                    self.stdout.write(self.style.WARNING('  ⚠ 将自动从角色中移除这些权限'))
                    
                    # 从角色中移除权限
                    for role in roles_with_perms:
                        role.custom_permissions.remove(*redundant_perms)
                
                if dry_run:
                    self.stdout.write(self.style.SUCCESS(f'  ✓ 将删除 {perm_count} 条冗余权限项（模拟）'))
                else:
                    deleted_count = redundant_perms.delete()[0]
                    self.stdout.write(self.style.SUCCESS(f'  ✓ 已删除 {deleted_count} 条冗余权限项'))

                if not dry_run:
                    self.stdout.write('')
                    self.stdout.write(self.style.SUCCESS('=' * 70))
                    self.stdout.write(self.style.SUCCESS('权限项清理完成！'))
                    self.stdout.write(self.style.SUCCESS('=' * 70))
                    self.stdout.write('')
                    self.stdout.write('现在系统中只保留标准业务权限：')
                    self.stdout.write('  - plan_management.view（菜单权限）')
                    self.stdout.write('  - plan_management.plan.view（查看计划）')
                    self.stdout.write('  - plan_management.goal.view（查看目标）')

        except Exception as e:
            self.stdout.write('')
            self.stdout.write(self.style.ERROR('=' * 70))
            self.stdout.write(self.style.ERROR('权限项清理失败！'))
            self.stdout.write(self.style.ERROR('=' * 70))
            self.stdout.write(self.style.ERROR(f'错误信息：{str(e)}'))
            import traceback
            self.stdout.write(self.style.ERROR(traceback.format_exc()))
            raise

