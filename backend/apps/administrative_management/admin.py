from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Count, Sum
from .models import (
    # 办公用品
    OfficeSupply, SupplyPurchase, SupplyPurchaseItem, SupplyRequest, SupplyRequestItem,
    # 会议室
    MeetingRoom, MeetingRoomBooking,
    # 用车
    Vehicle, VehicleBooking,
    # 接待
    ReceptionRecord, ReceptionExpense,
    # 公告
    Announcement, AnnouncementRead,
    # 印章
    Seal, SealBorrowing,
    # 固定资产
    FixedAsset, AssetTransfer, AssetMaintenance,
    # 报销
    ExpenseReimbursement, ExpenseItem,
)


# ==================== 办公用品管理 ====================

@admin.register(OfficeSupply)
class OfficeSupplyAdmin(admin.ModelAdmin):
    """办公用品管理"""
    list_display = ('code', 'name', 'category', 'unit', 'current_stock', 'min_stock', 'max_stock', 'stock_status', 'is_active', 'created_time')
    list_filter = ('category', 'is_active', 'created_time')
    search_fields = ('code', 'name', 'brand', 'supplier')
    ordering = ('-created_time',)
    list_per_page = 50
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
            'fields': ('description', 'is_active', 'created_by', 'created_time', 'updated_time')
        }),
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
class SupplyPurchaseAdmin(admin.ModelAdmin):
    """用品采购管理"""
    list_display = ('purchase_number', 'purchase_date', 'supplier', 'total_amount', 'status', 'approver', 'approved_time', 'created_by', 'created_time')
    list_filter = ('status', 'purchase_date', 'created_time')
    search_fields = ('purchase_number', 'supplier')
    ordering = ('-purchase_date', '-created_time')
    list_per_page = 50
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
            'fields': ('notes', 'created_by', 'created_time')
        }),
    )


class SupplyRequestItemInline(admin.TabularInline):
    """领用明细内联"""
    model = SupplyRequestItem
    extra = 1
    raw_id_fields = ('supply',)
    fields = ('supply', 'requested_quantity', 'approved_quantity', 'issued_quantity', 'notes')


@admin.register(SupplyRequest)
class SupplyRequestAdmin(admin.ModelAdmin):
    """用品领用申请管理"""
    list_display = ('request_number', 'applicant', 'request_date', 'purpose', 'status', 'approver', 'approved_time', 'issued_by', 'created_time')
    list_filter = ('status', 'request_date', 'created_time')
    search_fields = ('request_number', 'applicant__username', 'purpose')
    ordering = ('-request_date', '-created_time')
    list_per_page = 50
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
            'fields': ('notes', 'created_time')
        }),
    )


# ==================== 会议室管理 ====================

@admin.register(MeetingRoom)
class MeetingRoomAdmin(admin.ModelAdmin):
    """会议室管理"""
    list_display = ('code', 'name', 'location', 'capacity', 'status', 'is_active', 'created_time')
    list_filter = ('status', 'is_active', 'created_time')
    search_fields = ('code', 'name', 'location')
    ordering = ('code',)
    list_per_page = 50
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
            'fields': ('description', 'created_time')
        }),
    )


@admin.register(MeetingRoomBooking)
class MeetingRoomBookingAdmin(admin.ModelAdmin):
    """会议室预订管理"""
    list_display = ('booking_number', 'room', 'booker', 'booking_date', 'start_time', 'end_time', 'meeting_topic', 'status', 'created_time')
    list_filter = ('status', 'booking_date', 'room', 'created_time')
    search_fields = ('booking_number', 'meeting_topic', 'booker__username', 'room__name')
    ordering = ('-booking_date', '-start_time')
    list_per_page = 50
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
        ('其他信息', {
            'fields': ('created_time',)
        }),
    )


# ==================== 用车管理 ====================

@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    """车辆管理"""
    list_display = ('plate_number', 'brand', 'vehicle_type', 'fuel_type', 'driver', 'current_mileage', 'status', 'is_active', 'created_time')
    list_filter = ('vehicle_type', 'fuel_type', 'status', 'is_active', 'created_time')
    search_fields = ('plate_number', 'brand')
    ordering = ('plate_number',)
    list_per_page = 50
    raw_id_fields = ('driver',)
    readonly_fields = ('created_time',)
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
            'fields': ('description', 'created_time')
        }),
    )


@admin.register(VehicleBooking)
class VehicleBookingAdmin(admin.ModelAdmin):
    """用车申请管理"""
    list_display = ('booking_number', 'vehicle', 'applicant', 'driver', 'booking_date', 'start_time', 'end_time', 'destination', 'status', 'total_cost', 'created_time')
    list_filter = ('status', 'booking_date', 'vehicle', 'created_time')
    search_fields = ('booking_number', 'vehicle__plate_number', 'applicant__username', 'destination', 'purpose')
    ordering = ('-booking_date', '-start_time')
    list_per_page = 50
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
            'fields': ('notes', 'created_time')
        }),
    )


# ==================== 接待管理 ====================

class ReceptionExpenseInline(admin.TabularInline):
    """接待费用内联"""
    model = ReceptionExpense
    extra = 1
    fields = ('expense_type', 'expense_date', 'amount', 'description', 'invoice_number', 'status')


@admin.register(ReceptionRecord)
class ReceptionRecordAdmin(admin.ModelAdmin):
    """接待记录管理"""
    list_display = ('record_number', 'visitor_name', 'visitor_company', 'reception_date', 'reception_time', 'reception_type', 'reception_level', 'host', 'created_time')
    list_filter = ('reception_type', 'reception_level', 'reception_date', 'created_time')
    search_fields = ('record_number', 'visitor_name', 'visitor_company', 'host__username')
    ordering = ('-reception_date', '-reception_time')
    list_per_page = 50
    raw_id_fields = ('host', 'created_by')
    filter_horizontal = ('participants',)
    readonly_fields = ('record_number', 'created_time')
    date_hierarchy = 'reception_date'
    inlines = [ReceptionExpenseInline]
    fieldsets = (
        ('基本信息', {
            'fields': ('record_number', 'reception_date', 'reception_time', 'expected_duration')
        }),
        ('访客信息', {
            'fields': ('visitor_name', 'visitor_company', 'visitor_position', 'visitor_phone', 'visitor_count')
        }),
        ('接待信息', {
            'fields': ('reception_type', 'reception_level', 'host', 'participants', 'meeting_topic', 'meeting_location')
        }),
        ('安排信息', {
            'fields': ('catering_arrangement', 'accommodation_arrangement', 'gifts_exchanged')
        }),
        ('结果信息', {
            'fields': ('outcome', 'notes')
        }),
        ('其他信息', {
            'fields': ('created_by', 'created_time')
        }),
    )


@admin.register(ReceptionExpense)
class ReceptionExpenseAdmin(admin.ModelAdmin):
    """接待费用管理"""
    list_display = ('reception', 'expense_type', 'expense_date', 'amount', 'invoice_number', 'status', 'created_time')
    list_filter = ('expense_type', 'status', 'expense_date', 'created_time')
    search_fields = ('reception__record_number', 'invoice_number', 'description')
    ordering = ('-expense_date',)
    raw_id_fields = ('reception',)
    list_per_page = 50


# ==================== 公告通知管理 ====================

@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    """公告通知管理"""
    list_display = ('title', 'category', 'priority', 'target_scope', 'publisher', 'publish_date', 'expiry_date', 'is_top', 'is_popup', 'view_count', 'is_active', 'created_time')
    list_filter = ('category', 'priority', 'target_scope', 'is_top', 'is_popup', 'is_active', 'publish_date', 'created_time')
    search_fields = ('title', 'content', 'publisher__username')
    ordering = ('-is_top', '-publish_date', '-publish_time')
    list_per_page = 50
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
            'fields': ('view_count', 'publisher', 'publish_time', 'is_active', 'created_time')
        }),
    )


@admin.register(AnnouncementRead)
class AnnouncementReadAdmin(admin.ModelAdmin):
    """公告阅读记录管理"""
    list_display = ('announcement', 'user', 'read_time')
    list_filter = ('read_time',)
    search_fields = ('announcement__title', 'user__username')
    ordering = ('-read_time',)
    raw_id_fields = ('announcement', 'user')
    list_per_page = 50


# ==================== 印章管理 ====================

@admin.register(Seal)
class SealAdmin(admin.ModelAdmin):
    """印章管理"""
    list_display = ('seal_number', 'seal_name', 'seal_type', 'keeper', 'storage_location', 'status', 'is_active', 'created_time')
    list_filter = ('seal_type', 'status', 'is_active', 'created_time')
    search_fields = ('seal_number', 'seal_name', 'keeper__username')
    ordering = ('seal_number',)
    list_per_page = 50
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
            'fields': ('description', 'created_time')
        }),
    )


@admin.register(SealBorrowing)
class SealBorrowingAdmin(admin.ModelAdmin):
    """印章借用管理"""
    list_display = ('borrowing_number', 'seal', 'borrower', 'borrowing_date', 'expected_return_date', 'actual_return_date', 'status', 'approver', 'created_time')
    list_filter = ('status', 'borrowing_date', 'created_time')
    search_fields = ('borrowing_number', 'seal__seal_name', 'borrower__username', 'borrowing_reason')
    ordering = ('-borrowing_date',)
    list_per_page = 50
    raw_id_fields = ('seal', 'borrower', 'approver', 'return_received_by')
    readonly_fields = ('borrowing_number', 'created_time')
    date_hierarchy = 'borrowing_date'
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
            'fields': ('notes', 'created_time')
        }),
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
class FixedAssetAdmin(admin.ModelAdmin):
    """固定资产管理"""
    list_display = ('asset_number', 'asset_name', 'category', 'brand', 'current_user', 'department', 'status', 'purchase_price', 'net_value', 'is_active', 'created_time')
    list_filter = ('category', 'status', 'depreciation_method', 'is_active', 'created_time')
    search_fields = ('asset_number', 'asset_name', 'brand', 'model')
    ordering = ('-created_time',)
    list_per_page = 50
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
            'fields': ('description', 'created_time')
        }),
    )


@admin.register(AssetTransfer)
class AssetTransferAdmin(admin.ModelAdmin):
    """资产转移管理"""
    list_display = ('transfer_number', 'asset', 'from_user', 'to_user', 'transfer_date', 'transfer_reason', 'status', 'approver', 'created_time')
    list_filter = ('status', 'transfer_date', 'created_time')
    search_fields = ('transfer_number', 'asset__asset_name', 'from_user__username', 'to_user__username', 'transfer_reason')
    ordering = ('-transfer_date',)
    list_per_page = 50
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
            'fields': ('notes', 'created_time')
        }),
    )


@admin.register(AssetMaintenance)
class AssetMaintenanceAdmin(admin.ModelAdmin):
    """资产维护管理"""
    list_display = ('asset', 'maintenance_date', 'maintenance_type', 'service_provider', 'cost', 'next_maintenance_date', 'performed_by', 'created_time')
    list_filter = ('maintenance_type', 'maintenance_date', 'created_time')
    search_fields = ('asset__asset_name', 'asset__asset_number', 'description', 'service_provider')
    ordering = ('-maintenance_date',)
    raw_id_fields = ('asset', 'performed_by')
    list_per_page = 50
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


# ==================== 报销管理 ====================

class ExpenseItemInline(admin.TabularInline):
    """费用明细内联"""
    model = ExpenseItem
    extra = 1
    fields = ('expense_date', 'expense_type', 'description', 'amount', 'invoice_number', 'attachment', 'notes')


@admin.register(ExpenseReimbursement)
class ExpenseReimbursementAdmin(admin.ModelAdmin):
    """报销申请管理"""
    list_display = ('reimbursement_number', 'applicant', 'application_date', 'expense_type', 'total_amount', 'status', 'approver', 'finance_reviewer', 'payment_date', 'created_time')
    list_filter = ('status', 'expense_type', 'application_date', 'created_time')
    search_fields = ('reimbursement_number', 'applicant__username', 'notes')
    ordering = ('-application_date', '-created_time')
    list_per_page = 50
    raw_id_fields = ('applicant', 'approver', 'finance_reviewer')
    readonly_fields = ('reimbursement_number', 'total_amount', 'created_time')
    date_hierarchy = 'application_date'
    inlines = [ExpenseItemInline]
    fieldsets = (
        ('基本信息', {
            'fields': ('reimbursement_number', 'applicant', 'application_date', 'expense_type', 'status')
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
            'fields': ('notes', 'created_time')
        }),
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
class ExpenseItemAdmin(admin.ModelAdmin):
    """费用明细管理"""
    list_display = ('reimbursement', 'expense_date', 'expense_type', 'description', 'amount', 'invoice_number')
    list_filter = ('expense_type', 'expense_date')
    search_fields = ('reimbursement__reimbursement_number', 'description', 'invoice_number')
    ordering = ('expense_date',)
    raw_id_fields = ('reimbursement',)
    list_per_page = 50

