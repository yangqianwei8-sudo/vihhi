from rest_framework import serializers
from .models import Project, ProjectTeam, PaymentPlan, ProjectMilestone, ProjectDocument, ProjectArchive

class ProjectTeamSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    user_username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = ProjectTeam
        fields = '__all__'

class PaymentPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentPlan
        fields = '__all__'

class ProjectMilestoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectMilestone
        fields = '__all__'

class ProjectDocumentSerializer(serializers.ModelSerializer):
    uploaded_by_name = serializers.CharField(source='uploaded_by.get_full_name', read_only=True)
    
    class Meta:
        model = ProjectDocument
        fields = '__all__'

class ProjectSerializer(serializers.ModelSerializer):
    project_manager_name = serializers.CharField(source='project_manager.get_full_name', read_only=True)
    business_manager_name = serializers.CharField(source='business_manager.get_full_name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    client_name = serializers.CharField(source='client.name', read_only=True)
    
    # 嵌套序列化器
    team_members = ProjectTeamSerializer(many=True, read_only=True)
    payment_plans = PaymentPlanSerializer(many=True, read_only=True)
    milestones = ProjectMilestoneSerializer(many=True, read_only=True)
    documents = ProjectDocumentSerializer(many=True, read_only=True)
    
    # 计算字段
    total_planned_amount = serializers.SerializerMethodField()
    total_actual_amount = serializers.SerializerMethodField()
    progress_rate = serializers.SerializerMethodField()
    
    class Meta:
        model = Project
        fields = '__all__'
        read_only_fields = ['project_number', 'created_time', 'updated_time']
    
    def get_total_planned_amount(self, obj):
        return sum(plan.planned_amount for plan in obj.payment_plans.all())
    
    def get_total_actual_amount(self, obj):
        return sum(plan.actual_amount for plan in obj.payment_plans.all() if plan.actual_amount)
    
    def get_progress_rate(self, obj):
        completed_milestones = obj.milestones.filter(is_completed=True).count()
        total_milestones = obj.milestones.count()
        return int((completed_milestones / total_milestones * 100) if total_milestones > 0 else 0)

class ProjectCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = [
            'subsidiary', 'name', 'alias', 'description',
            'service_type', 'business_type', 'design_stage', 'service_professions',
            'contract_number', 'contract_amount', 'contract_date', 'contract_file',
            'client_company_name', 'client_contact_person', 'client_phone', 
            'client_email', 'client_address',
            'design_company', 'design_contact_person', 'design_phone', 'design_email',
        ]
    
    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        validated_data['business_manager'] = self.context['request'].user
        validated_data['status'] = 'draft'
        return super().create(validated_data)

class ProjectArchiveSerializer(serializers.ModelSerializer):
    archived_by_name = serializers.CharField(source='archived_by.get_full_name', read_only=True)
    project_name = serializers.CharField(source='project.name', read_only=True)
    
    class Meta:
        model = ProjectArchive
        fields = '__all__'
        read_only_fields = ['archive_number', 'archive_time', 'created_time']
