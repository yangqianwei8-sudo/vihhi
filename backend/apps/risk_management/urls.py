"""
风险管理模块URL路由配置
"""
from django.urls import path
from . import views_pages

app_name = "risk_management"

urlpatterns = [
    # 首页
    path("", views_pages.risk_management_home, name="risk_management_home"),
    path("home/", views_pages.risk_management_home, name="risk_management_home"),
]

