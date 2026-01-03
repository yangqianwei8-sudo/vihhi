from django.core.management.base import BaseCommand
from django.db import transaction
from backend.apps.permission_management.models import PermissionItem
from backend.apps.system_management.models import Role


class Command(BaseCommand):
    help = '删除所有废弃的权限（customer_success.* 等）'

    # 要删除的废弃权限代码前缀
    DEPRECATED_PREFIXES = [
        'customer_success.',  # 客户管理旧权限
    ]

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='仅显示将要删除的权限，不实际删除',
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)
        
        if dry_run:
            self.stdout.write(self.style.WARNING('🔍 模拟运行模式（不会实际删除）\n'))
        else:
            self.stdout.write(self.style.WARNING('⚠️  警告：将删除所有废弃权限！\n'))
        
        # 查找所有废弃权限（按前缀过滤）
        filtered_perms = []
        for prefix in self.DEPRECATED_PREFIXES:
            perms = PermissionItem.objects.filter(
                code__startswith=prefix,
                is_active=False
            )
            filtered_perms.extend(list(perms))
        
        if not filtered_perms:
            self.stdout.write(self.style.SUCCESS('✓ 没有找到需要删除的废弃权限'))
            return
        
        self.stdout.write(f'找到 {len(filtered_perms)} 个废弃权限：\n')
        
        # 统计角色关联
        role_counts = {}
        for perm in filtered_perms:
            count = Role.objects.filter(custom_permissions=perm, is_active=True).count()
            role_counts[perm.code] = count
            status = f'({count} 个角色)' if count > 0 else '(无角色关联)'
            self.stdout.write(f'  - {perm.code} - {perm.name} {status}')
        
        total_role_relations = sum(role_counts.values())
        if total_role_relations > 0:
            self.stdout.write(
                self.style.WARNING(
                    f'\n⚠️  警告：这些权限关联了 {total_role_relations} 个角色关系，删除后这些关联将丢失！'
                )
            )
        
        if dry_run:
            self.stdout.write(
                self.style.SUCCESS(
                    f'\n模拟运行完成：将删除 {len(filtered_perms)} 个权限'
                )
            )
            return
        
        # 确认删除
        confirm = input('\n确认删除？(yes/no): ')
        if confirm.lower() != 'yes':
            self.stdout.write(self.style.WARNING('已取消删除操作'))
            return
        
        # 执行删除
        with transaction.atomic():
            deleted_count = 0
            role_relations_removed = 0
            
            for perm in filtered_perms:
                # 统计角色关联
                roles = Role.objects.filter(custom_permissions=perm, is_active=True)
                role_count = roles.count()
                
                # 从角色中移除权限关联
                for role in roles:
                    role.custom_permissions.remove(perm)
                    role_relations_removed += 1
                
                # 删除权限
                perm.delete()
                deleted_count += 1
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'  ✓ 删除权限: {perm.code} (移除了 {role_count} 个角色关联)'
                    )
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n✅ 删除完成！\n'
                f'  删除权限: {deleted_count} 个\n'
                f'  移除角色关联: {role_relations_removed} 个'
            )
        )
        
        # 验证删除结果
        remaining = PermissionItem.objects.filter(
            code__startswith='customer_success.',
            is_active=False
        ).count()
        
        if remaining == 0:
            self.stdout.write(
                self.style.SUCCESS(
                    f'\n✓ 验证通过：所有废弃的 customer_success.* 权限已删除'
                )
            )
        else:
            self.stdout.write(
                self.style.WARNING(
                    f'\n⚠️  仍有 {remaining} 个 customer_success.* 权限存在'
                )
            )

