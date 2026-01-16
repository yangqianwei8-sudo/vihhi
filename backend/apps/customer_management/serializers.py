# ==================== 客户管理模块序列化器（按《客户管理详细设计方案 v1.12》实现）====================

from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    Client, ClientContact, ContactCareer, ContactEducation, ContactWorkExperience,
    ContactJobChange, ContactCooperation, ContactTracking,
    CustomerRelationship, CustomerRelationshipUpgrade, ClientProject
)

User = get_user_model()


# ==================== 客户序列化器 ====================

class ClientSerializer(serializers.ModelSerializer):
    """客户序列化器"""
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    responsible_user_name = serializers.CharField(source='responsible_user.get_full_name', read_only=True)
    client_level_display = serializers.CharField(source='get_client_level_display', read_only=True)
    grade_display = serializers.CharField(source='grade.name', read_only=True, allow_null=True)
    grade_code = serializers.CharField(source='grade.code', read_only=True, allow_null=True)
    credit_level_display = serializers.CharField(source='get_credit_level_display', read_only=True)
    client_type_display = serializers.CharField(source='client_type.name', read_only=True, allow_null=True)
    client_type_code = serializers.CharField(source='client_type.code', read_only=True, allow_null=True)
    source_display = serializers.CharField(source='get_source_display', read_only=True)
    public_sea_reason_display = serializers.CharField(source='get_public_sea_reason_display', read_only=True)
    
    class Meta:
        model = Client
        fields = [
            'id', 'name', 'unified_credit_code',
            'legal_representative', 'established_date', 'registered_capital',
            'company_phone', 'company_email', 'company_address',
            'client_level', 'client_level_display', 'grade', 'grade_display', 'grade_code',
            'credit_level', 'credit_level_display', 'client_type', 'client_type_display', 'client_type_code',
            'industry', 'region', 'source', 'source_display',
            'score', 'health_score',
            'total_contract_amount', 'total_payment_amount',
            'legal_risk_level', 'litigation_count', 'executed_person_count',
            'final_case_count', 'consumption_limit_count',
            'contact_name', 'contact_position', 'phone',
            'description', 'is_active',
            'responsible_user', 'responsible_user_name',
            'public_sea_entry_time', 'public_sea_reason', 'public_sea_reason_display',
            'created_by', 'created_by_name',
            'created_time', 'updated_time',
        ]
        read_only_fields = ['created_time', 'updated_time', 'score', 'grade', 'health_score']


class ClientCreateSerializer(serializers.ModelSerializer):
    """客户创建序列化器"""
    
    class Meta:
        model = Client
        fields = [
            'name', 'unified_credit_code',
            'legal_representative', 'established_date', 'registered_capital',
            'company_phone', 'company_email', 'company_address',
            'client_level', 'credit_level', 'client_type',
            'industry', 'region', 'source',
            'contact_name', 'contact_position', 'phone',
            'description', 'is_active',
        ]
    
    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


# ==================== 联系人序列化器 ====================

class ContactEducationSerializer(serializers.ModelSerializer):
    """教育背景序列化器"""
    degree_display = serializers.CharField(source='get_degree_display', read_only=True)
    
    class Meta:
        model = ContactEducation
        fields = [
            'id', 'school', 'major', 'degree', 'degree_display',
            'start_date', 'end_date', 'description',
        ]


class ContactWorkExperienceSerializer(serializers.ModelSerializer):
    """工作经历序列化器"""
    
    class Meta:
        model = ContactWorkExperience
        fields = [
            'id', 'company_name', 'position', 'start_date', 'end_date',
            'office_address', 'description',
        ]


class ContactCareerSerializer(serializers.ModelSerializer):
    """联系人职业信息序列化器"""
    duration = serializers.SerializerMethodField()
    
    class Meta:
        model = ContactCareer
        fields = [
            'id', 'company', 'unified_credit_code', 'department', 'position',
            'join_date', 'leave_date', 'duration',
            'created_time', 'updated_time',
        ]
        read_only_fields = ['created_time', 'updated_time']
    
    def get_duration(self, obj):
        """计算工作持续时间（年）"""
        return obj.calculate_duration()


class ClientContactSerializer(serializers.ModelSerializer):
    """联系人序列化器"""
    client_name = serializers.CharField(source='client.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    gender_display = serializers.CharField(source='get_gender_display', read_only=True)
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    relationship_level_display = serializers.CharField(source='get_relationship_level_display', read_only=True)
    decision_influence_display = serializers.CharField(source='get_decision_influence_display', read_only=True)
    contact_frequency_display = serializers.CharField(source='get_contact_frequency_display', read_only=True)
    
    educations = ContactEducationSerializer(many=True, read_only=True)
    work_experiences = ContactWorkExperienceSerializer(many=True, read_only=True)
    careers = ContactCareerSerializer(many=True, read_only=True)
    
    class Meta:
        model = ClientContact
        fields = [
            'id', 'client', 'client_name', 'name',
            'gender', 'gender_display', 'birthplace',
            'phone', 'email', 'wechat',
            'office_address',
            'role', 'role_display', 'relationship_level', 'relationship_level_display',
            'decision_influence', 'decision_influence_display', 'relationship_score',
            'first_contact_time', 'last_contact_time', 'contact_frequency', 'contact_frequency_display',
            'preferred_contact_methods', 'best_contact_time',
            'interests', 'focus_areas', 'tags',
            'is_primary', 'notes',
            'resume_file', 'resume_source', 'resume_upload_time',
            'educations', 'work_experiences', 'careers',
            'created_by', 'created_by_name',
            'created_time', 'updated_time',
        ]
        read_only_fields = ['created_time', 'updated_time', 'relationship_score']


class ClientContactCreateSerializer(serializers.ModelSerializer):
    """联系人创建序列化器"""
    careers = ContactCareerSerializer(many=True, required=False)
    
    class Meta:
        model = ClientContact
        fields = [
            'client', 'name', 'gender', 'birthplace',
            'phone', 'email', 'wechat',
            'office_address',
            'role', 'relationship_level', 'decision_influence',
            'first_contact_time', 'last_contact_time', 'contact_frequency',
            'preferred_contact_methods', 'best_contact_time',
            'interests', 'focus_areas', 'tags',
            'is_primary', 'notes',
            'resume_file', 'resume_source',
            'careers',
        ]
    
    def create(self, validated_data):
        careers_data = validated_data.pop('careers', [])
        validated_data['created_by'] = self.context['request'].user
        contact = super().create(validated_data)
        
        # 创建职业信息
        for career_data in careers_data:
            ContactCareer.objects.create(contact=contact, **career_data)
        
        return contact


# ==================== 工作变动、合作、跟踪序列化器 ====================

class ContactJobChangeSerializer(serializers.ModelSerializer):
    """工作变动序列化器"""
    change_type_display = serializers.CharField(source='get_change_type_display', read_only=True)
    
    class Meta:
        model = ContactJobChange
        fields = [
            'id', 'contact', 'change_date', 'change_type', 'change_type_display',
            'old_company', 'new_company', 'old_position', 'new_position',
            'reason', 'notes',
        ]


class ContactCooperationSerializer(serializers.ModelSerializer):
    """合作信息序列化器"""
    cooperation_type_display = serializers.CharField(source='get_cooperation_type_display', read_only=True)
    
    class Meta:
        model = ContactCooperation
        fields = [
            'id', 'contact', 'cooperation_date', 'cooperation_type', 'cooperation_type_display',
            'content', 'amount', 'notes',
        ]


class ContactTrackingSerializer(serializers.ModelSerializer):
    """跟踪信息序列化器"""
    tracking_method_display = serializers.CharField(source='get_tracking_method_display', read_only=True)
    tracked_by_name = serializers.CharField(source='tracked_by.get_full_name', read_only=True)
    
    class Meta:
        model = ContactTracking
        fields = [
            'id', 'contact', 'tracking_date', 'tracking_method', 'tracking_method_display',
            'content', 'tracked_by', 'tracked_by_name',
        ]


# ==================== 客户关系序列化器 ====================

class CustomerRelationshipSerializer(serializers.ModelSerializer):
    """客户关系（跟进与拜访）序列化器"""
    client_name = serializers.CharField(source='client.name', read_only=True)
    followup_person_name = serializers.CharField(source='followup_person.get_full_name', read_only=True)
    followup_method_display = serializers.CharField(source='get_followup_method_display', read_only=True)
    relationship_level_display = serializers.CharField(source='get_relationship_level_display', read_only=True)
    related_contacts_names = serializers.SerializerMethodField()
    
    class Meta:
        model = CustomerRelationship
        fields = [
            'id', 'client', 'client_name',
            'followup_method', 'followup_method_display',
            'content', 'followup_time',
            'related_contacts', 'related_contacts_names',
            'relationship_level', 'relationship_level_display',
            'followup_person', 'followup_person_name',
            'created_time', 'updated_time',
        ]
        read_only_fields = ['created_time', 'updated_time']
    
    def get_related_contacts_names(self, obj):
        """获取关联联系人名称列表"""
        return [contact.name for contact in obj.related_contacts.all()]


class CustomerRelationshipCreateSerializer(serializers.ModelSerializer):
    """客户关系创建序列化器"""
    
    class Meta:
        model = CustomerRelationship
        fields = [
            'client', 'followup_method', 'content', 'followup_time',
            'related_contacts', 'relationship_level',
        ]
    
    def create(self, validated_data):
        validated_data['followup_person'] = self.context['request'].user
        return super().create(validated_data)


# ==================== 关系升级序列化器 ====================

class CustomerRelationshipUpgradeSerializer(serializers.ModelSerializer):
    """关系升级序列化器"""
    client_name = serializers.CharField(source='client.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    from_level_display = serializers.CharField(source='get_from_level_display', read_only=True)
    to_level_display = serializers.CharField(source='get_to_level_display', read_only=True)
    approval_status_display = serializers.CharField(source='get_approval_status_display', read_only=True)
    related_contacts_names = serializers.SerializerMethodField()
    
    class Meta:
        model = CustomerRelationshipUpgrade
        fields = [
            'id', 'client', 'client_name',
            'from_level', 'from_level_display',
            'to_level', 'to_level_display',
            'upgrade_reason', 'related_contacts', 'related_contacts_names',
            'approval_status', 'approval_status_display',
            'approval_instance', 'created_by', 'created_by_name',
            'created_time', 'updated_time',
        ]
        read_only_fields = ['created_time', 'updated_time', 'approval_status', 'approval_instance']
    
    def get_related_contacts_names(self, obj):
        """获取关联联系人名称列表"""
        return [contact.name for contact in obj.related_contacts.all()]


class CustomerRelationshipUpgradeCreateSerializer(serializers.ModelSerializer):
    """关系升级创建序列化器"""
    
    class Meta:
        model = CustomerRelationshipUpgrade
        fields = [
            'client', 'from_level', 'to_level', 'upgrade_reason', 'related_contacts',
        ]
    
    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


# ==================== 客户项目序列化器 ====================

class ClientProjectSerializer(serializers.ModelSerializer):
    """客户项目序列化器（用于统计）"""
    project_name = serializers.CharField(source='project.name', read_only=True)
    project_number = serializers.CharField(source='project.project_number', read_only=True)
    
    class Meta:
        model = ClientProject
        fields = [
            'id', 'client', 'project', 'project_name', 'project_number',
            'created_time',
        ]
