"""
档案管理模块URL路由配置（页面路由）
"""
from django.urls import path
from . import views_pages

app_name = 'archive_management'

urlpatterns = [
    # 档案管理首页
    path('', views_pages.archive_list, name='archive_list'),
    
    # 项目档案
    path('project/', views_pages.project_archive_list, name='project_archive_list'),
    path('project/create/', views_pages.project_archive_create, name='project_archive_create'),
    path('project/<int:pk>/', views_pages.project_archive_detail, name='project_archive_detail'),
    path('project/<int:pk>/edit/', views_pages.project_archive_edit, name='project_archive_edit'),
    
    # 项目档案文档
    path('project/document/', views_pages.project_document_list, name='project_document_list'),
    path('project/document/upload/', views_pages.project_document_upload, name='project_document_upload'),
    path('project/document/<int:pk>/', views_pages.project_document_detail, name='project_document_detail'),
    
    # 图纸归档（待实现）
    path('project/drawing/', views_pages.project_drawing_archive_list, name='project_drawing_archive_list'),
    path('project/drawing/create/', views_pages.project_drawing_archive_create, name='project_drawing_archive_create'),
    path('project/drawing/<int:pk>/', views_pages.project_drawing_archive_detail, name='project_drawing_archive_detail'),
    
    # 交付归档（手动归档，待实现）
    path('project/delivery/', views_pages.project_delivery_archive_list, name='project_delivery_archive_list'),
    path('project/delivery/create/', views_pages.project_delivery_archive_create, name='project_delivery_archive_create'),
    path('project/delivery/<int:pk>/', views_pages.project_delivery_archive_detail, name='project_delivery_archive_detail'),
    
    # 行政档案
    path('administrative/', views_pages.administrative_archive_list, name='administrative_archive_list'),
    path('administrative/create/', views_pages.administrative_archive_create, name='administrative_archive_create'),
    path('administrative/<int:pk>/', views_pages.administrative_archive_detail, name='administrative_archive_detail'),
    
    # 档案分类
    path('category/', views_pages.archive_category_list, name='archive_category_list'),
    path('category/create/', views_pages.archive_category_create, name='archive_category_create'),
    path('category/<int:pk>/edit/', views_pages.archive_category_edit, name='archive_category_edit'),
    path('category/rule/', views_pages.archive_category_rule, name='archive_category_rule'),
    path('category/rule/create/', views_pages.archive_category_rule_create, name='archive_category_rule_create'),
    path('category/rule/<int:pk>/edit/', views_pages.archive_category_rule_edit, name='archive_category_rule_edit'),
    path('category/rule/<int:pk>/test/', views_pages.archive_category_rule_test, name='archive_category_rule_test'),
    
    # 档案借阅
    path('borrow/', views_pages.archive_borrow_list, name='archive_borrow_list'),
    path('borrow/create/', views_pages.archive_borrow_create, name='archive_borrow_create'),
    path('borrow/<int:pk>/', views_pages.archive_borrow_detail, name='archive_borrow_detail'),
    # 档案归还（待实现）
    path('borrow/return/', views_pages.archive_borrow_return_list, name='archive_borrow_return_list'),
    path('borrow/<int:pk>/return/', views_pages.archive_borrow_return, name='archive_borrow_return'),
    
    # 档案销毁
    path('destroy/', views_pages.archive_destroy_list, name='archive_destroy_list'),
    path('destroy/create/', views_pages.archive_destroy_create, name='archive_destroy_create'),
    path('destroy/<int:pk>/', views_pages.archive_destroy_detail, name='archive_destroy_detail'),
    
    # 档案库管理
    path('storage/', views_pages.archive_storage_list, name='archive_storage_list'),
    path('storage/room/', views_pages.archive_storage_room_list, name='archive_storage_room_list'),
    path('storage/room/create/', views_pages.archive_storage_room_create, name='archive_storage_room_create'),
    path('storage/location/', views_pages.archive_location_list, name='archive_location_list'),
    path('storage/location/create/', views_pages.archive_location_create, name='archive_location_create'),
    path('storage/shelf/', views_pages.archive_shelf_list, name='archive_shelf_list'),
    path('storage/inventory/', views_pages.archive_inventory_list, name='archive_inventory_list'),
    path('storage/inventory/create/', views_pages.archive_inventory_create, name='archive_inventory_create'),
    
    # 档案查询
    path('search/', views_pages.archive_search, name='archive_search'),
    # 档案检索（增强功能，待实现）
    path('search/fulltext/', views_pages.archive_search_fulltext, name='archive_search_fulltext'),
    path('search/advanced/', views_pages.archive_search_advanced, name='archive_search_advanced'),
    path('search/history/', views_pages.archive_search_history, name='archive_search_history'),
    
    # 档案安全（待实现）
    path('security/permission/', views_pages.archive_security_permission, name='archive_security_permission'),
    path('security/access/', views_pages.archive_security_access, name='archive_security_access'),
    path('security/log/', views_pages.archive_security_log, name='archive_security_log'),
    path('security/audit/', views_pages.archive_security_audit, name='archive_security_audit'),
    
    # 档案数字化（待实现）
    path('digitization/apply/', views_pages.archive_digitization_apply_list, name='archive_digitization_apply_list'),
    path('digitization/apply/create/', views_pages.archive_digitization_apply_create, name='archive_digitization_apply_create'),
    path('digitization/process/', views_pages.archive_digitization_process_list, name='archive_digitization_process_list'),
    path('digitization/result/', views_pages.archive_digitization_result_list, name='archive_digitization_result_list'),
    
    # 档案统计
    path('statistics/', views_pages.archive_statistics, name='archive_statistics'),
    # 档案统计（完善功能，待实现）
    path('statistics/usage/', views_pages.archive_statistics_usage, name='archive_statistics_usage'),
    path('statistics/storage/', views_pages.archive_statistics_storage, name='archive_statistics_storage'),
]

