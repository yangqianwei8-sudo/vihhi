from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.db import models
from django import forms
from backend.apps.workflow_engine.models import WorkflowTemplate, ApprovalNode, ApprovalInstance, ApprovalRecord
from backend.core.admin_base import BaseModelAdmin, AuditAdminMixin


# 定义每个模型对应的需要审批的表单列表
# 使用表单的主标题名称（用户在页面上看到的标题）
MODEL_FORM_MAP = {
    'plan': [
        ('plan', '创建计划'),
        ('strategicgoal', '创建战略目标'),
        ('plandecision', '计划决策'),
        ('planadjustment', '申请调整'),
        ('goaladjustment', '目标调整申请'),
    ],
    'businesscontract': [
        ('businesscontract', '创建合同'),
    ],
    'businessopportunity': [
        ('businessopportunity', '创建商机'),
    ],
    'project': [
        ('project', '创建项目'),
    ],
    'client': [
        ('client', '创建客户'),
    ],
    'strategicgoal': [
        ('strategicgoal', '创建战略目标'),
        ('goaladjustment', '目标调整申请'),
    ],
    'case': [
        ('case', '创建诉讼案件'),
    ],
    'litigationexpense': [
        ('litigationexpense', '创建诉讼费用'),
    ],
    'sealborrowing': [
        ('sealborrowing', '申请借用印章'),
    ],
    'sealusage': [
        ('sealusage', '申请用印'),
    ],
}

# 定义可用的业务模型选项
# 注意：模型名称使用小写，对应 Django ContentType 的 model 字段值
APPLICABLE_MODEL_CHOICES = [
    # 客户管理模块
    ('client', '客户 (Client)'),
    ('businesscontract', '合同 (BusinessContract)'),
    ('businessopportunity', '商机 (BusinessOpportunity)'),
    
    # 项目管理模块
    ('project', '项目 (Project)'),
    
    # 计划管理模块
    ('plan', '计划 (Plan)'),
    ('strategicgoal', '战略目标 (StrategicGoal)'),
    
    # 诉讼管理模块
    ('case', '诉讼案件 (Case)'),
    ('litigationexpense', '诉讼费用 (LitigationExpense)'),
    
    # 生产管理模块
    ('productiontask', '生产任务 (ProductionTask)'),
    ('productionplan', '生产计划 (ProductionPlan)'),
    
    # 结算管理模块
    ('settlement', '结算单 (Settlement)'),
    ('payment', '付款单 (Payment)'),
    
    # 财务管理模块
    ('invoice', '发票 (Invoice)'),
    ('fundflow', '资金流水 (FundFlow)'),
    
    # 行政管理模块
    ('vehiclebooking', '车辆预订 (VehicleBooking)'),
    ('meetingroombooking', '会议室预订 (MeetingRoomBooking)'),
    ('sealborrowing', '印章借用 (SealBorrowing)'),
    ('sealusage', '用印申请 (SealUsage)'),
    
    # 人事管理模块
    ('employee', '员工 (Employee)'),
    ('attendance', '考勤记录 (Attendance)'),
    
    # 档案管理模块
    ('archive', '档案 (Archive)'),
    ('document', '文档 (Document)'),
    
    # 任务协作模块
    ('task', '任务 (Task)'),
    ('collaborationtask', '协作任务 (CollaborationTask)'),
    
    # 交付客户模块
    ('deliveryrecord', '交付记录 (DeliveryRecord)'),
    ('deliveryfile', '交付文件 (DeliveryFile)'),
]


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
        ('适用范围', {
            'fields': ('applicable_models', 'form_filter_conditions'),
            'description': '选择此流程适用的业务模型类型。可以选择多个模型。如果为空，则适用于所有模型。右侧筛选框用于进一步筛选具体表单。'
        }),
        ('审计信息', {
            'fields': ('created_by',)
        }),
        # 时间信息会自动添加
    )
    
    def get_form(self, request, obj=None, **kwargs):
        """自定义表单，将 applicable_models 改为多选下拉框，并添加表单筛选条件字段"""
        form = super().get_form(request, obj, **kwargs)
        
        # 将 ArrayField 改为 MultipleChoiceField
        if 'applicable_models' in form.base_fields:
            form.base_fields['applicable_models'] = forms.MultipleChoiceField(
                choices=APPLICABLE_MODEL_CHOICES,
                required=False,
                widget=forms.SelectMultiple(attrs={
                    'size': 10,
                    'style': 'min-width: 300px;',
                    'class': 'form-select',
                    'id': 'id_applicable_models'
                }),
                help_text='选择此流程适用的业务模型类型。可以按住 Ctrl (Windows) 或 Cmd (Mac) 键进行多选。',
                label='适用模型',
            )
            # 如果正在编辑现有对象，设置初始值
            if obj and obj.applicable_models:
                form.base_fields['applicable_models'].initial = obj.applicable_models
        
        # 自定义表单筛选条件字段 - 改为多选下拉框
        if 'form_filter_conditions' in form.base_fields:
            # 获取所有可用的表单选项（合并所有模型的表单）
            all_form_choices = []
            for forms_list in MODEL_FORM_MAP.values():
                all_form_choices.extend(forms_list)
            
            # 去重并排序
            seen = set()
            unique_choices = []
            for choice in all_form_choices:
                if choice[0] not in seen:
                    seen.add(choice[0])
                    unique_choices.append(choice)
            unique_choices.sort(key=lambda x: x[1])
            
            # 将 JSONField 改为 MultipleChoiceField
            form.base_fields['form_filter_conditions'] = forms.MultipleChoiceField(
                choices=unique_choices if unique_choices else [('', '请先选择适用模型')],
                required=False,
                widget=forms.SelectMultiple(attrs={
                    'size': 10,
                    'style': 'min-width: 300px;',
                    'class': 'form-select',
                    'id': 'id_form_filter_conditions'
                }),
                help_text=format_html(
                    '根据左侧选择的模型，显示该模型下所有需要审批的表单。可以选择多个表单。<br>'
                    '<small style="color: #666;">提示：此字段会根据左侧选择的模型动态更新。</small>'
                ),
                label='具体表单',
            )
            # 如果正在编辑现有对象，从 JSON 中提取已选择的表单
            if obj and obj.form_filter_conditions:
                try:
                    # form_filter_conditions 是 JSON，格式可能是 {"plan": ["plan", "strategicgoal"]}
                    selected_forms = []
                    if isinstance(obj.form_filter_conditions, dict):
                        for model, forms_list in obj.form_filter_conditions.items():
                            if isinstance(forms_list, list):
                                selected_forms.extend(forms_list)
                    form.base_fields['form_filter_conditions'].initial = selected_forms
                except (TypeError, ValueError, AttributeError):
                    form.base_fields['form_filter_conditions'].initial = []
        
        return form
    
    class Media:
        css = {
            'all': ('admin/css/workflow_template_admin.css',)
        }
        js = ('admin/js/workflow_template_admin.js',)
    
    def save_model(self, request, obj, form, change):
        """保存模型时，确保字段不为 None，并处理 MultipleChoiceField 的数据"""
        # 处理 applicable_models（从 MultipleChoiceField 转换为列表）
        if 'applicable_models' in form.cleaned_data:
            obj.applicable_models = form.cleaned_data['applicable_models']
        elif not obj.applicable_models:
            obj.applicable_models = []
        
        # 处理 form_filter_conditions（从 MultipleChoiceField 转换为 JSON）
        if 'form_filter_conditions' in form.cleaned_data:
            selected_forms = form.cleaned_data['form_filter_conditions']
            # 将选择的表单按模型分组
            form_by_model = {}
            for form_name in selected_forms:
                # 查找表单属于哪个模型
                for model, forms_list in MODEL_FORM_MAP.items():
                    if any(f[0] == form_name for f in forms_list):
                        if model not in form_by_model:
                            form_by_model[model] = []
                        form_by_model[model].append(form_name)
                        break
            obj.form_filter_conditions = form_by_model
        elif not obj.form_filter_conditions:
            obj.form_filter_conditions = {}
        
        if not obj.sub_workflow_trigger_condition:
            obj.sub_workflow_trigger_condition = {}
        super().save_model(request, obj, form, change)


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
                
                if model_name == 'businesscontract':
                    try:
                        admin_url = reverse('admin:contract_management_businesscontract_change', args=[obj.object_id])
                    except:
                        pass
                elif model_name == 'businessopportunity':
                    try:
                        admin_url = reverse('admin:opportunity_management_businessopportunity_change', args=[obj.object_id])
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
                
                if model_name == 'businesscontract':
                    try:
                        admin_url = reverse('admin:contract_management_businesscontract_change', args=[obj.object_id])
                    except:
                        pass
                elif model_name == 'businessopportunity':
                    try:
                        admin_url = reverse('admin:opportunity_management_businessopportunity_change', args=[obj.object_id])
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
            if not success:
                messages.error(request, '审批操作失败')
            # 审批结果走通知中心，不写入 success messages
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
            if not success:
                messages.error(request, '驳回操作失败')
            # 审批结果走通知中心，不写入 success messages
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
        # 审批结果走通知中心，不写入 success messages
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
        # 审批结果走通知中心，不写入 success messages
    reject_selected.short_description = '批量审批驳回'


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
