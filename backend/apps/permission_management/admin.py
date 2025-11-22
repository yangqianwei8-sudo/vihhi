from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Count, Q

from .models import PermissionItem


class ModuleFilter(admin.SimpleListFilter):
    """按模块过滤"""
    title = '功能模块'
    parameter_name = 'module'

    def lookups(self, request, model_admin):
        return PermissionItem.MODULE_CHOICES

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(module=self.value())
        return queryset


@admin.register(PermissionItem)
class PermissionItemAdmin(admin.ModelAdmin):
    """权限管理 - 按模块分类"""
    list_display = ('code', 'name', 'module_badge', 'action', 'role_count', 'is_active', 'created_time')
    list_filter = (ModuleFilter, 'action', 'is_active', 'created_time')
    search_fields = ('code', 'name', 'description', 'module', 'action')
    ordering = ('module', 'action', 'code')
    list_per_page = 50
    readonly_fields = ('created_time',)
    fieldsets = (
        ('基本信息', {
            'fields': ('code', 'name', 'module', 'action', 'description')
        }),
        ('状态信息', {
            'fields': ('is_active', 'created_time')
        }),
    )
    
    def module_badge(self, obj):
        """显示模块标签"""
        colors = {
            '项目中心': '#3498db',
            '结算中心': '#2ecc71',
            '生产质量': '#e74c3c',
            '客户成功': '#f39c12',
            '人事管理': '#9b59b6',
            '风险管理': '#1abc9c',
            '系统管理': '#34495e',
            '权限管理': '#e67e22',
            '资源标准': '#16a085',
            '任务协作': '#e91e63',
            '交付客户': '#ff9800',
        }
        color = colors.get(obj.module, '#95a5a6')
        module_name = obj.module  # 现在 module 本身就是中文
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 8px; border-radius: 3px; font-size: 11px;">{}</span>',
            color,
            module_name
        )
    module_badge.short_description = '功能模块'
    module_badge.admin_order_field = 'module'
    
    def role_count(self, obj):
        """显示拥有此权限的角色数量"""
        # 通过反向关联查询
        from backend.apps.system_management.models import Role
        count = Role.objects.filter(custom_permissions=obj, is_active=True).count()
        if count > 0:
            url = reverse('admin:system_management_role_changelist') + f'?custom_permissions__id__exact={obj.id}'
            return format_html('<a href="{}">{} 个角色</a>', url, count)
        return '0 个角色'
    role_count.short_description = '角色数量'
    
    def get_queryset(self, request):
        """优化查询性能"""
        return super().get_queryset(request).select_related()
    
    def changelist_view(self, request, extra_context=None):
        """增强列表视图，添加模块统计"""
        response = super().changelist_view(request, extra_context=extra_context)
        try:
            qs = response.context_data['cl'].queryset
        except (AttributeError, KeyError):
            return response
        
        # 按模块统计权限数量
        module_stats = {}
        for module_code, module_name in PermissionItem.MODULE_CHOICES:
            count = qs.filter(module=module_code).count()
            if count > 0:
                module_stats[module_name] = count
        
        response.context_data['module_stats'] = module_stats
        return response
    
    actions = ['activate_permissions', 'deactivate_permissions']
    
    def activate_permissions(self, request, queryset):
        """批量激活权限"""
        count = queryset.update(is_active=True)
        self.message_user(request, f'已激活 {count} 个权限。')
    activate_permissions.short_description = '激活选中的权限'
    
    def deactivate_permissions(self, request, queryset):
        """批量停用权限"""
        count = queryset.update(is_active=False)
        self.message_user(request, f'已停用 {count} 个权限。')
    deactivate_permissions.short_description = '停用选中的权限'


# 创建按模块分类的管理类
class ProjectCenterPermissionAdmin(admin.ModelAdmin):
    """项目中心权限"""
    list_display = ('code', 'name', 'action', 'role_count', 'is_active')
    list_filter = ('action', 'is_active')
    search_fields = ('code', 'name', 'description')
    ordering = ('action', 'code')
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(module='project_center')
    
    def role_count(self, obj):
        from backend.apps.system_management.models import Role
        count = Role.objects.filter(custom_permissions=obj, is_active=True).count()
        if count > 0:
            url = reverse('admin:system_management_role_changelist') + f'?custom_permissions__id__exact={obj.id}'
            return format_html('<a href="{}">{} 个角色</a>', url, count)
        return '0 个角色'
    role_count.short_description = '角色数量'


# 注册按模块分类的代理模型（如果需要单独的管理界面）
# admin.site.register(PermissionItem, ProjectCenterPermissionAdmin)
