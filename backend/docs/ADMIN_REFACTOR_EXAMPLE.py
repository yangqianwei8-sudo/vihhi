# -*- coding: utf-8 -*-
"""
Admin配置重构示例
展示如何使用新的基类重构现有的Admin配置
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from backend.core.admin_base import BaseModelAdmin
from .models import ExampleModel


# ==================== 重构前（旧方式） ====================
@admin.register(ExampleModel)
class ExampleModelAdminOld(admin.ModelAdmin):
    """示例模型管理（旧方式）"""
    list_display = ('name', 'code', 'is_active', 'created_time')
    list_filter = ('is_active', 'created_time')
    search_fields = ('name', 'code')
    ordering = ('-created_time',)
    list_per_page = 50
    readonly_fields = ('created_time', 'updated_time')
    
    fieldsets = (
        ('基本信息', {
            'fields': ('name', 'code', 'description')
        }),
        ('状态信息', {
            'fields': ('is_active',)
        }),
    )
    
    actions = ['activate_items', 'deactivate_items']
    
    def activate_items(self, request, queryset):
        count = queryset.update(is_active=True)
        self.message_user(request, f'已激活 {count} 个项目。')
    activate_items.short_description = '激活选中的项目'
    
    def deactivate_items(self, request, queryset):
        count = queryset.update(is_active=False)
        self.message_user(request, f'已停用 {count} 个项目。')
    deactivate_items.short_description = '停用选中的项目'


# ==================== 重构后（新方式） ====================
@admin.register(ExampleModel)
class ExampleModelAdmin(BaseModelAdmin):
    """
    示例模型管理（新方式）
    
    使用 BaseModelAdmin 后：
    1. 自动提供 list_per_page = 50
    2. 自动处理 created_time 和 updated_time
    3. 自动提供 activate_items 和 deactivate_items 批量操作
    4. 自动添加时间信息字段集
    """
    list_display = ('name', 'code', 'is_active', 'created_time')
    list_filter = ('is_active', 'created_time')
    search_fields = ('name', 'code')
    ordering = ('-created_time',)
    
    # 只需要定义业务相关的字段集
    # 时间信息会自动添加
    fieldsets = (
        ('基本信息', {
            'fields': ('name', 'code', 'description')
        }),
        ('状态信息', {
            'fields': ('is_active',)
        }),
        # 时间信息会自动添加，无需手动定义
    )
    
    # 批量操作已由 StatusAdminMixin 提供，无需手动定义
    # actions = ['activate_items', 'deactivate_items']  # 已自动提供


# ==================== 带自定义方法的示例 ====================
@admin.register(ExampleModel)
class ExampleModelAdminWithCustom(BaseModelAdmin):
    """带自定义方法的示例"""
    list_display = ('name', 'code', 'related_count', 'is_active', 'created_time')
    list_filter = ('is_active', 'created_time')
    search_fields = ('name', 'code')
    ordering = ('-created_time',)
    
    fieldsets = (
        ('基本信息', {
            'fields': ('name', 'code', 'description')
        }),
        ('状态信息', {
            'fields': ('is_active',)
        }),
    )
    
    def related_count(self, obj):
        """显示关联数量（自定义方法）"""
        count = obj.related_items.count() if hasattr(obj, 'related_items') else 0
        if count > 0:
            url = reverse('admin:app_examplemodel_changelist') + f'?filter={obj.id}'
            return format_html('<a href="{}">{} 个</a>', url, count)
        return '0 个'
    related_count.short_description = '关联数量'


# ==================== 只读模型示例 ====================
from backend.core.admin_base import ReadOnlyAdminMixin

@admin.register(ReadOnlyExampleModel)
class ReadOnlyExampleModelAdmin(ReadOnlyAdminMixin, admin.ModelAdmin):
    """只读模型管理"""
    list_display = ('name', 'code', 'created_time')
    list_filter = ('created_time',)
    search_fields = ('name', 'code')
    
    # 只读模型自动禁用增删改操作
    # has_add_permission = False  # 已自动设置
    # has_change_permission = False  # 已自动设置
    # has_delete_permission = False  # 已自动设置


# ==================== 需要审计的模型示例 ====================
from backend.core.admin_base import AuditAdminMixin

@admin.register(AuditExampleModel)
class AuditExampleModelAdmin(AuditAdminMixin, BaseModelAdmin):
    """需要审计的模型管理"""
    list_display = ('name', 'code', 'created_by', 'updated_by', 'created_time')
    list_filter = ('created_time',)
    search_fields = ('name', 'code')
    
    readonly_fields = ('created_by', 'updated_by', 'created_time', 'updated_time')
    
    # AuditAdminMixin 会自动：
    # 1. 保存时记录 created_by 和 updated_by
    # 2. 显示成功消息


# ==================== 复杂字段集示例 ====================
@admin.register(ComplexExampleModel)
class ComplexExampleModelAdmin(BaseModelAdmin):
    """复杂字段集示例"""
    list_display = ('name', 'code', 'department', 'is_active', 'created_time')
    list_filter = ('is_active', 'department', 'created_time')
    search_fields = ('name', 'code', 'department__name')
    ordering = ('-created_time',)
    
    raw_id_fields = ('department',)  # 外键使用raw_id_fields优化性能
    filter_horizontal = ('tags',)  # 多对多使用filter_horizontal
    
    fieldsets = (
        (None, {
            'fields': ('name', 'code')  # 核心字段
        }),
        ('基本信息', {
            'fields': ('description', 'category')
        }),
        ('组织信息', {
            'fields': ('department', 'position')
        }),
        ('关联信息', {
            'fields': ('tags',),
            'description': '选择关联的标签'
        }),
        ('状态信息', {
            'fields': ('is_active',)
        }),
        # 时间信息会自动添加
    )


# ==================== 自定义权限示例 ====================
@admin.register(RestrictedExampleModel)
class RestrictedExampleModelAdmin(BaseModelAdmin):
    """自定义权限示例"""
    list_display = ('name', 'code', 'is_active', 'created_time')
    list_filter = ('is_active', 'created_time')
    search_fields = ('name', 'code')
    
    def has_add_permission(self, request):
        """只有超级用户可以添加"""
        return request.user.is_superuser
    
    def has_change_permission(self, request, obj=None):
        """只有超级用户和员工可以修改"""
        if request.user.is_superuser:
            return True
        return request.user.is_staff
    
    def has_delete_permission(self, request, obj=None):
        """只有超级用户可以删除"""
        return request.user.is_superuser


# ==================== 自定义视图示例 ====================
@admin.register(CustomViewExampleModel)
class CustomViewExampleModelAdmin(BaseModelAdmin):
    """自定义视图示例"""
    list_display = ('name', 'code', 'is_active', 'created_time')
    list_filter = ('is_active', 'created_time')
    search_fields = ('name', 'code')
    
    def changelist_view(self, request, extra_context=None):
        """自定义列表视图"""
        extra_context = extra_context or {}
        extra_context['custom_data'] = '自定义数据'
        return super().changelist_view(request, extra_context)
    
    def change_view(self, request, object_id, form_url='', extra_context=None):
        """自定义详情视图"""
        extra_context = extra_context or {}
        extra_context['custom_data'] = '自定义数据'
        return super().change_view(request, object_id, form_url, extra_context)

