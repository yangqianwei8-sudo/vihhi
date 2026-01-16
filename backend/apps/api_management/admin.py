from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from backend.apps.api_management.models import (
    ExternalSystem, ApiInterface, ApiCallLog, ApiTestRecord
)
from backend.apps.api_management.forms import ApiInterfaceForm, ApiTestRecordForm
from backend.core.admin_base import BaseModelAdmin, AuditAdminMixin, LinkAdminMixin, ReadOnlyAdminMixin, StatusBadgeMixin


@admin.register(ExternalSystem)
class ExternalSystemAdmin(StatusBadgeMixin, LinkAdminMixin, AuditAdminMixin, BaseModelAdmin):
    """外部系统管理"""
    list_display = ('code', 'name', 'base_url', 'status_badge', 'api_count', 'contact_person', 'contact_phone', 'is_active', 'created_time')
    list_filter = ('status', 'is_active', 'created_time')
    search_fields = ('code', 'name', 'base_url', 'contact_person', 'contact_phone')
    ordering = ('name',)
    raw_id_fields = ('created_by',)
    readonly_fields = ('code', 'api_count', 'created_time', 'updated_time')
    fieldsets = (
        ('基本信息', {
            'fields': ('code', 'name', 'description', 'status', 'is_active')
        }),
        ('系统配置', {
            'fields': ('base_url',)
        }),
        ('联系信息', {
            'fields': ('contact_person', 'contact_phone', 'contact_email')
        }),
        ('统计信息', {
            'fields': ('api_count', 'created_by')
        }),
        # 时间信息会自动添加
    )
    
    def save_model(self, request, obj, form, change):
        """保存时自动从环境变量同步DeepSeek API Key"""
        super().save_model(request, obj, form, change)
        
        # 如果是DeepSeek系统，自动同步API Key到相关接口
        if obj.code == 'DEEPSEEK':
            from django.conf import settings
            api_key = getattr(settings, 'DEEPSEEK_API_KEY', '')
            if api_key:
                # 更新所有DeepSeek API接口的认证配置
                for api_interface in obj.api_interfaces.filter(is_active=True):
                    if api_interface.auth_type == 'bearer_token' and api_interface.auth_config:
                        auth_config = api_interface.auth_config.copy()
                        if 'token' in auth_config:
                            auth_config['token'] = api_key
                            api_interface.auth_config = auth_config
                            api_interface.save(update_fields=['auth_config', 'updated_time'])
    
    def status_badge(self, obj):
        """状态标签"""
        return self.format_status_badge(
            obj.status,
            obj.get_status_display(),
            color_map={'active': '#28a745', 'inactive': '#dc3545'}
        )
    status_badge.short_description = '状态'
    status_badge.admin_order_field = 'status'
    
    def api_count(self, obj):
        """API接口数量"""
        count = obj.api_interfaces.filter(is_active=True).count()
        url = reverse('admin:api_management_apiinterface_changelist') + f'?external_system__id__exact={obj.id}'
        return self.make_link(url, str(count))
    api_count.short_description = 'API数量'


@admin.register(ApiInterface)
class ApiInterfaceAdmin(StatusBadgeMixin, AuditAdminMixin, BaseModelAdmin):
    """API接口管理"""
    form = ApiInterfaceForm
    list_display = ('code', 'name', 'external_system', 'method_badge', 'url', 'auth_type', 'status_badge', 'version', 'is_active', 'created_time')
    list_filter = ('external_system', 'method', 'auth_type', 'status', 'is_active', 'created_time')
    search_fields = ('code', 'name', 'url', 'description')
    ordering = ('-created_time',)
    raw_id_fields = ('external_system', 'created_by')
    readonly_fields = ('code', 'full_url', 'created_time', 'updated_time')
    fieldsets = (
        ('基本信息', {
            'fields': ('code', 'name', 'external_system', 'description', 'status', 'is_active', 'version')
        }),
        ('接口配置', {
            'fields': ('url', 'full_url', 'method', 'timeout', 'retry_count')
        }),
        ('认证配置', {
            'fields': ('auth_type', 'auth_config'),
            'description': '对于DeepSeek API，如果环境变量中配置了DEEPSEEK_API_KEY，保存时会自动同步到认证配置中'
        }),
        ('请求配置', {
            'fields': ('request_headers', 'request_params', 'request_body_schema'),
            'classes': ('collapse',)
        }),
        ('响应配置', {
            'fields': ('response_schema',),
            'classes': ('collapse',)
        }),
        ('其他信息', {
            'fields': ('created_by',)
        }),
        # 时间信息会自动添加
    )
    
    def method_badge(self, obj):
        """请求方法标签"""
        colors = {
            'GET': '#28a745',
            'POST': '#007bff',
            'PUT': '#ffc107',
            'PATCH': '#17a2b8',
            'DELETE': '#dc3545',
        }
        color = colors.get(obj.method, '#6c757d')
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 8px; border-radius: 3px; font-size: 11px; font-weight: bold;">{}</span>',
            color,
            obj.method
        )
    method_badge.short_description = '方法'
    method_badge.admin_order_field = 'method'
    
    def status_badge(self, obj):
        """状态标签"""
        return self.format_status_badge(
            obj.status,
            obj.get_status_display(),
            color_map={'active': '#28a745', 'inactive': '#dc3545', 'deprecated': '#6c757d'}
        )
    status_badge.short_description = '状态'
    status_badge.admin_order_field = 'status'
    
    def save_model(self, request, obj, form, change):
        """保存时自动从环境变量同步DeepSeek API Key"""
        # 如果是DeepSeek系统的API接口，且使用Bearer Token认证
        if (obj.external_system and obj.external_system.code == 'DEEPSEEK' and 
            obj.auth_type == 'bearer_token'):
            from django.conf import settings
            api_key = getattr(settings, 'DEEPSEEK_API_KEY', '')
            if api_key and obj.auth_config:
                # 更新认证配置中的token
                auth_config = obj.auth_config.copy()
                if 'token' in auth_config:
                    auth_config['token'] = api_key
                    obj.auth_config = auth_config
        
        super().save_model(request, obj, form, change)


@admin.register(ApiCallLog)
class ApiCallLogAdmin(StatusBadgeMixin, ReadOnlyAdminMixin, BaseModelAdmin):
    """API调用日志管理（只读）"""
    list_display = ('api_interface', 'request_method', 'request_url', 'response_status', 'status_badge', 'duration', 'called_by', 'called_time')
    list_filter = ('status', 'request_method', 'response_status', 'called_time')
    search_fields = ('api_interface__name', 'api_interface__code', 'request_url', 'error_message', 'called_by__username')
    ordering = ('-called_time',)
    raw_id_fields = ('api_interface', 'called_by')
    readonly_fields = ('called_time',)
    date_hierarchy = 'called_time'
    fieldsets = (
        ('基本信息', {
            'fields': ('api_interface', 'called_by', 'called_time', 'status', 'duration')
        }),
        ('请求信息', {
            'fields': ('request_url', 'request_method', 'request_headers', 'request_params', 'request_body'),
            'classes': ('collapse',)
        }),
        ('响应信息', {
            'fields': ('response_status', 'response_headers', 'response_body'),
            'classes': ('collapse',)
        }),
        ('错误信息', {
            'fields': ('error_message',),
            'classes': ('collapse',)
        }),
    )
    
    def status_badge(self, obj):
        """状态标签"""
        return self.format_status_badge(
            obj.status,
            obj.get_status_display(),
            color_map={'success': '#28a745', 'failed': '#dc3545', 'timeout': '#ffc107'}
        )
    status_badge.short_description = '状态'
    status_badge.admin_order_field = 'status'
    
    # ReadOnlyAdminMixin 已自动禁用增删改权限


@admin.register(ApiTestRecord)
class ApiTestRecordAdmin(StatusBadgeMixin, AuditAdminMixin, BaseModelAdmin):
    """API测试记录管理"""
    form = ApiTestRecordForm
    list_display = ('api_interface', 'test_name', 'status_badge', 'expected_status', 'actual_status', 'test_duration', 'tested_by', 'tested_time')
    list_filter = ('status', 'tested_time')
    search_fields = ('api_interface__name', 'api_interface__code', 'test_name', 'error_message', 'tested_by__username')
    ordering = ('-tested_time',)
    raw_id_fields = ('api_interface', 'tested_by')
    readonly_fields = ('tested_time',)
    date_hierarchy = 'tested_time'
    fieldsets = (
        ('基本信息', {
            'fields': ('api_interface', 'test_name', 'status', 'tested_by', 'tested_time', 'test_duration')
        }),
        ('测试配置', {
            'fields': ('test_params', 'test_body', 'expected_status', 'expected_response')
        }),
        ('测试结果', {
            'fields': ('actual_status', 'actual_response', 'error_message')
        }),
    )
    
    def status_badge(self, obj):
        """状态标签"""
        return self.format_status_badge(
            obj.status,
            obj.get_status_display(),
            color_map={'pending': '#6c757d', 'success': '#28a745', 'failed': '#dc3545'}
        )
    status_badge.short_description = '状态'
    status_badge.admin_order_field = 'status'
