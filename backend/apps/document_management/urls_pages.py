from django.urls import path
from . import views_pages

app_name = "document_pages"

urlpatterns = [
    # ==================== 收文管理路由 ====================
    # 收文管理首页
    path("incoming/home/", views_pages.incoming_document_home, name="incoming_document_home"),
    path("incoming/", views_pages.incoming_document_list, name="incoming_document_list"),
    path("incoming/create/", views_pages.incoming_document_create, name="incoming_document_create"),
    path("incoming/<int:document_id>/", views_pages.incoming_document_detail, name="incoming_document_detail"),
    path("incoming/<int:document_id>/edit/", views_pages.incoming_document_edit, name="incoming_document_edit"),
    
    # ==================== 发文管理路由 ====================
    # 发文管理首页
    path("outgoing/home/", views_pages.outgoing_document_home, name="outgoing_document_home"),
    path("outgoing/", views_pages.outgoing_document_list, name="outgoing_document_list"),
    path("outgoing/create/", views_pages.outgoing_document_create, name="outgoing_document_create"),
    path("outgoing/<int:document_id>/", views_pages.outgoing_document_detail, name="outgoing_document_detail"),
    path("outgoing/<int:document_id>/edit/", views_pages.outgoing_document_edit, name="outgoing_document_edit"),
    
    # ==================== 文件分类维护路由 ====================
    path("file-category/manage/", views_pages.file_category_manage, name="file_category_manage"),
    path("file-category/<str:stage_code>/", views_pages.file_category_list, name="file_category_list"),
    path("file-category/<str:stage_code>/create/", views_pages.file_category_create, name="file_category_create"),
    
    # ==================== 文件模板维护路由 ====================
    path("file-template/manage/", views_pages.file_template_manage, name="file_template_manage"),
]
