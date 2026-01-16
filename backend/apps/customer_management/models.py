from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from django.core.validators import MinValueValidator, MaxValueValidator
import logging
from backend.apps.system_management.models import User

logger = logging.getLogger(__name__)

# ==================== 客户管理模块模型（按《客户管理详细设计方案 v1.12》实现）====================

class ClientType(models.Model):
    """客户类型模型（后台管理）"""
    code = models.CharField(max_length=50, unique=True, verbose_name='类型代码', help_text='唯一标识，如：developer')
    name = models.CharField(max_length=100, verbose_name='类型名称', help_text='显示名称，如：开发商')
    display_order = models.IntegerField(default=0, verbose_name='显示顺序', help_text='数字越小越靠前')
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    description = models.TextField(blank=True, verbose_name='描述')
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    updated_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        db_table = 'customer_client_type'
        verbose_name = '客户类型'
        verbose_name_plural = verbose_name
        ordering = ['display_order', 'name']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return self.name


class ClientGrade(models.Model):
    """客户分级模型（后台管理）"""
    code = models.CharField(max_length=50, unique=True, verbose_name='分级代码', help_text='唯一标识，如：strategic')
    name = models.CharField(max_length=100, verbose_name='分级名称', help_text='显示名称，如：战略客户')
    display_order = models.IntegerField(default=0, verbose_name='显示顺序', help_text='数字越小越靠前')
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    description = models.TextField(blank=True, verbose_name='描述')
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    updated_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        db_table = 'customer_client_grade'
        verbose_name = '客户分级'
        verbose_name_plural = verbose_name
        ordering = ['display_order', 'name']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return self.name


class Client(models.Model):
    """客户模型"""
    CLIENT_LEVELS = [
        ('vip', 'VIP客户'),
        ('important', '重要客户'),
        ('general', '一般客户'),
        ('potential', '潜在客户'),
    ]
    
    CREDIT_LEVELS = [
        ('excellent', '优秀'),
        ('good', '良好'),
        ('normal', '一般'),
        ('poor', '较差'),
        ('bad', '很差'),
    ]
    
    # 注意：GRADE_CHOICES 和 CLIENT_TYPE_CHOICES 已迁移到后台管理
    # 请使用 ClientGrade 和 ClientType 模型
    # 保留这些常量仅用于向后兼容，新代码应使用模型查询
    
    SOURCE_CHOICES = [
        ('self_development', '自主开发'),
        ('customer_referral', '老客户推荐'),
        ('industry_exhibition', '行业展会'),
        ('online_promotion', '网络推广'),
        ('other', '其他'),
    ]
    
    PUBLIC_SEA_REASON_CHOICES = [
        ('unassigned', '未分配'),
        ('released', '已释放'),
        ('auto_entry', '自动进入'),
    ]
    
    # 基础信息
    name = models.CharField(max_length=200, verbose_name='客户名称')
    unified_credit_code = models.CharField(max_length=50, blank=True, verbose_name='统一信用代码')
    
    # 从启信宝获取的企业信息
    legal_representative = models.CharField(max_length=100, blank=True, verbose_name='法定代表人', help_text='从启信宝API获取')
    established_date = models.DateField(null=True, blank=True, verbose_name='成立日期', help_text='从启信宝API获取')
    registered_capital = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True, verbose_name='注册资本（万元）', help_text='从启信宝API获取')
    company_phone = models.CharField(max_length=20, blank=True, verbose_name='联系电话', help_text='从启信宝API获取')
    company_email = models.EmailField(blank=True, verbose_name='邮箱', help_text='从启信宝API获取')
    company_address = models.CharField(max_length=500, blank=True, verbose_name='地址', help_text='从启信宝API获取')
    
    # 分类信息
    client_level = models.CharField(max_length=20, choices=CLIENT_LEVELS, default='general', verbose_name='客户等级')
    grade = models.ForeignKey(
        'ClientGrade',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='clients',
        verbose_name='客户分级',
        help_text='用于商机管理的客户分级'
    )
    credit_level = models.CharField(max_length=20, choices=CREDIT_LEVELS, default='normal', verbose_name='信用等级')
    client_type = models.ForeignKey(
        'ClientType',
        on_delete=models.PROTECT,
        null=False,
        blank=False,
        related_name='clients',
        verbose_name='客户类型'
    )
    industry = models.CharField(max_length=100, blank=True, verbose_name='所属行业')
    region = models.CharField(max_length=100, blank=True, verbose_name='所属区域')
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, blank=True, verbose_name='客户来源')
    
    # 评分信息（用于自动分级）
    score = models.IntegerField(default=0, verbose_name='客户评分', help_text='0-100分，用于自动计算客户分级')
    
    # 联系信息
    contact_name = models.CharField(max_length=100, blank=True, verbose_name='联系人')
    contact_position = models.CharField(max_length=100, blank=True, verbose_name='职务')
    phone = models.CharField(max_length=20, blank=True, verbose_name='电话')
    
    # 财务信息
    total_contract_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='累计合同金额')
    total_payment_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='累计回款金额')
    
    # 法律风险信息
    legal_risk_level = models.CharField(
        max_length=20, 
        choices=[
            ('low', '低风险'),
            ('medium_low', '中低风险'),
            ('medium', '中风险'),
            ('medium_high', '中高风险'),
            ('high', '高风险'),
            ('unknown', '未知'),
        ],
        default='unknown',
        verbose_name='法律风险等级'
    )
    litigation_count = models.IntegerField(default=0, verbose_name='司法案件数量', help_text='从启信宝API获取')
    executed_person_count = models.IntegerField(default=0, verbose_name='被执行人数量', help_text='从启信宝API获取')
    final_case_count = models.IntegerField(default=0, verbose_name='终本案件数量', help_text='从启信宝API获取')
    consumption_limit_count = models.IntegerField(default=0, verbose_name='限制高消费数量', help_text='从启信宝API获取')
    total_execution_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='执行总金额', help_text='所有被执行记录的执行金额总和')
    
    # 状态信息
    is_active = models.BooleanField(default=True, verbose_name='是否活跃')
    health_score = models.IntegerField(default=0, verbose_name='健康度评分')
    description = models.TextField(blank=True, verbose_name='客户描述')
    
    # 负责人信息
    responsible_user = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='responsible_clients',
        verbose_name='负责人',
        help_text='为空表示在公海'
    )
    
    # 公海信息
    public_sea_entry_time = models.DateTimeField(null=True, blank=True, verbose_name='进入公海时间')
    public_sea_reason = models.CharField(
        max_length=20,
        choices=PUBLIC_SEA_REASON_CHOICES,
        blank=True,
        verbose_name='进入公海原因'
    )
    
    # 审计字段
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='created_clients', verbose_name='创建人')
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    updated_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        db_table = 'customer_client'
        verbose_name = '客户'
        verbose_name_plural = verbose_name
        ordering = ['-created_time']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['unified_credit_code']),
            models.Index(fields=['responsible_user', 'is_active']),
            models.Index(fields=['public_sea_entry_time']),
        ]
    
    def __str__(self):
        return self.name
    
    def calculate_score(self):
        """计算客户评分（0-100分）"""
        from decimal import Decimal
        score = 0
        
        # 合作历史（0-25分）- 从项目数量判断
        try:
            project_count = self.projects.count() if hasattr(self, 'projects') else 0
        except:
            project_count = 0
        
        if project_count >= 5:
            score += 25
        elif project_count >= 3:
            score += 15
        elif project_count >= 1:
            score += 8
        
        # 项目规模（0-20分）- 从累计合同金额判断
        if self.total_contract_amount:
            amount = float(self.total_contract_amount)
            if amount >= 10000000:  # 1000万以上
                score += 20
            elif amount >= 5000000:  # 500万以上
                score += 12
            elif amount >= 1000000:  # 100万以上
                score += 6
        
        # 付款信誉（0-15分）- 从回款率判断
        if self.total_contract_amount and float(self.total_contract_amount) > 0:
            payment_rate = (float(self.total_payment_amount) / float(self.total_contract_amount)) * 100
            if payment_rate >= 95:
                score += 15
            elif payment_rate >= 80:
                score += 10
            elif payment_rate >= 60:
                score += 5
        
        # 战略价值（0-10分）- 根据客户类型和等级判断
        if self.client_type == 'government' or self.client_level == 'vip':
            score += 10
        elif self.client_level == 'important':
            score += 6
        elif self.client_level == 'general':
            score += 3
        
        return min(score, 100)  # 最高100分
    
    def calculate_grade(self):
        """根据评分自动计算客户分级，返回ClientGrade对象"""
        score = self.calculate_score()
        
        # 根据评分确定分级代码
        if score >= 80:
            grade_code = 'strategic'  # 战略客户
        elif score >= 60:
            grade_code = 'core'  # 核心客户
        elif score >= 40:
            grade_code = 'potential'  # 潜力客户
        elif score >= 20:
            grade_code = 'regular'  # 常规客户
        elif score >= 10:
            grade_code = 'nurturing'  # 培育客户
        else:
            grade_code = 'observing'  # 观察客户
        
        # 查找对应的ClientGrade对象
        try:
            grade = ClientGrade.objects.get(code=grade_code, is_active=True)
            return grade
        except ClientGrade.DoesNotExist:
            # 如果找不到对应的分级，尝试查找任意启用的分级作为默认值
            try:
                default_grade = ClientGrade.objects.filter(is_active=True).first()
                if default_grade:
                    logger.warning(f"未找到代码为 '{grade_code}' 的客户分级，使用默认分级: {default_grade.name}")
                    return default_grade
            except Exception:
                pass
            # 如果都找不到，返回None
            logger.warning(f"未找到代码为 '{grade_code}' 的客户分级，且没有可用的默认分级")
            return None
    
    def save(self, *args, **kwargs):
        # 自动计算评分和分级
        # 对于新对象（首次保存），总是自动计算评分和分级
        # 对于已存在的对象，只有在明确指定update_score=True或update_grade=True时才更新
        
        is_new = self.pk is None
        
        # 计算评分
        if kwargs.get('update_score', False) or is_new:
            self.score = self.calculate_score()
        
        # 计算分级（分级依赖于评分，所以如果评分更新了，分级也应该更新）
        if kwargs.get('update_grade', False) or is_new or kwargs.get('update_score', False):
            calculated_grade = self.calculate_grade()
            if calculated_grade:
                self.grade = calculated_grade
        
        super().save(*args, **kwargs)
    
    def is_in_public_sea(self):
        """判断是否在公海"""
        return self.responsible_user is None
    
    def move_to_public_sea(self, reason='auto_entry'):
        """移入公海"""
        self.responsible_user = None
        self.public_sea_entry_time = timezone.now()
        self.public_sea_reason = reason
        self.save(update_fields=['responsible_user', 'public_sea_entry_time', 'public_sea_reason'])
    
    def claim_from_public_sea(self, user):
        """从公海认领"""
        self.responsible_user = user
        self.public_sea_entry_time = None
        self.public_sea_reason = ''
        self.save(update_fields=['responsible_user', 'public_sea_entry_time', 'public_sea_reason'])


class ClientContact(models.Model):
    """客户联系人模型"""
    GENDER_CHOICES = [
        ('male', '男'),
        ('female', '女'),
        ('unknown', '未知'),
    ]
    
    POSITION_LEVEL_CHOICES = [
        ('employee', '普通员工'),
        ('supervisor', '主管'),
        ('manager', '经理'),
        ('director', '总监'),
        ('vp', '副总'),
        ('ceo', '总经理'),
    ]
    
    ROLE_CHOICES = [
        ('contact_person', '对接人'),
        ('promoter', '推动人'),
        ('decision_maker', '决策人'),
        ('introducer', '介绍人'),
    ]
    
    RELATIONSHIP_LEVEL_CHOICES = [
        ('first_contact', '首次沟通'),
        ('requirement_communication', '需求沟通'),
        ('cooperation_intention', '合作意向'),
        ('cooperation_recognition', '合作认可'),
        ('external_partner', '外部合伙人'),
    ]
    
    DECISION_INFLUENCE_CHOICES = [
        ('high', '高'),
        ('medium', '中'),
        ('low', '低'),
    ]
    
    CONTACT_FREQUENCY_CHOICES = [
        ('daily', '每天'),
        ('weekly', '每周'),
        ('monthly', '每月'),
        ('quarterly', '每季度'),
        ('occasionally', '偶尔'),
        ('never', '从未'),
    ]
    
    PREFERRED_CONTACT_METHODS_CHOICES = [
        ('phone', '电话'),
        ('email', '邮件'),
        ('wechat', '微信'),
        ('face_to_face', '面谈'),
        ('other', '其他'),
    ]
    
    RESUME_SOURCE_CHOICES = [
        ('51job', '51job'),
        ('zhaopin', '智联招聘'),
        ('boss', 'BOSS直聘'),
        ('liepin', '猎聘'),
        ('other', '其他'),
    ]
    
    # 基础关联
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='contacts', verbose_name='客户')
    
    # 基本信息
    name = models.CharField(max_length=100, verbose_name='联系人姓名')
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, default='unknown', verbose_name='性别')
    birthplace = models.CharField(max_length=100, verbose_name='籍贯')
    
    # 旧版兼容字段（与ContactCareer重复，保留用于数据库兼容）
    position = models.CharField(max_length=100, blank=True, default='', verbose_name='职位（已废弃）')
    department = models.CharField(max_length=100, blank=True, default='', verbose_name='部门（已废弃）')
    telephone = models.CharField(max_length=20, blank=True, default='', verbose_name='电话（已废弃）')
    position_level = models.CharField(max_length=20, blank=True, default='', verbose_name='职位级别（已废弃）')
    join_date = models.DateField(null=True, blank=True, verbose_name='入职时间（已废弃）')
    work_years = models.IntegerField(null=True, blank=True, verbose_name='工作年限（已废弃）')
    birthday = models.DateField(null=True, blank=True, verbose_name='生日（已废弃）')
    home_address = models.CharField(max_length=500, blank=True, default='', verbose_name='家庭地址（已废弃）')
    
    # 联系方式
    phone = models.CharField(max_length=20, blank=True, default='', verbose_name='手机')
    email = models.EmailField(blank=True, default='', verbose_name='邮箱')
    wechat = models.CharField(max_length=200, blank=True, default='', verbose_name='微信号', help_text='可存储多个，用逗号分隔')
    office_address = models.CharField(max_length=500, blank=True, default='', verbose_name='办公地址')
    
    # 角色与关系
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, verbose_name='人员角色')
    relationship_level = models.CharField(
        max_length=30, 
        choices=RELATIONSHIP_LEVEL_CHOICES, 
        default='first_contact',
        verbose_name='关系等级'
    )
    decision_influence = models.CharField(max_length=10, choices=DECISION_INFLUENCE_CHOICES, verbose_name='决策影响力')
    relationship_score = models.IntegerField(default=0, verbose_name='关系评分', help_text='0-100分')
    
    # 关系维护信息
    first_contact_time = models.DateTimeField(null=True, blank=True, verbose_name='首次接触时间')
    last_contact_time = models.DateTimeField(null=True, blank=True, verbose_name='最后联系时间', help_text='自动更新')
    contact_frequency = models.CharField(max_length=20, choices=CONTACT_FREQUENCY_CHOICES, blank=True, verbose_name='联系频率')
    preferred_contact_methods = models.JSONField(default=list, blank=True, verbose_name='偏好沟通方式', help_text='多选：phone、email、wechat、face_to_face、other')
    best_contact_time = models.CharField(max_length=200, blank=True, verbose_name='最佳联系时间', help_text='如：工作日9-11点')
    interests = models.TextField(blank=True, verbose_name='个人兴趣爱好')
    focus_areas = models.TextField(blank=True, verbose_name='关注领域', help_text='如：技术、管理、市场等')
    
    # 跟踪周期设置（天）
    TRACKING_CYCLE_CHOICES = [
        (7, '每周'),
        (14, '每2周'),
        (21, '每3周'),
        (28, '每月'),
        (42, '每6周'),
        (56, '每8周'),
        (90, '每季度'),
    ]
    
    # 基于角色的默认周期
    ROLE_DEFAULT_CYCLE = {
        'contact_person': 21,      # 对接人：3周
        'promoter': 14,            # 推动人：2周
        'decision_maker': 28,      # 决策人：4周
        'introducer': 28,         # 介绍人：4周
    }
    
    tracking_cycle_days = models.IntegerField(
        choices=TRACKING_CYCLE_CHOICES,
        null=True,
        blank=True,
        verbose_name='跟踪周期（天）',
        help_text='建议的拜访跟踪周期，留空则根据角色和关系等级自动计算'
    )
    
    # 个人标签
    tags = models.JSONField(default=list, blank=True, verbose_name='个人标签', help_text='多选标签，如：技术专家、决策者、影响者、支持者等')
    
    # 其他信息
    is_primary = models.BooleanField(default=False, verbose_name='是否主要联系人')
    notes = models.TextField(blank=True, verbose_name='备注')
    
    # 审批状态
    APPROVAL_STATUS_CHOICES = [
        ('draft', '草稿'),
        ('pending', '待审批'),
        ('approved', '已通过'),
        ('rejected', '已驳回'),
    ]
    approval_status = models.CharField(
        max_length=20, 
        choices=APPROVAL_STATUS_CHOICES, 
        default='draft', 
        verbose_name='审批状态'
    )
    
    # 简历信息（用于验证信息客观性，非必须）
    resume_file = models.FileField(
        upload_to='contact_resumes/%Y/%m/', 
        blank=True, 
        null=True, 
        verbose_name='简历文件',
        help_text='支持格式：PDF、Word、图片；文件大小限制：10MB'
    )
    resume_source = models.CharField(max_length=20, choices=RESUME_SOURCE_CHOICES, blank=True, verbose_name='简历来源')
    resume_upload_time = models.DateTimeField(null=True, blank=True, verbose_name='简历上传时间', help_text='自动设置')
    
    # 审计字段
    created_by = models.ForeignKey(
        User, 
        on_delete=models.PROTECT, 
        related_name='created_contacts', 
        verbose_name='创建人',
        null=True,  # 允许null，用于迁移旧数据
        blank=True
    )
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    updated_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        db_table = 'customer_contact'
        verbose_name = '客户联系人'
        verbose_name_plural = verbose_name
        ordering = ['-is_primary', '-created_time']
        indexes = [
            models.Index(fields=['client', 'role']),
            models.Index(fields=['relationship_level']),
            models.Index(fields=['last_contact_time']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.client.name}"
    
    def calculate_relationship_score(self):
        """计算关系评分（0-100分）"""
        score = 0
        
        # 关系等级评分（40分）
        level_scores = {
            'first_contact': 5,
            'requirement_communication': 10,
            'cooperation_intention': 25,
            'cooperation_recognition': 35,
            'external_partner': 40,
        }
        score += level_scores.get(self.relationship_level, 0)
        
        # 决策影响力评分（30分）
        influence_scores = {
            'high': 30,
            'medium': 20,
            'low': 10,
        }
        score += influence_scores.get(self.decision_influence, 0)
        
        # 联系频率评分（20分）
        frequency_scores = {
            'daily': 20,
            'weekly': 18,
            'monthly': 15,
            'quarterly': 10,
            'occasionally': 5,
            'never': 0,
        }
        score += frequency_scores.get(self.contact_frequency, 0)
        
        # 最后联系时间评分（10分）
        if self.last_contact_time:
            days_since_contact = (timezone.now() - self.last_contact_time).days
            if days_since_contact <= 7:
                score += 10
            elif days_since_contact <= 30:
                score += 7
            elif days_since_contact <= 90:
                score += 4
            else:
                score += 1
        
        return min(score, 100)
    
    def update_last_contact_time(self):
        """更新最后联系时间"""
        self.last_contact_time = timezone.now()
        self.save(update_fields=['last_contact_time'])
    
    def calculate_tracking_cycle(self):
        """根据角色和关系等级计算跟踪周期（天）"""
        from datetime import timedelta
        
        # 如果已设置跟踪周期，直接返回
        if self.tracking_cycle_days:
            return self.tracking_cycle_days
        
        # 基础周期（基于角色）
        base_cycles = {
            'contact_person': 21,      # 对接人：3周
            'promoter': 14,            # 推动人：2周
            'decision_maker': 28,      # 决策人：4周
            'introducer': 28,         # 介绍人：4周
        }
        
        base_cycle = base_cycles.get(self.role, 21)
        
        # 根据关系等级调整
        level_adjustments = {
            'first_contact': -7,           # 首次沟通：缩短周期
            'requirement_communication': 0, # 需求沟通：标准周期
            'cooperation_intention': -7,    # 合作意向：缩短周期
            'cooperation_recognition': 7,   # 合作认可：延长周期
            'external_partner': 14,         # 外部合伙人：延长周期
        }
        
        adjustment = level_adjustments.get(self.relationship_level, 0)
        cycle = base_cycle + adjustment
        
        # 根据关系评分调整
        if self.relationship_score >= 80:
            cycle += 7  # 高关系评分：延长周期
        elif self.relationship_score < 50:
            cycle -= 7  # 低关系评分：缩短周期
        
        # 限制在合理范围内（7-90天）
        return max(7, min(90, cycle))
    
    def get_next_tracking_date(self):
        """计算下次跟踪日期"""
        from datetime import timedelta
        
        cycle_days = self.calculate_tracking_cycle()
        
        if not self.last_contact_time:
            # 如果没有最后联系时间，从今天开始计算
            return timezone.now().date() + timedelta(days=cycle_days)
        
        return self.last_contact_time.date() + timedelta(days=cycle_days)
    
    def is_tracking_overdue(self):
        """判断是否超期未跟踪"""
        next_date = self.get_next_tracking_date()
        return timezone.now().date() > next_date
    
    def get_overdue_days(self):
        """获取超期天数"""
        if not self.is_tracking_overdue():
            return 0
        next_date = self.get_next_tracking_date()
        return (timezone.now().date() - next_date).days
    
    def save(self, *args, **kwargs):
        # 自动计算关系评分
        if kwargs.get('update_relationship_score', True):
            self.relationship_score = self.calculate_relationship_score()
        
        # 如果没有设置跟踪周期，自动计算并保存
        if not self.tracking_cycle_days and kwargs.get('auto_calculate_tracking_cycle', True):
            self.tracking_cycle_days = self.calculate_tracking_cycle()
        
        super().save(*args, **kwargs)


class ContactCareer(models.Model):
    """联系人职业信息模型（支持多个职业记录）"""
    
    contact = models.ForeignKey(
        ClientContact, 
        on_delete=models.CASCADE, 
        related_name='careers', 
        verbose_name='联系人'
    )
    
    # 职业信息
    company = models.CharField(max_length=200, verbose_name='就职公司')
    unified_credit_code = models.CharField(max_length=18, blank=True, verbose_name='社会统一信用代码')
    department = models.CharField(max_length=100, verbose_name='部门')
    position = models.CharField(max_length=100, verbose_name='职位')
    join_date = models.DateField(verbose_name='入职时间')
    leave_date = models.DateField(null=True, blank=True, verbose_name='离职时间')
    
    # 审计字段
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    updated_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        db_table = 'customer_contact_career'
        verbose_name = '联系人职业信息'
        verbose_name_plural = verbose_name
        ordering = ['-join_date']
        indexes = [
            models.Index(fields=['contact']),
            models.Index(fields=['join_date']),
        ]
    
    def __str__(self):
        company_name = self.company or (self.contact.client.name if self.contact else '')
        return f"{self.contact.name if self.contact else ''} - {company_name} - {self.position}"
    
    def calculate_duration(self):
        """计算工作持续时间（年）"""
        if not self.join_date:
            return None
        
        from datetime import date
        end_date = self.leave_date if self.leave_date else date.today()
        
        years = end_date.year - self.join_date.year
        if end_date.month < self.join_date.month or (end_date.month == self.join_date.month and end_date.day < self.join_date.day):
            years -= 1
        
        return max(0, years)


class ContactColleague(models.Model):
    """联系人同事关系人员模型"""
    
    career = models.ForeignKey(
        ContactCareer,
        on_delete=models.CASCADE,
        related_name='colleagues',
        verbose_name='职业信息'
    )
    
    # 同事信息
    department = models.CharField(max_length=100, blank=True, verbose_name='部门')
    name = models.CharField(max_length=100, verbose_name='姓名')
    position = models.CharField(max_length=100, blank=True, verbose_name='职位')
    phone = models.CharField(max_length=20, blank=True, verbose_name='电话')
    
    # 审计字段
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    updated_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        db_table = 'customer_contact_colleague'
        verbose_name = '联系人同事关系人员'
        verbose_name_plural = verbose_name
        ordering = ['created_time']
        indexes = [
            models.Index(fields=['career']),
        ]
    
    def __str__(self):
        dept = self.department or '未填写部门'
        pos = self.position or '未填写职位'
        phone = self.phone or '未填写电话'
        return f"{self.name} - {dept} - {pos} - {phone}"


class School(models.Model):
    """学校管理模型（后台管理）"""
    REGION_CHOICES = [
        ('beijing', '北京'),
        ('tianjin', '天津'),
        ('hebei', '河北'),
        ('shanxi', '山西'),
        ('neimenggu', '内蒙古'),
        ('liaoning', '辽宁'),
        ('jilin', '吉林'),
        ('heilongjiang', '黑龙江'),
        ('shanghai', '上海'),
        ('jiangsu', '江苏'),
        ('zhejiang', '浙江'),
        ('anhui', '安徽'),
        ('fujian', '福建'),
        ('jiangxi', '江西'),
        ('shandong', '山东'),
        ('henan', '河南'),
        ('hubei', '湖北'),
        ('hunan', '湖南'),
        ('guangdong', '广东'),
        ('guangxi', '广西'),
        ('hainan', '海南'),
        ('chongqing', '重庆'),
        ('sichuan', '四川'),
        ('guizhou', '贵州'),
        ('yunnan', '云南'),
        ('xizang', '西藏'),
        ('shaanxi', '陕西'),
        ('gansu', '甘肃'),
        ('qinghai', '青海'),
        ('ningxia', '宁夏'),
        ('xinjiang', '新疆'),
        ('hongkong', '香港'),
        ('macau', '澳门'),
        ('taiwan', '台湾'),
    ]
    
    name = models.CharField(max_length=200, verbose_name='学校名称', db_index=True)
    region = models.CharField(max_length=20, choices=REGION_CHOICES, verbose_name='所在地区')
    is_211 = models.BooleanField(default=False, verbose_name='是否211', help_text='是否属于211工程院校')
    is_985 = models.BooleanField(default=False, verbose_name='是否985', help_text='是否属于985工程院校')
    is_double_first_class = models.BooleanField(default=False, verbose_name='是否双一流', help_text='是否属于双一流建设高校')
    display_order = models.IntegerField(default=0, verbose_name='显示顺序', help_text='数字越小越靠前')
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    notes = models.TextField(blank=True, verbose_name='备注')
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    updated_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        db_table = 'customer_school'
        verbose_name = '学校管理'
        verbose_name_plural = verbose_name
        ordering = ['display_order', 'region', 'name']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['region']),
            models.Index(fields=['is_211', 'is_985']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        tags = []
        if self.is_985:
            tags.append('985')
        if self.is_211:
            tags.append('211')
        if self.is_double_first_class:
            tags.append('双一流')
        tag_str = f" ({', '.join(tags)})" if tags else ""
        return f"{self.name}{tag_str}"
    
    def get_tags_display(self):
        """获取标签显示"""
        tags = []
        if self.is_985:
            tags.append('985')
        if self.is_211:
            tags.append('211')
        if self.is_double_first_class:
            tags.append('双一流')
        return ', '.join(tags) if tags else '普通院校'


class ContactEducation(models.Model):
    """客户人员教育背景模型"""
    DEGREE_CHOICES = [
        ('high_school', '高中'),
        ('college', '专科'),
        ('bachelor', '本科'),
        ('master', '硕士'),
        ('doctor', '博士'),
        ('other', '其他'),
    ]
    
    contact = models.ForeignKey(ClientContact, on_delete=models.CASCADE, related_name='educations', verbose_name='客户人员')
    degree = models.CharField(max_length=20, choices=DEGREE_CHOICES, verbose_name='学历')
    school = models.ForeignKey(
        School,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='educations',
        verbose_name='毕业学校',
        help_text='从后台管理的学校列表中选择'
    )
    school_name = models.CharField(max_length=200, blank=True, verbose_name='毕业学校名称（备用）', help_text='如果学校不在列表中，可手动输入')
    major = models.CharField(max_length=100, blank=True, verbose_name='专业')
    enrollment_date = models.DateField(verbose_name='入学时间')
    graduation_date = models.DateField(verbose_name='毕业时间')
    is_full_time = models.BooleanField(default=True, verbose_name='是否全日制')
    notes = models.TextField(blank=True, verbose_name='备注')
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    updated_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        db_table = 'customer_contact_education'
        verbose_name = '客户人员教育背景'
        verbose_name_plural = verbose_name
        ordering = ['-graduation_date', '-enrollment_date']
    
    def __str__(self):
        school_display = self.school.name if self.school else (self.school_name or '未填写')
        return f"{self.contact.name} - {school_display} - {self.get_degree_display()}"
    
    def get_school_display(self):
        """获取学校显示名称"""
        if self.school:
            return self.school.name
        return self.school_name or '未填写'
    
    def get_duration_years(self):
        """计算学习年限"""
        if self.enrollment_date and self.graduation_date:
            years = self.graduation_date.year - self.enrollment_date.year
            if self.graduation_date.month < self.enrollment_date.month or \
               (self.graduation_date.month == self.enrollment_date.month and self.graduation_date.day < self.enrollment_date.day):
                years -= 1
            return max(0, years)
        return None


class ContactWorkExperience(models.Model):
    """客户人员工作经历模型"""
    contact = models.ForeignKey(ClientContact, on_delete=models.CASCADE, related_name='work_experiences', verbose_name='客户人员')
    company_name = models.CharField(max_length=200, verbose_name='公司名称')
    position = models.CharField(max_length=100, verbose_name='职位')
    department = models.CharField(max_length=100, blank=True, verbose_name='部门')
    start_date = models.DateField(verbose_name='入职时间')
    end_date = models.DateField(null=True, blank=True, verbose_name='离职时间', help_text='为空表示至今')
    office_address = models.CharField(max_length=500, blank=True, verbose_name='办公地址')
    job_description = models.TextField(blank=True, verbose_name='工作内容')
    notes = models.TextField(blank=True, verbose_name='备注')
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    updated_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        db_table = 'customer_contact_work_experience'
        verbose_name = '客户人员工作经历'
        verbose_name_plural = verbose_name
        ordering = ['-start_date']
        indexes = [
            models.Index(fields=['company_name', 'start_date']),
        ]
    
    def __str__(self):
        return f"{self.contact.name} - {self.company_name} - {self.position}"
    
    def get_duration_months(self):
        """计算工作月数"""
        from datetime import date
        end = self.end_date if self.end_date else date.today()
        months = (end.year - self.start_date.year) * 12 + (end.month - self.start_date.month)
        if end.day < self.start_date.day:
            months -= 1
        return max(0, months)
    
    def is_current_job(self):
        """判断是否为当前工作"""
        return self.end_date is None


class ContactJobChange(models.Model):
    """人员工作变动记录模型"""
    CHANGE_TYPE_CHOICES = [
        ('join', '入职'),
        ('leave', '离职'),
        ('transfer', '调岗'),
        ('promotion', '升职'),
        ('demotion', '降职'),
    ]
    
    contact = models.ForeignKey(ClientContact, on_delete=models.CASCADE, related_name='job_changes', verbose_name='客户人员')
    change_type = models.CharField(max_length=20, choices=CHANGE_TYPE_CHOICES, verbose_name='变动类型')
    from_company = models.CharField(max_length=200, blank=True, verbose_name='原公司')
    to_company = models.CharField(max_length=200, verbose_name='新公司')
    from_position = models.CharField(max_length=100, blank=True, verbose_name='原职位')
    to_position = models.CharField(max_length=100, verbose_name='新职位')
    from_department = models.CharField(max_length=100, blank=True, verbose_name='原部门')
    to_department = models.CharField(max_length=100, blank=True, verbose_name='新部门')
    change_date = models.DateField(verbose_name='变动时间')
    change_reason = models.CharField(max_length=500, blank=True, verbose_name='变动原因')
    related_client = models.ForeignKey(
        Client, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='job_changes',
        verbose_name='关联客户',
        help_text='如果新公司是我们的客户'
    )
    notes = models.TextField(blank=True, verbose_name='备注')
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='created_job_changes', verbose_name='创建人')
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    updated_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        db_table = 'customer_contact_job_change'
        verbose_name = '人员工作变动记录'
        verbose_name_plural = verbose_name
        ordering = ['-change_date']
    
    def __str__(self):
        return f"{self.contact.name} - {self.get_change_type_display()} - {self.to_company}"
    
    def is_join_our_client(self):
        """判断是否入职我们的客户公司"""
        return self.related_client is not None and self.change_type == 'join'


class ContactCooperation(models.Model):
    """人员合作信息记录模型"""
    COOPERATION_TYPE_CHOICES = [
        ('project', '项目合作'),
        ('consulting', '咨询服务'),
        ('support', '技术支持'),
        ('training', '培训服务'),
        ('other', '其他'),
    ]
    
    COOPERATION_STATUS_CHOICES = [
        ('ongoing', '进行中'),
        ('completed', '已完成'),
        ('terminated', '已终止'),
    ]
    
    contact = models.ForeignKey(ClientContact, on_delete=models.CASCADE, related_name='cooperations', verbose_name='客户人员')
    cooperation_type = models.CharField(max_length=20, choices=COOPERATION_TYPE_CHOICES, verbose_name='合作类型')
    project = models.ForeignKey(
        'production_management.Project',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='contact_cooperations',
        verbose_name='关联项目'
    )
    cooperation_start_date = models.DateField(verbose_name='合作开始时间')
    cooperation_end_date = models.DateField(null=True, blank=True, verbose_name='合作结束时间')
    cooperation_status = models.CharField(max_length=20, choices=COOPERATION_STATUS_CHOICES, default='ongoing', verbose_name='合作状态')
    cooperation_amount = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True, verbose_name='合作金额（万元）')
    our_contact_person = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='contact_cooperations', verbose_name='我方对接人')
    cooperation_description = models.TextField(blank=True, verbose_name='合作描述')
    satisfaction_score = models.IntegerField(null=True, blank=True, verbose_name='满意度评分', help_text='0-100分')
    notes = models.TextField(blank=True, verbose_name='备注')
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='created_cooperations', verbose_name='创建人')
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    updated_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        db_table = 'customer_contact_cooperation'
        verbose_name = '人员合作信息记录'
        verbose_name_plural = verbose_name
        ordering = ['-cooperation_start_date']
    
    def __str__(self):
        return f"{self.contact.name} - {self.get_cooperation_type_display()}"
    
    def get_duration_months(self):
        """计算合作月数"""
        from datetime import date
        end = self.cooperation_end_date if self.cooperation_end_date else date.today()
        months = (end.year - self.cooperation_start_date.year) * 12 + (end.month - self.cooperation_start_date.month)
        if end.day < self.cooperation_start_date.day:
            months -= 1
        return max(0, months)


class ContactTracking(models.Model):
    """人员跟踪信息记录模型"""
    TRACKING_TYPE_CHOICES = [
        ('phone', '电话跟踪'),
        ('email', '邮件跟踪'),
        ('wechat', '微信跟踪'),
        ('face_to_face', '面谈跟踪'),
        ('meeting', '会议跟踪'),
        ('other', '其他'),
    ]
    
    TRACKING_RESULT_CHOICES = [
        ('success', '成功'),
        ('followup', '待跟进'),
        ('failed', '失败'),
        ('other', '其他'),
    ]
    
    contact = models.ForeignKey(ClientContact, on_delete=models.CASCADE, related_name='trackings', verbose_name='客户人员')
    tracking_type = models.CharField(max_length=20, choices=TRACKING_TYPE_CHOICES, verbose_name='跟踪类型')
    tracking_date = models.DateTimeField(verbose_name='跟踪时间')
    tracking_person = models.ForeignKey(User, on_delete=models.PROTECT, related_name='contact_trackings', verbose_name='跟踪人')
    tracking_content = models.TextField(verbose_name='跟踪内容')
    tracking_result = models.CharField(max_length=20, choices=TRACKING_RESULT_CHOICES, default='followup', verbose_name='跟踪结果')
    next_tracking_date = models.DateField(null=True, blank=True, verbose_name='下次跟踪时间')
    related_opportunity = models.ForeignKey(
        'customer_management.BusinessOpportunity',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='contact_trackings',
        verbose_name='关联商机'
    )
    related_project = models.ForeignKey(
        'production_management.Project',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='contact_trackings',
        verbose_name='关联项目'
    )
    notes = models.TextField(blank=True, verbose_name='备注')
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='created_trackings', verbose_name='创建人')
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    updated_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        db_table = 'customer_contact_tracking'
        verbose_name = '人员跟踪信息记录'
        verbose_name_plural = verbose_name
        ordering = ['-tracking_date']
        indexes = [
            models.Index(fields=['contact', 'tracking_date']),
            models.Index(fields=['next_tracking_date']),
        ]
    
    def __str__(self):
        return f"{self.contact.name} - {self.get_tracking_type_display()} - {self.tracking_date.strftime('%Y-%m-%d')}"
    
    def is_overdue(self):
        """判断是否超期未跟踪"""
        if self.next_tracking_date and self.tracking_result == 'followup':
            from datetime import date
            return date.today() > self.next_tracking_date
        return False


class CustomerRelationship(models.Model):
    """客户关系记录模型（跟进与拜访记录）"""
    RECORD_TYPE_CHOICES = [
        ('followup', '跟进记录'),
        ('visit', '拜访记录'),
    ]
    
    FOLLOWUP_METHOD_CHOICES = [
        ('phone', '电话'),
        ('email', '邮件'),
        ('wechat', '微信'),
        ('visit', '上门'),
        ('meeting', '会议'),
        ('exhibition', '展会'),
        ('other', '其他'),
    ]
    
    VISIT_TYPE_CHOICES = [
        ('cooperation', '合作洽谈'),
        ('contract', '合同洽谈'),
        ('settlement', '结算洽谈'),
        ('payment', '回款洽谈'),
        ('production', '生产洽谈'),
        ('other', '其他'),
    ]
    
    RELATIONSHIP_LEVEL_CHOICES = [
        ('first_contact', '首次沟通'),
        ('requirement_communication', '需求沟通'),
        ('cooperation_intention', '合作意向'),
        ('cooperation_recognition', '合作认可'),
        ('external_partner', '外部合伙人'),
    ]
    
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='relationships', verbose_name='客户')
    record_type = models.CharField(max_length=20, choices=RECORD_TYPE_CHOICES, default='followup', verbose_name='记录类型')
    followup_method = models.CharField(max_length=20, choices=FOLLOWUP_METHOD_CHOICES, default='phone', verbose_name='跟进方式')
    visit_type = models.CharField(max_length=20, choices=VISIT_TYPE_CHOICES, blank=True, null=True, verbose_name='拜访类型', help_text='仅当记录类型为拜访记录时使用')
    content = models.TextField(verbose_name='跟进/拜访内容')
    followup_person = models.ForeignKey(
        User, 
        on_delete=models.PROTECT, 
        related_name='customer_relationships', 
        verbose_name='跟进人',
        null=True,  # 允许null，用于迁移旧数据
        blank=True
    )
    followup_time = models.DateTimeField(default=timezone.now, verbose_name='跟进时间')
    related_contacts = models.ManyToManyField(ClientContact, related_name='relationships', blank=True, verbose_name='关联的客户人员')
    relationship_level = models.CharField(
        max_length=30,
        choices=RELATIONSHIP_LEVEL_CHOICES,
        default='requirement_communication',
        verbose_name='关系等级'
    )
    created_by = models.ForeignKey(
        User, 
        on_delete=models.PROTECT, 
        related_name='created_relationships', 
        verbose_name='创建人',
        null=True,  # 允许null，用于迁移旧数据
        blank=True
    )
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    updated_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    latitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True, verbose_name='纬度')
    longitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True, verbose_name='经度')
    location_address = models.CharField(max_length=500, blank=True, verbose_name='定位地址')
    
    class Meta:
        db_table = 'customer_relationship'
        verbose_name = '客户关系记录'
        verbose_name_plural = verbose_name
        ordering = ['-followup_time', '-created_time']
        indexes = [
            models.Index(fields=['client', 'followup_time']),
            models.Index(fields=['record_type', 'followup_time']),
        ]
    
    def __str__(self):
        return f"{self.client.name} - {self.get_record_type_display()} - {self.followup_time.strftime('%Y-%m-%d')}"
    
    @classmethod
    def get_last_visit_time(cls, contact):
        """获取指定联系人的最近一次拜访时间"""
        last_visit = cls.objects.filter(
            record_type='visit',
            related_contacts=contact
        ).order_by('-followup_time').first()
        return last_visit.followup_time if last_visit else None
    
    @classmethod
    def get_days_since_last_visit(cls, contact):
        """获取指定联系人距离最近一次拜访的天数"""
        last_visit_time = cls.get_last_visit_time(contact)
        if last_visit_time:
            delta = timezone.now() - last_visit_time
            return delta.days
        return None


class CustomerRelationshipUpgrade(models.Model):
    """客户关系升级记录模型"""
    RELATIONSHIP_LEVEL_CHOICES = [
        ('first_contact', '首次沟通'),
        ('requirement_communication', '需求沟通'),
        ('cooperation_intention', '合作意向'),
        ('cooperation_recognition', '合作认可'),
        ('external_partner', '外部合伙人'),
    ]
    
    APPROVAL_STATUS_CHOICES = [
        ('pending', '待审批'),
        ('approved', '已通过'),
        ('rejected', '已驳回'),
        ('withdrawn', '已撤回'),
    ]
    
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='relationship_upgrades', verbose_name='客户')
    from_level = models.CharField(max_length=30, choices=RELATIONSHIP_LEVEL_CHOICES, verbose_name='原关系等级')
    to_level = models.CharField(max_length=30, choices=RELATIONSHIP_LEVEL_CHOICES, verbose_name='目标关系等级')
    upgrade_reason = models.TextField(verbose_name='升级原因')
    related_contacts = models.ManyToManyField(ClientContact, related_name='relationship_upgrades', blank=True, verbose_name='关联的客户人员')
    approval_status = models.CharField(
        max_length=20,
        choices=APPROVAL_STATUS_CHOICES,
        default='pending',
        verbose_name='审批状态',
        help_text='如果升级到"合作意向"、"合作认可"或"外部合伙人"需要审批'
    )
    approval_instance = models.ForeignKey(
        'workflow_engine.ApprovalInstance',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='relationship_upgrades',
        verbose_name='审批实例'
    )
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='created_relationship_upgrades', verbose_name='创建人')
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    approved_time = models.DateTimeField(null=True, blank=True, verbose_name='审批通过时间')
    
    class Meta:
        db_table = 'customer_relationship_upgrade'
        verbose_name = '客户关系升级记录'
        verbose_name_plural = verbose_name
        ordering = ['-created_time']
        indexes = [
            models.Index(fields=['client', 'approval_status']),
            models.Index(fields=['to_level', 'approval_status']),
        ]
    
    def __str__(self):
        return f"{self.client.name} - {self.get_from_level_display()} → {self.get_to_level_display()}"
    
    def requires_approval(self):
        """判断是否需要审批"""
        # 升级到"合作意向"、"合作认可"或"外部合伙人"需要审批
        return self.to_level in ['cooperation_intention', 'cooperation_recognition', 'external_partner']
    
    def can_auto_approve(self):
        """判断是否可以自动生效（无需审批）"""
        # 升级到"需求沟通"无需审批，直接生效
        return self.to_level == 'requirement_communication'


class BusinessExpenseApplication(models.Model):
    """业务费申请模型"""
    EXPENSE_TYPE_CHOICES = [
        ('entertainment', '招待费'),
        ('gift', '礼品费'),
        ('travel', '差旅费'),
        ('meal', '餐费'),
        ('transportation', '交通费'),
        ('communication', '通讯费'),
        ('other', '其他费用'),
    ]
    
    APPROVAL_STATUS_CHOICES = [
        ('draft', '草稿'),
        ('pending', '待审批'),
        ('approved', '已通过'),
        ('rejected', '已驳回'),
        ('withdrawn', '已撤回'),
    ]
    
    application_number = models.CharField(max_length=100, unique=True, verbose_name='申请单号', help_text='自动生成')
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='business_expense_applications', verbose_name='关联客户')
    expense_type = models.CharField(max_length=30, choices=EXPENSE_TYPE_CHOICES, verbose_name='费用类型')
    amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0.01)], verbose_name='费用金额')
    expense_date = models.DateField(verbose_name='费用发生日期')
    description = models.TextField(verbose_name='费用说明')
    related_contacts = models.ManyToManyField(ClientContact, related_name='business_expense_applications', blank=True, verbose_name='关联的客户人员')
    attachment = models.FileField(upload_to='business_expenses/%Y/%m/', null=True, blank=True, verbose_name='附件', help_text='支持上传发票、凭证等')
    
    approval_status = models.CharField(
        max_length=20,
        choices=APPROVAL_STATUS_CHOICES,
        default='draft',
        verbose_name='审批状态'
    )
    approval_instance = models.ForeignKey(
        'workflow_engine.ApprovalInstance',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='business_expense_applications',
        verbose_name='审批实例'
    )
    
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='created_business_expense_applications', verbose_name='创建人')
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    approved_time = models.DateTimeField(null=True, blank=True, verbose_name='审批通过时间')
    updated_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        db_table = 'customer_business_expense_application'
        verbose_name = '业务费申请'
        verbose_name_plural = verbose_name
        ordering = ['-created_time']
        indexes = [
            models.Index(fields=['client', 'approval_status']),
            models.Index(fields=['expense_date']),
            models.Index(fields=['application_number']),
        ]
    
    def __str__(self):
        return f"{self.application_number} - {self.client.name} - ¥{self.amount}"
    
    def save(self, *args, **kwargs):
        if not self.application_number:
            # 自动生成申请单号：BEA-YYYYMMDD-XXXX
            from datetime import datetime
            date_str = datetime.now().strftime('%Y%m%d')
            last_application = BusinessExpenseApplication.objects.filter(
                application_number__startswith=f'BEA-{date_str}-'
            ).order_by('-application_number').first()
            
            if last_application:
                last_num = int(last_application.application_number.split('-')[-1])
                new_num = last_num + 1
            else:
                new_num = 1
            
            self.application_number = f'BEA-{date_str}-{new_num:04d}'
        
        super().save(*args, **kwargs)


class ClientProject(models.Model):
    """客户项目关联模型（用于统计）"""
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='projects', verbose_name='客户')
    project = models.ForeignKey('production_management.Project', on_delete=models.CASCADE, verbose_name='项目')
    service_type = models.CharField(max_length=50, blank=True, verbose_name='服务类型')
    contract_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='合同金额')
    start_date = models.DateField(null=True, blank=True, verbose_name='开始日期')
    end_date = models.DateField(null=True, blank=True, verbose_name='结束日期')
    status = models.CharField(max_length=20, blank=True, verbose_name='项目状态')
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    
    class Meta:
        db_table = 'customer_client_project'
        verbose_name = '客户项目'
        verbose_name_plural = verbose_name
        unique_together = [['client', 'project']]
    
    def __str__(self):
        return f"{self.client.name} - {self.project.name if self.project else '未知项目'}"


# BusinessContract和BusinessPaymentPlan已迁移到production_management模块
# 使用以下方式引用：
# from backend.apps.production_management.models import BusinessContract, BusinessPaymentPlan

class ContractNegotiation(models.Model):
    """合同洽谈记录"""
    NEGOTIATION_TYPE_CHOICES = [
        ('price', '价格洽谈'),
        ('terms', '条款洽谈'),
        ('schedule', '进度洽谈'),
        ('payment', '付款方式洽谈'),
        ('other', '其他洽谈'),
    ]
    
    STATUS_CHOICES = [
        ('ongoing', '进行中'),
        ('completed', '已完成'),
        ('suspended', '已暂停'),
        ('cancelled', '已取消'),
    ]
    
    # 关联信息
    contract = models.ForeignKey('production_management.BusinessContract', on_delete=models.CASCADE, related_name='negotiations', verbose_name='关联合同', null=True, blank=True, help_text='可选，如果洽谈时合同尚未创建可留空')
    client = models.ForeignKey('Client', on_delete=models.PROTECT, related_name='contract_negotiations', null=True, blank=True, verbose_name='客户', help_text='如果未关联合同，则必须填写客户')
    project = models.ForeignKey('production_management.Project', on_delete=models.SET_NULL, null=True, blank=True, related_name='contract_negotiations', verbose_name='关联项目')
    
    # 基本信息
    negotiation_number = models.CharField(max_length=100, unique=True, blank=True, null=True, verbose_name='洽谈编号', help_text='自动生成：NT-YYYY-NNNN')
    negotiation_type = models.CharField(max_length=20, choices=NEGOTIATION_TYPE_CHOICES, default='other', verbose_name='洽谈类型')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ongoing', verbose_name='洽谈状态')
    title = models.CharField(max_length=200, verbose_name='洽谈主题')
    content = models.TextField(verbose_name='洽谈内容', help_text='详细记录洽谈过程中的讨论内容、双方意见等')
    
    # 参与人员
    participants = models.ManyToManyField(User, related_name='participated_negotiations', verbose_name='参与人员', help_text='我方参与洽谈的人员')
    client_participants = models.TextField(blank=True, verbose_name='客户参与人员', help_text='客户方参与洽谈的人员，多个用逗号分隔')
    
    # 时间信息
    negotiation_date = models.DateField(default=timezone.now, verbose_name='洽谈日期')
    negotiation_start_time = models.TimeField(null=True, blank=True, verbose_name='开始时间')
    negotiation_end_time = models.TimeField(null=True, blank=True, verbose_name='结束时间')
    next_negotiation_date = models.DateField(null=True, blank=True, verbose_name='下次洽谈日期')
    
    # 洽谈结果
    result_summary = models.TextField(blank=True, verbose_name='洽谈结果摘要', help_text='本次洽谈达成的共识、待解决问题等')
    agreed_items = models.TextField(blank=True, verbose_name='已达成事项', help_text='双方已达成一致的事项')
    pending_items = models.TextField(blank=True, verbose_name='待解决事项', help_text='需要进一步讨论或解决的问题')
    
    # 附件和备注
    attachments = models.TextField(blank=True, verbose_name='附件说明', help_text='洽谈过程中涉及的文档、资料等')
    notes = models.TextField(blank=True, verbose_name='备注')
    
    # 审计字段
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='created_contract_negotiations', verbose_name='创建人')
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    updated_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        db_table = 'business_contract_negotiation'
        verbose_name = '合同洽谈记录'
        verbose_name_plural = verbose_name
        ordering = ['-negotiation_date', '-created_time']
        indexes = [
            models.Index(fields=['contract']),
            models.Index(fields=['client']),
            models.Index(fields=['negotiation_date']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        contract_info = self.contract.contract_number if self.contract else (self.client.name if self.client else '未关联')
        return f"{self.title} - {contract_info}"
    
    def save(self, *args, **kwargs):
        # 自动生成洽谈编号
        if not self.negotiation_number:
            from django.db.models import Max
            current_year = timezone.now().year
            max_number = ContractNegotiation.objects.filter(
                negotiation_number__startswith=f'NT-{current_year}-'
            ).aggregate(max_num=Max('negotiation_number'))['max_num']
            
            if max_number:
                try:
                    seq = int(max_number.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    seq = 1
            else:
                seq = 1
            
            self.negotiation_number = f'NT-{current_year}-{seq:04d}'
        
        super().save(*args, **kwargs)
        return f"{self.contract.contract_number} - {from_label} → {to_label}"


# ==================== 商机管理模块 ====================

class BusinessOpportunity(models.Model):
    """商机管理"""
    STATUS_CHOICES = [
        ('potential', '潜在客户'),           # 10%
        ('initial_contact', '初步接触'),     # 30%
        ('requirement_confirmed', '需求确认'), # 50%
        ('quotation', '方案报价'),          # 70%
        ('negotiation', '商务谈判'),         # 90%
        ('won', '赢单'),
        ('lost', '输单'),
        ('cancelled', '已取消'),
    ]
    
    URGENCY_CHOICES = [
        ('normal', '普通'),
        ('urgent', '紧急'),
        ('very_urgent', '特急'),
    ]
    
    OPPORTUNITY_TYPE_CHOICES = [
        ('project_cooperation', '项目合作'),
        ('centralized_procurement', '集中采购'),
    ]
    
    APPROVAL_STATUS_CHOICES = [
        ('pending', '待审批'),
        ('approved', '已审批'),
        ('rejected', '已驳回'),
    ]
    
    # 基本信息
    opportunity_number = models.CharField(max_length=50, unique=True, blank=True, null=True, verbose_name='商机编号', help_text='自动生成：SJ-YYYYMMDD-0000')
    name = models.CharField(max_length=200, verbose_name='商机名称')
    client = models.ForeignKey(Client, on_delete=models.PROTECT, related_name='opportunities', verbose_name='关联客户')
    business_manager = models.ForeignKey(User, on_delete=models.PROTECT, related_name='managed_opportunities', verbose_name='负责商务')
    opportunity_type = models.CharField(max_length=30, choices=OPPORTUNITY_TYPE_CHOICES, blank=True, verbose_name='商机类型')
    service_type = models.ForeignKey('production_management.ServiceType', on_delete=models.SET_NULL, null=True, blank=True, related_name='opportunities', verbose_name='服务类型')
    
    # 项目信息
    project_name = models.CharField(max_length=200, blank=True, verbose_name='项目名称')
    project_address = models.CharField(max_length=500, blank=True, verbose_name='项目地址')
    project_type = models.CharField(max_length=50, blank=True, verbose_name='项目业态', help_text='住宅/综合体/商业/写字楼等')
    building_area = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True, verbose_name='建筑面积（平方米）')
    drawing_stage = models.ForeignKey('production_management.DesignStage', on_delete=models.SET_NULL, null=True, blank=True, related_name='opportunities', verbose_name='图纸阶段', db_column='drawing_stage')
    
    # 金额和概率
    estimated_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name='预计金额（万元）')
    success_probability = models.IntegerField(default=10, verbose_name='成功概率（%）', help_text='10/30/50/70/90')
    weighted_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name='加权金额', help_text='预计金额 × 成功概率')
    
    # 状态和时间
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='potential', verbose_name='商机状态')
    urgency = models.CharField(max_length=20, choices=URGENCY_CHOICES, default='normal', verbose_name='紧急程度')
    expected_sign_date = models.DateField(null=True, blank=True, verbose_name='预计签约时间')
    actual_sign_date = models.DateField(null=True, blank=True, verbose_name='实际签约日期')
    
    # 审批信息
    approval_status = models.CharField(max_length=20, choices=APPROVAL_STATUS_CHOICES, default='pending', verbose_name='审批状态')
    approver = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_opportunities', verbose_name='审批人')
    approved_time = models.DateTimeField(null=True, blank=True, verbose_name='审批时间')
    approval_comment = models.TextField(blank=True, verbose_name='审批意见')
    
    # 赢单/输单信息
    actual_amount = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True, verbose_name='实际签约金额（万元）')
    contract_number = models.CharField(max_length=100, blank=True, verbose_name='合同编号')
    win_reason = models.TextField(blank=True, verbose_name='赢单原因')
    loss_reason = models.TextField(blank=True, verbose_name='输单原因')
    
    # 健康度
    health_score = models.IntegerField(default=0, verbose_name='健康度评分', help_text='0-100分')
    
    # 其他信息
    description = models.TextField(blank=True, verbose_name='商机描述')
    notes = models.TextField(blank=True, verbose_name='备注')
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    
    # 审计字段
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='created_opportunities', verbose_name='创建人')
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    updated_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        db_table = 'business_opportunity'
        verbose_name = '商机'
        verbose_name_plural = verbose_name
        ordering = ['-created_time']
        indexes = [
            models.Index(fields=['opportunity_number']),
            models.Index(fields=['status']),
            models.Index(fields=['business_manager', 'status']),
            models.Index(fields=['expected_sign_date']),
        ]
    
    def __str__(self):
        return f"{self.opportunity_number or '未编号'} - {self.name}"
    
    def save(self, *args, **kwargs):
        # 自动生成商机编号：SJ-YYYYMMDD-0000（连续编号）
        if not self.opportunity_number:
            from django.db.models import Max
            from datetime import datetime
            current_date = datetime.now().strftime('%Y%m%d')
            date_prefix = f'SJ-{current_date}-'
            
            # 查找当天最大编号
            max_opp = BusinessOpportunity.objects.filter(
                opportunity_number__startswith=date_prefix
            ).aggregate(max_num=Max('opportunity_number'))['max_num']
            
            if max_opp:
                try:
                    # 提取最后4位数字作为序号
                    seq = int(max_opp.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    seq = 1
            else:
                seq = 1
            
            self.opportunity_number = f'{date_prefix}{seq:04d}'
        
        # 自动计算加权金额
        if self.estimated_amount and self.success_probability:
            from decimal import Decimal
            self.weighted_amount = (self.estimated_amount * Decimal(self.success_probability)) / 100
        
        # 自动计算健康度（简化版，后续可以完善）
        if not self.health_score or kwargs.get('update_health', False):
            self.health_score = self._calculate_health_score()
        
        super().save(*args, **kwargs)
    
    def _calculate_health_score(self):
        """计算健康度评分"""
        score = 0
        
        # 1. 跟进及时性（25%）
        followup_score = 0
        # 只有在实例有主键时才访问关联关系
        last_followup = None
        if self.pk and hasattr(self, 'followups'):
            try:
                last_followup = self.followups.order_by('-follow_date').first()
            except Exception:
                pass
        if last_followup and last_followup.next_follow_date:
            days_overdue = (timezone.now().date() - last_followup.next_follow_date).days
            if days_overdue <= 0:
                # 及时跟进
                followup_score = 25
            elif days_overdue <= 3:
                # 轻微延迟
                followup_score = 20
            elif days_overdue <= 7:
                # 中度延迟
                followup_score = 12
            else:
                # 严重延迟
                followup_score = 5
        elif last_followup:
            # 有跟进记录但没有下次跟进计划
            days_since_last = (timezone.now().date() - last_followup.follow_date).days
            if days_since_last <= 7:
                followup_score = 20
            elif days_since_last <= 14:
                followup_score = 12
            else:
                followup_score = 5
        else:
            # 没有跟进记录
            created_date = self.created_time.date() if self.created_time else timezone.now().date()
            days_since_created = (timezone.now().date() - created_date).days
            if days_since_created <= 3:
                followup_score = 15
            elif days_since_created <= 7:
                followup_score = 8
            else:
                followup_score = 0
        score += followup_score
        
        # 2. 信息完整性（20%）
        info_score = 0
        required_fields = [
            ('project_name', 5),
            ('project_address', 5),
            ('estimated_amount', 5),
            ('expected_sign_date', 5),
        ]
        for field_name, field_score in required_fields:
            field_value = getattr(self, field_name, None)
            if field_value:
                info_score += field_score
        score += info_score
        
        # 3. 客户互动频次（20%）
        interaction_score = 0
        followup_count = 0
        if self.pk and hasattr(self, 'followups'):
            try:
                followup_count = self.followups.count()
            except Exception:
                pass
        if followup_count >= 5:
            interaction_score = 20
        elif followup_count >= 3:
            interaction_score = 15
        elif followup_count >= 2:
            interaction_score = 10
        elif followup_count >= 1:
            interaction_score = 5
        else:
            interaction_score = 0
        score += interaction_score
        
        # 4. 阶段推进速度（35%）
        progress_score = 0
        days_since_created = (timezone.now().date() - self.created_time.date()).days
        
        # 根据状态和停留时间计算
        if self.status == 'won':
            progress_score = 35
        elif self.status == 'negotiation':
            if days_since_created <= 30:
                progress_score = 35
            elif days_since_created <= 45:
                progress_score = 28
            elif days_since_created <= 60:
                progress_score = 20
            else:
                progress_score = 10
        elif self.status == 'quotation':
            if days_since_created <= 20:
                progress_score = 30
            elif days_since_created <= 30:
                progress_score = 22
            elif days_since_created <= 45:
                progress_score = 15
            else:
                progress_score = 8
        elif self.status == 'requirement_confirmed':
            if days_since_created <= 15:
                progress_score = 25
            elif days_since_created <= 25:
                progress_score = 18
            elif days_since_created <= 35:
                progress_score = 12
            else:
                progress_score = 6
        elif self.status == 'initial_contact':
            if days_since_created <= 10:
                progress_score = 20
            elif days_since_created <= 20:
                progress_score = 15
            elif days_since_created <= 30:
                progress_score = 10
            else:
                progress_score = 5
        elif self.status == 'potential':
            if days_since_created <= 7:
                progress_score = 15
            elif days_since_created <= 14:
                progress_score = 10
            else:
                progress_score = 5
        else:
            progress_score = 5
        score += progress_score
        
        return min(score, 100)
    
    def get_health_analysis(self):
        """获取健康度详细分析"""
        analysis = {
            'total_score': self.health_score,
            'health_level': 'high' if self.health_score >= 80 else ('medium' if self.health_score >= 60 else 'low'),
            'dimensions': {},
            'suggestions': []
        }
        
        # 跟进及时性分析
        last_followup = None
        if self.pk and hasattr(self, 'followups'):
            try:
                last_followup = self.followups.order_by('-follow_date').first()
            except Exception:
                pass
        followup_timeliness = 0
        if last_followup and last_followup.next_follow_date:
            days_overdue = (timezone.now().date() - last_followup.next_follow_date).days
            if days_overdue <= 0:
                followup_timeliness = 100
            elif days_overdue <= 3:
                followup_timeliness = 80
            elif days_overdue <= 7:
                followup_timeliness = 48
            else:
                followup_timeliness = 20
                analysis['suggestions'].append('跟进已超期，建议立即安排跟进')
        elif last_followup:
            days_since_last = (timezone.now().date() - last_followup.follow_date).days
            if days_since_last <= 7:
                followup_timeliness = 80
            elif days_since_last <= 14:
                followup_timeliness = 48
            else:
                followup_timeliness = 20
                analysis['suggestions'].append('长时间未跟进，建议尽快安排跟进')
        else:
            followup_timeliness = 0
            analysis['suggestions'].append('尚未有跟进记录，建议尽快建立首次联系')
        
        analysis['dimensions']['followup_timeliness'] = {
            'score': followup_timeliness,
            'weight': 0.25,
            'label': '跟进及时性'
        }
        
        # 信息完整性分析
        required_fields = ['project_name', 'project_address', 'estimated_amount', 'expected_sign_date']
        filled_fields = sum(1 for field in required_fields if getattr(self, field, None))
        info_completeness = (filled_fields / len(required_fields)) * 100
        if info_completeness < 100:
            missing = [f for f in required_fields if not getattr(self, f, None)]
            analysis['suggestions'].append(f'信息不完整，建议完善：{", ".join(missing)}')
        
        analysis['dimensions']['information_completeness'] = {
            'score': info_completeness,
            'weight': 0.20,
            'label': '信息完整性'
        }
        
        # 客户互动频次分析
        followup_count = 0
        if self.pk and hasattr(self, 'followups'):
            try:
                followup_count = self.followups.count()
            except Exception:
                pass
        if followup_count >= 5:
            interaction_score = 100
        elif followup_count >= 3:
            interaction_score = 75
        elif followup_count >= 2:
            interaction_score = 50
        elif followup_count >= 1:
            interaction_score = 25
        else:
            interaction_score = 0
            analysis['suggestions'].append('客户互动较少，建议增加跟进频次')
        
        analysis['dimensions']['client_interaction'] = {
            'score': interaction_score,
            'weight': 0.20,
            'label': '客户互动频次'
        }
        
        # 阶段推进速度分析
        days_since_created = (timezone.now().date() - self.created_time.date()).days
        progress_score = 0
        if self.status == 'won':
            progress_score = 100
        elif self.status == 'negotiation':
            progress_score = min(100, max(30, 100 - (days_since_created - 30) * 2))
        elif self.status == 'quotation':
            progress_score = min(100, max(25, 100 - (days_since_created - 20) * 3))
        elif self.status == 'requirement_confirmed':
            progress_score = min(100, max(20, 100 - (days_since_created - 15) * 4))
        elif self.status == 'initial_contact':
            progress_score = min(100, max(15, 100 - (days_since_created - 10) * 5))
        else:
            progress_score = min(100, max(10, 100 - days_since_created * 6))
        
        if progress_score < 50:
            analysis['suggestions'].append('阶段推进较慢，建议加快进度或重新评估商机')
        
        analysis['dimensions']['stage_progress'] = {
            'score': progress_score,
            'weight': 0.35,
            'label': '阶段推进速度'
        }
        
        return analysis
    
    @classmethod
    def get_valid_transitions(cls, current_status):
        """获取当前状态可以流转到的状态列表"""
        transitions = {
            'potential': ['initial_contact', 'cancelled'],
            'initial_contact': ['requirement_confirmed', 'potential', 'cancelled'],
            'requirement_confirmed': ['quotation', 'initial_contact', 'cancelled'],
            'quotation': ['negotiation', 'requirement_confirmed', 'cancelled'],
            'negotiation': ['won', 'lost', 'quotation', 'cancelled'],
            'won': [],
            'lost': [],
            'cancelled': [],
        }
        return transitions.get(current_status, [])
    
    def can_transition_to(self, target_status):
        """检查是否可以流转到目标状态"""
        valid_transitions = self.get_valid_transitions(self.status)
        return target_status in valid_transitions
    
    def transition_to(self, target_status, actor=None, comment=''):
        """执行状态流转"""
        if not self.can_transition_to(target_status):
            raise ValueError(f"无法从 {self.get_status_display()} 流转到 {dict(self.STATUS_CHOICES).get(target_status, target_status)}")
        
        old_status = self.status
        self.status = target_status
        self._status_change_actor = actor
        self._status_change_comment = comment
        self.save()
        
        # 记录状态流转日志
        if self.pk:
            OpportunityStatusLog.objects.create(
                opportunity=self,
                from_status=old_status,
                to_status=target_status,
                actor=actor,
                comment=comment,
            )
        
        return True


class OpportunityFollowUp(models.Model):
    """商机跟进记录"""
    FOLLOW_TYPE_CHOICES = [
        ('phone', '电话沟通'),
        ('visit', '上门拜访'),
        ('online_meeting', '线上会议'),
        ('email', '邮件沟通'),
        ('other', '其他'),
    ]
    
    opportunity = models.ForeignKey(BusinessOpportunity, on_delete=models.CASCADE, related_name='followups', verbose_name='商机')
    follow_date = models.DateField(verbose_name='跟进日期')
    follow_type = models.CharField(max_length=20, choices=FOLLOW_TYPE_CHOICES, default='phone', verbose_name='跟进方式')
    participants = models.CharField(max_length=500, blank=True, verbose_name='参与人员')
    content = models.TextField(verbose_name='跟进内容')
    customer_feedback = models.TextField(blank=True, verbose_name='客户反馈')
    next_plan = models.TextField(blank=True, verbose_name='下一步计划')
    next_follow_date = models.DateField(null=True, blank=True, verbose_name='预计下次跟进')
    
    # 审计字段
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='created_followups', verbose_name='创建人')
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    
    class Meta:
        db_table = 'business_opportunity_followup'
        verbose_name = '商机跟进记录'
        verbose_name_plural = verbose_name
        ordering = ['-follow_date', '-created_time']
    
    def __str__(self):
        return f"{self.opportunity.opportunity_number} - {self.follow_date}"


class QuotationRule(models.Model):
    """报价规则配置"""
    RULE_TYPE_CHOICES = [
        ('rate', '费率'),
        ('unit_price', '单价'),
        ('fixed', '固定金额'),
    ]
    
    name = models.CharField(max_length=100, verbose_name='规则名称')
    rule_type = models.CharField(max_length=20, choices=RULE_TYPE_CHOICES, verbose_name='规则类型')
    project_type = models.CharField(max_length=50, blank=True, verbose_name='项目业态')
    service_type = models.CharField(max_length=50, blank=True, verbose_name='服务类型')
    structure_type = models.CharField(max_length=50, blank=True, verbose_name='结构形式')
    
    # 规则参数（JSON格式存储复杂规则）
    rule_params = models.JSONField(default=dict, verbose_name='规则参数', help_text='存储费率、单价等参数')
    
    # 适用范围
    min_area = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True, verbose_name='最小面积')
    max_area = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True, verbose_name='最大面积')
    
    # 调整系数
    adjustment_factor = models.DecimalField(max_digits=5, decimal_places=2, default=1.0, verbose_name='调整系数')
    
    # 状态
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    description = models.TextField(blank=True, verbose_name='规则说明')
    
    # 审计字段
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_quotation_rules', verbose_name='创建人')
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    updated_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        db_table = 'business_quotation_rule'
        verbose_name = '报价规则'
        verbose_name_plural = verbose_name
        ordering = ['-created_time']
    
    def __str__(self):
        return self.name


class OpportunityQuotation(models.Model):
    """商机报价"""
    VERSION_TYPE_CHOICES = [
        ('draft', '初稿报价'),
        ('customer', '客户报价'),
        ('final', '最终报价'),
    ]
    
    # 报价模式选择（7种模式）
    QUOTATION_MODE_CHOICES = [
        ('rate', '纯费率模式'),
        ('base_fee_rate', '基本费+费率模式'),
        ('fixed', '包干价模式'),
        ('segmented', '分段累进模式'),
        ('min_savings_rate', '最低节省+费率模式'),
        ('performance_linked', '绩效挂钩模式'),
        ('hybrid', '混合计价模式'),
    ]
    
    opportunity = models.ForeignKey(BusinessOpportunity, on_delete=models.CASCADE, related_name='quotations', verbose_name='商机')
    version_type = models.CharField(max_length=20, choices=VERSION_TYPE_CHOICES, default='draft', verbose_name='版本类型')
    version_number = models.IntegerField(default=1, verbose_name='版本号')
    
    # 报价模式（新增）
    quotation_mode = models.CharField(
        max_length=30, 
        choices=QUOTATION_MODE_CHOICES, 
        default='rate', 
        verbose_name='报价模式',
        help_text='选择报价计算模式'
    )
    mode_params = models.JSONField(
        default=dict, 
        blank=True, 
        verbose_name='模式参数',
        help_text='JSON格式存储报价模式相关参数（费率、基本费、分段配置等）'
    )
    cap_fee = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        null=True, 
        blank=True, 
        verbose_name='封顶费（万元）',
        help_text='服务费上限，超过此金额按封顶费计算（可选）'
    )
    saved_amount = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        null=True, 
        blank=True, 
        default=0,
        verbose_name='节省金额（万元）',
        help_text='用于计算服务费的节省金额'
    )
    
    # 报价参数（保留原有字段以保持兼容性）
    building_area = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True, verbose_name='建筑面积（平方米）')
    project_type = models.CharField(max_length=50, blank=True, verbose_name='项目业态')
    service_type = models.CharField(max_length=50, blank=True, verbose_name='服务类型')
    structure_type = models.CharField(max_length=50, blank=True, verbose_name='结构形式')
    
    # 报价结果（保留原有字段，同时支持新模式）
    base_quotation = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name='基准报价（万元）', help_text='旧版报价字段，保留兼容性')
    adjustment_factor = models.DecimalField(max_digits=5, decimal_places=2, default=1.0, verbose_name='调整系数', help_text='旧版报价字段，保留兼容性')
    service_fee = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        default=0, 
        verbose_name='服务费（万元）',
        help_text='根据报价模式计算的服务费'
    )
    final_quotation = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        default=0, 
        verbose_name='最终报价（万元）',
        help_text='最终报价金额（兼容旧版：base_quotation × adjustment_factor；新版：service_fee）'
    )
    calculation_steps = models.JSONField(
        default=list, 
        blank=True, 
        verbose_name='计算步骤',
        help_text='JSON格式存储计算过程，用于展示计算明细'
    )
    quotation_note = models.TextField(blank=True, verbose_name='报价说明')
    
    # 使用的规则（保留兼容性）
    quotation_rule = models.ForeignKey(QuotationRule, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='使用的报价规则', help_text='旧版报价规则，保留兼容性')
    
    # 文件
    quotation_file = models.FileField(upload_to='quotations/%Y/%m/', blank=True, null=True, verbose_name='报价文件')
    
    # 审计字段
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='created_quotations', verbose_name='创建人')
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    updated_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        db_table = 'business_opportunity_quotation'
        verbose_name = '商机报价'
        verbose_name_plural = verbose_name
        ordering = ['-version_number', '-created_time']
        unique_together = [['opportunity', 'version_number']]
    
    def __str__(self):
        return f"{self.opportunity.opportunity_number} - {self.get_version_type_display()} v{self.version_number}"
    
    def save(self, *args, **kwargs):
        # 如果使用新模式，通过计算引擎计算服务费
        if self.quotation_mode and self.saved_amount:
            try:
                from backend.apps.customer_management.services.quotation_calculator import QuotationCalculator
                calculator = QuotationCalculator()
                result = calculator.calculate(
                    mode=self.quotation_mode,
                    saved_amount=float(self.saved_amount),
                    mode_params=self.mode_params or {},
                    cap_fee=float(self.cap_fee) if self.cap_fee else None
                )
                self.service_fee = result['service_fee']
                self.calculation_steps = result.get('calculation_steps', [])
                self.final_quotation = self.service_fee
            except Exception as e:
                # 如果计算失败，记录错误但不阻止保存
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f'报价计算失败: {str(e)}')
                # 保留旧版计算逻辑作为降级方案
                if self.base_quotation and self.adjustment_factor:
                    from decimal import Decimal
                    self.final_quotation = self.base_quotation * Decimal(str(self.adjustment_factor))
        else:
            # 兼容旧版计算逻辑
            if self.base_quotation and self.adjustment_factor:
                from decimal import Decimal
                self.final_quotation = self.base_quotation * Decimal(str(self.adjustment_factor))
        
        super().save(*args, **kwargs)


class OpportunityApproval(models.Model):
    """商机审批记录"""
    APPROVAL_RESULT_CHOICES = [
        ('approved', '通过'),
        ('rejected', '驳回'),
        ('pending', '待审核'),
    ]
    
    opportunity = models.ForeignKey(BusinessOpportunity, on_delete=models.CASCADE, related_name='approvals', verbose_name='商机')
    approver = models.ForeignKey(User, on_delete=models.PROTECT, related_name='opportunity_approvals', verbose_name='审核人')
    approval_level = models.IntegerField(default=1, verbose_name='审核层级', help_text='1=商务部经理, 2=商务总监, 3=总经理')
    result = models.CharField(max_length=20, choices=APPROVAL_RESULT_CHOICES, default='pending', verbose_name='审核结果')
    comment = models.TextField(blank=True, verbose_name='审核意见')
    approval_time = models.DateTimeField(null=True, blank=True, verbose_name='审核时间')
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    
    class Meta:
        db_table = 'business_opportunity_approval'
        verbose_name = '商机审批记录'
        verbose_name_plural = verbose_name
        ordering = ['approval_level', '-created_time']
    
    def __str__(self):
        return f"{self.opportunity.opportunity_number} - {self.approver.username} - {self.get_result_display()}"


class OpportunityStatusLog(models.Model):
    """商机状态流转日志"""
    opportunity = models.ForeignKey(BusinessOpportunity, on_delete=models.CASCADE, related_name='status_logs', verbose_name='商机')
    from_status = models.CharField(max_length=30, choices=BusinessOpportunity.STATUS_CHOICES, blank=True, verbose_name='原状态')
    to_status = models.CharField(max_length=30, choices=BusinessOpportunity.STATUS_CHOICES, verbose_name='目标状态')
    actor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='opportunity_status_actions', verbose_name='操作人')
    comment = models.TextField(blank=True, verbose_name='备注说明')
    created_time = models.DateTimeField(default=timezone.now, verbose_name='操作时间')
    
    class Meta:
        db_table = 'business_opportunity_status_log'
        verbose_name = '商机状态流转日志'
        verbose_name_plural = verbose_name
        ordering = ['-created_time']
    
    def __str__(self):
        from_label = dict(BusinessOpportunity.STATUS_CHOICES).get(self.from_status, '未知')
        to_label = dict(BusinessOpportunity.STATUS_CHOICES).get(self.to_status, '未知')
        return f"{self.opportunity.opportunity_number} - {from_label} → {to_label}"


# ==================== 客户线索管理模块（已删除）====================
# CustomerLead 和 LeadFollowUp 模型已删除（线索管理功能已移除）

# ==================== 客户关系管理模块（已删除，将按新设计方案重构）====================
# CustomerRelationship 模型已删除，将按新设计方案重新实现


class VisitPlan(models.Model):
    """拜访计划"""
    PLAN_STATUS_CHOICES = [
        ('planned', '已计划'),
        ('in_progress', '进行中'),
        ('completed', '已完成'),
        ('cancelled', '已取消'),
    ]
    
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='visit_plans', verbose_name='客户')
    plan_date = models.DateTimeField(verbose_name='计划日期')
    plan_title = models.CharField(max_length=200, verbose_name='计划标题')
    plan_purpose = models.TextField(verbose_name='拜访目的')
    location = models.CharField(max_length=200, blank=True, verbose_name='拜访地点')
    participants = models.CharField(max_length=500, blank=True, verbose_name='参与人员')
    status = models.CharField(max_length=20, choices=PLAN_STATUS_CHOICES, default='planned', verbose_name='计划状态')
    
    # 沟通清单相关字段
    communication_checklist = models.TextField(blank=True, verbose_name='沟通清单', help_text='拜访前需要准备的沟通要点和材料清单')
    checklist_prepared = models.BooleanField(default=False, verbose_name='清单已准备')
    checklist_prepared_time = models.DateTimeField(null=True, blank=True, verbose_name='清单准备时间')
    
    # 关联信息
    related_opportunity = models.ForeignKey(
        BusinessOpportunity,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='visit_plans',
        verbose_name='关联商机'
    )
    
    # 审计字段
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='created_visit_plans', verbose_name='创建人')
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    updated_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        db_table = 'customer_visit_plan'
        verbose_name = '拜访计划'
        verbose_name_plural = verbose_name
        ordering = ['plan_date', '-created_time']
        indexes = [
            models.Index(fields=['plan_date', 'status']),
            models.Index(fields=['client', 'plan_date']),
        ]
    
    def __str__(self):
        return f"{self.client.name} - {self.plan_title}"
    
    def get_current_step(self):
        """获取当前步骤"""
        if self.status == 'completed':
            return 4  # 已完成，显示复盘
        elif hasattr(self, 'checkins') and self.checkins.exists():
            return 3  # 已打卡，显示复盘
        elif self.checklist_prepared:
            return 2  # 清单已准备，显示打卡
        else:
            return 1  # 创建计划，显示清单准备


class VisitCheckin(models.Model):
    """拜访签到"""
    visit_plan = models.ForeignKey(VisitPlan, on_delete=models.CASCADE, related_name='checkins', null=True, blank=True, verbose_name='关联拜访计划')
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='visit_checkins', verbose_name='客户')
    checkin_time = models.DateTimeField(verbose_name='签到时间')
    checkin_location = models.CharField(max_length=200, verbose_name='签到地点')
    latitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True, verbose_name='纬度')
    longitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True, verbose_name='经度')
    notes = models.TextField(blank=True, verbose_name='备注')
    
    # 审计字段
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='created_checkins', verbose_name='签到人')
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    
    class Meta:
        db_table = 'customer_visit_checkin'
        verbose_name = '拜访签到'
        verbose_name_plural = verbose_name
        ordering = ['-checkin_time']
        indexes = [
            models.Index(fields=['client', 'checkin_time']),
            models.Index(fields=['checkin_time']),
        ]
    
    def __str__(self):
        return f"{self.client.name} - {self.checkin_time.strftime('%Y-%m-%d %H:%M')}"


class VisitReview(models.Model):
    """拜访结果复盘"""
    visit_plan = models.OneToOneField(VisitPlan, on_delete=models.CASCADE, related_name='review', verbose_name='关联拜访计划')
    visit_checkin = models.ForeignKey(VisitCheckin, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviews', verbose_name='关联签到')
    
    # 拜访结果
    visit_result = models.TextField(verbose_name='拜访结果', help_text='记录拜访过程中的关键信息和结果')
    customer_feedback = models.TextField(blank=True, verbose_name='客户反馈', help_text='客户的主要反馈和意见')
    key_points = models.TextField(blank=True, verbose_name='关键要点', help_text='本次拜访的关键要点和收获')
    next_actions = models.TextField(blank=True, verbose_name='下一步行动', help_text='后续需要跟进的事项和行动计划')
    
    # 效果评估
    satisfaction_score = models.IntegerField(
        null=True, 
        blank=True, 
        verbose_name='满意度评分',
        help_text='拜访满意度评分（1-10分）',
        validators=[MinValueValidator(1), MaxValueValidator(10)]
    )
    effectiveness = models.CharField(
        max_length=20,
        choices=[
            ('excellent', '非常有效'),
            ('good', '有效'),
            ('average', '一般'),
            ('poor', '效果不佳'),
        ],
        blank=True,
        verbose_name='拜访效果'
    )
    
    # 审计字段
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='created_visit_reviews', verbose_name='创建人')
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    updated_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        db_table = 'customer_visit_review'
        verbose_name = '拜访结果复盘'
        verbose_name_plural = verbose_name
        ordering = ['-created_time']
    
    def __str__(self):
        return f"{self.visit_plan.client.name} - {self.visit_plan.plan_title} - 复盘"


# ==================== 销售活动管理 ====================

class SalesActivity(models.Model):
    """销售活动"""
    ACTIVITY_TYPE_CHOICES = [
        ('visit', '客户拜访'),
        ('phone', '电话沟通'),
        ('meeting', '会议'),
        ('email', '邮件沟通'),
        ('other', '其他'),
    ]
    
    sales_person = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sales_activities', verbose_name='销售人员')
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_TYPE_CHOICES, verbose_name='活动类型')
    title = models.CharField(max_length=200, verbose_name='活动标题')
    start_time = models.DateTimeField(verbose_name='开始时间')
    end_time = models.DateTimeField(verbose_name='结束时间')
    location = models.CharField(max_length=200, blank=True, verbose_name='活动地点')
    related_opportunity = models.ForeignKey(
        BusinessOpportunity, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='activities',
        verbose_name='关联商机'
    )
    related_client = models.ForeignKey(
        Client, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='activities',
        verbose_name='关联客户'
    )
    description = models.TextField(blank=True, verbose_name='活动描述')
    is_completed = models.BooleanField(default=False, verbose_name='是否完成')
    completed_time = models.DateTimeField(null=True, blank=True, verbose_name='完成时间')
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    updated_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        db_table = 'sales_activity'
        verbose_name = '销售活动'
        verbose_name_plural = verbose_name
        ordering = ['start_time', '-created_time']
        indexes = [
            models.Index(fields=['sales_person', 'start_time']),
            models.Index(fields=['activity_type', 'start_time']),
            models.Index(fields=['is_completed', 'start_time']),
        ]
    
    def __str__(self):
        return f"{self.get_activity_type_display()} - {self.title} ({self.start_time.strftime('%Y-%m-%d %H:%M')})"
    
    def save(self, *args, **kwargs):
        # 如果标记为完成且完成时间为空，自动设置完成时间
        if self.is_completed and not self.completed_time:
            self.completed_time = timezone.now()
        super().save(*args, **kwargs)


# 审批流程完成回调
def on_contract_approval_completed(sender, instance, **kwargs):
    """合同审批完成后的回调处理"""
    try:
        # 只处理已完成的审批（通过或驳回）
        if instance.status not in ['approved', 'rejected']:
            return
        
        # 检查是否是合同相关的审批
        try:
            from backend.apps.production_management.models import BusinessContract
        except ImportError:
            return
        
        content_type = ContentType.objects.get_for_model(BusinessContract)
        if instance.content_type != content_type:
            return
        
        # 获取关联的合同
        try:
            contract = BusinessContract.objects.get(id=instance.object_id)
        except BusinessContract.DoesNotExist:
            return
        
        # 更新合同状态
        if instance.status == 'approved':
            # 审批通过，更新合同状态
            if contract.status in ['pending_review', 'reviewing']:
                contract.status = 'signed'  # 审批通过后变为已签订
                # 如果申请人存在，记录审批人
                if instance.applicant:
                    contract.approved_by = instance.applicant
                contract.save()
        elif instance.status == 'rejected':
            # 审批驳回，合同状态回到草稿
            if contract.status in ['pending_review', 'reviewing']:
                contract.status = 'draft'
                contract.save()
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception('合同审批完成回调处理失败: %s', str(e))


# 注册信号处理器
try:
    from backend.apps.workflow_engine.models import ApprovalInstance
    post_save.connect(on_contract_approval_completed, sender=ApprovalInstance)
except ImportError:
    # 如果workflow_engine未安装，忽略
    pass


class BusinessNegotiation(models.Model):
    """商务洽谈记录"""
    NEGOTIATION_TYPE_CHOICES = [
        ('phone', '电话沟通'),
        ('meeting', '会议洽谈'),
        ('visit', '上门拜访'),
        ('email', '邮件沟通'),
        ('online', '线上会议'),
        ('other', '其他'),
    ]
    
    opportunity = models.ForeignKey(
        BusinessOpportunity, 
        on_delete=models.CASCADE, 
        related_name='negotiations', 
        verbose_name='关联商机'
    )
    negotiation_date = models.DateField(verbose_name='洽谈日期')
    negotiation_type = models.CharField(
        max_length=20, 
        choices=NEGOTIATION_TYPE_CHOICES, 
        verbose_name='洽谈类型'
    )
    participants = models.CharField(
        max_length=500, 
        blank=True, 
        verbose_name='参与人员',
        help_text='参与洽谈的人员，多个用逗号分隔'
    )
    content = models.TextField(verbose_name='洽谈内容')
    client_feedback = models.TextField(blank=True, verbose_name='客户反馈')
    next_plan = models.TextField(blank=True, verbose_name='下一步计划')
    discussed_amount = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        null=True, 
        blank=True, 
        verbose_name='讨论金额（万元）'
    )
    payment_terms = models.TextField(blank=True, verbose_name='付款条件')
    contract_terms = models.TextField(blank=True, verbose_name='合同条款')
    
    # 审计字段
    created_by = models.ForeignKey(
        User, 
        on_delete=models.PROTECT, 
        related_name='created_negotiations', 
        verbose_name='创建人'
    )
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    updated_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        db_table = 'business_negotiation'
        verbose_name = '商务洽谈记录'
        verbose_name_plural = verbose_name
        ordering = ['-negotiation_date', '-created_time']
    
    def __str__(self):
        return f"{self.opportunity.name} - {self.negotiation_date} - {self.get_negotiation_type_display()}"


class OpportunityFiling(models.Model):
    """商机备案记录"""
    FILING_TYPE_CHOICES = [
        ('initial', '初始备案'),
        ('update', '更新备案'),
        ('supplement', '补充备案'),
        ('other', '其他'),
    ]
    
    opportunity = models.ForeignKey(
        BusinessOpportunity, 
        on_delete=models.CASCADE, 
        related_name='filings', 
        verbose_name='关联商机'
    )
    filing_date = models.DateField(verbose_name='备案日期')
    filing_type = models.CharField(
        max_length=20, 
        choices=FILING_TYPE_CHOICES, 
        verbose_name='备案类型'
    )
    filing_number = models.CharField(
        max_length=100, 
        blank=True, 
        verbose_name='备案编号',
        help_text='系统自动生成或手动输入'
    )
    filing_content = models.TextField(verbose_name='备案内容')
    filing_purpose = models.TextField(blank=True, verbose_name='备案目的')
    filing_notes = models.TextField(blank=True, verbose_name='备注说明')
    
    # 审计字段
    created_by = models.ForeignKey(
        User, 
        on_delete=models.PROTECT, 
        related_name='created_filings', 
        verbose_name='创建人'
    )
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    updated_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        db_table = 'business_opportunity_filing'
        verbose_name = '商机备案记录'
        verbose_name_plural = verbose_name
        ordering = ['-filing_date', '-created_time']
    
    def __str__(self):
        return f"{self.opportunity.name} - {self.filing_date} - {self.get_filing_type_display()}"
    
    def save(self, *args, **kwargs):
        # 如果备案编号为空，自动生成
        if not self.filing_number:
            from datetime import datetime
            date_str = datetime.now().strftime('%Y%m%d')
            count = OpportunityFiling.objects.filter(
                filing_date__year=datetime.now().year,
                filing_date__month=datetime.now().month,
                filing_date__day=datetime.now().day
            ).count()
            self.filing_number = f"FIL-{date_str}-{count + 1:04d}"
        super().save(*args, **kwargs)


class BiddingQuotation(models.Model):
    """投标报价记录"""
    STATUS_CHOICES = [
        ('draft', '草稿'),
        ('preparing', '准备中'),
        ('submitted', '已提交'),
        ('won', '中标'),
        ('lost', '未中标'),
        ('cancelled', '已取消'),
    ]
    
    opportunity = models.ForeignKey(
        BusinessOpportunity, 
        on_delete=models.CASCADE, 
        related_name='bidding_quotations', 
        verbose_name='关联商机'
    )
    bidding_number = models.CharField(
        max_length=100, 
        blank=True, 
        verbose_name='投标编号',
        help_text='系统自动生成或手动输入'
    )
    bidding_date = models.DateField(verbose_name='投标日期')
    submission_deadline = models.DateField(verbose_name='提交截止日期')
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='draft', 
        verbose_name='状态'
    )
    
    # 招标要求
    tender_requirements = models.TextField(verbose_name='招标要求', help_text='根据招标文件填写的要求')
    
    # 技术标信息（JSON格式存储）
    technical_proposal = models.JSONField(
        default=dict, 
        blank=True, 
        verbose_name='技术标信息',
        help_text='技术方案、技术能力、技术团队等信息'
    )
    
    # 商务标信息（JSON格式存储）
    commercial_proposal = models.JSONField(
        default=dict, 
        blank=True, 
        verbose_name='商务标信息',
        help_text='报价、付款方式、服务承诺等商务信息'
    )
    
    # 类似业绩（关联已完成项目）
    similar_projects = models.ManyToManyField(
        'production_management.Project',
        blank=True,
        related_name='bidding_quotations',
        verbose_name='类似业绩',
        help_text='选择类似的项目作为业绩证明'
    )
    
    # 人员证书（关联员工档案中的证书）
    personnel_certificates = models.JSONField(
        default=list,
        blank=True,
        verbose_name='人员证书',
        help_text='JSON格式存储选中的员工证书信息'
    )
    
    # 公司证件（JSON格式存储）
    company_certificates = models.JSONField(
        default=list,
        blank=True,
        verbose_name='公司证件',
        help_text='JSON格式存储公司资质证书、营业执照等信息'
    )
    
    # 投标文件
    bidding_documents = models.JSONField(
        default=list,
        blank=True,
        verbose_name='投标文件',
        help_text='JSON格式存储上传的投标文件列表'
    )
    
    # 备注
    notes = models.TextField(blank=True, verbose_name='备注说明')
    
    # 审计字段
    created_by = models.ForeignKey(
        User, 
        on_delete=models.PROTECT, 
        related_name='created_bidding_quotations', 
        verbose_name='创建人'
    )
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    updated_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        db_table = 'business_bidding_quotation'
        verbose_name = '投标报价记录'
        verbose_name_plural = verbose_name
        ordering = ['-bidding_date', '-created_time']
    
    def __str__(self):
        return f"{self.opportunity.name} - {self.bidding_date} - {self.get_status_display()}"
    
    def save(self, *args, **kwargs):
        # 如果投标编号为空，自动生成
        if not self.bidding_number:
            from datetime import datetime
            date_str = datetime.now().strftime('%Y%m%d')
            count = BiddingQuotation.objects.filter(
                bidding_date__year=datetime.now().year,
                bidding_date__month=datetime.now().month,
                bidding_date__day=datetime.now().day
            ).count()
            self.bidding_number = f"BID-{date_str}-{count + 1:04d}"
        super().save(*args, **kwargs)


# ==================== 客户关系协作管理模块 ====================

class CustomerRelationshipCollaboration(models.Model):
    """客户关系协作任务模型"""
    TASK_TYPE_CHOICES = [
        ('followup', '跟进协作'),
        ('visit', '拜访协作'),
        ('activity', '活动协作'),
        ('service', '服务协作'),
    ]
    
    PRIORITY_CHOICES = [
        ('high', '高'),
        ('medium', '中'),
        ('low', '低'),
    ]
    
    STATUS_CHOICES = [
        ('pending', '待处理'),
        ('in_progress', '进行中'),
        ('completed', '已完成'),
        ('cancelled', '已取消'),
    ]
    
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='collaborations', verbose_name='客户')
    task_type = models.CharField(max_length=20, choices=TASK_TYPE_CHOICES, verbose_name='任务类型')
    title = models.CharField(max_length=200, blank=True, default='', verbose_name='任务标题')
    description = models.TextField(verbose_name='任务描述')
    responsible_users = models.ManyToManyField(User, related_name='responsible_collaborations', verbose_name='负责人')
    collaborators = models.ManyToManyField(User, related_name='collaborated_tasks', blank=True, verbose_name='协作者')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium', verbose_name='优先级')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='任务状态')
    progress = models.IntegerField(default=0, verbose_name='任务进度', help_text='0-100')
    due_date = models.DateTimeField(null=True, blank=True, verbose_name='截止时间')
    related_contacts = models.ManyToManyField(ClientContact, related_name='collaborations', blank=True, verbose_name='关联的客户人员')
    related_relationships = models.ManyToManyField(CustomerRelationship, related_name='collaborations', blank=True, verbose_name='关联的跟进记录')
    # related_visits 暂时使用 related_relationships，后续可以单独定义Visit模型
    start_time = models.DateTimeField(null=True, blank=True, verbose_name='开始时间')
    completed_time = models.DateTimeField(null=True, blank=True, verbose_name='完成时间')
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='created_collaborations', verbose_name='创建人')
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    updated_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        db_table = 'customer_relationship_collaboration'
        verbose_name = '客户关系协作任务'
        verbose_name_plural = verbose_name
        ordering = ['-created_time']
    
    def __str__(self):
        if self.title:
            return f"{self.title} - {self.client.name}"
        else:
            # 使用描述的前50个字符作为显示
            desc = self.description[:50] if self.description else "无描述"
            return f"{desc}... - {self.client.name}"
    
    def get_task_type_display(self):
        return dict(self.TASK_TYPE_CHOICES).get(self.task_type, self.task_type)
    
    def get_priority_display(self):
        return dict(self.PRIORITY_CHOICES).get(self.priority, self.priority)
    
    def get_status_display(self):
        return dict(self.STATUS_CHOICES).get(self.status, self.status)


class CustomerRelationshipCollaborationComment(models.Model):
    """协作任务评论模型"""
    collaboration = models.ForeignKey(
        CustomerRelationshipCollaboration, 
        on_delete=models.CASCADE, 
        related_name='comments',
        verbose_name='协作任务'
    )
    user = models.ForeignKey(User, on_delete=models.PROTECT, related_name='collaboration_comments', verbose_name='评论人')
    content = models.TextField(verbose_name='评论内容')
    created_time = models.DateTimeField(default=timezone.now, verbose_name='评论时间')
    
    class Meta:
        db_table = 'customer_relationship_collaboration_comment'
        verbose_name = '协作任务评论'
        verbose_name_plural = verbose_name
        ordering = ['-created_time']
    
    def __str__(self):
        return f"{self.user.username} - {self.collaboration.title}"


class CustomerRelationshipCollaborationAttachment(models.Model):
    """协作任务附件模型"""
    collaboration = models.ForeignKey(
        CustomerRelationshipCollaboration, 
        on_delete=models.CASCADE, 
        related_name='attachments',
        verbose_name='协作任务'
    )
    file = models.FileField(upload_to='collaboration_attachments/%Y/%m/%d/', verbose_name='附件文件')
    file_name = models.CharField(max_length=255, verbose_name='文件名')
    file_size = models.BigIntegerField(verbose_name='文件大小（字节）')
    uploaded_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='collaboration_attachments', verbose_name='上传人')
    uploaded_time = models.DateTimeField(default=timezone.now, verbose_name='上传时间')
    
    class Meta:
        db_table = 'customer_relationship_collaboration_attachment'
        verbose_name = '协作任务附件'
        verbose_name_plural = verbose_name
        ordering = ['-uploaded_time']
    
    def __str__(self):
        if self.collaboration.title:
            return f"{self.file_name} - {self.collaboration.title}"
        else:
            desc = self.collaboration.description[:30] if self.collaboration.description else "无描述"
            return f"{self.file_name} - {desc}..."


class CustomerRelationshipCollaborationExecution(models.Model):
    """协作任务执行记录模型"""
    ACTION_CHOICES = [
        ('created', '创建任务'),
        ('started', '开始任务'),
        ('progress_updated', '更新进度'),
        ('status_changed', '状态变更'),
        ('commented', '添加评论'),
        ('attachment_added', '添加附件'),
        ('attachment_deleted', '删除附件'),
        ('completed', '完成任务'),
        ('cancelled', '取消任务'),
    ]
    
    collaboration = models.ForeignKey(
        CustomerRelationshipCollaboration, 
        on_delete=models.CASCADE, 
        related_name='executions',
        verbose_name='协作任务'
    )
    user = models.ForeignKey(User, on_delete=models.PROTECT, related_name='collaboration_executions', verbose_name='执行人')
    action = models.CharField(max_length=30, choices=ACTION_CHOICES, verbose_name='执行动作')
    content = models.TextField(blank=True, verbose_name='执行内容')
    execution_time = models.DateTimeField(default=timezone.now, verbose_name='执行时间')
    
    class Meta:
        db_table = 'customer_relationship_collaboration_execution'
        verbose_name = '协作任务执行记录'
        verbose_name_plural = verbose_name
        ordering = ['-execution_time']
    
    def __str__(self):
        return f"{self.get_action_display()} - {self.collaboration.title}"


class CustomerRelationshipCollaborationTemplate(models.Model):
    """协作任务模板模型"""
    TASK_TYPE_CHOICES = [
        ('followup', '跟进协作'),
        ('visit', '拜访协作'),
        ('activity', '活动协作'),
        ('service', '服务协作'),
    ]
    
    PRIORITY_CHOICES = [
        ('high', '高'),
        ('medium', '中'),
        ('low', '低'),
    ]
    
    template_name = models.CharField(max_length=100, verbose_name='模板名称')
    task_type = models.CharField(max_length=20, choices=TASK_TYPE_CHOICES, verbose_name='任务类型')
    title_template = models.CharField(max_length=200, verbose_name='标题模板')
    description_template = models.TextField(verbose_name='描述模板')
    default_priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium', verbose_name='默认优先级')
    is_shared = models.BooleanField(default=False, verbose_name='是否共享')
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='collaboration_templates', verbose_name='创建人')
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    updated_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        db_table = 'customer_relationship_collaboration_template'
        verbose_name = '协作任务模板'
        verbose_name_plural = verbose_name
        ordering = ['-created_time']
    
    def __str__(self):
        return f"{self.template_name} - {self.get_task_type_display()}"


class ExecutionRecord(models.Model):
    """被执行记录模型"""
    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name='execution_records',
        verbose_name='客户'
    )
    
    # 基本信息
    case_number = models.CharField(max_length=200, blank=True, verbose_name='案号')
    execution_status = models.CharField(
        max_length=50,
        choices=[
            ('pending', '待执行'),
            ('executing', '执行中'),
            ('completed', '已执行'),
            ('terminated', '已终止'),
            ('unknown', '未知'),
        ],
        default='unknown',
        verbose_name='执行状态'
    )
    execution_court = models.CharField(max_length=200, blank=True, verbose_name='执行法院')
    filing_date = models.DateField(null=True, blank=True, verbose_name='立案日期')
    execution_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='执行金额')
    
    # 数据来源
    source = models.CharField(
        max_length=50,
        choices=[
            ('qixinbao', '启信宝API'),
            ('manual', '手动录入'),
        ],
        default='qixinbao',
        verbose_name='数据来源'
    )
    
    # 审计字段
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    updated_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        db_table = 'customer_execution_record'
        verbose_name = '被执行记录'
        verbose_name_plural = verbose_name
        ordering = ['-filing_date', '-created_time']
        indexes = [
            models.Index(fields=['client', '-filing_date']),
            models.Index(fields=['case_number']),
        ]
    
    def __str__(self):
        return f"{self.client.name} - {self.case_number or '无案号'}"


class CustomerRequirementCommunication(models.Model):
    """客户需求沟通登记模型"""
    
    COMMUNICATION_TYPE_CHOICES = [
        ('phone', '电话沟通'),
        ('meeting', '会议沟通'),
        ('email', '邮件沟通'),
        ('site_visit', '现场拜访'),
        ('online', '线上沟通'),
        ('other', '其他'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', '低'),
        ('normal', '普通'),
        ('high', '高'),
        ('urgent', '紧急'),
    ]
    
    STATUS_CHOICES = [
        ('draft', '草稿'),
        ('submitted', '已提交'),
        ('processing', '处理中'),
        ('completed', '已完成'),
        ('cancelled', '已取消'),
    ]
    
    # 关联信息
    opportunity = models.ForeignKey(
        BusinessOpportunity,
        on_delete=models.CASCADE,
        related_name='requirement_communications',
        verbose_name='关联商机'
    )
    client = models.ForeignKey(
        Client,
        on_delete=models.PROTECT,
        related_name='requirement_communications',
        verbose_name='关联客户'
    )
    
    # 基本信息
    communication_number = models.CharField(
        max_length=50,
        unique=True,
        blank=True,
        null=True,
        verbose_name='沟通编号',
        help_text='自动生成：XQ-YYYYMMDD-0000'
    )
    title = models.CharField(max_length=200, verbose_name='沟通主题')
    communication_type = models.CharField(
        max_length=20,
        choices=COMMUNICATION_TYPE_CHOICES,
        default='meeting',
        verbose_name='沟通方式'
    )
    communication_date = models.DateTimeField(verbose_name='沟通时间')
    location = models.CharField(max_length=200, blank=True, verbose_name='沟通地点')
    
    # 参与人员
    our_participants = models.ManyToManyField(
        User,
        related_name='requirement_communications_participated',
        blank=True,
        verbose_name='我方参与人员'
    )
    client_participants = models.CharField(
        max_length=500,
        blank=True,
        verbose_name='客户参与人员',
        help_text='多个人员用逗号分隔'
    )
    
    # 需求信息
    requirement_description = models.TextField(verbose_name='需求描述')
    requirement_details = models.TextField(blank=True, verbose_name='需求详情')
    technical_requirements = models.TextField(blank=True, verbose_name='技术要求')
    business_requirements = models.TextField(blank=True, verbose_name='商务要求')
    budget_range = models.CharField(max_length=200, blank=True, verbose_name='预算范围')
    timeline_requirement = models.CharField(max_length=200, blank=True, verbose_name='时间要求')
    
    # 沟通结果
    communication_result = models.TextField(blank=True, verbose_name='沟通结果')
    next_action = models.TextField(blank=True, verbose_name='下一步行动')
    next_action_date = models.DateField(null=True, blank=True, verbose_name='下次行动时间')
    
    # 优先级和状态
    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_CHOICES,
        default='normal',
        verbose_name='优先级'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        verbose_name='状态'
    )
    
    # 附件和备注
    attachments = models.TextField(blank=True, verbose_name='附件说明', help_text='附件文件列表，用逗号分隔')
    notes = models.TextField(blank=True, verbose_name='备注')
    
    # 审计字段
    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='created_requirement_communications',
        verbose_name='创建人'
    )
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    updated_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        db_table = 'customer_requirement_communication'
        verbose_name = '客户需求沟通登记'
        verbose_name_plural = verbose_name
        ordering = ['-communication_date', '-created_time']
        indexes = [
            models.Index(fields=['opportunity', '-communication_date']),
            models.Index(fields=['client', '-communication_date']),
            models.Index(fields=['status', '-communication_date']),
            models.Index(fields=['communication_number']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.opportunity.name if self.opportunity else '未关联商机'}"
    
    def save(self, *args, **kwargs):
        # 自动生成沟通编号：XQ-YYYYMMDD-0000（连续编号）
        if not self.communication_number:
            from django.db.models import Max
            from datetime import datetime
            current_date = datetime.now().strftime('%Y%m%d')
            date_prefix = f'XQ-{current_date}-'
            
            # 查找当天最大编号
            max_comm = CustomerRequirementCommunication.objects.filter(
                communication_number__startswith=date_prefix
            ).aggregate(max_num=Max('communication_number'))['max_num']
            
            if max_comm:
                try:
                    # 提取最后4位数字作为序号
                    seq = int(max_comm.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    seq = 1
            else:
                seq = 1
            
            self.communication_number = f'{date_prefix}{seq:04d}'
        
        super().save(*args, **kwargs)


# ==================== 业务委托书管理模块 ====================

class AuthorizationLetter(models.Model):
    """业务委托书模型"""
    STATUS_CHOICES = [
        ('draft', '草稿'),
        ('submitted', '已提交'),
        ('confirmed', '已确认'),
        ('cancelled', '已作废'),
    ]
    
    # 设计阶段选择
    DESIGN_STAGE_CHOICES = [
        ('scheme', '方案阶段'),
        ('construction_drawing', '施工图阶段'),
        ('construction', '施工阶段'),
    ]
    
    # 结果优化范围选择
    RESULT_OPTIMIZATION_CHOICES = [
        ('structure', '结构'),
        ('architectural_structure', '建筑构造'),
        ('reduce_basement_area', '减少地库面积'),
        ('increase_parking_spaces', '增加地库车位'),
        ('building_energy_efficiency', '建筑节能'),
        ('electrical', '电气'),
        ('water_supply_drainage', '给排水'),
        ('hvac', '暖通'),
        ('curtain_wall', '幕墙'),
        ('doors_windows_railings', '门窗栏杆'),
        ('prefabricated', '装配式'),
        ('landscape', '园林景观'),
        ('geotechnical_support', '岩土及支护'),
        ('other_result', '其他'),
    ]
    
    # 过程优化范围选择
    PROCESS_OPTIMIZATION_CHOICES = [
        ('structure', '结构'),
        ('parking_space_index', '单车位指标'),
        ('other_process', '其他'),
    ]
    
    # 精细化审图范围选择
    DETAILED_REVIEW_CHOICES = [
        ('structural', '结构专业'),
        ('architectural', '建筑专业'),
        ('electrical', '电气专业'),
        ('water_supply_drainage', '给排水专业'),
        ('hvac', '暖通专业'),
        ('other_review', '其他'),
    ]
    
    # 基本信息
    letter_number = models.CharField(max_length=50, unique=True, blank=True, null=True, verbose_name='委托书编号', help_text='自动生成：VIH-AUTH-YYYY-NNNN')
    project_number = models.CharField(max_length=50, unique=True, blank=True, null=True, verbose_name='项目编号', help_text='自动生成：HT-YYYY-NNNN，不可修改')
    project_name = models.CharField(max_length=200, verbose_name='项目名称')
    provisional_price = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True, verbose_name='暂定价款（元）')
    letter_date = models.DateField(default=timezone.now, verbose_name='委托日期')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft', verbose_name='委托书状态')
    
    # 委托单位信息
    client_name = models.CharField(max_length=200, verbose_name='单位名称')
    client_contact = models.ForeignKey(
        ClientContact,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='authorization_letters',
        verbose_name='单位代表（联系人）'
    )
    client_representative = models.CharField(max_length=100, blank=True, verbose_name='单位代表')
    client_phone = models.CharField(max_length=50, blank=True, verbose_name='联系电话')
    client_email = models.EmailField(blank=True, verbose_name='电子邮箱')
    client_address = models.CharField(max_length=500, blank=True, verbose_name='收件地址')
    
    # 服务单位信息
    trustee_name = models.CharField(max_length=200, default='四川维海科技有限公司', verbose_name='服务单位')
    trustee_representative = models.CharField(max_length=100, blank=True, verbose_name='单位代表', help_text='例如：田霞')
    trustee_phone = models.CharField(max_length=50, blank=True, verbose_name='联系电话', help_text='例如：13666287899/02883574973')
    trustee_email = models.EmailField(blank=True, verbose_name='电子邮箱', help_text='例如：whkj@vihgroup.com.cn')
    trustee_address = models.CharField(max_length=500, blank=True, verbose_name='收件地址', help_text='例如：四川省成都市武侯区武科西一路瑞景产业园1号楼5A01')
    
    # 保留旧字段以兼容历史数据（已废弃）
    design_stages = models.JSONField(default=list, blank=True, verbose_name='设计阶段（已废弃）', help_text='已废弃，请使用图纸阶段')
    result_optimization_scopes = models.JSONField(default=list, blank=True, verbose_name='结果优化范围（已废弃）')
    process_optimization_scopes = models.JSONField(default=list, blank=True, verbose_name='过程优化范围（已废弃）')
    detailed_review_scopes = models.JSONField(default=list, blank=True, verbose_name='精细化审图范围（已废弃）')
    
    # 服务费确定原则
    result_optimization_rate = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name='结果优化费率（%）', help_text='10-15%')
    process_optimization_rate = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name='过程优化费率（%）', help_text='10-15%')
    detailed_review_unit_price_min = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name='精细化审图单价下限（元/平方米）', help_text='1.5元/平方米')
    detailed_review_unit_price_max = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name='精细化审图单价上限（元/平方米）', help_text='3.0元/平方米')
    fee_determination_principle = models.TextField(blank=True, verbose_name='服务费确定原则说明')
    
    # 结算与支付
    settlement_review_process = models.TextField(blank=True, verbose_name='结算审核流程说明')
    payment_schedule = models.JSONField(default=dict, blank=True, verbose_name='付款计划', help_text='三阶段付款：20%、30%、100%')
    
    # 补充约定
    supplementary_agreement = models.TextField(blank=True, verbose_name='补充约定')
    
    # 委托期限
    start_date = models.DateField(null=True, blank=True, verbose_name='开始日期')
    end_date = models.DateField(null=True, blank=True, verbose_name='结束日期')
    duration_days = models.IntegerField(null=True, blank=True, verbose_name='委托期限（天）', help_text='自动计算')
    
    # 关联信息
    client = models.ForeignKey(
        Client,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='authorization_letters',
        verbose_name='关联客户'
    )
    opportunity = models.ForeignKey(
        BusinessOpportunity, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='authorization_letters',
        verbose_name='关联商机'
    )
    project = models.ForeignKey(
        'production_management.Project',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='authorization_letters',
        verbose_name='关联项目'
    )
    business_manager = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='managed_authorization_letters',
        verbose_name='商务经理'
    )
    notes = models.TextField(blank=True, verbose_name='备注')
    
    # 审计字段
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='created_authorization_letters', verbose_name='创建人')
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    updated_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        db_table = 'business_authorization_letter'
        verbose_name = '业务委托书'
        verbose_name_plural = verbose_name
        ordering = ['-created_time']
        indexes = [
            models.Index(fields=['letter_number']),
            models.Index(fields=['status']),
            models.Index(fields=['client_name']),
            models.Index(fields=['opportunity']),
            models.Index(fields=['letter_date']),
        ]
    
    def __str__(self):
        return f"{self.letter_number or '未编号'} - {self.project_name}"
    
    def save(self, *args, **kwargs):
        # 如果设置了client但没有设置client_name，自动填充client_name
        if self.client and not self.client_name:
            self.client_name = self.client.name
        
        # 如果设置了client_contact但没有设置client_representative，自动填充client_representative
        if self.client_contact and not self.client_representative:
            self.client_representative = self.client_contact.name
            # 同时自动填充其他信息
            if not self.client_phone and self.client_contact.phone:
                self.client_phone = self.client_contact.phone
            if not self.client_email and self.client_contact.email:
                self.client_email = self.client_contact.email
            if not self.client_address and self.client_contact.office_address:
                self.client_address = self.client_contact.office_address
        
        # 自动生成项目编号：HT-YYYY-NNNN
        if not self.project_number:
            from django.db.models import Max
            from datetime import datetime
            current_year = datetime.now().strftime('%Y')
            year_prefix = f'HT-{current_year}-'
            
            # 查找当年最大项目编号（从业务委托书和合同中查找）
            from backend.apps.production_management.models import BusinessContract
            
            # 查找业务委托书中的最大项目编号
            max_letter = AuthorizationLetter.objects.filter(
                project_number__startswith=year_prefix
            ).exclude(id=self.id if self.id else None).aggregate(max_num=Max('project_number'))['max_num']
            
            # 查找合同中的最大项目编号
            max_contract = BusinessContract.objects.filter(
                project_number__startswith=year_prefix
            ).aggregate(max_num=Max('project_number'))['max_num']
            
            # 取两者中的最大值
            max_project_number = None
            if max_letter and max_contract:
                max_project_number = max(max_letter, max_contract)
            elif max_letter:
                max_project_number = max_letter
            elif max_contract:
                max_project_number = max_contract
            
            if max_project_number:
                try:
                    # 提取序列号，格式：HT-YYYY-NNNN
                    seq_str = max_project_number.split('-')[-1]
                    seq = int(seq_str) + 1
                except (ValueError, IndexError):
                    seq = 1
            else:
                seq = 1
            
            self.project_number = f'{year_prefix}{seq:04d}'
        
        # 自动计算委托期限（天）
        if self.start_date and self.end_date:
            delta = self.end_date - self.start_date
            self.duration_days = delta.days
        
        super().save(*args, **kwargs)
    
    def can_edit(self):
        """判断是否可以编辑（仅草稿状态可编辑）"""
        return self.status == 'draft'
    
    def can_delete(self):
        """判断是否可以删除（仅草稿状态可删除）"""
        return self.status == 'draft'
    
    def can_convert_to_contract(self):
        """判断是否可以转换为合同（已确认状态可转换）"""
        return self.status == 'confirmed'
    
    def get_design_stages_display(self):
        """获取设计阶段的中文显示"""
        if not self.design_stages:
            return []
        choices_dict = dict(self.DESIGN_STAGE_CHOICES)
        return [choices_dict.get(stage, stage) for stage in self.design_stages]
    
    def get_result_optimization_scopes_display(self):
        """获取结果优化范围的中文显示"""
        if not self.result_optimization_scopes:
            return []
        choices_dict = dict(self.RESULT_OPTIMIZATION_CHOICES)
        return [choices_dict.get(scope, scope) for scope in self.result_optimization_scopes]
    
    def get_process_optimization_scopes_display(self):
        """获取过程优化范围的中文显示"""
        if not self.process_optimization_scopes:
            return []
        choices_dict = dict(self.PROCESS_OPTIMIZATION_CHOICES)
        return [choices_dict.get(scope, scope) for scope in self.process_optimization_scopes]
    
    def get_detailed_review_scopes_display(self):
        """获取精细化审图范围的中文显示"""
        if not self.detailed_review_scopes:
            return []
        choices_dict = dict(self.DETAILED_REVIEW_CHOICES)
        return [choices_dict.get(scope, scope) for scope in self.detailed_review_scopes]


# ==================== 业务委托书模板 ====================

def authorization_letter_template_file_path(instance, filename):
    """业务委托书模板文件上传路径"""
    import os
    from datetime import datetime
    date_path = datetime.now().strftime('%Y/%m/%d')
    # 使用模板ID或时间戳作为文件名的一部分，避免文件名冲突
    if instance.pk:
        base_name, ext = os.path.splitext(filename)
        return f'authorization_letter_templates/{date_path}/template_{instance.pk}_{base_name}{ext}'
    else:
        return f'authorization_letter_templates/{date_path}/{filename}'


class AuthorizationLetterTemplate(models.Model):
    """业务委托书模板模型"""
    TEMPLATE_TYPE_CHOICES = [
        ('service', '服务委托书'),
        ('procurement', '采购委托书'),
        ('consulting', '咨询委托书'),
        ('other', '其他'),
    ]
    
    STATUS_CHOICES = [
        ('draft', '草稿'),
        ('active', '启用'),
        ('archived', '已归档'),
    ]
    
    # 基本信息
    template_name = models.CharField(max_length=200, verbose_name='模板名称')
    template_type = models.CharField(max_length=50, choices=TEMPLATE_TYPE_CHOICES, default='service', verbose_name='模板类型')
    category = models.CharField(max_length=100, blank=True, verbose_name='模板分类', help_text='用于模板分类管理')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft', verbose_name='状态')
    description = models.TextField(blank=True, verbose_name='模板说明')
    
    # 模板内容（JSON格式，存储所有字段的模板值）
    template_content = models.JSONField(default=dict, verbose_name='模板内容', help_text='存储委托书各字段的模板值，支持变量占位符')
    
    # 变量定义（JSON格式，存储变量列表和说明）
    variables = models.JSONField(default=list, verbose_name='变量列表', help_text='模板中使用的变量列表，格式：[{"name": "变量名", "label": "显示名称", "description": "说明"}]')
    
    # 模板文件（支持上传Word、PDF等格式的模板文件）
    template_file = models.FileField(
        null=True, 
        blank=True,
        upload_to=authorization_letter_template_file_path,
        verbose_name='模板文件',
        help_text='支持上传Word、PDF等格式的模板文件，用于预览和下载',
        max_length=500
    )
    template_file_name = models.CharField(max_length=255, blank=True, verbose_name='模板文件名', help_text='原始文件名')
    template_file_size = models.BigIntegerField(null=True, blank=True, verbose_name='文件大小（字节）')
    
    # 使用统计
    usage_count = models.IntegerField(default=0, verbose_name='使用次数')
    last_used_time = models.DateTimeField(null=True, blank=True, verbose_name='最后使用时间')
    
    # 审计字段
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='created_authorization_letter_templates', verbose_name='创建人')
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='updated_authorization_letter_templates', verbose_name='更新人')
    updated_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        db_table = 'business_authorization_letter_template'
        verbose_name = '业务委托书模板'
        verbose_name_plural = verbose_name
        ordering = ['-created_time']
        indexes = [
            models.Index(fields=['template_type', 'status']),
            models.Index(fields=['status']),
            models.Index(fields=['created_time']),
        ]
    
    def __str__(self):
        return f"{self.template_name} ({self.get_template_type_display()})"
    
    def increment_usage(self):
        """增加使用次数"""
        self.usage_count += 1
        self.last_used_time = timezone.now()
        self.save(update_fields=['usage_count', 'last_used_time'])
    
    def extract_variables(self):
        """从模板内容中提取变量（格式：{变量名}）"""
        import re
        variables = set()
        content_str = str(self.template_content)
        pattern = r'\{(\w+)\}'
        matches = re.findall(pattern, content_str)
        variables.update(matches)
        return list(variables)
    
    def save(self, *args, **kwargs):
        """保存时自动记录文件信息"""
        # 如果上传了新文件，记录文件名和大小
        # 注意：在Django中，文件上传后，template_file是一个FieldFile对象
        if self.template_file and self.template_file.name:
            import os
            # 获取文件名（去除路径，只保留文件名）
            self.template_file_name = os.path.basename(self.template_file.name)
            
            # 获取文件大小
            try:
                if hasattr(self.template_file, 'size'):
                    self.template_file_size = self.template_file.size
                else:
                    # 尝试通过文件对象获取大小
                    if hasattr(self.template_file, 'file'):
                        file_obj = self.template_file.file
                        if hasattr(file_obj, 'size'):
                            self.template_file_size = file_obj.size
                        elif hasattr(file_obj, 'seek') and hasattr(file_obj, 'tell'):
                            # 通过seek和tell获取文件大小
                            current_pos = file_obj.tell()
                            file_obj.seek(0, 2)  # 移动到文件末尾
                            self.template_file_size = file_obj.tell()
                            file_obj.seek(current_pos)  # 恢复原位置
                        else:
                            self.template_file_size = None
                    else:
                        self.template_file_size = None
            except (AttributeError, OSError, IOError) as e:
                # 如果无法获取文件大小，设置为 None
                logger.warning(f'无法获取模板文件大小: {e}')
                self.template_file_size = None
        
        super().save(*args, **kwargs)

