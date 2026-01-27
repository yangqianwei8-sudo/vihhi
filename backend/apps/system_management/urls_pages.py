from django.urls import path

from . import views_pages

app_name = "system_pages"

urlpatterns = [
    path("home/", views_pages.system_management_home, name="system_management_home"),
    path("account/settings/", views_pages.account_settings, name="account_settings"),
    path("settings/", views_pages.system_settings, name="system_settings"),
    path("logs/", views_pages.operation_logs, name="operation_logs"),
    path("dictionary/", views_pages.data_dictionary, name="data_dictionary"),
    path("permissions/matrix/", views_pages.permission_matrix, name="permission_matrix"),
    # 示例表单
    path("example-form/", views_pages.example_form, name="example_form"),
    path("create-form-example/", views_pages.create_form_example, name="create_form_example"),
    path("detail-page-example/", views_pages.detail_page_example, name="detail_page_example"),
    path("list-page-example/", views_pages.list_page_example, name="list_page_example"),
    path("three-column-layout-example/", views_pages.three_column_layout_example, name="three_column_layout_example"),
    # 反馈功能
    path("feedback/submit/", views_pages.feedback_submit, name="feedback_submit"),
    path("feedback/", views_pages.feedback_list, name="feedback_list"),
    path("feedback/<int:feedback_id>/process/", views_pages.feedback_process, name="feedback_process"),
]

