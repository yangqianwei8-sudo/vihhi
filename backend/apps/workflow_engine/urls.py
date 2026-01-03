from django.urls import path
from . import views_pages

app_name = 'workflow_engine'

urlpatterns = [
    # 首页
    path('', views_pages.workflow_engine_home, name='workflow_engine_home'),
    path('home/', views_pages.workflow_engine_home, name='workflow_engine_home'),
    
    # 流程模板管理
    path('workflows/', views_pages.workflow_list, name='workflow_list'),
    path('workflows/create/', views_pages.workflow_create, name='workflow_create'),
    path('workflows/<int:workflow_id>/', views_pages.workflow_detail, name='workflow_detail'),
    path('workflows/<int:workflow_id>/edit/', views_pages.workflow_edit, name='workflow_edit'),
    path('workflows/<int:workflow_id>/create-test-instance/', views_pages.create_test_approval_instance, name='create_test_approval_instance'),
    
    # 测试审批实例创建
    path('create-test-instance/', views_pages.create_test_instance_select, name='create_test_instance_select'),
    
    # 节点管理
    path('workflows/<int:workflow_id>/nodes/create/', views_pages.node_create, name='node_create'),
    path('nodes/<int:node_id>/edit/', views_pages.node_edit, name='node_edit'),
    path('nodes/<int:node_id>/delete/', views_pages.node_delete, name='node_delete'),
    
    # 审批操作
    path('my-applications/', views_pages.my_applications, name='my_applications'),
    path('approvals/', views_pages.approval_list, name='approval_list'),
    path('approvals/<int:instance_id>/', views_pages.approval_detail, name='approval_detail'),
    path('approvals/<int:instance_id>/action/', views_pages.approval_action, name='approval_action'),
    
    # 审批统计
    path('statistics/', views_pages.approval_statistics, name='approval_statistics'),
    
    # 全部流程（系统管理员）
    path('all-workflows/', views_pages.all_workflows, name='all_workflows'),
    
    # 批量操作
    path('approvals/batch/', views_pages.batch_approve, name='batch_approve'),
    path('approvals/export/', views_pages.export_approvals, name='export_approvals'),
]

