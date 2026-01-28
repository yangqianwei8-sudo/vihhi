"""
清除办公用品相关的所有测试数据
"""
from django.core.management.base import BaseCommand
from django.db import transaction, connection
from django.db.utils import ProgrammingError, OperationalError
from backend.apps.administrative_management.models import (
    # 库存调整
    InventoryAdjustItem,
    InventoryAdjust,
    # 库存盘点
    InventoryCheckItem,
    InventoryCheck,
    # 用品领用
    SupplyRequestItem,
    SupplyRequest,
    # 用品采购
    SupplyPurchaseItem,
    SupplyPurchase,
    # 办公用品
    OfficeSupply,
    # 办公用品分类
    SupplyCategory,
)


class Command(BaseCommand):
    help = '清除所有办公用品相关的测试数据'

    def add_arguments(self, parser):
        parser.add_argument(
            '--keep-categories',
            action='store_true',
            help='保留办公用品分类（只清除用品数据）',
        )

    def _safe_count(self, model):
        """安全地获取模型记录数，如果表不存在则返回0"""
        try:
            return model.objects.count()
        except (ProgrammingError, OperationalError) as e:
            return 0

    def _safe_delete(self, model, force=False):
        """安全地删除模型记录，如果表不存在则返回0"""
        try:
            with transaction.atomic():
                if force:
                    # 强制删除，忽略外键约束
                    from django.db import connection
                    table_name = model._meta.db_table
                    with connection.cursor() as cursor:
                        cursor.execute(f'DELETE FROM "{table_name}"')
                        return cursor.rowcount
                else:
                    return model.objects.all().delete()[0]
        except (ProgrammingError, OperationalError) as e:
            if force:
                return 0
            # 如果普通删除失败，尝试强制删除
            try:
                return self._safe_delete(model, force=True)
            except:
                return 0

    def handle(self, *args, **options):
        keep_categories = options.get('keep_categories', False)
        
        self.stdout.write(self.style.WARNING('开始清除办公用品测试数据...'))
        
        # 统计删除前的数据量
        stats = {}
        
        # 1. 清除库存调整明细
        count = self._safe_count(InventoryAdjustItem)
        deleted = self._safe_delete(InventoryAdjustItem)
        stats['InventoryAdjustItem'] = (count, deleted)
        self.stdout.write(f'  清除库存调整明细: {deleted}/{count} 条')
        
        # 2. 清除库存调整
        count = self._safe_count(InventoryAdjust)
        deleted = self._safe_delete(InventoryAdjust)
        stats['InventoryAdjust'] = (count, deleted)
        self.stdout.write(f'  清除库存调整: {deleted}/{count} 条')
        
        # 3. 清除库存盘点明细
        count = self._safe_count(InventoryCheckItem)
        deleted = self._safe_delete(InventoryCheckItem)
        stats['InventoryCheckItem'] = (count, deleted)
        self.stdout.write(f'  清除库存盘点明细: {deleted}/{count} 条')
        
        # 4. 清除库存盘点
        count = self._safe_count(InventoryCheck)
        deleted = self._safe_delete(InventoryCheck)
        stats['InventoryCheck'] = (count, deleted)
        self.stdout.write(f'  清除库存盘点: {deleted}/{count} 条')
        
        # 5. 清除领用明细
        count = self._safe_count(SupplyRequestItem)
        deleted = self._safe_delete(SupplyRequestItem)
        stats['SupplyRequestItem'] = (count, deleted)
        self.stdout.write(f'  清除领用明细: {deleted}/{count} 条')
        
        # 6. 清除领用申请
        count = self._safe_count(SupplyRequest)
        deleted = self._safe_delete(SupplyRequest)
        stats['SupplyRequest'] = (count, deleted)
        self.stdout.write(f'  清除领用申请: {deleted}/{count} 条')
        
        # 7. 清除采购明细
        count = self._safe_count(SupplyPurchaseItem)
        deleted = self._safe_delete(SupplyPurchaseItem)
        stats['SupplyPurchaseItem'] = (count, deleted)
        self.stdout.write(f'  清除采购明细: {deleted}/{count} 条')
        
        # 8. 清除采购单
        count = self._safe_count(SupplyPurchase)
        deleted = self._safe_delete(SupplyPurchase)
        stats['SupplyPurchase'] = (count, deleted)
        self.stdout.write(f'  清除采购单: {deleted}/{count} 条')
        
        # 9. 清除办公用品（先清除所有关联的外键引用）
        # 先清除可能存在的关联数据
        try:
            # 清除采购明细中对办公用品的引用
            SupplyPurchaseItem.objects.filter(supply__isnull=False).update(supply=None)
        except:
            pass
        try:
            # 清除领用明细中对办公用品的引用
            SupplyRequestItem.objects.filter(supply__isnull=False).update(supply=None)
        except:
            pass
        try:
            # 清除盘点明细中对办公用品的引用
            InventoryCheckItem.objects.filter(supply__isnull=False).update(supply=None)
        except:
            pass
        try:
            # 清除调整明细中对办公用品的引用
            InventoryAdjustItem.objects.filter(supply__isnull=False).update(supply=None)
        except:
            pass
        
        count = self._safe_count(OfficeSupply)
        deleted = self._safe_delete(OfficeSupply)
        stats['OfficeSupply'] = (count, deleted)
        self.stdout.write(f'  清除办公用品: {deleted}/{count} 条')
        
        # 10. 清除分类（可选）
        if not keep_categories:
            count = self._safe_count(SupplyCategory)
            deleted = self._safe_delete(SupplyCategory)
            stats['SupplyCategory'] = (count, deleted)
            self.stdout.write(f'  清除办公用品分类: {deleted}/{count} 条')
        else:
            self.stdout.write(self.style.NOTICE('  保留办公用品分类'))
        
        # 输出统计信息
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 50))
        self.stdout.write(self.style.SUCCESS('清除完成！统计信息：'))
        self.stdout.write(self.style.SUCCESS('=' * 50))
        total_deleted = 0
        for model_name, (total, deleted) in stats.items():
            self.stdout.write(f'  {model_name}: {deleted}/{total} 条')
            total_deleted += deleted
        self.stdout.write(self.style.SUCCESS(f'总计清除: {total_deleted} 条记录'))
        self.stdout.write(self.style.SUCCESS('=' * 50))
