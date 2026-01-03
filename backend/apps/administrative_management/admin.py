# 行政管理模块的所有模型已从后台管理中移除，请使用前端管理页面
# 前端管理页面路径：/administrative/

from django.contrib import admin
# from django.utils.html import format_html
# from django.urls import reverse
# from django.db.models import Count, Sum
# from backend.core.admin_base import BaseModelAdmin, AuditAdminMixin, LinkAdminMixin, ReadOnlyAdminMixin
# from backend.apps.administrative_management.models import (
#     # 行政事务
#     AdministrativeAffair,
#     # 办公用品
#     OfficeSupply, SupplyPurchase, SupplyPurchaseItem, SupplyRequest, SupplyRequestItem, SupplyCategory,
#     InventoryCheck, InventoryCheckItem, InventoryAdjust, InventoryAdjustItem,
#     # 会议室和会议
#     MeetingRoom, MeetingRoomBooking, Meeting, MeetingRecord, MeetingResolution,
#     # 用车
#     Vehicle, VehicleBooking, VehicleMaintenance,
#     # 接待
#     ReceptionRecord, ReceptionExpense,
#     # 公告
#     Announcement, AnnouncementRead,
#     # 印章
#     Seal, SealBorrowing, SealUsage,
#     # 固定资产
#     FixedAsset, AssetTransfer, AssetMaintenance,
#     # 差旅
#     TravelApplication,
#     # 报销
#     ExpenseReimbursement, ExpenseItem,
#     # 采购管理
#     Supplier, PurchaseContract, PurchasePayment,
# )


# ==================== 办公用品管理 ====================
# 所有模型已从后台管理中移除，请使用前端管理页面

# @admin.register(SupplyCategory)
# class SupplyCategoryAdmin(BaseModelAdmin):
#     """办公用品分类管理"""
#     pass

# @admin.register(OfficeSupply)
# class OfficeSupplyAdmin(AuditAdminMixin, BaseModelAdmin):
#     """办公用品管理"""
#     pass

# @admin.register(SupplyPurchase)
# class SupplyPurchaseAdmin(AuditAdminMixin, BaseModelAdmin):
#     """用品采购管理"""
#     pass

# @admin.register(SupplyRequest)
# class SupplyRequestAdmin(AuditAdminMixin, BaseModelAdmin):
#     """用品领用申请管理"""
#     pass

# @admin.register(InventoryCheck)
# class InventoryCheckAdmin(AuditAdminMixin, BaseModelAdmin):
#     """库存盘点管理"""
#     pass

# @admin.register(InventoryAdjust)
# class InventoryAdjustAdmin(AuditAdminMixin, BaseModelAdmin):
#     """库存调整管理"""
#     pass


# ==================== 会议室管理 ====================
# 所有模型已从后台管理中移除，请使用前端管理页面

# @admin.register(MeetingRoom)
# class MeetingRoomAdmin(BaseModelAdmin):
#     """会议室管理"""
#     pass

# @admin.register(Meeting)
# class MeetingAdmin(AuditAdminMixin, BaseModelAdmin):
#     """会议管理"""
#     pass

# @admin.register(MeetingRecord)
# class MeetingRecordAdmin(AuditAdminMixin, BaseModelAdmin):
#     """会议记录管理"""
#     pass

# @admin.register(MeetingResolution)
# class MeetingResolutionAdmin(BaseModelAdmin):
#     """会议决议管理"""
#     pass

# @admin.register(MeetingRoomBooking)
# class MeetingRoomBookingAdmin(AuditAdminMixin, BaseModelAdmin):
#     """会议室预订管理"""
#     pass


# ==================== 用车管理 ====================
# 所有模型已从后台管理中移除，请使用前端管理页面

# @admin.register(Vehicle)
# class VehicleAdmin(BaseModelAdmin):
#     """车辆管理"""
#     pass

# @admin.register(VehicleBooking)
# class VehicleBookingAdmin(AuditAdminMixin, BaseModelAdmin):
#     """用车申请管理"""
#     pass

# @admin.register(VehicleMaintenance)
# class VehicleMaintenanceAdmin(AuditAdminMixin, BaseModelAdmin):
#     """车辆维护管理"""
#     pass


# ==================== 接待管理 ====================
# 所有模型已从后台管理中移除，请使用前端管理页面

# @admin.register(ReceptionRecord)
# class ReceptionRecordAdmin(AuditAdminMixin, BaseModelAdmin):
#     """接待记录管理"""
#     pass

# @admin.register(ReceptionExpense)
# class ReceptionExpenseAdmin(BaseModelAdmin):
#     """接待费用管理"""
#     pass


# ==================== 公告通知管理 ====================
# 所有模型已从后台管理中移除，请使用前端管理页面

# @admin.register(Announcement)
# class AnnouncementAdmin(AuditAdminMixin, BaseModelAdmin):
#     """公告通知管理"""
#     pass

# @admin.register(AnnouncementRead)
# class AnnouncementReadAdmin(BaseModelAdmin):
#     """公告阅读记录管理"""
#     pass


# ==================== 印章管理 ====================
# 所有模型已从后台管理中移除，请使用前端管理页面

# @admin.register(Seal)
# class SealAdmin(BaseModelAdmin):
#     """印章管理"""
#     pass

# @admin.register(SealBorrowing)
# class SealBorrowingAdmin(AuditAdminMixin, BaseModelAdmin):
#     """印章借用管理"""
#     pass

# @admin.register(SealUsage)
# class SealUsageAdmin(AuditAdminMixin, BaseModelAdmin):
#     """用印记录管理"""
#     pass


# ==================== 固定资产管理 ====================
# 所有模型已从后台管理中移除，请使用前端管理页面

# @admin.register(FixedAsset)
# class FixedAssetAdmin(AuditAdminMixin, BaseModelAdmin):
#     """固定资产管理"""
#     pass

# @admin.register(AssetTransfer)
# class AssetTransferAdmin(AuditAdminMixin, BaseModelAdmin):
#     """资产转移管理"""
#     pass

# @admin.register(AssetMaintenance)
# class AssetMaintenanceAdmin(AuditAdminMixin, BaseModelAdmin):
#     """资产维护管理"""
#     pass


# ==================== 差旅管理 ====================
# 所有模型已从后台管理中移除，请使用前端管理页面

# @admin.register(TravelApplication)
# class TravelApplicationAdmin(AuditAdminMixin, BaseModelAdmin):
#     """差旅申请管理"""
#     pass


# ==================== 报销管理 ====================
# 所有模型已从后台管理中移除，请使用前端管理页面

# @admin.register(ExpenseReimbursement)
# class ExpenseReimbursementAdmin(AuditAdminMixin, BaseModelAdmin):
#     """报销申请管理"""
#     pass

# @admin.register(ExpenseItem)
# class ExpenseItemAdmin(BaseModelAdmin):
#     """费用明细管理"""
#     pass


# ==================== 行政事务管理 ====================
# 所有模型已从后台管理中移除，请使用前端管理页面

# @admin.register(AdministrativeAffair)
# class AdministrativeAffairAdmin(AuditAdminMixin, BaseModelAdmin):
#     """行政事务管理"""
#     pass


# ==================== 采购管理 ====================
# 所有模型已从后台管理中移除，请使用前端管理页面

# @admin.register(Supplier)
# class SupplierAdmin(AuditAdminMixin, BaseModelAdmin):
#     """供应商管理"""
#     pass

# @admin.register(PurchaseContract)
# class PurchaseContractAdmin(AuditAdminMixin, BaseModelAdmin):
#     """采购合同管理"""
#     pass

# @admin.register(PurchasePayment)
# class PurchasePaymentAdmin(AuditAdminMixin, BaseModelAdmin):
#     """采购付款管理"""
#     pass
