from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DeliveryRecordViewSet, DeliveryFileViewSet

router = DefaultRouter()
router.register(r'delivery', DeliveryRecordViewSet, basename='delivery')
router.register(r'files', DeliveryFileViewSet, basename='delivery-file')

urlpatterns = [
    path('', include(router.urls)),
]
