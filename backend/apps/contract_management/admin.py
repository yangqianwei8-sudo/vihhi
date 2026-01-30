from django.contrib import admin
from backend.core.admin_base import BaseModelAdmin
from .models import (
    BusinessContract,
    BusinessPaymentPlan,
    ContractParty,
    ResultFileType,
)

# ==================== 合同管理 ====================

@admin.register(BusinessContract)
class BusinessContractAdmin(BaseModelAdmin):
    """商务合同管理"""
    list_display = (
        'contract_number', 'project_number', 'contract_name', 'contract_type',
        'status', 'contract_amount', 'contract_date', 'created_time'
    )
    list_filter = ('contract_type', 'status', 'contract_date', 'created_time')
    search_fields = ('contract_number', 'project_number', 'contract_name', 'party_a_name', 'party_b_name')
    ordering = ('-created_time',)
    raw_id_fields = ('project', 'client', 'opportunity', 'parent_contract', 'signed_by', 'approved_by', 'business_manager', 'created_by')
    readonly_fields = ('created_time', 'updated_time')
    date_hierarchy = 'contract_date'

@admin.register(BusinessPaymentPlan)
class BusinessPaymentPlanAdmin(BaseModelAdmin):
    """商务回款计划管理"""
    list_display = (
        'contract', 'phase_name', 'planned_amount', 'planned_date',
        'actual_amount', 'actual_date', 'status', 'created_time'
    )
    list_filter = ('status', 'planned_date', 'created_time')
    search_fields = ('phase_name', 'phase_description', 'notes')
    ordering = ('-planned_date',)
    raw_id_fields = ('contract',)
    readonly_fields = ('created_time', 'updated_time')
    date_hierarchy = 'planned_date'

@admin.register(ContractParty)
class ContractPartyAdmin(BaseModelAdmin):
    """合同签约主体管理"""
    list_display = (
        'contract', 'party_type', 'party_name', 'credit_code',
        'legal_representative', 'is_active', 'created_time'
    )
    list_filter = ('party_type', 'is_active', 'created_time')
    search_fields = ('party_name', 'credit_code', 'legal_representative', 'party_contact')
    ordering = ('-created_time',)
    raw_id_fields = ('contract',)
    readonly_fields = ('created_time', 'updated_time')

@admin.register(ResultFileType)
class ResultFileTypeAdmin(BaseModelAdmin):
    """成果文件类型管理"""
    list_display = (
        'service_category', 'code', 'name', 'order', 'is_active', 'created_time'
    )
    list_filter = ('service_category', 'is_active', 'created_time')
    search_fields = ('code', 'name', 'description')
    ordering = ('service_category', 'order', 'id')
    readonly_fields = ('created_time', 'updated_time')
