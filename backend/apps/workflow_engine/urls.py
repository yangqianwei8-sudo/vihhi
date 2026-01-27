from django.urls import path
from django.views.generic import RedirectView
from . import views_pages

app_name = 'workflow_engine'

urlpatterns = [
    # 首页 - 根路径重定向到 /home/
    path('', RedirectView.as_view(url='home/', permanent=False), name='workflow_home'),
    path('home/', views_pages.workflow_home, name='workflow_home_alt'),
    
    # 流程模板管理
    path('workflows/', views_pages.workflow_list, name='workflow_list'),
    path('workflows/create/', views_pages.workflow_create, name='workflow_create'),
    path('workflows/<int:workflow_id>/', views_pages.workflow_detail, name='workflow_detail'),
    path('workflows/<int:workflow_id>/edit/', views_pages.workflow_edit, name='workflow_edit'),
    
    # 节点管理
    path('workflows/<int:workflow_id>/nodes/create/', views_pages.node_create, name='node_create'),
    path('nodes/<int:node_id>/edit/', views_pages.node_edit, name='node_edit'),
    path('nodes/<int:node_id>/delete/', views_pages.node_delete, name='node_delete'),
    
    # 审批操作
    path('approvals/', views_pages.approval_list, name='approval_list'),
    path('approvals/<int:instance_id>/', views_pages.approval_detail, name='approval_detail'),
    path('approvals/<int:instance_id>/action/', views_pages.approval_action, name='approval_action'),
    path('approvals/<int:instance_id>/withdraw/', views_pages.approval_withdraw, name='approval_withdraw'),
    
    # 我的申请
    path('my-applications/', views_pages.my_application_list, name='my_application_list'),
]

