from django.core.management.base import BaseCommand
from django.db import transaction
from backend.apps.permission_management.models import PermissionItem


class Command(BaseCommand):
    help = '将权限点的模块字段从英文迁移到中文'

    MODULE_MAPPING = {
        # 项目中心
        'project_center': '项目中心',
        # 结算中心
        'settlement_center': '结算中心',
        # 生产质量
        # 'production_quality': '生产质量',  # 已删除生产质量模块
        # 客户成功
        'customer_success': '客户成功',
        # 人事管理
        'personnel_management': '人事管理',
        # 风险管理
        'risk_management': '风险管理',
        # 系统管理
        'system_management': '系统管理',
        # 权限管理
        'permission_management': '权限管理',
        # 资源标准（原 resource_center）
        'resource_center': '资源标准',
        # 任务协作
        'task_collaboration': '任务协作',
        # 交付客户（原 delivery_center, delivery_portal）
        'delivery_center': '交付客户',
        'delivery_portal': '交付客户',
        # 已禁用的模块（需要删除）
        'administrative_management': None,  # 删除
        'financial_management': None,  # 删除
    }

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('开始迁移权限点模块字段...'))
        
        with transaction.atomic():
            # 统计信息
            updated_count = 0
            deleted_count = 0
            
            # 更新模块字段
            for old_module, new_module in self.MODULE_MAPPING.items():
                if new_module is None:
                    # 删除已禁用模块的权限点
                    deleted = PermissionItem.objects.filter(module=old_module).delete()[0]
                    if deleted > 0:
                        self.stdout.write(
                            self.style.WARNING(
                                f'  删除模块 "{old_module}" 的 {deleted} 个权限点'
                            )
                        )
                        deleted_count += deleted
                else:
                    # 更新模块字段
                    updated = PermissionItem.objects.filter(module=old_module).update(module=new_module)
                    if updated > 0:
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'  更新模块 "{old_module}" -> "{new_module}": {updated} 个权限点'
                            )
                        )
                        updated_count += updated
            
            # 检查是否有未映射的模块
            all_modules = PermissionItem.objects.values_list('module', flat=True).distinct()
            valid_modules = ['生产管理', '结算管理', '生产质量', '客户管理', '商机管理', '合同管理', '人事管理', '风险管理', '系统管理', '权限管理', '资源标准', '任务协作', '交付客户']
            unmapped = [m for m in all_modules if m not in valid_modules]
            if unmapped:
                self.stdout.write(
                    self.style.WARNING(
                        f'  警告：发现未映射的模块: {", ".join(unmapped)}'
                    )
                )
        
        self.stdout.write(self.style.SUCCESS(
            f'\n迁移完成！\n'
            f'  更新: {updated_count} 个权限点\n'
            f'  删除: {deleted_count} 个权限点'
        ))

