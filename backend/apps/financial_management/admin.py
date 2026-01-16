from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Count, Sum
from backend.apps.financial_management.models import (
    AccountSubject, Voucher, VoucherEntry,
    Ledger, Budget, Invoice, FundFlow,
)
from backend.core.admin_base import BaseModelAdmin, LinkAdminMixin, AuditAdminMixin


# ==================== 会计科目管理 ====================

@admin.register(AccountSubject)
class AccountSubjectAdmin(LinkAdminMixin, BaseModelAdmin):
    """会计科目管理"""
    list_display = ('code', 'name', 'subject_type', 'direction', 'level', 'is_active', 'parent_link', 'created_time')
    list_filter = ('subject_type', 'direction', 'level', 'is_active', 'created_time')
    search_fields = ('code', 'name', 'description')
    ordering = ('code',)
    raw_id_fields = ('parent', 'created_by')
    readonly_fields = ('created_time',)
    fieldsets = (
        ('基本信息', {
            'fields': ('code', 'name', 'parent', 'level')
        }),
        ('科目属性', {
            'fields': ('subject_type', 'direction')
        }),
        ('其他信息', {
            'fields': ('description', 'is_active', 'created_by')
        }),
        # 时间信息会自动添加
    )
    
    def parent_link(self, obj):
        if obj.parent:
            url = reverse('admin:financial_management_accountsubject_change', args=[obj.parent.id])
            return self.make_link(url, str(obj.parent))
        return '-'
    parent_link.short_description = '上级科目'


# ==================== 凭证管理 ====================

class VoucherEntryInline(admin.TabularInline):
    """凭证分录内联"""
    model = VoucherEntry
    extra = 3
    fields = ('line_number', 'account_subject', 'summary', 'debit_amount', 'credit_amount')
    raw_id_fields = ('account_subject',)


@admin.register(Voucher)
class VoucherAdmin(AuditAdminMixin, BaseModelAdmin):
    """记账凭证管理"""
    list_display = ('voucher_number', 'voucher_date', 'status', 'total_debit', 'total_credit', 'balance_check', 'preparer', 'reviewer', 'created_time')
    list_filter = ('status', 'voucher_date', 'created_time')
    search_fields = ('voucher_number', 'notes')
    ordering = ('-voucher_date', '-voucher_number')
    raw_id_fields = ('preparer', 'reviewer', 'posted_by')
    readonly_fields = ('created_time', 'updated_time')
    inlines = [VoucherEntryInline]
    fieldsets = (
        ('基本信息', {
            'fields': ('voucher_number', 'voucher_date', 'attachment_count')
        }),
        ('金额信息', {
            'fields': ('total_debit', 'total_credit')
        }),
        ('状态信息', {
            'fields': ('status', 'preparer', 'reviewer', 'reviewed_time', 'posted_by', 'posted_time')
        }),
        ('其他信息', {
            'fields': ('notes',)
        }),
        # 时间信息会自动添加
    )
    
    def balance_check(self, obj):
        """借贷平衡检查"""
        if obj.total_debit == obj.total_credit:
            return format_html('<span style="color: green;">✓ 平衡</span>')
        else:
            return format_html('<span style="color: red;">✗ 不平衡</span>')
    balance_check.short_description = '借贷平衡'


@admin.register(VoucherEntry)
class VoucherEntryAdmin(LinkAdminMixin, BaseModelAdmin):
    """凭证分录管理"""
    list_display = ('voucher_link', 'line_number', 'account_subject', 'summary', 'debit_amount', 'credit_amount')
    list_filter = ('voucher__voucher_date', 'account_subject__subject_type')
    search_fields = ('voucher__voucher_number', 'summary', 'account_subject__name')
    ordering = ('voucher', 'line_number')
    raw_id_fields = ('voucher', 'account_subject')
    
    def voucher_link(self, obj):
        url = reverse('admin:financial_management_voucher_change', args=[obj.voucher.id])
        return self.make_link(url, obj.voucher.voucher_number)
    voucher_link.short_description = '凭证字号'


# ==================== 账簿管理 ====================

@admin.register(Ledger)
class LedgerAdmin(BaseModelAdmin):
    """总账管理"""
    list_display = ('account_subject', 'period_date', 'period_year', 'period_month', 'opening_balance', 'period_debit', 'period_credit', 'closing_balance', 'created_time')
    list_filter = ('period_year', 'period_month', 'account_subject__subject_type', 'created_time')
    search_fields = ('account_subject__code', 'account_subject__name')
    ordering = ('-period_date', 'account_subject')
    raw_id_fields = ('account_subject',)
    readonly_fields = ('created_time',)
    fieldsets = (
        ('基本信息', {
            'fields': ('account_subject', 'period_year', 'period_month', 'period_date')
        }),
        ('余额信息', {
            'fields': ('opening_balance', 'period_debit', 'period_credit', 'closing_balance')
        }),
        # 时间信息会自动添加
    )


# ==================== 预算管理 ====================

@admin.register(Budget)
class BudgetAdmin(AuditAdminMixin, BaseModelAdmin):
    """预算管理"""
    list_display = ('budget_number', 'name', 'budget_year', 'budget_amount', 'used_amount', 'remaining_amount', 'usage_rate', 'status', 'department', 'approver', 'created_time')
    list_filter = ('status', 'budget_year', 'department', 'created_time')
    search_fields = ('budget_number', 'name', 'description')
    ordering = ('-budget_year', '-created_time')
    raw_id_fields = ('department', 'account_subject', 'approver', 'created_by')
    readonly_fields = ('remaining_amount', 'created_time')
    fieldsets = (
        ('基本信息', {
            'fields': ('budget_number', 'name', 'budget_year', 'department', 'account_subject')
        }),
        ('金额信息', {
            'fields': ('budget_amount', 'used_amount', 'remaining_amount')
        }),
        ('时间信息', {
            'fields': ('start_date', 'end_date')
        }),
        ('状态信息', {
            'fields': ('status', 'approver', 'approved_time')
        }),
        ('其他信息', {
            'fields': ('description', 'created_by')
        }),
        # 系统时间信息会自动添加
    )
    
    def usage_rate(self, obj):
        """使用率"""
        if obj.budget_amount > 0:
            rate = (obj.used_amount / obj.budget_amount) * 100
            color = 'green' if rate < 80 else 'orange' if rate < 100 else 'red'
            return format_html('<span style="color: {};">{:.1f}%</span>', color, rate)
        return '-'
    usage_rate.short_description = '使用率'


# ==================== 发票管理 ====================

@admin.register(Invoice)
class InvoiceAdmin(AuditAdminMixin, BaseModelAdmin):
    """发票管理"""
    list_display = ('invoice_number', 'invoice_code', 'invoice_type', 'invoice_date', 'amount', 'tax_amount', 'total_amount', 'status', 'customer_or_supplier', 'verified_by', 'created_time')
    list_filter = ('invoice_type', 'status', 'invoice_date', 'created_time')
    search_fields = ('invoice_number', 'invoice_code', 'customer_name', 'supplier_name', 'notes')
    ordering = ('-invoice_date', '-invoice_number')
    raw_id_fields = ('verified_by', 'created_by')
    readonly_fields = ('created_time',)
    fieldsets = (
        ('基本信息', {
            'fields': ('invoice_number', 'invoice_code', 'invoice_type', 'invoice_date')
        }),
        ('金额信息', {
            'fields': ('amount', 'tax_amount', 'total_amount')
        }),
        ('单位信息', {
            'fields': ('customer_name', 'supplier_name')
        }),
        ('状态信息', {
            'fields': ('status', 'verified_by', 'verified_time')
        }),
        ('其他信息', {
            'fields': ('attachment', 'notes', 'created_by')
        }),
        # 时间信息会自动添加
    )
    
    def customer_or_supplier(self, obj):
        """客户或供应商"""
        if obj.invoice_type == 'outgoing':
            return obj.customer_name or '-'
        else:
            return obj.supplier_name or '-'
    customer_or_supplier.short_description = '对方单位'


# ==================== 资金流水 ====================

@admin.register(FundFlow)
class FundFlowAdmin(LinkAdminMixin, AuditAdminMixin, BaseModelAdmin):
    """资金流水管理"""
    list_display = ('flow_number', 'flow_date', 'flow_type', 'amount', 'account_name', 'counterparty', 'summary', 'project_link', 'voucher_link', 'created_time')
    list_filter = ('flow_type', 'flow_date', 'account_name', 'created_time')
    search_fields = ('flow_number', 'account_name', 'counterparty', 'summary')
    ordering = ('-flow_date', '-flow_number')
    raw_id_fields = ('project', 'voucher', 'created_by')
    readonly_fields = ('created_time',)
    fieldsets = (
        ('基本信息', {
            'fields': ('flow_number', 'flow_date', 'flow_type')
        }),
        ('金额信息', {
            'fields': ('amount', 'account_name', 'counterparty')
        }),
        ('关联信息', {
            'fields': ('summary', 'project', 'voucher')
        }),
        ('其他信息', {
            'fields': ('created_by',)
        }),
        # 时间信息会自动添加
    )
    
    def project_link(self, obj):
        if obj.project:
            url = reverse('admin:project_center_project_change', args=[obj.project.id])
            return self.make_link(url, obj.project.project_number)
        return '-'
    project_link.short_description = '关联项目'
    
    def voucher_link(self, obj):
        if obj.voucher:
            url = reverse('admin:financial_management_voucher_change', args=[obj.voucher.id])
            return self.make_link(url, obj.voucher.voucher_number)
        return '-'
    voucher_link.short_description = '关联凭证'
