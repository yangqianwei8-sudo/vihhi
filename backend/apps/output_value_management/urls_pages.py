from django.urls import path
from . import views_pages

app_name = "output_value_pages"

urlpatterns = [
    # 产值管理首页
    path("home/", views_pages.output_value_management_home, name="output_value_management_home"),
    
    # 产值模板管理
    path("template/", views_pages.output_value_template_manage, name="output_value_template_manage"),
    
    # 产值记录管理
    path("records/", views_pages.output_value_record_list, name="output_value_record_list"),
    path("records/export/", views_pages.output_value_record_list, name="output_value_record_export"),  # 导出（暂用列表视图）
    path("records/batch-confirm/", views_pages.output_value_record_list, name="output_value_record_batch_confirm"),  # 批量确认（暂用列表视图）
    path("records/<int:record_id>/confirm/", views_pages.output_value_record_confirm, name="output_value_record_confirm"),
    path("project/<int:project_id>/", views_pages.project_output_value_detail, name="project_output_value_detail"),
    
    # 产值统计
    path("statistics/", views_pages.output_value_statistics, name="output_value_statistics"),
]
