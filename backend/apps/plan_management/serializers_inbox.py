"""
审批待办箱序列化器（轻量级，仅用于列表展示）
C2-1-1: 提供 Plan 和 Goal 的轻量序列化器，避免字段膨胀
"""
from rest_framework import serializers
from .models import Plan, StrategicGoal


class PlanInboxItemSerializer(serializers.ModelSerializer):
    """计划待办项序列化器（轻量）"""
    number = serializers.CharField(source='plan_number', read_only=True)
    title = serializers.CharField(source='name', read_only=True)
    responsible_person = serializers.SerializerMethodField()
    created_by = serializers.SerializerMethodField()
    created_at = serializers.DateTimeField(source='created_time', read_only=True)
    company = serializers.SerializerMethodField()
    org_department = serializers.SerializerMethodField()
    
    class Meta:
        model = Plan
        fields = [
            'id',
            'number',
            'title',
            'status',
            'plan_period',
            'responsible_person',
            'created_by',
            'created_at',
            'company',
            'org_department',
        ]
    
    def get_responsible_person(self, obj):
        """返回负责人信息"""
        if obj.responsible_person:
            return {
                'id': obj.responsible_person.id,
                'username': obj.responsible_person.username,
            }
        return None
    
    def get_created_by(self, obj):
        """返回创建人信息"""
        if obj.created_by:
            return {
                'id': obj.created_by.id,
                'username': obj.created_by.username,
            }
        return None
    
    def get_company(self, obj):
        """返回公司信息"""
        if obj.company:
            return {
                'id': obj.company.id,
                'name': obj.company.name,
            }
        return None
    
    def get_org_department(self, obj):
        """返回部门信息"""
        if obj.org_department:
            return {
                'id': obj.org_department.id,
                'name': obj.org_department.name,
            }
        return None


class GoalInboxItemSerializer(serializers.ModelSerializer):
    """目标待办项序列化器（轻量）"""
    number = serializers.CharField(source='goal_number', read_only=True)
    title = serializers.CharField(source='indicator_name', read_only=True)
    responsible_person = serializers.SerializerMethodField()
    created_by = serializers.SerializerMethodField()
    created_at = serializers.DateTimeField(source='created_time', read_only=True)
    company = serializers.SerializerMethodField()
    org_department = serializers.SerializerMethodField()
    
    class Meta:
        model = StrategicGoal
        fields = [
            'id',
            'number',
            'title',
            'status',
            'goal_period',
            'responsible_person',
            'created_by',
            'created_at',
            'company',
            'org_department',
        ]
    
    def get_responsible_person(self, obj):
        """返回负责人信息"""
        if obj.responsible_person:
            return {
                'id': obj.responsible_person.id,
                'username': obj.responsible_person.username,
            }
        return None
    
    def get_created_by(self, obj):
        """返回创建人信息"""
        if obj.created_by:
            return {
                'id': obj.created_by.id,
                'username': obj.created_by.username,
            }
        return None
    
    def get_company(self, obj):
        """返回公司信息"""
        if obj.company:
            return {
                'id': obj.company.id,
                'name': obj.company.name,
            }
        return None
    
    def get_org_department(self, obj):
        """返回部门信息"""
        if obj.org_department:
            return {
                'id': obj.org_department.id,
                'name': obj.org_department.name,
            }
        return None

