from django.core.management.base import BaseCommand
from django.db import transaction
from backend.apps.permission_management.models import PermissionItem


class Command(BaseCommand):
    help = '同步更新权限点的模块名称，将旧模块名称更新为新名称'

    MODULE_MAPPING = {
        # 旧模块名称 -> 新模块名称
        '项目中心': '生产管理',
        '结算中心': '结算管理',
        # 客户成功模块拆分映射（需要根据权限代码进一步细分）
        # 注意：客户成功模块需要根据权限代码细分到客户管理、商机管理、合同管理
        # 这个映射只处理通用的客户成功权限，具体细分在 handle 方法中处理
    }
    
    # 客户成功模块的细分映射（根据权限代码）
    CUSTOMER_SUCCESS_MAPPING = {
        # 客户管理相关权限
        'customer_success.manage': '客户管理',
        'customer_success.view': '客户管理',
        'customer_success.contact.': '客户管理',  # contact相关
        'customer_success.relationship.': '客户管理',  # relationship相关
        'customer_success.public_sea.': '客户管理',  # public_sea相关
        'customer_success.analyze': '客户管理',
        # 商机管理相关权限
        'customer_success.opportunity': '商机管理',
        'customer_success.opportunity.': '商机管理',  # opportunity相关
        'customer_success.quotation.': '商机管理',  # quotation相关
        # 合同管理相关权限
        'customer_success.contract.': '合同管理',  # contract相关
    }

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('开始同步更新权限点模块名称...'))
        
        with transaction.atomic():
            updated_count = 0
            
            # 更新模块字段（通用映射）
            for old_module, new_module in self.MODULE_MAPPING.items():
                count = PermissionItem.objects.filter(module=old_module).count()
                if count > 0:
                    updated = PermissionItem.objects.filter(module=old_module).update(module=new_module)
                    if updated > 0:
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'  ✓ 更新模块 "{old_module}" -> "{new_module}": {updated} 个权限点'
                            )
                        )
                        updated_count += updated
                else:
                    self.stdout.write(
                        self.style.WARNING(
                            f'  - 模块 "{old_module}" 没有找到需要更新的权限点'
                        )
                    )
            
            # 处理客户成功模块的细分
            customer_success_perms = PermissionItem.objects.filter(module='客户成功')
            if customer_success_perms.exists():
                self.stdout.write(self.style.SUCCESS('\n处理客户成功模块的细分...'))
                for perm in customer_success_perms:
                    new_module = None
                    # 根据权限代码确定新模块
                    for code_prefix, target_module in self.CUSTOMER_SUCCESS_MAPPING.items():
                        if perm.code.startswith(code_prefix):
                            new_module = target_module
                            break
                    
                    if new_module:
                        perm.module = new_module
                        perm.save()
                        updated_count += 1
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'  ✓ 更新权限 "{perm.code}": 客户成功 -> {new_module}'
                            )
                        )
                    else:
                        # 如果没有匹配的映射，默认归到客户管理
                        perm.module = '客户管理'
                        perm.save()
                        updated_count += 1
                        self.stdout.write(
                            self.style.WARNING(
                                f'  ⚠ 更新权限 "{perm.code}": 客户成功 -> 客户管理（默认）'
                            )
                        )
            
            # 删除已废弃模块的权限点（迁移完成后删除残留数据）
            deprecated_modules = ['项目中心', '结算中心', '客户成功']
            deleted_count = 0
            for deprecated_module in deprecated_modules:
                remaining = PermissionItem.objects.filter(module=deprecated_module).count()
                if remaining > 0:
                    deleted = PermissionItem.objects.filter(module=deprecated_module).delete()[0]
                    deleted_count += deleted
                    self.stdout.write(
                        self.style.WARNING(
                            f'  ⚠️  删除已废弃模块 "{deprecated_module}" 的 {deleted} 个权限点'
                        )
                    )
            
            if deleted_count > 0:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'\n✓ 已删除 {deleted_count} 个已废弃模块的权限点'
                    )
                )
            
            # 检查当前所有模块
            all_modules = PermissionItem.objects.values_list('module', flat=True).distinct()
            self.stdout.write(
                self.style.SUCCESS(
                    f'\n当前数据库中的模块列表: {", ".join(sorted(all_modules))}'
                )
            )
            
            # 统计各模块的权限数量
            module_counts = {}
            for module in all_modules:
                count = PermissionItem.objects.filter(module=module).count()
                module_counts[module] = count
            
            self.stdout.write(self.style.SUCCESS('\n各模块权限数量统计:'))
            for module, count in sorted(module_counts.items()):
                self.stdout.write(f'  ✓ {module}: {count} 个权限点')
            
            # 验证所有模块是否都在 MODULE_CHOICES 中
            valid_modules = [choice[0] for choice in PermissionItem.MODULE_CHOICES]
            invalid_modules = [m for m in all_modules if m not in valid_modules]
            if invalid_modules:
                self.stdout.write(
                    self.style.ERROR(
                        f'\n❌ 错误：发现不在 MODULE_CHOICES 中的模块: {", ".join(sorted(invalid_modules))}'
                    )
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'\n✓ 所有模块都在 MODULE_CHOICES 中，同步完成！'
                    )
                )
        
        self.stdout.write(self.style.SUCCESS(
            f'\n同步完成！共更新 {updated_count} 个权限点的模块名称。'
        ))

