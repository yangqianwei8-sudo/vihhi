# 产值管理 API 路由（V1 与冻结文档一致）
from django.urls import path
from . import views_api_v1

app_name = 'output_api'

urlpatterns = [
    # 文档 八.1：查询当前动态产值
    path('v1/opportunity/<int:id>/', views_api_v1.opportunity_dynamic_output_v1, name='v1_opportunity_dynamic_output'),
]
