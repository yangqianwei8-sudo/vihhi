from rest_framework import serializers
from .models import (
    Project,
    ProjectTeam,
    ProjectMilestone,
    ProjectDocument,
    ProjectArchive,
    ProjectTeamNotification,
    ProjectDrawingSubmission,
    ProjectDrawingReview,
    ProjectDrawingFile,
    ProjectStartNotice,
    ServiceProfession,
)

class ProjectTeamSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    user_username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = ProjectTeam
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

class ProjectDrawingFileSerializer(serializers.ModelSerializer):
    uploaded_by_name = serializers.CharField(source='uploaded_by.get_full_name', read_only=True)

    class Meta:
        model = ProjectDrawingFile
        fields = '__all__'
        read_only_fields = ['uploaded_time', 'uploaded_by']


class ProjectDrawingReviewSerializer(serializers.ModelSerializer):
    reviewer_name = serializers.CharField(source='reviewer.get_full_name', read_only=True)
    reviewer_username = serializers.CharField(source='reviewer.username', read_only=True)

    class Meta:
        model = ProjectDrawingReview
        fields = '__all__'
        read_only_fields = ['reviewed_time']


class ProjectDrawingSubmissionSerializer(serializers.ModelSerializer):
    submitter_name = serializers.CharField(source='submitter.get_full_name', read_only=True)
    submitter_username = serializers.CharField(source='submitter.username', read_only=True)
    project_name = serializers.CharField(source='project.name', read_only=True)
    latest_review_detail = ProjectDrawingReviewSerializer(source='latest_review', read_only=True)
    files = ProjectDrawingFileSerializer(many=True, read_only=True)
    reviews = ProjectDrawingReviewSerializer(many=True, read_only=True)

    class Meta:
        model = ProjectDrawingSubmission
        fields = '__all__'
        read_only_fields = [
            'submitted_time',
            'submitter',
            'latest_review',
            'client_notified',
            'client_notified_time',
            'created_time',
            'updated_time',
        ]


class ProjectStartNoticeSerializer(serializers.ModelSerializer):
    project_name = serializers.CharField(source='project.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    recipient_user_name = serializers.CharField(source='recipient_user.get_full_name', read_only=True)

    class Meta:
        model = ProjectStartNotice
        fields = '__all__'
        read_only_fields = [
            'created_time',
            'sent_time',
            'acknowledged_time',
            'created_by',
        ]


class ProjectSerializer(serializers.ModelSerializer):
    project_manager_name = serializers.CharField(source='project_manager.get_full_name', read_only=True)
    business_manager_name = serializers.CharField(source='business_manager.get_full_name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    client_name = serializers.CharField(source='client.name', read_only=True)
    service_type_name = serializers.CharField(source='service_type.name', read_only=True)
    business_type_name = serializers.CharField(source='business_type.name', read_only=True)
    service_profession_names = serializers.SerializerMethodField()
    
    # 嵌套序列化器
    team_members = ProjectTeamSerializer(many=True, read_only=True)
    milestones = ProjectMilestoneSerializer(many=True, read_only=True)
    documents = ProjectDocumentSerializer(many=True, read_only=True)
    drawing_submissions = ProjectDrawingSubmissionSerializer(many=True, read_only=True)
    
    # 计算字段
    progress_rate = serializers.SerializerMethodField()
    
    class Meta:
        model = Project
        fields = '__all__'
        read_only_fields = ['project_number', 'created_time', 'updated_time']
    
    def get_progress_rate(self, obj):
        completed_milestones = obj.milestones.filter(is_completed=True).count()
        total_milestones = obj.milestones.count()
        return int((completed_milestones / total_milestones * 100) if total_milestones > 0 else 0)

    def get_service_profession_names(self, obj):
        return list(obj.service_professions.values_list('name', flat=True))

class ProjectCreateSerializer(serializers.ModelSerializer):
    service_professions = serializers.PrimaryKeyRelatedField(
        queryset=ServiceProfession.objects.all(),
        many=True,
        required=False,
        allow_empty=True,
    )

    class Meta:
        model = Project
        fields = [
            'name', 'alias', 'description',
            'service_type', 'business_type', 'design_stage', 'service_professions',
            'client_company_name', 'client_contact_person', 'client_phone',
            'client_email', 'client_address',
            'design_company', 'design_contact_person', 'design_phone', 'design_email',
        ]
    
    def create(self, validated_data):
        professions = validated_data.pop('service_professions', [])
        validated_data['created_by'] = self.context['request'].user
        validated_data['business_manager'] = self.context['request'].user
        validated_data['status'] = 'draft'
        project = super().create(validated_data)
        if professions:
            project.service_professions.set(professions)
        return project

class ProjectArchiveSerializer(serializers.ModelSerializer):
    archived_by_name = serializers.CharField(source='archived_by.get_full_name', read_only=True)
    project_name = serializers.CharField(source='project.name', read_only=True)
    
    class Meta:
        model = ProjectArchive
        fields = '__all__'
        read_only_fields = ['archive_number', 'archive_time', 'created_time']


class ProjectTeamNotificationSerializer(serializers.ModelSerializer):
    project_id = serializers.IntegerField(source='project.id', read_only=True)
    project_name = serializers.CharField(source='project.name', read_only=True)
    project_number = serializers.CharField(source='project.project_number', read_only=True)
    operator_name = serializers.CharField(source='operator.get_full_name', read_only=True)
    operator_username = serializers.CharField(source='operator.username', read_only=True)

    class Meta:
        model = ProjectTeamNotification
        fields = [
            'id',
            'title',
            'message',
            'category',
            'action_url',
            'is_read',
            'created_time',
            'read_time',
            'project_id',
            'project_name',
            'project_number',
            'operator_name',
            'operator_username',
            'context',
        ]
        read_only_fields = [
            'title',
            'message',
            'category',
            'action_url',
            'created_time',
            'read_time',
            'project_id',
            'project_name',
            'project_number',
            'operator_name',
            'operator_username',
            'context',
        ]
