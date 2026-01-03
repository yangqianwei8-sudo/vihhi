from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.db import models
from backend.apps.workflow_engine.models import (
    WorkflowTemplate, ApprovalNode, ApprovalInstance, ApprovalRecord,
    AgentConversation, AgentMessage
)
from backend.core.admin_base import BaseModelAdmin, AuditAdminMixin


@admin.register(WorkflowTemplate)
class WorkflowTemplateAdmin(AuditAdminMixin, BaseModelAdmin):
    """工作流模板管理"""
    list_display = ('name', 'code', 'category', 'status', 'created_by', 'created_time')
    list_filter = ('status', 'category', 'created_time')
    search_fields = ('name', 'code', 'description')
    readonly_fields = ('created_time', 'updated_time')
    fieldsets = (
        ('基本信息', {
            'fields': ('name', 'code', 'description', 'category', 'status')
        }),
        ('流程配置', {
            'fields': ('allow_withdraw', 'allow_reject', 'allow_transfer', 'timeout_hours', 'timeout_action')
        }),
        ('审计信息', {
            'fields': ('created_by',)
        }),
        # 时间信息会自动添加
    )


@admin.register(ApprovalNode)
class ApprovalNodeAdmin(BaseModelAdmin):
    """审批节点管理"""
    list_display = ('name', 'workflow', 'node_type', 'sequence', 'approver_type', 'approval_mode')
    list_filter = ('node_type', 'approver_type', 'approval_mode', 'workflow')
    search_fields = ('name', 'workflow__name')
    filter_horizontal = ('approver_users', 'approver_roles', 'approver_departments')
    raw_id_fields = ['workflow']
    fieldsets = (
        ('基本信息', {
            'fields': ('workflow', 'name', 'node_type', 'sequence', 'description')
        }),
        ('审批人配置', {
            'fields': ('approver_type', 'approver_users', 'approver_roles', 'approver_departments', 'approval_mode')
        }),
        ('节点配置', {
            'fields': ('is_required', 'can_reject', 'can_transfer', 'timeout_hours')
        }),
        ('条件配置', {
            'fields': ('condition_expression',),
            'classes': ('collapse',)
        }),
    )


@admin.register(ApprovalInstance)
class ApprovalInstanceAdmin(BaseModelAdmin):
    """审批实例管理（保留所有自定义逻辑）"""
    list_display = ('instance_number', 'workflow', 'status', 'applicant', 'content_object_link_display', 'approval_actions', 'created_time')
    list_filter = ('status', 'workflow', 'created_time')
    search_fields = ('instance_number', 'applicant__username')
    readonly_fields = ('instance_number', 'created_time', 'updated_time', 'content_object_link', 'approval_records_display')
    raw_id_fields = ['workflow', 'current_node', 'applicant', 'content_type']
    actions = ['approve_selected', 'reject_selected']
    
    def has_view_permission(self, request, obj=None):
        """检查用户是否有查看权限"""
        # 超级用户和员工都可以查看
        if request.user.is_superuser or request.user.is_staff:
            return True
        # 如果是审批人，也可以查看
        if obj:
            return obj.records.filter(approver=request.user).exists()
        return True
    
    def has_change_permission(self, request, obj=None):
        """检查用户是否有修改权限"""
        # 超级用户和员工都可以修改
        if request.user.is_superuser or request.user.is_staff:
            return True
        # 如果是待审批状态的审批人，也可以修改（进行审批操作）
        if obj and obj.status == 'pending':
            return obj.records.filter(approver=request.user, result='pending').exists()
        return False
    
    def get_queryset(self, request):
        """自定义查询集，普通用户只能看到自己相关的审批"""
        qs = super().get_queryset(request)
        # 超级用户可以看到所有
        if request.user.is_superuser:
            return qs
        # 普通员工可以看到所有（因为is_staff=True）
        if request.user.is_staff:
            return qs
        # 其他用户只能看到自己作为审批人或申请人的
        return qs.filter(
            models.Q(applicant=request.user) |
            models.Q(records__approver=request.user)
        ).distinct()
    fieldsets = (
        ('基本信息', {
            'fields': ('instance_number', 'workflow', 'status', 'current_node')
        }),
        ('关联对象', {
            'fields': ('content_type', 'object_id', 'content_object_link'),
            'description': '关联对象用于将审批流程与具体的业务对象（如合同、商机等）关联起来。通常不需要手动填写，审批流程会在业务代码中自动创建并关联。'
        }),
        ('申请信息', {
            'fields': ('applicant', 'apply_time', 'apply_comment')
        }),
        ('审批记录', {
            'fields': ('approval_records_display',),
            'classes': ('collapse',)
        }),
        ('完成信息', {
            'fields': ('completed_time', 'final_comment')
        }),
        # 时间信息会自动添加
    )
    
    def get_form(self, request, obj=None, **kwargs):
        """自定义表单，为字段添加帮助文本"""
        form = super().get_form(request, obj, **kwargs)
        
        # 为 content_type 字段添加详细的帮助文本
        if 'content_type' in form.base_fields:
            form.base_fields['content_type'].help_text = format_html(
                '<div style="margin-top: 6px; padding: 10px; background: #f0f7ff; border-left: 3px solid #2196F3; border-radius: 3px; font-size: 13px;">'
                '<strong style="color: #1976d2;">📌 填写说明：</strong><br>'
                '选择要关联的业务对象类型，例如：<br>'
                '• <code>businesscontract</code> - 合同<br>'
                '• <code>businessopportunity</code> - 商机<br>'
                '• <code>project</code> - 项目<br>'
                '<small style="color: #666; margin-top: 4px; display: block;">💡 提示：通常不需要手动填写，审批流程会在业务代码中自动创建并关联。</small>'
                '</div>'
            )
        
        # 为 object_id 字段添加详细的帮助文本
        if 'object_id' in form.base_fields:
            form.base_fields['object_id'].help_text = format_html(
                '<div style="margin-top: 6px; padding: 10px; background: #f0f7ff; border-left: 3px solid #2196F3; border-radius: 3px; font-size: 13px;">'
                '<strong style="color: #1976d2;">📌 填写说明：</strong><br>'
                '填写该业务对象的具体ID，例如：<br>'
                '• 合同ID为 <code>123</code>，则填写 <code>123</code><br>'
                '• 商机ID为 <code>456</code>，则填写 <code>456</code><br>'
                '<small style="color: #666; margin-top: 4px; display: block;">💡 提示：可以在业务对象的详情页或列表页找到ID。如果已填写关联对象类型，下方会显示当前关联对象的链接。</small>'
                '</div>'
            )
        
        return form
    
    def content_object_link(self, obj):
        """显示关联对象的链接（在编辑页面，显示在字段下方）"""
        if obj.content_type and obj.object_id:
            try:
                content_obj = obj.content_type.get_object_for_this_type(id=obj.object_id)
                model_name = obj.content_type.model
                obj_str = str(content_obj)
                
                # 尝试生成链接（根据不同的模型类型）
                admin_url = None
                
                # businesscontract已从后台管理中移除
                # if model_name == 'businesscontract':
                #     try:
                #         admin_url = reverse('admin:customer_success_businesscontract_change', args=[obj.object_id])
                #     except:
                #         pass
                if model_name == 'businessopportunity':
                    try:
                        admin_url = reverse('admin:customer_success_businessopportunity_change', args=[obj.object_id])
                    except:
                        pass
                elif model_name == 'project':
                    try:
                        admin_url = reverse('admin:production_management_project_change', args=[obj.object_id])
                    except:
                        pass
                
                if admin_url:
                    return format_html(
                        '<div style="margin-top: 10px; padding: 12px; background: #e8f5e9; border-left: 4px solid #4caf50; border-radius: 4px;">'
                        '<strong style="color: #2e7d32;">✅ 当前关联对象：</strong><br>'
                        '<a href="{}" target="_blank" style="color: #1976d2; text-decoration: none; font-weight: 500; margin-top: 6px; display: inline-block;">'
                        '🔗 {}: {} (ID: {})</a>'
                        '<br><small style="color: #666; margin-top: 4px; display: block;">点击链接可跳转到该对象的详情页</small>'
                        '</div>',
                        admin_url, model_name, obj_str, obj.object_id
                    )
                else:
                    return format_html(
                        '<div style="margin-top: 10px; padding: 12px; background: #f5f5f5; border-left: 4px solid #9e9e9e; border-radius: 4px;">'
                        '<strong style="color: #616161;">当前关联对象：</strong><br>'
                        '<span style="color: #424242; margin-top: 6px; display: inline-block;">{}: {} (ID: {})</span>'
                        '</div>',
                        model_name, obj_str, obj.object_id
                    )
            except Exception as e:
                return format_html(
                    '<div style="margin-top: 10px; padding: 12px; background: #ffebee; border-left: 4px solid #f44336; border-radius: 4px;">'
                    '<strong style="color: #c62828;">⚠️ 关联对象不存在：</strong><br>'
                    '<span style="color: #c62828; margin-top: 6px; display: inline-block;">{} (ID: {}) - 对象可能已被删除</span>'
                    '</div>',
                    obj.content_type.model, obj.object_id
                )
        return format_html(
            '<div style="margin-top: 10px; padding: 12px; background: #fff3e0; border-left: 4px solid #ff9800; border-radius: 4px;">'
            '<strong style="color: #e65100;">ℹ️ 未关联对象</strong><br>'
            '<span style="color: #e65100; margin-top: 6px; display: inline-block;">请填写上方的"关联对象类型"和"关联对象ID"字段</span>'
            '</div>'
        )
    content_object_link.short_description = '关联对象预览'
    
    def content_object_link_display(self, obj):
        """在列表页显示关联对象（可点击链接）"""
        if obj.content_type and obj.object_id:
            try:
                content_obj = obj.content_type.get_object_for_this_type(id=obj.object_id)
                model_name = obj.content_type.model
                obj_str = str(content_obj)[:30]
                
                # 尝试生成链接
                admin_url = None
                
                # businesscontract已从后台管理中移除
                # if model_name == 'businesscontract':
                #     try:
                #         admin_url = reverse('admin:customer_success_businesscontract_change', args=[obj.object_id])
                #     except:
                #         pass
                if model_name == 'businessopportunity':
                    try:
                        admin_url = reverse('admin:customer_success_businessopportunity_change', args=[obj.object_id])
                    except:
                        pass
                elif model_name == 'project':
                    try:
                        admin_url = reverse('admin:production_management_project_change', args=[obj.object_id])
                    except:
                        pass
                
                if admin_url:
                    return format_html(
                        '<a href="{}" target="_blank" style="color: #1976d2; text-decoration: none;">'
                        '🔗 {}: {}</a>',
                        admin_url, model_name, obj_str
                    )
                else:
                    return f"{model_name}: {obj_str}"
            except:
                return f"{obj.content_type.model} (ID: {obj.object_id})"
        return "-"
    content_object_link_display.short_description = '关联对象'
    
    def approval_actions(self, obj):
        """在列表页显示审批操作按钮"""
        if obj.status == 'pending':
            from django.urls import reverse
            approve_url = reverse('admin:workflow_engine_approvalinstance_approve', args=[obj.pk])
            reject_url = reverse('admin:workflow_engine_approvalinstance_reject', args=[obj.pk])
            return format_html(
                '<a href="{}" class="button" style="background: #4caf50; color: white; padding: 4px 8px; text-decoration: none; border-radius: 3px; margin-right: 4px;">通过</a>'
                '<a href="{}" class="button" style="background: #f44336; color: white; padding: 4px 8px; text-decoration: none; border-radius: 3px;">驳回</a>',
                approve_url, reject_url
            )
        return '-'
    approval_actions.short_description = '审批操作'
    
    def approval_records_display(self, obj):
        """在详情页显示审批记录"""
        if not obj:
            return '-'
        
        records = obj.records.all().order_by('approval_time')
        if not records.exists():
            return format_html('<p>暂无审批记录</p>')
        
        html = '<div style="margin-top: 10px;">'
        html += '<h4 style="margin-bottom: 10px;">审批记录</h4>'
        html += '<table style="width: 100%; border-collapse: collapse;">'
        html += '<thead><tr style="background: #f5f5f5;"><th style="padding: 8px; border: 1px solid #ddd;">节点</th><th style="padding: 8px; border: 1px solid #ddd;">审批人</th><th style="padding: 8px; border: 1px solid #ddd;">结果</th><th style="padding: 8px; border: 1px solid #ddd;">意见</th><th style="padding: 8px; border: 1px solid #ddd;">时间</th></tr></thead>'
        html += '<tbody>'
        
        for record in records:
            result_color = {
                'approved': '#4caf50',
                'rejected': '#f44336',
                'pending': '#ff9800',
                'transferred': '#2196f3',
                'withdrawn': '#9e9e9e'
            }.get(record.result, '#9e9e9e')
            
            html += f'<tr>'
            html += f'<td style="padding: 8px; border: 1px solid #ddd;">{record.node.name}</td>'
            html += f'<td style="padding: 8px; border: 1px solid #ddd;">{record.approver.username}</td>'
            html += f'<td style="padding: 8px; border: 1px solid #ddd;"><span style="color: {result_color}; font-weight: bold;">{record.get_result_display()}</span></td>'
            html += f'<td style="padding: 8px; border: 1px solid #ddd;">{record.comment or "-"}</td>'
            html += f'<td style="padding: 8px; border: 1px solid #ddd;">{record.approval_time.strftime("%Y-%m-%d %H:%M") if record.approval_time else "-"}</td>'
            html += f'</tr>'
        
        html += '</tbody></table></div>'
        return format_html(html)
    approval_records_display.short_description = '审批记录'
    
    def get_urls(self):
        """添加自定义URL"""
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path('<int:instance_id>/approve/', self.admin_site.admin_view(self.approve_instance), name='workflow_engine_approvalinstance_approve'),
            path('<int:instance_id>/reject/', self.admin_site.admin_view(self.reject_instance), name='workflow_engine_approvalinstance_reject'),
        ]
        return custom_urls + urls
    
    def approve_instance(self, request, instance_id):
        """审批通过"""
        from django.shortcuts import get_object_or_404, redirect
        from django.contrib import messages
        from .services import ApprovalEngine
        
        instance = get_object_or_404(ApprovalInstance, id=instance_id)
        
        if request.method == 'POST':
            comment = request.POST.get('comment', '')
            success = ApprovalEngine.approve(
                instance=instance,
                approver=request.user,
                result='approved',
                comment=comment
            )
            if success:
                messages.success(request, '审批已通过')
            else:
                messages.error(request, '审批操作失败')
            return redirect('admin:workflow_engine_approvalinstance_changelist')
        
        # GET请求，显示确认页面
        from django.template.response import TemplateResponse
        context = {
            **self.admin_site.each_context(request),
            'title': '审批通过',
            'instance': instance,
            'opts': self.model._meta,
            'has_view_permission': self.has_view_permission(request, instance),
        }
        return TemplateResponse(request, 'admin/workflow_engine/approvalinstance/approve.html', context)
    
    def reject_instance(self, request, instance_id):
        """审批驳回"""
        from django.shortcuts import get_object_or_404, redirect
        from django.contrib import messages
        from .services import ApprovalEngine
        
        instance = get_object_or_404(ApprovalInstance, id=instance_id)
        
        if request.method == 'POST':
            comment = request.POST.get('comment', '')
            if not comment:
                messages.error(request, '驳回时必须填写审批意见')
                return redirect('admin:workflow_engine_approvalinstance_change', instance_id)
            
            success = ApprovalEngine.approve(
                instance=instance,
                approver=request.user,
                result='rejected',
                comment=comment
            )
            if success:
                messages.success(request, '审批已驳回')
            else:
                messages.error(request, '驳回操作失败')
            return redirect('admin:workflow_engine_approvalinstance_changelist')
        
        # GET请求，显示确认页面
        from django.template.response import TemplateResponse
        context = {
            **self.admin_site.each_context(request),
            'title': '审批驳回',
            'instance': instance,
            'opts': self.model._meta,
            'has_view_permission': self.has_view_permission(request, instance),
        }
        return TemplateResponse(request, 'admin/workflow_engine/approvalinstance/reject.html', context)
    
    def approve_selected(self, request, queryset):
        """批量审批通过"""
        from .services import ApprovalEngine
        from django.contrib import messages
        
        count = 0
        for instance in queryset.filter(status='pending'):
            success = ApprovalEngine.approve(
                instance=instance,
                approver=request.user,
                result='approved',
                comment='后台批量审批通过'
            )
            if success:
                count += 1
        
        messages.success(request, f'成功审批通过 {count} 条记录')
    approve_selected.short_description = '批量审批通过'
    
    def reject_selected(self, request, queryset):
        """批量审批驳回"""
        from .services import ApprovalEngine
        from django.contrib import messages
        
        count = 0
        for instance in queryset.filter(status='pending'):
            success = ApprovalEngine.approve(
                instance=instance,
                approver=request.user,
                result='rejected',
                comment='后台批量审批驳回'
            )
            if success:
                count += 1
        
        messages.success(request, f'成功驳回 {count} 条记录')
    reject_selected.short_description = '批量审批驳回'


@admin.register(AgentConversation)
class AgentConversationAdmin(BaseModelAdmin):
    """Agent对话会话管理"""
    list_display = ('title', 'user', 'message_count_display', 'is_active', 'is_archived', 'created_time', 'last_message_time')
    list_filter = ('is_active', 'is_archived', 'created_time')
    search_fields = ('title', 'description', 'user__username')
    readonly_fields = ('created_time', 'updated_time', 'last_message_time')
    raw_id_fields = ['user']
    fieldsets = (
        ('基本信息', {
            'fields': ('title', 'description', 'user')
        }),
        ('状态', {
            'fields': ('is_active', 'is_archived')
        }),
        ('元数据', {
            'fields': ('metadata',),
            'classes': ('collapse',)
        }),
        # 时间信息会自动添加
    )
    
    def message_count_display(self, obj):
        """显示消息数量"""
        count = obj.messages.count()
        return format_html(
            '<a href="{}?conversation__id__exact={}" style="color: #1976d2;">{} 条消息</a>',
            reverse('admin:workflow_engine_agentmessage_changelist'),
            obj.id,
            count
        )
    message_count_display.short_description = '消息数量'
    
    def get_queryset(self, request):
        """优化查询，预加载消息数量"""
        qs = super().get_queryset(request)
        return qs.prefetch_related('messages')


@admin.register(AgentMessage)
class AgentMessageAdmin(BaseModelAdmin):
    """Agent对话消息管理"""
    list_display = ('conversation', 'role', 'content_preview', 'sequence', 'created_time')
    list_filter = ('role', 'created_time', 'conversation')
    search_fields = ('content', 'conversation__title')
    readonly_fields = ('created_time',)
    raw_id_fields = ['conversation']
    fieldsets = (
        ('基本信息', {
            'fields': ('conversation', 'role', 'sequence')
        }),
        ('消息内容', {
            'fields': ('content',)
        }),
        ('元数据', {
            'fields': ('metadata',),
            'classes': ('collapse',)
        }),
        # 时间信息会自动添加
    )
    
    def content_preview(self, obj):
        """显示消息内容预览"""
        preview = obj.content[:100] if len(obj.content) > 100 else obj.content
        if len(obj.content) > 100:
            preview += '...'
        return format_html('<span title="{}">{}</span>', obj.content, preview)
    content_preview.short_description = '消息内容'


@admin.register(ApprovalRecord)
class ApprovalRecordAdmin(BaseModelAdmin):
    """审批记录管理"""
    list_display = ('instance', 'node', 'approver', 'result', 'approval_time')
    list_filter = ('result', 'approval_time')
    search_fields = ('instance__instance_number', 'approver__username')
    readonly_fields = ('approval_time', 'created_time')
    raw_id_fields = ['instance', 'node', 'approver', 'transferred_to']
    fieldsets = (
        ('基本信息', {
            'fields': ('instance', 'node', 'approver', 'result')
        }),
        ('审批信息', {
            'fields': ('comment', 'transferred_to')
        }),
        # 时间信息会自动添加
    )
