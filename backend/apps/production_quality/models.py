from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils import timezone

from backend.apps.project_center.models import Project
from backend.apps.resource_standard.models import (
    ProfessionalCategory,
    StandardReviewItem,
    ReportTemplate,
)


class Opinion(models.Model):
    """核心意见填报数据模型"""

    class OpinionStatus(models.TextChoices):
        DRAFT = "draft", "草稿"
        SUBMITTED = "submitted", "已提交"
        IN_REVIEW = "in_review", "审核中"
        APPROVED = "approved", "已通过"
        REJECTED = "rejected", "已驳回"
        NEEDS_UPDATE = "needs_update", "需修改"

    class OpinionSource(models.TextChoices):
        PROJECT_MANAGER = "project_manager", "项目经理"
        ENGINEER = "engineer", "专业工程师"
        QUALITY_AUDIT = "quality_audit", "质量巡检"
        CLIENT_FEEDBACK = "client_feedback", "甲方反馈"
        OTHER = "other", "其他来源"

    class PriorityLevel(models.TextChoices):
        URGENT = "urgent", "紧急"
        HIGH = "high", "高"
        MEDIUM = "medium", "中"
        LOW = "low", "低"

    class CalculationMode(models.TextChoices):
        AUTO = "auto", "自动计算"
        MANUAL = "manual", "手动输入"

    class IssueCategory(models.TextChoices):
        ERROR = "error", "错误"
        OMISSION = "omission", "遗漏"
        CONFLICT = "conflict", "矛盾"
        DEFECT = "defect", "缺陷"
        IMPROVEMENT = "improvement", "优化建议"

    class SeverityLevel(models.TextChoices):
        MAJOR = "major", "重大"
        NORMAL = "normal", "一般"
        MINOR = "minor", "轻微"

    opinion_number = models.CharField("意见编号", max_length=50, unique=True)
    project = models.ForeignKey(
        Project,
        verbose_name="关联项目",
        on_delete=models.CASCADE,
        related_name="opinions",
    )
    professional_category = models.ForeignKey(
        ProfessionalCategory,
        verbose_name="专业分类",
        on_delete=models.PROTECT,
        related_name="opinions",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="提出人",
        on_delete=models.PROTECT,
        related_name="opinions_created",
    )
    current_reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="当前审核人",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="opinions_assigned",
    )
    status = models.CharField(
        "状态",
        max_length=20,
        choices=OpinionStatus.choices,
        default=OpinionStatus.DRAFT,
    )
    source = models.CharField(
        "意见来源",
        max_length=30,
        choices=OpinionSource.choices,
        default=OpinionSource.ENGINEER,
    )
    priority = models.CharField(
        "优先级",
        max_length=10,
        choices=PriorityLevel.choices,
        default=PriorityLevel.MEDIUM,
    )
    drawing_number = models.CharField("图纸编号", max_length=100, blank=True)
    drawing_version = models.CharField("图纸版本", max_length=100, blank=True)
    location_name = models.CharField("部位名称", max_length=100)
    review_points = models.ManyToManyField(
        StandardReviewItem,
        verbose_name="关联审查要点",
        blank=True,
        related_name="opinions",
    )

    issue_description = models.TextField("问题描述")
    current_practice = models.TextField("现行做法", blank=True)
    recommendation = models.TextField("优化建议")
    issue_category = models.CharField(
        "问题类别",
        max_length=20,
        choices=IssueCategory.choices,
    )
    severity_level = models.CharField(
        "严重等级",
        max_length=20,
        choices=SeverityLevel.choices,
    )
    reference_codes = models.CharField("引用规范", max_length=255, blank=True)

    calculation_mode = models.CharField(
        "计算方式",
        max_length=10,
        choices=CalculationMode.choices,
        default=CalculationMode.AUTO,
    )
    quantity_before = models.DecimalField(
        "优化前工程量",
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
    )
    quantity_after = models.DecimalField(
        "优化后工程量",
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
    )
    measure_unit = models.CharField("计量单位", max_length=30, blank=True)
    unit_price_before = models.DecimalField(
        "优化前综合单价",
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
    )
    unit_price_after = models.DecimalField(
        "优化后综合单价",
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
    )
    saving_amount = models.DecimalField(
        "节省金额",
        max_digits=14,
        decimal_places=2,
        null=True,
        blank=True,
    )
    calculation_note = models.TextField("计算说明", blank=True)

    impact_scope = models.JSONField("影响范围", default=list, blank=True)
    expected_complete_date = models.DateField("计划完成日期", null=True, blank=True)
    actual_complete_date = models.DateField("实际完成日期", null=True, blank=True)
    response_deadline = models.DateField("整改要求完成期限", null=True, blank=True)

    is_template_applied = models.BooleanField("是否应用模板", default=False)
    submitted_at = models.DateTimeField("提交时间", null=True, blank=True)
    reviewed_at = models.DateTimeField("审核完成时间", null=True, blank=True)
    first_assigned_at = models.DateTimeField("首次指派时间", null=True, blank=True)
    first_response_at = models.DateTimeField("首次响应时间", null=True, blank=True)
    closed_at = models.DateTimeField("结案时间", null=True, blank=True)
    cycle_time_hours = models.DecimalField(
        "流转耗时（小时）", max_digits=8, decimal_places=2, null=True, blank=True
    )
    created_at = models.DateTimeField("创建时间", default=timezone.now)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "咨询意见"
        verbose_name_plural = "咨询意见"

    def __str__(self) -> str:
        return self.opinion_number

    def refresh_cycle_metrics(self, commit: bool = False) -> None:
        """根据提交与结案时间计算流转耗时"""
        hours = None
        if self.submitted_at and self.closed_at:
            total_seconds = (self.closed_at - self.submitted_at).total_seconds()
            if total_seconds > 0:
                hours = (Decimal(str(total_seconds)) / Decimal("3600")).quantize(
                    Decimal("0.01")
                )
        self.cycle_time_hours = hours
        if commit:
            self.save(update_fields=["cycle_time_hours"])


def opinion_attachment_path(instance, filename: str) -> str:
    return f"opinions/{instance.opinion_id}/{filename}"


class OpinionAttachment(models.Model):
    """意见附件"""

    class AttachmentType(models.TextChoices):
        CURRENT_DRAWING = "current_drawing", "现状图纸"
        PROPOSED_DRAWING = "proposed_drawing", "建议图纸"
        CALCULATION = "calculation", "计算书"
        OTHER = "other", "其他附件"

    opinion = models.ForeignKey(
        Opinion,
        verbose_name="关联意见",
        on_delete=models.CASCADE,
        related_name="attachments",
    )
    attachment_type = models.CharField(
        "附件类型",
        max_length=20,
        choices=AttachmentType.choices,
        default=AttachmentType.OTHER,
    )
    file = models.FileField("附件文件", upload_to=opinion_attachment_path)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="上传人",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="opinion_attachments",
    )
    uploaded_at = models.DateTimeField("上传时间", default=timezone.now)

    class Meta:
        verbose_name = "意见附件"
        verbose_name_plural = "意见附件"

    def __str__(self) -> str:
        return f"{self.opinion_id}-{self.file.name}"


class OpinionReview(models.Model):
    """意见审核记录"""

    class ReviewRole(models.TextChoices):
        PROFESSIONAL_LEAD = "professional_lead", "专业负责人"
        PROJECT_LEAD = "project_lead", "项目负责人"
        QUALITY_MANAGER = "quality_manager", "质量经理"

    class ReviewStatus(models.TextChoices):
        PENDING = "pending", "待审核"
        APPROVED = "approved", "通过"
        REJECTED = "rejected", "驳回"
        NEEDS_UPDATE = "needs_update", "需修改"

    opinion = models.ForeignKey(
        Opinion,
        verbose_name="关联意见",
        on_delete=models.CASCADE,
        related_name="reviews",
    )
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="审核人",
        on_delete=models.CASCADE,
        related_name="opinion_reviews",
    )
    role = models.CharField(
        "审核角色",
        max_length=30,
        choices=ReviewRole.choices,
    )
    status = models.CharField(
        "审核状态",
        max_length=20,
        choices=ReviewStatus.choices,
        default=ReviewStatus.PENDING,
    )
    comments = models.TextField("审核意见", blank=True)
    technical_score = models.PositiveSmallIntegerField("技术评分", null=True, blank=True)
    economic_score = models.PositiveSmallIntegerField("经济评分", null=True, blank=True)
    internal_note = models.TextField("内部备注", blank=True)
    created_at = models.DateTimeField("创建时间", default=timezone.now)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        verbose_name = "意见审核记录"
        verbose_name_plural = "意见审核记录"
        unique_together = ("opinion", "reviewer", "role")

    def __str__(self) -> str:
        return f"{self.opinion_id}-{self.reviewer_id}-{self.role}"


class OpinionParticipant(models.Model):
    """意见协同参与人"""

    class ParticipantRole(models.TextChoices):
        PROPOSER = "proposer", "提出人"
        PROFESSIONAL_ENGINEER = "professional_engineer", "专业工程师"
        PROFESSIONAL_LEAD = "professional_lead", "专业负责人"
        PROJECT_MANAGER = "project_manager", "项目负责人"
        COST_ENGINEER = "cost_engineer", "造价工程师"
        QUALITY_MANAGER = "quality_manager", "质量经理"
        REVIEWER = "reviewer", "审核人"
        OBSERVER = "observer", "关注人"

    opinion = models.ForeignKey(
        Opinion,
        verbose_name="关联意见",
        on_delete=models.CASCADE,
        related_name="participants",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="用户",
        on_delete=models.CASCADE,
        related_name="opinion_participations",
    )
    role = models.CharField(
        "角色",
        max_length=40,
        choices=ParticipantRole.choices,
    )
    is_primary = models.BooleanField("是否主责", default=False)
    joined_at = models.DateTimeField("加入时间", default=timezone.now)
    removed_at = models.DateTimeField("移除时间", null=True, blank=True)
    extra_info = models.JSONField("扩展信息", default=dict, blank=True)

    class Meta:
        verbose_name = "意见参与人"
        verbose_name_plural = "意见参与人"
        unique_together = ("opinion", "user", "role")
        ordering = ["-joined_at"]

    def __str__(self) -> str:
        return f"{self.opinion_id}-{self.user_id}-{self.role}"


class OpinionWorkflowLog(models.Model):
    """意见流程日志"""

    class ActionType(models.TextChoices):
        CREATED = "created", "创建意见"
        UPDATED = "updated", "更新内容"
        SUBMITTED = "submitted", "提交意见"
        REASSIGNED = "reassigned", "重新指派"
        REVIEWED = "reviewed", "审核处理"
        COMMENTED = "commented", "追加说明"
        STATUS_CHANGED = "status_changed", "状态变更"
        ATTACHMENT_ADDED = "attachment_added", "新增附件"
        ATTACHMENT_REMOVED = "attachment_removed", "移除附件"

    opinion = models.ForeignKey(
        Opinion,
        verbose_name="关联意见",
        on_delete=models.CASCADE,
        related_name="workflow_logs",
    )
    action = models.CharField(
        "操作类型",
        max_length=40,
        choices=ActionType.choices,
    )
    from_status = models.CharField(
        "原状态",
        max_length=20,
        choices=Opinion.OpinionStatus.choices,
        null=True,
        blank=True,
    )
    to_status = models.CharField(
        "目标状态",
        max_length=20,
        choices=Opinion.OpinionStatus.choices,
        null=True,
        blank=True,
    )
    operator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="操作人",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="opinion_workflow_logs",
    )
    operator_role = models.CharField(
        "操作角色",
        max_length=40,
        choices=OpinionParticipant.ParticipantRole.choices,
        null=True,
        blank=True,
    )
    message = models.TextField("备注说明", blank=True)
    payload = models.JSONField("上下文信息", default=dict, blank=True)
    created_at = models.DateTimeField("记录时间", default=timezone.now)

    class Meta:
        verbose_name = "意见流程日志"
        verbose_name_plural = "意见流程日志"
        ordering = ["-created_at", "-id"]

    def __str__(self) -> str:
        return f"{self.opinion_id}-{self.action}-{self.created_at:%Y%m%d%H%M}"


class OpinionSavingItem(models.Model):
    """意见节省金额分项数据"""

    class SavingCategory(models.TextChoices):
        MATERIAL = "material", "材料"
        LABOR = "labor", "人工"
        EQUIPMENT = "equipment", "设备"
        INDIRECT = "indirect", "间接费用"
        ENERGY = "energy", "能耗"
        SCHEDULE = "schedule", "工期"
        OTHER = "other", "其他"

    opinion = models.ForeignKey(
        Opinion,
        verbose_name="关联意见",
        on_delete=models.CASCADE,
        related_name="saving_items",
    )
    category = models.CharField(
        "节省类型",
        max_length=20,
        choices=SavingCategory.choices,
        default=SavingCategory.OTHER,
    )
    description = models.CharField("说明", max_length=255, blank=True)
    quantity = models.DecimalField(
        "数量",
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
    )
    unit = models.CharField("单位", max_length=30, blank=True)
    unit_saving = models.DecimalField(
        "单位节省",
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
    )
    total_saving = models.DecimalField(
        "节省金额",
        max_digits=14,
        decimal_places=2,
        null=True,
        blank=True,
    )
    notes = models.TextField("备注", blank=True)
    created_at = models.DateTimeField("创建时间", default=timezone.now)

    class Meta:
        verbose_name = "意见节省分项"
        verbose_name_plural = "意见节省分项"
        ordering = ["-created_at", "-id"]

    def __str__(self) -> str:
        return f"{self.opinion_id}-{self.category}-{self.total_saving or 0}"

    def recalculate_total(self) -> None:
        if self.quantity is not None and self.unit_saving is not None:
            self.total_saving = (self.quantity or 0) * (self.unit_saving or 0)

class ProductionReport(models.Model):
    """专业报告"""

    class ReportStatus(models.TextChoices):
        DRAFT = "draft", "草稿"
        GENERATED = "generated", "已生成"
        APPROVED = "approved", "已发布"
        ARCHIVED = "archived", "已归档"

    report_number = models.CharField("报告编号", max_length=50, unique=True)
    name = models.CharField("报告名称", max_length=255)
    project = models.ForeignKey(
        Project,
        verbose_name="关联项目",
        on_delete=models.CASCADE,
        related_name="production_reports",
    )
    professional_category = models.ForeignKey(
        ProfessionalCategory,
        verbose_name="专业分类",
        on_delete=models.PROTECT,
        related_name="production_reports",
    )
    template = models.ForeignKey(
        ReportTemplate,
        verbose_name="关联模板",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="production_reports",
    )
    generated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="生成者",
        on_delete=models.SET_NULL,
        null=True,
        related_name="production_reports",
    )
    summary = models.TextField("报告摘要", blank=True)
    configuration = models.JSONField("报告配置", default=dict, blank=True)
    status = models.CharField(
        "状态",
        max_length=20,
        choices=ReportStatus.choices,
        default=ReportStatus.DRAFT,
    )
    generated_at = models.DateTimeField("生成时间", null=True, blank=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        ordering = ["-generated_at", "-updated_at"]
        verbose_name = "生产报告"
        verbose_name_plural = "生产报告"

    def __str__(self) -> str:
        return self.report_number


class ProductionReportSection(models.Model):
    """报告章节或版块"""

    report = models.ForeignKey(
        ProductionReport,
        verbose_name="所属报告",
        on_delete=models.CASCADE,
        related_name="sections",
    )
    title = models.CharField("章节标题", max_length=255)
    order = models.PositiveIntegerField("排序", default=0)
    content = models.TextField("章节内容", blank=True)
    metadata = models.JSONField("章节配置", default=dict, blank=True)

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "报告章节"
        verbose_name_plural = "报告章节"

    def __str__(self) -> str:
        return f"{self.report_id}-{self.title}"


class ProductionStatistic(models.Model):
    """生产统计数据聚合"""

    STAT_TYPE_CHOICES = (
        ("overview", "总体概览"),
        ("quality", "质量指标"),
        ("efficiency", "效率指标"),
        ("capacity", "产能分析"),
    )

    project = models.ForeignKey(
        Project,
        verbose_name="关联项目",
        on_delete=models.CASCADE,
        related_name="production_statistics",
        null=True,
        blank=True,
    )
    statistic_type = models.CharField("统计类型", max_length=30, choices=STAT_TYPE_CHOICES)
    snapshot_date = models.DateField("统计日期", default=timezone.now)
    payload = models.JSONField("统计数据", default=dict, blank=True)
    created_at = models.DateTimeField("创建时间", default=timezone.now)

    class Meta:
        verbose_name = "生产统计"
        verbose_name_plural = "生产统计"
        unique_together = ("project", "statistic_type", "snapshot_date")

    def __str__(self) -> str:
        return f"{self.statistic_type}-{self.snapshot_date}"

