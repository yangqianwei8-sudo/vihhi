from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
from django.views.generic import RedirectView
from django.conf import settings
from django.conf.urls.static import static
from backend.core.api_views import api_root, api_docs, notification_list, mark_notification_read
from backend.core.views import home, dashboard, health_check, login_view, logout_view, favicon_view, test_admin_page, django_service_control
from backend.apps.system_management import views_registration as registration_views

from backend.core.dashboard_views import dashboard_stats, dashboard_todos


from django.contrib.auth.decorators import login_required

@login_required
def payment_management_redirect(request):
    """回款管理重定向视图"""
    # 直接调用回款计划列表视图，而不是重定向
    from backend.apps.settlement_center.views_pages import payment_plan_list
    return payment_plan_list(request)

@login_required
def report_management_redirect(request):
    """报表管理重定向视图"""
    # 重定向到财务报表管理页面
    return redirect('finance_pages:report_management')

@login_required
def risk_management_redirect(request):
    """风险管理重定向视图"""
    # 风险管理模块尚未实现，暂时重定向到admin首页
    # TODO: 当风险管理功能实现后，修改此重定向
    return redirect('admin:index')

# 导入自定义admin配置（这会禁用"最近动作"模块）
from backend.config import admin as custom_admin  # noqa: F401

# 使用默认的admin.site（已被custom_admin修改）
admin_site = admin.site

# 使用自定义AdminSite（已禁用最近动作模块）
# 自定义 Django admin 站点配置
admin_site.site_header = '维海科技信息化管理平台'
admin_site.site_title = '维海科技信息化管理后台'
admin_site.index_title = '系统管理后台'
# 配置站点URL，用于"查看站点"功能（指向dashboard）
admin_site.site_url = '/dashboard/'

urlpatterns = [
    path('', RedirectView.as_view(url='/dashboard/', permanent=False), name='home'),
    path('dashboard/', dashboard, name='dashboard'),
    path('favicon.ico', favicon_view, name='favicon'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('register/', registration_views.register, name='register'),
    path('register/submitted/', registration_views.registration_submitted, name='registration_submitted'),
    # path('profile/complete/', registration_views.complete_profile, name='complete_profile'),  # 已注释：禁用资料完善页面
    path('health/', health_check, name='health-check'),
    path('api/service/control/', django_service_control, name='django_service_control'),
    path('test-admin/', test_admin_page, name='test-admin'),
    # admin路由必须在admin_site.urls之前，但要确保更具体的路由在更通用的路由之前
    # 注意：admin_site.urls包含了/admin/login/等路由，所以必须放在最后
    # 使用Django默认的admin登录
    path('admin/registrations/', registration_views.registration_list, name='admin_registration_list'),
    path('admin/registrations/<int:pk>/', registration_views.registration_detail, name='admin_registration_detail'),
    # 回款管理重定向（从admin路径重定向到settlement路径）
    path('admin/payment_management/', payment_management_redirect, name='admin_payment_management'),
    # 报表管理重定向（从admin路径重定向到financial路径）
    path('admin/report_management/', report_management_redirect, name='admin_report_management'),
    # 风险管理重定向（风险管理模块尚未实现，暂时重定向到admin首页）
    path('admin/risk_management/', risk_management_redirect, name='admin_risk_management'),
    path('admin/', admin_site.urls),
    path('api/', api_root, name='api-root'),
    path('api/docs/', api_docs, name='api-docs'),
    # 通知API
    path('api/notifications/', notification_list, name='notification_list'),
    path('api/notifications/mark-read/', mark_notification_read, name='mark_notification_read'),
    # 仪表盘API
    path('api/admin/dashboard/stats/', dashboard_stats, name='dashboard_stats'),
    path('api/admin/dashboard/todos/', dashboard_todos, name='dashboard_todos'),
    
    # API 路由
    path('api/system/', include(('backend.apps.system_management.urls', 'system'), namespace='system')),
    path('api/production/', include(('backend.apps.production_management.urls', 'production'), namespace='production')),  # 生产管理API
    # path('api/project/', include(('backend.apps.project_center.urls', 'project'), namespace='project')),  # 已删除：迁移到production_management
    path('api/customer/', include(('backend.apps.customer_management.urls', 'customer'), namespace='customer')),  # 客户管理API
    path('api/delivery/', include(('backend.apps.delivery_customer.urls_api', 'delivery'), namespace='delivery_api')),
    path('api/settlement/', include(('backend.apps.settlement_center.urls', 'settlement'), namespace='settlement')),  # 结算中心API
    path('api/archive/', include(('backend.apps.archive_management.urls_api', 'archive'), namespace='archive_api')),
    path('api/plan/', include(('backend.apps.plan_management.urls', 'plan'), namespace='plan')),  # 计划管理API
    
    # 页面路由
    path('production/', include(('backend.apps.production_management.urls', 'production'), namespace='production_pages')),  # 生产管理页面
    # path('project/', include(('backend.apps.project_center.urls', 'project'), namespace='project_pages')),  # 已删除：迁移到production_management
    path('resource/', include(('backend.apps.resource_standard.urls', 'resource_standard'), namespace='resource_standard_pages')),
    path('delivery/', include(('backend.apps.delivery_customer.urls', 'delivery'), namespace='delivery_pages')),
    # 客户管理、商机管理、合同管理分离为独立路径
    path('customers/', include(('backend.apps.customer_management.customer_urls', 'customer'), namespace='customer_pages')),  # 客户管理页面
    path('opportunities/', include(('backend.apps.customer_management.opportunity_urls', 'opportunity'), namespace='opportunity_pages')),  # 商机管理页面
    path('contracts/', include(('backend.apps.customer_management.contract_urls', 'contract'), namespace='contract_pages')),  # 合同管理页面
    # 保持向后兼容：business/路径重定向到customers/
    path('business/', include(('backend.apps.customer_management.customer_urls', 'business'), namespace='business_pages')),  # 向后兼容重定向
    path('collaboration/', include(('backend.apps.task_collaboration.urls', 'task_collaboration'), namespace='collaboration_pages')),
    path('system-center/', include(('backend.apps.system_management.urls_pages', 'system_pages'), namespace='system_pages')),
    path('settlement/', include(('backend.apps.settlement_center.urls_pages', 'settlement_pages'), namespace='settlement_pages')),  # 结算管理（使用settlement_center模块）
    # 行政管理、财务管理模块
    path('administrative/', include(('backend.apps.administrative_management.urls', 'admin_pages'), namespace='admin_pages')),
    path('financial/', include(('backend.apps.financial_management.urls', 'finance_pages'), namespace='finance_pages')),
    path('personnel/', include(('backend.apps.personnel_management.urls', 'personnel_pages'), namespace='personnel_pages')),
    path('workflow/', include(('backend.apps.workflow_engine.urls', 'workflow_engine'), namespace='workflow_engine')),
    # 档案管理模块
    path('archive/', include(('backend.apps.archive_management.urls', 'archive_management'), namespace='archive_management')),
    # 诉讼管理模块
    path('litigation/', include(('backend.apps.litigation_management.urls_pages', 'litigation_pages'), namespace='litigation_pages')),
    # 计划管理模块
    path('plan/', include(('backend.apps.plan_management.urls_pages', 'plan_pages'), namespace='plan_pages')),
]

# 静态文件服务配置
# 在 DEBUG 模式下，Django 开发服务器会自动提供静态文件
# 在生产模式下，使用 Whitenoise 中间件提供静态文件
# 注意：无论 DEBUG 状态如何，都添加静态文件路由以确保文件可访问
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
if settings.DEBUG:
    # 开发环境：Django 开发服务器提供静态文件
    # 优先使用 STATIC_ROOT，因为它包含了所有收集的静态文件（包括 Django admin）
    # 如果 STATIC_ROOT 不存在，则回退到 STATICFILES_DIRS
    import os
    if settings.STATIC_ROOT and os.path.exists(settings.STATIC_ROOT):
        urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    elif settings.STATICFILES_DIRS and len(settings.STATICFILES_DIRS) > 0:
        urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
    
    # P2: 已移除旧版 Vue SPA 静态资源服务
    # 不再提供 frontend/dist 下的 js/css/img 等静态资源
    # 旧版前端已彻底移除，所有请求应使用 Django 模板或返回 404
    # from django.views.static import serve
    # import os
    # frontend_dist = os.path.join(settings.BASE_DIR.parent, 'frontend', 'dist')
    # if os.path.exists(frontend_dist):
    #     urlpatterns += [
    #         path('js/<path:path>', serve, {'document_root': os.path.join(frontend_dist, 'js')}),
    #         path('css/<path:path>', serve, {'document_root': os.path.join(frontend_dist, 'css')}),
    #         path('img/<path:path>', serve, {'document_root': os.path.join(frontend_dist, 'img')}),
    #         path('favicon.ico', serve, {'document_root': frontend_dist, 'path': 'favicon.ico'}),
    #     ]
