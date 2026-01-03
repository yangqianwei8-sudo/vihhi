"""
结算中心模块的序列化器
"""
from rest_framework import serializers
from backend.apps.settlement_center.models import (
    ServiceFeeSettlementScheme,
    ServiceFeeSegmentedRate,
    ServiceFeeJumpPointRate,
    ServiceFeeUnitCapDetail
)
from backend.apps.production_management.models import BusinessContract, Project


class ServiceFeeSegmentedRateSerializer(serializers.ModelSerializer):
    """分段递增提成配置序列化器"""
    
    class Meta:
        model = ServiceFeeSegmentedRate
        fields = [
            'id', 'scheme', 'threshold', 'rate', 'description', 
            'order', 'is_active', 'created_time', 'updated_time'
        ]
        read_only_fields = ['id', 'created_time', 'updated_time']


class ServiceFeeJumpPointRateSerializer(serializers.ModelSerializer):
    """跳点提成配置序列化器"""
    
    class Meta:
        model = ServiceFeeJumpPointRate
        fields = [
            'id', 'scheme', 'threshold', 'rate', 'description',
            'order', 'is_active', 'created_time', 'updated_time'
        ]
        read_only_fields = ['id', 'created_time', 'updated_time']


class ServiceFeeUnitCapDetailSerializer(serializers.ModelSerializer):
    """单价封顶费明细序列化器"""
    
    class Meta:
        model = ServiceFeeUnitCapDetail
        fields = [
            'id', 'scheme', 'unit_name', 'cap_unit_price', 'description',
            'order', 'created_time', 'updated_time'
        ]
        read_only_fields = ['id', 'created_time', 'updated_time']


class ServiceFeeSettlementSchemeSerializer(serializers.ModelSerializer):
    """服务费结算方案序列化器"""
    
    # 嵌套序列化器
    segmented_rates = ServiceFeeSegmentedRateSerializer(many=True, read_only=True)
    jump_point_rates = ServiceFeeJumpPointRateSerializer(many=True, read_only=True)
    unit_cap_details = ServiceFeeUnitCapDetailSerializer(many=True, read_only=True)
    
    # 关联对象信息
    contract_number = serializers.CharField(source='contract.contract_number', read_only=True)
    contract_name = serializers.CharField(source='contract.contract_name', read_only=True)
    project_number = serializers.CharField(source='project.project_number', read_only=True)
    project_name = serializers.CharField(source='project.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    
    # 计算字段
    settlement_method_display = serializers.CharField(source='get_settlement_method_display', read_only=True)
    area_type_display = serializers.CharField(source='get_area_type_display', read_only=True)
    cap_type_display = serializers.CharField(source='get_cap_type_display', read_only=True)
    
    class Meta:
        model = ServiceFeeSettlementScheme
        fields = [
            'id', 'name', 'code', 'description',
            'contract', 'contract_number', 'contract_name',
            'project', 'project_number', 'project_name',
            'settlement_method', 'settlement_method_display',
            # 方式一：固定价款
            'fixed_total_price', 'fixed_unit_price', 'area_type', 'area_type_display',
            # 方式二：按实结算
            'cumulative_rate',
            # 方式三：组合方式
            'combined_fixed_method', 'combined_fixed_total', 'combined_fixed_unit',
            'combined_fixed_area_type', 'combined_actual_method', 'combined_cumulative_rate',
            'combined_deduct_fixed',
            # 封顶费和保底费
            'has_cap_fee', 'cap_type', 'cap_type_display', 'total_cap_amount',
            'has_minimum_fee', 'minimum_fee_amount',
            # 嵌套数据
            'segmented_rates', 'jump_point_rates', 'unit_cap_details',
            # 状态和排序
            'is_active', 'is_default', 'sort_order',
            # 创建信息
            'created_by', 'created_by_name', 'created_time', 'updated_time'
        ]
        read_only_fields = ['id', 'created_time', 'updated_time']


class ServiceFeeSettlementSchemeCreateSerializer(serializers.ModelSerializer):
    """服务费结算方案创建序列化器（包含嵌套数据）"""
    
    segmented_rates = ServiceFeeSegmentedRateSerializer(many=True, required=False)
    jump_point_rates = ServiceFeeJumpPointRateSerializer(many=True, required=False)
    unit_cap_details = ServiceFeeUnitCapDetailSerializer(many=True, required=False)
    
    class Meta:
        model = ServiceFeeSettlementScheme
        fields = [
            'name', 'code', 'description',
            'contract', 'project',
            'settlement_method',
            'fixed_total_price', 'fixed_unit_price', 'area_type',
            'cumulative_rate',
            'combined_fixed_method', 'combined_fixed_total', 'combined_fixed_unit',
            'combined_fixed_area_type', 'combined_actual_method', 'combined_cumulative_rate',
            'combined_deduct_fixed',
            'has_cap_fee', 'cap_type', 'total_cap_amount',
            'has_minimum_fee', 'minimum_fee_amount',
            'is_active', 'is_default', 'sort_order',
            'segmented_rates', 'jump_point_rates', 'unit_cap_details'
        ]
    
    def create(self, validated_data):
        """创建结算方案及其关联数据"""
        segmented_rates_data = validated_data.pop('segmented_rates', [])
        jump_point_rates_data = validated_data.pop('jump_point_rates', [])
        unit_cap_details_data = validated_data.pop('unit_cap_details', [])
        
        # 创建主方案
        scheme = ServiceFeeSettlementScheme.objects.create(**validated_data)
        
        # 创建分段递增提成配置
        for rate_data in segmented_rates_data:
            ServiceFeeSegmentedRate.objects.create(scheme=scheme, **rate_data)
        
        # 创建跳点提成配置
        for rate_data in jump_point_rates_data:
            ServiceFeeJumpPointRate.objects.create(scheme=scheme, **rate_data)
        
        # 创建单价封顶费明细
        for detail_data in unit_cap_details_data:
            ServiceFeeUnitCapDetail.objects.create(scheme=scheme, **detail_data)
        
        return scheme
    
    def update(self, instance, validated_data):
        """更新结算方案及其关联数据"""
        segmented_rates_data = validated_data.pop('segmented_rates', None)
        jump_point_rates_data = validated_data.pop('jump_point_rates', None)
        unit_cap_details_data = validated_data.pop('unit_cap_details', None)
        
        # 更新主方案
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # 更新分段递增提成配置
        if segmented_rates_data is not None:
            instance.segmented_rates.all().delete()
            for rate_data in segmented_rates_data:
                ServiceFeeSegmentedRate.objects.create(scheme=instance, **rate_data)
        
        # 更新跳点提成配置
        if jump_point_rates_data is not None:
            instance.jump_point_rates.all().delete()
            for rate_data in jump_point_rates_data:
                ServiceFeeJumpPointRate.objects.create(scheme=instance, **rate_data)
        
        # 更新单价封顶费明细
        if unit_cap_details_data is not None:
            instance.unit_cap_details.all().delete()
            for detail_data in unit_cap_details_data:
                ServiceFeeUnitCapDetail.objects.create(scheme=instance, **detail_data)
        
        return instance


class ServiceFeeCalculationSerializer(serializers.Serializer):
    """服务费计算请求序列化器"""
    scheme_id = serializers.IntegerField(help_text='结算方案ID')
    saving_amount = serializers.DecimalField(
        max_digits=14, decimal_places=2, 
        required=False, allow_null=True,
        help_text='节省金额（按实结算时使用）'
    )
    service_area = serializers.DecimalField(
        max_digits=12, decimal_places=2,
        required=False, allow_null=True,
        help_text='服务面积（固定单价时使用）'
    )
    unit_cap_details = serializers.ListField(
        child=serializers.DictField(),
        required=False,
        help_text='单价封顶明细列表，格式：[{"unit_name": "单体名称", "area": 面积, "cap_unit_price": 封顶单价}]'
    )


class ServiceFeeCalculationResultSerializer(serializers.Serializer):
    """服务费计算结果序列化器"""
    settlement_price = serializers.DecimalField(max_digits=14, decimal_places=2, help_text='结算价（应用封顶和保底前）')
    final_fee = serializers.DecimalField(max_digits=14, decimal_places=2, help_text='最终服务费（应用封顶和保底后）')
    fixed_part = serializers.DecimalField(max_digits=14, decimal_places=2, help_text='固定部分（组合方式时）')
    actual_part = serializers.DecimalField(max_digits=14, decimal_places=2, help_text='按实结算部分（组合方式时）')
    cap_fee = serializers.DecimalField(max_digits=14, decimal_places=2, allow_null=True, help_text='封顶费')
    # minimum_fee 字段已删除
    calculation_details = serializers.DictField(help_text='计算明细')

