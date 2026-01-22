"""
Admin配置模块
使用Django默认的admin登录
方案一：完全恢复为 Django 原生，只保留必要的权限检查
"""

import types
from django.contrib import admin
from django.http import HttpResponseForbidden

# 修改Django auth应用的显示名称
from django.apps import apps
try:
    auth_app = apps.get_app_config('auth')
    auth_app.verbose_name = '团队管理'
except Exception:
    pass

# ========== 限制管理后台访问：只允许admin用户 ==========
def admin_only(user):
    """检查用户是否是admin用户"""
    if not user or not user.is_authenticated:
        return False
    return user.username == 'admin' or user.is_superuser

# 重写admin.site的has_permission和has_module_permission方法，确保只有admin用户可以访问
try:
    _original_has_permission = admin.site.has_permission
    _original_has_module_permission = admin.site.has_module_permission
except AttributeError:
    def _original_has_permission(request, obj=None):
        return request.user.is_authenticated and request.user.is_staff
    def _original_has_module_permission(request, app_label):
        return request.user.is_authenticated and request.user.is_staff

def custom_has_permission(self, request, obj=None):
    """自定义权限检查：只允许admin用户"""
    if not request.user or not request.user.is_authenticated:
        return False
    if not admin_only(request.user):
        return False
    try:
        return _original_has_permission(request, obj)
    except TypeError:
        return _original_has_permission(self, request, obj)

def custom_has_module_permission(self, request, app_label):
    """自定义模块权限检查：只允许admin用户"""
    if not request.user or not request.user.is_authenticated:
        return False
    if not admin_only(request.user):
        return False
    try:
        return _original_has_module_permission(request, app_label)
    except TypeError:
        return _original_has_module_permission(self, request, app_label)

# 绑定方法到admin.site实例
try:
    admin.site.has_permission = types.MethodType(custom_has_permission, admin.site)
    admin.site.has_module_permission = types.MethodType(custom_has_module_permission, admin.site)
except AttributeError:
    pass
# ========== 限制管理后台访问结束 ==========

# ========== 自定义应用列表顺序：将系统管理提到最前面 ==========
_original_get_app_list = admin.site.get_app_list

def custom_get_app_list(self, request, app_label=None):
    """
    自定义get_app_list，将系统管理应用移到最前面
    """
    app_list = _original_get_app_list(request, app_label)
    
    # 将 system_management 应用移到最前面
    system_management_app = None
    other_apps = []
    
    for app in app_list:
        if app.get('app_label') == 'system_management':
            system_management_app = app
        else:
            other_apps.append(app)
    
    # 如果找到了系统管理应用，将其放在最前面
    if system_management_app:
        return [system_management_app] + other_apps
    
    return app_list

# 绑定方法到admin.site实例
admin.site.get_app_list = types.MethodType(custom_get_app_list, admin.site)
# ========== 自定义应用列表顺序结束 ==========

# 为了兼容性，创建一个admin_site别名指向admin.site
admin_site = admin.site
