"""
结算中心模块的URL路由
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'settlement'

router = DefaultRouter()
router.register('service-fee-schemes', views.ServiceFeeSettlementSchemeViewSet, basename='service-fee-scheme')
router.register('service-fee-segmented-rates', views.ServiceFeeSegmentedRateViewSet, basename='service-fee-segmented-rate')
router.register('service-fee-jump-point-rates', views.ServiceFeeJumpPointRateViewSet, basename='service-fee-jump-point-rate')
router.register('service-fee-unit-cap-details', views.ServiceFeeUnitCapDetailViewSet, basename='service-fee-unit-cap-detail')

urlpatterns = [
    path('api/', include(router.urls)),
]

