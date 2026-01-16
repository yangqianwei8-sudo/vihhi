from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from django.contrib import messages
from django.db.models import Count

from backend.apps.system_management.models import (
    User, Department, Role, RegistrationRequest,
    DataDictionary, SystemConfig, OurCompany
)
from backend.core.admin_base import BaseModelAdmin, AuditAdminMixin, StatusBadgeMixin
from .services_registration import finalize_approval


@admin.register(Role)
class RoleAdmin(BaseModelAdmin):
    """角色管理"""
    list_display = ('name', 'code', 'user_count', 'permission_count', 'is_active', 'created_time')
    list_filter = ('is_active', 'created_time')
    search_fields = ('name', 'code', 'description')
    ordering = ('-created_time',)
    filter_horizontal = ('custom_permissions', 'permissions')
    readonly_fields = ('created_time',)
    
    class Media:
        css = {
            'all': ('admin/css/permission_filter.css',)
        }
        js = ('admin/js/permission_filter.js',)
    
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
            'description': '业务系统的自定义权限（如 customer_management.client.view_all 等）。<br>'
                          '<strong>客户管理权限推荐配置：</strong><br>'
                          '• 商务经理：<code>customer_management.client.view_assigned</code>（查看本人负责）<br>'
                          '• 部门经理：<code>customer_management.client.view_department</code>（查看本部门）<br>'
                          '• 总经理：<code>customer_management.client.view_all</code>（查看全部）<br><br>'
                          '<strong>提示：</strong>在权限选择器的搜索框中输入 <code>customer_management.client</code> 可以快速筛选客户管理权限'
        }),
        # 时间信息会自动添加，无需手动定义
    )
    
    def formfield_for_manytomany(self, db_field, request, **kwargs):
        """自定义多对多字段的显示"""
        if db_field.name == 'custom_permissions':
            from backend.apps.permission_management.models import PermissionItem
            # 只显示激活的权限，并按模块和代码排序
            kwargs['queryset'] = PermissionItem.objects.filter(
                is_active=True
            ).order_by('module', 'code')
            # 添加搜索提示
            kwargs['help_text'] = (
                '提示：在搜索框中输入权限代码或名称可以快速查找。'
                '例如：输入 "customer_management.client" 可以筛选所有客户管理权限；'
                '输入 "view_assigned" 可以查找"查看本人负责"权限。'
            )
        return super().formfield_for_manytomany(db_field, request, **kwargs)
    
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
    
    # 批量操作已由 BaseModelAdmin 提供（activate_items/deactivate_items）
    # 如果需要自定义名称，可以重写：
    def get_actions(self, request):
        """自定义批量操作名称"""
        actions = super().get_actions(request)
        # 重命名批量操作（元组不可变，需要创建新元组）
        if 'activate_items' in actions:
            old_action = actions['activate_items']
            actions['activate_items'] = (
                old_action[0],  # 函数对象
                old_action[1],  # 函数名
                '激活选中的角色'  # 新的显示名称
            )
        if 'deactivate_items' in actions:
            old_action = actions['deactivate_items']
            actions['deactivate_items'] = (
                old_action[0],  # 函数对象
                old_action[1],  # 函数名
                '停用选中的角色'  # 新的显示名称
            )
        return actions


@admin.register(Department)
class DepartmentAdmin(BaseModelAdmin):
    """部门管理"""
    list_display = ('name', 'code', 'parent', 'leader', 'member_count', 'order', 'is_active', 'created_time')
    list_filter = ('is_active', 'parent', 'created_time')
    search_fields = ('name', 'code', 'description')
    ordering = ('order', 'name')
    raw_id_fields = ('parent', 'leader')
    readonly_fields = ('created_time',)
    fieldsets = (
        ('基本信息', {
            'fields': ('name', 'code', 'parent', 'leader', 'description')
        }),
        ('组织信息', {
            'fields': ('order', 'is_active')
        }),
        # 时间信息会自动添加
    )
    
    def member_count(self, obj):
        """显示部门成员数量"""
        count = obj.members.filter(is_active=True).count()
        if count > 0:
            url = reverse('admin:system_management_user_changelist') + f'?department__id__exact={obj.id}'
            return format_html('<a href="{}">{} 人</a>', url, count)
        return '0 人'
    member_count.short_description = '成员数量'
    
    # 批量操作已由 BaseModelAdmin 提供


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
    list_filter = ('user_type', 'department', 'is_active', 'is_staff', 'is_superuser', 'date_joined', 'profile_completed')
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
            'fields': ('department', 'position', 'is_staff', 'is_superuser'),
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
                role_links.append(format_html('...等{}个', roles.count()))
            from django.utils.safestring import mark_safe
            return mark_safe(', '.join(str(link) for link in role_links))
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
    
    def get_queryset(self, request):
        """重写查询集，避免查询不存在的关联表"""
        qs = super().get_queryset(request)
        # 只选择必要的关联，避免查询可能不存在的表
        return qs.select_related('department').prefetch_related('roles')
    
    def changelist_view(self, request, extra_context=None):
        """重写列表视图，捕获数据库错误"""
        from django.db import ProgrammingError
        from django.contrib import messages
        
        try:
            return super().changelist_view(request, extra_context)
        except ProgrammingError as e:
            # 检查是否是表或字段不存在的错误
            error_msg = str(e)
            if 'does not exist' in error_msg:
                if 'settlement_management_payment_record' in error_msg or 'settlement_payment_record' in error_msg:
                    messages.error(
                        request,
                        '数据库表 settlement_payment_record 不存在。'
                        '请运行迁移命令创建表：python manage.py migrate settlement_center'
                    )
                elif 'system_role.description' in error_msg:
                    messages.warning(
                        request,
                        '数据库表 system_role 缺少 description 字段。'
                        '请运行迁移命令：python manage.py migrate system_management'
                    )
                else:
                    messages.error(
                        request,
                        f'数据库错误：{error_msg[:200]}'
                    )
                # 返回一个空的响应，避免显示错误页面
                from django.http import HttpResponseRedirect
                from django.urls import reverse
                return HttpResponseRedirect(reverse('admin:index'))
            # 其他数据库错误，继续抛出
            raise
    
    def has_delete_permission(self, request, obj=None):
        """检查用户是否有删除权限"""
        # 超级用户可以删除任何用户
        if request.user.is_superuser:
            return True
        # 员工用户（is_staff=True）也可以删除用户
        if request.user.is_staff:
            return True
        # 其他情况需要检查是否有delete_user权限
        return request.user.has_perm('system_management.delete_user')


@admin.register(RegistrationRequest)
class RegistrationRequestAdmin(StatusBadgeMixin, BaseModelAdmin):
    """注册申请管理"""
    list_display = ('username', 'phone', 'get_client_type_display', 'status_badge', 'submitted_time', 'processed_time', 'processed_by')
    list_filter = ('client_type', 'status', 'submitted_time', 'processed_time')
    search_fields = ('username', 'phone', 'feedback')
    ordering = ('-submitted_time',)
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
        color_map = {
            'pending': '#ffc107',  # orange -> yellow
            'approved': '#28a745',  # green
            'rejected': '#dc3545',  # red
        }
        return self.format_status_badge(
            obj.status,
            obj.get_status_display(),
            color_map=color_map
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
class DataDictionaryAdmin(BaseModelAdmin):
    """数据字典管理"""
    list_display = ('name', 'code', 'value', 'get_dict_type_display', 'parent', 'order', 'is_active', 'created_time')
    list_filter = ('dict_type', 'is_active', 'parent', 'created_time')
    search_fields = ('name', 'code', 'value', 'description')
    ordering = ('dict_type', 'order', 'id')
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
            'fields': ('is_active',)
        }),
        # 时间信息会自动添加
    )
    
    # 批量操作已由 BaseModelAdmin 提供


@admin.register(SystemConfig)
class SystemConfigAdmin(AuditAdminMixin, BaseModelAdmin):
    """系统配置管理"""
    list_display = ('key', 'value_preview', 'description', 'is_encrypted', 'updated_time', 'created_time')
    list_filter = ('is_encrypted', 'created_time', 'updated_time')
    search_fields = ('key', 'value', 'description')
    ordering = ('key',)
    readonly_fields = ('created_time', 'updated_time')
    fieldsets = (
        ('配置信息', {
            'fields': ('key', 'value', 'description', 'is_encrypted')
        }),
        # 时间信息会自动添加
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
    
    # AuditAdminMixin 会自动显示成功消息，但这里需要自定义消息
    def save_model(self, request, obj, form, change):
        """保存时记录操作"""
        super().save_model(request, obj, form, change)
        if change:
            messages.success(request, f'系统配置 "{obj.key}" 已更新。')


@admin.register(OurCompany)
class OurCompanyAdmin(AuditAdminMixin, BaseModelAdmin):
    """我方主体信息管理"""
    list_display = ('company_name', 'credit_code', 'legal_representative', 'order', 'is_active', 'updated_time')
    list_filter = ('is_active', 'created_time', 'updated_time')
    search_fields = ('company_name', 'credit_code', 'legal_representative', 'registered_address')
    ordering = ('order', 'id')
    readonly_fields = ('created_time', 'updated_time')
    fieldsets = (
        ('基本信息', {
            'fields': ('company_name', 'credit_code', 'legal_representative', 'registered_address')
        }),
        ('设置', {
            'fields': ('order', 'is_active')
        }),
        # 时间信息会自动添加
    )
    
    # AuditAdminMixin 会自动显示成功消息，但这里需要自定义消息
    def save_model(self, request, obj, form, change):
        """保存时记录操作"""
        super().save_model(request, obj, form, change)
        if change:
            messages.success(request, f'我方主体信息 "{obj.company_name}" 已更新。')
        else:
            messages.success(request, f'我方主体信息 "{obj.company_name}" 已创建。')
