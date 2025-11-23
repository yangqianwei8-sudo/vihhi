from django.urls import path

from . import views_pages

app_name = "delivery"

urlpatterns = [
    # 交付管理首页
    path("", views_pages.report_delivery, name="report_delivery"),
    path("report/", views_pages.report_delivery, name="report_delivery"),
    
    # 交付记录管理页面
    path("list/", views_pages.delivery_list, name="delivery_list"),
    path("create/", views_pages.delivery_create, name="delivery_create"),
    path("<int:delivery_id>/", views_pages.delivery_detail, name="delivery_detail"),
    path("statistics/", views_pages.delivery_statistics, name="delivery_statistics"),
    path("warnings/", views_pages.delivery_warnings, name="delivery_warnings"),
    
    # 其他功能（保留原有路由）
    path("collaboration/", views_pages.customer_collaboration, name="customer_collaboration"),
    path("portal/", views_pages.customer_portal, name="customer_portal"),
    path("signature/", views_pages.electronic_signature, name="electronic_signature"),
]

