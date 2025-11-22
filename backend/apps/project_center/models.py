from django.db import models
from django.utils import timezone
from backend.apps.system_management.models import User


class ServiceType(models.Model):
    """服务类型"""
    code = models.CharField(max_length=50, unique=True, verbose_name='服务类型编码')
    name = models.CharField(max_length=100, verbose_name='服务类型名称')
    order = models.PositiveIntegerField(default=0, verbose_name='排序')

    class Meta:
        db_table = 'project_center_service_type'
        verbose_name = '服务类型'
        verbose_name_plural = verbose_name
        ordering = ['order', 'id']

    def __str__(self):
        return self.name


class ServiceProfession(models.Model):
    """服务专业"""
    service_type = models.ForeignKey(ServiceType, on_delete=models.CASCADE, related_name='professions', verbose_name='所属服务类型')
    code = models.CharField(max_length=50, verbose_name='服务专业编码')
    name = models.CharField(max_length=100, verbose_name='服务专业名称')
    order = models.PositiveIntegerField(default=0, verbose_name='排序')

    class Meta:
        db_table = 'project_center_service_profession'
        verbose_name = '服务专业'
        verbose_name_plural = verbose_name
        ordering = ['service_type__order', 'order', 'id']
        unique_together = ('service_type', 'code')

    def __str__(self):
        return f"{self.service_type.name} - {self.name}"


class Project(models.Model):
    """项目模型"""
    PROJECT_STATUS = [
        ('draft', '草稿'),
        ('waiting_initiation_approval', '待立项审批'),
        ('initiation_rejected', '立项审批已驳回'),
        ('initiation_approved', '立项已审批'),
        ('waiting_receive', '待接收'),
        ('configuring', '配置中'),
        ('waiting_start', '待开工'),
        ('in_progress', '进行中'),
        ('suspended', '暂停'),
        ('completed', '已完工'),
        ('archived', '已归档'),
        ('cancelled', '已取消'),
    ]
    LAUNCH_STATUS = [
        ('handover_pending', '待商务移交'),
        ('awaiting_drawings', '待图纸上传'),
        ('precheck_in_progress', '预审中'),
        ('changes_requested', '待补充资料'),
        ('ready_to_start', '待开工通知'),
        ('started', '已开工'),
    ]
    FLOW_STEPS = [
        ('pending_documents', '等待资料上传'),
        ('precheck', '资料预审'),
        ('start_notice', '开工通知'),
        ('opinions', '意见编制'),
        ('internal_review', '内部审核'),
        ('ready_to_push', '待推送'),
        ('pushed', '报告已推送'),
    ]
    
    SUBSIDIARY_CHOICES = [
        ('sichuan', '四川维海科技有限公司'),
        ('chongqing', '重庆维海科技有限公司'),
        ('xian', '西安维海科技有限公司'),
        ('hejian_chengdu', '禾间成都建筑设计咨询有限公司'),
        ('hongtian', '成都宏天升荣科技有限公司'),
    ]
    
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
    project_number = models.CharField(max_length=50, unique=True, blank=True, null=True, verbose_name='项目编号')
    name = models.CharField(max_length=200, verbose_name='项目名称')
    alias = models.CharField(max_length=200, blank=True, verbose_name='项目别名')
    description = models.TextField(blank=True, verbose_name='项目描述')
    
    # 立项相关字段
    initiation_document_type = models.CharField(
        max_length=50,
        choices=[
            ('winning_notice', '中标通知书'),
            ('business_commission', '业务委托书'),
            ('contract_text', '合同文本'),
        ],
        blank=True,
        null=True,
        verbose_name='立项凭证类型'
    )
    initiation_document = models.FileField(
        upload_to='project_initiation_documents/%Y/%m/',
        null=True,
        blank=True,
        verbose_name='立项凭证文件'
    )
    
    # 服务信息
    service_type = models.ForeignKey(ServiceType, on_delete=models.SET_NULL, null=True, blank=True, related_name='projects', verbose_name='服务类型')
    business_type = models.CharField(max_length=50, choices=BUSINESS_TYPES, blank=True, null=True, verbose_name='项目业态')
    design_stage = models.CharField(max_length=50, choices=DESIGN_STAGES, blank=True, null=True, verbose_name='图纸阶段')
    service_professions = models.ManyToManyField('ServiceProfession', blank=True, related_name='projects', verbose_name='服务专业')
    
    # 委托单位（甲方）信息
    client = models.ForeignKey('customer_success.Client', on_delete=models.PROTECT, null=True, blank=True, verbose_name='客户')
    client_company_name = models.CharField(max_length=200, blank=True, verbose_name='委托单位名称')
    client_credit_code = models.CharField(max_length=50, blank=True, verbose_name='统一社会信用代码')
    client_registered_capital = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True, verbose_name='注册资本（万元）')
    client_registered_address = models.CharField(max_length=500, blank=True, verbose_name='注册地址')
    client_company_type = models.CharField(
        max_length=50,
        choices=[
            ('project_company', '项目公司'),
            ('regional_company', '区域公司'),
            ('group_company', '集团公司'),
        ],
        blank=True,
        null=True,
        verbose_name='企业类型'
    )
    client_ownership_type = models.CharField(
        max_length=50,
        choices=[
            ('central_enterprise', '中央企业'),
            ('state_owned', '国有企业'),
            ('platform_company', '平台公司'),
            ('listed_company', '上市公司'),
            ('private_enterprise', '民营企业'),
        ],
        blank=True,
        null=True,
        verbose_name='企业所有'
    )
    client_established_date = models.DateField(null=True, blank=True, verbose_name='成立日期')
    client_contact_person = models.CharField(max_length=100, blank=True, verbose_name='项目负责人')
    client_phone = models.CharField(max_length=20, blank=True, verbose_name='项目负责人联系电话')
    # 启信宝公开信息（可选）
    client_litigation_count = models.IntegerField(null=True, blank=True, verbose_name='司法案件数量（启信宝公开数量）')
    client_enforcement_count = models.IntegerField(null=True, blank=True, verbose_name='被执行人数量（启信宝公开数量）')
    client_final_case_count = models.IntegerField(null=True, blank=True, verbose_name='终本案件数量（启信宝公开数量）')
    client_restriction_count = models.IntegerField(null=True, blank=True, verbose_name='限制高消费数量（启信宝公开数量）')
    # 保留原有字段用于向后兼容
    client_email = models.EmailField(blank=True, verbose_name='电子邮箱')
    client_address = models.CharField(max_length=500, blank=True, verbose_name='通讯地址')
    client_leader = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='client_projects',
        verbose_name='甲方负责人账号'
    )
    
    # 设计单位信息
    design_company = models.CharField(max_length=200, blank=True, verbose_name='设计单位名称')
    design_credit_code = models.CharField(max_length=50, blank=True, verbose_name='统一社会信用代码')
    design_contact_person = models.CharField(max_length=100, blank=True, verbose_name='项目负责人')
    design_phone = models.CharField(max_length=20, blank=True, verbose_name='项目负责人联系电话')
    # 保留原有字段用于向后兼容
    design_email = models.EmailField(blank=True, verbose_name='设计方电子邮箱')
    design_leader = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='design_projects',
        verbose_name='设计方负责人账号'
    )
    
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
    
    STRUCTURE_TYPE_CHOICES = [
        ('shear_wall', '剪力墙结构'),
        ('frame', '框架结构'),
        ('steel', '钢结构'),
        ('other', '其他'),
    ]
    structure_type = models.CharField(
        max_length=50,
        choices=STRUCTURE_TYPE_CHOICES,
        blank=True,
        null=True,
        verbose_name='结构形式'
    )
    
    # 项目规模（分批次）
    # 存储格式: [{"batch_name": "一批次", "total_area": 1000.00, "aboveground_area": 800.00, "underground_area": 200.00, "aboveground_floors": 10, "underground_floors": 2}, ...]
    project_batches = models.JSONField(default=list, blank=True, verbose_name='项目规模（分批次）')
    
    # 服务范围（一批次/二批次等，多个用逗号分隔）
    service_scope = models.CharField(max_length=500, blank=True, verbose_name='服务范围')
    
    # 特殊要求
    client_special_requirements = models.TextField(blank=True, verbose_name='甲方特殊要求')
    technical_difficulties = models.TextField(blank=True, verbose_name='技术难点说明')
    risk_assessment = models.TextField(blank=True, verbose_name='项目风险预判')
    
    # 时间信息
    start_date = models.DateField(null=True, blank=True, verbose_name='开始日期')
    end_date = models.DateField(null=True, blank=True, verbose_name='结束日期')
    actual_start_date = models.DateField(null=True, blank=True, verbose_name='实际开始日期')
    actual_end_date = models.DateField(null=True, blank=True, verbose_name='实际结束日期')
    
    # 合同金额计算相关字段
    BILLING_METHOD_CHOICES = [
        ('pure_rate', '纯费率计费'),
        ('base_fee_rate', '基本费+费率取费'),
        ('unit_price', '综合单价包干'),
    ]
    billing_method = models.CharField(
        max_length=50,
        choices=BILLING_METHOD_CHOICES,
        blank=True,
        null=True,
        verbose_name='服务费取费方式'
    )
    
    REGION_CHOICES = [
        ('provincial_capital', '省会城市'),
        ('non_provincial_city', '非省会市级城市'),
        ('county_city', '县级城市'),
        ('tier1_city', '北京、上海、广州、深圳'),
    ]
    
    project_region = models.CharField(
        max_length=50,
        choices=REGION_CHOICES,
        blank=True,
        null=True,
        verbose_name='项目区域'
    )
    # structure_type 字段已存在，但需要更新为使用 choices
    
    base_fee = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='基本费（元）'
    )
    unit_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='包干单价（元/平方米）'
    )
    fee_rate_coefficient = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        null=True,
        blank=True,
        verbose_name='取费系数（%）'
    )
    
    # 状态和财务
    status = models.CharField(max_length=30, choices=PROJECT_STATUS, default='draft', verbose_name='项目状态')
    contract_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, verbose_name='合同金额（元）')
    estimated_cost = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, verbose_name='预估成本')
    estimated_savings = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, verbose_name='预计节省金额')
    launch_status = models.CharField(max_length=30, choices=LAUNCH_STATUS, default='handover_pending', verbose_name='项目启动状态')
    launch_status_updated_time = models.DateTimeField(default=timezone.now, verbose_name='启动状态更新时间')
    handover_submitted_time = models.DateTimeField(null=True, blank=True, verbose_name='商务移交时间')
    drawing_precheck_completed_time = models.DateTimeField(null=True, blank=True, verbose_name='图纸预审完成时间')
    start_notice_sent_time = models.DateTimeField(null=True, blank=True, verbose_name='开工通知时间')
    flow_step = models.CharField(max_length=40, choices=FLOW_STEPS, default='pending_documents', verbose_name='当前流程步骤')
    flow_step_started_time = models.DateTimeField(default=timezone.now, verbose_name='步骤开始时间')
    flow_deadline = models.DateTimeField(null=True, blank=True, verbose_name='当前步骤截止时间')
    flow_payload = models.JSONField(default=dict, blank=True, verbose_name='流程上下文')
    
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
    
    def calculate_contract_amount(self):
        """计算合同金额"""
        from decimal import Decimal
        
        if not self.billing_method:
            return None
        
        # 获取建筑面积（从project_batches计算总和，如果没有则使用building_area）
        total_building_area = self.building_area or Decimal('0')
        if self.project_batches:
            total_building_area = sum(
                Decimal(str(batch.get('total_area', 0) or 0))
                for batch in self.project_batches
            )
        
        if total_building_area <= 0:
            return None
        
        # 获取地下面积和地上面积
        total_underground_area = sum(
            Decimal(str(batch.get('underground_area', 0) or 0))
            for batch in self.project_batches
        ) if self.project_batches else (self.underground_area or Decimal('0'))
        
        # 计算地下面积/总建筑面积比例
        underground_ratio = (total_underground_area / total_building_area) if total_building_area > 0 else Decimal('0')
        
        # 获取服务专业数量
        profession_count = self.service_professions.count()
        # 标准专业：结构+构造+电气+给排水 = 4个
        standard_professions = ['结构', '构造', '电气', '给排水']
        selected_profession_names = [p.name for p in self.service_professions.all()]
        
        if self.billing_method == 'pure_rate':
            # 纯费率计费：合同金额 = 建筑面积 * 25元/平方米 * 10% * 调整系数
            
            # 节省金额调整系数
            # 服务类型
            service_type_coef = Decimal('1.0')
            if self.service_type:
                service_type_code = self.service_type.code if hasattr(self.service_type, 'code') else ''
                if 'result_optimization' in service_type_code or '结果优化' in str(self.service_type):
                    service_type_coef = Decimal('1.0')
                elif 'process_optimization' in service_type_code or '过程优化' in str(self.service_type):
                    service_type_coef = Decimal('1.5')
            
            # 项目业态
            business_type_coef = Decimal('1.0')
            if self.business_type == 'residential':
                business_type_coef = Decimal('1.0')
            elif self.business_type == 'complex':
                business_type_coef = Decimal('1.3')
            elif self.business_type == 'industrial':
                business_type_coef = Decimal('1.1')
            
            # 服务专业系数
            profession_coef = Decimal('1.0')
            # 检查标准专业是否存在
            has_structure = any('结构' in name for name in selected_profession_names)
            has_construction = any('构造' in name for name in selected_profession_names)
            has_electrical = any('电气' in name for name in selected_profession_names)
            has_plumbing = any('给排水' in name for name in selected_profession_names)
            
            if not has_structure or not has_construction or not has_electrical or not has_plumbing:
                # 减少专业
                if not has_structure:
                    profession_coef -= Decimal('0.35')
                if not has_construction:
                    profession_coef -= Decimal('0.40')
                if not has_electrical:
                    profession_coef -= Decimal('0.15')
                if not has_plumbing:
                    profession_coef -= Decimal('0.1')
            elif profession_count > 4:
                # 增加专业
                extra = profession_count - 4
                profession_coef += Decimal(str(extra)) * Decimal('0.15')
            
            # 项目区域
            region_coef = Decimal('1.0')
            if self.project_region == 'provincial_capital':
                region_coef = Decimal('1.0')
            elif self.project_region == 'non_provincial_city':
                region_coef = Decimal('1.1')
            elif self.project_region == 'county_city':
                region_coef = Decimal('1.2')
            elif self.project_region == 'tier1_city':
                region_coef = Decimal('0.7')
            
            # 地下面积比例
            underground_coef = Decimal('1.2') if underground_ratio > Decimal('0.2') else Decimal('1.0')
            
            # 结构形式
            structure_coef = Decimal('1.0')
            if self.structure_type == 'shear_wall':
                structure_coef = Decimal('1.0')
            elif self.structure_type == 'frame':
                structure_coef = Decimal('0.6')
            elif self.structure_type == 'steel':
                structure_coef = Decimal('1.2')
            else:
                structure_coef = Decimal('0.9')
            
            # 取费系数（如果未设置，使用默认10%）
            fee_rate = (self.fee_rate_coefficient / Decimal('10')) if self.fee_rate_coefficient else Decimal('1.0')
            
            # 综合调整系数
            adjustment_coef = service_type_coef * business_type_coef * profession_coef * region_coef * underground_coef * structure_coef * fee_rate
            
            # 计算合同金额
            contract_amount = total_building_area * Decimal('25') * Decimal('0.1') * adjustment_coef
            
            return contract_amount
        
        elif self.billing_method == 'base_fee_rate':
            # 基本费+费率取费
            # 合同金额 = 基本费 + 建筑面积 * 25元/平方米 * 10% * 节省金额综合调整系数 * 取费系数综合调整系数
            # 或者：合同金额 = 建筑面积 * 20元/平方米 * 10% * 节省金额综合调整系数 * 取费系数综合调整系数
            
            # 节省金额综合调整系数
            # 服务类型
            service_type_coef = Decimal('1.0')
            if self.service_type:
                service_type_code = self.service_type.code if hasattr(self.service_type, 'code') else ''
                if 'result_optimization' in service_type_code or '结果优化' in str(self.service_type):
                    service_type_coef = Decimal('1.0')
                elif 'process_optimization' in service_type_code or '过程优化' in str(self.service_type):
                    service_type_coef = Decimal('1.2')
            
            # 项目业态
            business_type_coef = Decimal('1.0')
            if self.business_type == 'residential':
                business_type_coef = Decimal('1.0')
            elif self.business_type == 'complex':
                business_type_coef = Decimal('1.3')
            elif self.business_type == 'industrial':
                business_type_coef = Decimal('1.1')
            
            # 服务专业系数
            profession_coef = Decimal('1.0')
            if profession_count < 4:
                missing = 4 - profession_count
                profession_coef -= Decimal(str(missing)) * Decimal('0.25')
            elif profession_count > 4:
                extra = profession_count - 4
                profession_coef += Decimal(str(extra)) * Decimal('0.1')
            
            # 项目区域
            region_coef = Decimal('1.0')
            if self.project_region == 'provincial_capital':
                region_coef = Decimal('1.0')
            elif self.project_region == 'non_provincial_city':
                region_coef = Decimal('1.1')
            elif self.project_region == 'county_city':
                region_coef = Decimal('1.2')
            elif self.project_region == 'tier1_city':
                region_coef = Decimal('0.7')
            
            # 地下面积比例
            underground_coef = Decimal('1.2') if underground_ratio > Decimal('0.2') else Decimal('1.0')
            
            # 结构形式
            structure_coef = Decimal('1.0')
            if self.structure_type == 'shear_wall':
                structure_coef = Decimal('1.0')
            elif self.structure_type == 'frame':
                structure_coef = Decimal('0.6')
            elif self.structure_type == 'steel':
                structure_coef = Decimal('1.2')
            
            # 节省金额综合调整系数
            saving_adjustment_coef = service_type_coef * business_type_coef * profession_coef * region_coef * underground_coef * structure_coef
            
            # 取费系数综合调整系数（取费系数的最小值/10%）
            fee_rate_coef = (self.fee_rate_coefficient / Decimal('10')) if self.fee_rate_coefficient else Decimal('1.0')
            
            # 计算合同金额
            base_fee_amount = self.base_fee or Decimal('0')
            if base_fee_amount > 0:
                # 使用基本费 + 费率方式
                contract_amount = base_fee_amount + total_building_area * Decimal('25') * Decimal('0.1') * saving_adjustment_coef * fee_rate_coef
            else:
                # 使用20元/平方米方式
                contract_amount = total_building_area * Decimal('20') * Decimal('0.1') * saving_adjustment_coef * fee_rate_coef
            
            return contract_amount
        
        elif self.billing_method == 'unit_price':
            # 综合单价包干：合同金额 = 建筑面积 * 包干单价 * 综合调整系数
            
            if not self.unit_price:
                return None
            
            # 综合调整系数
            service_type_coef = Decimal('0.8')
            if self.service_type:
                service_type_code = self.service_type.code if hasattr(self.service_type, 'code') else ''
                if 'detailed_review' in service_type_code or '精细化审图' in str(self.service_type):
                    service_type_coef = Decimal('0.80')
                elif 'full_process_consulting' in service_type_code or '过程咨询' in str(self.service_type):
                    service_type_coef = Decimal('0.9')
            
            contract_amount = total_building_area * self.unit_price * service_type_coef
            
            return contract_amount
        
        return None
    
    def advance_flow(self, step, *, deadline=None, payload=None, actor=None, notes=''):
        prev_step = self.flow_step
        self.flow_step = step
        self.flow_step_started_time = timezone.now()
        self.flow_deadline = deadline
        update_fields = ['flow_step', 'flow_step_started_time', 'flow_deadline']
        if payload is not None:
            self.flow_payload = payload
            update_fields.append('flow_payload')
        self.save(update_fields=update_fields)
        ProjectFlowLog.objects.create(
            project=self,
            action='advance',
            from_step=prev_step,
            to_step=step,
            actor=actor,
            notes=notes or '',
            metadata=payload or {},
        )

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

class ProjectFlowLog(models.Model):
    """项目流程日志"""
    ACTION_CHOICES = [
        ('advance', '流程流转'),
        ('note', '备注'),
    ]

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='flow_logs', verbose_name='项目')
    action = models.CharField(max_length=30, choices=ACTION_CHOICES, default='advance', verbose_name='动作类型')
    from_step = models.CharField(max_length=40, blank=True, verbose_name='原步骤')
    to_step = models.CharField(max_length=40, blank=True, verbose_name='目标步骤')
    actor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='project_flow_actions', verbose_name='操作人')
    notes = models.TextField(blank=True, verbose_name='备注')
    metadata = models.JSONField(default=dict, blank=True, verbose_name='扩展信息')
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')

    class Meta:
        db_table = 'project_center_flow_log'
        verbose_name = '项目流程日志'
        verbose_name_plural = verbose_name
        ordering = ['-created_time']

    def __str__(self):
        return f"{self.project} - {self.action}"


class ProjectTeam(models.Model):
    """项目团队"""

    UNIT_CHOICES = [
        ('management', '管理团队'),
        ('business', '商务团队'),
        ('internal_tech', '内部技术团队'),
        ('external_tech', '外部技术团队'),
        ('internal_cost', '内部结算团队'),
        ('external_cost', '外部结算团队'),
        ('client_side', '甲方团队'),
        ('design_side', '设计团队'),
    ]

    ROLE_CHOICES = [
        ('business_manager', '商务经理'),
        ('project_manager', '项目经理'),
        ('professional_leader', '内部专业负责人'),
        ('engineer', '内部专业工程师'),
        ('technical_assistant', '技术助理'),
        ('external_leader', '外部专业负责人'),
        ('external_engineer', '外部专业工程师'),
        ('cost_reviewer_civil', '内部土建审核人'),
        ('cost_reviewer_installation', '内部安装审核人'),
        ('cost_engineer_civil', '内部土建造价师'),
        ('cost_engineer_installation', '内部安装造价师'),
        ('external_cost_reviewer_civil', '外部土建审核人'),
        ('external_cost_reviewer_installation', '外部安装审核人'),
        ('external_cost_engineer_civil', '外部土建造价师'),
        ('external_cost_engineer_installation', '外部安装造价师'),
        ('client_lead', '甲方项目负责人'),
        ('client_engineer', '甲方专业工程师'),
        ('design_lead', '设计方项目负责人'),
        ('design_engineer', '设计方专业工程师'),
    ]

    ROLE_UNIT_MAP = {
        'business_manager': 'business',
        'project_manager': 'management',
        'professional_leader': 'internal_tech',
        'engineer': 'internal_tech',
        'technical_assistant': 'internal_tech',
        'external_leader': 'external_tech',
        'external_engineer': 'external_tech',
        'cost_reviewer_civil': 'internal_cost',
        'cost_reviewer_installation': 'internal_cost',
        'cost_engineer_civil': 'internal_cost',
        'cost_engineer_installation': 'internal_cost',
        'external_cost_reviewer_civil': 'external_cost',
        'external_cost_reviewer_installation': 'external_cost',
        'external_cost_engineer_civil': 'external_cost',
        'external_cost_engineer_installation': 'external_cost',
        'client_lead': 'client_side',
        'client_engineer': 'client_side',
        'design_lead': 'design_side',
        'design_engineer': 'design_side',
    }

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='team_members', verbose_name='项目')
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='成员')
    service_profession = models.ForeignKey(ServiceProfession, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='所属专业')
    role = models.CharField(max_length=50, choices=ROLE_CHOICES, verbose_name='角色')
    unit = models.CharField(max_length=32, choices=UNIT_CHOICES, default='management', verbose_name='所属团队')
    is_external = models.BooleanField(default=False, verbose_name='是否外部成员')
    join_date = models.DateField(default=timezone.now, verbose_name='加入日期')
    leave_date = models.DateField(null=True, blank=True, verbose_name='离开日期')
    responsibility = models.TextField(blank=True, verbose_name='职责描述')
    is_active = models.BooleanField(default=True, verbose_name='是否有效')
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    
    class Meta:
        db_table = 'project_center_team'
        verbose_name = '项目团队'
        verbose_name_plural = verbose_name
        unique_together = ['project', 'user', 'role', 'service_profession']

    def save(self, *args, **kwargs):
        if not self.unit:
            self.unit = self.ROLE_UNIT_MAP.get(self.role, 'management')
        else:
            self.unit = self.ROLE_UNIT_MAP.get(self.role, self.unit)
        self.is_external = self.unit in {'external_tech', 'external_cost', 'client_side', 'design_side'}
        super().save(*args, **kwargs)


class ProjectTeamChangeLog(models.Model):
    """项目团队变更日志"""
    ACTION_CHOICES = [
        ('added', '新增'),
        ('removed', '移除'),
    ]

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='team_change_logs', verbose_name='项目')
    member = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='team_change_logs', verbose_name='成员')
    role = models.CharField(max_length=50, verbose_name='角色')
    unit = models.CharField(max_length=32, choices=ProjectTeam.UNIT_CHOICES, default='management', verbose_name='所属团队')
    is_external = models.BooleanField(default=False, verbose_name='是否外部成员')
    service_profession = models.ForeignKey(ServiceProfession, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='所属专业')
    action = models.CharField(max_length=20, choices=ACTION_CHOICES, verbose_name='操作类型')
    operator = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='team_change_operations', verbose_name='操作人')
    timestamp = models.DateTimeField(default=timezone.now, verbose_name='操作时间')
    notes = models.TextField(blank=True, verbose_name='备注')

    class Meta:
        db_table = 'project_center_team_log'
        verbose_name = '项目团队变更日志'
        verbose_name_plural = verbose_name
        ordering = ['-timestamp']


class ProjectTeamNotification(models.Model):
    """项目团队通知"""
    CATEGORY_CHOICES = [
        ('team_change', '团队变更'),
        ('quality_alert', '质量提醒'),
    ]

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='team_notifications', verbose_name='项目')
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='team_notifications', verbose_name='接收人')
    operator = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='team_notifications_sent', verbose_name='操作人')
    title = models.CharField(max_length=200, verbose_name='标题')
    message = models.TextField(verbose_name='内容')
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='team_change', verbose_name='通知分类')
    action_url = models.CharField(max_length=300, blank=True, verbose_name='跳转链接')
    is_read = models.BooleanField(default=False, verbose_name='是否已读')
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    read_time = models.DateTimeField(null=True, blank=True, verbose_name='读取时间')
    context = models.JSONField(default=dict, blank=True, verbose_name='上下文信息')

    class Meta:
        db_table = 'project_center_team_notification'
        verbose_name = '项目团队通知'
        verbose_name_plural = verbose_name
        ordering = ['-created_time']

    def __str__(self):
        return f"{self.project.project_number if self.project_id else '未知项目'} - {self.title}"


class ProjectTask(models.Model):
    """项目阶段任务 / 待办"""

    STATUS_CHOICES = [
        ('pending', '待处理'),
        ('in_progress', '进行中'),
        ('completed', '已完成'),
        ('cancelled', '已取消'),
    ]

    TASK_TYPE_CHOICES = [
        ('project_complete_info', '完善项目信息'),
        ('configure_team', '配置项目团队'),
        ('client_upload_pre_docs', '甲方上传优化前资料'),
        ('client_resubmit_pre_docs', '甲方补充/重传资料'),
        ('internal_precheck_docs', '我方预审优化前资料'),
        ('client_issue_start_notice', '甲方发布开工通知'),
    ]

    ACTIVE_STATUSES = ('pending', 'in_progress')

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='tasks', verbose_name='项目')
    title = models.CharField(max_length=200, verbose_name='任务标题')
    task_type = models.CharField(max_length=64, choices=TASK_TYPE_CHOICES, verbose_name='任务类型')
    description = models.TextField(blank=True, verbose_name='任务说明')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='状态')
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='project_tasks',
        verbose_name='指派给'
    )
    assigned_role = models.CharField(max_length=50, blank=True, verbose_name='指派角色')
    target_unit = models.CharField(max_length=32, blank=True, verbose_name='目标团队')
    due_time = models.DateTimeField(null=True, blank=True, verbose_name='截止时间')
    completed_time = models.DateTimeField(null=True, blank=True, verbose_name='完成时间')
    completed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='project_tasks_completed',
        verbose_name='完成操作人'
    )
    cancelled_time = models.DateTimeField(null=True, blank=True, verbose_name='取消时间')
    cancelled_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='project_tasks_cancelled',
        verbose_name='取消操作人'
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='project_tasks_created',
        verbose_name='创建人'
    )
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    updated_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    metadata = models.JSONField(default=dict, blank=True, verbose_name='扩展信息')

    class Meta:
        db_table = 'project_center_task'
        verbose_name = '项目任务'
        verbose_name_plural = verbose_name
        ordering = ['due_time', 'created_time']
        indexes = [
            models.Index(fields=['project', 'task_type']),
            models.Index(fields=['project', 'status']),
        ]

    def __str__(self):
        return f"{self.project.name if self.project_id else '未知项目'} - {self.get_task_type_display()}"


class ProjectDesignReply(models.Model):
    REPLY_STATUS_CHOICES = [
        ('agree', '同意优化'),
        ('reject', '不同意优化'),
        ('partial', '部分同意'),
    ]

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='design_replies', verbose_name='项目')
    opinion = models.ForeignKey('production_quality.Opinion', on_delete=models.CASCADE, related_name='design_replies', verbose_name='关联意见', null=True, blank=True)
    issue_title = models.CharField(max_length=200, verbose_name='事项 / 问题')
    status = models.CharField(max_length=20, choices=REPLY_STATUS_CHOICES, default='agree', verbose_name='回复结果')
    response_detail = models.TextField(blank=True, verbose_name='回复说明')
    submitted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='design_replies', verbose_name='提交人')
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    updated_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'project_center_design_reply'
        verbose_name = '设计方回复'
        verbose_name_plural = verbose_name
        ordering = ['-created_time']
        indexes = [
            models.Index(fields=['project', 'opinion']),
        ]

    def __str__(self):
        return f"{self.project.name if self.project_id else ''} - {self.issue_title}"


class ProjectMeetingRecord(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='meeting_records', verbose_name='项目')
    meeting_date = models.DateField(default=timezone.now, verbose_name='会议日期')
    topic = models.CharField(max_length=200, verbose_name='会议主题')
    client_decision = models.TextField(blank=True, verbose_name='甲方意见')
    design_decision = models.TextField(blank=True, verbose_name='设计方意见')
    consultant_decision = models.TextField(blank=True, verbose_name='我方意见')
    conclusions = models.TextField(blank=True, verbose_name='结论 / 待办')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='meeting_records', verbose_name='记录人')
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')

    class Meta:
        db_table = 'project_center_meeting_record'
        verbose_name = '三方会议记录'
        verbose_name_plural = verbose_name
        ordering = ['-meeting_date', '-created_time']

    def __str__(self):
        return f"{self.project.name if self.project_id else ''} - {self.topic}"


class ProjectMeetingDecision(models.Model):
    DECISION_CHOICES = [
        ('agree', '同意'),
        ('reject', '不同意'),
        ('partial', '部分同意'),
        ('pending', '待确认'),
    ]

    meeting = models.ForeignKey(ProjectMeetingRecord, on_delete=models.CASCADE, related_name='decisions', verbose_name='会议记录')
    opinion = models.ForeignKey('production_quality.Opinion', on_delete=models.CASCADE, related_name='meeting_decisions', verbose_name='关联意见')
    decision = models.CharField(max_length=20, choices=DECISION_CHOICES, default='pending', verbose_name='会议结论')
    client_comment = models.TextField(blank=True, verbose_name='甲方意见')
    design_comment = models.TextField(blank=True, verbose_name='设计方意见')
    consultant_comment = models.TextField(blank=True, verbose_name='我方意见')
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')

    class Meta:
        db_table = 'project_center_meeting_decision'
        verbose_name = '三方会议结论'
        verbose_name_plural = verbose_name
        unique_together = ('meeting', 'opinion')
        ordering = ['-created_time']

    def __str__(self):
        return f"{self.meeting_id} - {self.opinion_id}"

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


class ProjectDrawingSubmission(models.Model):
    """项目图纸提交"""

    STATUS_CHOICES = [
        ('submitted', '待预审'),
        ('in_review', '预审中'),
        ('changes_requested', '需补充资料'),
        ('approved', '预审通过'),
        ('cancelled', '已取消'),
    ]

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='drawing_submissions', verbose_name='项目')
    title = models.CharField(max_length=200, verbose_name='提交标题')
    version = models.CharField(max_length=50, blank=True, verbose_name='版本号')
    description = models.TextField(blank=True, verbose_name='提交说明')
    submitter = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='drawing_submissions', verbose_name='提交人')
    submitter_role = models.CharField(max_length=100, blank=True, verbose_name='提交人角色')
    submitted_time = models.DateTimeField(default=timezone.now, verbose_name='提交时间')
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='submitted', verbose_name='预审状态')
    review_deadline = models.DateTimeField(null=True, blank=True, verbose_name='预审截止时间')
    latest_review = models.ForeignKey('ProjectDrawingReview', on_delete=models.SET_NULL, null=True, blank=True, related_name='+', verbose_name='最新预审记录')
    client_notified = models.BooleanField(default=False, verbose_name='是否已通知甲方')
    client_notified_time = models.DateTimeField(null=True, blank=True, verbose_name='甲方通知时间')
    client_notification_channel = models.CharField(max_length=30, blank=True, verbose_name='甲方通知渠道')
    metadata = models.JSONField(default=dict, blank=True, verbose_name='扩展信息')
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    updated_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'project_center_drawing_submission'
        verbose_name = '项目图纸提交'
        verbose_name_plural = verbose_name
        ordering = ['-submitted_time']

    def __str__(self):
        return f"{self.project.project_number} - {self.title}"


class ProjectDrawingFile(models.Model):
    """项目图纸文件"""

    FILE_CATEGORIES = [
        ('general', '通用资料'),
        ('architecture', '建筑'),
        ('structure', '结构'),
        ('mep', '机电'),
        ('civil', '土建'),
        ('other', '其他'),
    ]

    submission = models.ForeignKey(ProjectDrawingSubmission, on_delete=models.CASCADE, related_name='files', verbose_name='图纸提交')
    name = models.CharField(max_length=200, verbose_name='文件名称')
    category = models.CharField(max_length=30, choices=FILE_CATEGORIES, default='general', verbose_name='文件分类')
    file = models.FileField(upload_to='project_drawings/%Y/%m/', verbose_name='文件')
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='drawing_files', verbose_name='上传人')
    uploaded_time = models.DateTimeField(default=timezone.now, verbose_name='上传时间')
    notes = models.TextField(blank=True, verbose_name='备注')
    metadata = models.JSONField(default=dict, blank=True, verbose_name='扩展信息')

    class Meta:
        db_table = 'project_center_drawing_file'
        verbose_name = '项目图纸文件'
        verbose_name_plural = verbose_name
        ordering = ['-uploaded_time']

    def __str__(self):
        return self.name


class ProjectDrawingReview(models.Model):
    """项目图纸预审记录"""

    RESULT_CHOICES = [
        ('pending', '待处理'),
        ('approved', '通过'),
        ('changes_requested', '需修改'),
    ]

    submission = models.ForeignKey(ProjectDrawingSubmission, on_delete=models.CASCADE, related_name='reviews', verbose_name='图纸提交')
    reviewer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='drawing_reviews', verbose_name='预审人')
    result = models.CharField(max_length=30, choices=RESULT_CHOICES, default='pending', verbose_name='预审结果')
    comment = models.TextField(blank=True, verbose_name='预审意见')
    reviewed_time = models.DateTimeField(default=timezone.now, verbose_name='预审时间')
    attachments = models.JSONField(default=list, blank=True, verbose_name='附件列表')
    metadata = models.JSONField(default=dict, blank=True, verbose_name='扩展信息')

    class Meta:
        db_table = 'project_center_drawing_review'
        verbose_name = '项目图纸预审记录'
        verbose_name_plural = verbose_name
        ordering = ['-reviewed_time']

    def __str__(self):
        return f"{self.submission} - {self.get_result_display()}"


class ProjectStartNotice(models.Model):
    """项目开工通知"""

    CHANNEL_CHOICES = [
        ('system', '系统通知'),
        ('email', '邮件'),
        ('sms', '短信'),
        ('manual', '线下确认'),
    ]

    STATUS_CHOICES = [
        ('pending', '待发送'),
        ('sent', '已发送'),
        ('failed', '发送失败'),
        ('acknowledged', '已确认'),
    ]

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='start_notices', verbose_name='项目')
    submission = models.ForeignKey(ProjectDrawingSubmission, on_delete=models.SET_NULL, null=True, blank=True, related_name='start_notices', verbose_name='关联图纸提交')
    subject = models.CharField(max_length=200, verbose_name='通知主题')
    message = models.TextField(verbose_name='通知内容')
    channel = models.CharField(max_length=30, choices=CHANNEL_CHOICES, default='system', verbose_name='通知渠道')
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='pending', verbose_name='通知状态')
    recipient_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='received_start_notices', verbose_name='接收人')
    recipient_name = models.CharField(max_length=100, blank=True, verbose_name='接收人姓名')
    recipient_phone = models.CharField(max_length=20, blank=True, verbose_name='接收人电话')
    recipient_email = models.EmailField(blank=True, verbose_name='接收人邮箱')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='start_notices_created', verbose_name='创建人')
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    sent_time = models.DateTimeField(null=True, blank=True, verbose_name='发送时间')
    acknowledged_time = models.DateTimeField(null=True, blank=True, verbose_name='确认时间')
    failure_reason = models.TextField(blank=True, verbose_name='失败原因')
    metadata = models.JSONField(default=dict, blank=True, verbose_name='扩展信息')

    class Meta:
        db_table = 'project_center_start_notice'
        verbose_name = '项目开工通知'
        verbose_name_plural = verbose_name
        ordering = ['-created_time']

    def __str__(self):
        return f"{self.project.project_number} - {self.subject}"

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


class ProjectInitiationApproval(models.Model):
    """项目立项审批"""
    APPROVAL_STATUS_CHOICES = [
        ('pending_business_manager', '待商务经理提交'),
        ('pending_supervisor', '待直接上级审批'),
        ('pending_technical_manager', '待技术部经理审批'),
        ('approved', '审批通过'),
        ('rejected', '审批驳回'),
    ]
    
    project = models.OneToOneField(
        Project,
        on_delete=models.CASCADE,
        related_name='initiation_approval',
        verbose_name='关联项目'
    )
    
    # 提交信息
    submitted_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='initiation_approvals_submitted',
        verbose_name='提交人（商务经理）'
    )
    submitted_time = models.DateTimeField(default=timezone.now, verbose_name='提交时间')
    submission_comment = models.TextField(blank=True, verbose_name='提交说明')
    
    # 审批流程
    status = models.CharField(
        max_length=30,
        choices=APPROVAL_STATUS_CHOICES,
        default='pending_business_manager',
        verbose_name='审批状态'
    )
    
    # 直接上级审批
    supervisor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='initiation_approvals_supervisor',
        verbose_name='直接上级'
    )
    supervisor_approved_time = models.DateTimeField(null=True, blank=True, verbose_name='直接上级审批时间')
    supervisor_comment = models.TextField(blank=True, verbose_name='直接上级审批意见')
    
    # 技术部经理审批
    technical_manager = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='initiation_approvals_technical',
        verbose_name='技术部经理'
    )
    technical_manager_approved_time = models.DateTimeField(null=True, blank=True, verbose_name='技术部经理审批时间')
    technical_manager_comment = models.TextField(blank=True, verbose_name='技术部经理审批意见')
    
    # 最终审批结果
    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='initiation_approvals_approved',
        verbose_name='最终审批人'
    )
    approved_time = models.DateTimeField(null=True, blank=True, verbose_name='审批通过时间')
    rejected_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='initiation_approvals_rejected',
        verbose_name='驳回人'
    )
    rejected_time = models.DateTimeField(null=True, blank=True, verbose_name='驳回时间')
    rejection_reason = models.TextField(blank=True, verbose_name='驳回原因')
    
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    updated_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        db_table = 'project_center_initiation_approval'
        verbose_name = '项目立项审批'
        verbose_name_plural = verbose_name
        ordering = ['-created_time']
    
    def __str__(self):
        return f"{self.project.project_number if self.project.project_number else '待生成编号'} - {self.get_status_display()}"
