"""
结算中心模块的API视图
"""
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.db.models import Q
from decimal import Decimal

from backend.apps.settlement_center.models import (
    ServiceFeeSettlementScheme,
    ServiceFeeSegmentedRate,
    ServiceFeeJumpPointRate,
    ServiceFeeUnitCapDetail
)
from backend.apps.settlement_center.serializers import (
    ServiceFeeSettlementSchemeSerializer,
    ServiceFeeSettlementSchemeCreateSerializer,
    ServiceFeeSegmentedRateSerializer,
    ServiceFeeJumpPointRateSerializer,
    ServiceFeeUnitCapDetailSerializer,
    ServiceFeeCalculationSerializer,
    ServiceFeeCalculationResultSerializer
)
from backend.apps.settlement_center.services import (
    get_service_fee_scheme,
    calculate_service_fee_by_scheme
)


class ServiceFeeSettlementSchemeViewSet(viewsets.ModelViewSet):
    """服务费结算方案视图集"""
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['contract', 'project', 'settlement_method', 'is_active', 'is_default']
    search_fields = ['name', 'code', 'description']
    ordering_fields = ['created_time', 'updated_time', 'sort_order']
    ordering = ['sort_order', '-created_time']
    
    def get_queryset(self):
        queryset = ServiceFeeSettlementScheme.objects.with_relations().all()
        
        # 根据合同或项目过滤
        contract_id = self.request.query_params.get('contract_id')
        project_id = self.request.query_params.get('project_id')
        
        if contract_id:
            queryset = queryset.filter(
                Q(contract_id=contract_id) | Q(contract__isnull=True)
            )
        
        if project_id:
            queryset = queryset.filter(
                Q(project_id=project_id) | Q(project__isnull=True)
            )
        
        return queryset
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return ServiceFeeSettlementSchemeCreateSerializer
        return ServiceFeeSettlementSchemeSerializer
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    def perform_destroy(self, instance):
        """删除前检查是否可以删除"""
        if instance.is_used():
            from rest_framework.exceptions import ValidationError
            raise ValidationError({
                'error': '该结算方案已被使用，无法删除。如需删除，请先解除所有关联的结算单。'
            })
        if instance.is_default:
            from rest_framework.exceptions import ValidationError
            raise ValidationError({
                'error': '默认方案无法删除，请先取消默认设置。'
            })
        super().perform_destroy(instance)
    
    @action(detail=False, methods=['get'])
    def by_contract(self, request):
        """根据合同获取结算方案"""
        from backend.apps.production_management.models import BusinessContract
        
        contract_id = request.query_params.get('contract_id')
        if not contract_id:
            return Response(
                {'error': '缺少contract_id参数'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            contract = BusinessContract.objects.get(id=contract_id)
        except BusinessContract.DoesNotExist:
            return Response(
                {'error': '合同不存在'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        scheme = get_service_fee_scheme(contract=contract)
        if scheme:
            serializer = self.get_serializer(scheme)
            return Response(serializer.data)
        return Response({'detail': '未找到结算方案'}, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=False, methods=['get'])
    def by_project(self, request):
        """根据项目获取结算方案"""
        from backend.apps.production_management.models import Project
        
        project_id = request.query_params.get('project_id')
        if not project_id:
            return Response(
                {'error': '缺少project_id参数'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            project = Project.objects.get(id=project_id)
        except Project.DoesNotExist:
            return Response(
                {'error': '项目不存在'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        scheme = get_service_fee_scheme(project=project)
        if scheme:
            serializer = self.get_serializer(scheme)
            return Response(serializer.data)
        return Response({'detail': '未找到结算方案'}, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=True, methods=['post'])
    def calculate(self, request, pk=None):
        """计算服务费"""
        scheme = self.get_object()
        
        serializer = ServiceFeeCalculationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        saving_amount = serializer.validated_data.get('saving_amount')
        service_area = serializer.validated_data.get('service_area')
        unit_cap_details = serializer.validated_data.get('unit_cap_details')
        
        # 转换为Decimal
        if saving_amount is not None:
            saving_amount = Decimal(str(saving_amount))
        if service_area is not None:
            service_area = Decimal(str(service_area))
        
        # 计算服务费
        result = calculate_service_fee_by_scheme(
            scheme=scheme,
            saving_amount=saving_amount,
            service_area=service_area,
            unit_cap_details=unit_cap_details
        )
        
        result_serializer = ServiceFeeCalculationResultSerializer(result)
        return Response(result_serializer.data)
    
    @action(detail=False, methods=['post'])
    def calculate_by_scheme_id(self, request):
        """根据方案ID计算服务费"""
        serializer = ServiceFeeCalculationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        scheme_id = serializer.validated_data['scheme_id']
        saving_amount = serializer.validated_data.get('saving_amount')
        service_area = serializer.validated_data.get('service_area')
        unit_cap_details = serializer.validated_data.get('unit_cap_details')
        
        try:
            scheme = ServiceFeeSettlementScheme.objects.get(id=scheme_id, is_active=True)
        except ServiceFeeSettlementScheme.DoesNotExist:
            return Response(
                {'error': '结算方案不存在或已禁用'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # 转换为Decimal
        if saving_amount is not None:
            saving_amount = Decimal(str(saving_amount))
        if service_area is not None:
            service_area = Decimal(str(service_area))
        
        # 计算服务费
        result = calculate_service_fee_by_scheme(
            scheme=scheme,
            saving_amount=saving_amount,
            service_area=service_area,
            unit_cap_details=unit_cap_details
        )
        
        result_serializer = ServiceFeeCalculationResultSerializer(result)
        return Response(result_serializer.data)
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """获取结算方案统计信息"""
        from backend.apps.settlement_center.services import get_scheme_statistics
        
        scheme_id = request.query_params.get('scheme_id')
        contract_id = request.query_params.get('contract_id')
        project_id = request.query_params.get('project_id')
        
        stats = get_scheme_statistics(
            scheme_id=scheme_id,
            contract_id=contract_id,
            project_id=project_id
        )
        
        return Response(stats)
    
    @action(detail=True, methods=['post'])
    def validate_config(self, request, pk=None):
        """验证结算方案配置"""
        from backend.apps.settlement_center.services import validate_scheme_configuration
        
        scheme = self.get_object()
        result = validate_scheme_configuration(scheme)
        
        return Response(result)
    
    @action(detail=True, methods=['post'])
    def duplicate(self, request, pk=None):
        """复制结算方案"""
        from backend.apps.settlement_center.services import duplicate_scheme
        
        scheme = self.get_object()
        new_name = request.data.get('new_name')
        new_contract_id = request.data.get('new_contract_id')
        new_project_id = request.data.get('new_project_id')
        
        new_contract = None
        if new_contract_id:
            from backend.apps.production_management.models import BusinessContract
            try:
                new_contract = BusinessContract.objects.get(id=new_contract_id)
            except BusinessContract.DoesNotExist:
                return Response(
                    {'error': '合同不存在'},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        new_project = None
        if new_project_id:
            from backend.apps.production_management.models import Project
            try:
                new_project = Project.objects.get(id=new_project_id)
            except Project.DoesNotExist:
                return Response(
                    {'error': '项目不存在'},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        new_scheme = duplicate_scheme(
            scheme=scheme,
            new_name=new_name,
            new_contract=new_contract,
            new_project=new_project
        )
        
        serializer = self.get_serializer(new_scheme)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ServiceFeeSegmentedRateViewSet(viewsets.ModelViewSet):
    """分段递增提成配置视图集"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ServiceFeeSegmentedRateSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['scheme', 'is_active']
    ordering_fields = ['order', 'threshold']
    ordering = ['order', 'threshold']
    
    def get_queryset(self):
        return ServiceFeeSegmentedRate.objects.select_related('scheme').all()


class ServiceFeeJumpPointRateViewSet(viewsets.ModelViewSet):
    """跳点提成配置视图集"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ServiceFeeJumpPointRateSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['scheme', 'is_active']
    ordering_fields = ['order', 'threshold']
    ordering = ['order', 'threshold']
    
    def get_queryset(self):
        return ServiceFeeJumpPointRate.objects.select_related('scheme').all()


class ServiceFeeUnitCapDetailViewSet(viewsets.ModelViewSet):
    """单价封顶费明细视图集"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ServiceFeeUnitCapDetailSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['scheme']
    ordering_fields = ['order', 'unit_name']
    ordering = ['order', 'unit_name']
    
    def get_queryset(self):
        return ServiceFeeUnitCapDetail.objects.select_related('scheme').all()

