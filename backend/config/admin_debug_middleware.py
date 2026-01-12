"""
Admin调试中间件 - 用于追踪admin URL模式的生成
"""
from django.urls import clear_url_caches


class AdminDebugMiddleware:
    """追踪admin URL模式的中间件"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # 在每次请求时清除 URL 缓存，确保使用最新的 URL 模式
        # 这样可以确保新注册的应用（如 workflow_engine）能够被正确识别
        if request.path.startswith('/admin/'):
            clear_url_caches()
        
        response = self.get_response(request)
        return response

