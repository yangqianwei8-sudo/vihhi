"""
档案管理模块API视图
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.utils import timezone
from django.db.models import Q

from .services import (
    ArchivePushService,
    ProjectArchiveService,
    ArchiveBorrowService,
    ArchiveDestroyService,
)
from backend.apps.archive_management.models import (
    ArchiveCategory,
    ArchiveProjectArchive,
    ProjectArchiveDocument,
    ArchivePushRecord,
    AdministrativeArchive,
    ArchiveBorrow,
    ArchiveDestroy,
    ArchiveStorageRoom,
    ArchiveLocation,
    ArchiveShelf,
    ArchiveInventory,
)
from .serializers import (
    ArchiveCategorySerializer,
    ProjectArchiveSerializer,
    ProjectArchiveDocumentSerializer,
    ArchivePushRecordSerializer,
    AdministrativeArchiveSerializer,
    ArchiveBorrowSerializer,
    ArchiveDestroySerializer,
    ArchiveStorageRoomSerializer,
    ArchiveLocationSerializer,
    ArchiveShelfSerializer,
    ArchiveInventorySerializer,
)


class ArchiveCategoryViewSet(viewsets.ModelViewSet):
    """档案分类视图集"""
    queryset = ArchiveCategory.objects.all()
    serializer_class = ArchiveCategorySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['category_type', 'is_active', 'parent']
    search_fields = ['name', 'code']
    ordering_fields = ['order', 'created_time']
    ordering = ['category_type', 'order', 'id']


class ProjectArchiveViewSet(viewsets.ModelViewSet):
    """项目归档视图集"""
    queryset = ArchiveProjectArchive.objects.all()
    serializer_class = ProjectArchiveSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'project']
    search_fields = ['archive_number', 'project__project_name', 'project__project_number']
    ordering_fields = ['created_time', 'applied_time']
    ordering = ['-created_time']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.select_related('project', 'applicant', 'executor', 'confirmed_by')
        return queryset
    
    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        """确认归档完成"""
        archive = self.get_object()
        try:
            ProjectArchiveService.confirm_project_archive(archive, request.user)
            return Response({'status': 'archived', 'message': '归档已确认完成'})
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class ProjectArchiveDocumentViewSet(viewsets.ModelViewSet):
    """项目档案文档视图集"""
    queryset = ProjectArchiveDocument.objects.all()
    serializer_class = ProjectArchiveDocumentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['document_type', 'status', 'project', 'category']
    search_fields = ['document_number', 'document_name', 'project__project_name']
    ordering_fields = ['uploaded_time']
    ordering = ['-uploaded_time']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.select_related('project', 'category', 'uploaded_by', 'parent_version')
        return queryset
    
    def perform_create(self, serializer):
        serializer.save(uploaded_by=self.request.user)


class ArchivePushRecordViewSet(viewsets.ReadOnlyModelViewSet):
    """交付推送记录视图集（只读）"""
    queryset = ArchivePushRecord.objects.all()
    serializer_class = ArchivePushRecordSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['push_status', 'project']
    search_fields = ['delivery_record__delivery_number']
    ordering_fields = ['created_time', 'push_time']
    ordering = ['-created_time']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.select_related('delivery_record', 'project')
        return queryset
    
    @action(detail=True, methods=['post'])
    def retry(self, request, pk=None):
        """重试推送"""
        push_record = self.get_object()
        if push_record.push_status == 'success':
            return Response({'error': '推送已成功，无需重试'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            ArchivePushService.retry_push(push_record)
            return Response({'status': 'success', 'message': '推送成功'})
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AdministrativeArchiveViewSet(viewsets.ModelViewSet):
    """行政档案视图集"""
    queryset = AdministrativeArchive.objects.all()
    serializer_class = AdministrativeArchiveSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'category', 'storage_room', 'security_level']
    search_fields = ['archive_number', 'archive_name']
    ordering_fields = ['created_time', 'archive_date']
    ordering = ['-created_time']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.select_related('category', 'archive_department', 'archivist', 'storage_room', 'location')
        return queryset
    
    def perform_create(self, serializer):
        serializer.save(archivist=self.request.user)


class ArchiveBorrowViewSet(viewsets.ModelViewSet):
    """档案借阅视图集"""
    queryset = ArchiveBorrow.objects.all()
    serializer_class = ArchiveBorrowSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'borrow_method', 'borrower']
    search_fields = ['borrow_number', 'borrower__username']
    ordering_fields = ['created_time', 'borrow_date', 'return_date']
    ordering = ['-created_time']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.select_related(
            'project_document', 'administrative_archive',
            'borrower', 'borrower_department', 'approver', 'out_by', 'returned_by'
        )
        return queryset
    
    def perform_create(self, serializer):
        serializer.save(borrower=self.request.user)
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """审批借阅"""
        borrow = self.get_object()
        approval_opinion = request.data.get('approval_opinion', '')
        approved = request.data.get('approved', True)
        
        try:
            ArchiveBorrowService.approve_borrow(borrow, request.user, approved, approval_opinion)
            return Response({'status': borrow.status, 'message': '审批完成'})
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def checkout(self, request, pk=None):
        """出库"""
        borrow = self.get_object()
        try:
            ArchiveBorrowService.checkout_borrow(borrow, request.user)
            return Response({'status': 'out', 'message': '出库成功'})
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def return_archive(self, request, pk=None):
        """归还档案"""
        borrow = self.get_object()
        return_status = request.data.get('return_status', '完好')
        return_notes = request.data.get('return_notes', '')
        
        try:
            ArchiveBorrowService.return_borrow(borrow, request.user, return_status, return_notes)
            return Response({'status': 'returned', 'message': '归还成功'})
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class ArchiveDestroyViewSet(viewsets.ModelViewSet):
    """档案销毁视图集"""
    queryset = ArchiveDestroy.objects.all()
    serializer_class = ArchiveDestroySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'destroy_method']
    search_fields = ['destroy_number', 'destroyer__username']
    ordering_fields = ['created_time', 'destroy_date']
    ordering = ['-created_time']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.select_related(
            'project_document', 'administrative_archive',
            'destroyer', 'approver'
        )
        return queryset
    
    def perform_create(self, serializer):
        serializer.save(destroyer=self.request.user)
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """审批销毁"""
        destroy = self.get_object()
        approval_opinion = request.data.get('approval_opinion', '')
        approved = request.data.get('approved', True)
        
        try:
            ArchiveDestroyService.approve_destroy(destroy, request.user, approved, approval_opinion)
            return Response({'status': destroy.status, 'message': '审批完成'})
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def execute(self, request, pk=None):
        """执行销毁"""
        destroy = self.get_object()
        destroy_record = request.data.get('destroy_record', '')
        destroy_proof = request.FILES.get('destroy_proof')
        destroy_photos = request.data.get('destroy_photos', [])
        
        try:
            ArchiveDestroyService.execute_destroy(destroy, destroy_record, destroy_proof, destroy_photos)
            return Response({'status': 'destroyed', 'message': '销毁完成'})
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class ArchiveStorageRoomViewSet(viewsets.ModelViewSet):
    """档案库房视图集"""
    queryset = ArchiveStorageRoom.objects.all()
    serializer_class = ArchiveStorageRoomSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status']
    search_fields = ['room_number', 'room_name']
    ordering_fields = ['created_time']
    ordering = ['room_number']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.select_related('manager')
        return queryset


class ArchiveLocationViewSet(viewsets.ModelViewSet):
    """档案位置视图集"""
    queryset = ArchiveLocation.objects.all()
    serializer_class = ArchiveLocationSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['storage_room', 'location_type']
    search_fields = ['location_number', 'location_name']
    ordering_fields = ['created_time']
    ordering = ['storage_room', 'location_number']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.select_related('storage_room')
        return queryset


class ArchiveShelfViewSet(viewsets.ModelViewSet):
    """档案上架记录视图集"""
    queryset = ArchiveShelf.objects.all()
    serializer_class = ArchiveShelfSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['archive', 'location']
    search_fields = ['archive__archive_number', 'location__location_number']
    ordering_fields = ['shelf_time']
    ordering = ['-shelf_time']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.select_related('archive', 'location', 'shelf_by')
        return queryset
    
    def perform_create(self, serializer):
        serializer.save(shelf_by=self.request.user)


class ArchiveInventoryViewSet(viewsets.ModelViewSet):
    """档案盘点视图集"""
    queryset = ArchiveInventory.objects.all()
    serializer_class = ArchiveInventorySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['inventory_type', 'storage_room']
    search_fields = ['inventory_number', 'inventory_name']
    ordering_fields = ['created_time', 'inventory_date']
    ordering = ['-created_time']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.select_related('inventory_by', 'storage_room', 'category')
        return queryset
    
    def perform_create(self, serializer):
        serializer.save(inventory_by=self.request.user)

