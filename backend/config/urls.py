from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from backend.core.api_views import api_root, api_docs
from backend.core.views import home, health_check, login_view, logout_view

urlpatterns = [
    path('', home, name='home'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('health/', health_check, name='health-check'),
    path('admin/', admin.site.urls),
    path('api/', api_root, name='api-root'),
    path('api/docs/', api_docs, name='api-docs'),
    
    # API 路由
    path('api/system/', include(('backend.apps.system_management.urls', 'system'), namespace='system')),
    path('api/project/', include(('backend.apps.project_center.urls', 'project'), namespace='project')),
    path('api/customer/', include(('backend.apps.customer_success.urls', 'customer'), namespace='customer')),
    
    # 页面路由
    path('project/', include(('backend.apps.project_center.urls', 'project'), namespace='project_pages')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
