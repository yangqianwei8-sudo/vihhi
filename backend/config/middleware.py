"""
自动登录中间件 - 绕过登录页面，直接进入dashboard
Host 守卫中间件 - 严格限制访问来源
公司隔离安全门槛中间件 - 拒绝company为空的用户访问业务模块
"""
from django.contrib.auth import get_user_model, login
from django.http import HttpResponseForbidden, HttpResponse
from django.utils.deprecation import MiddlewareMixin
from django.shortcuts import render
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


class CompanyIsolationGuardMiddleware(MiddlewareMixin):
    """
    P0-2补充: 公司隔离安全门槛中间件
    
    任何用户 company 为空，直接拒绝访问所有业务模块
    返回提示：请在后台为该用户配置所属公司
    """
    
    # 允许访问的路径（不需要company检查）
    ALLOWED_PATHS = [
        '/admin/',  # Django Admin
        '/accounts/',  # 登录/登出/验证码等（若使用 accounts 前缀）
        '/login/',  # 登录页
        '/logout/',  # 登出
        '/register/',  # 注册
        '/health/',  # 健康检查
        '/dashboard/',  # 首页（但会在视图中检查）
        '/api/service/control/',  # 服务控制
        '/static/',  # 静态资源
        '/media/',  # 媒体文件
        '/favicon.ico',  # 图标
        '/__health',  # 健康检查
        '/healthz',  # 健康检查
        '/ready',  # 健康检查
        '/readiness',  # 健康检查
    ]
    
    # 业务模块路径前缀（需要company检查）
    BUSINESS_MODULE_PATHS = [
        '/production/',
        '/contracts/',
        '/plan/',
        '/workflow/',
        '/customers/',
        '/opportunities/',
        '/settlement/',
        '/payment/',
        '/administrative/',
        '/financial/',
        '/personnel/',
        '/archive/',
        '/litigation/',
        '/documents/',
        '/delivery/',
        '/collaboration/',
        '/system-center/',
        '/resource/',
        '/output-value/',
        '/api/production/',
        '/api/contract/',
        '/api/plan/',
        '/api/workflow/',
        '/api/customer/',
        '/api/opportunity/',
        '/api/settlement/',
        '/api/payment/',
        '/api/administrative/',
        '/api/financial/',
        '/api/personnel/',
        '/api/archive/',
        '/api/litigation/',
        '/api/document/',
        '/api/delivery/',
        '/api/collaboration/',
        '/api/resource/',
        '/api/output-value/',
    ]
    
    def process_request(self, request):
        # 未登录用户不检查
        if not request.user.is_authenticated:
            return None
        
        # 超管不检查
        if request.user.is_superuser:
            return None
        
        # 检查路径是否在允许列表中
        path = request.path
        if any(path.startswith(allowed) for allowed in self.ALLOWED_PATHS):
            return None
        
        # 检查是否是业务模块路径
        is_business_module = any(path.startswith(business_path) for business_path in self.BUSINESS_MODULE_PATHS)
        
        if is_business_module:
            # 检查用户 company 是否为空
            if not request.user.company_id:
                import logging
                logger = logging.getLogger('backend.config.middleware')
                logger.warning(
                    f"CompanyIsolationGuardMiddleware: 拒绝访问 - "
                    f"用户 {request.user.username} (ID: {request.user.id}) company_id 为空, "
                    f"Path: {path}"
                )
                
                # 返回友好的错误页面
                from django.shortcuts import render
                return render(
                    request,
                    'shared/company_not_configured.html',
                    {
                        'user': request.user,
                        'requested_path': path,
                    },
                    status=403
                )
        
        return None
