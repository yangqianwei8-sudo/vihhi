from django.db import models
from django.utils import timezone
from backend.apps.system_management.models import User

class Project(models.Model):
    """项目模型"""
    PROJECT_STATUS = [
        ('draft', '草稿'),
        ('waiting_receive', '待接收'),
        ('configuring', '配置中'),
        ('waiting_start', '待开工'),
        ('in_progress', '进行中'),
        ('suspended', '暂停'),
        ('completed', '已完工'),
        ('archived', '已归档'),
        ('cancelled', '已取消'),
    ]
    
    SUBSIDIARY_CHOICES = [
        ('sichuan', '四川维海科技有限公司'),
        ('chongqing', '重庆维海科技有限公司'),
        ('xian', '西安维海科技有限公司'),
        ('hejian_chengdu', '禾间成都建筑设计咨询有限公司'),
        ('hongtian', '成都宏天升荣科技有限公司'),
    ]
    
    SERVICE_TYPES = [
        ('result_optimization', '结果优化'),
        ('process_optimization', '过程优化'),
        ('detailed_review', '精细化审图'),
        ('full_process_consulting', '全过程咨询'),
    ]
    
    # 服务专业与服务类型对应关系
    SERVICE_PROFESSIONS_MAP = {
        'result_optimization': [
            '结构', '构造', '地库减面积', '地库加车位', '停车效率', '节能', 
            '门窗栏杆', '幕墙', '总坪景观', '电气', '给排水', '暖通', '市政道路'
        ],
        'process_optimization': ['结构', '建筑地库'],
        'detailed_review': ['建筑', '结构', '电气', '给排水', '暖通'],
        'full_process_consulting': ['建筑', '结构', '电气', '给排水', '暖通'],
    }
    
    # 成果文件与服务类型对应关系
    DELIVERABLES_MAP = {
        'result_optimization': ['咨询意见书', '三方沟通成果', '核图意见书'],
        'process_optimization': ['过程优化报告', '核图意见书'],
        'detailed_review': ['咨询意见书', '三方沟通成果', '核图意见书'],
        'full_process_consulting': ['每周快报', '核图意见书'],
    }
    
    BUSINESS_TYPES = [
        ('residential', '住宅'),
        ('complex', '综合体'),
        ('commercial', '商业'),
        ('office', '写字楼'),
        ('school', '学校'),
        ('hospital', '医院'),
        ('industrial', '工业厂房'),
        ('municipal', '市政'),
        ('other', '其他'),
    ]
    
    DESIGN_STAGES = [
        ('construction_drawing_unreviewed', '施工图（未审图）'),
        ('construction_drawing_reviewed', '施工图（已审图）'),
        ('preliminary_design', '初设阶段'),
        ('extended_preliminary', '扩初阶段'),
        ('detailed_planning', '详规阶段'),
        ('construction_phase', '施工阶段'),
    ]
    
    # 基础信息
    subsidiary = models.CharField(max_length=50, choices=SUBSIDIARY_CHOICES, default='sichuan', verbose_name='子公司')
    project_number = models.CharField(max_length=50, unique=True, verbose_name='项目编号')
    name = models.CharField(max_length=200, verbose_name='项目名称')
    alias = models.CharField(max_length=200, blank=True, verbose_name='项目别名')
    description = models.TextField(blank=True, verbose_name='项目描述')
    
    # 服务信息
    service_type = models.CharField(max_length=50, choices=SERVICE_TYPES, blank=True, null=True, verbose_name='服务类型')
    business_type = models.CharField(max_length=50, choices=BUSINESS_TYPES, blank=True, null=True, verbose_name='项目业态')
    design_stage = models.CharField(max_length=50, choices=DESIGN_STAGES, blank=True, null=True, verbose_name='图纸阶段')
    service_professions = models.JSONField(default=list, blank=True, verbose_name='服务专业')
    
    # 客户信息
    client = models.ForeignKey('customer_success.Client', on_delete=models.PROTECT, null=True, blank=True, verbose_name='客户')
    client_company_name = models.CharField(max_length=200, blank=True, verbose_name='甲方公司名称')
    client_contact_person = models.CharField(max_length=100, blank=True, verbose_name='甲方项目负责人')
    client_phone = models.CharField(max_length=20, blank=True, verbose_name='联系电话')
    client_email = models.EmailField(blank=True, verbose_name='电子邮箱')
    client_address = models.CharField(max_length=500, blank=True, verbose_name='通讯地址')
    
    # 设计方信息
    design_company = models.CharField(max_length=200, blank=True, verbose_name='设计单位名称')
    design_contact_person = models.CharField(max_length=100, blank=True, verbose_name='设计方项目负责人')
    design_phone = models.CharField(max_length=20, blank=True, verbose_name='设计方联系电话')
    design_email = models.EmailField(blank=True, verbose_name='设计方电子邮箱')
    
    # 项目团队
    business_manager = models.ForeignKey(User, on_delete=models.PROTECT, related_name='business_managed_projects', null=True, blank=True, verbose_name='商务经理')
    project_manager = models.ForeignKey(User, on_delete=models.PROTECT, related_name='managed_projects', null=True, blank=True, verbose_name='项目负责人')
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='created_projects', null=True, blank=True, verbose_name='创建人')
    
    # 项目详细信息
    project_address = models.CharField(max_length=500, blank=True, verbose_name='项目地址')
    building_area = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, verbose_name='建筑面积(㎡)')
    underground_area = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, verbose_name='地下面积(㎡)')
    aboveground_area = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, verbose_name='地上面积(㎡)')
    building_height = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name='建筑高度(米)')
    aboveground_floors = models.IntegerField(null=True, blank=True, verbose_name='地上层数')
    underground_floors = models.IntegerField(null=True, blank=True, verbose_name='地下层数')
    structure_type = models.CharField(max_length=100, blank=True, verbose_name='结构形式')
    
    # 特殊要求
    client_special_requirements = models.TextField(blank=True, verbose_name='甲方特殊要求')
    technical_difficulties = models.TextField(blank=True, verbose_name='技术难点说明')
    risk_assessment = models.TextField(blank=True, verbose_name='项目风险预判')
    
    # 时间信息
    start_date = models.DateField(null=True, blank=True, verbose_name='开始日期')
    end_date = models.DateField(null=True, blank=True, verbose_name='结束日期')
    actual_start_date = models.DateField(null=True, blank=True, verbose_name='实际开始日期')
    actual_end_date = models.DateField(null=True, blank=True, verbose_name='实际结束日期')
    
    # 合同信息
    contract_number = models.CharField(max_length=100, blank=True, verbose_name='合同编号')
    contract_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, verbose_name='合同金额')
    contract_date = models.DateField(null=True, blank=True, verbose_name='签约日期')
    contract_file = models.FileField(upload_to='project_contracts/%Y/%m/', null=True, blank=True, verbose_name='合同附件')
    
    # 状态和财务
    status = models.CharField(max_length=20, choices=PROJECT_STATUS, default='draft', verbose_name='项目状态')
    estimated_cost = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, verbose_name='预估成本')
    estimated_savings = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, verbose_name='预计节省金额')
    
    # 审计字段
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    updated_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        db_table = 'project_center_project'
        verbose_name = '项目'
        verbose_name_plural = verbose_name
        ordering = ['-created_time']
    
    def __str__(self):
        return f"{self.project_number} - {self.name}"
    
    def save(self, *args, **kwargs):
        if not self.project_number:
            # 自动生成项目编号：VIH-当前年份-001（年份自动，序号手动填写）
            # 如果用户没有手动填写序号，则自动生成
            import datetime
            from django.db.models import Max
            current_year = datetime.datetime.now().year
            
            # 获取当前年份的最大序列号
            max_number = Project.objects.filter(
                project_number__startswith=f'VIH-{current_year}-'
            ).aggregate(max_num=Max('project_number'))['max_num']
            
            if max_number:
                # 提取序列号并加1
                try:
                    seq = int(max_number.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    seq = 1
            else:
                seq = 1
            
            self.project_number = f"VIH-{current_year}-{seq:03d}"
        super().save(*args, **kwargs)

class ProjectTeam(models.Model):
    """项目团队"""
    ROLE_CHOICES = [
        ('business_manager', '商务经理'),
        ('project_manager', '项目负责人'),
        ('professional_leader', '专业负责人'),
        ('engineer', '专业工程师'),
        ('technical_assistant', '技术助理'),
        ('cost_reviewer_civil', '土建造价审核人'),
        ('cost_reviewer_installation', '安装造价审核人'),
        ('cost_engineer_civil', '土建造价师'),
        ('cost_engineer_installation', '安装造价师'),
        ('external_engineer', '外部专业工程师'),
        ('external_leader', '外部专业负责人'),
        ('external_cost_reviewer_civil', '外部土建造价审核人'),
        ('external_cost_reviewer_installation', '外部安装造价审核人'),
        ('external_cost_engineer_civil', '外部土建造价师'),
        ('external_cost_engineer_installation', '外部安装造价师'),
    ]
    
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='team_members', verbose_name='项目')
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='成员')
    role = models.CharField(max_length=50, choices=ROLE_CHOICES, verbose_name='角色')
    is_external = models.BooleanField(default=False, verbose_name='是否外部成员')
    join_date = models.DateField(verbose_name='加入日期')
    leave_date = models.DateField(null=True, blank=True, verbose_name='离开日期')
    responsibility = models.TextField(blank=True, verbose_name='职责描述')
    is_active = models.BooleanField(default=True, verbose_name='是否有效')
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    
    class Meta:
        db_table = 'project_center_team'
        verbose_name = '项目团队'
        verbose_name_plural = verbose_name
        unique_together = ['project', 'user']

class PaymentPlan(models.Model):
    """回款计划"""
    PAYMENT_STATUS = [
        ('pending', '待回款'),
        ('partial', '部分回款'),
        ('completed', '已完成'),
        ('overdue', '已逾期'),
        ('cancelled', '已取消'),
    ]
    
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='payment_plans', verbose_name='项目')
    phase_name = models.CharField(max_length=100, verbose_name='回款阶段')
    phase_description = models.TextField(blank=True, verbose_name='阶段描述')
    planned_amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='计划金额')
    planned_date = models.DateField(verbose_name='计划日期')
    actual_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, verbose_name='实际金额')
    actual_date = models.DateField(null=True, blank=True, verbose_name='实际日期')
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='pending', verbose_name='状态')
    notes = models.TextField(blank=True, verbose_name='备注')
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    updated_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        db_table = 'project_center_payment_plan'
        verbose_name = '回款计划'
        verbose_name_plural = verbose_name
        ordering = ['planned_date']

class ProjectMilestone(models.Model):
    """项目里程碑"""
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='milestones', verbose_name='项目')
    name = models.CharField(max_length=100, verbose_name='里程碑名称')
    description = models.TextField(blank=True, verbose_name='里程碑描述')
    planned_date = models.DateField(verbose_name='计划日期')
    actual_date = models.DateField(null=True, blank=True, verbose_name='实际日期')
    completion_rate = models.IntegerField(default=0, verbose_name='完成率')
    is_completed = models.BooleanField(default=False, verbose_name='是否完成')
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    
    class Meta:
        db_table = 'project_center_milestone'
        verbose_name = '项目里程碑'
        verbose_name_plural = verbose_name
        ordering = ['planned_date']

class ProjectDocument(models.Model):
    """项目文档"""
    DOCUMENT_TYPES = [
        ('contract', '合同文件'),
        ('design', '设计文件'),
        ('report', '报告文件'),
        ('meeting', '会议纪要'),
        ('other', '其他文件'),
    ]
    
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='documents', verbose_name='项目')
    name = models.CharField(max_length=200, verbose_name='文档名称')
    document_type = models.CharField(max_length=50, choices=DOCUMENT_TYPES, verbose_name='文档类型')
    file = models.FileField(upload_to='project_documents/%Y/%m/', verbose_name='文档文件')
    description = models.TextField(blank=True, verbose_name='文档描述')
    uploaded_by = models.ForeignKey(User, on_delete=models.PROTECT, verbose_name='上传人')
    uploaded_time = models.DateTimeField(default=timezone.now, verbose_name='上传时间')
    
    class Meta:
        db_table = 'project_center_document'
        verbose_name = '项目文档'
        verbose_name_plural = verbose_name
        ordering = ['-uploaded_time']

class ProjectArchive(models.Model):
    """项目归档"""
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='archives', verbose_name='项目')
    archive_number = models.CharField(max_length=50, unique=True, verbose_name='归档编号')
    archive_time = models.DateTimeField(default=timezone.now, verbose_name='归档时间')
    archived_by = models.ForeignKey(User, on_delete=models.PROTECT, verbose_name='归档人')
    archive_version = models.IntegerField(default=1, verbose_name='归档版本')
    archive_content = models.JSONField(default=dict, verbose_name='归档内容')
    view_permissions = models.JSONField(default=list, blank=True, verbose_name='查看权限')
    download_permissions = models.JSONField(default=list, blank=True, verbose_name='下载权限')
    modify_permissions = models.JSONField(default=list, blank=True, verbose_name='修改权限')
    notes = models.TextField(blank=True, verbose_name='备注')
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    
    class Meta:
        db_table = 'project_center_archive'
        verbose_name = '项目归档'
        verbose_name_plural = verbose_name
        ordering = ['-archive_time']
        unique_together = ['project', 'archive_version']
    
    def save(self, *args, **kwargs):
        if not self.archive_number:
            # 自动生成归档编号
            import datetime
            from django.db.models import Max
            current_year = datetime.datetime.now().year
            max_number = ProjectArchive.objects.filter(
                archive_number__startswith=f'ARCH-{current_year}-'
            ).aggregate(max_num=Max('archive_number'))['max_num']
            
            if max_number:
                try:
                    seq = int(max_number.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    seq = 1
            else:
                seq = 1
            
            self.archive_number = f"ARCH-{current_year}-{seq:05d}"
        super().save(*args, **kwargs)
