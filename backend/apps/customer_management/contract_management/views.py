"""
合同管理模块API视图（RESTful API）

提供合同管理的RESTful API接口
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from backend.apps.production_management.models import BusinessContract
from .serializers import ContractSerializer
from .permissions import (
    check_contract_permission,
    PERMISSION_VIEW,
    PERMISSION_CREATE,
)
from .services import ContractService


class ContractViewSet(viewsets.ModelViewSet):
    """
    合同视图集
    
    提供合同的CRUD操作和业务操作接口
    """
    queryset = BusinessContract.objects.all()
    serializer_class = ContractSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'contract_type', 'client', 'project']
    search_fields = ['contract_number', 'contract_name', 'client__name']
    ordering_fields = ['created_time', 'contract_date', 'contract_amount']
    ordering = ['-created_time']
    
    def get_queryset(self):
        """获取查询集"""
        queryset = super().get_queryset()
        
        # 权限过滤
        user = self.request.user
        if not check_contract_permission(user, PERMISSION_VIEW):
            return queryset.none()
        
        return queryset.select_related('client', 'project', 'created_by')
    
    def create(self, request, *args, **kwargs):
        """创建合同"""
        if not check_contract_permission(request.user, PERMISSION_CREATE):
            return Response(
                {'error': '您没有权限创建合同'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        contract, success, error = ContractService.create_contract(
            serializer.validated_data,
            request.user
        )
        
        if success:
            return Response(
                ContractSerializer(contract).data,
                status=status.HTTP_201_CREATED
            )
        else:
            return Response(
                {'error': error},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def submit_approval(self, request, pk=None):
        """提交审核"""
        contract = self.get_object()
        success, error = ContractService.submit_for_approval(contract, request.user)
        
        if success:
            return Response({'message': '提交审核成功'})
        else:
            return Response(
                {'error': error},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """审核通过"""
        contract = self.get_object()
        approval_comment = request.data.get('comment', '')
        
        success, error = ContractService.approve_contract(
            contract,
            request.user,
            approval_comment
        )
        
        if success:
            return Response({'message': '审核通过'})
        else:
            return Response(
                {'error': error},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """拒绝审核"""
        contract = self.get_object()
        rejection_reason = request.data.get('reason', '')
        
        success, error = ContractService.reject_contract(
            contract,
            request.user,
            rejection_reason
        )
        
        if success:
            return Response({'message': '已拒绝'})
        else:
            return Response(
                {'error': error},
                status=status.HTTP_400_BAD_REQUEST
            )

