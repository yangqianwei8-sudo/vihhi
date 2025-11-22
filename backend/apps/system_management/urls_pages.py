from django.urls import path

from . import views_pages

app_name = "system_pages"

urlpatterns = [
    path("account/settings/", views_pages.account_settings, name="account_settings"),
    path("settings/", views_pages.system_settings, name="system_settings"),
    path("logs/", views_pages.operation_logs, name="operation_logs"),
    path("dictionary/", views_pages.data_dictionary, name="data_dictionary"),
    path("permissions/matrix/", views_pages.permission_matrix, name="permission_matrix"),
]

