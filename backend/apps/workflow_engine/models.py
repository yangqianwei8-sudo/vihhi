from django.db import models
from django.utils import timezone
from django.contrib.postgres.fields import ArrayField
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
        ('user', '指定用户'),
        ('role', '指定角色'),
        ('department', '指定部门'),
        ('department_manager', '部门经理'),
        ('creator', '创建人'),
        ('creator_manager', '创建人上级'),
        ('custom', '自定义规则'),
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

