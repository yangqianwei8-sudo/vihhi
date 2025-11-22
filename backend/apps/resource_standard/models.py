from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.utils import timezone


class Standard(models.Model):
    STANDARD_TYPE_CHOICES = [
        ("client", "甲方标准"),
        ("company", "公司标准"),
    ]

    STATUS_CHOICES = [
        ("draft", "草稿"),
        ("effective", "生效"),
        ("inactive", "停用"),
    ]

    PROFESSION_CHOICES = [
        ("ARCH", "建筑"),
        ("STRU", "结构"),
        ("ELEC", "电气"),
        ("WATR", "给排水"),
        ("HVAC", "暖通"),
        ("OTHR", "其他"),
    ]

    BUSINESS_TYPE_CHOICES = [
        ("residential", "住宅"),
        ("complex", "综合体"),
        ("commercial", "商业"),
        ("office", "写字楼"),
        ("school", "学校"),
        ("hospital", "医院"),
        ("industrial", "工业厂房"),
        ("municipal", "市政"),
        ("other", "其他"),
    ]

    SCOPE_CHOICES = [
        ("all", "全公司"),
        ("sichuan", "四川维海"),
        ("chongqing", "重庆维海"),
        ("xian", "西安维海"),
        ("hejian_chengdu", "禾间成都"),
        ("hongtian", "宏天升荣"),
    ]

    code = models.CharField("标准编号", max_length=50, unique=True, blank=True)
    name = models.CharField("标准名称", max_length=200)
    standard_type = models.CharField("标准类型", max_length=20, choices=STANDARD_TYPE_CHOICES)
    applicable_professions = ArrayField(
        models.CharField(max_length=8, choices=PROFESSION_CHOICES),
        verbose_name="适用专业",
    )
    applicable_business_types = ArrayField(
        models.CharField(max_length=20, choices=BUSINESS_TYPE_CHOICES),
        verbose_name="适用业态",
        blank=True,
        default=list,
    )
    effective_date = models.DateField("生效日期")
    status = models.CharField("状态", max_length=20, choices=STATUS_CHOICES, default="draft")
    visible_scope = ArrayField(
        models.CharField(max_length=20, choices=SCOPE_CHOICES),
        verbose_name="可见范围",
        default=list,
    )
    editable_roles = models.ManyToManyField(
        "system_management.Role",
        blank=True,
        related_name="editable_standards",
        verbose_name="可编辑角色",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="standards_created",
        verbose_name="创建人",
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="standards_updated",
        verbose_name="更新人",
    )
    created_time = models.DateTimeField("创建时间", default=timezone.now)
    updated_time = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        db_table = "resource_standard_standard"
        verbose_name = "审查标准"
        verbose_name_plural = "审查标准"
        ordering = ["-created_time"]

    def save(self, *args, **kwargs):
        if not self.code:
            profession_code = self.applicable_professions[0] if self.applicable_professions else "GEN"
            prefix = f"STD-{profession_code}-"
            last_code = (
                Standard.objects.filter(code__startswith=prefix)
                .order_by("-code")
                .values_list("code", flat=True)
                .first()
            )
            if last_code:
                try:
                    seq = int(last_code.split("-")[-1]) + 1
                except ValueError:
                    seq = 1
            else:
                seq = 1
            self.code = f"{prefix}{seq:04d}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.code} {self.name}"


class StandardReviewItem(models.Model):
    ISSUE_CATEGORY_CHOICES = [
        ("compliance", "合规性"),
        ("drawing_quality", "图纸质量"),
        ("function", "功能性"),
        ("constructability", "可施工性"),
        ("other", "其他"),
    ]

    SEVERITY_CHOICES = [
        ("high", "重大"),
        ("medium", "一般"),
        ("low", "轻微"),
    ]

    standard = models.ForeignKey(
        Standard,
        on_delete=models.CASCADE,
        related_name="review_items",
        verbose_name="所属标准",
    )
    section_name = models.CharField("部位名称", max_length=200)
    review_point = models.TextField("审查要点")
    issue_category = models.CharField("问题类别", max_length=32, choices=ISSUE_CATEGORY_CHOICES, default="other")
    severity_level = models.CharField("严重等级", max_length=16, choices=SEVERITY_CHOICES, default="medium")
    order = models.PositiveIntegerField("排序", default=0)

    class Meta:
        db_table = "resource_standard_review_item"
        verbose_name = "标准审查要点"
        verbose_name_plural = "标准审查要点"
        ordering = ["order", "id"]

    def __str__(self):
        return f"{self.standard.code} - {self.section_name}"


class MaterialPrice(models.Model):
    PRICE_TYPE_CHOICES = [
        ("material", "材料价"),
        ("labor", "人工价"),
        ("machine", "机械价"),
        ("composite", "综合价"),
    ]

    PRICE_SOURCE_CHOICES = [
        ("market", "市场价"),
        ("quota", "定额价"),
        ("client", "甲方确认价"),
        ("history", "历史项目价"),
    ]

    REGION_CHOICES = [
        ("sichuan", "四川"),
        ("chongqing", "重庆"),
        ("shaanxi", "陕西"),
        ("yunnan", "云南"),
        ("guizhou", "贵州"),
        ("other", "其他"),
    ]

    UNIT_CHOICES = [
        ("m", "米"),
        ("m2", "平方米"),
        ("m3", "立方米"),
        ("t", "吨"),
        ("pcs", "个"),
    ]

    code = models.CharField("材料编号", max_length=50, unique=True, blank=True)
    name = models.CharField("材料名称", max_length=200)
    specification = models.CharField("规格型号", max_length=200, blank=True)
    unit = models.CharField("单位", max_length=10, choices=UNIT_CHOICES)
    brand_requirement = models.CharField("品牌要求", max_length=200, blank=True)
    applicable_regions = ArrayField(
        models.CharField(max_length=20, choices=REGION_CHOICES),
        verbose_name="适用地区",
        default=list,
    )
    price = models.DecimalField("综合单价", max_digits=12, decimal_places=2)
    price_type = models.CharField("价格类型", max_length=20, choices=PRICE_TYPE_CHOICES, default="material")
    price_source = models.CharField("价格来源", max_length=20, choices=PRICE_SOURCE_CHOICES, default="market")
    effective_date = models.DateField("生效时间", null=True, blank=True)
    expire_date = models.DateField("失效时间", null=True, blank=True)
    tax_rate = models.DecimalField("税率", max_digits=5, decimal_places=2, default=0)
    version = models.PositiveIntegerField("版本号", default=1)
    change_note = models.TextField("变更说明", blank=True)
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="material_prices_changed",
        verbose_name="变更人",
    )
    changed_time = models.DateTimeField("变更时间", default=timezone.now)
    created_time = models.DateTimeField("创建时间", default=timezone.now)

    class Meta:
        db_table = "resource_standard_material_price"
        verbose_name = "综合单价"
        verbose_name_plural = "综合单价"
        ordering = ["name", "-version"]

    def save(self, *args, **kwargs):
        if not self.code:
            prefix = "MAT-"
            date_prefix = timezone.now().strftime("%Y%m")
            prefix = f"{prefix}{date_prefix}-"
            last_code = (
                MaterialPrice.objects.filter(code__startswith=prefix)
                .order_by("-code")
                .values_list("code", flat=True)
                .first()
            )
            if last_code:
                try:
                    seq = int(last_code.split("-")[-1]) + 1
                except ValueError:
                    seq = 1
            else:
                seq = 1
            self.code = f"{prefix}{seq:04d}"
        if not self.changed_time:
            self.changed_time = timezone.now()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.code} {self.name} v{self.version}"


class CostIndicator(models.Model):
    BUSINESS_TYPE_CHOICES = Standard.BUSINESS_TYPE_CHOICES

    BUILDING_TYPE_CHOICES = [
        ("high", "高层"),
        ("mid", "小高层"),
        ("low", "多层"),
        ("garage", "地下车库"),
    ]

    REGION_CHOICES = MaterialPrice.REGION_CHOICES

    RELIABILITY_CHOICES = [
        ("high", "高"),
        ("medium", "中"),
        ("low", "低"),
    ]

    UPDATE_FREQ_CHOICES = [
        ("monthly", "月度"),
        ("quarterly", "季度"),
        ("yearly", "年度"),
    ]

    code = models.CharField("指标编号", max_length=50, unique=True, blank=True)
    name = models.CharField("指标名称", max_length=200)
    business_type = models.CharField("业态类型", max_length=20, choices=BUSINESS_TYPE_CHOICES)
    building_type = models.CharField("建筑类型", max_length=20, choices=BUILDING_TYPE_CHOICES, blank=True)
    region = models.CharField("地区", max_length=20, choices=REGION_CHOICES)
    data_year = models.PositiveIntegerField("数据年份", null=True, blank=True)

    steel_consumption = models.DecimalField("钢筋含量", max_digits=10, decimal_places=2, null=True, blank=True)
    concrete_consumption = models.DecimalField("混凝土含量", max_digits=10, decimal_places=2, null=True, blank=True)
    formwork_consumption = models.DecimalField("模板含量", max_digits=10, decimal_places=2, null=True, blank=True)
    masonry_consumption = models.DecimalField("砌体含量", max_digits=10, decimal_places=2, null=True, blank=True)
    door_window_index = models.DecimalField("门窗指标", max_digits=10, decimal_places=2, null=True, blank=True)
    decoration_index = models.DecimalField("装饰指标", max_digits=12, decimal_places=2, null=True, blank=True)

    reference_project = models.CharField("参考项目", max_length=200, blank=True)
    sample_size = models.PositiveIntegerField("样本数量", null=True, blank=True)
    data_reliability = models.CharField("数据可靠性", max_length=10, choices=RELIABILITY_CHOICES, default="medium")
    update_frequency = models.CharField("更新频率", max_length=10, choices=UPDATE_FREQ_CHOICES, default="yearly")

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="cost_indicators_created",
        verbose_name="创建人",
    )
    created_time = models.DateTimeField("创建时间", default=timezone.now)
    updated_time = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        db_table = "resource_standard_cost_indicator"
        verbose_name = "成本指标"
        verbose_name_plural = "成本指标"
        ordering = ["-created_time"]

    def save(self, *args, **kwargs):
        if not self.code:
            prefix = "COST-"
            region_code = self.region.upper() if self.region else "GEN"
            prefix = f"{prefix}{region_code}-"
            last_code = (
                CostIndicator.objects.filter(code__startswith=prefix)
                .order_by("-code")
                .values_list("code", flat=True)
                .first()
            )
            if last_code:
                try:
                    seq = int(last_code.split("-")[-1]) + 1
                except ValueError:
                    seq = 1
            else:
                seq = 1
            self.code = f"{prefix}{seq:04d}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.code} {self.name}"


class ReportTemplate(models.Model):
    TEMPLATE_TYPE_CHOICES = [
        ("consultation", "咨询意见书"),
        ("optimization", "优化报告"),
        ("review", "审图报告"),
        ("weekly", "每周快报"),
    ]

    template_code = models.CharField("模板编号", max_length=50, unique=True, blank=True)
    name = models.CharField("模板名称", max_length=200)
    template_type = models.CharField("模板类型", max_length=30, choices=TEMPLATE_TYPE_CHOICES)
    service_types = ArrayField(
        models.CharField(max_length=32),
        verbose_name="适用服务类型",
        default=list,
    )
    version = models.PositiveIntegerField("版本号", default=1)
    cover_content = models.TextField("封面设计", blank=True)
    header_footer = models.JSONField("页眉页脚设置", default=dict, blank=True)
    sections = models.JSONField("章节结构", default=list, blank=True)
    styles = models.JSONField("样式设置", default=dict, blank=True)
    is_active = models.BooleanField("是否可用", default=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="report_templates_created",
        verbose_name="创建人",
    )
    created_time = models.DateTimeField("创建时间", default=timezone.now)
    updated_time = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        db_table = "resource_standard_report_template"
        verbose_name = "报告模板"
        verbose_name_plural = "报告模板"
        ordering = ["template_type", "name", "-version"]

    def save(self, *args, **kwargs):
        if not self.template_code:
            prefix = "TPL-REP-"
            last = (
                ReportTemplate.objects.filter(template_code__startswith=prefix)
                .order_by("-template_code")
                .values_list("template_code", flat=True)
                .first()
            )
            if last:
                try:
                    seq = int(last.split("-")[-1]) + 1
                except ValueError:
                    seq = 1
            else:
                seq = 1
            self.template_code = f"{prefix}{seq:04d}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.template_code} {self.name} v{self.version}"


class ReportTemplateVersion(models.Model):
    template = models.ForeignKey(
        ReportTemplate,
        on_delete=models.CASCADE,
        related_name="history",
        verbose_name="所属模板",
    )
    version = models.PositiveIntegerField("版本号")
    cover_content = models.TextField("封面设计", blank=True)
    header_footer = models.JSONField("页眉页脚设置", default=dict, blank=True)
    sections = models.JSONField("章节结构", default=list, blank=True)
    styles = models.JSONField("样式设置", default=dict, blank=True)
    change_note = models.TextField("变更说明", blank=True)
    created_time = models.DateTimeField("创建时间", default=timezone.now)

    class Meta:
        db_table = "resource_standard_report_template_version"
        verbose_name = "报告模板版本"
        verbose_name_plural = "报告模板版本"
        unique_together = ("template", "version")
        ordering = ["template", "-version"]

    def __str__(self):
        return f"{self.template.template_code} v{self.version}"


class OpinionTemplate(models.Model):
    PROFESSIONAL_TYPE_CHOICES = Standard.PROFESSION_CHOICES

    template_code = models.CharField("模板编号", max_length=50, unique=True, blank=True)
    professional_type = models.CharField("专业类型", max_length=32, choices=PROFESSIONAL_TYPE_CHOICES)
    name = models.CharField("模板名称", max_length=200)
    default_review_points = models.ManyToManyField(
        StandardReviewItem,
        blank=True,
        related_name="opinion_templates",
        verbose_name="默认审查要点",
    )
    auto_fields = models.JSONField("自动带出字段", default=list, blank=True)
    category_templates = models.JSONField("意见分类模板", default=dict, blank=True)
    calculation_rules = models.JSONField("节省金额计算模板", default=dict, blank=True)
    version = models.PositiveIntegerField("版本号", default=1)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="opinion_templates_created",
        verbose_name="创建人",
    )
    created_time = models.DateTimeField("创建时间", default=timezone.now)
    updated_time = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        db_table = "resource_standard_opinion_template"
        verbose_name = "意见书模板"
        verbose_name_plural = "意见书模板"
        ordering = ["professional_type", "name", "-version"]

    def save(self, *args, **kwargs):
        if not self.template_code:
            prefix = "TPL-OPN-"
            last = (
                OpinionTemplate.objects.filter(template_code__startswith=prefix)
                .order_by("-template_code")
                .values_list("template_code", flat=True)
                .first()
            )
            if last:
                try:
                    seq = int(last.split("-")[-1]) + 1
                except ValueError:
                    seq = 1
            else:
                seq = 1
            self.template_code = f"{prefix}{seq:04d}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.template_code} {self.name} v{self.version}"


class OpinionTemplateVersion(models.Model):
    template = models.ForeignKey(
        OpinionTemplate,
        on_delete=models.CASCADE,
        related_name="history",
        verbose_name="所属模板",
    )
    version = models.PositiveIntegerField("版本号")
    auto_fields = models.JSONField("自动带出字段", default=list, blank=True)
    category_templates = models.JSONField("意见分类模板", default=dict, blank=True)
    calculation_rules = models.JSONField("节省金额计算模板", default=dict, blank=True)
    change_note = models.TextField("变更说明", blank=True)
    created_time = models.DateTimeField("创建时间", default=timezone.now)

    class Meta:
        db_table = "resource_standard_opinion_template_version"
        verbose_name = "意见书模板版本"
        verbose_name_plural = "意见书模板版本"
        unique_together = ("template", "version")
        ordering = ["template", "-version"]

    def __str__(self):
        return f"{self.template.template_code} v{self.version}"


class KnowledgeTag(models.Model):
    name = models.CharField("标签名称", max_length=50, unique=True)
    description = models.CharField("描述", max_length=200, blank=True)

    class Meta:
        db_table = "resource_standard_knowledge_tag"
        verbose_name = "知识标签"
        verbose_name_plural = "知识标签"

    def __str__(self):
        return self.name


class RiskCase(models.Model):
    CASE_TYPE_CHOICES = [
        ("technical", "技术风险"),
        ("schedule", "进度风险"),
        ("cost", "成本风险"),
        ("client", "客户风险"),
    ]

    case_code = models.CharField("案例编号", max_length=50, unique=True, blank=True)
    title = models.CharField("案例标题", max_length=200)
    case_type = models.CharField("案例类型", max_length=20, choices=CASE_TYPE_CHOICES)
    project = models.ForeignKey(
        "project_center.Project",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="发生项目",
    )
    occurred_on = models.DateField("发生时间", null=True, blank=True)
    risk_description = models.TextField("风险描述")
    root_cause = models.TextField("根本原因", blank=True)
    impact_scope = models.TextField("影响范围", blank=True)
    loss_estimation = models.DecimalField("损失评估", max_digits=12, decimal_places=2, null=True, blank=True)
    counter_measure = models.TextField("应对措施")
    prevention = models.TextField("预防措施", blank=True)
    outcome = models.TextField("处理效果", blank=True)
    lessons = models.TextField("经验教训", blank=True)
    tags = models.ManyToManyField(KnowledgeTag, blank=True, related_name="risk_cases")
    recommend_score = models.PositiveSmallIntegerField("推荐指数", default=3)
    applicable_scenarios = models.JSONField("适用场景", default=list, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="risk_cases_created",
        verbose_name="创建人",
    )
    created_time = models.DateTimeField("创建时间", default=timezone.now)
    updated_time = models.DateTimeField("更新时间", auto_now=True)
    is_published = models.BooleanField("是否已发布", default=False)

    class Meta:
        db_table = "resource_standard_risk_case"
        verbose_name = "风险案例"
        verbose_name_plural = "风险案例"
        ordering = ["-created_time"]

    def save(self, *args, **kwargs):
        if not self.case_code:
            prefix = "CASE-"
            today_prefix = timezone.now().strftime("%Y%m%d")
            prefix = f"{prefix}{today_prefix}-"
            last = (
                RiskCase.objects.filter(case_code__startswith=prefix)
                .order_by("-case_code")
                .values_list("case_code", flat=True)
                .first()
            )
            if last:
                try:
                    seq = int(last.split("-")[-1]) + 1
                except ValueError:
                    seq = 1
            else:
                seq = 1
            self.case_code = f"{prefix}{seq:04d}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.case_code} {self.title}"


class TechnicalSolution(models.Model):
    DOMAIN_CHOICES = [
        ("structure", "结构"),
        ("architecture", "建筑"),
        ("mep", "机电"),
        ("geotechnical", "岩土"),
        ("other", "其他"),
    ]

    DIFFICULTY_CHOICES = [
        ("high", "高"),
        ("medium", "中"),
        ("low", "低"),
    ]

    solution_code = models.CharField("方案编号", max_length=50, unique=True, blank=True)
    name = models.CharField("方案名称", max_length=200)
    domain = models.CharField("技术领域", max_length=20, choices=DOMAIN_CHOICES)
    issue_type = models.CharField("问题类型", max_length=100, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="technical_solutions_created",
        verbose_name="创建人",
    )
    created_time = models.DateTimeField("创建时间", default=timezone.now)
    problem_description = models.TextField("问题描述", blank=True)
    traditional_method = models.TextField("传统做法", blank=True)
    optimized_solution = models.TextField("优化方案")
    technical_principle = models.TextField("技术原理", blank=True)
    conditions = models.TextField("适用条件", blank=True)
    cost_comparison = models.JSONField("成本对比", default=dict, blank=True)
    saving_effect = models.DecimalField("节省效果", max_digits=12, decimal_places=2, null=True, blank=True)
    difficulty = models.CharField("实施难度", max_length=10, choices=DIFFICULTY_CHOICES, default="medium")
    promotion_value = models.CharField("推广价值", max_length=10, choices=DIFFICULTY_CHOICES, default="medium")
    calculation_file = models.FileField("计算书", upload_to="knowledge/solutions/", blank=True)
    drawing_sample = models.FileField("图纸示例", upload_to="knowledge/solutions/", blank=True)
    effect_picture = models.ImageField("效果图", upload_to="knowledge/solutions/", blank=True)
    reference_codes = models.TextField("参考规范", blank=True)
    tags = models.ManyToManyField(KnowledgeTag, blank=True, related_name="technical_solutions")
    is_published = models.BooleanField("是否已发布", default=False)
    updated_time = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        db_table = "resource_standard_technical_solution"
        verbose_name = "技术解决方案"
        verbose_name_plural = "技术解决方案"
        ordering = ["-created_time"]

    def save(self, *args, **kwargs):
        if not self.solution_code:
            prefix = "TS-"
            date_prefix = timezone.now().strftime("%Y%m")
            prefix = f"{prefix}{date_prefix}-"
            last = (
                TechnicalSolution.objects.filter(solution_code__startswith=prefix)
                .order_by("-solution_code")
                .values_list("solution_code", flat=True)
                .first()
            )
            if last:
                try:
                    seq = int(last.split("-")[-1]) + 1
                except ValueError:
                    seq = 1
            else:
                seq = 1
            self.solution_code = f"{prefix}{seq:04d}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.solution_code} {self.name}"


class ProfessionalCategory(models.Model):
    CATEGORY_CHOICES = [
        ("architecture", "建筑"),
        ("structure", "结构"),
        ("mep", "机电"),
        ("landscape", "景观"),
        ("other", "其他"),
    ]

    code = models.CharField("专业代码", max_length=50, unique=True)
    name = models.CharField("专业名称", max_length=100)
    category = models.CharField("专业类别", max_length=20, choices=CATEGORY_CHOICES, default="other")
    order = models.PositiveIntegerField("排序号", default=0)
    service_types = ArrayField(
        models.CharField(max_length=32),
        verbose_name="适用服务类型",
        default=list,
        blank=True,
    )
    default_owner = models.ForeignKey(
        "system_management.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="default_professional_categories",
        verbose_name="默认负责人",
    )
    workflow_template = models.CharField("工作流模板", max_length=100, blank=True)
    data_permissions = models.ManyToManyField(
        "system_management.Role",
        blank=True,
        related_name="professional_data_permissions",
        verbose_name="数据权限角色",
    )
    operation_permissions = models.ManyToManyField(
        "system_management.Role",
        blank=True,
        related_name="professional_operation_permissions",
        verbose_name="操作权限角色",
    )
    created_time = models.DateTimeField("创建时间", default=timezone.now)
    updated_time = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        db_table = "resource_standard_professional_category"
        verbose_name = "专业分类"
        verbose_name_plural = "专业分类"
        ordering = ["order", "code"]

    def __str__(self):
        return f"{self.code} {self.name}"


class SystemParameter(models.Model):
    key = models.CharField("参数键", max_length=100, unique=True)
    value = models.CharField("参数值", max_length=200)
    description = models.CharField("描述", max_length=300, blank=True)
    category = models.CharField("分类", max_length=50, default="business")
    updated_time = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        db_table = "resource_standard_system_param"
        verbose_name = "系统参数"
        verbose_name_plural = "系统参数"
        ordering = ["category", "key"]

    def __str__(self):
        return f"{self.key}"
