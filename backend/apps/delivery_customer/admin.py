from django.contrib import admin
from backend.apps.delivery_customer.models import (
    # OutgoingDocumentStatusLog,  # 已从后台管理中移除
    # DeliveryRecord,  # 已从后台管理中移除
    # DeliveryFile,  # 已从后台管理中移除
    # DeliveryFeedback,  # 已从后台管理中移除
    # DeliveryTracking,  # 已从后台管理中移除
    ExpressCompany,
    # IncomingDocument,  # 已从后台管理中移除
    OutgoingDocument,
    DeliveryMethod,
    # OutgoingDocumentTracking  # 已从后台管理中移除
)
from backend.core.admin_base import BaseModelAdmin, AuditAdminMixin


# 交付记录已从后台管理中移除，请使用前端管理页面
# @admin.register(DeliveryRecord)
# class DeliveryRecordAdmin(AuditAdminMixin, BaseModelAdmin):
#     """交付记录管理"""
#     list_display = (
#         'delivery_number', 'title', 'delivery_method', 'status', 
#         'project', 'client', 'recipient_name', 'priority',
#         'created_at', 'deadline', 'is_overdue', 'risk_level'
#     )
#     list_filter = (
#         'delivery_method', 'status', 'priority', 'is_overdue', 
#         'risk_level', 'created_at', 'deadline'
#     )
#     search_fields = ('delivery_number', 'title', 'recipient_name', 'recipient_email')
#     readonly_fields = ('delivery_number', 'created_at', 'updated_at')
#     fieldsets = (
#         ('基本信息', {
#             'fields': ('delivery_number', 'title', 'description', 'delivery_method')
#         }),
#         ('关联信息', {
#             'fields': ('project', 'client')
#         }),
#         ('收件人信息', {
#             'fields': ('recipient_name', 'recipient_phone', 'recipient_email', 'recipient_address')
#         }),
#         ('邮件信息', {
#             'fields': ('email_subject', 'email_message', 'cc_emails', 'bcc_emails', 'use_template', 'template_name'),
#             'classes': ('collapse',)
#         }),
#         ('快递信息', {
#             'fields': ('express_company', 'express_number', 'express_fee'),
#             'classes': ('collapse',)
#         }),
#         ('送达信息', {
#             'fields': ('delivery_person', 'delivery_notes'),
#             'classes': ('collapse',)
#         }),
#         ('状态信息', {
#             'fields': ('status', 'priority', 'is_overdue', 'risk_level')
#         }),
#         ('时间信息', {
#             'fields': ('deadline', 'scheduled_delivery_time', 'submitted_at', 
#                       'sent_at', 'delivered_at', 'received_at', 'confirmed_at', 'archived_at')
#         }),
#         ('反馈信息', {
#             'fields': ('feedback_received', 'feedback_content', 'feedback_time', 'feedback_by'),
#             'classes': ('collapse',)
#         }),
#         ('归档信息', {
#             'fields': ('auto_archive_enabled', 'archive_condition', 'archive_days'),
#             'classes': ('collapse',)
#         }),
#         ('风险预警', {
#             'fields': ('warning_sent', 'warning_times', 'overdue_days'),
#             'classes': ('collapse',)
#         }),
#         ('操作信息', {
#             'fields': ('created_by', 'sent_by', 'notes')
#         }),
#         # 系统时间信息会自动添加
#     )


# 交付文件已从后台管理中移除，请使用前端管理页面
# @admin.register(DeliveryFile)
# class DeliveryFileAdmin(AuditAdminMixin, BaseModelAdmin):
#     """交付文件管理"""
#     list_display = ('file_name', 'delivery_record', 'file_type', 'file_size', 'uploaded_at', 'uploaded_by')
#     list_filter = ('file_type', 'uploaded_at')
#     search_fields = ('file_name', 'delivery_record__delivery_number')


# 交付反馈已从后台管理中移除，请使用前端管理页面
# @admin.register(DeliveryFeedback)
# class DeliveryFeedbackAdmin(BaseModelAdmin):
#     """交付反馈管理"""
#     list_display = ('delivery_record', 'feedback_type', 'feedback_by', 'created_at', 'is_read')
#     list_filter = ('feedback_type', 'is_read', 'created_at')
#     search_fields = ('delivery_record__delivery_number', 'feedback_by', 'content')


# 交付跟踪记录已从后台管理中移除，请使用前端管理页面
# @admin.register(DeliveryTracking)
# class DeliveryTrackingAdmin(BaseModelAdmin):
#     """交付跟踪管理"""
#     list_display = ('delivery_record', 'event_type', 'event_description', 'location', 'event_time', 'operator')
#     list_filter = ('event_type', 'event_time')
#     search_fields = ('delivery_record__delivery_number', 'event_description')


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
            'fields': ('contact_phone', 'contact_email', 'website'),
            'classes': ('collapse',)
        }),
        ('状态设置', {
            'fields': ('is_active', 'is_default')
        }),
        ('备注信息', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        ('系统信息', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
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


# 收文已从后台管理中移除，请使用前端管理页面
# @admin.register(IncomingDocument)
# class IncomingDocumentAdmin(AuditAdminMixin, BaseModelAdmin):
#     """收文管理"""
#     list_display = ('document_number', 'title', 'sender', 'receive_date', 'status', 'priority', 'handler', 'created_at')
#     list_filter = ('status', 'priority', 'receive_date', 'created_at')
#     search_fields = ('document_number', 'title', 'sender', 'sender_contact')
#     readonly_fields = ('document_number', 'created_at', 'updated_at')
#     fieldsets = (
#         ('基本信息', {
#             'fields': ('document_number', 'title', 'sender', 'sender_contact', 'sender_phone')
#         }),
#         ('文件信息', {
#             'fields': ('document_date', 'receive_date', 'document_type')
#         }),
#         ('内容', {
#             'fields': ('content', 'summary')
#         }),
#         ('状态和优先级', {
#             'fields': ('status', 'priority')
#         }),
#         ('处理信息', {
#             'fields': ('handler', 'handle_notes', 'completed_at')
#         }),
#         ('附件', {
#             'fields': ('attachment',)
#         }),
#         ('备注', {
#             'fields': ('notes',)
#         }),
#         ('操作信息', {
#             'fields': ('created_by',)
#         }),
#         # 时间信息会自动添加
#     )


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


# 发文状态流转日志已从后台管理中移除，请使用前端管理页面
# @admin.register(OutgoingDocumentStatusLog)
# class OutgoingDocumentStatusLogAdmin(BaseModelAdmin):
#     """发文状态流转日志管理"""
#     list_display = ('document', 'from_status_display', 'to_status_display', 'actor', 'created_at')
#     list_filter = ('to_status', 'created_at')
#     search_fields = ('document__document_number', 'document__title', 'comment')
#     readonly_fields = ('document', 'from_status', 'to_status', 'actor', 'comment', 'created_at')
#     
#     def from_status_display(self, obj):
#         if obj.from_status:
#             return dict(OutgoingDocument.STATUS_CHOICES).get(obj.from_status, obj.from_status)
#         return '初始'
#     from_status_display.short_description = '原状态'
#     
#     def to_status_display(self, obj):
#         return dict(OutgoingDocument.STATUS_CHOICES).get(obj.to_status, obj.to_status)
#     to_status_display.short_description = '目标状态'
#     
#     fieldsets = (
#         ('基本信息', {
#             'fields': ('document', 'from_status', 'to_status', 'actor', 'created_at')
#         }),
#         ('备注', {
#             'fields': ('comment',)
#         }),
#     )
#     
#     def has_add_permission(self, request):
#         return False  # 禁止手动添加，只能通过状态流转自动创建
#     
#     def has_change_permission(self, request, obj=None):
#         return False  # 禁止修改，日志只读


@admin.register(DeliveryMethod)
class DeliveryMethodAdmin(AuditAdminMixin, BaseModelAdmin):
    """报送方式管理"""
    list_display = ('name', 'code', 'sort_order', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'code', 'description')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('基本信息', {
            'fields': ('name', 'code', 'description')
        }),
        ('设置', {
            'fields': ('sort_order', 'is_active')
        }),
        ('操作信息', {
            'fields': ('created_by',)
        }),
        # 时间信息会自动添加
    )


# 发文跟踪记录已从后台管理中移除，请使用前端管理页面
# @admin.register(OutgoingDocumentTracking)
# class OutgoingDocumentTrackingAdmin(AuditAdminMixin, BaseModelAdmin):
#     """发文跟踪记录管理"""
#     list_display = (
#         'document', 'delivery_method', 'status', 'sent_at', 
#         'received_at', 'confirmed_at', 'created_at'
#     )
#     list_filter = (
#         'delivery_method', 'status', 'created_at', 'sent_at'
#     )
#     search_fields = (
#         'document__document_number', 'document__title', 
#         'express_number', 'email_to', 'email_message_id'
#     )
#     readonly_fields = ('created_at', 'updated_at')
#     fieldsets = (
#         ('基本信息', {
#             'fields': ('document', 'delivery_method', 'status')
#         }),
#         ('邮件信息', {
#             'fields': (
#                 'email_subject', 'email_to', 'email_sent_at', 
#                 'email_read_at', 'email_tracking_id', 'email_message_id'
#             ),
#             'classes': ('collapse',)
#         }),
#         ('快递信息', {
#             'fields': (
#                 'express_company', 'express_number', 'express_status',
#                 'express_last_update', 'express_tracking_data'
#             ),
#             'classes': ('collapse',)
#         }),
#         ('现场送达信息', {
#             'fields': (
#                 'hand_delivery_location', 'hand_delivery_latitude', 
#                 'hand_delivery_longitude', 'hand_delivery_photo',
#                 'hand_delivery_checkin_at', 'hand_delivery_checkin_by'
#             ),
#             'classes': ('collapse',)
#         }),
#         ('易签宝信息', {
#             'fields': (
#                 'yisign_contract_id', 'yisign_contract_url', 'yisign_status',
#                 'yisign_signed_at', 'yisign_signed_by', 'yisign_callback_data'
#             ),
#             'classes': ('collapse',)
#         }),
#         ('时间信息', {
#             'fields': ('sent_at', 'received_at', 'confirmed_at', 'completed_at')
#         }),
#         ('异常信息', {
#             'fields': ('error_message', 'retry_count', 'last_retry_at'),
#             'classes': ('collapse',)
#         }),
#         ('其他', {
#             'fields': ('notes', 'created_by', 'created_at', 'updated_at')
#         }),
#     )
