from django.contrib import admin
from backend.apps.delivery_customer.models import (
    DeliveryRecord, DeliveryFile, DeliveryFeedback, DeliveryTracking, 
    ExpressCompany, IncomingDocument, OutgoingDocument
)
from backend.core.admin_base import BaseModelAdmin, AuditAdminMixin


@admin.register(DeliveryRecord)
class DeliveryRecordAdmin(AuditAdminMixin, BaseModelAdmin):
    """交付记录管理"""
    list_display = (
        'delivery_number', 'title', 'delivery_method', 'status', 
        'project', 'client', 'recipient_name', 'priority',
        'created_at', 'deadline', 'is_overdue', 'risk_level'
    )
    list_filter = (
        'delivery_method', 'status', 'priority', 'is_overdue', 
        'risk_level', 'created_at', 'deadline'
    )
    search_fields = ('delivery_number', 'title', 'recipient_name', 'recipient_email')
    readonly_fields = ('delivery_number', 'created_at', 'updated_at')
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
            'fields': ('created_by', 'sent_by', 'notes')
        }),
        # 系统时间信息会自动添加
    )


@admin.register(DeliveryFile)
class DeliveryFileAdmin(AuditAdminMixin, BaseModelAdmin):
    """交付文件管理"""
    list_display = ('file_name', 'delivery_record', 'file_type', 'file_size', 'uploaded_at', 'uploaded_by')
    list_filter = ('file_type', 'uploaded_at')
    search_fields = ('file_name', 'delivery_record__delivery_number')


@admin.register(DeliveryFeedback)
class DeliveryFeedbackAdmin(BaseModelAdmin):
    """交付反馈管理"""
    list_display = ('delivery_record', 'feedback_type', 'feedback_by', 'created_at', 'is_read')
    list_filter = ('feedback_type', 'is_read', 'created_at')
    search_fields = ('delivery_record__delivery_number', 'feedback_by', 'content')


@admin.register(DeliveryTracking)
class DeliveryTrackingAdmin(BaseModelAdmin):
    """交付跟踪管理"""
    list_display = ('delivery_record', 'event_type', 'event_description', 'location', 'event_time', 'operator')
    list_filter = ('event_type', 'event_time')
    search_fields = ('delivery_record__delivery_number', 'event_description')


@admin.register(ExpressCompany)
class ExpressCompanyAdmin(AuditAdminMixin, BaseModelAdmin):
    """快递公司管理"""
    list_display = ('name', 'code', 'is_active', 'is_default', 'sort_order', 'contact_phone', 'created_at')
    list_filter = ('is_active', 'is_default', 'created_at')
    search_fields = ('name', 'code', 'alias', 'contact_phone')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('基本信息', {
            'fields': ('name', 'code', 'alias', 'sort_order')
        }),
        ('联系方式', {
            'fields': ('contact_phone', 'contact_email', 'website')
        }),
        ('设置', {
            'fields': ('is_active', 'is_default')
        }),
        ('备注', {
            'fields': ('notes',)
        }),
        ('操作信息', {
            'fields': ('created_by',)
        }),
        # 时间信息会自动添加
    )


@admin.register(IncomingDocument)
class IncomingDocumentAdmin(AuditAdminMixin, BaseModelAdmin):
    """收文管理"""
    list_display = ('document_number', 'title', 'sender', 'receive_date', 'status', 'priority', 'handler', 'created_at')
    list_filter = ('status', 'priority', 'receive_date', 'created_at')
    search_fields = ('document_number', 'title', 'sender', 'sender_contact')
    readonly_fields = ('document_number', 'created_at', 'updated_at')
    fieldsets = (
        ('基本信息', {
            'fields': ('document_number', 'title', 'sender', 'sender_contact', 'sender_phone')
        }),
        ('文件信息', {
            'fields': ('document_date', 'receive_date', 'document_type')
        }),
        ('内容', {
            'fields': ('content', 'summary')
        }),
        ('状态和优先级', {
            'fields': ('status', 'priority')
        }),
        ('处理信息', {
            'fields': ('handler', 'handle_notes', 'completed_at')
        }),
        ('附件', {
            'fields': ('attachment',)
        }),
        ('备注', {
            'fields': ('notes',)
        }),
        ('操作信息', {
            'fields': ('created_by',)
        }),
        # 时间信息会自动添加
    )


@admin.register(OutgoingDocument)
class OutgoingDocumentAdmin(AuditAdminMixin, BaseModelAdmin):
    """发文管理"""
    list_display = ('document_number', 'title', 'recipient', 'send_date', 'status', 'priority', 'reviewer', 'created_at')
    list_filter = ('status', 'priority', 'send_date', 'created_at')
    search_fields = ('document_number', 'title', 'recipient', 'recipient_contact')
    readonly_fields = ('document_number', 'created_at', 'updated_at')
    fieldsets = (
        ('基本信息', {
            'fields': ('document_number', 'title', 'recipient', 'recipient_contact', 'recipient_phone', 'recipient_address')
        }),
        ('文件信息', {
            'fields': ('document_date', 'send_date', 'document_type')
        }),
        ('内容', {
            'fields': ('content', 'summary')
        }),
        ('状态和优先级', {
            'fields': ('status', 'priority')
        }),
        ('审核信息', {
            'fields': ('reviewer', 'review_notes', 'reviewed_at')
        }),
        ('发送信息', {
            'fields': ('sender', 'send_method', 'sent_at')
        }),
        ('附件', {
            'fields': ('attachment',)
        }),
        ('备注', {
            'fields': ('notes',)
        }),
        ('操作信息', {
            'fields': ('created_by',)
        }),
        # 时间信息会自动添加
    )
