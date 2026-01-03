from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.db import transaction
from backend.apps.system_management.models import Role

User = get_user_model()


class Command(BaseCommand):
    help = '设置admin账户为系统管理员并授予全部权限'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            default='admin',
            help='要设置的用户名（默认：admin）',
        )

    def handle(self, *args, **options):
        username = options['username']
        
        self.stdout.write(f'正在检查并设置用户 "{username}" 的权限...')
        
        try:
            with transaction.atomic():
                # 获取或创建用户
                user, created = User.objects.get_or_create(
                    username=username,
                    defaults={
                        'email': f'{username}@system.local',
                        'is_active': True,
                        'is_staff': True,
                        'is_superuser': True,
                    }
                )
                
                if created:
                    self.stdout.write(
                        self.style.WARNING(f'⚠ 用户 "{username}" 不存在，已创建新用户')
                    )
                    # 设置默认密码（建议首次登录后修改）
                    user.set_password('admin123456')
                    user.save()
                    self.stdout.write(
                        self.style.WARNING('⚠ 默认密码已设置为: admin123456，请尽快修改！')
                    )
                else:
                    self.stdout.write(f'✓ 找到用户: {user.username}')
                
                # 记录原始状态
                was_superuser = user.is_superuser
                was_staff = user.is_staff
                was_active = user.is_active
                
                # 设置全部权限标志
                user.is_superuser = True
                user.is_staff = True
                user.is_active = True
                user.save()
                
                # 显示变更信息
                changes = []
                if not was_superuser:
                    changes.append('超级用户权限')
                if not was_staff:
                    changes.append('员工权限')
                if not was_active:
                    changes.append('激活状态')
                
                if changes:
                    self.stdout.write(
                        self.style.SUCCESS(f'✓ 已设置: {", ".join(changes)}')
                    )
                else:
                    self.stdout.write('✓ 用户已拥有所有基本权限标志')
                
                # 分配所有Django权限（虽然is_superuser已经包含，但明确分配更清晰）
                all_permissions = Permission.objects.all()
                user.user_permissions.set(all_permissions)
                self.stdout.write(
                    self.style.SUCCESS(f'✓ 已分配所有Django权限（共 {all_permissions.count()} 个）')
                )
                
                # 尝试分配system_admin角色（如果存在）
                try:
                    system_admin_role = Role.objects.get(code='system_admin', is_active=True)
                    if system_admin_role not in user.roles.all():
                        user.roles.add(system_admin_role)
                        self.stdout.write(
                            self.style.SUCCESS(f'✓ 已分配角色: {system_admin_role.name} ({system_admin_role.code})')
                        )
                    else:
                        self.stdout.write(
                            f'✓ 用户已拥有角色: {system_admin_role.name}'
                        )
                except Role.DoesNotExist:
                    self.stdout.write(
                        self.style.WARNING('⚠ system_admin 角色不存在，跳过角色分配')
                    )
                    # 可选：创建system_admin角色
                    self.stdout.write('   提示：可以运行 seed_org_structure 命令来创建系统角色')
                
                # 尝试分配general_manager角色（如果存在）
                try:
                    general_manager_role = Role.objects.get(code='general_manager', is_active=True)
                    if general_manager_role not in user.roles.all():
                        user.roles.add(general_manager_role)
                        self.stdout.write(
                            self.style.SUCCESS(f'✓ 已分配角色: {general_manager_role.name} ({general_manager_role.code})')
                        )
                except Role.DoesNotExist:
                    pass  # general_manager角色不存在也没关系
                
                # 显示最终状态
                self.stdout.write('\n' + '='*60)
                self.stdout.write(self.style.SUCCESS('权限设置完成！'))
                self.stdout.write('='*60)
                self.stdout.write(f'用户名: {user.username}')
                self.stdout.write(f'是否激活: {user.is_active}')
                self.stdout.write(f'是否员工: {user.is_staff}')
                self.stdout.write(f'是否超级用户: {user.is_superuser}')
                self.stdout.write(f'Django权限数: {user.user_permissions.count()}')
                self.stdout.write(f'业务角色数: {user.roles.count()}')
                
                if user.roles.exists():
                    role_names = ', '.join([f'{r.name}({r.code})' for r in user.roles.all()])
                    self.stdout.write(f'业务角色: {role_names}')
                
                self.stdout.write('\n根据权限检查逻辑：')
                self.stdout.write('  - is_superuser=True → 拥有全部业务权限 (__all__)')
                if user.roles.filter(code__in=['system_admin', 'general_manager']).exists():
                    self.stdout.write('  - 拥有 system_admin 或 general_manager 角色 → 拥有全部业务权限')
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ 设置权限时发生错误: {str(e)}')
            )
            raise


