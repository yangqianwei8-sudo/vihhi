from django.core.management.base import BaseCommand
from backend.apps.permission_management.models import PermissionItem
from backend.apps.system_management.management.commands.seed_permissions import PERMISSION_DEFINITIONS


class Command(BaseCommand):
    help = '验证权限定义中的模块名称是否与 PermissionItem.MODULE_CHOICES 一致'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('开始验证权限模块同步情况...\n'))
        
        # 获取所有有效的模块名称
        valid_modules = {choice[0] for choice in PermissionItem.MODULE_CHOICES}
        
        # 从权限定义中提取所有使用的模块
        used_modules = {perm_def['module'] for perm_def in PERMISSION_DEFINITIONS}
        
        # 检查一致性
        missing_modules = used_modules - valid_modules
        unused_valid_modules = valid_modules - used_modules
        
        # 显示结果
        self.stdout.write(f'权限定义中使用的模块 ({len(used_modules)} 个):')
        for module in sorted(used_modules):
            status = '✓' if module in valid_modules else '✗'
            self.stdout.write(f'  {status} {module}')
        
        self.stdout.write(f'\nMODULE_CHOICES 中定义的模块 ({len(valid_modules)} 个):')
        for module in sorted(valid_modules):
            status = '✓' if module in used_modules else '○'
            self.stdout.write(f'  {status} {module}')
        
        # 报告问题
        if missing_modules:
            self.stdout.write(
                self.style.ERROR(
                    f'\n❌ 错误：以下模块在权限定义中使用，但不在 MODULE_CHOICES 中:\n'
                    f'   {", ".join(sorted(missing_modules))}'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    '\n✓ 所有权限定义中使用的模块都在 MODULE_CHOICES 中！'
                )
            )
        
        if unused_valid_modules:
            self.stdout.write(
                self.style.WARNING(
                    f'\n⚠️  警告：以下模块在 MODULE_CHOICES 中定义，但未在权限定义中使用:\n'
                    f'   {", ".join(sorted(unused_valid_modules))}'
                )
            )
        
        # 检查数据库中的模块
        db_modules = set(PermissionItem.objects.values_list('module', flat=True).distinct())
        db_invalid = db_modules - valid_modules
        
        if db_invalid:
            self.stdout.write(
                self.style.ERROR(
                    f'\n❌ 错误：数据库中存在不在 MODULE_CHOICES 中的模块:\n'
                    f'   {", ".join(sorted(db_invalid))}\n'
                    f'   请运行: python manage.py sync_module_names'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'\n✓ 数据库中的所有模块都在 MODULE_CHOICES 中！'
                )
            )
        
        # 总结
        if not missing_modules and not db_invalid:
            self.stdout.write(
                self.style.SUCCESS(
                    '\n✅ 验证通过！权限模块定义已同步。'
                )
            )
        else:
            self.stdout.write(
                self.style.ERROR(
                    '\n❌ 验证失败！请修复上述问题。'
                )
            )

