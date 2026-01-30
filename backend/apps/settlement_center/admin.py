"""
结算中心模块的Admin配置
注意：业务模块数据应在前端管理，不再在Django Admin中显示
这些数据应通过API接口在前端管理
"""

from django.contrib import admin
from django.db.models import Sum
from backend.core.admin_base import BaseModelAdmin
# 注意：这些模型已迁移到 settlement_management，但为了保持向后兼容，仍从 settlement_center 导入
from backend.apps.settlement_center.models import (
    OutputValueStage, OutputValueMilestone, OutputValueEvent, OutputValueRecord,
    ServiceFeeSettlementScheme, ServiceFeeSegmentedRate, 
    ServiceFeeJumpPointRate, ServiceFeeUnitCapDetail,
      # PaymentRecord 已迁移到 settlement_center
    SettlementMethod,
)
# 以下模型已迁移到 settlement_management
try:
    from backend.apps.settlement_management.models import (
        ProjectSettlement, SettlementItem, ServiceFeeRate, ContractSettlement,
    )
except ImportError:
    # 如果 settlement_management 不可用，使用空占位符
    ProjectSettlement = None
    SettlementItem = None
    ServiceFeeRate = None
    ContractSettlement = None


# 注意：业务模型的Admin注册已移除，改为在前端管理
# 如需查看数据，请使用API接口或前端管理页面


# ==================== 结算方式管理 ====================

@admin.register(SettlementMethod)
class SettlementMethodAdmin(BaseModelAdmin):
    """结算方式管理"""
    list_display = ('code', 'name', 'description', 'sort_order', 'is_active', 'created_time')
    list_filter = ('is_active', 'code', 'created_time')
    search_fields = ('code', 'name', 'description')
    ordering = ('sort_order', 'name')
    readonly_fields = ('created_time', 'updated_time')
    fieldsets = (
        ('基本信息', {
            'fields': ('code', 'name', 'description', 'sort_order', 'is_active')
        }),
        # 时间信息会自动添加
    )


# ==================== 回款记录管理 ====================
# 注意：PaymentRecord已迁移到payment_management应用
# 如需在Django Admin中管理，请在payment_management/admin.py中注册


# ==================== 取消注册其他模型，只保留结算方式和回款记录 ====================
# 确保其他模型不会显示在菜单中
try:
    # 如果这些模型已经被注册，取消注册
    if ServiceFeeSettlementScheme in admin.site._registry:
        admin.site.unregister(ServiceFeeSettlementScheme)
    if ServiceFeeSegmentedRate in admin.site._registry:
        admin.site.unregister(ServiceFeeSegmentedRate)
    if ServiceFeeJumpPointRate in admin.site._registry:
        admin.site.unregister(ServiceFeeJumpPointRate)
    if ServiceFeeUnitCapDetail in admin.site._registry:
        admin.site.unregister(ServiceFeeUnitCapDetail)
except Exception:
    # 如果取消注册失败，忽略错误（可能模型还未注册）
    pass
