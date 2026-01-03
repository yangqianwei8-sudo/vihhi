"""
合同管理模块URL路由配置
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# 创建路由器
router = DefaultRouter()
router.register(r'contracts', views.ContractViewSet, basename='contract')

app_name = 'contract_management'

urlpatterns = [
    # API路由
    path('api/', include(router.urls)),
]

