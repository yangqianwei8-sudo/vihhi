"""
档案管理模块API路由配置
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'categories', views.ArchiveCategoryViewSet, basename='archive-category')
router.register(r'project-archives', views.ProjectArchiveViewSet, basename='project-archive')
router.register(r'project-documents', views.ProjectArchiveDocumentViewSet, basename='project-document')
router.register(r'push-records', views.ArchivePushRecordViewSet, basename='archive-push-record')
router.register(r'administrative-archives', views.AdministrativeArchiveViewSet, basename='administrative-archive')
router.register(r'borrows', views.ArchiveBorrowViewSet, basename='archive-borrow')
router.register(r'destroys', views.ArchiveDestroyViewSet, basename='archive-destroy')
router.register(r'storage-rooms', views.ArchiveStorageRoomViewSet, basename='archive-storage-room')
router.register(r'locations', views.ArchiveLocationViewSet, basename='archive-location')
router.register(r'shelves', views.ArchiveShelfViewSet, basename='archive-shelf')
router.register(r'inventories', views.ArchiveInventoryViewSet, basename='archive-inventory')

urlpatterns = [
    path('', include(router.urls)),
]

