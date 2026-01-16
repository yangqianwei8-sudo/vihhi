"""
限制管理后台访问权限

只允许admin用户访问Django管理后台，其他用户均拒绝访问。

使用方法：
    python manage.py restrict_admin_access
    python manage.py restrict_admin_access --dry-run  # 预览模式
"""
from django.core.management.base import BaseCommand
from django.db import transaction

from backend.apps.system_management.models import User


class Command(BaseCommand):
    help = "限制管理后台访问权限，只允许admin用户访问"

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='预览将要执行的操作，不实际修改数据库',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        if dry_run:
            self.stdout.write(self.style.WARNING('=== 预览模式（不会实际修改数据库）===\n'))

        # 查找admin用户
        admin_user = User.objects.filter(username='admin').first()
        
        if not admin_user:
            self.stdout.write(
                self.style.ERROR('⚠ 警告：未找到admin用户！')
            )
            self.stdout.write(
                self.style.WARNING('  建议：请先创建admin用户或确认admin用户名是否正确')
            )
            return

        # 确保admin用户有访问权限
        admin_needs_update = False
        if not admin_user.is_staff:
            admin_needs_update = True
            if not dry_run:
                admin_user.is_staff = True
                admin_user.save(update_fields=['is_staff'])
            self.stdout.write(
                self.style.SUCCESS(f'✓ 设置admin用户 is_staff=True')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f'✓ admin用户已有访问权限 (is_staff=True)')
            )

        # 查找所有非admin用户且is_staff=True的用户
        non_admin_staff_users = User.objects.filter(
            is_staff=True
        ).exclude(username='admin')

        affected_count = non_admin_staff_users.count()

        if affected_count == 0:
            self.stdout.write(
                self.style.SUCCESS('\n✓ 没有需要修改的用户，所有非admin用户的is_staff已经是False')
            )
        else:
            self.stdout.write(
                self.style.WARNING(f'\n找到 {affected_count} 个需要修改的用户：')
            )
            
            for user in non_admin_staff_users[:20]:  # 只显示前20个
                self.stdout.write(f'  - {user.username} (is_staff=True)')

            if affected_count > 20:
                self.stdout.write(f'  ... 还有 {affected_count - 20} 个用户')

            if not dry_run:
                with transaction.atomic():
                    updated_count = non_admin_staff_users.update(is_staff=False)
                    self.stdout.write(
                        self.style.SUCCESS(f'\n✓ 已更新 {updated_count} 个用户的is_staff=False')
                    )
            else:
                self.stdout.write(
                    self.style.WARNING(f'\n预览：将更新 {affected_count} 个用户的is_staff=False')
                )

        # 验证结果
        if not dry_run:
            self.stdout.write('\n' + '=' * 60)
            self.stdout.write('验证结果：')
            self.stdout.write('=' * 60)
            
            total_staff = User.objects.filter(is_staff=True).count()
            admin_staff = User.objects.filter(username='admin', is_staff=True).count()
            
            if total_staff == admin_staff == 1:
                self.stdout.write(
                    self.style.SUCCESS(f'✓ 成功！现在只有admin用户可以访问管理后台')
                )
                self.stdout.write(f'  - is_staff=True的用户数: {total_staff}')
                self.stdout.write(f'  - admin用户is_staff: {admin_staff > 0}')
            else:
                self.stdout.write(
                    self.style.WARNING(f'⚠ 注意：is_staff=True的用户数: {total_staff}')
                )
                if total_staff > 1:
                    other_staff = User.objects.filter(is_staff=True).exclude(username='admin')
                    self.stdout.write(
                        self.style.ERROR(f'  仍有 {other_staff.count()} 个非admin用户is_staff=True')
                    )
                    for user in other_staff[:5]:
                        self.stdout.write(f'    - {user.username}')
        else:
            self.stdout.write(
                self.style.WARNING('\n=== 预览模式：未实际修改数据库 ===')
            )
