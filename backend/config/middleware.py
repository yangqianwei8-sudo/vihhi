"""
自动登录中间件 - 绕过登录页面，直接进入dashboard
Host 守卫中间件 - 严格限制访问来源
"""
from django.contrib.auth import get_user_model, login
from django.http import HttpResponseForbidden
from django.utils.deprecation import MiddlewareMixin
import os


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


class HostGuardMiddleware(MiddlewareMixin):
    """
    Host 守卫中间件
    严格验证请求的 Host 头，只允许指定的公网域名访问
    防止通过 Service IP、Pod IP、内部域名等方式绕过访问控制
    """
    
    # 健康检查路径（允许任何 Host，用于 K8s 健康检查）
    HEALTH_CHECK_PATHS = ['/__health', '/health', '/healthz', '/ready', '/readiness']
    
    def process_request(self, request):
        # 健康检查路径允许任何 Host（K8s 健康检查可能使用内部 IP）
        if any(request.path.startswith(path) for path in self.HEALTH_CHECK_PATHS):
            return None
        
        # 从 Django settings 获取允许的 Host 列表（与 ALLOWED_HOSTS 保持一致）
        from django.conf import settings
        allowed_hosts = getattr(settings, 'ALLOWED_HOSTS', [])
        
        # 获取请求的 Host（不包含端口）
        request_host = request.get_host().split(':')[0]
        
        # 严格匹配：Host 必须完全等于允许的域名之一
        if request_host not in allowed_hosts:
            # 记录拒绝的请求（用于安全审计）
            import logging
            logger = logging.getLogger('backend.config.middleware')
            logger.warning(
                f"HostGuardMiddleware: 拒绝访问 - Host: {request_host}, "
                f"Path: {request.path}, "
                f"RemoteAddr: {request.META.get('REMOTE_ADDR', 'unknown')}"
            )
            return HttpResponseForbidden(
                "Forbidden: 访问被拒绝。只允许通过指定的公网域名访问。"
            )
        
        return None
