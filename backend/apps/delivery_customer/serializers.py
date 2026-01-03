from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import DeliveryRecord, DeliveryFile, DeliveryFeedback, DeliveryTracking

User = get_user_model()


class DeliveryFileSerializer(serializers.ModelSerializer):
    """交付文件序列化器"""
    file_size_display = serializers.SerializerMethodField()
    uploaded_by_name = serializers.SerializerMethodField()
    
    class Meta:
        model = DeliveryFile
        fields = [
            'id', 'file', 'file_name', 'file_type', 'file_size', 
            'file_size_display', 'file_extension', 'description', 
            'version', 'uploaded_at', 'uploaded_by', 'uploaded_by_name'
        ]
        read_only_fields = ['file_size', 'file_extension', 'uploaded_at']
    
    def get_file_size_display(self, obj):
        return obj.get_file_size_display()
    
    def get_uploaded_by_name(self, obj):
        return obj.uploaded_by.get_full_name() if obj.uploaded_by else ''


class DeliveryTrackingSerializer(serializers.ModelSerializer):
    """交付跟踪序列化器"""
    operator_name = serializers.SerializerMethodField()
    
    class Meta:
        model = DeliveryTracking
        fields = [
            'id', 'event_type', 'event_description', 'location',
            'event_time', 'operator', 'operator_name', 'notes'
        ]
        read_only_fields = ['event_time']
    
    def get_operator_name(self, obj):
        return obj.operator.get_full_name() if obj.operator else ''


class DeliveryFeedbackSerializer(serializers.ModelSerializer):
    """交付反馈序列化器"""
    
    class Meta:
        model = DeliveryFeedback
        fields = [
            'id', 'feedback_type', 'content', 'feedback_by',
            'feedback_email', 'feedback_phone', 'created_at',
            'is_read', 'read_at', 'read_by'
        ]
        read_only_fields = ['created_at']


class DeliveryRecordListSerializer(serializers.ModelSerializer):
    """交付记录列表序列化器"""
    project_name = serializers.SerializerMethodField()
    project_number = serializers.SerializerMethodField()
    client_name = serializers.SerializerMethodField()
    created_by_name = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    delivery_method_display = serializers.CharField(source='get_delivery_method_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    risk_level_display = serializers.CharField(source='get_risk_level_display', read_only=True)
    
    class Meta:
        model = DeliveryRecord
        fields = [
            'id', 'delivery_number', 'title', 'delivery_method', 
            'delivery_method_display', 'status', 'status_display',
            'priority', 'priority_display', 'project', 'project_name',
            'project_number', 'client', 'client_name', 'recipient_name',
            'recipient_email', 'created_by', 'created_by_name',
            'created_at', 'deadline', 'is_overdue', 'risk_level',
            'risk_level_display', 'overdue_days', 'file_count',
            'total_file_size'
        ]
    
    def get_project_name(self, obj):
        return obj.project.name if obj.project else ''
    
    def get_project_number(self, obj):
        return obj.project.project_number if obj.project else ''
    
    def get_client_name(self, obj):
        return obj.client.name if obj.client else ''
    
    def get_created_by_name(self, obj):
        return obj.created_by.get_full_name() if obj.created_by else ''


class DeliveryRecordDetailSerializer(serializers.ModelSerializer):
    """交付记录详情序列化器"""
    project_name = serializers.SerializerMethodField()
    project_number = serializers.SerializerMethodField()
    client_name = serializers.SerializerMethodField()
    created_by_name = serializers.SerializerMethodField()
    sent_by_name = serializers.SerializerMethodField()
    delivery_person_name = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    delivery_method_display = serializers.CharField(source='get_delivery_method_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    risk_level_display = serializers.CharField(source='get_risk_level_display', read_only=True)
    
    files = DeliveryFileSerializer(many=True, read_only=True)
    tracking_records = DeliveryTrackingSerializer(many=True, read_only=True)
    feedbacks = DeliveryFeedbackSerializer(many=True, read_only=True)
    
    class Meta:
        model = DeliveryRecord
        fields = '__all__'
        read_only_fields = [
            'delivery_number', 'created_at', 'updated_at',
            'file_count', 'total_file_size'
        ]
    
    def get_project_name(self, obj):
        return obj.project.name if obj.project else ''
    
    def get_project_number(self, obj):
        return obj.project.project_number if obj.project else ''
    
    def get_client_name(self, obj):
        return obj.client.name if obj.client else ''
    
    def get_created_by_name(self, obj):
        return obj.created_by.get_full_name() if obj.created_by else ''
    
    def get_sent_by_name(self, obj):
        return obj.sent_by.get_full_name() if obj.sent_by else ''
    
    def get_delivery_person_name(self, obj):
        return obj.delivery_person.get_full_name() if obj.delivery_person else ''


class DeliveryRecordCreateSerializer(serializers.ModelSerializer):
    """创建交付记录序列化器"""
    
    class Meta:
        model = DeliveryRecord
        fields = [
            'title', 'description', 'delivery_method', 'project', 'client',
            'recipient_name', 'recipient_phone', 'recipient_email', 'recipient_address',
            'cc_emails', 'bcc_emails', 'email_subject', 'email_message',
            'use_template', 'template_name', 'express_company', 'express_number',
            'express_fee', 'delivery_person', 'delivery_notes',
            'priority', 'scheduled_delivery_time', 'deadline',
            'auto_archive_enabled', 'archive_condition', 'archive_days', 'notes'
        ]
    
    def validate(self, data):
        """验证业务规则"""
        delivery_method = data.get('delivery_method')
        
        # 邮件交付方式必须填写收件人邮箱
        if delivery_method == 'email':
            recipient_email = data.get('recipient_email', '')
            if not recipient_email or not recipient_email.strip():
                raise serializers.ValidationError({
                    'recipient_email': '邮件交付方式必须填写收件人邮箱'
                })
        
        # 验证收件人姓名必填
        recipient_name = data.get('recipient_name', '')
        if not recipient_name or not recipient_name.strip():
            raise serializers.ValidationError({
                'recipient_name': '收件人姓名不能为空'
            })
        
        # 验证标题必填
        title = data.get('title', '')
        if not title or not title.strip():
            raise serializers.ValidationError({
                'title': '交付标题不能为空'
            })
        
        # 验证时间逻辑：计划交付时间不能晚于交付期限
        scheduled_delivery_time = data.get('scheduled_delivery_time')
        deadline = data.get('deadline')
        if scheduled_delivery_time and deadline:
            if scheduled_delivery_time > deadline:
                raise serializers.ValidationError({
                    'deadline': '交付期限不能早于计划交付时间'
                })
        
        return data
    
    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        validated_data['status'] = 'draft'
        return super().create(validated_data)
