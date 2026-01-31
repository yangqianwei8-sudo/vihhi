"""
基础数据 Admin
"""
from django.contrib import admin
from .models import (
    ServiceType, ServiceProfession, BusinessType,
    DesignStage, StructureType, DesignUnitCategory,
)


class ServiceProfessionInline(admin.TabularInline):
    model = ServiceProfession
    extra = 0


@admin.register(ServiceType)
class ServiceTypeAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'order']
    search_fields = ['code', 'name']
    ordering = ['order', 'id']
    inlines = [ServiceProfessionInline]


@admin.register(ServiceProfession)
class ServiceProfessionAdmin(admin.ModelAdmin):
    list_display = ['service_type', 'code', 'name', 'order']
    list_filter = ['service_type']
    search_fields = ['code', 'name']
    ordering = ['service_type__order', 'order', 'id']


@admin.register(BusinessType)
class BusinessTypeAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'order', 'is_active']
    search_fields = ['code', 'name']
    list_filter = ['is_active']
    ordering = ['order', 'id']


@admin.register(DesignStage)
class DesignStageAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'order', 'is_active']
    search_fields = ['code', 'name']
    list_filter = ['is_active']
    ordering = ['order', 'id']


@admin.register(StructureType)
class StructureTypeAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'order', 'is_active']
    search_fields = ['code', 'name']
    list_filter = ['is_active']
    ordering = ['order', 'id']


@admin.register(DesignUnitCategory)
class DesignUnitCategoryAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'order', 'is_active']
    search_fields = ['code', 'name']
    list_filter = ['is_active']
    ordering = ['order', 'id']
