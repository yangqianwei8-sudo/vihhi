"""
验证统一权限系统是否正常工作
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from backend.core.permissions import has_perm2, require_perm

User = get_user_model()


class Command(BaseCommand):
    help = '验证统一权限系统是否正常工作'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            help='指定用户名（不指定则测试总经理和tester1）'
        )

    def handle(self, *args, **options):
        username = options.get('username')
        
        if username:
            users = [User.objects.get(username=username)]
        else:
            # 测试总经理和tester1
            users = User.objects.filter(username__in=['13880399996', 'tester1'], is_active=True)
        
        self.stdout.write('=' * 60)
        self.stdout.write('验证统一权限系统')
        self.stdout.write('=' * 60)
        self.stdout.write('')
        
        # 使用标准业务权限进行测试
        test_permissions = [
            'plan_management.view',  # 标准权限（菜单系统使用）
            'plan_management.plan.view',  # 业务权限（查看计划）
            'plan_management.goal.view',  # 业务权限（查看目标）
            'plan_management.plan.create',  # 业务权限（创建计划）
        ]
        
        for user in users:
            self.stdout.write(f'\n用户: {user.username}')
            self.stdout.write(f'  is_superuser: {user.is_superuser}')
            self.stdout.write(f'  所属组: {[g.name for g in user.groups.all()]}')
            
            self.stdout.write('\n  has_perm2 检查:')
            all_passed = True
            for perm in test_permissions:
                result = has_perm2(user, perm)
                status = '✓' if result else '✗'
                color = self.style.SUCCESS if result else self.style.ERROR
                self.stdout.write(color(f'    {status} {perm}: {result}'))
                if not result:
                    all_passed = False
            
            self.stdout.write('\n  require_perm 检查:')
            try:
                require_perm(user, 'plan_management.plan.view')
                self.stdout.write(self.style.SUCCESS('    ✓ require_perm("plan_management.plan.view"): 通过'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'    ✗ require_perm("plan_management.plan.view") 失败: {e}'))
                all_passed = False
            
            if all_passed:
                self.stdout.write(self.style.SUCCESS(f'\n  ✅ 用户 {user.username} 权限验证通过'))
            else:
                self.stdout.write(self.style.ERROR(f'\n  ❌ 用户 {user.username} 权限验证失败'))
        
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write('验证完成')
        self.stdout.write('=' * 60)

