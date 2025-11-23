"""
生产启动相关模型
"""
from decimal import Decimal
from django.db import models
from django.utils import timezone
from django.conf import settings
from backend.apps.project_center.models import Project, ServiceProfession


def drawing_file_path(instance, filename):
    """图纸文件上传路径"""
    return f"projects/{instance.project.id}/drawings/{instance.directory.path if instance.directory else 'root'}/{filename}"


class ProjectStartup(models.Model):
    """项目生产启动记录"""
    
    STATUS_CHOICES = [
        ('project_received', '项目已接收'),
        ('drawings_uploading', '图纸载入中'),
        ('team_configuring', '团队配置中'),
        ('tasks_creating', '任务清单创建中'),
        ('waiting_approval', '待审批'),
        ('approved', '已审批通过'),
        ('rejected', '已驳回'),
        ('started', '已启动'),
    ]
    
    project = models.OneToOneField(
        Project,
        on_delete=models.CASCADE,
        related_name='startup',
        verbose_name='项目'
    )
    
    # 项目接收信息
    received_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='received_startups',
        verbose_name='接收人（技术部经理）'
    )
    received_time = models.DateTimeField(null=True, blank=True, verbose_name='接收时间')
    project_manager_assigned = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_startups',
        verbose_name='分配的项目经理'
    )
    project_manager_assigned_time = models.DateTimeField(null=True, blank=True, verbose_name='项目经理分配时间')
    
    # 图纸载入信息
    drawings_uploaded = models.BooleanField(default=False, verbose_name='图纸是否已上传')
    drawings_upload_time = models.DateTimeField(null=True, blank=True, verbose_name='图纸上传时间')
    drawings_uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='uploaded_drawings_startups',
        verbose_name='图纸上传人'
    )
    
    # 团队配置信息
    team_configured = models.BooleanField(default=False, verbose_name='团队是否已配置')
    team_configured_time = models.DateTimeField(null=True, blank=True, verbose_name='团队配置时间')
    
    # 任务清单信息
    tasks_created = models.BooleanField(default=False, verbose_name='任务是否已创建')
    tasks_created_time = models.DateTimeField(null=True, blank=True, verbose_name='任务创建时间')
    total_tasks = models.IntegerField(default=0, verbose_name='任务总数')
    total_saving_target = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='任务节省目标总额'
    )
    contract_saving_target = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='合同节省目标'
    )
    
    # 审批信息
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='submitted_startups',
        verbose_name='提交审批人'
    )
    submitted_time = models.DateTimeField(null=True, blank=True, verbose_name='提交审批时间')
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_startups',
        verbose_name='审批人（技术部经理）'
    )
    approved_time = models.DateTimeField(null=True, blank=True, verbose_name='审批时间')
    approval_comment = models.TextField(blank=True, verbose_name='审批意见')
    rejected_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='rejected_startups',
        verbose_name='驳回人'
    )
    rejected_time = models.DateTimeField(null=True, blank=True, verbose_name='驳回时间')
    rejection_reason = models.TextField(blank=True, verbose_name='驳回原因')
    
    # 启动信息
    started_time = models.DateTimeField(null=True, blank=True, verbose_name='启动时间')
    
    # 状态
    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default='project_received',
        verbose_name='启动状态'
    )
    
    # 元数据
    metadata = models.JSONField(default=dict, blank=True, verbose_name='扩展信息')
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    updated_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        db_table = 'production_quality_startup'
        verbose_name = '项目生产启动'
        verbose_name_plural = verbose_name
        ordering = ['-created_time']
    
    def __str__(self):
        return f"{self.project.project_number} - {self.get_status_display()}"


class ProjectDrawingDirectory(models.Model):
    """项目图纸目录结构"""
    
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='drawing_directories',
        verbose_name='项目'
    )
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
        verbose_name='父目录'
    )
    name = models.CharField(max_length=200, verbose_name='目录名称')
    path = models.CharField(max_length=500, verbose_name='目录路径')
    order = models.IntegerField(default=0, verbose_name='排序')
    is_template = models.BooleanField(default=False, verbose_name='是否模板目录')
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_drawing_directories',
        verbose_name='创建人'
    )
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    
    class Meta:
        db_table = 'production_quality_drawing_directory'
        verbose_name = '图纸目录'
        verbose_name_plural = verbose_name
        ordering = ['order', 'id']
        unique_together = ['project', 'path']
    
    def __str__(self):
        return f"{self.project.project_number} - {self.path}"


class ProjectDrawingFile(models.Model):
    """项目图纸文件"""
    
    DRAWING_TYPE_CHOICES = [
        ('dwg', 'DWG'),
        ('pdf', 'PDF'),
        ('jpg', 'JPG'),
        ('png', 'PNG'),
        ('rvt', 'RVT'),
        ('other', '其他'),
    ]
    
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='startup_drawing_files',
        verbose_name='项目'
    )
    directory = models.ForeignKey(
        ProjectDrawingDirectory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='files',
        verbose_name='所属目录'
    )
    file = models.FileField(upload_to=drawing_file_path, verbose_name='图纸文件')
    file_name = models.CharField(max_length=255, verbose_name='文件名')
    file_type = models.CharField(max_length=20, choices=DRAWING_TYPE_CHOICES, verbose_name='文件类型')
    file_size = models.BigIntegerField(null=True, blank=True, verbose_name='文件大小（字节）')
    thumbnail = models.ImageField(
        upload_to=drawing_file_path,
        null=True,
        blank=True,
        verbose_name='缩略图'
    )
    
    # 图纸识别信息
    drawing_number = models.CharField(max_length=100, blank=True, verbose_name='图纸编号')
    drawing_version = models.CharField(max_length=50, blank=True, verbose_name='图纸版本')
    drawing_date = models.DateField(null=True, blank=True, verbose_name='出图日期')
    design_unit = models.CharField(max_length=200, blank=True, verbose_name='设计单位')
    scale = models.CharField(max_length=50, blank=True, verbose_name='比例尺')
    profession_type = models.CharField(max_length=50, blank=True, verbose_name='专业类型')
    
    # 识别状态
    recognition_status = models.CharField(
        max_length=20,
        choices=[
            ('pending', '待识别'),
            ('recognized', '已识别'),
            ('manual', '手动录入'),
            ('failed', '识别失败'),
        ],
        default='pending',
        verbose_name='识别状态'
    )
    
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='uploaded_drawing_files',
        verbose_name='上传人'
    )
    uploaded_time = models.DateTimeField(default=timezone.now, verbose_name='上传时间')
    
    class Meta:
        db_table = 'production_quality_drawing_file'
        verbose_name = '图纸文件'
        verbose_name_plural = verbose_name
        ordering = ['-uploaded_time']
    
    def __str__(self):
        return f"{self.project.project_number} - {self.file_name}"


class ProjectTaskBreakdown(models.Model):
    """项目任务分解（WBS）"""
    
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='task_breakdowns',
        verbose_name='项目'
    )
    task_code = models.CharField(max_length=50, verbose_name='任务编码')
    task_name = models.CharField(max_length=200, verbose_name='任务名称')
    profession = models.ForeignKey(
        ServiceProfession,
        on_delete=models.PROTECT,
        related_name='task_breakdowns',
        verbose_name='所属专业'
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_task_breakdowns',
        verbose_name='分配人员'
    )
    task_content = models.TextField(verbose_name='任务内容')
    scope = models.JSONField(default=list, blank=True, verbose_name='任务范围（图纸区域）')
    building_area = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='建筑面积（㎡）'
    )
    saving_target_per_sqm = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='每平方米节省金额（元/㎡）'
    )
    saving_target = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='节省目标（元）'
    )
    planned_start_date = models.DateField(null=True, blank=True, verbose_name='计划开始日期')
    planned_end_date = models.DateField(null=True, blank=True, verbose_name='计划完成日期')
    order = models.IntegerField(default=0, verbose_name='排序')
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_task_breakdowns',
        verbose_name='创建人'
    )
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    updated_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        db_table = 'production_quality_task_breakdown'
        verbose_name = '任务分解'
        verbose_name_plural = verbose_name
        ordering = ['order', 'id']
        unique_together = ['project', 'task_code']
    
    def __str__(self):
        return f"{self.project.project_number} - {self.task_name}"
    
    def calculate_saving_target(self):
        """计算节省目标"""
        if self.building_area and self.saving_target_per_sqm:
            return self.building_area * self.saving_target_per_sqm
        return None


class ProjectStartupApproval(models.Model):
    """项目启动审批记录"""
    
    startup = models.ForeignKey(
        ProjectStartup,
        on_delete=models.CASCADE,
        related_name='approvals',
        verbose_name='生产启动'
    )
    approver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='startup_approvals',
        verbose_name='审批人'
    )
    approval_time = models.DateTimeField(null=True, blank=True, verbose_name='审批时间')
    decision = models.CharField(
        max_length=20,
        choices=[
            ('approved', '通过'),
            ('rejected', '驳回'),
            ('pending', '待审批'),
        ],
        default='pending',
        verbose_name='审批决定'
    )
    comment = models.TextField(blank=True, verbose_name='审批意见')
    attachments = models.JSONField(default=list, blank=True, verbose_name='附件列表')
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    
    class Meta:
        db_table = 'production_quality_startup_approval'
        verbose_name = '启动审批记录'
        verbose_name_plural = verbose_name
        ordering = ['-approval_time', '-created_time']
    
    def __str__(self):
        return f"{self.startup.project.project_number} - {self.get_decision_display()}"

