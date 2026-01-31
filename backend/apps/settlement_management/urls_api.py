"""
结算管理模块的 API 路由（由原 settlement_center 迁入，统一使用 settlement_management 的 models/serializers/services）
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views_api

app_name = 'settlement'

router = DefaultRouter()
router.register('service-fee-schemes', views_api.ServiceFeeSettlementSchemeViewSet, basename='service-fee-scheme')
router.register('service-fee-segmented-rates', views_api.ServiceFeeSegmentedRateViewSet, basename='service-fee-segmented-rate')
router.register('service-fee-jump-point-rates', views_api.ServiceFeeJumpPointRateViewSet, basename='service-fee-jump-point-rate')
router.register('service-fee-unit-cap-details', views_api.ServiceFeeUnitCapDetailViewSet, basename='service-fee-unit-cap-detail')

urlpatterns = [
    path('api/', include(router.urls)),
]
