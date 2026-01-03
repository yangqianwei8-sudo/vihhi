"""
API管理模块URL路由配置
"""
from django.urls import path
from . import views_pages

app_name = "api_management"

urlpatterns = [
    # 首页
    path("", views_pages.api_management_home, name="api_management_home"),
    path("home/", views_pages.api_management_home, name="api_management_home"),
]

