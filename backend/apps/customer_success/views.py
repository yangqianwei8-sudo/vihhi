from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q, Count, Sum
from django_filters.rest_framework import DjangoFilterBackend
from .models import Client, ClientContact, ClientProject
from .serializers import (
    ClientSerializer, ClientCreateSerializer, 
    ClientContactSerializer, ClientProjectSerializer
)

class ClientViewSet(viewsets.ModelViewSet):
    queryset = Client.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['client_level', 'credit_level', 'is_active']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return ClientCreateSerializer
        return ClientSerializer
    
    def get_queryset(self):
        queryset = Client.objects.all()
        
        # 搜索功能
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(short_name__icontains=search) |
                Q(code__icontains=search)
            )
        
        return queryset.select_related('created_by').prefetch_related('contacts', 'projects')
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """客户统计信息"""
        total_clients = Client.objects.count()
        active_clients = Client.objects.filter(is_active=True).count()
        vip_clients = Client.objects.filter(client_level='vip').count()
        
        # 财务统计
        total_contract_amount = Client.objects.aggregate(
            total=Sum('total_contract_amount')
        )['total'] or 0
        
        total_payment_amount = Client.objects.aggregate(
            total=Sum('total_payment_amount')
        )['total'] or 0
        
        statistics = {
            'total_clients': total_clients,
            'active_clients': active_clients,
            'vip_clients': vip_clients,
            'total_contract_amount': float(total_contract_amount),
            'total_payment_amount': float(total_payment_amount),
            'payment_rate': float((total_payment_amount / total_contract_amount * 100) if total_contract_amount > 0 else 0),
        }
        
        return Response(statistics)

class ClientContactViewSet(viewsets.ModelViewSet):
    queryset = ClientContact.objects.all()
    serializer_class = ClientContactSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = ClientContact.objects.all()
        client_id = self.request.query_params.get('client')
        if client_id:
            queryset = queryset.filter(client_id=client_id)
        return queryset.select_related('client')

class ClientProjectViewSet(viewsets.ModelViewSet):
    queryset = ClientProject.objects.all()
    serializer_class = ClientProjectSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = ClientProject.objects.all()
        client_id = self.request.query_params.get('client')
        if client_id:
            queryset = queryset.filter(client_id=client_id)
        return queryset.select_related('client', 'project')
