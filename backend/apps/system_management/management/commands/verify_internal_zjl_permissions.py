"""
验证 internal_zjl 角色的 Django 权限是否正常
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from backend.core.permissions import require_perm, has_perm2

User = get_user_model()


class Command(BaseCommand):
    help = '验证 internal_zjl 角色的 Django 权限是否正常'

    def handle(self, *args, **options):
        self.stdout.write('=' * 60)
        self.stdout.write('验证 internal_zjl 角色权限')
        self.stdout.write('=' * 60)
        self.stdout.write('')

        # 查找 internal_zjl 角色用户
        from backend.apps.system_management.models import Role
        role = Role.objects.filter(code='internal_zjl', is_active=True).first()
        
        if not role:
            self.stdout.write(self.style.ERROR('未找到 internal_zjl 角色'))
            return

        users = User.objects.filter(roles=role, is_active=True).distinct()
        if not users.exists():
            self.stdout.write(self.style.WARNING('未找到具有 internal_zjl 角色的用户'))
            return

        # 检查 Group
        try:
            group = Group.objects.get(name='INTERNAL_ZJL')
            self.stdout.write(f'\nGroup: {group.name}')
            self.stdout.write(f'  权限数: {group.permissions.count()}')
            self.stdout.write(f'  用户数: {group.user_set.count()}')
        except Group.DoesNotExist:
            self.stdout.write(self.style.ERROR('\n错误：未找到 INTERNAL_ZJL Group'))
            self.stdout.write('提示：请先运行 sync_internal_roles_to_groups 命令')
            return

        # 验证每个用户
        test_permissions = [
            'plan_management.view_plan',
            'plan_management.change_plan',
            'plan_management.approve_plan',
            'plan_management.view_strategicgoal',
            'plan_management.change_strategicgoal',
            'plan_management.approve_strategicgoal',
        ]

        for user in users:
            self.stdout.write(f'\n用户: {user.username}')
            self.stdout.write(f'  所属组: {[g.name for g in user.groups.all()]}')
            self.stdout.write(f'  是否在 INTERNAL_ZJL 组: {group in user.groups.all()}')

            self.stdout.write('\n  Django 权限检查 (user.has_perm):')
            all_passed = True
            for perm in test_permissions:
                result = user.has_perm(perm)
                status = '✓' if result else '✗'
                color = self.style.SUCCESS if result else self.style.ERROR
                self.stdout.write(color(f'    {status} {perm}: {result}'))
                if not result:
                    all_passed = False

            self.stdout.write('\n  has_perm2 检查（Django优先+业务兜底）:')
            for perm in test_permissions:
                result = has_perm2(user, perm)
                status = '✓' if result else '✗'
                color = self.style.SUCCESS if result else self.style.ERROR
                self.stdout.write(color(f'    {status} {perm}: {result}'))

            self.stdout.write('\n  require_perm 检查:')
            try:
                require_perm(user, 'plan_management.view_plan')
                self.stdout.write(self.style.SUCCESS('    ✓ require_perm("plan_management.view_plan"): 通过'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'    ✗ require_perm 失败: {e}'))
                all_passed = False

            if all_passed:
                self.stdout.write(self.style.SUCCESS(f'\n  ✅ 用户 {user.username} 权限验证通过'))
            else:
                self.stdout.write(self.style.ERROR(f'\n  ❌ 用户 {user.username} 权限验证失败'))

        self.stdout.write('\n' + '=' * 60)
        self.stdout.write('验证完成')
        self.stdout.write('=' * 60)

