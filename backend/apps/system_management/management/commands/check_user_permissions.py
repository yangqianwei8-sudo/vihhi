"""
检查用户权限的诊断工具

使用方法：
    python manage.py check_user_permissions tester1
"""
from django.core.management.base import BaseCommand
from backend.apps.system_management.models import User
from backend.apps.system_management.services import get_user_permission_codes
from backend.core.views import _permission_granted


class Command(BaseCommand):
    help = "检查用户权限配置"

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='要检查的用户名')

    def handle(self, *args, **options):
        username = options['username']
        
        user = User.objects.filter(username=username).first()
        if not user:
            self.stdout.write(self.style.ERROR(f'用户 {username} 不存在'))
            return
        
        self.stdout.write(self.style.SUCCESS(f'\n检查用户: {username} ({user.get_full_name()})'))
        self.stdout.write('=' * 70)
        
        # 检查角色
        roles = user.roles.filter(is_active=True)
        self.stdout.write(f'\n角色 ({roles.count()} 个):')
        if roles.exists():
            for role in roles:
                self.stdout.write(f'  - {role.name} ({role.code})')
        else:
            self.stdout.write(self.style.WARNING('  无角色'))
        
        # 获取权限
        permission_set = get_user_permission_codes(user)
        
        # 检查计划管理权限
        plan_permissions = [p for p in permission_set if p.startswith('plan_management')]
        self.stdout.write(f'\n计划管理权限 ({len(plan_permissions)} 个):')
        if plan_permissions:
            for perm in sorted(plan_permissions):
                self.stdout.write(f'  ✓ {perm}')
        else:
            self.stdout.write(self.style.ERROR('  ✗ 无计划管理权限'))
        
        # 测试权限检查
        self.stdout.write('\n权限检查测试:')
        test_permissions = [
            'plan_management.view',
            'plan_management.plan.view',
            'plan_management.goal.view',
            'plan_management.approve',
        ]
        
        for perm in test_permissions:
            result = _permission_granted(perm, permission_set)
            status = self.style.SUCCESS('✓') if result else self.style.ERROR('✗')
            self.stdout.write(f'  {status} {perm}: {result}')
        
        # 诊断建议
        self.stdout.write('\n' + '=' * 70)
        self.stdout.write('诊断建议:')
        self.stdout.write('=' * 70)
        
        if not plan_permissions:
            self.stdout.write(self.style.ERROR('\n✗ 用户没有计划管理权限'))
            self.stdout.write('  解决方案: 给用户分配包含计划管理权限的角色')
        else:
            has_view = 'plan_management.view' in permission_set
            if has_view:
                self.stdout.write(self.style.SUCCESS('\n✓ 用户有 plan_management.view 权限'))
                self.stdout.write('\n如果仍然提示无权限，请尝试:')
                self.stdout.write('  1. 让用户重新登录（清除会话缓存）')
                self.stdout.write('  2. 清除浏览器缓存（Ctrl+F5 强制刷新）')
                self.stdout.write('  3. 检查是否在其他页面（非首页）提示无权限')
            else:
                self.stdout.write(self.style.WARNING('\n⚠ 用户没有 plan_management.view 权限'))
                self.stdout.write('  但有其他计划管理权限，可能需要分配包含view权限的角色')
        
        self.stdout.write('\n' + '=' * 70)
