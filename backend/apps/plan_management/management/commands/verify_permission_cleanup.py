"""
管理命令：验证权限清理结果

检查系统中是否还存在冗余权限，并显示当前权限状态。
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Permission, Group
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import get_user_model
from backend.apps.plan_management.models import Plan, StrategicGoal
from backend.apps.permission_management.models import PermissionItem
from backend.apps.system_management.models import Role

User = get_user_model()


class Command(BaseCommand):
    help = '验证权限清理结果，检查是否还存在冗余权限'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('=' * 70))
        self.stdout.write(self.style.WARNING('权限清理验证'))
        self.stdout.write(self.style.WARNING('=' * 70))
        self.stdout.write('')

        # ========== 检查 Django 自动生成的权限 ==========
        self.stdout.write(self.style.SUCCESS('1. 检查 Django 自动生成的权限（auth_permission 表）'))
        self.stdout.write('-' * 70)
        
        plan_content_type = ContentType.objects.get_for_model(Plan)
        goal_content_type = ContentType.objects.get_for_model(StrategicGoal)

        plan_perms = Permission.objects.filter(
            content_type=plan_content_type
        ).exclude(codename__startswith='custom_')
        
        goal_perms = Permission.objects.filter(
            content_type=goal_content_type
        ).exclude(codename__startswith='custom_')

        if plan_perms.exists():
            self.stdout.write(self.style.ERROR(f'  ✗ 发现 {plan_perms.count()} 条 Plan 模型权限：'))
            for perm in plan_perms:
                # 检查是否有用户或组在使用
                users_count = User.objects.filter(user_permissions=perm).count()
                groups_count = Group.objects.filter(permissions=perm).count()
                self.stdout.write(f'    • plan_management.{perm.codename} (用户: {users_count}, 组: {groups_count})')
        else:
            self.stdout.write(self.style.SUCCESS('  ✓ Plan 模型权限已清理'))

        if goal_perms.exists():
            self.stdout.write(self.style.ERROR(f'  ✗ 发现 {goal_perms.count()} 条 StrategicGoal 模型权限：'))
            for perm in goal_perms:
                users_count = User.objects.filter(user_permissions=perm).count()
                groups_count = Group.objects.filter(permissions=perm).count()
                self.stdout.write(f'    • plan_management.{perm.codename} (用户: {users_count}, 组: {groups_count})')
        else:
            self.stdout.write(self.style.SUCCESS('  ✓ StrategicGoal 模型权限已清理'))

        self.stdout.write('')

        # ========== 检查业务权限表中的冗余权限 ==========
        self.stdout.write(self.style.SUCCESS('2. 检查业务权限表中的冗余权限（system_permission_item 表）'))
        self.stdout.write('-' * 70)
        
        redundant_business_perms = PermissionItem.objects.filter(
            code__in=['plan_management.view_plan', 'plan_management.view_strategicgoal']
        )

        if redundant_business_perms.exists():
            self.stdout.write(self.style.ERROR(f'  ✗ 发现 {redundant_business_perms.count()} 条冗余业务权限：'))
            for perm in redundant_business_perms:
                roles_count = Role.objects.filter(custom_permissions=perm).count()
                self.stdout.write(f'    • {perm.code}: {perm.name} (角色: {roles_count})')
        else:
            self.stdout.write(self.style.SUCCESS('  ✓ 冗余业务权限已清理'))

        self.stdout.write('')

        # ========== 检查标准权限是否存在 ==========
        self.stdout.write(self.style.SUCCESS('3. 检查标准业务权限'))
        self.stdout.write('-' * 70)
        
        standard_perms = PermissionItem.objects.filter(
            code__in=[
                'plan_management.view',
                'plan_management.plan.view',
                'plan_management.plan.create',
                'plan_management.plan.manage',
                'plan_management.goal.view',
                'plan_management.goal.create',
                'plan_management.manage_goal',
            ]
        )

        expected_codes = {
            'plan_management.view',
            'plan_management.plan.view',
            'plan_management.plan.create',
            'plan_management.plan.manage',
            'plan_management.goal.view',
            'plan_management.goal.create',
            'plan_management.manage_goal',
        }

        existing_codes = set(standard_perms.values_list('code', flat=True))
        missing_codes = expected_codes - existing_codes

        if missing_codes:
            self.stdout.write(self.style.WARNING(f'  ⚠ 缺少 {len(missing_codes)} 条标准权限：'))
            for code in missing_codes:
                self.stdout.write(f'    • {code}')
            self.stdout.write('  建议运行: python manage.py seed_permissions')
        else:
            self.stdout.write(self.style.SUCCESS('  ✓ 所有标准权限都存在'))

        self.stdout.write('')
        self.stdout.write('标准权限详情：')
        for perm in standard_perms.order_by('code'):
            roles_count = Role.objects.filter(custom_permissions=perm).count()
            status = '✓' if perm.is_active else '✗'
            self.stdout.write(f'  {status} {perm.code}: {perm.name} (角色: {roles_count})')

        self.stdout.write('')

        # ========== 总结 ==========
        self.stdout.write(self.style.WARNING('=' * 70))
        self.stdout.write('验证总结')
        self.stdout.write('=' * 70)
        
        has_issues = False
        
        if plan_perms.exists() or goal_perms.exists():
            self.stdout.write(self.style.ERROR('  ✗ 发现 Django 自动生成的权限，需要清理'))
            has_issues = True
        
        if redundant_business_perms.exists():
            self.stdout.write(self.style.ERROR('  ✗ 发现冗余业务权限，需要清理'))
            has_issues = True
        
        if missing_codes:
            self.stdout.write(self.style.WARNING('  ⚠ 缺少标准权限，需要运行 seed_permissions'))
            has_issues = True
        
        if not has_issues:
            self.stdout.write(self.style.SUCCESS('  ✓ 权限清理完成，所有检查通过'))
            self.stdout.write('')
            self.stdout.write('建议操作：')
            self.stdout.write('  1. 检查角色配置，确保只使用标准权限')
            self.stdout.write('  2. 测试系统功能确保权限控制正常')
        else:
            self.stdout.write('')
            self.stdout.write('建议操作：')
            if plan_perms.exists() or goal_perms.exists() or redundant_business_perms.exists():
                self.stdout.write('  1. 运行: python manage.py cleanup_all_redundant_permissions')
            if missing_codes:
                self.stdout.write('  2. 运行: python manage.py seed_permissions')
            self.stdout.write('  3. 重新运行此命令验证清理结果')

