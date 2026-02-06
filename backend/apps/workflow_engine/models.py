from django.db import models
from django.utils import timezone
from django.contrib.postgres.fields import ArrayField
from django.db.models import Max
from backend.apps.system_management.models import User


class WorkflowTemplate(models.Model):
    """审批流程模板"""
    STATUS_CHOICES = [
        ('draft', '草稿'),
        ('active', '启用'),
        ('inactive', '停用'),
    ]
    
    name = models.CharField(max_length=200, verbose_name='流程名称', help_text='例如：合同审批流程、商机审批流程')
    code = models.CharField(max_length=100, unique=True, verbose_name='流程代码', help_text='唯一标识，例如：contract_approval')
    description = models.TextField(blank=True, verbose_name='流程描述')
    category = models.CharField(max_length=100, blank=True, verbose_name='流程分类', help_text='例如：合同管理、商机管理')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft', verbose_name='状态')
    
    # 流程配置
    allow_withdraw = models.BooleanField(default=True, verbose_name='允许撤回', help_text='审批过程中是否允许撤回')
    allow_reject = models.BooleanField(default=True, verbose_name='允许驳回', help_text='是否允许审批人驳回')
    allow_transfer = models.BooleanField(default=False, verbose_name='允许转交', help_text='是否允许审批人转交给他人')
    
    # 超时配置
    timeout_hours = models.IntegerField(null=True, blank=True, verbose_name='超时时间（小时）', help_text='节点审批超时时间，为空则不限制')
    timeout_action = models.CharField(
        max_length=20,
        choices=[
            ('auto_approve', '自动通过'),
            ('auto_reject', '自动驳回'),
            ('notify', '仅通知'),
            ('escalate', '升级审批'),
        ],
        default='notify',
        verbose_name='超时处理方式'
    )
    
    # 适用模型配置
    applicable_models = ArrayField(
        models.TextField(),
        verbose_name='适用模型',
        help_text='指定此流程适用的业务模型，例如：businesscontract（合同）、businessopportunity（商机）、project（项目）等',
        default=list,
        blank=True,
    )
    
    # 具体表单筛选条件
    form_filter_conditions = models.JSONField(
        verbose_name='表单筛选条件',
        help_text='针对所选模型的具体表单筛选条件，JSON格式。例如：{"businesscontract": {"contract_type": ["sales", "purchase"]}}',
        default=dict,
        blank=True,
    )
    
    # 子工作流配置
    sub_workflow_trigger_condition = models.JSONField(
        verbose_name='子工作流触发条件',
        help_text='子工作流触发的条件配置，JSON格式',
        default=dict,
        blank=True,
    )
    
    # 审计字段
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='created_workflows', verbose_name='创建人')
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    updated_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        db_table = 'workflow_template'
        verbose_name = '审批流程模板'
        verbose_name_plural = verbose_name
        ordering = ['-created_time']
    
    def __str__(self):
        return self.name


class ApprovalNode(models.Model):
    """审批节点"""
    NODE_TYPE_CHOICES = [
        ('start', '开始节点'),
        ('approval', '审批节点'),
        ('condition', '条件节点'),
        ('parallel', '并行节点'),
        ('end', '结束节点'),
    ]
    
    APPROVER_TYPE_CHOICES = [
        ('role', '指定角色'),
        ('department', '指定部门'),
        ('department_manager', '部门经理'),
        ('creator', '创建人'),
        ('creator_manager', '创建人直属上级'),
        ('creator_manager_chain', '创建人多级上级'),
    ]
    
    APPROVAL_MODE_CHOICES = [
        ('single', '单人审批'),
        ('any', '任意一人通过'),
        ('all', '全部通过'),
        ('majority', '多数通过'),
    ]
    
    workflow = models.ForeignKey(WorkflowTemplate, on_delete=models.CASCADE, related_name='nodes', verbose_name='所属流程')
    name = models.CharField(max_length=200, verbose_name='节点名称')
    node_type = models.CharField(max_length=20, choices=NODE_TYPE_CHOICES, default='approval', verbose_name='节点类型')
    sequence = models.IntegerField(default=1, verbose_name='节点顺序', help_text='数字越小越靠前')
    
    # 审批人配置
    approver_type = models.CharField(max_length=30, choices=APPROVER_TYPE_CHOICES, blank=True, verbose_name='审批人类型')
    approver_users = models.ManyToManyField(User, blank=True, related_name='approval_nodes', verbose_name='指定审批人')
    approver_roles = models.ManyToManyField('system_management.Role', blank=True, related_name='approval_nodes', verbose_name='指定角色')
    approver_departments = models.ManyToManyField('system_management.Department', blank=True, related_name='approval_nodes', verbose_name='指定部门')
    approver_config = models.JSONField(default=dict, blank=True, verbose_name='审批人规则配置', help_text='JSON格式的审批人规则配置参数，例如：{"levels": 2} 用于多级上级审批')
    approval_mode = models.CharField(max_length=20, choices=APPROVAL_MODE_CHOICES, default='single', verbose_name='审批模式')
    
    # 条件配置（用于条件节点）
    condition_expression = models.TextField(blank=True, verbose_name='条件表达式', help_text='JSON格式的条件表达式')
    
    # 节点配置
    is_required = models.BooleanField(default=True, verbose_name='是否必审', help_text='是否必须审批通过')
    can_reject = models.BooleanField(default=True, verbose_name='可驳回')
    can_transfer = models.BooleanField(default=False, verbose_name='可转交')
    timeout_hours = models.IntegerField(null=True, blank=True, verbose_name='超时时间（小时）', help_text='覆盖流程默认超时时间')
    
    # 描述
    description = models.TextField(blank=True, verbose_name='节点描述')
    
    class Meta:
        db_table = 'workflow_approval_node'
        verbose_name = '审批节点'
        verbose_name_plural = verbose_name
        ordering = ['workflow', 'sequence']
        unique_together = [['workflow', 'sequence']]
    
    def clean(self):
        """模型校验：禁止使用已废弃的审批人类型，并校验 approver_config"""
        from django.core.exceptions import ValidationError
        
        # 禁止使用 user 类型（写死用户，无法适应组织变化）
        if self.approver_type == 'user':
            raise ValidationError({
                'approver_type': '审批人类型 "指定用户" 已废弃，禁止使用。请使用 "指定角色" 或其他配置化类型，以支持组织变化自动适配。'
            })
        
        # 禁止使用 custom 类型（硬编码逻辑，无法配置）
        if self.approver_type == 'custom':
            raise ValidationError({
                'approver_type': '审批人类型 "自定义规则" 已废弃，禁止使用。请使用 "指定角色" 或其他配置化类型。'
            })
        
        # 校验 approver_config（针对 creator_manager_chain）
        if self.approver_type == 'creator_manager_chain':
            if not isinstance(self.approver_config, dict):
                raise ValidationError({
                    'approver_config': 'creator_manager_chain 类型必须配置 approver_config（JSON格式）'
                })
            
            levels = self.approver_config.get('levels')
            if levels is None:
                raise ValidationError({
                    'approver_config': 'creator_manager_chain 类型必须配置 levels 参数（向上追溯的级数）'
                })
            
            if not isinstance(levels, int) or levels < 1:
                raise ValidationError({
                    'approver_config': 'levels 必须为正整数（1-10），当前值：{}'.format(levels)
                })
            
            if levels > 10:
                raise ValidationError({
                    'approver_config': 'levels 不能超过 10 级，当前值：{}。建议值：2-4 级'.format(levels)
                })
        
        super().clean()
    
    def save(self, *args, **kwargs):
        """保存时强制校验，防止绕过clean"""
        self.full_clean()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.workflow.name} - {self.name}"


class ApprovalInstance(models.Model):
    """审批实例"""
    STATUS_CHOICES = [
        ('draft', '草稿'),
        ('pending', '审批中'),
        ('approved', '已通过'),
        ('rejected', '已驳回'),
        ('withdrawn', '已撤回'),
        ('cancelled', '已取消'),
    ]
    
    workflow = models.ForeignKey(WorkflowTemplate, on_delete=models.PROTECT, related_name='instances', verbose_name='流程模板')
    instance_number = models.CharField(max_length=100, unique=True, verbose_name='实例编号', help_text='自动生成')
    
    # 关联业务对象（通用设计）
    content_type = models.ForeignKey(
        'contenttypes.ContentType', 
        on_delete=models.CASCADE, 
        verbose_name='关联对象类型',
        help_text='选择要关联的业务对象类型。例如：合同(businesscontract)、商机(businessopportunity)、项目(project)等。通常不需要手动填写，审批流程会在业务代码中自动创建并关联。'
    )
    object_id = models.PositiveIntegerField(
        verbose_name='关联对象ID',
        help_text='填写该业务对象的具体ID。例如：合同ID为123，则填写123。通常不需要手动填写，审批流程会在业务代码中自动创建并关联。'
    )
    
    # 流程状态
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft', verbose_name='审批状态')
    current_node = models.ForeignKey(ApprovalNode, on_delete=models.SET_NULL, null=True, blank=True, related_name='active_instances', verbose_name='当前节点')
    
    # 申请人信息
    applicant = models.ForeignKey(User, on_delete=models.PROTECT, related_name='applied_approvals', verbose_name='申请人')
    apply_time = models.DateTimeField(null=True, blank=True, verbose_name='申请时间')
    apply_comment = models.TextField(blank=True, verbose_name='申请说明')
    
    # 完成信息
    completed_time = models.DateTimeField(null=True, blank=True, verbose_name='完成时间')
    final_comment = models.TextField(blank=True, verbose_name='最终意见')
    
    # 审计字段
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    updated_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        db_table = 'workflow_approval_instance'
        verbose_name = '审批实例'
        verbose_name_plural = verbose_name
        ordering = ['-created_time']
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.instance_number} - {self.get_status_display()}"


class ApprovalRecord(models.Model):
    """审批记录"""
    RESULT_CHOICES = [
        ('pending', '待审批'),
        ('approved', '通过'),
        ('rejected', '驳回'),
        ('transferred', '转交'),
        ('withdrawn', '撤回'),
    ]
    
    instance = models.ForeignKey(ApprovalInstance, on_delete=models.CASCADE, related_name='records', verbose_name='审批实例')
    node = models.ForeignKey(ApprovalNode, on_delete=models.PROTECT, related_name='records', verbose_name='审批节点')
    
    # 审批人信息
    approver = models.ForeignKey(User, on_delete=models.PROTECT, related_name='approval_records', verbose_name='审批人')
    result = models.CharField(max_length=20, choices=RESULT_CHOICES, default='pending', verbose_name='审批结果')
    comment = models.TextField(blank=True, verbose_name='审批意见')
    
    # 转交信息
    transferred_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='transferred_approvals', verbose_name='转交给')
    
    # 时间信息
    approval_time = models.DateTimeField(default=timezone.now, verbose_name='审批时间')
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    
    class Meta:
        db_table = 'workflow_approval_record'
        verbose_name = '审批记录'
        verbose_name_plural = verbose_name
        ordering = ['-approval_time']
    
    def __str__(self):
        return f"{self.instance.instance_number} - {self.approver.username} - {self.get_result_display()}"


class WorkflowBinding(models.Model):
    """流程模板绑定配置
    
    用于配置业务对象类型 + 操作类型 → 流程模板的绑定关系
    支持同一业务对象的不同操作（如 plan 的 start/cancel）使用不同的流程模板
    """
    # 用于模板选择的操作类型（仅这些操作会参与流程模板绑定）
    ACTION_CHOICES_FOR_BINDING = [
        ('submit', '提交审批'),
        ('start', '启动'),
        ('cancel', '取消'),
    ]
    
    # 完整的操作类型列表（包含不用于模板选择的操作，用于向后兼容）
    ACTION_CHOICES = ACTION_CHOICES_FOR_BINDING + [
        ('approve', '审批'),  # 不用于模板选择
        ('reject', '驳回'),   # 不用于模板选择
        ('withdraw', '撤回'), # 不用于模板选择
    ]
    
    # 绑定目标：业务对象类型
    content_type = models.ForeignKey(
        'contenttypes.ContentType',
        on_delete=models.CASCADE,
        verbose_name='业务对象类型',
        help_text='选择要绑定的业务对象类型，例如：loanapplication（借款申请）、sealusage（用印申请）等'
    )
    
    # 操作类型
    action = models.CharField(
        max_length=50,
        choices=ACTION_CHOICES,
        default='submit',
        verbose_name='操作类型',
        help_text='选择操作类型，例如：submit（提交审批）、start（启动）、cancel（取消）等'
    )
    
    # 绑定的流程模板
    workflow_template = models.ForeignKey(
        WorkflowTemplate,
        on_delete=models.PROTECT,
        related_name='bindings',
        verbose_name='流程模板',
        help_text='选择要绑定的流程模板'
    )
    
    # 优先级（数字越大优先级越高，用于同一 content_type + action 有多条配置时）
    priority = models.IntegerField(
        default=0,
        verbose_name='优先级',
        help_text='数字越大优先级越高。当同一业务对象类型和操作类型有多条配置时，选择优先级最高的启用配置'
    )
    
    # 是否启用
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        verbose_name='是否启用',
        help_text='只有启用的配置才会生效'
    )
    
    # 备注
    note = models.TextField(
        blank=True,
        verbose_name='备注',
        help_text='配置说明或备注信息'
    )
    
    # 审计字段
    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='created_workflow_bindings',
        verbose_name='创建人'
    )
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='updated_workflow_bindings',
        verbose_name='更新人'
    )
    updated_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        db_table = 'workflow_binding'
        verbose_name = '流程模板绑定配置'
        verbose_name_plural = verbose_name
        ordering = ['-priority', '-created_time']
        indexes = [
            models.Index(fields=['content_type', 'action', 'is_active']),
            models.Index(fields=['is_active']),
        ]
        # 唯一约束：同一 content_type + action + is_active=True 时，priority 应该唯一（通过业务逻辑保证）
    
    def __str__(self):
        content_type_name = self.content_type.model if self.content_type else 'Unknown'
        action_display = self.get_action_display()
        workflow_name = self.workflow_template.name if self.workflow_template else 'Unknown'
        return f"{content_type_name} - {action_display} → {workflow_name}"
    
    def clean(self):
        """模型级别的验证"""
        from django.core.exceptions import ValidationError
        
        # 验证操作类型：只允许用于模板选择的操作类型
        if self.action not in [choice[0] for choice in self.ACTION_CHOICES_FOR_BINDING]:
            raise ValidationError({
                'action': f'操作类型 "{self.get_action_display()}" 不用于流程模板选择，请选择 submit/start/cancel 之一'
            })
        
        # 验证流程模板状态
        if self.workflow_template and self.workflow_template.status != 'active':
            raise ValidationError({
                'workflow_template': '只能绑定状态为"启用"的流程模板'
            })
        
        # 注意：唯一生效规则的实际保证在 save() 方法中通过自动禁用其他配置实现
        # 这里不再进行严格的优先级检查，因为 save() 会自动处理
    
    def save(self, *args, **kwargs):
        """
        保存前执行验证，并确保唯一启用规则（事务一致）
        
        策略：当启用一条配置时，自动禁用同 content_type + action 的其他启用配置
        这样可以确保数据库级一致性，避免并发问题
        """
        from django.db import transaction
        
        self.full_clean()
        
        # 如果当前配置要启用，且存在同 content_type + action 的其他启用配置
        # 则自动禁用它们（确保唯一启用规则）
        if self.is_active and self.content_type and self.action:
            with transaction.atomic():
                # 先保存当前对象（如果已存在pk）
                if self.pk:
                    super().save(*args, **kwargs)
                
                # 禁用同 content_type + action 的其他启用配置
                conflicting = WorkflowBinding.objects.filter(
                    content_type=self.content_type,
                    action=self.action,
                    is_active=True
                ).exclude(pk=self.pk if self.pk else None)
                
                if conflicting.exists():
                    # 禁用其他启用配置（确保唯一启用规则）
                    # 注意：这里不检查优先级，因为启用当前配置时，其他配置应该被禁用
                    # 如果用户想要保留其他配置，应该先停用当前配置，再启用其他配置
                    conflicting.update(is_active=False)
                
                # 如果当前对象是新创建的，现在保存
                if not self.pk:
                    super().save(*args, **kwargs)
        else:
            # 如果当前配置不启用，直接保存
            super().save(*args, **kwargs)

