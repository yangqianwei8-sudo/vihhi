"""
批量重置所有用户密码

将所有用户的密码统一修改为指定密码。

使用方法：
    python manage.py reset_all_passwords T159357
    python manage.py reset_all_passwords T159357 --dry-run  # 预览模式
"""
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.contrib.auth.hashers import make_password

from backend.apps.system_management.models import User


class Command(BaseCommand):
    help = "批量重置所有用户密码"

    def add_arguments(self, parser):
        parser.add_argument(
            'password',
            type=str,
            help='要设置的新密码（明文）',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='预览将要执行的操作，不实际修改数据库',
        )
        parser.add_argument(
            '--exclude-admin',
            action='store_true',
            help='排除admin用户，不修改admin用户的密码',
        )

    def handle(self, *args, **options):
        new_password = options['password']
        dry_run = options['dry_run']
        exclude_admin = options['exclude_admin']

        if not new_password:
            raise CommandError('必须提供新密码')

        if len(new_password) < 6:
            self.stdout.write(
                self.style.WARNING('⚠ 警告：密码长度少于6个字符，可能不符合安全要求')
            )

        if dry_run:
            self.stdout.write(self.style.WARNING('=== 预览模式（不会实际修改数据库）===\n'))

        # 构建查询
        queryset = User.objects.all()
        if exclude_admin:
            queryset = queryset.exclude(username='admin')
            self.stdout.write(self.style.WARNING('⚠ 将排除admin用户\n'))

        total_users = queryset.count()

        if total_users == 0:
            self.stdout.write(self.style.WARNING('没有找到需要修改的用户'))
            return

        self.stdout.write(f'找到 {total_users} 个用户需要修改密码\n')

        # 显示将要修改的用户列表
        users_to_update = queryset[:20]  # 只显示前20个
        self.stdout.write('将要修改密码的用户：')
        for user in users_to_update:
            status = ''
            if user.username == 'admin':
                status = ' (admin)'
            elif not user.is_active:
                status = ' (已停用)'
            self.stdout.write(f'  - {user.username}{status}')

        if total_users > 20:
            self.stdout.write(f'  ... 还有 {total_users - 20} 个用户')

        # 确认操作
        if not dry_run:
            self.stdout.write(
                self.style.WARNING(f'\n⚠ 警告：即将修改 {total_users} 个用户的密码为: {new_password}')
            )
            self.stdout.write(
                self.style.WARNING('   请确认这是您想要的操作！')
            )

        # 执行更新
        if not dry_run:
            # 生成密码哈希
            password_hash = make_password(new_password)

            with transaction.atomic():
                updated_count = queryset.update(password=password_hash)
                self.stdout.write(
                    self.style.SUCCESS(f'\n✓ 已成功更新 {updated_count} 个用户的密码')
                )
        else:
            self.stdout.write(
                self.style.WARNING(f'\n预览：将更新 {total_users} 个用户的密码')
            )

        # 验证结果
        if not dry_run:
            self.stdout.write('\n' + '=' * 60)
            self.stdout.write('验证结果：')
            self.stdout.write('=' * 60)

            # 测试密码是否正确设置（通过尝试验证）
            test_user = queryset.first()
            if test_user:
                from django.contrib.auth import authenticate
                # 重新从数据库加载用户（获取最新密码）
                test_user.refresh_from_db()
                # 验证密码
                authenticated_user = authenticate(
                    username=test_user.username,
                    password=new_password
                )
                if authenticated_user:
                    self.stdout.write(
                        self.style.SUCCESS(f'✓ 密码验证成功（测试用户: {test_user.username}）')
                    )
                else:
                    self.stdout.write(
                        self.style.ERROR(f'✗ 密码验证失败（测试用户: {test_user.username}）')
                    )
                    self.stdout.write(
                        self.style.WARNING('   请检查密码设置是否正确')
                    )

            self.stdout.write(f'\n✓ 密码重置完成！所有用户的新密码为: {new_password}')
            if exclude_admin:
                self.stdout.write('  （admin用户密码未修改）')
        else:
            self.stdout.write(
                self.style.WARNING('\n=== 预览模式：未实际修改数据库 ===')
            )
