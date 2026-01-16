"""
管理命令：为系统管理员（超级用户）授予所有权限

使用方法:
    python manage.py grant_all_permissions_to_admin [username]
    
如果不指定用户名，将为所有超级用户授予权限。
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = '为系统管理员（超级用户）授予所有权限（确保is_superuser=True）'

    def add_arguments(self, parser):
        parser.add_argument(
            'username',
            nargs='?',
            type=str,
            help='要设置权限的用户名（可选，如果不指定则处理所有超级用户）',
        )

    def handle(self, *args, **options):
        username = options.get('username')
        
        if username:
            try:
                user = User.objects.get(username=username)
                if user.is_superuser:
                    user.is_staff = True
                    user.is_superuser = True
                    user.save()
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'成功设置用户 "{username}" 为超级管理员（is_superuser=True, is_staff=True）'
                        )
                    )
                else:
                    # 询问是否要设置为超级用户
                    user.is_staff = True
                    user.is_superuser = True
                    user.save()
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'已将用户 "{username}" 设置为超级管理员（is_superuser=True, is_staff=True）'
                        )
                    )
            except User.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'用户 "{username}" 不存在')
                )
        else:
            # 处理所有超级用户
            superusers = User.objects.filter(is_superuser=True)
            count = 0
            for user in superusers:
                if not user.is_staff:
                    user.is_staff = True
                    user.save()
                    count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f'用户 "{user.username}" 已确认为超级管理员（is_superuser=True, is_staff=True）'
                    )
                )
            
            if count > 0:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'共为 {count} 个用户启用了 is_staff 标志'
                    )
                )
            
            if superusers.count() == 0:
                self.stdout.write(
                    self.style.WARNING('未找到任何超级用户')
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'共处理了 {superusers.count()} 个超级用户'
                    )
                )


