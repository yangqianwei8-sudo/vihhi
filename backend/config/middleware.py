"""
自动登录中间件 - 绕过登录页面，直接进入dashboard
动态主机名验证中间件 - 支持 *.sealosbja.site 通配符
"""
from django.contrib.auth import get_user_model, login
from django.utils.deprecation import MiddlewareMixin


class AutoLoginMiddleware(MiddlewareMixin):
    """
    自动登录中间件
    如果用户访问admin页面但未登录，自动登录第一个superuser
    """
    
    def process_request(self, request):
        # 只处理admin相关的请求
        if request.path.startswith('/admin/'):
            # 如果用户未登录
            if not request.user.is_authenticated:
                User = get_user_model()
                try:
                    # 尝试获取第一个superuser
                    auto_user = User.objects.filter(is_superuser=True, is_active=True).first()
                    if auto_user:
                        login(request, auto_user)
                    else:
                        # 如果没有superuser，尝试获取第一个staff用户
                        auto_user = User.objects.filter(is_staff=True, is_active=True).first()
                        if auto_user:
                            login(request, auto_user)
                except Exception:
                    # 如果自动登录失败，继续正常流程
                    pass
        
        return None


class AllowedHostsMiddleware(MiddlewareMixin):
    """
    动态主机名验证中间件
    支持 *.sealosbja.site 通配符模式
    允许所有以 .sealosbja.site 结尾的子域名
    
    这个中间件必须在 CommonMiddleware 之前运行
    """
    
    def process_request(self, request):
        try:
            # 从 HTTP_HOST 头获取主机名（不触发 Django 的验证）
            host_header = request.META.get('HTTP_HOST', '')
            if not host_header:
                return None
            
            host = host_header.split(':')[0]  # 移除端口号
            
            # 检查是否以 .sealosbja.site 结尾（支持通配符）
            if host.endswith('.sealosbja.site'):
                from django.conf import settings
                
                # 动态添加到 ALLOWED_HOSTS（如果还没有的话）
                if host not in settings.ALLOWED_HOSTS:
                    settings.ALLOWED_HOSTS.append(host)
                
                # 同时添加到 CSRF_TRUSTED_ORIGINS（支持 HTTP 和 HTTPS）
                scheme = 'https' if request.is_secure() else 'http'
                http_origin = f'http://{host}'
                https_origin = f'https://{host}'
                
                if http_origin not in settings.CSRF_TRUSTED_ORIGINS:
                    settings.CSRF_TRUSTED_ORIGINS.append(http_origin)
                if https_origin not in settings.CSRF_TRUSTED_ORIGINS:
                    settings.CSRF_TRUSTED_ORIGINS.append(https_origin)
                
                return None
        except Exception:
            # 如果获取主机名失败，让 Django 的默认验证处理
            pass
        
        return None
