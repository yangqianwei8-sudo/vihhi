from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from django.contrib import messages
from django.db.models import Count

from .models import (
    User, Department, Role, RegistrationRequest,
    DataDictionary, SystemConfig
)
from .services_registration import finalize_approval


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    """角色管理"""
    list_display = ('name', 'code', 'user_count', 'permission_count', 'is_active', 'created_time')
    list_filter = ('is_active', 'created_time')
    search_fields = ('name', 'code', 'description')
    ordering = ('-created_time',)
    list_per_page = 50
    filter_horizontal = ('custom_permissions', 'permissions')
    readonly_fields = ('created_time',)
    fieldsets = (
        ('基本信息', {
            'fields': ('name', 'code', 'description', 'is_active')
        }),
        ('Django 权限', {
            'fields': ('permissions',),
            'description': 'Django 框架的内置权限（如 add_user, change_user 等）'
        }),
        ('业务权限', {
            'fields': ('custom_permissions',),
            'description': '业务系统的自定义权限（如 project_center.view_all 等）'
        }),
        ('其他信息', {
            'fields': ('created_time',)
        }),
    )
    
    def user_count(self, obj):
        """显示拥有此角色的用户数量"""
        count = obj.users.filter(is_active=True).count()
        if count > 0:
            url = reverse('admin:system_management_user_changelist') + f'?roles__id__exact={obj.id}'
            return format_html('<a href="{}">{} 个用户</a>', url, count)
        return '0 个用户'
    user_count.short_description = '用户数量'
    
    def permission_count(self, obj):
        """显示此角色拥有的权限数量"""
        count = obj.custom_permissions.filter(is_active=True).count()
        if count > 0:
            url = reverse('admin:permission_management_permissionitem_changelist') + f'?roles__id__exact={obj.id}'
            return format_html('<a href="{}">{} 个权限</a>', url, count)
        return '0 个权限'
    permission_count.short_description = '权限数量'
    
    actions = ['activate_roles', 'deactivate_roles']
    
    def activate_roles(self, request, queryset):
        """批量激活角色"""
        count = queryset.update(is_active=True)
        self.message_user(request, f'已激活 {count} 个角色。')
    activate_roles.short_description = '激活选中的角色'
    
    def deactivate_roles(self, request, queryset):
        """批量停用角色"""
        count = queryset.update(is_active=False)
        self.message_user(request, f'已停用 {count} 个角色。')
    deactivate_roles.short_description = '停用选中的角色'


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    """部门管理"""
    list_display = ('name', 'code', 'parent', 'leader', 'member_count', 'order', 'is_active', 'created_time')
    list_filter = ('is_active', 'parent', 'created_time')
    search_fields = ('name', 'code', 'description')
    ordering = ('order', 'name')
    list_per_page = 50
    raw_id_fields = ('parent', 'leader')
    readonly_fields = ('created_time',)
    fieldsets = (
        ('基本信息', {
            'fields': ('name', 'code', 'parent', 'leader', 'description')
        }),
        ('组织信息', {
            'fields': ('order', 'is_active', 'created_time')
        }),
    )
    
    def member_count(self, obj):
        """显示部门成员数量"""
        count = obj.members.filter(is_active=True).count()
        if count > 0:
            url = reverse('admin:system_management_user_changelist') + f'?department__id__exact={obj.id}'
            return format_html('<a href="{}">{} 人</a>', url, count)
        return '0 人'
    member_count.short_description = '成员数量'
    
    actions = ['activate_departments', 'deactivate_departments']
    
    def activate_departments(self, request, queryset):
        """批量激活部门"""
        count = queryset.update(is_active=True)
        self.message_user(request, f'已激活 {count} 个部门。')
    activate_departments.short_description = '激活选中的部门'
    
    def deactivate_departments(self, request, queryset):
        """批量停用部门"""
        count = queryset.update(is_active=False)
        self.message_user(request, f'已停用 {count} 个部门。')
    deactivate_departments.short_description = '停用选中的部门'


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    """用户管理"""
    list_display = (
        'username',
        'get_full_name',
        'email',
        'phone',
        'department',
        'position',
        'get_user_type_display',
        'role_list',
        'is_active',
        'is_staff',
        'is_superuser',
        'date_joined',
    )
    list_filter = ('user_type', 'department', 'is_active', 'is_staff', 'is_superuser', 'roles', 'date_joined', 'profile_completed')
    search_fields = ('username', 'first_name', 'last_name', 'email', 'phone', 'position')
    ordering = ('-date_joined',)
    list_per_page = 50
    date_hierarchy = 'date_joined'
    filter_horizontal = ('roles', 'groups', 'user_permissions')
    raw_id_fields = ('department',)
    readonly_fields = ('last_login', 'date_joined', 'created_time', 'updated_time')
    
    fieldsets = (
        (None, {
            'fields': ('username', 'password')
        }),
        ('个人信息', {
            'fields': ('first_name', 'last_name', 'email', 'phone', 'avatar')
        }),
        ('组织信息', {
            'fields': ('department', 'position', 'user_type', 'client_type')
        }),
        ('权限信息', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions', 'roles')
        }),
        ('其他信息', {
            'fields': ('profile_completed', 'notification_preferences')
        }),
        ('时间信息', {
            'fields': ('last_login', 'date_joined', 'created_time', 'updated_time')
        }),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2', 'email', 'phone'),
        }),
        ('组织信息', {
            'classes': ('wide',),
            'fields': ('department', 'position', 'user_type', 'is_staff', 'is_superuser'),
        }),
    )
    
    def role_list(self, obj):
        """显示用户角色列表"""
        roles = obj.roles.filter(is_active=True)
        if roles.exists():
            role_links = []
            for role in roles[:3]:  # 最多显示3个角色
                url = reverse('admin:system_management_role_change', args=[role.id])
                role_links.append(format_html('<a href="{}">{}</a>', url, role.name))
            if roles.count() > 3:
                role_links.append(f'...等{roles.count()}个')
            return format_html(', '.join(role_links))
        return '-'
    role_list.short_description = '角色'
    
    actions = ['activate_users', 'deactivate_users', 'make_staff', 'remove_staff', 'make_superuser', 'remove_superuser']
    
    def activate_users(self, request, queryset):
        """批量激活用户"""
        count = queryset.update(is_active=True)
        self.message_user(request, f'已激活 {count} 个用户。')
    activate_users.short_description = '激活选中的用户'
    
    def deactivate_users(self, request, queryset):
        """批量停用用户"""
        count = queryset.update(is_active=False)
        self.message_user(request, f'已停用 {count} 个用户。')
    deactivate_users.short_description = '停用选中的用户'
    
    def make_staff(self, request, queryset):
        """批量设置为员工"""
        count = queryset.update(is_staff=True)
        self.message_user(request, f'已将 {count} 个用户设置为员工。')
    make_staff.short_description = '设置为员工'
    
    def remove_staff(self, request, queryset):
        """批量取消员工权限"""
        count = queryset.update(is_staff=False, is_superuser=False)
        self.message_user(request, f'已取消 {count} 个用户的员工权限。')
    remove_staff.short_description = '取消员工权限'
    
    def make_superuser(self, request, queryset):
        """批量设置为超级管理员"""
        count = queryset.update(is_superuser=True, is_staff=True)
        self.message_user(request, f'已将 {count} 个用户设置为超级管理员。')
    make_superuser.short_description = '设置为超级管理员'
    
    def remove_superuser(self, request, queryset):
        """批量取消超级管理员"""
        count = queryset.update(is_superuser=False)
        self.message_user(request, f'已取消 {count} 个用户的超级管理员权限。')
    remove_superuser.short_description = '取消超级管理员'


@admin.register(RegistrationRequest)
class RegistrationRequestAdmin(admin.ModelAdmin):
    """注册申请管理"""
    list_display = ('username', 'phone', 'get_client_type_display', 'status_badge', 'submitted_time', 'processed_time', 'processed_by')
    list_filter = ('client_type', 'status', 'submitted_time', 'processed_time')
    search_fields = ('username', 'phone', 'feedback')
    ordering = ('-submitted_time',)
    list_per_page = 50
    date_hierarchy = 'submitted_time'
    readonly_fields = ('submitted_time', 'processed_time', 'processed_by', 'encoded_password')
    raw_id_fields = ('processed_by',)
    
    fieldsets = (
        ('申请信息', {
            'fields': ('username', 'phone', 'client_type', 'encoded_password')
        }),
        ('审核信息', {
            'fields': ('status', 'processed_by', 'processed_time', 'feedback')
        }),
        ('时间信息', {
            'fields': ('submitted_time',)
        }),
    )
    
    def status_badge(self, obj):
        """状态标签"""
        colors = {
            'pending': 'orange',
            'approved': 'green',
            'rejected': 'red',
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="background: {}; color: white; padding: 4px 10px; border-radius: 4px; font-size: 12px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = '状态'
    
    actions = ['approve_requests', 'reject_requests']
    
    def approve_requests(self, request, queryset):
        """批量批准申请"""
        count = 0
        for req in queryset.filter(status=RegistrationRequest.STATUS_PENDING):
            req.status = RegistrationRequest.STATUS_APPROVED
            req.processed_by = request.user
            req.processed_time = timezone.now()
            req.save()
            finalize_approval(req, processed_by=request.user)
            count += 1
        self.message_user(request, f'已批准 {count} 个注册申请。')
    approve_requests.short_description = '批准选中的申请'
    
    def reject_requests(self, request, queryset):
        """批量拒绝申请"""
        count = queryset.filter(status=RegistrationRequest.STATUS_PENDING).update(
            status=RegistrationRequest.STATUS_REJECTED,
            processed_by=request.user,
            processed_time=timezone.now()
        )
        self.message_user(request, f'已拒绝 {count} 个注册申请。')
    reject_requests.short_description = '拒绝选中的申请'

    def save_model(self, request, obj, form, change):
        previous_status = None
        if change and obj.pk:
            try:
                previous_status = RegistrationRequest.objects.only('status').get(pk=obj.pk).status
            except RegistrationRequest.DoesNotExist:
                previous_status = None

        super().save_model(request, obj, form, change)

        if obj.status == RegistrationRequest.STATUS_APPROVED:
            if previous_status != RegistrationRequest.STATUS_APPROVED or obj.processed_time is None:
                finalize_approval(obj, processed_by=request.user)


@admin.register(DataDictionary)
class DataDictionaryAdmin(admin.ModelAdmin):
    """数据字典管理"""
    list_display = ('name', 'code', 'value', 'get_dict_type_display', 'parent', 'order', 'is_active', 'created_time')
    list_filter = ('dict_type', 'is_active', 'parent', 'created_time')
    search_fields = ('name', 'code', 'value', 'description')
    ordering = ('dict_type', 'order', 'id')
    list_per_page = 50
    raw_id_fields = ('parent',)
    readonly_fields = ('created_time',)
    fieldsets = (
        ('基本信息', {
            'fields': ('name', 'code', 'value', 'dict_type', 'description')
        }),
        ('层级信息', {
            'fields': ('parent', 'order')
        }),
        ('状态信息', {
            'fields': ('is_active', 'created_time')
        }),
    )
    
    actions = ['activate_items', 'deactivate_items']
    
    def activate_items(self, request, queryset):
        """批量激活字典项"""
        count = queryset.update(is_active=True)
        self.message_user(request, f'已激活 {count} 个字典项。')
    activate_items.short_description = '激活选中的字典项'
    
    def deactivate_items(self, request, queryset):
        """批量停用字典项"""
        count = queryset.update(is_active=False)
        self.message_user(request, f'已停用 {count} 个字典项。')
    deactivate_items.short_description = '停用选中的字典项'


@admin.register(SystemConfig)
class SystemConfigAdmin(admin.ModelAdmin):
    """系统配置管理"""
    list_display = ('key', 'value_preview', 'description', 'is_encrypted', 'updated_time', 'created_time')
    list_filter = ('is_encrypted', 'created_time', 'updated_time')
    search_fields = ('key', 'value', 'description')
    ordering = ('key',)
    list_per_page = 50
    readonly_fields = ('created_time', 'updated_time')
    fieldsets = (
        ('配置信息', {
            'fields': ('key', 'value', 'description', 'is_encrypted')
        }),
        ('时间信息', {
            'fields': ('created_time', 'updated_time')
        }),
    )
    
    def value_preview(self, obj):
        """显示配置值预览（隐藏长文本）"""
        value = obj.value
        if len(value) > 50:
            return format_html('<span title="{}">{}...</span>', value, value[:50])
        if obj.is_encrypted:
            return '***已加密***'
        return value
    value_preview.short_description = '配置值'
    
    def save_model(self, request, obj, form, change):
        """保存时记录操作人（可扩展）"""
        super().save_model(request, obj, form, change)
        if change:
            messages.success(request, f'系统配置 "{obj.key}" 已更新。')
