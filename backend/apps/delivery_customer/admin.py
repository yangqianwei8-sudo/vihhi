from django.contrib import admin
from .models import DeliveryRecord, DeliveryFile, DeliveryFeedback, DeliveryTracking


@admin.register(DeliveryRecord)
class DeliveryRecordAdmin(admin.ModelAdmin):
    list_display = [
        'delivery_number', 'title', 'delivery_method', 'status', 
        'project', 'client', 'recipient_name', 'priority',
        'created_at', 'deadline', 'is_overdue', 'risk_level'
    ]
    list_filter = [
        'delivery_method', 'status', 'priority', 'is_overdue', 
        'risk_level', 'created_at', 'deadline'
    ]
    search_fields = ['delivery_number', 'title', 'recipient_name', 'recipient_email']
    readonly_fields = ['delivery_number', 'created_at', 'updated_at']
    fieldsets = (
        ('基本信息', {
            'fields': ('delivery_number', 'title', 'description', 'delivery_method')
        }),
        ('关联信息', {
            'fields': ('project', 'client')
        }),
        ('收件人信息', {
            'fields': ('recipient_name', 'recipient_phone', 'recipient_email', 'recipient_address')
        }),
        ('邮件信息', {
            'fields': ('email_subject', 'email_message', 'cc_emails', 'bcc_emails', 'use_template', 'template_name'),
            'classes': ('collapse',)
        }),
        ('快递信息', {
            'fields': ('express_company', 'express_number', 'express_fee'),
            'classes': ('collapse',)
        }),
        ('送达信息', {
            'fields': ('delivery_person', 'delivery_notes'),
            'classes': ('collapse',)
        }),
        ('状态信息', {
            'fields': ('status', 'priority', 'is_overdue', 'risk_level')
        }),
        ('时间信息', {
            'fields': ('deadline', 'scheduled_delivery_time', 'submitted_at', 
                      'sent_at', 'delivered_at', 'received_at', 'confirmed_at', 'archived_at')
        }),
        ('反馈信息', {
            'fields': ('feedback_received', 'feedback_content', 'feedback_time', 'feedback_by'),
            'classes': ('collapse',)
        }),
        ('归档信息', {
            'fields': ('auto_archive_enabled', 'archive_condition', 'archive_days'),
            'classes': ('collapse',)
        }),
        ('风险预警', {
            'fields': ('warning_sent', 'warning_times', 'overdue_days'),
            'classes': ('collapse',)
        }),
        ('操作信息', {
            'fields': ('created_by', 'sent_by', 'created_at', 'updated_at', 'notes')
        }),
    )


@admin.register(DeliveryFile)
class DeliveryFileAdmin(admin.ModelAdmin):
    list_display = ['file_name', 'delivery_record', 'file_type', 'file_size', 'uploaded_at', 'uploaded_by']
    list_filter = ['file_type', 'uploaded_at']
    search_fields = ['file_name', 'delivery_record__delivery_number']


@admin.register(DeliveryFeedback)
class DeliveryFeedbackAdmin(admin.ModelAdmin):
    list_display = ['delivery_record', 'feedback_type', 'feedback_by', 'created_at', 'is_read']
    list_filter = ['feedback_type', 'is_read', 'created_at']
    search_fields = ['delivery_record__delivery_number', 'feedback_by', 'content']


@admin.register(DeliveryTracking)
class DeliveryTrackingAdmin(admin.ModelAdmin):
    list_display = ['delivery_record', 'event_type', 'event_description', 'location', 'event_time', 'operator']
    list_filter = ['event_type', 'event_time']
    search_fields = ['delivery_record__delivery_number', 'event_description']
