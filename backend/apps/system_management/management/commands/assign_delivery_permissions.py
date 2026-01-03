"""
给用户分配发文管理（交付客户）的全部权限
用法: python manage.py assign_delivery_permissions <username>
"""
from django.core.management.base import BaseCommand, CommandError
from backend.apps.system_management.models import User
from backend.apps.permission_management.models import PermissionItem
from backend.apps.system_management.models import Role


class Command(BaseCommand):
    help = '给用户分配发文管理（交付客户）的全部权限'

    def add_arguments(self, parser):
        parser.add_argument(
            'username',
            type=str,
            help='用户名（可以是用户名、姓名的一部分）'
        )

    def handle(self, *args, **options):
        username = options['username']
        
        # 查找用户
        from django.db.models import Q
        user = User.objects.filter(
            Q(username__icontains=username) |
            Q(first_name__icontains=username) |
            Q(last_name__icontains=username)
        ).first()
        
        if not user:
            self.stdout.write(self.style.ERROR(f'未找到用户: {username}'))
            self.stdout.write('\n可用的用户列表:')
            for u in User.objects.all().order_by('username')[:20]:
                name = u.get_full_name() or u.first_name or u.last_name or '无姓名'
                self.stdout.write(f'  - {u.username}: {name}')
            return
        
        self.stdout.write(f'找到用户: {user.username} ({user.get_full_name() or user.first_name or user.last_name or "无姓名"})')
        
        # 查找所有交付客户（发文管理）相关的权限
        permissions = PermissionItem.objects.filter(
            module='交付客户',
            is_active=True
        )
        
        if not permissions.exists():
            self.stdout.write(self.style.ERROR('未找到交付客户相关的权限'))
            return
        
        self.stdout.write(f'\n找到 {permissions.count()} 个交付客户相关权限:')
        for perm in permissions:
            self.stdout.write(f'  - {perm.code}: {perm.name}')
        
        # 获取用户的所有角色
        user_roles = user.roles.all()
        if not user_roles.exists():
            self.stdout.write(self.style.WARNING(f'\n用户 {user.username} 没有分配任何角色'))
            self.stdout.write('建议先给用户分配角色，然后通过角色来管理权限')
            return
        
        # 给用户的所有角色分配这些权限
        updated_roles = []
        for role in user_roles:
            # 获取角色当前已有的业务权限
            role_permissions = set(role.custom_permissions.values_list('code', flat=True))
            
            # 添加新的权限
            new_permissions = set(perm.code for perm in permissions)
            all_permissions = role_permissions | new_permissions
            
            # 更新角色的业务权限
            role.custom_permissions.set(
                PermissionItem.objects.filter(code__in=all_permissions)
            )
            updated_roles.append(role.name)
        
        self.stdout.write(self.style.SUCCESS(f'\n✓ 已为用户 {user.username} 的所有角色分配交付客户权限'))
        self.stdout.write(f'  更新的角色: {", ".join(updated_roles)}')
        self.stdout.write(f'  分配的权限数量: {permissions.count()}')

