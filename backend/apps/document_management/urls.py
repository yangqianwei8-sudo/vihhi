from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'document'

router = DefaultRouter()
# 文档管理API路由将在迁移后添加

urlpatterns = [
    path('', include(router.urls)),
]
