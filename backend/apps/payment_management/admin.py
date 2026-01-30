# 回款管理模块的Django Admin配置
from django.contrib import admin
from backend.core.admin_base import BaseModelAdmin
from .models import PaymentRecord

# ==================== 回款记录管理 ====================

@admin.register(PaymentRecord)
class PaymentRecordAdmin(BaseModelAdmin):
    """回款记录管理"""
    list_display = (
        'payment_number', 'payment_amount', 'payment_date', 
        'payment_method', 'status', 'created_time'
    )
    list_filter = ('status', 'payment_method', 'payment_date', 'payment_plan_type', 'created_time')
    search_fields = ('payment_number', 'invoice_number', 'bank_account', 'notes')
    ordering = ('-payment_date', '-created_time')
    raw_id_fields = ('confirmed_by', 'created_by')
    readonly_fields = ('created_time', 'confirmed_time')
    date_hierarchy = 'payment_date'
    fieldsets = (
        ('回款计划关联', {
            'fields': ('payment_plan_type', 'payment_plan_id')
        }),
        ('回款信息', {
            'fields': ('payment_number', 'payment_amount', 'payment_date', 'payment_method')
        }),
        ('财务信息', {
            'fields': ('invoice_number', 'bank_account', 'receipt_voucher')
        }),
        ('状态和审核', {
            'fields': ('status', 'confirmed_by', 'confirmed_time')
        }),
        ('其他信息', {
            'fields': ('notes', 'created_by')
        }),
        # 时间信息会自动添加
    )
