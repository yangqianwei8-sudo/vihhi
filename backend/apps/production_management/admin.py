"""
项目中心模块的Admin配置
包含专业配置：服务类型和服务专业
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse, path
from django import forms
from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required

from backend.apps.production_management.models import (
    ServiceType, ServiceProfession, BusinessType, DesignStage,
    StructureType, DesignUnitCategory, Project,
)
# BusinessContract, BusinessPaymentPlan, ResultFileType, ContractParty 已迁移到 contract_management
# ComprehensiveAdjustmentCoefficient 已迁移到 contract_management
from backend.core.admin_base import BaseModelAdmin, AuditAdminMixin, LinkAdminMixin


class ServiceProfessionInline(admin.TabularInline):
    """服务专业内联编辑"""
    model = ServiceProfession
    extra = 1
    fields = ('code', 'name', 'order')
    ordering = ('order',)


@admin.register(ServiceType)
class ServiceTypeAdmin(LinkAdminMixin, BaseModelAdmin):
    """服务类型管理"""
    list_display = ('name', 'code', 'order', 'profession_count')
    list_filter = ('order',)
    search_fields = ('name', 'code')
    ordering = ('order', 'id')
    fieldsets = (
        ('基本信息', {
            'fields': ('code', 'name', 'order')
        }),
    )
    inlines = [ServiceProfessionInline]
    
    def profession_count(self, obj):
        """显示服务类型下的专业数量"""
        count = obj.professions.count()
        if count > 0:
            url = f'/admin/production_management/serviceprofession/?service_type__id__exact={obj.id}'
            return self.make_link(url, f'{count} 个专业')
        return '0 个专业'
    profession_count.short_description = '专业数量'


@admin.register(ServiceProfession)
class ServiceProfessionAdmin(BaseModelAdmin):
    """服务专业管理"""
    list_display = ('name', 'code', 'service_type', 'order')
    list_filter = ('service_type',)
    search_fields = ('name', 'code', 'service_type__name')
    ordering = ('service_type__order', 'order', 'id')
    raw_id_fields = ('service_type',)
    fieldsets = (
        ('基本信息', {
            'fields': ('service_type', 'code', 'name', 'order')
        }),
    )


@admin.register(BusinessType)
class BusinessTypeAdmin(LinkAdminMixin, BaseModelAdmin):
    """项目业态管理"""
    list_display = ('name', 'code', 'order', 'is_active', 'project_count')
    list_filter = ('is_active',)
    search_fields = ('name', 'code')
    ordering = ('order', 'id')
    fieldsets = (
        ('基本信息', {
            'fields': ('code', 'name', 'order', 'is_active', 'description')
        }),
    )
    
    def project_count(self, obj):
        """显示使用该业态的项目数量"""
        count = obj.projects.count()
        if count > 0:
            url = f'/admin/production_management/project/?business_type__id__exact={obj.id}'
            return self.make_link(url, f'{count} 个项目')
        return '0 个项目'
    project_count.short_description = '项目数量'


@admin.register(DesignStage)
class DesignStageAdmin(LinkAdminMixin, BaseModelAdmin):
    """图纸阶段管理"""
    list_display = ('name', 'code', 'order', 'is_active', 'project_count')
    list_filter = ('is_active',)
    search_fields = ('name', 'code')
    ordering = ('order', 'id')
    fieldsets = (
        ('基本信息', {
            'fields': ('code', 'name', 'order', 'is_active', 'description')
        }),
    )
    
    def project_count(self, obj):
        """显示使用该图纸阶段的项目数量"""
        count = obj.projects.count()
        if count > 0:
            url = f'/admin/production_management/project/?design_stage__id__exact={obj.id}'
            return self.make_link(url, f'{count} 个项目')
        return '0 个项目'
    project_count.short_description = '项目数量'


@admin.register(StructureType)
class StructureTypeAdmin(LinkAdminMixin, BaseModelAdmin):
    """结构形式管理"""
    list_display = ('name', 'code', 'order', 'is_active', 'contract_count', 'project_count')
    list_filter = ('is_active',)
    search_fields = ('name', 'code')
    ordering = ('order', 'id')
    fieldsets = (
        ('基本信息', {
            'fields': ('code', 'name', 'order', 'is_active', 'description')
        }),
    )
    
    def contract_count(self, obj):
        """显示使用该结构形式的合同数量"""
        from backend.apps.contract_management.models import BusinessContract
        count = BusinessContract.objects.filter(structure_type=obj.code).count()
        if count > 0:
            url = f'/admin/contract_management/businesscontract/?structure_type={obj.code}'
            return self.make_link(url, f'{count} 个合同')
        return '0 个合同'
    contract_count.short_description = '合同数量'
    
    def project_count(self, obj):
        """显示使用该结构形式的项目数量"""
        count = Project.objects.filter(structure_type=obj.code).count()
        if count > 0:
            url = f'/admin/production_management/project/?structure_type={obj.code}'
            return self.make_link(url, f'{count} 个项目')
        return '0 个项目'
    project_count.short_description = '项目数量'


@admin.register(DesignUnitCategory)
class DesignUnitCategoryAdmin(LinkAdminMixin, BaseModelAdmin):
    """设计单位分类管理"""
    list_display = ('name', 'code', 'order', 'is_active', 'contract_count')
    list_filter = ('is_active',)
    search_fields = ('name', 'code')
    ordering = ('order', 'id')
    fieldsets = (
        ('基本信息', {
            'fields': ('code', 'name', 'order', 'is_active', 'description')
        }),
    )
    
    def contract_count(self, obj):
        """显示使用该分类的合同数量"""
        from backend.apps.contract_management.models import BusinessContract
        count = BusinessContract.objects.filter(design_unit_category=obj.code).count()
        if count > 0:
            url = f'/admin/contract_management/businesscontract/?design_unit_category={obj.code}'
            return self.make_link(url, f'{count} 个合同')
        return '0 个合同'
    contract_count.short_description = '合同数量'



