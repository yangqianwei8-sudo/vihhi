from django.contrib import admin
from backend.apps.litigation_management.models import (
    LitigationCase, LitigationProcess, LitigationDocument,
    LitigationExpense, LitigationPerson, LitigationTimeline,
    PreservationSeal
)
from backend.core.admin_base import BaseModelAdmin, AuditAdminMixin


@admin.register(LitigationCase)
class LitigationCaseAdmin(AuditAdminMixin, BaseModelAdmin):
    """诉讼案件管理"""
    list_display = (
        'case_number', 'case_name', 'case_type', 'case_nature', 'status',
        'priority', 'case_manager', 'registration_date', 'created_at'
    )
    list_filter = (
        'case_type', 'case_nature', 'status', 'priority',
        'registration_date', 'created_at'
    )
    search_fields = ('case_number', 'case_name', 'description')
    readonly_fields = ('case_number', 'created_at', 'updated_at')
    fieldsets = (
        ('基本信息', {
            'fields': ('case_number', 'case_name', 'case_type', 'case_nature', 'description')
        }),
        ('关联信息', {
            'fields': ('project', 'client', 'contract')
        }),
        ('金额信息', {
            'fields': ('litigation_amount', 'dispute_amount')
        }),
        ('状态信息', {
            'fields': ('status', 'priority', 'case_manager')
        }),
        ('时间信息', {
            'fields': ('registration_date', 'filing_date', 'trial_date', 
                      'judgment_date', 'execution_date', 'closing_date')
        }),
        ('登记信息', {
            'fields': ('registered_by', 'registered_department')
        }),
        # 系统时间信息会自动添加
    )


@admin.register(LitigationProcess)
class LitigationProcessAdmin(BaseModelAdmin):
    """诉讼流程管理"""
    list_display = ('case', 'process_type', 'process_date', 'status', 'created_at')
    list_filter = ('process_type', 'status', 'process_date')
    search_fields = ('case__case_number', 'case__case_name')


@admin.register(LitigationDocument)
class LitigationDocumentAdmin(AuditAdminMixin, BaseModelAdmin):
    """诉讼文档管理"""
    list_display = ('document_name', 'case', 'document_type', 'version', 'uploaded_at', 'uploaded_by')
    list_filter = ('document_type', 'uploaded_at')
    search_fields = ('document_name', 'case__case_number')


@admin.register(LitigationExpense)
class LitigationExpenseAdmin(BaseModelAdmin):
    """诉讼费用管理"""
    list_display = ('expense_name', 'case', 'expense_type', 'amount', 'expense_date', 'payment_status', 'created_at')
    list_filter = ('expense_type', 'payment_status', 'expense_date')
    search_fields = ('expense_name', 'case__case_number')


@admin.register(LitigationPerson)
class LitigationPersonAdmin(BaseModelAdmin):
    """诉讼人员管理"""
    list_display = ('name', 'person_type', 'case', 'contact_phone', 'rating', 'created_at')
    list_filter = ('person_type', 'rating')
    search_fields = ('name', 'case__case_number')


@admin.register(LitigationTimeline)
class LitigationTimelineAdmin(BaseModelAdmin):
    """诉讼时间线管理"""
    list_display = ('timeline_name', 'case', 'timeline_type', 'timeline_date', 'status', 'reminder_enabled', 'created_at')
    list_filter = ('timeline_type', 'status', 'reminder_enabled', 'timeline_date')
    search_fields = ('timeline_name', 'case__case_number')


@admin.register(PreservationSeal)
class PreservationSealAdmin(BaseModelAdmin):
    """财产保全管理"""
    list_display = ('case', 'seal_type', 'seal_amount', 'court_name', 'start_date', 'end_date', 'status', 'created_at')
    list_filter = ('seal_type', 'status', 'end_date')
    search_fields = ('case__case_number', 'seal_number', 'court_name')

