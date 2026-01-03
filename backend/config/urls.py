from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
from django.conf import settings
from django.conf.urls.static import static
from backend.core.api_views import api_root, api_docs
from backend.core.views import home, health_check, login_view, logout_view, favicon_view, test_admin_page, django_service_control
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
def business_contract_redirect(request):
    """商务合同重定向视图（已从后台管理移除）"""
    from django.contrib import messages
    from django.shortcuts import redirect
    messages.info(request, '商务合同管理已从后台管理中移除，请使用前端管理页面。')
    # 重定向到生产管理首页
    return redirect('/admin/production_management/')

# 使用Django原生admin（admin已在文件开头导入）
admin_site = admin.site

urlpatterns = [
    path('', home, name='home'),  # 系统总工作台首页
    path('favicon.ico', favicon_view, name='favicon'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('register/', registration_views.register, name='register'),
    path('register/submitted/', registration_views.registration_submitted, name='registration_submitted'),
    path('profile/complete/', registration_views.complete_profile, name='complete_profile'),
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
    # 商务合同重定向（已从后台管理移除）
    path('admin/production_management/businesscontract/', business_contract_redirect, name='admin_business_contract_redirect'),
    path('admin/production_management/businesscontract/<path:path>', business_contract_redirect, name='admin_business_contract_redirect_detail'),
    # 商务回款计划重定向（已从后台管理移除）
    path('admin/production_management/businesspaymentplan/', business_contract_redirect, name='admin_business_payment_plan_redirect'),
    path('admin/production_management/businesspaymentplan/<path:path>', business_contract_redirect, name='admin_business_payment_plan_redirect_detail'),
    path('admin/', admin_site.urls),
    path('api/', api_root, name='api-root'),
    path('api/docs/', api_docs, name='api-docs'),
    # 仪表盘API
    path('api/admin/dashboard/stats/', dashboard_stats, name='dashboard_stats'),
    path('api/admin/dashboard/todos/', dashboard_todos, name='dashboard_todos'),
    
    # API 路由
    path('api/system/', include(('backend.apps.system_management.urls', 'system'), namespace='system')),
    path('api/production/', include(('backend.apps.production_management.urls', 'production'), namespace='production')),  # 生产管理API
    # path('api/project/', include(('backend.apps.project_center.urls', 'project'), namespace='project')),  # 已删除：迁移到production_management
    path('api/customer/', include(('backend.apps.customer_management.urls', 'customer'), namespace='customer')),  # 客户管理API
    path('api/settlement/', include(('backend.apps.settlement_center.urls', 'settlement'), namespace='settlement')),  # 结算中心API
    path('api/archive/', include(('backend.apps.archive_management.urls_api', 'archive'), namespace='archive_api')),
    path('api/workflow/', include(('backend.apps.workflow_engine.urls_api', 'workflow_engine'), namespace='workflow_engine_api')),  # 工作流引擎API（包含Agent对话）
    
    # 页面路由
    path('production/', include(('backend.apps.production_management.urls', 'production'), namespace='production_pages')),  # 生产管理页面
    # path('project/', include(('backend.apps.project_center.urls', 'project'), namespace='project_pages')),  # 已删除：迁移到production_management
    path('resource/', include(('backend.apps.resource_standard.urls', 'resource_standard'), namespace='resource_standard_pages')),
    path('business/', include(('backend.apps.customer_management.urls_pages', 'business'), namespace='business_pages')),  # 客户管理页面
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
    # API管理模块
    path('api-management/', include(('backend.apps.api_management.urls', 'api_management'), namespace='api_management')),
    # 风险管理模块
    path('risk/', include(('backend.apps.risk_management.urls', 'risk_management'), namespace='risk_management')),
    # 收发管理模块（收文管理、发文管理）
    path('delivery/', include(('backend.apps.delivery_customer.urls', 'delivery_pages'), namespace='delivery_pages')),
]

# 静态文件服务配置
# 在 DEBUG 模式下，Django 开发服务器会自动提供静态文件
# 在生产模式下，使用 Whitenoise 中间件提供静态文件
# 注意：无论 DEBUG 状态如何，都添加静态文件路由以确保文件可访问
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# 前端构建文件的静态资源路径（/js/, /css/, /img/等）
# 无论 DEBUG 状态如何，都需要提供前端静态文件
from django.views.static import serve
import os
frontend_dist = os.path.join(settings.BASE_DIR.parent, 'frontend', 'dist')
if os.path.exists(frontend_dist):
    urlpatterns += [
        path('js/<path:path>', serve, {'document_root': os.path.join(frontend_dist, 'js')}),
        path('css/<path:path>', serve, {'document_root': os.path.join(frontend_dist, 'css')}),
        path('img/<path:path>', serve, {'document_root': os.path.join(frontend_dist, 'img')}),
        # 注意：favicon.ico 已经在上面通过 favicon_view 处理，这里不再重复定义
    ]

if settings.DEBUG:
    # 开发环境：Django 开发服务器提供静态文件
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
