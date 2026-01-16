"""
Admin配置模块
使用Django默认的admin登录
"""

import sys
import types
from django.contrib import admin
from django.contrib.admin.views.decorators import staff_member_required
from django.template.response import TemplateResponse
from django.utils.translation import gettext_lazy as _
from django.contrib.admin.models import LogEntry
from django.http import HttpResponseForbidden
from django.urls import path
from .admin_menu_config import build_menu_structure, MENU_URL_MAPPING
import re

# 修改Django auth应用的显示名称
from django.apps import apps
try:
    auth_app = apps.get_app_config('auth')
    auth_app.verbose_name = '团队管理'
except Exception:
    pass

# 注意：使用Django默认的admin登录功能

def _extract_app_label_from_path(path):
    """
    从URL路径中提取app_label
    
    Args:
        path: URL路径，例如 '/admin/production_management/' 或 '/admin/production_management/project/'
    
    Returns:
        app_label字符串，如果无法提取则返回None
    """
    match = re.match(r'^/admin/([^/]+)(?:/|$)', path)
    return match.group(1) if match else None

# 保存原始的index方法
# 注意：_original_index本身有@staff_member_required装饰器
# 权限检查统一由 @staff_member_required 装饰器处理，不再重复检查
_original_index = admin.site.index

def custom_index(self, request, extra_context=None):
    """
    自定义index方法，完全移除recent_actions上下文
    这样"最近动作"模块就不会被生成和显示
    并添加菜单结构数据
    如果当前URL是应用级别的页面（如/admin/production_management/），则只显示该应用的菜单项
    """
    # 重要：登录/登出页面不经过此函数，应该被 Django admin 的登录视图处理
    # 但如果被误调用，直接返回原始行为，避免权限检查干扰
    current_path = request.path
    if '/admin/login' in current_path or '/admin/logout' in current_path:
        return _original_index(self, request, extra_context)
    
    # ========== 限制管理后台访问：只允许admin用户 ==========
    # 检查用户是否是admin用户（除了登录/登出页面）
    if not (request.user.is_authenticated and (request.user.username == 'admin' or request.user.is_superuser)):
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden('您没有权限访问管理后台。只有系统管理员可以访问。')
    # ========== 限制管理后台访问结束 ==========
    
    # 权限检查：依赖 @staff_member_required 装饰器（已在 _original_index 上）
    # 移除重复的登录检查，统一使用 Django 标准的权限检查机制
    # 注意：_original_index 本身有 @staff_member_required 装饰器，会检查登录和staff权限
    
    # 检测当前URL路径，判断是否是应用级别的页面
    filter_app_label = _extract_app_label_from_path(request.path)
    
    try:
        extra_context = extra_context or {}
        extra_context['recent_actions'] = []
        
        # 注意：不再清空 app_list，因为 Django 默认的 index.html 需要它来显示应用列表
        # 如果之前是为了清除卡片内容，应该通过修改模板来实现，而不是清空数据
        
        # 调用原始方法（_original_index本身有@staff_member_required装饰器，会检查权限）
        # 权限检查由 @staff_member_required 装饰器统一处理
        response = _original_index(request, extra_context)
        
        # 生成动态菜单结构
        if hasattr(response, 'context_data') and response.context_data:
            # 保留 app_list，让 Django 默认模板正常显示
            # 生成菜单结构
            try:
                app_list = admin.site.get_app_list(request)
                if app_list:
                    menu_structure = build_menu_structure(app_list, filter_app_label=filter_app_label)
                    response.context_data['admin_menu_structure'] = menu_structure
                else:
                    response.context_data['admin_menu_structure'] = None
            except Exception:
                response.context_data['admin_menu_structure'] = None
        
        # 确保 recent_actions 为空
        if hasattr(response, 'context_data') and response.context_data:
            response.context_data['recent_actions'] = []
        
        # 成功时直接返回，避免重复处理
        return response
        
    except Exception as e:
        # 如果自定义index失败，回退到原始方法
        extra_context = extra_context or {}
        extra_context['recent_actions'] = []
        # 保留 app_list，让 Django 默认模板正常显示
        try:
            response = _original_index(request, extra_context)
            # 生成动态菜单结构
            if hasattr(response, 'context_data') and response.context_data:
                # 保留 app_list，让 Django 默认模板正常显示
                try:
                    app_list = admin.site.get_app_list(request)
                    if app_list:
                        # 重新检测 filter_app_label
                        filter_app_label = _extract_app_label_from_path(request.path)
                        menu_structure = build_menu_structure(app_list, filter_app_label=filter_app_label)
                        response.context_data['admin_menu_structure'] = menu_structure
                    else:
                        response.context_data['admin_menu_structure'] = None
                except Exception:
                    response.context_data['admin_menu_structure'] = None
            
            # 确保 recent_actions 为空
            if hasattr(response, 'context_data') and response.context_data:
                response.context_data['recent_actions'] = []
            
            return response
        except Exception as e2:
            from django.http import HttpResponseServerError
            return HttpResponseServerError(f'Admin页面加载失败: {str(e2)}')

# 保存原始的each_context方法
_original_each_context = admin.site.each_context

def custom_each_context(self, request):
    """
    自定义each_context方法，确保在所有上下文中都不包含recent_actions
    并移除subtitle，避免显示"A管理员在线"等信息
    同时添加菜单结构数据，使所有admin页面都能访问
    如果当前URL是应用级别的页面（如/admin/production_management/），则只显示该应用的菜单项
    """
    context = _original_each_context(request)
    # 移除recent_actions，确保它不会被传递到模板
    context['recent_actions'] = []
    # 移除subtitle，避免显示用户在线信息
    if 'subtitle' in context:
        del context['subtitle']
    
    # 检测当前URL路径，判断是否是应用级别的页面
    filter_app_label = _extract_app_label_from_path(request.path)
    
    # 保留 app_list，让 Django 默认模板正常显示
    # 注意：不再清空 app_list，因为 Django 默认的 index.html 需要它
    
    # 生成动态菜单结构
    try:
        app_list = admin.site.get_app_list(request)
        if app_list:
            menu_structure = build_menu_structure(app_list, filter_app_label=filter_app_label)
            context['admin_menu_structure'] = menu_structure
        else:
            context['admin_menu_structure'] = None
    except Exception:
        context['admin_menu_structure'] = None
    
    # 添加菜单URL映射到上下文，供前端使用
    context['admin_menu_url_mapping'] = MENU_URL_MAPPING
    
    # 添加排序后的主菜单项列表，供前端使用，并为每个菜单项添加URL
    from .admin_menu_config import MAIN_MENU_ITEMS, get_menu_url
    main_menu_items_with_url = []
    for item in MAIN_MENU_ITEMS:
        menu_item = item.copy()
        menu_path = menu_item.get('path', '')
        menu_item['url'] = get_menu_url(menu_path) if menu_path else '#'
        main_menu_items_with_url.append(menu_item)
    context['admin_main_menu_items'] = main_menu_items_with_url
    
    return context

# 重写get_app_list方法，确保不包含recent_actions，并移除"增加"和"修改"链接
_original_get_app_list = admin.site.get_app_list

def custom_get_app_list(self, request, app_label=None):
    """
    自定义get_app_list，确保不返回recent_actions相关数据
    并处理模型URL链接
    """
    if app_label is not None:
        app_list = _original_get_app_list(request, app_label)
    else:
        app_list = _original_get_app_list(request)
    
    # 遍历所有应用来处理URL
    for app in app_list:
        if 'models' in app:
            for model in app['models']:
                admin_url = model.get('admin_url', '')
                needs_changelist_url = False
                
                if not admin_url:
                    needs_changelist_url = True
                elif admin_url and ('/add/' in admin_url or '/change/' in admin_url or '/view/' in admin_url):
                    needs_changelist_url = True
                
                if needs_changelist_url:
                    try:
                        from django.urls import reverse
                        app_label_name = app.get('app_label', '')
                        model_name = model.get('object_name', '').lower()
                        if app_label_name and model_name:
                            try:
                                changelist_url = reverse(f'admin:{app_label_name}_{model_name}_changelist')
                                model['admin_url'] = changelist_url
                            except Exception:
                                model['admin_url'] = f'/admin/{app_label_name}/{model_name}/'
                    except Exception:
                        app_label_name = app.get('app_label', '')
                        model_name = model.get('object_name', '').lower()
                        if app_label_name and model_name:
                            model['admin_url'] = f'/admin/{app_label_name}/{model_name}/'
                
                model_name = model.get('name', '')
                if model_name and ('查看' in model_name or 'view' in model_name.lower()):
                    model['_should_remove'] = True
    
    # 移除标记为需要删除的模型
    for app in app_list:
        if 'models' in app:
            app['models'] = [m for m in app['models'] if not m.get('_should_remove', False)]
    
    return app_list

# 注意：白名单机制已取消，所有模型都可以正常编辑

admin.site.index = types.MethodType(custom_index, admin.site)
admin.site.each_context = types.MethodType(custom_each_context, admin.site)
admin.site.get_app_list = types.MethodType(custom_get_app_list, admin.site)

# ========== 统一使用Django标准的权限检查机制 ==========
# 所有admin视图统一使用 @staff_member_required 装饰器进行权限检查
# 不再有特殊例外，学校管理页面也需要登录和staff权限
# ========== 统一权限检查结束 ==========

# ========== 限制管理后台访问：只允许admin用户 ==========
from django.http import HttpResponseForbidden

def admin_only(user):
    """检查用户是否是admin用户"""
    if not user or not user.is_authenticated:
        return False
    return user.username == 'admin' or user.is_superuser

# 重写admin.site的has_permission和has_module_permission方法，确保只有admin用户可以访问
# 使用延迟访问，避免在Django完全初始化前访问admin.site的方法
try:
    # 保存原始方法（如果可用）
    _original_has_permission = admin.site.has_permission
    _original_has_module_permission = admin.site.has_module_permission
except AttributeError:
    # 如果方法不存在，使用默认实现
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
    # 调用原始方法
    try:
        return _original_has_permission(request, obj)
    except TypeError:
        # 如果原始方法是实例方法，需要传入self
        return _original_has_permission(self, request, obj)

def custom_has_module_permission(self, request, app_label):
    """自定义模块权限检查：只允许admin用户"""
    if not request.user or not request.user.is_authenticated:
        return False
    if not admin_only(request.user):
        return False
    # 调用原始方法
    try:
        return _original_has_module_permission(request, app_label)
    except TypeError:
        # 如果原始方法是实例方法，需要传入self
        return _original_has_module_permission(self, request, app_label)

# 使用MethodType绑定方法到admin.site实例
try:
    admin.site.has_permission = types.MethodType(custom_has_permission, admin.site)
    admin.site.has_module_permission = types.MethodType(custom_has_module_permission, admin.site)
except AttributeError:
    # 如果方法不存在，跳过（可能Django版本不支持）
    pass

# 注意：admin用户检查已经在custom_index函数内部完成（第58-62行）
# custom_index已经在第234行被赋值给admin.site.index，无需再次赋值
# ========== 限制管理后台访问结束 ==========

# 为了兼容性，创建一个admin_site别名指向admin.site
admin_site = admin.site

# ==================== 自定义客户管理app_index视图 ====================
from django.contrib.admin.views.decorators import staff_member_required
from django.template.response import TemplateResponse
from django.urls import reverse

_original_app_index = admin.site.app_index

def custom_app_index(self, request, app_label, extra_context=None):
    """
    自定义app_index方法，为所有应用显示自定义首页
    """
    # ========== 限制管理后台访问：只允许admin用户 ==========
    # 检查用户是否是admin用户
    if not (request.user.is_authenticated and (request.user.username == 'admin' or request.user.is_superuser)):
        return HttpResponseForbidden('您没有权限访问管理后台。只有系统管理员可以访问。')
    # ========== 限制管理后台访问结束 ==========
    
    # 定义需要自定义首页的应用列表
    apps_with_custom_index = [
        'customer_management',
        'production_management',
        'settlement_center',
        'delivery_customer',
        'archive_management',
        'financial_management',
        'administrative_management',
        'plan_management',
        'litigation_management',
        # 'system_management',  # 已移除：应用索引页面为空，直接重定向到用户列表页
        # 'permission_management',  # 已移除：应用索引页面为空，直接使用默认行为或重定向
        'workflow_engine',
    ]
    
    # permission_management 应用索引页面重定向到模型列表页
    if app_label == 'permission_management':
        from django.shortcuts import redirect
        return redirect('admin:permission_management_permissionitem_changelist')
    
    # system_management 应用索引页面重定向到用户列表页
    if app_label == 'system_management':
        from django.shortcuts import redirect
        return redirect('admin:system_management_user_changelist')
    
    # 如果是需要自定义首页的应用，显示自定义首页
    if app_label in apps_with_custom_index:
        extra_context = extra_context or {}
        
        # 获取应用列表（用于生成菜单）
        try:
            app_list = admin.site.get_app_list(request)
            if app_list:
                menu_structure = build_menu_structure(app_list, filter_app_label=app_label)
                extra_context['admin_menu_structure'] = menu_structure
            else:
                extra_context['admin_menu_structure'] = None
        except Exception:
            extra_context['admin_menu_structure'] = None
        
        # 获取该应用的模型列表
        try:
            app_dict = admin.site._build_app_dict(request, app_label)
            # _build_app_dict 返回的是 {app_label: {...}} 格式
            if app_label in app_dict:
                app_info = app_dict[app_label]
                if 'models' in app_info:
                    from django.apps import apps
                    for model_info in app_info['models']:
                        try:
                            model = apps.get_model(app_label, model_info['object_name'])
                            model_info['count'] = model.objects.count()
                        except Exception:
                            model_info['count'] = 0
                
                extra_context.update({
                    'app_label': app_label,
                    'app_dict': app_info,  # 使用 app_info 而不是整个 app_dict
                    'title': f'{app_info.get("name", app_label)}管理',
                })
            else:
                # 如果没有找到应用信息，使用默认值
                extra_context.update({
                    'app_label': app_label,
                    'app_dict': {'models': []},
                    'title': f'{app_label}管理',
                })
        except Exception:
            extra_context.update({
                'app_label': app_label,
                'app_dict': {'models': []},
                'title': f'{app_label}管理',
            })
        
        
        # 添加客户管理的左侧导航菜单（仅customer_management）
        if app_label == 'customer_management' and request.user.is_authenticated:
            try:
                from backend.apps.system_management.services import get_user_permission_codes
                from backend.apps.customer_management.views_pages import _build_customer_management_menu
                permission_set = get_user_permission_codes(request.user)
                customer_menu = _build_customer_management_menu(permission_set, active_id=None)
                extra_context['customer_menu'] = customer_menu
            except Exception:
                extra_context['customer_menu'] = []
        
        # 添加each_context中的内容
        context = admin.site.each_context(request)
        extra_context.update(context)
        
        # 根据app_label选择对应的模板
        template_path = f'admin/{app_label}/app_index.html'
        
        try:
            return TemplateResponse(
                request,
                template_path,
                extra_context
            )
        except Exception:
            return _original_app_index(request, app_label, extra_context)
    
    # 其他应用使用默认的app_index
    return _original_app_index(request, app_label, extra_context)

# 替换app_index方法
admin.site.app_index = types.MethodType(custom_app_index, admin.site)
