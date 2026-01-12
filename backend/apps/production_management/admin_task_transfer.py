"""
任务自动转交配置的Admin管理界面
"""
from django.contrib import admin
from django.contrib import messages
from django.utils.html import format_html
from backend.apps.production_management.models import TaskAutoTransferConfig, ProjectTask
from backend.core.admin_base import BaseModelAdmin, AuditAdminMixin


@admin.register(TaskAutoTransferConfig)
class TaskAutoTransferConfigAdmin(AuditAdminMixin, BaseModelAdmin):
    """任务自动转交配置管理
    
    配置任务完成后的自动转交规则，实现工作流的自动化流转。
    例如：张三完成工作A后，自动转交给李四实施工作B。
    """
    
    list_display = (
        'source_task_display', 
        'target_task_display', 
        'condition_type_display',
        'is_active', 
        'order', 
        'delay_hours',
        'workflow_preview',
        'created_by',
        'created_time'
    )
    list_filter = (
        'is_active', 
        'condition_type',
        'source_task_type',
        'created_time'
    )
    search_fields = (
        'source_task_type', 
        'target_task_type', 
        'description'
    )
    readonly_fields = (
        'created_time', 
        'updated_time',
        'workflow_preview',
        'circular_dependency_check'
    )
    ordering = ('source_task_type', 'order', 'created_time')
    
    fieldsets = (
        ('转交规则配置', {
            'fields': ('source_task_type', 'target_task_type', 'condition_type'),
            'description': '配置源任务完成后自动转交到目标任务。系统会自动检测循环依赖。'
        }),
        ('执行设置', {
            'fields': ('is_active', 'order', 'delay_hours'),
            'description': '设置转交规则的执行条件和顺序。同一源任务可以有多个转交目标，按顺序执行。'
        }),
        ('配置说明', {
            'fields': ('description',),
            'description': '描述此转交规则的业务场景和用途，便于后续维护。'
        }),
        ('工作流预览', {
            'fields': ('workflow_preview', 'circular_dependency_check'),
            'classes': ('collapse',),
            'description': '预览转交规则形成的工作流路径，检查是否存在循环依赖。'
        }),
        ('审计信息', {
            'fields': ('created_by', 'created_time', 'updated_time'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['activate_selected', 'deactivate_selected', 'validate_selected']
    
    def source_task_display(self, obj):
        """显示源任务类型（带链接）"""
        task_choices = dict(ProjectTask.TASK_TYPE_CHOICES)
        display_name = task_choices.get(obj.source_task_type, obj.source_task_type)
        url = f'/admin/production_management/taskautotransferconfig/?source_task_type__exact={obj.source_task_type}'
        return format_html(
            '<a href="{}" style="font-weight: bold; color: #1976d2;">{}</a>',
            url, display_name
        )
    source_task_display.short_description = '源任务'
    source_task_display.admin_order_field = 'source_task_type'
    
    def target_task_display(self, obj):
        """显示目标任务类型（带链接）"""
        task_choices = dict(ProjectTask.TASK_TYPE_CHOICES)
        display_name = task_choices.get(obj.target_task_type, obj.target_task_type)
        url = f'/admin/production_management/taskautotransferconfig/?target_task_type__exact={obj.target_task_type}'
        return format_html(
            '<a href="{}" style="font-weight: bold; color: #4caf50;">{}</a>',
            url, display_name
        )
    target_task_display.short_description = '目标任务'
    target_task_display.admin_order_field = 'target_task_type'
    
    def condition_type_display(self, obj):
        """显示执行条件"""
        condition_map = {
            'always': ('✓', '总是执行', '#4caf50'),
            'on_success': ('✓', '仅成功时', '#2196f3'),
            'on_failure': ('✗', '仅失败时', '#ff9800'),
        }
        icon, text, color = condition_map.get(obj.condition_type, ('?', obj.get_condition_type_display(), '#9e9e9e'))
        return format_html(
            '<span style="color: {}; font-weight: bold;">{} {}</span>',
            color, icon, text
        )
    condition_type_display.short_description = '执行条件'
    condition_type_display.admin_order_field = 'condition_type'
    
    def workflow_preview(self, obj):
        """预览工作流路径"""
        if not obj.pk:
            return format_html('<span style="color: #9e9e9e;">保存后显示工作流预览</span>')
        
        # 构建工作流路径
        path = self._build_workflow_path(obj.source_task_type, obj.target_task_type, max_depth=5)
        
        if not path:
            return format_html('<span style="color: #9e9e9e;">无后续转交</span>')
        
        html = '<div style="padding: 10px; background: #f5f5f5; border-radius: 4px; font-family: monospace;">'
        task_choices = dict(ProjectTask.TASK_TYPE_CHOICES)
        html += f'<strong>{task_choices.get(obj.source_task_type, obj.source_task_type)}</strong>'
        
        for task_type in path:
            task_name = task_choices.get(task_type, task_type)
            html += f' → <strong>{task_name}</strong>'
        
        html += '</div>'
        return format_html(html)
    workflow_preview.short_description = '工作流预览'
    
    def circular_dependency_check(self, obj):
        """检查循环依赖"""
        if not obj.pk:
            return format_html('<span style="color: #9e9e9e;">保存后检查循环依赖</span>')
        
        try:
            # 检查是否存在循环依赖
            visited = set()
            has_circular = self._check_circular_dependency(
                obj.source_task_type, 
                obj.target_task_type, 
                visited
            )
            
            task_choices = dict(ProjectTask.TASK_TYPE_CHOICES)
            
            if has_circular:
                path_display = [task_choices.get(obj.source_task_type, obj.source_task_type)]
                for t in list(visited)[:5]:
                    path_display.append(task_choices.get(t, t))
                if len(visited) > 5:
                    path_display.append('...')
                
                return format_html(
                    '<div style="padding: 10px; background: #ffebee; border-left: 4px solid #f44336; border-radius: 4px;">'
                    '<strong style="color: #c62828;">⚠️ 检测到循环依赖！</strong><br>'
                    '<span style="color: #c62828;">路径：{}</span>'
                    '</div>',
                    ' → '.join(path_display)
                )
            else:
                return format_html(
                    '<div style="padding: 10px; background: #e8f5e9; border-left: 4px solid #4caf50; border-radius: 4px;">'
                    '<strong style="color: #2e7d32;">✓ 无循环依赖</strong>'
                    '</div>'
                )
        except Exception as e:
            return format_html(
                '<div style="padding: 10px; background: #fff3e0; border-left: 4px solid #ff9800; border-radius: 4px;">'
                '<strong style="color: #e65100;">检查失败：{}</strong>'
                '</div>',
                str(e)
            )
    circular_dependency_check.short_description = '循环依赖检查'
    
    def _build_workflow_path(self, start_task, end_task, max_depth=5, current_path=None):
        """构建工作流路径"""
        if current_path is None:
            current_path = []
        
        if len(current_path) >= max_depth:
            return None
        
        # 查找从end_task转交出去的任务
        configs = TaskAutoTransferConfig.objects.filter(
            source_task_type=end_task,
            is_active=True
        ).order_by('order')
        
        if not configs.exists():
            return current_path
        
        # 取第一个转交目标
        first_config = configs.first()
        current_path.append(first_config.target_task_type)
        
        # 递归查找
        return self._build_workflow_path(start_task, first_config.target_task_type, max_depth, current_path)
    
    def _check_circular_dependency(self, start_task, current_task, visited):
        """检查是否存在循环依赖"""
        if current_task == start_task and len(visited) > 0:
            return True
        
        if current_task in visited:
            return False
        
        visited.add(current_task)
        
        # 查找当前任务的所有转交目标
        configs = TaskAutoTransferConfig.objects.filter(
            source_task_type=current_task,
            is_active=True
        )
        
        for config in configs:
            if self._check_circular_dependency(start_task, config.target_task_type, visited.copy()):
                return True
        
        return False
    
    def activate_selected(self, request, queryset):
        """批量启用"""
        count = queryset.update(is_active=True)
        self.message_user(request, f'已启用 {count} 条转交规则。', messages.SUCCESS)
    activate_selected.short_description = '启用选中的转交规则'
    
    def deactivate_selected(self, request, queryset):
        """批量禁用"""
        count = queryset.update(is_active=False)
        self.message_user(request, f'已禁用 {count} 条转交规则。', messages.SUCCESS)
    deactivate_selected.short_description = '禁用选中的转交规则'
    
    def validate_selected(self, request, queryset):
        """批量验证配置"""
        errors = []
        warnings = []
        
        for config in queryset:
            try:
                config.full_clean()
                # 检查循环依赖
                visited = set()
                if self._check_circular_dependency(
                    config.source_task_type,
                    config.target_task_type,
                    visited
                ):
                    warnings.append(f'{config}: 检测到循环依赖')
            except Exception as e:
                errors.append(f'{config}: {str(e)}')
        
        if errors:
            self.message_user(request, f'验证失败：{"; ".join(errors)}', messages.ERROR)
        elif warnings:
            self.message_user(request, f'验证通过，但有警告：{"; ".join(warnings)}', messages.WARNING)
        else:
            self.message_user(request, f'所有 {queryset.count()} 条配置验证通过。', messages.SUCCESS)
    validate_selected.short_description = '验证选中的配置'
    
    def get_form(self, request, obj=None, **kwargs):
        """自定义表单，添加帮助文本"""
        form = super().get_form(request, obj, **kwargs)
        
        # 为字段添加帮助文本
        if 'source_task_type' in form.base_fields:
            form.base_fields['source_task_type'].help_text = (
                '选择完成后需要触发自动转交的任务类型。'
                '例如：选择"完善项目信息"，当该任务完成时，会自动创建目标任务。'
            )
        
        if 'target_task_type' in form.base_fields:
            form.base_fields['target_task_type'].help_text = (
                '选择源任务完成后自动创建的任务类型。'
                '系统会自动检测是否与源任务相同，以及是否存在循环依赖。'
            )
        
        if 'order' in form.base_fields:
            form.base_fields['order'].help_text = (
                '当同一源任务有多个转交目标时，按此顺序执行。'
                '数字越小越先执行，相同顺序按创建时间排序。'
            )
        
        if 'delay_hours' in form.base_fields:
            form.base_fields['delay_hours'].help_text = (
                '源任务完成后延迟多少小时再创建目标任务。'
                '设置为0表示立即执行。可用于需要等待时间的业务场景。'
            )
        
        return form
    
    def save_model(self, request, obj, form, change):
        """保存模型前设置创建人"""
        if not change:  # 新建时
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

