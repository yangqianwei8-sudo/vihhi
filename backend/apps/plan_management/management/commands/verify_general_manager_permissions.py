"""
验证总经理用户的计划管理权限
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from backend.apps.system_management.models import Role

User = get_user_model()


class Command(BaseCommand):
    help = '验证总经理用户的计划管理权限'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            help='指定用户名（如果不指定，则检查所有总经理角色用户）'
        )

    def handle(self, *args, **options):
        username = options.get('username')

        self.stdout.write('=' * 60)
        self.stdout.write('验证总经理计划管理权限')
        self.stdout.write('=' * 60)
        self.stdout.write('')

        # 获取用户
        if username:
            try:
                users = [User.objects.get(username=username)]
            except User.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'错误：用户 {username} 不存在'))
                return
        else:
            # 查找所有总经理角色用户
            gm_role = Role.objects.filter(code='general_manager', is_active=True).first()
            zjl_role = Role.objects.filter(code='internal_zjl', is_active=True).first()

            from django.db.models import Q
            role_filter = Q()
            if gm_role:
                role_filter |= Q(roles=gm_role)
            if zjl_role:
                role_filter |= Q(roles=zjl_role)

            users = User.objects.filter(role_filter, is_active=True).distinct()

        if not users.exists():
            self.stdout.write(self.style.WARNING('⚠ 未找到总经理用户'))
            return

        # 验证每个用户的权限
        all_passed = True
        for user in users:
            self.stdout.write(f'\n用户: {user.username}')
            self.stdout.write(f'  是否激活: {user.is_active}')
            self.stdout.write(f'  是否超级用户: {user.is_superuser}')
            self.stdout.write(f'  所属组: {[g.name for g in user.groups.all()]}')

            # 检查关键权限
            key_permissions = [
                'plan_management.view_plan',
                'plan_management.view_strategicgoal',
                'plan_management.add_plan',
                'plan_management.change_plan',
                'plan_management.approve_plan',
            ]

            self.stdout.write('\n  权限检查:')
            user_passed = True
            for perm in key_permissions:
                has_perm = user.has_perm(perm)
                status = '✓' if has_perm else '✗'
                color = self.style.SUCCESS if has_perm else self.style.ERROR
                self.stdout.write(color(f'    {status} {perm}: {has_perm}'))
                if not has_perm:
                    user_passed = False
                    all_passed = False

            # 检查 require_perm 函数（模拟）
            self.stdout.write('\n  require_perm 检查（模拟）:')
            try:
                from backend.apps.plan_management.views_pages import require_perm
                require_perm(user, "plan_management.view_plan")
                self.stdout.write(self.style.SUCCESS('    ✓ require_perm("plan_management.view_plan"): 通过'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'    ✗ require_perm("plan_management.view_plan"): 失败 - {e}'))
                user_passed = False
                all_passed = False

            if user_passed:
                self.stdout.write(self.style.SUCCESS(f'\n  ✓ 用户 {user.username} 权限验证通过'))
            else:
                self.stdout.write(self.style.ERROR(f'\n  ✗ 用户 {user.username} 权限验证失败'))

        # 总结
        self.stdout.write('')
        self.stdout.write('=' * 60)
        if all_passed:
            self.stdout.write(self.style.SUCCESS('✅ 所有用户权限验证通过'))
        else:
            self.stdout.write(self.style.ERROR('❌ 部分用户权限验证失败'))
        self.stdout.write('=' * 60)

        # 提示
        self.stdout.write('\n提示：')
        self.stdout.write('  1. 请使用总经理账号登录系统')
        self.stdout.write('  2. 访问 /plan/dashboard/ 或 /plan/plans/ 确认可以正常访问（200）')
        self.stdout.write('  3. 使用无权限用户访问确认仍返回 403')

