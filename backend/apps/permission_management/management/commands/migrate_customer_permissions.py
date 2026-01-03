from django.core.management.base import BaseCommand
from django.db import transaction
from backend.apps.permission_management.models import PermissionItem
from backend.apps.system_management.models import Role


class Command(BaseCommand):
    help = '迁移客户管理权限代码，从 customer_success.* 迁移到 customer_management.*'

    # 权限代码映射：旧代码 -> 新代码
    PERMISSION_MAPPING = {
        # 客户信息管理
        'customer_success.view': 'customer_management.client.view',
        'customer_success.manage': 'customer_management.client.edit',  # manage 映射到 edit
        # 客户人员管理
        'customer_success.contact.view': 'customer_management.contact.view',
        'customer_success.contact.manage': 'customer_management.contact.edit',  # manage 映射到 edit
        # 客户关系管理
        'customer_success.relationship.view': 'customer_management.relationship.view',
        'customer_success.relationship.manage': 'customer_management.relationship.edit',  # manage 映射到 edit
        # 客户公海
        'customer_success.public_sea.view': 'customer_management.public_sea.view',
        'customer_success.public_sea.claim': 'customer_management.public_sea.claim',
        # 客户分析
        'customer_success.analyze': 'customer_management.analysis.view',
    }

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('开始迁移客户管理权限代码...\n'))
        
        with transaction.atomic():
            migrated_count = 0
            role_updated_count = 0
            
            for old_code, new_code in self.PERMISSION_MAPPING.items():
                try:
                    old_perm = PermissionItem.objects.get(code=old_code)
                    new_perm, created = PermissionItem.objects.get_or_create(
                        code=new_code,
                        defaults={
                            'module': old_perm.module,
                            'action': new_code.split('.')[-1],
                            'name': old_perm.name.replace('（已废弃）', '').replace('已废弃，', ''),
                            'description': old_perm.description.replace('已废弃，', ''),
                            'is_active': True,
                        }
                    )
                    
                    if not created:
                        # 如果新权限已存在，更新描述
                        new_perm.description = old_perm.description.replace('已废弃，', '')
                        new_perm.is_active = True
                        new_perm.save()
                    
                    # 迁移角色关联：将所有使用旧权限的角色关联到新权限
                    roles_with_old_perm = Role.objects.filter(custom_permissions=old_perm, is_active=True)
                    for role in roles_with_old_perm:
                        if new_perm not in role.custom_permissions.all():
                            role.custom_permissions.add(new_perm)
                            role_updated_count += 1
                    
                    # 标记旧权限为已废弃
                    old_perm.is_active = False
                    old_perm.description = f"已废弃，请使用 {new_code}"
                    old_perm.name = f"{old_perm.name}（已废弃）"
                    old_perm.save()
                    
                    migrated_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'  ✓ {old_code} -> {new_code}'
                        )
                    )
                    
                except PermissionItem.DoesNotExist:
                    self.stdout.write(
                        self.style.WARNING(
                            f'  - 权限 {old_code} 不存在，跳过'
                        )
                    )
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(
                            f'  ✗ 迁移 {old_code} 时出错: {str(e)}'
                        )
                    )
            
            # 统计信息
            self.stdout.write(
                self.style.SUCCESS(
                    f'\n迁移完成！\n'
                    f'  迁移权限: {migrated_count} 个\n'
                    f'  更新角色关联: {role_updated_count} 个'
                )
            )
            
            # 显示新权限统计
            new_perms = PermissionItem.objects.filter(
                code__startswith='customer_management.',
                is_active=True
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f'\n新的客户管理权限 ({new_perms.count()} 个):'
                )
            )
            for perm in new_perms.order_by('code'):
                role_count = Role.objects.filter(custom_permissions=perm, is_active=True).count()
                self.stdout.write(f'  ✓ {perm.code} - {perm.name} ({role_count} 个角色)')

