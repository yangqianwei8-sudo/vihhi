from django.core.management.base import BaseCommand
from django.db import transaction
from backend.apps.permission_management.models import PermissionItem
from backend.apps.system_management.models import Role


class Command(BaseCommand):
    help = '为客户管理角色设置分级查看权限'

    # 角色与权限的映射
    ROLE_PERMISSION_MAP = {
        # 商务经理（普通员工）：只能查看本人负责的
        'business_manager': [
            'customer_management.client.view_assigned',
            'customer_management.client.create',
            'customer_management.client.edit',  # 仅限自己负责的客户
        ],
        # 商务部经理（部门经理）：可以查看本部门的
        'business_team': [
            'customer_management.client.view_department',
            'customer_management.client.view_all',  # 也可以查看全部
            'customer_management.client.create',
            'customer_management.client.edit',
        ],
        # 总经理：可以查看全部
        'general_manager': [
            'customer_management.client.view_all',
            'customer_management.client.create',
            'customer_management.client.edit',
            'customer_management.client.delete',
            'customer_management.client.export',
        ],
    }

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='仅显示将要设置的权限，不实际设置',
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)
        
        if dry_run:
            self.stdout.write(self.style.WARNING('🔍 模拟运行模式（不会实际设置）\n'))
        else:
            self.stdout.write(self.style.SUCCESS('开始设置客户查看权限...\n'))
        
        with transaction.atomic():
            for role_code, permission_codes in self.ROLE_PERMISSION_MAP.items():
                try:
                    role = Role.objects.get(code=role_code, is_active=True)
                    self.stdout.write(f'\n角色: {role.name} ({role_code})')
                    
                    # 获取权限对象
                    permissions = []
                    for perm_code in permission_codes:
                        try:
                            perm = PermissionItem.objects.get(code=perm_code, is_active=True)
                            permissions.append(perm)
                            self.stdout.write(f'  ✓ {perm_code} - {perm.name}')
                        except PermissionItem.DoesNotExist:
                            self.stdout.write(
                                self.style.WARNING(f'  ⚠ 权限不存在: {perm_code}')
                            )
                    
                    if not dry_run:
                        # 添加权限到角色
                        role.custom_permissions.add(*permissions)
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'  → 已为角色 "{role.name}" 分配 {len(permissions)} 个权限'
                            )
                        )
                    else:
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'  → 将为角色 "{role.name}" 分配 {len(permissions)} 个权限'
                            )
                        )
                        
                except Role.DoesNotExist:
                    self.stdout.write(
                        self.style.WARNING(f'  ⚠ 角色不存在: {role_code}')
                    )
        
        if not dry_run:
            self.stdout.write(
                self.style.SUCCESS('\n✅ 权限设置完成！')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS('\n✅ 模拟运行完成！使用 --dry-run=false 实际设置权限')
            )
        
        # 显示当前权限分配情况
        self.stdout.write('\n当前权限分配情况:')
        for role_code, permission_codes in self.ROLE_PERMISSION_MAP.items():
            try:
                role = Role.objects.get(code=role_code, is_active=True)
                assigned_perms = role.custom_permissions.filter(
                    code__in=permission_codes,
                    is_active=True
                )
                self.stdout.write(
                    f'  {role.name}: {assigned_perms.count()}/{len(permission_codes)} 个权限'
                )
            except Role.DoesNotExist:
                pass

