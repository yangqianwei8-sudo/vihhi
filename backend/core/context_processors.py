"""
上下文处理器：自动为所有模板提供当前模块的左侧菜单
"""
from backend.apps.system_management.services import get_user_permission_codes


def sidebar_menu(request):
    """
    上下文处理器：根据当前URL路径自动获取对应的左侧菜单
    
    使用方式：
    1. 在 settings.py 的 TEMPLATES['OPTIONS']['context_processors'] 中添加：
       'backend.core.context_processors.sidebar_menu',
    2. 在模板中直接使用 {{ sidebar_menu }} 即可获取当前模块的左侧菜单
    """
    # 如果请求对象不存在或用户未登录，直接返回空菜单
    if not request:
        return {'sidebar_menu': []}
    
    try:
        # 检查用户是否已认证
        if not hasattr(request, 'user') or not request.user.is_authenticated:
            return {'sidebar_menu': []}
    except Exception:
        # 如果检查用户认证状态时出错，返回空菜单
        return {'sidebar_menu': []}
    
    try:
        # 如果导入的函数不存在，直接返回空菜单
        # 这样可以避免导入错误导致整个应用无法启动
        try:
            from backend.core.views import _get_current_module_from_path, _get_sidebar_menu_for_module
        except (ImportError, AttributeError):
            # 如果函数不存在，返回空菜单
            return {'sidebar_menu': []}
        
        # 检查函数是否存在
        if not hasattr(_get_current_module_from_path, '__call__') or not hasattr(_get_sidebar_menu_for_module, '__call__'):
            return {'sidebar_menu': []}
        
        # 获取当前路径
        request_path = getattr(request, 'path', '')
        
        # 判断当前模块
        try:
            current_module = _get_current_module_from_path(request_path)
        except Exception:
            # 如果获取模块失败，返回空菜单
            return {'sidebar_menu': []}
        
        # 如果无法判断模块，返回空菜单
        if not current_module:
            return {'sidebar_menu': []}
        
        # 获取用户权限（可能因为数据库连接失败而抛出异常）
        try:
            permission_set = get_user_permission_codes(request.user)
        except Exception:
            # 如果获取权限失败（可能是数据库连接问题），返回空菜单
            return {'sidebar_menu': []}
        
        # 获取当前模块的左侧菜单
        try:
            sidebar_menu_items = _get_sidebar_menu_for_module(
                current_module,
                permission_set,
                request_path,
                request.user
            )
        except Exception:
            # 如果获取菜单失败，返回空菜单
            return {'sidebar_menu': []}
        
        return {'sidebar_menu': sidebar_menu_items}
    
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        # 只记录警告，不抛出异常，避免导致 503 错误
        logger.warning(f'获取左侧菜单失败: {e}', exc_info=True)
        return {'sidebar_menu': []}


def notification_widget(request):
    """
    上下文处理器：为所有模板提供通知组件脚本引用
    
    使用方式：
    1. 在 settings.py 的 TEMPLATES['OPTIONS']['context_processors'] 中添加：
       'backend.core.context_processors.notification_widget',
    2. 在基础模板的 </body> 标签前添加：
       {% if notification_widget_enabled %}
       <script src="{% static 'js/notification_widget.js' %}"></script>
       {% endif %}
    """
    # 如果用户未登录，不启用通知组件
    if not request or not hasattr(request, 'user') or not request.user.is_authenticated:
        return {'notification_widget_enabled': False}
    
    return {'notification_widget_enabled': True}
