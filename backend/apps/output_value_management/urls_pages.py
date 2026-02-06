from django.urls import path
from . import views_pages

app_name = "output_value_pages"

urlpatterns = [
    # 产值管理首页（V1 收敛）
    path("home/", views_pages.output_value_management_home, name="output_value_management_home"),
    # 以下旧入口已收敛至 V1 API，统一重定向到首页
    path("template/", views_pages.output_value_410_gone, name="output_value_template_manage"),
    path("records/", views_pages.output_value_410_gone, name="output_value_record_list"),
    path("records/export/", views_pages.output_value_410_gone, name="output_value_record_export"),
    path("records/batch-confirm/", views_pages.output_value_410_gone, name="output_value_record_batch_confirm"),
    path("records/<int:record_id>/confirm/", views_pages.output_value_410_gone, name="output_value_record_confirm"),
    path("project/<int:project_id>/", views_pages.output_value_410_gone, name="project_output_value_detail"),
    path("statistics/", views_pages.output_value_410_gone, name="output_value_statistics"),
]
