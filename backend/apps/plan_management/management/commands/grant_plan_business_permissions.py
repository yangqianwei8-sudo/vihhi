"""
给用户分配计划管理业务权限（PermissionItem）
通过角色分配，确保菜单能正常显示
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from backend.apps.permission_management.models import PermissionItem
from backend.apps.system_management.models import Role

User = get_user_model()


class Command(BaseCommand):
    help = '给用户分配计划管理业务权限（用于菜单显示）'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            required=True,
            help='用户名'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='仅显示将要执行的操作，不实际执行'
        )

    def handle(self, *args, **options):
        username = options['username']
        dry_run = options.get('dry_run', False)

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'错误：用户 {username} 不存在'))
            return

        if dry_run:
            self.stdout.write(self.style.WARNING('🔍 模拟运行模式，不会实际修改数据'))

        self.stdout.write(f'\n开始为用户 {username} 分配计划管理业务权限...')

        # 需要的业务权限代码（菜单使用的权限代码）
        required_permissions = [
            'plan_management.view_plan',
            'plan_management.view_strategicgoal',
        ]
        
        # 如果上述权限不存在，尝试使用替代权限代码
        fallback_permissions = [
            'plan_management.plan.view',
            'plan_management.goal.view',
        ]

        # 获取或创建权限项
        permissions = []
        for perm_code in required_permissions:
            try:
                perm = PermissionItem.objects.get(code=perm_code, is_active=True)
                permissions.append(perm)
                self.stdout.write(f'  ✓ 找到权限：{perm_code} ({perm.name})')
            except PermissionItem.DoesNotExist:
                # 尝试使用替代权限代码
                fallback_code = None
                if perm_code == 'plan_management.view_plan':
                    fallback_code = 'plan_management.plan.view'
                elif perm_code == 'plan_management.view_strategicgoal':
                    fallback_code = 'plan_management.goal.view'
                
                if fallback_code:
                    try:
                        perm = PermissionItem.objects.get(code=fallback_code, is_active=True)
                        permissions.append(perm)
                        self.stdout.write(f'  ✓ 使用替代权限：{fallback_code} ({perm.name})')
                    except PermissionItem.DoesNotExist:
                        self.stdout.write(self.style.WARNING(f'  ⚠ 权限不存在：{perm_code} 和 {fallback_code}'))
                else:
                    self.stdout.write(self.style.WARNING(f'  ⚠ 权限不存在：{perm_code}'))

        if not permissions:
            self.stdout.write(self.style.ERROR('错误：没有找到任何权限项'))
            self.stdout.write('提示：请先运行 seed_permissions 命令创建权限项')
            return

        # 获取用户的所有角色
        user_roles = user.roles.filter(is_active=True)
        if not user_roles.exists():
            self.stdout.write(self.style.WARNING(f'用户 {username} 没有分配任何角色'))
            self.stdout.write('提示：请先给用户分配角色')
            return

        self.stdout.write(f'\n用户角色: {[r.name for r in user_roles]}')

        # 给每个角色分配权限
        updated_roles = []
        for role in user_roles:
            current_perms = set(role.custom_permissions.filter(is_active=True).values_list('code', flat=True))
            new_perms = {p.code for p in permissions}
            
            if new_perms.issubset(current_perms):
                self.stdout.write(f'  角色 {role.name} 已有所有权限')
            else:
                missing_perms = new_perms - current_perms
                if not dry_run:
                    # 添加新权限到角色
                    role.custom_permissions.add(*permissions)
                updated_roles.append(role.name)
                self.stdout.write(self.style.SUCCESS(f'  ✓ 为角色 {role.name} 添加权限: {", ".join(missing_perms)}'))

        if updated_roles and not dry_run:
            self.stdout.write(self.style.SUCCESS(f'\n✓ 已为用户 {username} 的角色分配业务权限'))
            self.stdout.write(f'  更新的角色: {", ".join(updated_roles)}')
        elif updated_roles:
            self.stdout.write(self.style.SUCCESS(f'\n✓ 将为用户 {username} 的角色分配业务权限（模拟）'))

        # 清除用户权限缓存
        if not dry_run and hasattr(user, '_permission_codes_cache'):
            delattr(user, '_permission_codes_cache')

        # 验证
        from backend.apps.system_management.services import get_user_permission_codes
        perms = get_user_permission_codes(user)
        self.stdout.write(f'\n验证结果:')
        self.stdout.write(f'  用户业务权限: {perms}')
        self.stdout.write(f'  是否有 plan_management.view_plan: {"plan_management.view_plan" in perms}')
        self.stdout.write(f'  是否有 plan_management.view_strategicgoal: {"plan_management.view_strategicgoal" in perms}')
        
        if 'plan_management.view_plan' in perms or '__all__' in perms:
            self.stdout.write(self.style.SUCCESS('\n✅ 权限分配成功，菜单应该能正常显示'))
        else:
            self.stdout.write(self.style.ERROR('\n❌ 权限分配失败，请检查'))

