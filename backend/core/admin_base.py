# -*- coding: utf-8 -*-
"""
Django Admin 统一基类和混入类
提供标准化的Admin配置，确保所有模块的Admin配置风格一致
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.contrib import messages
from django.utils import timezone
from django.db.models import QuerySet
from django.http import HttpResponse
import csv


class BaseAdminMixin:
    """
    Admin基类混入，提供通用的配置和方法
    所有Admin类都应该继承这个混入类
    """
    # 通用配置
    list_per_page = 50
    list_max_show_all = 200
    preserve_filters = True
    
    # 默认的只读字段（子类可以覆盖）
    default_readonly_fields = ('created_time', 'updated_time')
    
    def get_readonly_fields(self, request, obj=None):
        """统一处理只读字段"""
        readonly = list(self.readonly_fields) if hasattr(self, 'readonly_fields') else []
        
        # 如果是新增，created_time和updated_time应该是只读的
        if obj is None:
            if 'created_time' not in readonly:
                readonly.append('created_time')
            if 'updated_time' not in readonly:
                readonly.append('updated_time')
        
        return readonly
    
    def get_fieldsets(self, request, obj=None):
        """统一字段集结构，确保有时间信息部分"""
        # 先尝试调用父类的 get_fieldsets 方法
        # 如果父类（admin.ModelAdmin）有 get_fieldsets，会处理 fieldsets 属性
        try:
            fieldsets = super().get_fieldsets(request, obj)
        except AttributeError:
            # 如果父类没有 get_fieldsets 方法，使用 fieldsets 属性
            if hasattr(self, 'fieldsets') and self.fieldsets:
                fieldsets = self.fieldsets
            else:
                fieldsets = ()
        
        # 检查是否已有时间信息部分
        has_time_section = any(
            section[0] == '时间信息' or section[0] == '系统信息'
            for section in fieldsets
        )
        
        # 如果没有时间信息部分，且模型有时间字段，则添加
        if not has_time_section:
            model = self.model
            time_fields = []
            if hasattr(model, 'created_time'):
                time_fields.append('created_time')
            if hasattr(model, 'updated_time'):
                time_fields.append('updated_time')
            
            if time_fields:
                fieldsets = fieldsets + (
                    ('时间信息', {
                        'fields': time_fields,
                        'classes': ('collapse',)
                    }),
                )
        
        return fieldsets


class StandardAdminMixin(BaseAdminMixin):
    """
    标准Admin混入，提供标准的列表显示和筛选配置
    适用于大多数模型
    """
    def get_list_display(self, request):
        """获取列表显示字段"""
        list_display = list(self.list_display) if hasattr(self, 'list_display') else []
        
        # 如果没有配置list_display，使用默认字段
        if not list_display:
            model = self.model
            default_fields = []
            
            # 根据模型字段自动添加
            if hasattr(model, 'name'):
                default_fields.append('name')
            elif hasattr(model, 'title'):
                default_fields.append('title')
            elif hasattr(model, 'code'):
                default_fields.append('code')
            
            if hasattr(model, 'is_active'):
                default_fields.append('is_active')
            
            if hasattr(model, 'created_time'):
                default_fields.append('created_time')
            
            return default_fields if default_fields else ['__str__']
        
        return list_display
    
    def get_list_filter(self, request):
        """获取列表筛选字段"""
        list_filter = list(self.list_filter) if hasattr(self, 'list_filter') else []
        
        # 自动添加常用筛选字段
        model = self.model
        if hasattr(model, 'is_active') and 'is_active' not in list_filter:
            list_filter.insert(0, 'is_active')
        
        if hasattr(model, 'created_time') and 'created_time' not in list_filter:
            list_filter.append('created_time')
        
        return list_filter
    
    def get_search_fields(self, request):
        """获取搜索字段"""
        search_fields = list(self.search_fields) if hasattr(self, 'search_fields') else []
        
        # 自动添加常用搜索字段
        model = self.model
        if not search_fields:
            if hasattr(model, 'name'):
                search_fields.append('name')
            if hasattr(model, 'title'):
                search_fields.append('title')
            if hasattr(model, 'code'):
                search_fields.append('code')
            if hasattr(model, 'description'):
                search_fields.append('description')
        
        return search_fields


class TimestampAdminMixin(BaseAdminMixin):
    """
    时间戳混入，自动处理created_time和updated_time字段
    """
    def save_model(self, request, obj, form, change):
        """保存时自动更新时间戳"""
        if not change:  # 新增
            if hasattr(obj, 'created_time') and not obj.created_time:
                obj.created_time = timezone.now()
        
        if hasattr(obj, 'updated_time'):
            obj.updated_time = timezone.now()
        
        super().save_model(request, obj, form, change)


class StatusAdminMixin(BaseAdminMixin):
    """
    状态管理混入，提供激活/停用的批量操作
    适用于有is_active字段的模型
    """
    def get_actions(self, request):
        """添加批量操作"""
        actions = super().get_actions(request)
        
        # 检查模型是否有is_active字段
        if hasattr(self.model, 'is_active'):
            if 'activate_items' not in actions:
                actions['activate_items'] = (
                    self.activate_items,
                    'activate_items',
                    '激活选中的项目'
                )
            if 'deactivate_items' not in actions:
                actions['deactivate_items'] = (
                    self.deactivate_items,
                    'deactivate_items',
                    '停用选中的项目'
                )
        
        return actions
    
    def activate_items(self, request, queryset):
        """批量激活"""
        count = queryset.update(is_active=True)
        self.message_user(request, f'已激活 {count} 个项目。', messages.SUCCESS)
    activate_items.short_description = '激活选中的项目'
    
    def deactivate_items(self, request, queryset):
        """批量停用"""
        count = queryset.update(is_active=False)
        self.message_user(request, f'已停用 {count} 个项目。', messages.SUCCESS)
    deactivate_items.short_description = '停用选中的项目'


class QueryOptimizationMixin(BaseAdminMixin):
    """
    查询优化混入，自动优化查询性能
    子类可以通过设置 select_related_fields 和 prefetch_related_fields 来优化查询
    """
    # 子类可以覆盖这些属性来指定需要优化的关联字段
    select_related_fields = None  # 例如: ['department', 'created_by']
    prefetch_related_fields = None  # 例如: ['roles', 'permissions']
    
    def get_queryset(self, request):
        """优化查询集"""
        qs = super().get_queryset(request)
        
        # 应用 select_related 优化（用于 ForeignKey 和 OneToOneField）
        if self.select_related_fields:
            qs = qs.select_related(*self.select_related_fields)
        
        # 应用 prefetch_related 优化（用于 ManyToManyField 和反向 ForeignKey）
        if self.prefetch_related_fields:
            qs = qs.prefetch_related(*self.prefetch_related_fields)
        
        return qs


class BaseModelAdmin(QueryOptimizationMixin, StandardAdminMixin, TimestampAdminMixin, StatusAdminMixin, admin.ModelAdmin):
    """
    标准模型Admin基类
    所有普通模型的Admin都应该继承这个类
    
    特性：
    - 自动查询优化（可通过select_related_fields和prefetch_related_fields配置）
    - 标准化的列表显示和筛选
    - 自动时间戳处理
    - 批量激活/停用操作
    - 状态标签格式化支持
    """
    pass


class ReadOnlyAdminMixin(BaseAdminMixin):
    """
    只读Admin混入，用于只读模型
    """
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False


class AuditAdminMixin(BaseAdminMixin):
    """
    审计混入，记录操作日志
    """
    def save_model(self, request, obj, form, change):
        """保存时记录操作人"""
        if change:
            if hasattr(obj, 'updated_by') and not obj.updated_by:
                obj.updated_by = request.user
        else:
            if hasattr(obj, 'created_by') and not obj.created_by:
                obj.created_by = request.user
        
        super().save_model(request, obj, form, change)
        
        # 显示成功消息
        action = '更新' if change else '创建'
        messages.success(request, f'已成功{action} {obj}。')


class LinkAdminMixin(BaseAdminMixin):
    """
    链接混入，提供生成链接的辅助方法
    """
    def make_link(self, url, text, title=None):
        """生成HTML链接"""
        attrs = {'href': url}
        if title:
            attrs['title'] = title
        return format_html('<a {}>{}</a>', 
                          ' '.join(f'{k}="{v}"' for k, v in attrs.items()),
                          text)
    
    def reverse_admin_url(self, view_name, args=None, kwargs=None):
        """生成Admin URL"""
        app_label = self.model._meta.app_label
        model_name = self.model._meta.model_name
        return reverse(f'admin:{app_label}_{model_name}_{view_name}', args=args, kwargs=kwargs)


class ExportMixin(BaseAdminMixin):
    """
    数据导出混入，提供CSV导出功能
    """
    # 导出时包含的字段（如果为None，则使用list_display）
    export_fields = None
    # 导出文件名前缀
    export_filename_prefix = None
    
    def get_export_fields(self):
        """获取导出字段列表"""
        if self.export_fields:
            return self.export_fields
        # 如果没有指定，使用list_display（排除方法）
        if hasattr(self, 'list_display'):
            return [f for f in self.list_display if not callable(getattr(self, f, None))]
        return []
    
    def export_as_csv(self, request, queryset):
        """导出为CSV"""
        meta = self.model._meta
        field_names = self.get_export_fields()
        
        response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
        filename_prefix = self.export_filename_prefix or meta.verbose_name
        response['Content-Disposition'] = f'attachment; filename="{filename_prefix}_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'
        
        writer = csv.writer(response)
        
        # 写入表头
        headers = []
        for field_name in field_names:
            if hasattr(self, field_name):
                # 如果是方法，使用short_description
                method = getattr(self, field_name)
                if hasattr(method, 'short_description'):
                    headers.append(method.short_description)
                else:
                    headers.append(field_name)
            else:
                # 尝试获取字段的verbose_name
                try:
                    field = meta.get_field(field_name)
                    headers.append(field.verbose_name or field_name)
                except:
                    headers.append(field_name)
        writer.writerow(headers)
        
        # 写入数据
        for obj in queryset:
            row = []
            for field_name in field_names:
                if hasattr(self, field_name):
                    # 如果是方法，调用它
                    method = getattr(self, field_name)
                    value = method(obj)
                    # 如果是HTML，提取文本
                    if hasattr(value, '__html__'):
                        from django.utils.html import strip_tags
                        value = strip_tags(str(value))
                    row.append(str(value) if value is not None else '')
                else:
                    # 直接获取字段值
                    value = getattr(obj, field_name, '')
                    row.append(str(value) if value is not None else '')
            writer.writerow(row)
        
        return response
    
    export_as_csv.short_description = '导出选中项为CSV'
    
    def get_actions(self, request):
        """添加导出操作"""
        actions = super().get_actions(request)
        actions['export_as_csv'] = (
            self.export_as_csv,
            'export_as_csv',
            '导出选中项为CSV'
        )
        return actions


class StatusBadgeMixin(BaseAdminMixin):
    """
    状态标签混入，提供统一的状态显示格式
    """
    def format_status_badge(self, status_value, status_display=None, color_map=None):
        """
        格式化状态为带颜色的标签
        
        Args:
            status_value: 状态值
            status_display: 状态显示文本（如果为None，会尝试获取get_xxx_display）
            color_map: 颜色映射字典，例如 {'active': '#28a745', 'inactive': '#dc3545'}
        """
        if status_display is None:
            # 尝试自动获取显示文本
            status_display = str(status_value)
        
        # 默认颜色映射
        default_colors = {
            'active': '#28a745',
            'inactive': '#dc3545',
            'pending': '#ffc107',
            'completed': '#28a745',
            'cancelled': '#6c757d',
            'success': '#28a745',
            'failed': '#dc3545',
            'warning': '#ffc107',
        }
        
        if color_map:
            default_colors.update(color_map)
        
        # 根据状态值选择颜色
        status_lower = str(status_value).lower()
        color = default_colors.get(status_lower, '#6c757d')
        
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 8px; border-radius: 3px; font-size: 11px;">{}</span>',
            color,
            status_display
        )
    
    def format_boolean_badge(self, value, true_text='是', false_text='否'):
        """格式化布尔值为标签"""
        if value:
            return format_html(
                '<span style="background: #28a745; color: white; padding: 3px 8px; border-radius: 3px; font-size: 11px;">{}</span>',
                true_text
            )
        else:
            return format_html(
                '<span style="background: #dc3545; color: white; padding: 3px 8px; border-radius: 3px; font-size: 11px;">{}</span>',
                false_text
            )


class DateRangeFilterMixin(BaseAdminMixin):
    """
    日期范围过滤器混入，提供日期范围筛选功能
    需要安装 django-admin-date-range-filter 或自定义实现
    """
    date_range_fields = None  # 例如: ['created_time', 'updated_time']
    
    def get_list_filter(self, request):
        """添加日期范围过滤器"""
        list_filter = list(super().get_list_filter(request))
        
        if self.date_range_fields:
            for field in self.date_range_fields:
                # 这里可以添加自定义的日期范围过滤器
                # 目前先添加普通的日期过滤器
                if field not in list_filter:
                    list_filter.append(field)
        
        return list_filter


# 导出常用的Admin基类
__all__ = [
    'BaseAdminMixin',
    'StandardAdminMixin',
    'TimestampAdminMixin',
    'StatusAdminMixin',
    'BaseModelAdmin',
    'ReadOnlyAdminMixin',
    'AuditAdminMixin',
    'LinkAdminMixin',
    'QueryOptimizationMixin',
    'ExportMixin',
    'StatusBadgeMixin',
    'DateRangeFilterMixin',
]

