"""
档案管理模块数据模型
"""
from django.db import models
from django.utils import timezone
from django.db.models import Max
from django.core.validators import FileExtensionValidator, MinValueValidator, MaxValueValidator
from datetime import datetime
import os

from backend.apps.system_management.models import User, Department
from backend.apps.production_management.models import Project
from backend.apps.customer_management.models import Client
from backend.apps.delivery_customer.models import DeliveryRecord

# 尝试导入图纸相关模型（如果存在）
try:
    from backend.apps.production_management.models import ProjectDrawingFile, ProjectDrawingSubmission
except ImportError:
    ProjectDrawingFile = None
    ProjectDrawingSubmission = None

# 尝试导入文件分类模型（用于在档案管理中显示）
try:
    from backend.apps.delivery_customer.models import FileCategory as DeliveryFileCategory
    
    class FileCategory(DeliveryFileCategory):
        """文件分类（档案管理代理模型）"""
        class Meta:
            proxy = True
            app_label = 'archive_management'
            verbose_name = '文件分类'
            verbose_name_plural = '文件分类'
            ordering = ['stage', 'sort_order', 'name']
        
        def __str__(self):
            return f"{self.get_stage_display()} - {self.name}"
except (ImportError, AttributeError) as e:
    # 如果导入失败，创建一个占位符类
    FileCategory = None


# ==================== 文件上传路径 ====================

def archive_file_upload_path(instance, filename):
    """档案文件上传路径"""
    date_path = timezone.now().strftime('%Y/%m/%d')
    if hasattr(instance, 'archive_number'):
        return f'archive_files/{date_path}/{instance.archive_number}/{filename}'
    elif hasattr(instance, 'document_number'):
        return f'archive_files/{date_path}/{instance.document_number}/{filename}'
    else:
        return f'archive_files/{date_path}/{filename}'


# ==================== 档案分类 ====================

class ArchiveCategory(models.Model):
    """档案分类"""
    CATEGORY_TYPE_CHOICES = [
        ('project', '项目档案分类'),
        ('administrative', '行政档案分类'),
    ]
    
    SECURITY_LEVEL_CHOICES = [
        ('public', '公开'),
        ('internal', '内部'),
        ('confidential', '机密'),
        ('secret', '秘密'),
    ]
    
    name = models.CharField('分类名称', max_length=100)
    code = models.CharField('分类代码', max_length=50, unique=True)
    category_type = models.CharField('分类类型', max_length=20, choices=CATEGORY_TYPE_CHOICES)
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
        verbose_name='上级分类'
    )
    description = models.TextField('分类描述', blank=True)
    order = models.IntegerField('排序', default=0)
    icon = models.CharField('图标', max_length=50, blank=True)
    storage_period = models.IntegerField('保管期限(年)', default=10, help_text='单位：年')
    security_level = models.CharField('密级', max_length=20, choices=SECURITY_LEVEL_CHOICES, default='internal')
    is_active = models.BooleanField('是否启用', default=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='created_archive_categories', verbose_name='创建人')
    created_time = models.DateTimeField('创建时间', default=timezone.now)
    updated_time = models.DateTimeField('更新时间', auto_now=True)
    
    class Meta:
        db_table = 'archive_category'
        verbose_name = '档案分类'
        verbose_name_plural = verbose_name
        ordering = ['category_type', 'order', 'id']
        indexes = [
            models.Index(fields=['category_type', 'is_active']),
            models.Index(fields=['parent']),
        ]
    
    def __str__(self):
        return f"{self.get_category_type_display()} - {self.name}"
    
    @property
    def archive_count(self):
        """该分类下的档案数量"""
        if self.category_type == 'project':
            return ProjectArchiveDocument.objects.filter(category=self).count()
        else:
            return AdministrativeArchive.objects.filter(category=self).count()


class ArchiveCategoryRule(models.Model):
    """档案分类规则"""
    RULE_TYPE_CHOICES = [
        ('auto', '自动分类规则'),
        ('manual', '手动分类规则'),
    ]
    
    RULE_STATUS_CHOICES = [
        ('active', '启用'),
        ('inactive', '停用'),
        ('testing', '测试中'),
    ]
    
    name = models.CharField('规则名称', max_length=100)
    rule_type = models.CharField('规则类型', max_length=20, choices=RULE_TYPE_CHOICES, default='auto')
    category = models.ForeignKey(
        ArchiveCategory,
        on_delete=models.CASCADE,
        related_name='rules',
        verbose_name='目标分类'
    )
    priority = models.IntegerField('优先级', default=0, help_text='数字越大优先级越高')
    rule_expression = models.TextField('规则表达式', help_text='支持JSON格式的规则表达式')
    rule_conditions = models.JSONField('规则条件', default=dict, blank=True, help_text='规则条件配置')
    description = models.TextField('规则描述', blank=True)
    status = models.CharField('规则状态', max_length=20, choices=RULE_STATUS_CHOICES, default='active')
    is_active = models.BooleanField('是否启用', default=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='created_category_rules', verbose_name='创建人')
    created_time = models.DateTimeField('创建时间', default=timezone.now)
    updated_time = models.DateTimeField('更新时间', auto_now=True)
    
    class Meta:
        db_table = 'archive_category_rule'
        verbose_name = '档案分类规则'
        verbose_name_plural = verbose_name
        ordering = ['-priority', '-created_time']
        indexes = [
            models.Index(fields=['category', 'status']),
            models.Index(fields=['rule_type', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.category.name}"
    
    def test_rule(self, archive_data):
        """
        测试规则是否匹配
        archive_data: dict，包含档案数据的字典
        返回: bool，是否匹配
        
        规则条件格式示例：
        {
            "field": "project_name",
            "operator": "contains",
            "value": "测试"
        }
        或
        {
            "conditions": [
                {"field": "project_name", "operator": "contains", "value": "测试"},
                {"field": "status", "operator": "equals", "value": "completed"}
            ],
            "logic": "and"  # 或 "or"
        }
        """
        if not self.rule_conditions:
            # 如果没有规则条件，返回False
            return False
        
        try:
            import json
            
            # 解析规则表达式（如果存在）
            if self.rule_expression:
                try:
                    rule_expr = json.loads(self.rule_expression) if isinstance(self.rule_expression, str) else self.rule_expression
                except (json.JSONDecodeError, TypeError):
                    rule_expr = {}
            else:
                rule_expr = {}
            
            # 使用rule_conditions（优先）或rule_expression
            conditions = self.rule_conditions if self.rule_conditions else rule_expr
            
            if not conditions:
                return False
            
            # 处理单个条件
            if 'field' in conditions:
                return self._evaluate_condition(conditions, archive_data)
            
            # 处理多个条件（使用logic连接）
            if 'conditions' in conditions:
                logic = conditions.get('logic', 'and').lower()
                condition_list = conditions['conditions']
                
                if logic == 'and':
                    return all(self._evaluate_condition(cond, archive_data) for cond in condition_list)
                elif logic == 'or':
                    return any(self._evaluate_condition(cond, archive_data) for cond in condition_list)
                else:
                    return False
            
            return False
        except Exception:
            # 规则匹配出错时返回False
            return False
    
    def _evaluate_condition(self, condition, archive_data):
        """
        评估单个条件
        condition: dict，条件字典
        archive_data: dict，档案数据字典
        返回: bool，是否匹配
        """
        field = condition.get('field')
        operator = condition.get('operator', 'equals').lower()
        value = condition.get('value')
        
        if not field or value is None:
            return False
        
        # 获取字段值（支持嵌套字段，如 project.name）
        field_value = archive_data
        for key in field.split('.'):
            if isinstance(field_value, dict):
                field_value = field_value.get(key)
            elif hasattr(field_value, key):
                field_value = getattr(field_value, key, None)
            else:
                return False
            
            if field_value is None:
                return False
        
        # 根据操作符进行比较
        if operator == 'equals' or operator == '==':
            return str(field_value) == str(value)
        elif operator == 'not_equals' or operator == '!=':
            return str(field_value) != str(value)
        elif operator == 'contains':
            return str(value).lower() in str(field_value).lower()
        elif operator == 'not_contains':
            return str(value).lower() not in str(field_value).lower()
        elif operator == 'starts_with':
            return str(field_value).lower().startswith(str(value).lower())
        elif operator == 'ends_with':
            return str(field_value).lower().endswith(str(value).lower())
        elif operator == 'greater_than' or operator == '>':
            try:
                return float(field_value) > float(value)
            except (ValueError, TypeError):
                return False
        elif operator == 'less_than' or operator == '<':
            try:
                return float(field_value) < float(value)
            except (ValueError, TypeError):
                return False
        elif operator == 'greater_equal' or operator == '>=':
            try:
                return float(field_value) >= float(value)
            except (ValueError, TypeError):
                return False
        elif operator == 'less_equal' or operator == '<=':
            try:
                return float(field_value) <= float(value)
            except (ValueError, TypeError):
                return False
        elif operator == 'in':
            if isinstance(value, list):
                return str(field_value) in [str(v) for v in value]
            return str(field_value) in str(value)
        elif operator == 'not_in':
            if isinstance(value, list):
                return str(field_value) not in [str(v) for v in value]
            return str(field_value) not in str(value)
        else:
            # 未知操作符，默认使用equals
            return str(field_value) == str(value)


# ==================== 项目档案 ====================

class ArchiveProjectArchive(models.Model):
    """项目归档（档案管理模块）"""
    ARCHIVE_STATUS_CHOICES = [
        ('pending', '待归档'),
        ('approving', '归档审批中'),
        ('archiving', '归档执行中'),
        ('archived', '已归档'),
        ('rejected', '归档驳回'),
    ]
    
    archive_number = models.CharField('归档编号', max_length=100, unique=True, db_index=True)
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='archive_records',
        verbose_name='关联项目',
        db_constraint=True
    )
    archive_reason = models.TextField('归档原因', blank=True)
    archive_description = models.TextField('归档说明', blank=True)
    status = models.CharField('归档状态', max_length=20, choices=ARCHIVE_STATUS_CHOICES, default='pending')
    
    # 归档申请人
    applicant = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='applied_project_archives',
        verbose_name='归档申请人'
    )
    applied_time = models.DateTimeField('申请时间', default=timezone.now)
    
    # 归档执行人
    executor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='executed_project_archives',
        verbose_name='归档执行人'
    )
    executed_time = models.DateTimeField('执行时间', null=True, blank=True)
    
    # 归档确认
    confirmed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='confirmed_project_archives',
        verbose_name='确认人'
    )
    confirmed_time = models.DateTimeField('确认时间', null=True, blank=True)
    
    # 归档文件清单（JSON格式存储文件列表）
    file_list = models.JSONField('归档文件清单', default=list, blank=True)
    
    created_time = models.DateTimeField('创建时间', default=timezone.now)
    updated_time = models.DateTimeField('更新时间', auto_now=True)
    
    class Meta:
        db_table = 'archive_project_archive'
        verbose_name = '项目归档（档案管理）'
        verbose_name_plural = verbose_name
        ordering = ['-created_time']
        indexes = [
            models.Index(fields=['project', 'status']),
            models.Index(fields=['archive_number']),
            models.Index(fields=['status', '-created_time']),
        ]
    
    def __str__(self):
        return f"{self.archive_number} - {self.project.project_name if self.project else 'N/A'}"
    
    def generate_archive_number(self):
        """生成归档编号：ARCH-PROJ-{YYYYMMDD}-{序列号}"""
        date_str = timezone.now().strftime('%Y%m%d')
        prefix = f'ARCH-PROJ-{date_str}-'
        last_record = ArchiveProjectArchive.objects.filter(
            archive_number__startswith=prefix
        ).order_by('-archive_number').first()
        
        if last_record:
            try:
                seq = int(last_record.archive_number.split('-')[-1]) + 1
            except (ValueError, IndexError):
                seq = 1
        else:
            seq = 1
        
        return f"{prefix}{seq:04d}"
    
    def save(self, *args, **kwargs):
        if not self.archive_number:
            self.archive_number = self.generate_archive_number()
        super().save(*args, **kwargs)


class ProjectArchiveDocument(models.Model):
    """项目档案文档"""
    DOCUMENT_TYPE_CHOICES = [
        ('project_doc', '项目文档'),
        ('drawing', '图纸'),
        ('delivery_file', '交付文件'),
        ('process_file', '过程文件'),
        ('other', '其他'),
    ]
    
    DOCUMENT_STATUS_CHOICES = [
        ('draft', '草稿'),
        ('pending_archive', '待归档'),
        ('archived', '已归档'),
        ('borrowed', '已借出'),
    ]
    
    document_number = models.CharField('文档编号', max_length=100, unique=True, db_index=True)
    document_name = models.CharField('文档名称', max_length=200)
    document_type = models.CharField('文档类型', max_length=20, choices=DOCUMENT_TYPE_CHOICES)
    category = models.ForeignKey(
        ArchiveCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='project_documents',
        verbose_name='档案分类',
        limit_choices_to={'category_type': 'project'}
    )
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='archive_documents',
        verbose_name='关联项目',
        db_constraint=True
    )
    project_archive = models.ForeignKey(
        'ArchiveProjectArchive',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='documents',
        verbose_name='项目归档记录'
    )
    
    # 文件信息
    file = models.FileField(
        '文件',
        upload_to=archive_file_upload_path,
        validators=[
            FileExtensionValidator(
                allowed_extensions=['pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx',
                                  'dwg', 'dgn', 'jpg', 'jpeg', 'png', 'zip', 'rar', '7z']
            )
        ],
        max_length=500
    )
    file_name = models.CharField('原始文件名', max_length=255)
    file_size = models.BigIntegerField('文件大小(字节)')
    file_extension = models.CharField('文件扩展名', max_length=20, blank=True)
    mime_type = models.CharField('MIME类型', max_length=100, blank=True)
    
    # 文档描述
    description = models.TextField('文档描述', blank=True)
    tags = models.CharField('标签', max_length=500, blank=True, help_text='多个标签用逗号分隔')
    security_level = models.CharField('密级', max_length=20, choices=ArchiveCategory.SECURITY_LEVEL_CHOICES, default='internal')
    
    # 版本管理
    version = models.CharField('版本号', max_length=50, default='1.0')
    parent_version = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='child_versions',
        verbose_name='父版本'
    )
    
    status = models.CharField('文档状态', max_length=20, choices=DOCUMENT_STATUS_CHOICES, default='draft')
    
    uploaded_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='uploaded_project_documents', verbose_name='上传人')
    uploaded_time = models.DateTimeField('上传时间', default=timezone.now)
    updated_time = models.DateTimeField('更新时间', auto_now=True)
    
    class Meta:
        db_table = 'project_archive_document'
        verbose_name = '项目档案文档'
        verbose_name_plural = verbose_name
        ordering = ['-uploaded_time']
        indexes = [
            models.Index(fields=['project', 'status']),
            models.Index(fields=['category', 'status']),
            models.Index(fields=['document_number']),
        ]
    
    def __str__(self):
        return f"{self.document_number} - {self.document_name}"
    
    def generate_document_number(self):
        """生成文档编号：DOC-{YYYYMMDD}-{序列号}"""
        date_str = timezone.now().strftime('%Y%m%d')
        prefix = f'DOC-{date_str}-'
        last_record = ProjectArchiveDocument.objects.filter(
            document_number__startswith=prefix
        ).order_by('-document_number').first()
        
        if last_record:
            try:
                seq = int(last_record.document_number.split('-')[-1]) + 1
            except (ValueError, IndexError):
                seq = 1
        else:
            seq = 1
        
        return f"{prefix}{seq:04d}"
    
    def save(self, *args, **kwargs):
        if not self.document_number:
            self.document_number = self.generate_document_number()
        super().save(*args, **kwargs)


# ==================== 交付推送记录 ====================

class ArchivePushRecord(models.Model):
    """交付推送记录（记录从收发管理模块推送的文件）"""
    PUSH_STATUS_CHOICES = [
        ('pending', '待推送'),
        ('success', '推送成功'),
        ('failed', '推送失败'),
        ('retrying', '重试中'),
    ]
    
    delivery_record = models.ForeignKey(
        DeliveryRecord,
        on_delete=models.CASCADE,
        related_name='archive_push_records',
        verbose_name='交付记录',
        db_constraint=True
    )
    project = models.ForeignKey(
        Project,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='archive_push_records',
        verbose_name='关联项目',
        db_constraint=True
    )
    push_status = models.CharField('推送状态', max_length=20, choices=PUSH_STATUS_CHOICES, default='pending')
    push_time = models.DateTimeField('推送时间', null=True, blank=True)
    receive_time = models.DateTimeField('接收时间', null=True, blank=True)
    error_message = models.TextField('错误信息', blank=True)
    retry_count = models.IntegerField('重试次数', default=0)
    
    # 推送的文件列表（JSON格式）
    pushed_files = models.JSONField('推送文件列表', default=list, blank=True)
    
    created_time = models.DateTimeField('创建时间', default=timezone.now)
    updated_time = models.DateTimeField('更新时间', auto_now=True)
    
    class Meta:
        db_table = 'archive_push_record'
        verbose_name = '交付推送记录'
        verbose_name_plural = verbose_name
        ordering = ['-created_time']
        indexes = [
            models.Index(fields=['delivery_record', 'push_status']),
            models.Index(fields=['project', 'push_status']),
        ]
    
    def __str__(self):
        return f"{self.delivery_record.delivery_number} - {self.get_push_status_display()}"


# ==================== 图纸归档 ====================

class ProjectDrawingArchive(models.Model):
    """项目图纸归档"""
    ARCHIVE_STATUS_CHOICES = [
        ('pending', '待归档'),
        ('approving', '归档审批中'),
        ('archiving', '归档执行中'),
        ('archived', '已归档'),
        ('rejected', '归档驳回'),
    ]
    
    ARCHIVE_TYPE_CHOICES = [
        ('all', '全部图纸'),
        ('submission', '按提交归档'),
        ('category', '按分类归档'),
        ('custom', '自定义选择'),
    ]
    
    archive_number = models.CharField('归档编号', max_length=100, unique=True, db_index=True)
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='drawing_archives',
        verbose_name='关联项目',
        db_constraint=True
    )
    
    archive_type = models.CharField('归档类型', max_length=20, choices=ARCHIVE_TYPE_CHOICES, default='all')
    archive_reason = models.TextField('归档原因', blank=True)
    archive_description = models.TextField('归档说明', blank=True)
    status = models.CharField('归档状态', max_length=20, choices=ARCHIVE_STATUS_CHOICES, default='pending')
    
    # 归档的图纸提交ID列表（JSON格式）
    drawing_submission_ids = models.JSONField('图纸提交ID列表', default=list, blank=True)
    # 归档的图纸文件ID列表（JSON格式）
    drawing_file_ids = models.JSONField('图纸文件ID列表', default=list, blank=True)
    
    # 归档申请人
    applicant = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='applied_drawing_archives',
        verbose_name='归档申请人'
    )
    applied_time = models.DateTimeField('申请时间', default=timezone.now)
    
    # 归档执行人
    executor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='executed_drawing_archives',
        verbose_name='归档执行人'
    )
    executed_time = models.DateTimeField('执行时间', null=True, blank=True)
    
    # 归档确认
    confirmed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='confirmed_drawing_archives',
        verbose_name='确认人'
    )
    confirmed_time = models.DateTimeField('确认时间', null=True, blank=True)
    
    # 归档分类
    category = models.ForeignKey(
        ArchiveCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='drawing_archives',
        verbose_name='归档分类'
    )
    
    created_time = models.DateTimeField('创建时间', default=timezone.now)
    updated_time = models.DateTimeField('更新时间', auto_now=True)
    
    class Meta:
        db_table = 'archive_project_drawing_archive'
        verbose_name = '项目图纸归档'
        verbose_name_plural = verbose_name
        ordering = ['-created_time']
        indexes = [
            models.Index(fields=['project', 'status']),
            models.Index(fields=['archive_number']),
            models.Index(fields=['status', '-created_time']),
        ]
    
    def __str__(self):
        return f"{self.archive_number} - {self.project.project_name if self.project else 'N/A'}"
    
    def generate_archive_number(self):
        """生成归档编号：ARCH-DRAW-{YYYYMMDD}-{序列号}"""
        date_str = timezone.now().strftime('%Y%m%d')
        prefix = f'ARCH-DRAW-{date_str}-'
        last_record = ProjectDrawingArchive.objects.filter(
            archive_number__startswith=prefix
        ).order_by('-archive_number').first()
        
        if last_record:
            try:
                seq = int(last_record.archive_number.split('-')[-1]) + 1
            except (ValueError, IndexError):
                seq = 1
        else:
            seq = 1
        
        return f"{prefix}{seq:04d}"
    
    def save(self, *args, **kwargs):
        if not self.archive_number:
            self.archive_number = self.generate_archive_number()
        super().save(*args, **kwargs)
    
    def get_drawing_submissions(self):
        """获取归档的图纸提交"""
        if not self.drawing_submission_ids:
            return []
        try:
            if ProjectDrawingSubmission:
                return ProjectDrawingSubmission.objects.filter(id__in=self.drawing_submission_ids)
        except:
            pass
        return []
    
    def get_drawing_files(self):
        """获取归档的图纸文件"""
        if not self.drawing_file_ids:
            return []
        try:
            if ProjectDrawingFile:
                return ProjectDrawingFile.objects.filter(id__in=self.drawing_file_ids)
        except:
            pass
        return []
    
    @property
    def drawing_count(self):
        """图纸数量"""
        return len(self.drawing_file_ids) if self.drawing_file_ids else 0


# ==================== 行政档案 ====================

class ProjectDeliveryArchive(models.Model):
    """交付归档记录（手动归档）"""
    ARCHIVE_STATUS_CHOICES = [
        ('pending', '待归档'),
        ('approving', '归档审批中'),
        ('archiving', '归档执行中'),
        ('archived', '已归档'),
        ('rejected', '归档驳回'),
    ]
    
    archive_number = models.CharField('归档编号', max_length=100, unique=True, db_index=True)
    
    # 关联交付记录
    delivery_record = models.ForeignKey(
        DeliveryRecord,
        on_delete=models.CASCADE,
        related_name='manual_archive_records',
        verbose_name='交付记录',
        db_constraint=True
    )
    project = models.ForeignKey(
        Project,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='delivery_archives',
        verbose_name='关联项目',
        db_constraint=True
    )
    
    archive_reason = models.TextField('归档原因', blank=True)
    archive_description = models.TextField('归档说明', blank=True)
    status = models.CharField('归档状态', max_length=20, choices=ARCHIVE_STATUS_CHOICES, default='pending')
    
    # 归档申请人
    applicant = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='applied_delivery_archives',
        verbose_name='归档申请人'
    )
    applied_time = models.DateTimeField('申请时间', default=timezone.now)
    
    # 归档执行人
    executor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='executed_delivery_archives',
        verbose_name='归档执行人'
    )
    executed_time = models.DateTimeField('执行时间', null=True, blank=True)
    
    # 归档确认
    confirmed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='confirmed_delivery_archives',
        verbose_name='确认人'
    )
    confirmed_time = models.DateTimeField('确认时间', null=True, blank=True)
    
    # 归档分类
    category = models.ForeignKey(
        ArchiveCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='delivery_archives',
        verbose_name='归档分类'
    )
    
    created_time = models.DateTimeField('创建时间', default=timezone.now)
    updated_time = models.DateTimeField('更新时间', auto_now=True)
    
    class Meta:
        db_table = 'archive_project_delivery_archive'
        verbose_name = '交付归档（手动）'
        verbose_name_plural = verbose_name
        ordering = ['-created_time']
        indexes = [
            models.Index(fields=['delivery_record', 'status']),
            models.Index(fields=['project', 'status']),
            models.Index(fields=['archive_number']),
            models.Index(fields=['status', '-created_time']),
        ]
    
    def __str__(self):
        return f"{self.archive_number} - {self.delivery_record.delivery_number if self.delivery_record else 'N/A'}"
    
    def generate_archive_number(self):
        """生成归档编号：ARCH-DELIV-{YYYYMMDD}-{序列号}"""
        date_str = timezone.now().strftime('%Y%m%d')
        prefix = f'ARCH-DELIV-{date_str}-'
        last_record = ProjectDeliveryArchive.objects.filter(
            archive_number__startswith=prefix
        ).order_by('-archive_number').first()
        
        if last_record:
            try:
                seq = int(last_record.archive_number.split('-')[-1]) + 1
            except (ValueError, IndexError):
                seq = 1
        else:
            seq = 1
        
        return f"{prefix}{seq:04d}"
    
    def save(self, *args, **kwargs):
        if not self.archive_number:
            self.archive_number = self.generate_archive_number()
        # 自动设置项目
        if self.delivery_record and self.delivery_record.project and not self.project:
            self.project = self.delivery_record.project
        super().save(*args, **kwargs)


class AdministrativeArchive(models.Model):
    """行政档案"""
    ARCHIVE_STATUS_CHOICES = [
        ('pending', '待归档'),
        ('approving', '归档审批中'),
        ('archived', '已归档'),
        ('borrowed', '已借出'),
        ('destroyed', '已销毁'),
        ('rejected', '归档驳回'),
    ]
    
    archive_number = models.CharField('档案编号', max_length=100, unique=True, db_index=True)
    archive_name = models.CharField('档案名称', max_length=200)
    category = models.ForeignKey(
        ArchiveCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='administrative_archives',
        verbose_name='档案分类',
        limit_choices_to={'category_type': 'administrative'}
    )
    archive_date = models.DateField('归档日期', default=timezone.now)
    archive_department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='archives',
        verbose_name='归档部门'
    )
    archivist = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='archived_administrative_archives',
        verbose_name='归档人'
    )
    description = models.TextField('档案描述', blank=True)
    security_level = models.CharField('密级', max_length=20, choices=ArchiveCategory.SECURITY_LEVEL_CHOICES, default='internal')
    storage_period = models.IntegerField('保管期限(年)', default=10)
    
    # 文件信息（JSON格式存储文件列表）
    files = models.JSONField('档案文件', default=list, blank=True)
    
    # 档案著录信息（JSON格式）
    cataloging_info = models.JSONField('著录信息', default=dict, blank=True)
    
    status = models.CharField('档案状态', max_length=20, choices=ARCHIVE_STATUS_CHOICES, default='pending')
    
    # 库房位置
    storage_room = models.ForeignKey(
        'ArchiveStorageRoom',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='archives',
        verbose_name='库房'
    )
    location = models.ForeignKey(
        'ArchiveLocation',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='archives',
        verbose_name='位置'
    )
    
    created_time = models.DateTimeField('创建时间', default=timezone.now)
    updated_time = models.DateTimeField('更新时间', auto_now=True)
    
    class Meta:
        db_table = 'administrative_archive'
        verbose_name = '行政档案'
        verbose_name_plural = verbose_name
        ordering = ['-created_time']
        indexes = [
            models.Index(fields=['category', 'status']),
            models.Index(fields=['archive_number']),
            models.Index(fields=['status', '-created_time']),
        ]
    
    def __str__(self):
        return f"{self.archive_number} - {self.archive_name}"
    
    def generate_archive_number(self):
        """生成档案编号：ARCH-{YYYYMMDD}-{序列号}"""
        date_str = timezone.now().strftime('%Y%m%d')
        prefix = f'ARCH-{date_str}-'
        last_record = AdministrativeArchive.objects.filter(
            archive_number__startswith=prefix
        ).order_by('-archive_number').first()
        
        if last_record:
            try:
                seq = int(last_record.archive_number.split('-')[-1]) + 1
            except (ValueError, IndexError):
                seq = 1
        else:
            seq = 1
        
        return f"{prefix}{seq:04d}"
    
    def save(self, *args, **kwargs):
        if not self.archive_number:
            self.archive_number = self.generate_archive_number()
        super().save(*args, **kwargs)


# ==================== 档案借阅 ====================

class ArchiveBorrow(models.Model):
    """档案借阅"""
    BORROW_STATUS_CHOICES = [
        ('pending', '待审批'),
        ('approving', '审批中'),
        ('approved', '已批准'),
        ('out', '已出库'),
        ('returned', '已归还'),
        ('rejected', '已拒绝'),
        ('overdue', '已逾期'),
    ]
    
    BORROW_METHOD_CHOICES = [
        ('onsite', '现场查阅'),
        ('borrow', '借出'),
        ('copy', '复印'),
        ('scan', '扫描'),
    ]
    
    borrow_number = models.CharField('借阅单号', max_length=100, unique=True, db_index=True)
    
    # 借阅档案（支持项目档案和行政档案）
    project_document = models.ForeignKey(
        ProjectArchiveDocument,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='borrows',
        verbose_name='项目档案文档'
    )
    administrative_archive = models.ForeignKey(
        AdministrativeArchive,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='borrows',
        verbose_name='行政档案'
    )
    
    borrow_reason = models.TextField('借阅事由')
    borrow_date = models.DateField('借阅日期', default=timezone.now)
    return_date = models.DateField('归还日期')
    borrower = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='borrowed_archives',
        verbose_name='借阅人'
    )
    borrower_department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='borrowed_archives',
        verbose_name='借阅部门'
    )
    borrow_purpose = models.CharField('借阅用途', max_length=200, blank=True)
    borrow_method = models.CharField('借阅方式', max_length=20, choices=BORROW_METHOD_CHOICES, default='onsite')
    
    status = models.CharField('借阅状态', max_length=20, choices=BORROW_STATUS_CHOICES, default='pending')
    
    # 审批信息
    approver = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_borrows',
        verbose_name='审批人'
    )
    approved_time = models.DateTimeField('审批时间', null=True, blank=True)
    approval_opinion = models.TextField('审批意见', blank=True)
    
    # 出库信息
    out_time = models.DateTimeField('出库时间', null=True, blank=True)
    out_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='out_archives',
        verbose_name='出库人'
    )
    
    # 归还信息
    returned_time = models.DateTimeField('归还时间', null=True, blank=True)
    returned_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='returned_archives',
        verbose_name='归还人'
    )
    return_status = models.CharField('归还状态', max_length=50, blank=True, help_text='完好/损坏/缺失')
    return_notes = models.TextField('归还备注', blank=True)
    
    created_time = models.DateTimeField('创建时间', default=timezone.now)
    updated_time = models.DateTimeField('更新时间', auto_now=True)
    
    class Meta:
        db_table = 'archive_borrow'
        verbose_name = '档案借阅'
        verbose_name_plural = verbose_name
        ordering = ['-created_time']
        indexes = [
            models.Index(fields=['borrower', 'status']),
            models.Index(fields=['borrow_number']),
            models.Index(fields=['status', '-created_time']),
        ]
    
    def __str__(self):
        archive_name = ''
        if self.project_document:
            archive_name = self.project_document.document_name
        elif self.administrative_archive:
            archive_name = self.administrative_archive.archive_name
        return f"{self.borrow_number} - {archive_name}"
    
    def generate_borrow_number(self):
        """生成借阅单号：BOR-{YYYYMMDD}-{序列号}"""
        date_str = timezone.now().strftime('%Y%m%d')
        prefix = f'BOR-{date_str}-'
        last_record = ArchiveBorrow.objects.filter(
            borrow_number__startswith=prefix
        ).order_by('-borrow_number').first()
        
        if last_record:
            try:
                seq = int(last_record.borrow_number.split('-')[-1]) + 1
            except (ValueError, IndexError):
                seq = 1
        else:
            seq = 1
        
        return f"{prefix}{seq:04d}"
    
    def save(self, *args, **kwargs):
        if not self.borrow_number:
            self.borrow_number = self.generate_borrow_number()
        super().save(*args, **kwargs)
    
    @property
    def is_overdue(self):
        """是否逾期"""
        if self.status in ['out', 'approved'] and self.return_date:
            return timezone.now().date() > self.return_date
        return False


# ==================== 档案销毁 ====================

class ArchiveDestroy(models.Model):
    """档案销毁"""
    DESTROY_STATUS_CHOICES = [
        ('pending', '待审批'),
        ('approving', '审批中'),
        ('approved', '已批准'),
        ('destroyed', '已销毁'),
        ('rejected', '已拒绝'),
    ]
    
    DESTROY_METHOD_CHOICES = [
        ('shred', '粉碎'),
        ('burn', '焚烧'),
        ('delete', '删除'),
        ('other', '其他'),
    ]
    
    destroy_number = models.CharField('销毁单号', max_length=100, unique=True, db_index=True)
    
    # 销毁档案（支持项目档案和行政档案）
    project_document = models.ForeignKey(
        ProjectArchiveDocument,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='destroys',
        verbose_name='项目档案文档'
    )
    administrative_archive = models.ForeignKey(
        AdministrativeArchive,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='destroys',
        verbose_name='行政档案'
    )
    
    destroy_reason = models.TextField('销毁原因')
    destroy_date = models.DateField('销毁日期', default=timezone.now)
    destroyer = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='destroyed_archives',
        verbose_name='销毁人'
    )
    destroy_method = models.CharField('销毁方式', max_length=20, choices=DESTROY_METHOD_CHOICES, default='shred')
    destroy_basis = models.CharField('销毁依据', max_length=500, blank=True)
    
    status = models.CharField('销毁状态', max_length=20, choices=DESTROY_STATUS_CHOICES, default='pending')
    
    # 审批信息
    approver = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_destroys',
        verbose_name='审批人'
    )
    approved_time = models.DateTimeField('审批时间', null=True, blank=True)
    approval_opinion = models.TextField('审批意见', blank=True)
    
    # 销毁执行信息
    destroyed_time = models.DateTimeField('销毁时间', null=True, blank=True)
    destroy_record = models.TextField('销毁记录', blank=True)
    destroy_proof = models.ImageField('销毁证明', upload_to='archive_destroy_proofs/', blank=True)
    destroy_photos = models.JSONField('销毁照片', default=list, blank=True)
    
    created_time = models.DateTimeField('创建时间', default=timezone.now)
    updated_time = models.DateTimeField('更新时间', auto_now=True)
    
    class Meta:
        db_table = 'archive_destroy'
        verbose_name = '档案销毁'
        verbose_name_plural = verbose_name
        ordering = ['-created_time']
        indexes = [
            models.Index(fields=['destroyer', 'status']),
            models.Index(fields=['destroy_number']),
        ]
    
    def __str__(self):
        archive_name = ''
        if self.project_document:
            archive_name = self.project_document.document_name
        elif self.administrative_archive:
            archive_name = self.administrative_archive.archive_name
        return f"{self.destroy_number} - {archive_name}"
    
    def generate_destroy_number(self):
        """生成销毁单号：DES-{YYYYMMDD}-{序列号}"""
        date_str = timezone.now().strftime('%Y%m%d')
        prefix = f'DES-{date_str}-'
        last_record = ArchiveDestroy.objects.filter(
            destroy_number__startswith=prefix
        ).order_by('-destroy_number').first()
        
        if last_record:
            try:
                seq = int(last_record.destroy_number.split('-')[-1]) + 1
            except (ValueError, IndexError):
                seq = 1
        else:
            seq = 1
        
        return f"{prefix}{seq:04d}"
    
    def save(self, *args, **kwargs):
        if not self.destroy_number:
            self.destroy_number = self.generate_destroy_number()
        super().save(*args, **kwargs)


# ==================== 档案库管理 ====================

class ArchiveStorageRoom(models.Model):
    """档案库房"""
    STATUS_CHOICES = [
        ('active', '启用'),
        ('inactive', '停用'),
        ('maintenance', '维护中'),
    ]
    
    room_number = models.CharField('库房编号', max_length=50, unique=True)
    room_name = models.CharField('库房名称', max_length=200)
    location = models.CharField('库房位置', max_length=500)
    area = models.DecimalField('库房面积(平方米)', max_digits=10, decimal_places=2, null=True, blank=True)
    capacity = models.IntegerField('库房容量(卷)', null=True, blank=True)
    manager = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='managed_storage_rooms',
        verbose_name='库房负责人'
    )
    description = models.TextField('库房描述', blank=True)
    status = models.CharField('库房状态', max_length=20, choices=STATUS_CHOICES, default='active')
    
    created_time = models.DateTimeField('创建时间', default=timezone.now)
    updated_time = models.DateTimeField('更新时间', auto_now=True)
    
    class Meta:
        db_table = 'archive_storage_room'
        verbose_name = '档案库房'
        verbose_name_plural = verbose_name
        ordering = ['room_number']
        indexes = [
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.room_number} - {self.room_name}"
    
    @property
    def archive_count(self):
        """库房中的档案数量"""
        return AdministrativeArchive.objects.filter(storage_room=self).count()
    
    @property
    def usage_rate(self):
        """使用率"""
        if self.capacity and self.capacity > 0:
            return (self.archive_count / self.capacity) * 100
        return 0


class ArchiveLocation(models.Model):
    """档案位置（架位）"""
    LOCATION_TYPE_CHOICES = [
        ('shelf', '架位'),
        ('cabinet', '柜位'),
        ('box', '箱位'),
        ('other', '其他'),
    ]
    
    location_number = models.CharField('位置编号', max_length=50)
    location_name = models.CharField('位置名称', max_length=200)
    storage_room = models.ForeignKey(
        ArchiveStorageRoom,
        on_delete=models.CASCADE,
        related_name='locations',
        verbose_name='所属库房',
        db_constraint=True
    )
    location_type = models.CharField('位置类型', max_length=20, choices=LOCATION_TYPE_CHOICES, default='shelf')
    capacity = models.IntegerField('位置容量(卷)', null=True, blank=True)
    description = models.TextField('位置描述', blank=True)
    
    created_time = models.DateTimeField('创建时间', default=timezone.now)
    updated_time = models.DateTimeField('更新时间', auto_now=True)
    
    class Meta:
        db_table = 'archive_location'
        verbose_name = '档案位置'
        verbose_name_plural = verbose_name
        ordering = ['storage_room', 'location_number']
        unique_together = ('storage_room', 'location_number')
        indexes = [
            models.Index(fields=['storage_room', 'location_type']),
        ]
    
    def __str__(self):
        return f"{self.storage_room.room_number}-{self.location_number} - {self.location_name}"
    
    @property
    def archive_count(self):
        """位置中的档案数量"""
        return AdministrativeArchive.objects.filter(location=self).count()
    
    @property
    def usage_rate(self):
        """使用率"""
        if self.capacity and self.capacity > 0:
            return (self.archive_count / self.capacity) * 100
        return 0


class ArchiveShelf(models.Model):
    """档案上架记录"""
    archive = models.ForeignKey(
        AdministrativeArchive,
        on_delete=models.CASCADE,
        related_name='shelf_records',
        verbose_name='档案',
        db_constraint=True
    )
    location = models.ForeignKey(
        ArchiveLocation,
        on_delete=models.CASCADE,
        related_name='shelf_records',
        verbose_name='位置',
        db_constraint=True
    )
    shelf_time = models.DateTimeField('上架时间', default=timezone.now)
    shelf_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='shelved_archives',
        verbose_name='上架人'
    )
    notes = models.TextField('备注', blank=True)
    
    class Meta:
        db_table = 'archive_shelf'
        verbose_name = '档案上架记录'
        verbose_name_plural = verbose_name
        ordering = ['-shelf_time']
        indexes = [
            models.Index(fields=['archive', 'location']),
        ]
    
    def __str__(self):
        return f"{self.archive.archive_number} - {self.location.location_number}"


class ArchiveInventory(models.Model):
    """档案盘点"""
    INVENTORY_TYPE_CHOICES = [
        ('full', '全面盘点'),
        ('sample', '抽样盘点'),
        ('key', '重点盘点'),
    ]
    
    inventory_number = models.CharField('盘点单号', max_length=100, unique=True, db_index=True)
    inventory_name = models.CharField('盘点名称', max_length=200)
    inventory_type = models.CharField('盘点方式', max_length=20, choices=INVENTORY_TYPE_CHOICES, default='full')
    inventory_date = models.DateField('盘点日期', default=timezone.now)
    inventory_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='inventoried_archives',
        verbose_name='盘点人'
    )
    
    # 盘点范围
    storage_room = models.ForeignKey(
        ArchiveStorageRoom,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='inventories',
        verbose_name='库房'
    )
    category = models.ForeignKey(
        ArchiveCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='inventories',
        verbose_name='分类'
    )
    date_range_start = models.DateField('日期范围开始', null=True, blank=True)
    date_range_end = models.DateField('日期范围结束', null=True, blank=True)
    
    # 盘点结果
    total_count = models.IntegerField('应盘数量', default=0)
    actual_count = models.IntegerField('实盘数量', default=0)
    difference_count = models.IntegerField('差异数量', default=0)
    difference_details = models.JSONField('差异明细', default=list, blank=True)
    
    notes = models.TextField('备注', blank=True)
    
    created_time = models.DateTimeField('创建时间', default=timezone.now)
    updated_time = models.DateTimeField('更新时间', auto_now=True)
    
    class Meta:
        db_table = 'archive_inventory'
        verbose_name = '档案盘点'
        verbose_name_plural = verbose_name
        ordering = ['-created_time']
        indexes = [
            models.Index(fields=['inventory_number']),
            models.Index(fields=['inventory_date']),
        ]
    
    def __str__(self):
        return f"{self.inventory_number} - {self.inventory_name}"
    
    def generate_inventory_number(self):
        """生成盘点单号：INV-{YYYYMMDD}-{序列号}"""
        date_str = timezone.now().strftime('%Y%m%d')
        prefix = f'INV-{date_str}-'
        last_record = ArchiveInventory.objects.filter(
            inventory_number__startswith=prefix
        ).order_by('-inventory_number').first()
        
        if last_record:
            try:
                seq = int(last_record.inventory_number.split('-')[-1]) + 1
            except (ValueError, IndexError):
                seq = 1
        else:
            seq = 1
        
        return f"{prefix}{seq:04d}"
    
    def save(self, *args, **kwargs):
        if not self.inventory_number:
            self.inventory_number = self.generate_inventory_number()
        if self.actual_count and self.total_count:
            self.difference_count = self.actual_count - self.total_count
        super().save(*args, **kwargs)


# ==================== 档案数字化 ====================

class ArchiveDigitizationApply(models.Model):
    """档案数字化申请"""
    DIGITIZATION_TYPE_CHOICES = [
        ('scan', '扫描'),
        ('ocr', 'OCR识别'),
        ('format_convert', '格式转换'),
        ('video_convert', '视频转换'),
        ('audio_convert', '音频转换'),
        ('other', '其他'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', '低'),
        ('normal', '普通'),
        ('high', '高'),
        ('urgent', '紧急'),
    ]
    
    STATUS_CHOICES = [
        ('pending', '待审批'),
        ('approved', '已批准'),
        ('rejected', '已驳回'),
        ('processing', '处理中'),
        ('completed', '已完成'),
        ('cancelled', '已取消'),
    ]
    
    apply_number = models.CharField('申请编号', max_length=100, unique=True, db_index=True)
    
    # 关联的档案（项目文档或行政档案）
    project_document = models.ForeignKey(
        ProjectArchiveDocument,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='digitization_applies',
        verbose_name='项目文档',
        db_constraint=True
    )
    administrative_archive = models.ForeignKey(
        AdministrativeArchive,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='digitization_applies',
        verbose_name='行政档案',
        db_constraint=True
    )
    
    digitization_type = models.CharField('数字化类型', max_length=30, choices=DIGITIZATION_TYPE_CHOICES)
    priority = models.CharField('优先级', max_length=20, choices=PRIORITY_CHOICES, default='normal')
    apply_reason = models.TextField('申请原因', blank=True)
    apply_description = models.TextField('申请说明', blank=True)
    
    # 申请信息
    applicant = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='digitization_applies',
        verbose_name='申请人'
    )
    applied_time = models.DateTimeField('申请时间', default=timezone.now)
    
    # 审批信息
    approver = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_digitization_applies',
        verbose_name='审批人'
    )
    approved_time = models.DateTimeField('审批时间', null=True, blank=True)
    approval_opinion = models.TextField('审批意见', blank=True)
    
    status = models.CharField('申请状态', max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # 处理信息
    processor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='processed_digitization_applies',
        verbose_name='处理人'
    )
    process_start_time = models.DateTimeField('处理开始时间', null=True, blank=True)
    process_end_time = models.DateTimeField('处理结束时间', null=True, blank=True)
    
    # 额外信息（JSON格式）
    extra_data = models.JSONField('额外信息', default=dict, blank=True)
    
    created_time = models.DateTimeField('创建时间', default=timezone.now)
    updated_time = models.DateTimeField('更新时间', auto_now=True)
    
    class Meta:
        db_table = 'archive_digitization_apply'
        verbose_name = '档案数字化申请'
        verbose_name_plural = verbose_name
        ordering = ['-created_time']
        indexes = [
            models.Index(fields=['status', '-created_time']),
            models.Index(fields=['applicant', '-created_time']),
            models.Index(fields=['digitization_type', 'status']),
        ]
    
    def __str__(self):
        archive_name = ''
        if self.project_document:
            archive_name = self.project_document.document_name
        elif self.administrative_archive:
            archive_name = self.administrative_archive.archive_name
        return f"{self.apply_number} - {archive_name}"
    
    def generate_apply_number(self):
        """生成申请编号：DIG-APPLY-{YYYYMMDD}-{序列号}"""
        date_str = timezone.now().strftime('%Y%m%d')
        prefix = f'DIG-APPLY-{date_str}-'
        last_record = ArchiveDigitizationApply.objects.filter(
            apply_number__startswith=prefix
        ).order_by('-apply_number').first()
        
        if last_record:
            try:
                seq = int(last_record.apply_number.split('-')[-1]) + 1
            except (ValueError, IndexError):
                seq = 1
        else:
            seq = 1
        
        return f"{prefix}{seq:04d}"
    
    def save(self, *args, **kwargs):
        if not self.apply_number:
            self.apply_number = self.generate_apply_number()
        super().save(*args, **kwargs)


class ArchiveDigitizationProcess(models.Model):
    """档案数字化处理"""
    PROCESS_STATUS_CHOICES = [
        ('pending', '待处理'),
        ('processing', '处理中'),
        ('quality_check', '质量检查中'),
        ('completed', '已完成'),
        ('failed', '处理失败'),
        ('cancelled', '已取消'),
    ]
    
    process_number = models.CharField('处理编号', max_length=100, unique=True, db_index=True)
    
    # 关联的申请
    apply = models.ForeignKey(
        ArchiveDigitizationApply,
        on_delete=models.CASCADE,
        related_name='processes',
        verbose_name='数字化申请',
        db_constraint=True
    )
    
    # 处理信息
    processor = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='digitization_processes',
        verbose_name='处理人'
    )
    process_start_time = models.DateTimeField('处理开始时间', default=timezone.now)
    process_end_time = models.DateTimeField('处理结束时间', null=True, blank=True)
    
    status = models.CharField('处理状态', max_length=20, choices=PROCESS_STATUS_CHOICES, default='pending')
    process_description = models.TextField('处理说明', blank=True)
    process_notes = models.TextField('处理备注', blank=True)
    
    # 质量检查
    quality_checker = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='checked_digitization_processes',
        verbose_name='质量检查人'
    )
    quality_check_time = models.DateTimeField('质量检查时间', null=True, blank=True)
    quality_check_result = models.CharField('质量检查结果', max_length=20, choices=[
        ('passed', '通过'),
        ('failed', '不通过'),
        ('pending', '待检查'),
    ], default='pending')
    quality_check_notes = models.TextField('质量检查备注', blank=True)
    
    # 处理进度（0-100）
    progress = models.IntegerField('处理进度', default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    
    # 处理文件列表（JSON格式）
    process_files = models.JSONField('处理文件列表', default=list, blank=True)
    
    # 额外信息（JSON格式）
    extra_data = models.JSONField('额外信息', default=dict, blank=True)
    
    created_time = models.DateTimeField('创建时间', default=timezone.now)
    updated_time = models.DateTimeField('更新时间', auto_now=True)
    
    class Meta:
        db_table = 'archive_digitization_process'
        verbose_name = '档案数字化处理'
        verbose_name_plural = verbose_name
        ordering = ['-created_time']
        indexes = [
            models.Index(fields=['apply', 'status']),
            models.Index(fields=['processor', '-created_time']),
            models.Index(fields=['status', '-created_time']),
        ]
    
    def __str__(self):
        return f"{self.process_number} - {self.apply.apply_number}"
    
    def generate_process_number(self):
        """生成处理编号：DIG-PROC-{YYYYMMDD}-{序列号}"""
        date_str = timezone.now().strftime('%Y%m%d')
        prefix = f'DIG-PROC-{date_str}-'
        last_record = ArchiveDigitizationProcess.objects.filter(
            process_number__startswith=prefix
        ).order_by('-process_number').first()
        
        if last_record:
            try:
                seq = int(last_record.process_number.split('-')[-1]) + 1
            except (ValueError, IndexError):
                seq = 1
        else:
            seq = 1
        
        return f"{prefix}{seq:04d}"
    
    def save(self, *args, **kwargs):
        if not self.process_number:
            self.process_number = self.generate_process_number()
        super().save(*args, **kwargs)


class ArchiveDigitizationResult(models.Model):
    """档案数字化成果"""
    result_number = models.CharField('成果编号', max_length=100, unique=True, db_index=True)
    
    # 关联的处理
    process = models.ForeignKey(
        ArchiveDigitizationProcess,
        on_delete=models.CASCADE,
        related_name='results',
        verbose_name='数字化处理',
        db_constraint=True
    )
    
    # 成果信息
    result_name = models.CharField('成果名称', max_length=200)
    result_description = models.TextField('成果说明', blank=True)
    result_type = models.CharField('成果类型', max_length=50, blank=True)  # pdf, image, video, audio等
    
    # 成果文件
    result_file = models.FileField('成果文件', upload_to='archive_digitization/%Y/%m/', null=True, blank=True)
    file_size = models.BigIntegerField('文件大小（字节）', null=True, blank=True)
    file_format = models.CharField('文件格式', max_length=50, blank=True)
    
    # 成果元数据（JSON格式）
    metadata = models.JSONField('元数据', default=dict, blank=True)
    
    # 关联的原始档案
    project_document = models.ForeignKey(
        ProjectArchiveDocument,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='digitization_results',
        verbose_name='项目文档',
        db_constraint=True
    )
    administrative_archive = models.ForeignKey(
        AdministrativeArchive,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='digitization_results',
        verbose_name='行政档案',
        db_constraint=True
    )
    
    # 创建信息
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_digitization_results',
        verbose_name='创建人'
    )
    created_time = models.DateTimeField('创建时间', default=timezone.now)
    updated_time = models.DateTimeField('更新时间', auto_now=True)
    
    class Meta:
        db_table = 'archive_digitization_result'
        verbose_name = '档案数字化成果'
        verbose_name_plural = verbose_name
        ordering = ['-created_time']
        indexes = [
            models.Index(fields=['process', '-created_time']),
            models.Index(fields=['result_type', '-created_time']),
        ]
    
    def __str__(self):
        return f"{self.result_number} - {self.result_name}"
    
    def generate_result_number(self):
        """生成成果编号：DIG-RESULT-{YYYYMMDD}-{序列号}"""
        date_str = timezone.now().strftime('%Y%m%d')
        prefix = f'DIG-RESULT-{date_str}-'
        last_record = ArchiveDigitizationResult.objects.filter(
            result_number__startswith=prefix
        ).order_by('-result_number').first()
        
        if last_record:
            try:
                seq = int(last_record.result_number.split('-')[-1]) + 1
            except (ValueError, IndexError):
                seq = 1
        else:
            seq = 1
        
        return f"{prefix}{seq:04d}"
    
    def save(self, *args, **kwargs):
        if not self.result_number:
            self.result_number = self.generate_result_number()
        # 自动设置文件大小
        if self.result_file and not self.file_size:
            try:
                self.file_size = self.result_file.size
            except:
                pass
        super().save(*args, **kwargs)


# ==================== 档案安全 - 操作日志 ====================

class ArchiveOperationLog(models.Model):
    """档案操作日志"""
    OPERATION_TYPE_CHOICES = [
        ('upload', '上传'),
        ('download', '下载'),
        ('edit', '编辑'),
        ('delete', '删除'),
        ('archive', '归档'),
        ('borrow', '借阅'),
        ('return', '归还'),
        ('destroy', '销毁'),
        ('move', '移动'),
        ('copy', '复制'),
        ('view', '查看'),
        ('approve', '审批'),
        ('reject', '驳回'),
    ]
    
    OPERATION_RESULT_CHOICES = [
        ('success', '成功'),
        ('failed', '失败'),
        ('pending', '待处理'),
    ]
    
    operation_type = models.CharField('操作类型', max_length=20, choices=OPERATION_TYPE_CHOICES)
    operator = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='archive_operations',
        verbose_name='操作人'
    )
    operation_time = models.DateTimeField('操作时间', default=timezone.now, db_index=True)
    operation_content = models.TextField('操作内容', blank=True)
    operation_result = models.CharField('操作结果', max_length=20, choices=OPERATION_RESULT_CHOICES, default='success')
    error_message = models.TextField('错误信息', blank=True)
    
    # 关联的档案（项目文档或行政档案）
    project_document = models.ForeignKey(
        ProjectArchiveDocument,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='operation_logs',
        verbose_name='项目文档',
        db_constraint=True
    )
    administrative_archive = models.ForeignKey(
        AdministrativeArchive,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='operation_logs',
        verbose_name='行政档案',
        db_constraint=True
    )
    
    # 关联的项目归档
    project_archive = models.ForeignKey(
        ArchiveProjectArchive,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='operation_logs',
        verbose_name='项目归档',
        db_constraint=True
    )
    
    # 关联的借阅记录
    borrow_record = models.ForeignKey(
        'ArchiveBorrow',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='operation_logs',
        verbose_name='借阅记录',
        db_constraint=True
    )
    
    # IP地址和用户代理
    ip_address = models.GenericIPAddressField('IP地址', null=True, blank=True)
    user_agent = models.CharField('用户代理', max_length=500, blank=True)
    
    # 额外信息（JSON格式）
    extra_data = models.JSONField('额外信息', default=dict, blank=True)
    
    created_time = models.DateTimeField('创建时间', default=timezone.now)
    
    class Meta:
        db_table = 'archive_operation_log'
        verbose_name = '档案操作日志'
        verbose_name_plural = verbose_name
        ordering = ['-operation_time']
        indexes = [
            models.Index(fields=['operation_type', 'operation_time']),
            models.Index(fields=['operator', 'operation_time']),
            models.Index(fields=['operation_result', 'operation_time']),
            models.Index(fields=['project_document', 'operation_time']),
            models.Index(fields=['administrative_archive', 'operation_time']),
        ]
    
    def __str__(self):
        archive_name = ''
        if self.project_document:
            archive_name = self.project_document.document_name
        elif self.administrative_archive:
            archive_name = self.administrative_archive.archive_name
        elif self.project_archive:
            archive_name = self.project_archive.archive_number
        
        operator_name = self.operator.get_full_name() if self.operator else '系统'
        return f"{operator_name} - {self.get_operation_type_display()} - {archive_name or 'N/A'}"


# ==================== 档案检索 - 检索历史 ====================

class ArchiveSearchHistory(models.Model):
    """档案检索历史"""
    SEARCH_TYPE_CHOICES = [
        ('fulltext', '全文检索'),
        ('advanced', '高级检索'),
        ('simple', '简单检索'),
    ]
    
    searcher = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='archive_search_histories',
        verbose_name='检索人'
    )
    search_type = models.CharField('检索类型', max_length=20, choices=SEARCH_TYPE_CHOICES, default='simple')
    search_keyword = models.CharField('检索关键词', max_length=500, blank=True)
    search_conditions = models.JSONField('检索条件', default=dict, blank=True, help_text='高级检索的条件配置')
    search_range = models.CharField('检索范围', max_length=100, blank=True, help_text='检索的档案类型范围')
    result_count = models.IntegerField('结果数量', default=0)
    search_time = models.DateTimeField('检索时间', default=timezone.now, db_index=True)
    search_duration = models.FloatField('检索耗时(秒)', null=True, blank=True)
    
    # 检索结果快照（可选，保存前N条结果）
    result_snapshot = models.JSONField('结果快照', default=list, blank=True)
    
    created_time = models.DateTimeField('创建时间', default=timezone.now)
    
    class Meta:
        db_table = 'archive_search_history'
        verbose_name = '档案检索历史'
        verbose_name_plural = verbose_name
        ordering = ['-search_time']
        indexes = [
            models.Index(fields=['searcher', 'search_time']),
            models.Index(fields=['search_type', 'search_time']),
        ]
    
    def __str__(self):
        return f"{self.searcher.username} - {self.get_search_type_display()} - {self.search_keyword[:50]}"

