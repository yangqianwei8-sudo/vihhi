from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'customer'

router = DefaultRouter()
router.register('clients', views.ClientViewSet, basename='client')
router.register('client-contacts', views.ClientContactViewSet, basename='client-contact')
router.register('client-projects', views.ClientProjectViewSet, basename='client-project')

urlpatterns = [
    path('', include(router.urls)),
]
