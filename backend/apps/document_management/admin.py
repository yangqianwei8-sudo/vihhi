from django.contrib import admin
from backend.core.admin_base import BaseModelAdmin
from .models import (
    IncomingDocument,
    OutgoingDocument,
    FileCategory,
    FileTemplate,
)

# ==================== 文档管理 ====================

@admin.register(IncomingDocument)
class IncomingDocumentAdmin(BaseModelAdmin):
    """收文管理"""
    list_display = (
        'document_number', 'title', 'sender', 'receive_date',
        'status', 'priority', 'handler', 'created_at'
    )
    list_filter = ('status', 'priority', 'stage', 'receive_date', 'created_at')
    search_fields = ('document_number', 'title', 'sender', 'sender_contact', 'content', 'summary')
    ordering = ('-receive_date', '-created_at')
    raw_id_fields = ('handler', 'created_by', 'file_category')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'receive_date'
    fieldsets = (
        ('基本信息', {
            'fields': ('document_number', 'title', 'sender', 'sender_contact', 'sender_phone')
        }),
        ('文件信息', {
            'fields': ('document_date', 'receive_date', 'document_type', 'file_category', 'stage')
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
        ('附件和备注', {
            'fields': ('attachment', 'notes')
        }),
        ('系统信息', {
            'fields': ('created_by', 'created_at', 'updated_at')
        }),
    )

@admin.register(OutgoingDocument)
class OutgoingDocumentAdmin(BaseModelAdmin):
    """发文管理"""
    list_display = (
        'document_number', 'title', 'recipient', 'send_date',
        'status', 'priority', 'reviewer', 'created_at'
    )
    list_filter = ('status', 'priority', 'stage', 'send_date', 'created_at')
    search_fields = ('document_number', 'title', 'recipient', 'recipient_contact', 'content', 'summary')
    ordering = ('-send_date', '-created_at')
    raw_id_fields = ('project', 'client', 'client_contact', 'reviewer', 'sender', 'created_by', 'file_category')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'send_date'
    fieldsets = (
        ('基本信息', {
            'fields': ('document_number', 'title', 'project', 'client', 'client_contact')
        }),
        ('收文单位信息', {
            'fields': ('recipient', 'recipient_contact', 'recipient_phone', 'recipient_email', 'recipient_address')
        }),
        ('文件信息', {
            'fields': ('document_date', 'send_date', 'document_type', 'file_category', 'stage')
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
            'fields': ('sender', 'send_method', 'delivery_methods', 'sent_at')
        }),
        ('附件和备注', {
            'fields': ('attachment', 'notes')
        }),
        ('系统信息', {
            'fields': ('created_by', 'created_at', 'updated_at')
        }),
    )

@admin.register(FileCategory)
class FileCategoryAdmin(BaseModelAdmin):
    """文件分类管理"""
    list_display = (
        'name', 'code', 'stage', 'sort_order', 'is_active', 'created_at'
    )
    list_filter = ('stage', 'is_active', 'created_at')
    search_fields = ('name', 'code', 'description')
    ordering = ('stage', 'sort_order', 'name')
    raw_id_fields = ('created_by',)
    readonly_fields = ('created_at', 'updated_at')

@admin.register(FileTemplate)
class FileTemplateAdmin(BaseModelAdmin):
    """文件模板管理"""
    list_display = (
        'name', 'code', 'stage', 'category', 'sort_order', 'is_active', 'created_at'
    )
    list_filter = ('stage', 'is_active', 'category', 'created_at')
    search_fields = ('name', 'code', 'description')
    ordering = ('stage', 'sort_order', 'name')
    raw_id_fields = ('category', 'created_by')
    readonly_fields = ('created_at', 'updated_at')
