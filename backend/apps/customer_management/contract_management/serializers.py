"""
合同管理模块序列化器

用于API接口的数据序列化和反序列化
"""

from rest_framework import serializers
from backend.apps.production_management.models import BusinessContract
# Client和Project模型在其他模块中，这里不需要导入


class ContractSerializer(serializers.ModelSerializer):
    """合同序列化器"""
    
    client_name = serializers.CharField(source='client.name', read_only=True)
    project_name = serializers.CharField(source='project.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    contract_type_display = serializers.CharField(source='get_contract_type_display', read_only=True)
    structure_type_display = serializers.CharField(source='get_structure_type_display', read_only=True)
    design_unit_category_display = serializers.CharField(source='get_design_unit_category_display', read_only=True)
    
    class Meta:
        model = BusinessContract
        fields = [
            'id',
            'contract_number',
            'contract_name',
            'contract_type',
            'contract_type_display',
            'status',
            'status_display',
            'client',
            'client_name',
            'project',
            'project_name',
            'structure_type',
            'structure_type_display',
            'design_unit_category',
            'design_unit_category_display',
            'contract_amount',
            'contract_amount_tax',
            'contract_amount_excl_tax',
            'tax_rate',
            'settlement_amount',
            'payment_amount',
            'unpaid_amount',
            'contract_date',
            'effective_date',
            'start_date',
            'end_date',
            'contract_period',
            'created_by',
            'created_by_name',
            'created_time',
            'updated_time',
        ]
        read_only_fields = [
            'id',
            'contract_number',
            'created_by',
            'created_time',
            'updated_time',
            'unpaid_amount',
        ]


class ContractListSerializer(serializers.ModelSerializer):
    """合同列表序列化器（简化版）"""
    
    client_name = serializers.CharField(source='client.name', read_only=True)
    project_name = serializers.CharField(source='project.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = BusinessContract
        fields = [
            'id',
            'contract_number',
            'contract_name',
            'status',
            'status_display',
            'client_name',
            'project_name',
            'contract_amount',
            'contract_date',
            'created_time',
        ]

