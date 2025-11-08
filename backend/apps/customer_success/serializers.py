from rest_framework import serializers
from .models import Client, ClientContact, ClientProject

class ClientContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClientContact
        fields = '__all__'

class ClientProjectSerializer(serializers.ModelSerializer):
    project_name = serializers.CharField(source='project.name', read_only=True)
    project_number = serializers.CharField(source='project.project_number', read_only=True)
    
    class Meta:
        model = ClientProject
        fields = '__all__'

class ClientSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    contacts = ClientContactSerializer(many=True, read_only=True)
    projects = ClientProjectSerializer(many=True, read_only=True)
    
    # 统计字段
    project_count = serializers.IntegerField(read_only=True, source='get_project_count')
    active_project_count = serializers.IntegerField(read_only=True, source='get_active_project_count')
    
    class Meta:
        model = Client
        fields = [
            'id', 'name', 'short_name', 'code',
            'client_level', 'credit_level', 'industry',
            'address', 'phone', 'email', 'website',
            'total_contract_amount', 'total_payment_amount',
            'is_active', 'health_score', 'description',
            'created_by', 'created_by_name',
            'created_time', 'updated_time',
            'contacts', 'projects',
            'project_count', 'active_project_count'
        ]
        read_only_fields = ['created_time', 'updated_time']
    
    def get_project_count(self, obj):
        return obj.projects.count()
    
    def get_active_project_count(self, obj):
        return obj.projects.filter(status='in_progress').count()

class ClientCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = [
            'name', 'short_name', 'code', 'client_level',
            'credit_level', 'industry', 'address', 'phone',
            'email', 'website', 'description'
        ]
    
    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)
