"""
项目中心模块的Admin配置
包含专业配置：服务类型和服务专业
"""

from django.contrib import admin
from django.utils.html import format_html

from .models import ServiceType, ServiceProfession


class ServiceProfessionInline(admin.TabularInline):
    """服务专业内联编辑"""
    model = ServiceProfession
    extra = 1
    fields = ('code', 'name', 'order')
    ordering = ('order',)


@admin.register(ServiceType)
class ServiceTypeAdmin(admin.ModelAdmin):
    """服务类型管理"""
    list_display = ('name', 'code', 'order', 'profession_count')
    list_filter = ('order',)
    search_fields = ('name', 'code')
    ordering = ('order', 'id')
    list_per_page = 50
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
            url = f'/admin/project_center/serviceprofession/?service_type__id__exact={obj.id}'
            return format_html('<a href="{}">{} 个专业</a>', url, count)
        return '0 个专业'
    profession_count.short_description = '专业数量'


@admin.register(ServiceProfession)
class ServiceProfessionAdmin(admin.ModelAdmin):
    """服务专业管理"""
    list_display = ('name', 'code', 'service_type', 'order')
    list_filter = ('service_type',)
    search_fields = ('name', 'code', 'service_type__name')
    ordering = ('service_type__order', 'order', 'id')
    list_per_page = 50
    raw_id_fields = ('service_type',)
    fieldsets = (
        ('基本信息', {
            'fields': ('service_type', 'code', 'name', 'order')
        }),
    )

