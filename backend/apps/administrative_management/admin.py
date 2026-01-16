from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Count, Sum
from backend.core.admin_base import BaseModelAdmin, AuditAdminMixin, LinkAdminMixin, ReadOnlyAdminMixin
from backend.apps.administrative_management.models import (
    # 行政事务
    AdministrativeAffair, AffairStatusHistory, AffairProgressRecord,
    # 办公用品
    OfficeSupply, SupplyPurchase, SupplyPurchaseItem, SupplyRequest, SupplyRequestItem, SupplyCategory,
    InventoryCheck, InventoryCheckItem, InventoryAdjust, InventoryAdjustItem,
    # 会议室和会议
    MeetingRoom, MeetingRoomBooking, Meeting, MeetingRecord, MeetingResolution,
    # 用车
    Vehicle, VehicleBooking, VehicleMaintenance,
    # 接待
    ReceptionRecord, ReceptionExpense,
    # 公告
    Announcement, AnnouncementRead,
    # 印章
    Seal, SealBorrowing, SealUsage,
    # 固定资产
    FixedAsset, AssetTransfer, AssetMaintenance,
    # 差旅
    TravelApplication,
    # 报销
    ExpenseReimbursement, ExpenseItem,
    # 采购管理
    Supplier, PurchaseContract, PurchasePayment,
)


# ==================== 办公用品管理 ====================

@admin.register(SupplyCategory)
class SupplyCategoryAdmin(BaseModelAdmin):
    """办公用品分类管理"""
    list_display = ('code', 'name', 'parent', 'sort_order', 'is_active', 'created_time')
    list_filter = ('is_active', 'parent', 'created_time')
    search_fields = ('code', 'name', 'description')
    ordering = ('sort_order', 'name')
    readonly_fields = ('code', 'created_time', 'updated_time')
    fieldsets = (
        ('基本信息', {
            'fields': ('code', 'name', 'parent', 'description', 'sort_order', 'is_active')
        }),
        # 时间信息会自动添加
    )


@admin.register(OfficeSupply)
class OfficeSupplyAdmin(AuditAdminMixin, BaseModelAdmin):
    """办公用品管理"""
    list_display = ('code', 'name', 'category', 'unit', 'current_stock', 'min_stock', 'max_stock', 'stock_status', 'is_active', 'created_time')
    list_filter = ('category', 'is_active', 'created_time')
    search_fields = ('code', 'name', 'brand', 'supplier')
    ordering = ('-created_time',)
    raw_id_fields = ('created_by',)
    readonly_fields = ('created_time', 'updated_time')
    fieldsets = (
        ('基本信息', {
            'fields': ('code', 'name', 'category', 'unit', 'specification', 'brand')
        }),
        ('供应商信息', {
            'fields': ('supplier', 'purchase_price')
        }),
        ('库存信息', {
            'fields': ('current_stock', 'min_stock', 'max_stock', 'storage_location')
        }),
        ('其他信息', {
            'fields': ('description', 'is_active', 'created_by')
        }),
        # 时间信息会自动添加
    )
    
    def stock_status(self, obj):
        """库存状态"""
        if obj.is_low_stock:
            return format_html('<span style="color: red;">低库存</span>')
        elif obj.max_stock > 0 and obj.current_stock >= obj.max_stock:
            return format_html('<span style="color: orange;">库存充足</span>')
        return format_html('<span style="color: green;">正常</span>')
    stock_status.short_description = '库存状态'


class SupplyPurchaseItemInline(admin.TabularInline):
    """采购明细内联"""
    model = SupplyPurchaseItem
    extra = 1
    raw_id_fields = ('supply',)
    fields = ('supply', 'quantity', 'unit_price', 'total_amount', 'received_quantity', 'notes')


@admin.register(SupplyPurchase)
class SupplyPurchaseAdmin(AuditAdminMixin, BaseModelAdmin):
    """用品采购管理"""
    list_display = ('purchase_number', 'purchase_date', 'supplier', 'total_amount', 'status', 'approver', 'approved_time', 'created_by', 'created_time')
    list_filter = ('status', 'purchase_date', 'created_time')
    search_fields = ('purchase_number', 'supplier')
    ordering = ('-purchase_date', '-created_time')
    raw_id_fields = ('approver', 'received_by', 'created_by')
    readonly_fields = ('purchase_number', 'created_time')
    date_hierarchy = 'purchase_date'
    inlines = [SupplyPurchaseItemInline]
    fieldsets = (
        ('基本信息', {
            'fields': ('purchase_number', 'purchase_date', 'supplier', 'status')
        }),
        ('金额信息', {
            'fields': ('total_amount',)
        }),
        ('审批信息', {
            'fields': ('approver', 'approved_time')
        }),
        ('收货信息', {
            'fields': ('received_by', 'received_time')
        }),
        ('其他信息', {
            'fields': ('notes', 'created_by')
        }),
        # 时间信息会自动添加
    )


class SupplyRequestItemInline(admin.TabularInline):
    """领用明细内联"""
    model = SupplyRequestItem
    extra = 1
    raw_id_fields = ('supply',)
    fields = ('supply', 'requested_quantity', 'approved_quantity', 'issued_quantity', 'notes')


@admin.register(SupplyRequest)
class SupplyRequestAdmin(AuditAdminMixin, BaseModelAdmin):
    """用品领用申请管理"""
    list_display = ('request_number', 'applicant', 'request_date', 'purpose', 'status', 'approver', 'approved_time', 'issued_by', 'created_time')
    list_filter = ('status', 'request_date', 'created_time')
    search_fields = ('request_number', 'applicant__username', 'purpose')
    ordering = ('-request_date', '-created_time')
    raw_id_fields = ('applicant', 'approver', 'issued_by')
    readonly_fields = ('request_number', 'created_time')
    date_hierarchy = 'request_date'
    inlines = [SupplyRequestItemInline]
    fieldsets = (
        ('基本信息', {
            'fields': ('request_number', 'applicant', 'request_date', 'purpose', 'status')
        }),
        ('审批信息', {
            'fields': ('approver', 'approved_time')
        }),
        ('发放信息', {
            'fields': ('issued_by', 'issued_time')
        }),
        ('其他信息', {
            'fields': ('notes',)
        }),
        # 时间信息会自动添加
    )


class InventoryCheckItemInline(admin.TabularInline):
    """库存盘点明细内联"""
    model = InventoryCheckItem
    extra = 1
    raw_id_fields = ('supply', 'checked_by')
    fields = ('supply', 'book_quantity', 'actual_quantity', 'difference', 'difference_amount', 'notes', 'checked_by', 'checked_time')
    readonly_fields = ('difference', 'difference_amount')


@admin.register(InventoryCheck)
class InventoryCheckAdmin(AuditAdminMixin, BaseModelAdmin):
    """库存盘点管理"""
    list_display = ('check_number', 'check_date', 'check_scope', 'checker', 'status', 'completed_time', 'approver', 'created_time')
    list_filter = ('status', 'check_date', 'created_time')
    search_fields = ('check_number', 'check_scope', 'checker__username')
    ordering = ('-check_date', '-created_time')
    raw_id_fields = ('checker', 'approver')
    filter_horizontal = ('participants',)
    readonly_fields = ('check_number', 'created_time', 'updated_time')
    date_hierarchy = 'check_date'
    inlines = [InventoryCheckItemInline]
    fieldsets = (
        ('基本信息', {
            'fields': ('check_number', 'check_date', 'check_scope', 'check_location', 'status')
        }),
        ('人员信息', {
            'fields': ('checker', 'participants')
        }),
        ('审核信息', {
            'fields': ('approver', 'approved_time', 'completed_time')
        }),
        ('其他信息', {
            'fields': ('notes',)
        }),
        # 时间信息会自动添加
    )


class InventoryAdjustItemInline(admin.TabularInline):
    """库存调整明细内联"""
    model = InventoryAdjustItem
    extra = 1
    raw_id_fields = ('supply',)
    fields = ('supply', 'adjust_quantity', 'adjust_amount', 'notes')
    readonly_fields = ('adjust_amount',)


@admin.register(InventoryAdjust)
class InventoryAdjustAdmin(AuditAdminMixin, BaseModelAdmin):
    """库存调整管理"""
    list_display = ('adjust_number', 'adjust_date', 'reason', 'status', 'approver', 'approved_time', 'executed_by', 'executed_time', 'created_time')
    list_filter = ('status', 'adjust_date', 'created_time')
    search_fields = ('adjust_number', 'reason', 'created_by__username')
    ordering = ('-adjust_date', '-created_time')
    raw_id_fields = ('approver', 'executed_by', 'created_by')
    readonly_fields = ('adjust_number', 'created_time', 'updated_time')
    date_hierarchy = 'adjust_date'
    inlines = [InventoryAdjustItemInline]
    fieldsets = (
        ('基本信息', {
            'fields': ('adjust_number', 'adjust_date', 'reason', 'status')
        }),
        ('审批信息', {
            'fields': ('approver', 'approved_time')
        }),
        ('执行信息', {
            'fields': ('executed_by', 'executed_time')
        }),
        ('其他信息', {
            'fields': ('notes', 'created_by', 'created_time', 'updated_time')
        }),
    )


# ==================== 会议室管理 ====================

@admin.register(MeetingRoom)
class MeetingRoomAdmin(BaseModelAdmin):
    """会议室管理"""
    list_display = ('code', 'name', 'location', 'capacity', 'status', 'is_active', 'created_time')
    list_filter = ('status', 'is_active', 'created_time')
    search_fields = ('code', 'name', 'location')
    ordering = ('code',)
    readonly_fields = ('created_time',)
    fieldsets = (
        ('基本信息', {
            'fields': ('code', 'name', 'location', 'capacity', 'status', 'is_active')
        }),
        ('设备设施', {
            'fields': ('equipment', 'facilities')
        }),
        ('费用信息', {
            'fields': ('hourly_rate',)
        }),
        ('其他信息', {
            'fields': ('description',)
        }),
        # 时间信息会自动添加
    )


@admin.register(Meeting)
class MeetingAdmin(AuditAdminMixin, BaseModelAdmin):
    """会议管理"""
    list_display = ('meeting_number', 'title', 'meeting_type', 'room', 'meeting_date', 'start_time', 'end_time', 'organizer', 'status', 'created_time')
    list_filter = ('meeting_type', 'status', 'meeting_date', 'created_time')
    search_fields = ('meeting_number', 'title', 'agenda', 'organizer__username')
    ordering = ('-meeting_date', '-start_time')
    raw_id_fields = ('room', 'organizer', 'created_by', 'cancelled_by')
    filter_horizontal = ('attendees',)
    readonly_fields = ('meeting_number', 'created_time', 'updated_time')
    date_hierarchy = 'meeting_date'
    fieldsets = (
        ('基本信息', {
            'fields': ('meeting_number', 'title', 'meeting_type', 'status')
        }),
        ('时间地点', {
            'fields': ('room', 'meeting_date', 'start_time', 'end_time', 'duration')
        }),
        ('人员信息', {
            'fields': ('organizer', 'attendees')
        }),
        ('会议内容', {
            'fields': ('agenda', 'attachment')
        }),
        ('取消信息', {
            'fields': ('cancelled_by', 'cancelled_time', 'cancelled_reason'),
            'classes': ('collapse',)
        }),
        ('实际时间', {
            'fields': ('actual_start_time', 'actual_end_time'),
            'classes': ('collapse',)
        }),
        ('其他信息', {
            'fields': ('created_by',)
        }),
        # 时间信息会自动添加
    )


class MeetingResolutionInline(admin.TabularInline):
    """会议决议内联"""
    model = MeetingResolution
    extra = 1
    raw_id_fields = ('responsible_user',)
    fields = ('resolution_content', 'responsible_user', 'due_date', 'status', 'completion_notes', 'completed_time')


@admin.register(MeetingRecord)
class MeetingRecordAdmin(AuditAdminMixin, BaseModelAdmin):
    """会议记录管理"""
    list_display = ('meeting', 'recorder', 'record_time', 'created_time')
    list_filter = ('record_time',)
    search_fields = ('meeting__meeting_number', 'meeting__title', 'recorder__username', 'minutes')
    ordering = ('-record_time',)
    raw_id_fields = ('meeting', 'recorder')
    date_hierarchy = 'record_time'
    readonly_fields = ('record_time', 'created_time', 'updated_time')
    inlines = [MeetingResolutionInline]
    fieldsets = (
        ('基本信息', {
            'fields': ('meeting', 'recorder', 'record_time')
        }),
        ('记录内容', {
            'fields': ('minutes', 'resolutions', 'attachment')
        }),
        # 时间信息会自动添加
    )


@admin.register(MeetingResolution)
class MeetingResolutionAdmin(BaseModelAdmin):
    """会议决议管理"""
    list_display = ('record', 'resolution_content', 'responsible_user', 'due_date', 'status', 'completed_time')
    list_filter = ('status', 'due_date', 'created_time')
    search_fields = ('record__meeting__meeting_number', 'resolution_content', 'responsible_user__username')
    ordering = ('-created_time',)
    raw_id_fields = ('record', 'responsible_user')
    readonly_fields = ('created_time',)
    fieldsets = (
        ('基本信息', {
            'fields': ('record', 'resolution_content', 'responsible_user')
        }),
        ('执行信息', {
            'fields': ('due_date', 'status', 'completion_notes', 'completed_time')
        }),
        # 时间信息会自动添加
    )


@admin.register(MeetingRoomBooking)
class MeetingRoomBookingAdmin(AuditAdminMixin, BaseModelAdmin):
    """会议室预订管理"""
    list_display = ('booking_number', 'room', 'booker', 'booking_date', 'start_time', 'end_time', 'meeting_topic', 'status', 'created_time')
    list_filter = ('status', 'booking_date', 'room', 'created_time')
    search_fields = ('booking_number', 'meeting_topic', 'booker__username', 'room__name')
    ordering = ('-booking_date', '-start_time')
    raw_id_fields = ('room', 'booker', 'cancelled_by')
    filter_horizontal = ('attendees',)
    readonly_fields = ('booking_number', 'created_time')
    date_hierarchy = 'booking_date'
    fieldsets = (
        ('基本信息', {
            'fields': ('booking_number', 'room', 'booker', 'booking_date', 'start_time', 'end_time', 'status')
        }),
        ('会议信息', {
            'fields': ('meeting_topic', 'attendees_count', 'attendees', 'equipment_needed', 'special_requirements')
        }),
        ('取消信息', {
            'fields': ('cancelled_by', 'cancelled_time', 'cancelled_reason'),
            'classes': ('collapse',)
        }),
        ('实际使用', {
            'fields': ('actual_start_time', 'actual_end_time'),
            'classes': ('collapse',)
        }),
        # 时间信息会自动添加
    )


# ==================== 用车管理 ====================

class VehicleMaintenanceInline(admin.TabularInline):
    """车辆维护内联"""
    model = VehicleMaintenance
    extra = 1
    raw_id_fields = ('performed_by',)
    fields = ('maintenance_date', 'maintenance_type', 'maintenance_items', 'cost', 'service_provider', 'next_maintenance_date', 'performed_by')
    readonly_fields = ('created_time',)


@admin.register(Vehicle)
class VehicleAdmin(BaseModelAdmin):
    """车辆管理"""
    list_display = ('plate_number', 'brand', 'vehicle_type', 'fuel_type', 'driver', 'current_mileage', 'status', 'is_active', 'created_time')
    list_filter = ('vehicle_type', 'fuel_type', 'status', 'is_active', 'created_time')
    search_fields = ('plate_number', 'brand')
    ordering = ('plate_number',)
    raw_id_fields = ('driver',)
    readonly_fields = ('created_time',)
    inlines = [VehicleMaintenanceInline]
    fieldsets = (
        ('基本信息', {
            'fields': ('plate_number', 'brand', 'vehicle_type', 'color', 'fuel_type', 'status', 'is_active')
        }),
        ('购买信息', {
            'fields': ('purchase_date', 'purchase_price')
        }),
        ('使用信息', {
            'fields': ('current_mileage', 'driver')
        }),
        ('证件信息', {
            'fields': ('insurance_expiry', 'annual_inspection_date')
        }),
        ('其他信息', {
            'fields': ('description',)
        }),
        # 时间信息会自动添加
    )


@admin.register(VehicleBooking)
class VehicleBookingAdmin(AuditAdminMixin, BaseModelAdmin):
    """用车申请管理"""
    list_display = ('booking_number', 'vehicle', 'applicant', 'driver', 'booking_date', 'start_time', 'end_time', 'destination', 'status', 'total_cost', 'created_time')
    list_filter = ('status', 'booking_date', 'vehicle', 'created_time')
    search_fields = ('booking_number', 'vehicle__plate_number', 'applicant__username', 'destination', 'purpose')
    ordering = ('-booking_date', '-start_time')
    raw_id_fields = ('vehicle', 'applicant', 'driver', 'approver')
    readonly_fields = ('booking_number', 'total_cost', 'created_time')
    date_hierarchy = 'booking_date'
    fieldsets = (
        ('基本信息', {
            'fields': ('booking_number', 'vehicle', 'applicant', 'driver', 'booking_date', 'status')
        }),
        ('时间信息', {
            'fields': ('start_time', 'end_time', 'actual_start_time', 'actual_end_time')
        }),
        ('行程信息', {
            'fields': ('destination', 'purpose', 'passenger_count', 'mileage_before', 'mileage_after')
        }),
        ('费用信息', {
            'fields': ('fuel_cost', 'parking_fee', 'toll_fee', 'other_cost', 'total_cost')
        }),
        ('审批信息', {
            'fields': ('approver', 'approved_time'),
            'classes': ('collapse',)
        }),
        ('其他信息', {
            'fields': ('notes',)
        }),
        # 时间信息会自动添加
    )


# ==================== 接待管理 ====================

class ReceptionExpenseInline(admin.TabularInline):
    """接待费用内联"""
    model = ReceptionExpense
    extra = 1
    fields = ('expense_type', 'expense_date', 'amount', 'description', 'invoice_number', 'status')


@admin.register(ReceptionRecord)
class ReceptionRecordAdmin(AuditAdminMixin, BaseModelAdmin):
    """接待记录管理"""
    list_display = ('record_number', 'visitor_name', 'visitor_company', 'reception_date', 'reception_time', 'reception_type', 'reception_level', 'status', 'host', 'created_time')
    list_filter = ('reception_type', 'reception_level', 'status', 'reception_date', 'created_time')
    search_fields = ('record_number', 'visitor_name', 'visitor_company', 'host__username')
    ordering = ('-reception_date', '-reception_time')
    raw_id_fields = ('host', 'created_by', 'approver')
    filter_horizontal = ('participants',)
    readonly_fields = ('record_number', 'created_time', 'updated_time')
    date_hierarchy = 'reception_date'
    inlines = [ReceptionExpenseInline]
    fieldsets = (
        ('基本信息', {
            'fields': ('record_number', 'reception_date', 'reception_time', 'expected_duration', 'status')
        }),
        ('访客信息', {
            'fields': ('visitor_name', 'visitor_company', 'visitor_position', 'visitor_phone', 'visitor_count')
        }),
        ('接待信息', {
            'fields': ('reception_type', 'reception_level', 'host', 'participants', 'meeting_topic', 'meeting_location')
        }),
        ('安排信息', {
            'fields': ('catering_arrangement', 'accommodation_arrangement', 'reception_budget', 'gifts_exchanged')
        }),
        ('审批信息', {
            'fields': ('approver', 'approved_time', 'approval_notes'),
            'classes': ('collapse',)
        }),
        ('结果信息', {
            'fields': ('outcome', 'feedback', 'notes')
        }),
        ('其他信息', {
            'fields': ('created_by',)
        }),
        # 时间信息会自动添加
    )


@admin.register(ReceptionExpense)
class ReceptionExpenseAdmin(BaseModelAdmin):
    """接待费用管理"""
    list_display = ('reception', 'expense_type', 'expense_date', 'amount', 'invoice_number', 'status', 'created_time')
    list_filter = ('expense_type', 'status', 'expense_date', 'created_time')
    search_fields = ('reception__record_number', 'invoice_number', 'description')
    ordering = ('-expense_date',)
    raw_id_fields = ('reception',)


# ==================== 公告通知管理 ====================

@admin.register(Announcement)
class AnnouncementAdmin(AuditAdminMixin, BaseModelAdmin):
    """公告通知管理"""
    list_display = ('title', 'category', 'priority', 'target_scope', 'publisher', 'publish_date', 'expiry_date', 'is_top', 'is_popup', 'view_count', 'is_active', 'created_time')
    list_filter = ('category', 'priority', 'target_scope', 'is_top', 'is_popup', 'is_active', 'publish_date', 'created_time')
    search_fields = ('title', 'content', 'publisher__username')
    ordering = ('-is_top', '-publish_date', '-publish_time')
    raw_id_fields = ('publisher',)
    filter_horizontal = ('target_departments', 'target_roles', 'target_users')
    readonly_fields = ('view_count', 'publish_time', 'created_time')
    date_hierarchy = 'publish_date'
    fieldsets = (
        ('基本信息', {
            'fields': ('title', 'content', 'category', 'priority', 'attachment')
        }),
        ('发布设置', {
            'fields': ('target_scope', 'target_departments', 'target_roles', 'target_users', 'publish_date', 'expiry_date', 'is_top', 'is_popup')
        }),
        ('统计信息', {
            'fields': ('view_count', 'publisher', 'publish_time', 'is_active')
        }),
        # 时间信息会自动添加
    )


@admin.register(AnnouncementRead)
class AnnouncementReadAdmin(BaseModelAdmin):
    """公告阅读记录管理"""
    list_display = ('announcement', 'user', 'read_time')
    list_filter = ('read_time',)
    search_fields = ('announcement__title', 'user__username')
    ordering = ('-read_time',)
    raw_id_fields = ('announcement', 'user')


# ==================== 印章管理 ====================

@admin.register(Seal)
class SealAdmin(BaseModelAdmin):
    """印章管理"""
    list_display = ('seal_number', 'seal_name', 'seal_type', 'keeper', 'storage_location', 'status', 'is_active', 'created_time')
    list_filter = ('seal_type', 'status', 'is_active', 'created_time')
    search_fields = ('seal_number', 'seal_name', 'keeper__username')
    ordering = ('seal_number',)
    raw_id_fields = ('keeper',)
    readonly_fields = ('created_time',)
    fieldsets = (
        ('基本信息', {
            'fields': ('seal_number', 'seal_name', 'seal_type', 'status', 'is_active')
        }),
        ('保管信息', {
            'fields': ('keeper', 'storage_location')
        }),
        ('其他信息', {
            'fields': ('description',)
        }),
        # 时间信息会自动添加
    )


class SealUsageInline(admin.TabularInline):
    """用印记录内联"""
    model = SealUsage
    extra = 0
    raw_id_fields = ('used_by', 'witness')
    fields = ('usage_date', 'usage_time', 'usage_type', 'usage_reason', 'usage_count', 'document_name', 'used_by', 'witness')
    readonly_fields = ('usage_number', 'created_time')


@admin.register(SealBorrowing)
class SealBorrowingAdmin(AuditAdminMixin, BaseModelAdmin):
    """印章借用管理"""
    list_display = ('borrowing_number', 'seal', 'borrower', 'borrowing_date', 'expected_return_date', 'actual_return_date', 'status', 'approver', 'created_time')
    list_filter = ('status', 'borrowing_date', 'created_time')
    search_fields = ('borrowing_number', 'seal__seal_name', 'borrower__username', 'borrowing_reason')
    ordering = ('-borrowing_date',)
    raw_id_fields = ('seal', 'borrower', 'approver', 'return_received_by')
    readonly_fields = ('borrowing_number', 'created_time')
    date_hierarchy = 'borrowing_date'
    inlines = [SealUsageInline]
    fieldsets = (
        ('基本信息', {
            'fields': ('borrowing_number', 'seal', 'borrower', 'borrowing_date', 'expected_return_date', 'status')
        }),
        ('借用信息', {
            'fields': ('borrowing_reason',)
        }),
        ('审批信息', {
            'fields': ('approver', 'approved_time')
        }),
        ('归还信息', {
            'fields': ('actual_return_date', 'return_received_by')
        }),
        ('其他信息', {
            'fields': ('notes',)
        }),
        # 时间信息会自动添加
    )


@admin.register(SealUsage)
class SealUsageAdmin(AuditAdminMixin, BaseModelAdmin):
    """用印记录管理"""
    list_display = ('usage_number', 'seal', 'usage_type', 'usage_date', 'usage_time', 'usage_count', 'document_name', 'used_by', 'witness', 'created_time')
    list_filter = ('usage_type', 'usage_date', 'created_time')
    search_fields = ('usage_number', 'seal__seal_name', 'document_name', 'usage_reason', 'used_by__username')
    ordering = ('-usage_date', '-usage_time')
    raw_id_fields = ('seal', 'borrowing', 'used_by', 'witness')
    date_hierarchy = 'usage_date'
    readonly_fields = ('usage_number', 'created_time')
    fieldsets = (
        ('基本信息', {
            'fields': ('usage_number', 'seal', 'borrowing', 'usage_type', 'usage_date', 'usage_time')
        }),
        ('用印信息', {
            'fields': ('usage_reason', 'usage_count', 'document_name', 'document_file')
        }),
        ('人员信息', {
            'fields': ('used_by', 'witness')
        }),
        ('其他信息', {
            'fields': ('notes',)
        }),
        # 时间信息会自动添加
    )


# ==================== 固定资产管理 ====================

class AssetMaintenanceInline(admin.TabularInline):
    """资产维护内联"""
    model = AssetMaintenance
    extra = 1
    raw_id_fields = ('performed_by',)
    fields = ('maintenance_date', 'maintenance_type', 'service_provider', 'cost', 'description', 'next_maintenance_date', 'performed_by')
    readonly_fields = ('created_time',)


@admin.register(FixedAsset)
class FixedAssetAdmin(AuditAdminMixin, BaseModelAdmin):
    """固定资产管理"""
    list_display = ('asset_number', 'asset_name', 'category', 'brand', 'current_user', 'department', 'status', 'purchase_price', 'net_value', 'is_active', 'created_time')
    list_filter = ('category', 'status', 'depreciation_method', 'is_active', 'created_time')
    search_fields = ('asset_number', 'asset_name', 'brand', 'model')
    ordering = ('-created_time',)
    raw_id_fields = ('current_user', 'department')
    readonly_fields = ('asset_number', 'created_time')
    date_hierarchy = 'purchase_date'
    inlines = [AssetMaintenanceInline]
    fieldsets = (
        ('基本信息', {
            'fields': ('asset_number', 'asset_name', 'category', 'status', 'is_active')
        }),
        ('规格信息', {
            'fields': ('brand', 'model', 'specification')
        }),
        ('购买信息', {
            'fields': ('purchase_date', 'purchase_price', 'supplier', 'warranty_period', 'warranty_expiry')
        }),
        ('使用信息', {
            'fields': ('current_user', 'current_location', 'department')
        }),
        ('折旧信息', {
            'fields': ('depreciation_method', 'depreciation_rate', 'net_value')
        }),
        ('其他信息', {
            'fields': ('description',)
        }),
        # 时间信息会自动添加
    )


@admin.register(AssetTransfer)
class AssetTransferAdmin(AuditAdminMixin, BaseModelAdmin):
    """资产转移管理"""
    list_display = ('transfer_number', 'asset', 'from_user', 'to_user', 'transfer_date', 'transfer_reason', 'status', 'approver', 'created_time')
    list_filter = ('status', 'transfer_date', 'created_time')
    search_fields = ('transfer_number', 'asset__asset_name', 'from_user__username', 'to_user__username', 'transfer_reason')
    ordering = ('-transfer_date',)
    raw_id_fields = ('asset', 'from_user', 'to_user', 'approver', 'completed_by')
    readonly_fields = ('transfer_number', 'created_time')
    date_hierarchy = 'transfer_date'
    fieldsets = (
        ('基本信息', {
            'fields': ('transfer_number', 'asset', 'transfer_date', 'status')
        }),
        ('转移信息', {
            'fields': ('from_user', 'from_location', 'to_user', 'to_location', 'transfer_reason')
        }),
        ('审批信息', {
            'fields': ('approver', 'approved_time')
        }),
        ('完成信息', {
            'fields': ('completed_by', 'completed_time')
        }),
        ('其他信息', {
            'fields': ('notes',)
        }),
        # 时间信息会自动添加
    )


@admin.register(AssetMaintenance)
class AssetMaintenanceAdmin(AuditAdminMixin, BaseModelAdmin):
    """资产维护管理"""
    list_display = ('asset', 'maintenance_date', 'maintenance_type', 'service_provider', 'cost', 'next_maintenance_date', 'performed_by', 'created_time')
    list_filter = ('maintenance_type', 'maintenance_date', 'created_time')
    search_fields = ('asset__asset_name', 'asset__asset_number', 'description', 'service_provider')
    ordering = ('-maintenance_date',)
    raw_id_fields = ('asset', 'performed_by')
    date_hierarchy = 'maintenance_date'
    fieldsets = (
        ('基本信息', {
            'fields': ('asset', 'maintenance_date', 'maintenance_type')
        }),
        ('维护信息', {
            'fields': ('service_provider', 'cost', 'description', 'performed_by')
        }),
        ('下次维护', {
            'fields': ('next_maintenance_date',)
        }),
        ('其他信息', {
            'fields': ('created_time',)
        }),
    )


# ==================== 差旅管理 ====================

@admin.register(TravelApplication)
class TravelApplicationAdmin(AuditAdminMixin, BaseModelAdmin):
    """差旅申请管理"""
    list_display = ('application_number', 'applicant', 'destination', 'start_date', 'end_date', 'travel_days', 'travel_method', 'travel_budget', 'status', 'approver', 'created_time')
    list_filter = ('status', 'travel_method', 'application_date', 'created_time')
    search_fields = ('application_number', 'destination', 'travel_reason', 'applicant__username')
    ordering = ('-application_date', '-created_time')
    raw_id_fields = ('applicant', 'approver', 'department')
    filter_horizontal = ('travelers',)
    readonly_fields = ('application_number', 'travel_days', 'created_time', 'updated_time')
    date_hierarchy = 'application_date'
    fieldsets = (
        ('基本信息', {
            'fields': ('application_number', 'applicant', 'application_date', 'department', 'status')
        }),
        ('差旅信息', {
            'fields': ('travel_reason', 'destination', 'start_date', 'end_date', 'travel_days', 'travel_method', 'travel_budget')
        }),
        ('人员信息', {
            'fields': ('travelers',)
        }),
        ('审批信息', {
            'fields': ('approver', 'approved_time', 'approval_notes'),
            'classes': ('collapse',)
        }),
        ('其他信息', {
            'fields': ('notes', 'created_time', 'updated_time')
        }),
    )


# ==================== 报销管理 ====================

class ExpenseItemInline(admin.TabularInline):
    """费用明细内联"""
    model = ExpenseItem
    extra = 1
    fields = ('expense_date', 'expense_type', 'description', 'amount', 'invoice_number', 'attachment', 'notes')


@admin.register(ExpenseReimbursement)
class ExpenseReimbursementAdmin(AuditAdminMixin, BaseModelAdmin):
    """报销申请管理"""
    list_display = ('reimbursement_number', 'travel_application', 'applicant', 'application_date', 'expense_type', 'total_amount', 'status', 'approver', 'finance_reviewer', 'payment_date', 'created_time')
    list_filter = ('status', 'expense_type', 'application_date', 'created_time')
    search_fields = ('reimbursement_number', 'applicant__username', 'notes', 'travel_application__application_number')
    ordering = ('-application_date', '-created_time')
    raw_id_fields = ('travel_application', 'applicant', 'approver', 'finance_reviewer')
    readonly_fields = ('reimbursement_number', 'total_amount', 'created_time')
    date_hierarchy = 'application_date'
    inlines = [ExpenseItemInline]
    fieldsets = (
        ('基本信息', {
            'fields': ('reimbursement_number', 'travel_application', 'applicant', 'application_date', 'expense_type', 'status')
        }),
        ('金额信息', {
            'fields': ('total_amount',)
        }),
        ('审批信息', {
            'fields': ('approver', 'approved_time')
        }),
        ('财务审核', {
            'fields': ('finance_reviewer', 'finance_reviewed_time')
        }),
        ('支付信息', {
            'fields': ('payment_date', 'payment_method')
        }),
        ('其他信息', {
            'fields': ('notes',)
        }),
        # 时间信息会自动添加
    )
    
    def save_formset(self, request, form, formset, change):
        """保存内联表单集时，自动计算总金额"""
        instances = formset.save(commit=False)
        for instance in instances:
            instance.save()
        formset.save_m2m()
        
        # 重新计算总金额
        if hasattr(form, 'instance') and form.instance.pk:
            total = form.instance.items.aggregate(total=Sum('amount'))['total'] or 0
            form.instance.total_amount = total
            form.instance.save(update_fields=['total_amount'])


@admin.register(ExpenseItem)
class ExpenseItemAdmin(BaseModelAdmin):
    """费用明细管理"""
    list_display = ('reimbursement', 'expense_date', 'expense_type', 'description', 'amount', 'invoice_number')
    list_filter = ('expense_type', 'expense_date')
    search_fields = ('reimbursement__reimbursement_number', 'description', 'invoice_number')
    ordering = ('expense_date',)
    raw_id_fields = ('reimbursement',)


@admin.register(VehicleMaintenance)
class VehicleMaintenanceAdmin(AuditAdminMixin, BaseModelAdmin):
    """车辆维护管理"""
    list_display = ('vehicle', 'maintenance_date', 'maintenance_type', 'maintenance_items', 'cost', 'service_provider', 'next_maintenance_date', 'performed_by', 'created_time')
    list_filter = ('maintenance_type', 'maintenance_date', 'created_time')
    search_fields = ('vehicle__plate_number', 'vehicle__brand', 'maintenance_items', 'description', 'service_provider')
    ordering = ('-maintenance_date',)
    raw_id_fields = ('vehicle', 'performed_by')
    date_hierarchy = 'maintenance_date'
    readonly_fields = ('created_time',)
    fieldsets = (
        ('基本信息', {
            'fields': ('vehicle', 'maintenance_date', 'maintenance_type')
        }),
        ('维护信息', {
            'fields': ('maintenance_items', 'service_provider', 'cost', 'description', 'performed_by')
        }),
        ('下次维护', {
            'fields': ('next_maintenance_date', 'next_maintenance_mileage')
        }),
        ('其他信息', {
            'fields': ('created_time',)
        }),
    )


# ==================== 行政事务管理 ====================

class AffairProgressRecordInline(admin.TabularInline):
    """事务进度记录内联"""
    model = AffairProgressRecord
    extra = 0
    raw_id_fields = ('recorder',)
    fields = ('record_time', 'progress', 'notes', 'attachment', 'recorder')
    readonly_fields = ('record_time',)


class AffairStatusHistoryInline(admin.TabularInline):
    """事务状态历史内联"""
    model = AffairStatusHistory
    extra = 0
    raw_id_fields = ('operator',)
    fields = ('operation_time', 'old_status', 'new_status', 'operator', 'notes')
    readonly_fields = ('operation_time',)


@admin.register(AdministrativeAffair)
class AdministrativeAffairAdmin(AuditAdminMixin, BaseModelAdmin):
    """行政事务管理"""
    list_display = ('affair_number', 'title', 'affair_type', 'priority', 'responsible_user', 'status', 'progress', 'planned_start_time', 'planned_end_time', 'created_time')
    list_filter = ('affair_type', 'status', 'priority', 'created_time')
    search_fields = ('affair_number', 'title', 'content', 'responsible_user__username', 'created_by__username')
    ordering = ('-created_time',)
    raw_id_fields = ('responsible_user', 'created_by')
    filter_horizontal = ('participants',)
    readonly_fields = ('affair_number', 'created_time', 'updated_time')
    date_hierarchy = 'created_time'
    inlines = [AffairProgressRecordInline, AffairStatusHistoryInline]
    fieldsets = (
        ('基本信息', {
            'fields': ('affair_number', 'title', 'affair_type', 'priority', 'status', 'progress')
        }),
        ('事务内容', {
            'fields': ('content', 'attachment')
        }),
        ('人员信息', {
            'fields': ('responsible_user', 'participants', 'created_by')
        }),
        ('时间安排', {
            'fields': ('planned_start_time', 'planned_end_time', 'actual_start_time', 'actual_end_time')
        }),
        ('处理信息', {
            'fields': ('processing_notes', 'completion_notes')
        }),
        # 时间信息会自动添加
    )


@admin.register(AffairStatusHistory)
class AffairStatusHistoryAdmin(ReadOnlyAdminMixin, BaseModelAdmin):
    """事务状态历史管理"""
    list_display = ('affair', 'old_status', 'new_status', 'operator', 'operation_time', 'notes')
    list_filter = ('new_status', 'operation_time')
    search_fields = ('affair__affair_number', 'affair__title', 'operator__username', 'notes')
    ordering = ('-operation_time',)
    raw_id_fields = ('affair', 'operator')
    date_hierarchy = 'operation_time'
    readonly_fields = ('operation_time',)


@admin.register(AffairProgressRecord)
class AffairProgressRecordAdmin(ReadOnlyAdminMixin, BaseModelAdmin):
    """事务进度记录管理"""
    list_display = ('affair', 'progress', 'record_time', 'recorder', 'notes')
    list_filter = ('record_time',)
    search_fields = ('affair__affair_number', 'affair__title', 'recorder__username', 'notes')
    ordering = ('-record_time',)
    raw_id_fields = ('affair', 'recorder')
    date_hierarchy = 'record_time'
    readonly_fields = ('record_time',)


# ==================== 采购管理 ====================

@admin.register(Supplier)
class SupplierAdmin(AuditAdminMixin, BaseModelAdmin):
    """供应商管理"""
    list_display = ('code', 'name', 'contact_person', 'contact_phone', 'rating', 'credit_limit', 'is_active', 'created_time')
    list_filter = ('rating', 'is_active', 'created_time')
    search_fields = ('code', 'name', 'contact_person', 'contact_phone')
    ordering = ('name',)
    raw_id_fields = ('created_by',)
    readonly_fields = ('code', 'created_time', 'updated_time')
    fieldsets = (
        ('基本信息', {
            'fields': ('code', 'name', 'contact_person', 'contact_phone', 'contact_email', 'address')
        }),
        ('财务信息', {
            'fields': ('tax_id', 'bank_name', 'bank_account', 'credit_limit', 'payment_terms')
        }),
        ('评级信息', {
            'fields': ('rating', 'description', 'is_active')
        }),
        ('其他信息', {
            'fields': ('created_by',)
        }),
        # 时间信息会自动添加
    )


class PurchasePaymentInline(admin.TabularInline):
    """采购付款内联"""
    model = PurchasePayment
    extra = 0
    fields = ('payment_number', 'amount', 'payment_date', 'payment_method', 'status', 'paid_by', 'paid_time')
    readonly_fields = ('payment_number', 'paid_time')


@admin.register(PurchaseContract)
class PurchaseContractAdmin(AuditAdminMixin, BaseModelAdmin):
    """采购合同管理"""
    list_display = ('contract_number', 'contract_name', 'supplier', 'contract_amount', 'signed_date', 'status', 'created_by', 'created_time')
    list_filter = ('status', 'signed_date', 'created_time')
    search_fields = ('contract_number', 'contract_name', 'supplier__name')
    ordering = ('-created_time',)
    raw_id_fields = ('supplier', 'purchase', 'created_by')
    readonly_fields = ('contract_number', 'created_time', 'updated_time')
    date_hierarchy = 'signed_date'
    inlines = [PurchasePaymentInline]
    fieldsets = (
        ('基本信息', {
            'fields': ('contract_number', 'contract_name', 'supplier', 'purchase')
        }),
        ('合同信息', {
            'fields': ('contract_amount', 'signed_date', 'start_date', 'end_date', 'payment_terms', 'status')
        }),
        ('合同文件', {
            'fields': ('contract_file',)
        }),
        ('其他信息', {
            'fields': ('notes', 'created_by', 'created_time', 'updated_time')
        }),
    )


@admin.register(PurchasePayment)
class PurchasePaymentAdmin(AuditAdminMixin, BaseModelAdmin):
    """采购付款管理"""
    list_display = ('payment_number', 'contract', 'amount', 'payment_date', 'payment_method', 'status', 'paid_by', 'paid_time', 'created_time')
    list_filter = ('status', 'payment_method', 'payment_date', 'created_time')
    search_fields = ('payment_number', 'voucher_number', 'contract__contract_number')
    ordering = ('-payment_date', '-created_time')
    raw_id_fields = ('contract', 'paid_by', 'created_by')
    readonly_fields = ('payment_number', 'paid_time', 'created_time', 'updated_time')
    date_hierarchy = 'payment_date'
    fieldsets = (
        ('基本信息', {
            'fields': ('payment_number', 'contract', 'amount', 'payment_date', 'payment_method')
        }),
        ('付款信息', {
            'fields': ('status', 'voucher_number', 'paid_by', 'paid_time')
        }),
        ('其他信息', {
            'fields': ('notes', 'created_by', 'created_time', 'updated_time')
        }),
    )

