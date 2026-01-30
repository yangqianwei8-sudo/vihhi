from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'output_value'

router = DefaultRouter()
# 产值管理API路由将在需要时添加

urlpatterns = [
    path('', include(router.urls)),
]
