from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'system'

router = DefaultRouter()
router.register('users', views.UserViewSet, basename='user')
router.register('departments', views.DepartmentViewSet, basename='department')
router.register('roles', views.RoleViewSet, basename='role')
router.register('dictionaries', views.DataDictionaryViewSet, basename='dictionary')
router.register('configs', views.SystemConfigViewSet, basename='config')

urlpatterns = [
    path('', include(router.urls)),
]
