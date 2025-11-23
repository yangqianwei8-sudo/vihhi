from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from backend.core.api_views import api_root, api_docs
from backend.core.views import home, health_check, login_view, logout_view
from backend.apps.system_management import views_registration as registration_views

# 自定义 Django admin 站点配置
admin.site.site_header = '维海科技信息化管理平台'
admin.site.site_title = '维海科技管理后台'
admin.site.index_title = '系统管理后台'

urlpatterns = [
    path('', home, name='home'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('register/', registration_views.register, name='register'),
    path('register/submitted/', registration_views.registration_submitted, name='registration_submitted'),
    path('profile/complete/', registration_views.complete_profile, name='complete_profile'),
    path('health/', health_check, name='health-check'),
    path('admin/registrations/', registration_views.registration_list, name='admin_registration_list'),
    path('admin/registrations/<int:pk>/', registration_views.registration_detail, name='admin_registration_detail'),
    path('admin/', admin.site.urls),
    path('api/', api_root, name='api-root'),
    path('api/docs/', api_docs, name='api-docs'),
    
    # API 路由
    path('api/system/', include(('backend.apps.system_management.urls', 'system'), namespace='system')),
    path('api/project/', include(('backend.apps.project_center.urls', 'project'), namespace='project')),
    path('api/customer/', include(('backend.apps.customer_success.urls', 'customer'), namespace='customer')),
    
    # 页面路由
    path('project/', include(('backend.apps.project_center.urls', 'project'), namespace='project_pages')),
    path('resource/', include(('backend.apps.resource_standard.urls', 'resource_standard'), namespace='resource_standard_pages')),
    path('production/', include(('backend.apps.production_quality.urls', 'production_quality'), namespace='production_quality_pages')),
    path('delivery/', include(('backend.apps.delivery_customer.urls', 'delivery'), namespace='delivery_pages')),
    path('business/', include(('backend.apps.customer_success.urls_pages', 'business'), namespace='business_pages')),
    path('collaboration/', include(('backend.apps.task_collaboration.urls', 'task_collaboration'), namespace='collaboration_pages')),
    path('system-center/', include(('backend.apps.system_management.urls_pages', 'system_pages'), namespace='system_pages')),
    path('settlement/', include(('backend.apps.settlement_center.urls_pages', 'settlement_pages'), namespace='settlement_pages')),
    # 行政管理、财务管理模块已移除
    path('administrative/', include(('backend.apps.administrative_management.urls', 'admin_pages'), namespace='admin_pages')),
    # path('financial/', include(('backend.apps.financial_management.urls', 'finance_pages'), namespace='finance_pages')),
    path('personnel/', include(('backend.apps.personnel_management.urls', 'personnel_pages'), namespace='personnel_pages')),
]

# 静态文件服务配置
# 在 DEBUG 模式下，Django 开发服务器会自动提供静态文件
# 在生产模式下，使用 Whitenoise 中间件提供静态文件
# 注意：无论 DEBUG 状态如何，都添加静态文件路由以确保文件可访问
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
if settings.DEBUG:
    # 开发环境：Django 开发服务器提供静态文件
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
