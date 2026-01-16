from django.db import models
from django.utils import timezone
from backend.apps.system_management.models import User


class ServiceType(models.Model):
    """服务类型"""
    code = models.CharField(max_length=50, unique=True, verbose_name='服务类型编码')
    name = models.CharField(max_length=100, verbose_name='服务类型名称')
    order = models.PositiveIntegerField(default=0, verbose_name='排序')

    class Meta:
        db_table = 'production_management_service_type'
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
        db_table = 'production_management_service_profession'
        verbose_name = '服务专业'
        verbose_name_plural = verbose_name
        ordering = ['service_type__order', 'order', 'id']
        unique_together = ('service_type', 'code')

    def __str__(self):
        return f"{self.service_type.name} - {self.name}"


class BusinessType(models.Model):
    """项目业态"""
    code = models.CharField(max_length=50, unique=True, verbose_name='业态编码')
    name = models.CharField(max_length=100, verbose_name='业态名称')
    order = models.PositiveIntegerField(default=0, verbose_name='排序')
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    description = models.TextField(blank=True, verbose_name='业态描述')

    class Meta:
        db_table = 'production_management_business_type'
        verbose_name = '项目业态'
        verbose_name_plural = verbose_name
        ordering = ['order', 'id']

    def __str__(self):
        return self.name


class DesignStage(models.Model):
    """图纸阶段"""
    code = models.CharField(max_length=50, unique=True, verbose_name='阶段编码')
    name = models.CharField(max_length=100, verbose_name='阶段名称')
    order = models.PositiveIntegerField(default=0, verbose_name='排序')
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    description = models.TextField(blank=True, verbose_name='阶段描述')

    class Meta:
        db_table = 'production_management_design_stage'
        verbose_name = '图纸阶段'
        verbose_name_plural = verbose_name
        ordering = ['order', 'id']

    def __str__(self):
        return self.name


class SettlementNodeType(models.Model):
    """结算节点类型"""
    code = models.CharField(max_length=50, unique=True, verbose_name='节点编码')
    name = models.CharField(max_length=100, verbose_name='节点名称')
    order = models.PositiveIntegerField(default=0, verbose_name='排序')
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    description = models.TextField(blank=True, verbose_name='节点描述')

    class Meta:
        db_table = 'production_management_settlement_node_type'
        verbose_name = '结算节点类型'
        verbose_name_plural = verbose_name
        ordering = ['order', 'id']

    def __str__(self):
        return self.name


class AfterSalesNodeType(models.Model):
    """售后节点类型"""
    code = models.CharField(max_length=50, unique=True, verbose_name='节点编码')
    name = models.CharField(max_length=100, verbose_name='节点名称')
    order = models.PositiveIntegerField(default=0, verbose_name='排序')
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    description = models.TextField(blank=True, verbose_name='节点描述')

    class Meta:
        db_table = 'production_management_after_sales_node_type'
        verbose_name = '售后节点类型'
        verbose_name_plural = verbose_name
        ordering = ['order', 'id']

    def __str__(self):
        return self.name


class StructureType(models.Model):
    """结构形式"""
    code = models.CharField(max_length=50, unique=True, verbose_name='结构形式编码')
    name = models.CharField(max_length=100, verbose_name='结构形式名称')
    order = models.PositiveIntegerField(default=0, verbose_name='排序')
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    description = models.TextField(blank=True, verbose_name='结构形式描述')

    class Meta:
        db_table = 'production_management_structure_type'
        verbose_name = '结构形式'
        verbose_name_plural = verbose_name
        ordering = ['order', 'id']

    def __str__(self):
        return self.name


class DesignUnitCategory(models.Model):
    """设计单位分类"""
    code = models.CharField(max_length=50, unique=True, verbose_name='分类编码')
    name = models.CharField(max_length=100, verbose_name='分类名称')
    order = models.PositiveIntegerField(default=0, verbose_name='排序')
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    description = models.TextField(blank=True, verbose_name='分类描述')

    class Meta:
        db_table = 'production_management_design_unit_category'
        verbose_name = '设计单位分类'
        verbose_name_plural = verbose_name
        ordering = ['order', 'id']

    def __str__(self):
        return self.name


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
    
    # BUSINESS_TYPES 已迁移到 BusinessType 模型，保留此常量用于向后兼容和数据迁移
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
    
    # DESIGN_STAGES 已迁移到 DesignStage 模型，保留此常量用于向后兼容和数据迁移
    DESIGN_STAGES = [
        ('preliminary_scheme', '初步方案'),
        ('detailed_scheme', '详细方案'),
        ('preliminary_design', '初步设计'),
        ('extended_preliminary_design', '扩初设计'),
        ('construction_drawing_design', '施工图设计'),
        ('construction_drawing_review', '施工图审查'),
        ('construction_phase', '施工阶段'),
        ('special_design', '专项设计'),
        # 保留旧选项以兼容历史数据
        ('construction_drawing_unreviewed', '施工图（未审图）'),
        ('construction_drawing_reviewed', '施工图（已审图）'),
        ('extended_preliminary', '扩初阶段'),
        ('detailed_planning', '详规阶段'),
    ]
    
    # 基础信息
    project_number = models.CharField(max_length=50, unique=True, blank=True, null=True, verbose_name='项目编号')
    name = models.CharField(max_length=200, verbose_name='项目名称')
    alias = models.CharField(max_length=200, blank=True, verbose_name='项目别名')
    description = models.TextField(blank=True, verbose_name='项目描述')
    
    # 服务信息
    service_type = models.ForeignKey(ServiceType, on_delete=models.SET_NULL, null=True, blank=True, related_name='projects', verbose_name='服务类型')
    business_type = models.ForeignKey('BusinessType', on_delete=models.SET_NULL, null=True, blank=True, related_name='projects', verbose_name='项目业态', db_column='business_type')
    design_stage = models.ForeignKey('DesignStage', on_delete=models.SET_NULL, null=True, blank=True, related_name='projects', verbose_name='图纸阶段', db_column='design_stage')
    service_professions = models.ManyToManyField('ServiceProfession', blank=True, related_name='projects', verbose_name='服务专业')
    
    # 委托单位（甲方）信息
    client = models.ForeignKey('customer_management.Client', on_delete=models.PROTECT, null=True, blank=True, verbose_name='客户')
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
    
    # 我方单位信息
    our_company_name = models.CharField(max_length=200, blank=True, verbose_name='我方单位名称')
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
        db_table = 'production_management_project'
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
            if self.business_type:
                business_type_code = self.business_type.code if hasattr(self.business_type, 'code') else ''
                if business_type_code == 'residential':
                    business_type_coef = Decimal('1.0')
                elif business_type_code == 'complex':
                    business_type_coef = Decimal('1.3')
                elif business_type_code == 'industrial':
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
            if self.business_type:
                business_type_code = self.business_type.code if hasattr(self.business_type, 'code') else ''
                if business_type_code == 'residential':
                    business_type_coef = Decimal('1.0')
                elif business_type_code == 'complex':
                    business_type_coef = Decimal('1.3')
                elif business_type_code == 'industrial':
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
        # 项目编号在审批通过时自动生成（通过信号处理器）
        # 这里不再自动生成，避免在立项创建时就生成编号
        # 如果需要在其他地方手动生成编号，可以调用 generate_project_number() 方法
        super().save(*args, **kwargs)
    
    def generate_project_number(self):
        """生成项目编号"""
        if self.project_number:
            return self.project_number
        
        import datetime
        from django.db.models import Max
        current_year = datetime.datetime.now().year

        # 获取当前年份的最大序列号
        max_number = Project.objects.filter(
            project_number__startswith=f'VIH-{current_year}-'
        ).exclude(id=self.id).aggregate(max_num=Max('project_number'))['max_num']

        if max_number:
            # 提取序列号并加1
            try:
                seq = int(max_number.split('-')[-1]) + 1
            except (ValueError, IndexError):
                seq = 1
        else:
            seq = 1

        self.project_number = f"VIH-{current_year}-{seq:03d}"
        return self.project_number

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
        db_table = 'production_management_flow_log'
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
        db_table = 'production_management_team'
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
        db_table = 'production_management_team_log'
        verbose_name = '项目团队变更日志'
        verbose_name_plural = verbose_name
        ordering = ['-timestamp']


class ProjectTeamNotification(models.Model):
    """项目团队通知"""
    CATEGORY_CHOICES = [
        ('team_change', '团队变更'),
        ('quality_alert', '质量提醒'),
        ('approval', '审批通知'),
    ]

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='team_notifications', null=True, blank=True, verbose_name='项目', help_text='关联项目（可选，用于非项目相关通知时可为空）')
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
        db_table = 'production_management_team_notification'
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
        db_table = 'production_management_task'
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
    opinion_id = models.IntegerField(null=True, blank=True, verbose_name='关联意见ID', help_text='已删除生产质量模块，此字段保留用于历史数据')
    issue_title = models.CharField(max_length=200, verbose_name='事项 / 问题')
    status = models.CharField(max_length=20, choices=REPLY_STATUS_CHOICES, default='agree', verbose_name='回复结果')
    response_detail = models.TextField(blank=True, verbose_name='回复说明')
    submitted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='design_replies', verbose_name='提交人')
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    updated_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'production_management_design_reply'
        verbose_name = '设计方回复'
        verbose_name_plural = verbose_name
        ordering = ['-created_time']
        indexes = [
            models.Index(fields=['project', 'opinion_id']),
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
        db_table = 'production_management_meeting_record'
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
    opinion_id = models.IntegerField(null=True, blank=True, verbose_name='关联意见ID', help_text='已删除生产质量模块，此字段保留用于历史数据')
    decision = models.CharField(max_length=20, choices=DECISION_CHOICES, default='pending', verbose_name='会议结论')
    client_comment = models.TextField(blank=True, verbose_name='甲方意见')
    design_comment = models.TextField(blank=True, verbose_name='设计方意见')
    consultant_comment = models.TextField(blank=True, verbose_name='我方意见')
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')

    class Meta:
        db_table = 'production_management_meeting_decision'
        verbose_name = '三方会议结论'
        verbose_name_plural = verbose_name
        unique_together = ('meeting', 'opinion_id')
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
        db_table = 'production_management_milestone'
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
        db_table = 'production_management_drawing_submission'
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
        db_table = 'production_management_drawing_file'
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
        db_table = 'production_management_drawing_review'
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
        db_table = 'production_management_start_notice'
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
        db_table = 'production_management_document'
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
        db_table = 'production_management_archive'
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


class BusinessContract(models.Model):
    """商务合同信息"""
    CONTRACT_TYPE_CHOICES = [
        ('strategic', '战略合同'),
        ('framework', '框架合同'),
        ('project', '项目合同'),
        ('intent', '意向合同'),
        ('supplement', '补充协议'),
        ('change', '变更协议'),
        ('termination', '终止协议'),
        ('other', '其他'),
    ]
    
    CONTRACT_STATUS_CHOICES = [
        # 创建合同流程
        ('draft', '合同草稿'),  # 第一步：合同草稿
        ('dispute', '合同争议'),  # 第二步：合同争议
        ('finalized', '合同定稿'),  # 第三步：合同定稿
        # 合同签署流程
        ('party_b_signed', '我方签章'),  # 第一步：我方签章
        ('signed', '对方签章'),  # 第二步：对方签章（双方都已签章）
        # 合同执行流程
        ('effective', '已生效'),
        ('executing', '执行中'),
        ('completed', '已完成'),
        ('terminated', '已终止'),
        ('cancelled', '已取消'),
    ]
    
    # 关联信息
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='contracts', null=True, blank=True, verbose_name='关联项目')
    # TODO: Client模型需要迁移或处理，暂时保留对customer_management.Client的引用
    client = models.ForeignKey('customer_management.Client', on_delete=models.PROTECT, related_name='production_contracts', null=True, blank=True, verbose_name='客户')
    opportunity = models.ForeignKey('customer_management.BusinessOpportunity', on_delete=models.SET_NULL, null=True, blank=True, related_name='contracts', verbose_name='关联商机')
    parent_contract = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='sub_contracts', verbose_name='主合同', help_text='用于补充协议、变更协议关联主合同')
    
    # 基本信息
    contract_number = models.CharField(max_length=100, unique=True, blank=True, null=True, verbose_name='合同编号', help_text='唯一标识，留空将自动生成（格式：VIH-CON-YYYY-NNNN）')
    project_number = models.CharField(max_length=50, unique=True, blank=True, null=True, verbose_name='项目编号', help_text='自动生成：YYYYMMDD-0000，可手动修改。项目编号须保持唯一性')
    contract_name = models.CharField(max_length=200, blank=True, verbose_name='合同名称', help_text='如未填写，将使用合同编号')
    contract_type = models.CharField(max_length=20, choices=CONTRACT_TYPE_CHOICES, default='project', verbose_name='合同类型')
    status = models.CharField(max_length=20, choices=CONTRACT_STATUS_CHOICES, default='draft', verbose_name='合同状态')
    
    # 金额信息
    contract_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, verbose_name='合同金额（含税）')
    contract_amount_tax = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, verbose_name='合同税额')
    contract_amount_excl_tax = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, verbose_name='合同金额（不含税）')
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=6.00, verbose_name='税率(%)', help_text='默认6%，可调整')
    settlement_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='已结算金额')
    payment_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='已回款金额')
    unpaid_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, verbose_name='未回款金额', help_text='自动计算：合同金额-已回款金额')
    
    # 时间信息
    contract_date = models.DateField(null=True, blank=True, verbose_name='合同签订日期')
    effective_date = models.DateField(null=True, blank=True, verbose_name='合同生效日期')
    start_date = models.DateField(null=True, blank=True, verbose_name='合同开始日期')
    end_date = models.DateField(null=True, blank=True, verbose_name='合同结束日期')
    contract_period = models.IntegerField(null=True, blank=True, verbose_name='合同期限（天）', help_text='自动计算：结束日期-开始日期')
    
    party_a_name = models.CharField(max_length=200, blank=True, verbose_name='甲方名称')
    party_a_contact = models.CharField(max_length=100, blank=True, verbose_name='甲方联系人')
    party_b_name = models.CharField(max_length=200, blank=True, verbose_name='乙方名称', default='四川维海科技有限公司')
    party_b_contact = models.CharField(max_length=100, blank=True, verbose_name='乙方联系人')
    signed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='signed_production_contracts', verbose_name='合同签订人')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_production_contracts', verbose_name='合同审批人')
    
    # 管理信息
    department = models.ForeignKey('system_management.Department', on_delete=models.SET_NULL, null=True, blank=True, related_name='contracts', verbose_name='部门', help_text='默认填写人的部门')
    business_manager = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='managed_contracts', verbose_name='商务经理', help_text='默认为填写人')
    
    # 项目信息
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
        verbose_name='结构形式',
        help_text='项目的结构形式，用于合同管理和维护'
    )
    
    # 设计单位分类
    DESIGN_UNIT_CATEGORY_CHOICES = [
        ('class_1', '一类设计院'),
        ('class_2', '二类设计院'),
        ('class_3', '三类设计院'),
        ('class_4', '四类设计院'),
    ]
    design_unit_category = models.CharField(
        max_length=20,
        choices=DESIGN_UNIT_CATEGORY_CHOICES,
        blank=True,
        null=True,
        verbose_name='设计单位分类',
        help_text='设计单位的分类等级，用于合同管理和维护'
    )
    
    # 综合调整系数相关字段
    SERVICE_TYPE_CHOICES = [
        ('result_optimization', '结果优化'),
        ('process_optimization', '过程优化'),
    ]
    service_type = models.CharField(
        max_length=30,
        choices=SERVICE_TYPE_CHOICES,
        blank=True,
        null=True,
        verbose_name='服务类型',
        help_text='服务类型调整（T1）：结果优化：1.0，过程优化：1.5'
    )
    
    PROJECT_TYPE_CHOICES = [
        ('residential', '住宅'),
        ('complex', '综合体'),
        ('industrial', '工业厂房'),
        ('office', '写字楼'),
        ('commercial', '商业'),
        ('school', '学校'),
        ('hospital', '医院'),
        ('municipal', '市政'),
        ('other', '其他'),
    ]
    project_type = models.CharField(
        max_length=30,
        choices=PROJECT_TYPE_CHOICES,
        blank=True,
        null=True,
        verbose_name='项目业态',
        help_text='项目业态调整（T2）：住宅：1.0，综合体：1.2，工业厂房：1.10，写字楼=1.15，商业=1.3，学校=1.05，医院=1.25，市政=1.4，其他=1.0'
    )
    
    # 服务专业（多选，使用JSONField存储）
    service_professions = models.JSONField(
        default=list,
        blank=True,
        verbose_name='服务专业',
        help_text='服务专业调整（T3）：结构：0.32；构造：0.48，电气：0.14，给排水：0.06，其他专业每增加一个，调整系数增加0.1，但总系数不超过1.5'
    )
    
    DRAWING_STAGE_CHOICES = [
        ('construction_unaudited', '施工图（未审图）'),
        ('construction_audited', '施工图（已审图）'),
        ('preliminary_scheme', '初步方案'),
        ('detailed_scheme', '详细方案'),
        ('preliminary_design', '初步设计'),
        ('extended_preliminary', '扩初设计'),
        ('construction_stage', '施工阶段'),
        ('special_design', '专项设计'),
    ]
    drawing_stage = models.CharField(
        max_length=30,
        choices=DRAWING_STAGE_CHOICES,
        blank=True,
        null=True,
        verbose_name='图纸阶段',
        help_text='图纸阶段调整（T5）：施工图（未审图）：1.0，施工图（已审图）：0.6，初步方案：1.5，详细方案：1.4，初步设计：1.3，扩初设计：1.2，施工阶段：0.5，专项设计：1.0'
    )
    
    # 地下面积和总建筑面积（用于计算T6）
    basement_area = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='地下室面积（㎡）',
        help_text='用于计算地下面积占比调整（T6）'
    )
    total_building_area = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='总建筑面积（㎡）',
        help_text='用于计算地下面积占比调整（T6）'
    )
    
    # 综合调整系数（自动计算）
    comprehensive_adjustment_coefficient = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='综合调整系数',
        help_text='自动计算：T1*T2*T3*T4*T5*T6*T7，最大不超过2.0'
    )
    
    # 其他信息
    description = models.TextField(blank=True, verbose_name='合同描述')
    notes = models.TextField(blank=True, verbose_name='备注')
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    
    # 审计字段
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='created_production_contracts', null=True, blank=True, verbose_name='创建人')
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    updated_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'business_contract'  # 保持原表名，避免数据迁移问题
        verbose_name = '商务合同'
        verbose_name_plural = verbose_name
        ordering = ['-created_time']
        indexes = [
            models.Index(fields=['contract_number']),
            models.Index(fields=['status', 'contract_type']),
            models.Index(fields=['contract_date']),
        ]

    def __str__(self):
        project_num = self.project_number or '未生成编号'
        contract_name = self.contract_name or '未命名合同'
        return f"{project_num} - {contract_name}"
    
    def calculate_comprehensive_adjustment_coefficient(self):
        """计算综合调整系数：T1*T2*T3*T4*T5*T6*T7，最大不超过2.0"""
        from decimal import Decimal
        
        # T1: 服务类型调整
        t1 = Decimal('1.0')
        if self.service_type == 'result_optimization':
            t1 = Decimal('1.0')
        elif self.service_type == 'process_optimization':
            t1 = Decimal('1.5')
        
        # T2: 项目业态调整
        t2 = Decimal('1.0')
        project_type_map = {
            'residential': Decimal('1.0'),
            'complex': Decimal('1.2'),
            'industrial': Decimal('1.10'),
            'office': Decimal('1.15'),
            'commercial': Decimal('1.3'),
            'school': Decimal('1.05'),
            'hospital': Decimal('1.25'),
            'municipal': Decimal('1.4'),
            'other': Decimal('1.0'),
        }
        if self.project_type:
            t2 = project_type_map.get(self.project_type, Decimal('1.0'))
        
        # T3: 服务专业调整
        t3 = Decimal('0.0')
        profession_coefficients = {
            'structure': Decimal('0.32'),  # 结构
            'construction': Decimal('0.48'),  # 构造
            'electrical': Decimal('0.14'),  # 电气
            'plumbing': Decimal('0.06'),  # 给排水
        }
        
        if self.service_professions:
            # 计算已知专业的系数
            for profession in self.service_professions:
                if profession in profession_coefficients:
                    t3 += profession_coefficients[profession]
                elif profession.startswith('other_'):
                    # 其他专业每增加一个，调整系数增加0.1
                    t3 += Decimal('0.1')
                else:
                    # 未知专业也按其他专业处理
                    t3 += Decimal('0.1')
        
        # 总系数不超过1.5
        if t3 > Decimal('1.5'):
            t3 = Decimal('1.5')
        
        # 如果没有选择任何专业，默认值为1.0（不影响计算）
        if t3 == Decimal('0.0'):
            t3 = Decimal('1.0')
        
        # T4: 设计质量调整（设计单位分类）
        t4 = Decimal('1.0')
        design_category_map = {
            'class_1': Decimal('1.0'),
            'class_2': Decimal('1.1'),
            'class_3': Decimal('1.2'),
            'class_4': Decimal('1.3'),
        }
        if self.design_unit_category:
            t4 = design_category_map.get(self.design_unit_category, Decimal('1.0'))
        
        # T5: 图纸阶段调整
        t5 = Decimal('1.0')
        drawing_stage_map = {
            'construction_unaudited': Decimal('1.0'),  # 施工图（未审图）
            'construction_audited': Decimal('0.6'),  # 施工图（已审图）
            'preliminary_scheme': Decimal('1.5'),  # 初步方案
            'detailed_scheme': Decimal('1.4'),  # 详细方案
            'preliminary_design': Decimal('1.3'),  # 初步设计
            'extended_preliminary': Decimal('1.2'),  # 扩初设计
            'construction_stage': Decimal('0.5'),  # 施工阶段
            'special_design': Decimal('1.0'),  # 专项设计
        }
        if self.drawing_stage:
            t5 = drawing_stage_map.get(self.drawing_stage, Decimal('1.0'))
        
        # T6: 地下面积占比调整
        t6 = Decimal('1.0')
        if self.basement_area and self.total_building_area and self.total_building_area > 0:
            ratio = self.basement_area / self.total_building_area
            if ratio > Decimal('0.20'):
                t6 = Decimal('1.2')
            else:
                t6 = Decimal('1.0')
        
        # T7: 结构类型调整
        t7 = Decimal('1.0')
        structure_type_map = {
            'shear_wall': Decimal('1.0'),  # 剪力墙结构
            'frame': Decimal('0.6'),  # 框架结构
            'steel': Decimal('1.2'),  # 钢结构
            'other': Decimal('0.9'),  # 其他
        }
        if self.structure_type:
            t7 = structure_type_map.get(self.structure_type, Decimal('1.0'))
        
        # 计算综合调整系数：T1*T2*T3*T4*T5*T6*T7
        coefficient = t1 * t2 * t3 * t4 * t5 * t6 * t7
        
        # 最大不超过2.0
        if coefficient > Decimal('2.0'):
            coefficient = Decimal('2.0')
        
        return coefficient
    
    def get_adjustment_coefficient_details(self):
        """获取综合调整系数计算明细"""
        from decimal import Decimal
        
        details = {
            'T1': {'name': '服务类型调整', 'value': Decimal('1.0'), 'description': ''},
            'T2': {'name': '项目业态调整', 'value': Decimal('1.0'), 'description': ''},
            'T3': {'name': '服务专业调整', 'value': Decimal('1.0'), 'description': ''},
            'T4': {'name': '设计质量调整', 'value': Decimal('1.0'), 'description': ''},
            'T5': {'name': '图纸阶段调整', 'value': Decimal('1.0'), 'description': ''},
            'T6': {'name': '地下面积占比调整', 'value': Decimal('1.0'), 'description': ''},
            'T7': {'name': '结构类型调整', 'value': Decimal('1.0'), 'description': ''},
        }
        
        # T1: 服务类型调整
        if self.service_type == 'result_optimization':
            details['T1']['value'] = Decimal('1.0')
            details['T1']['description'] = '结果优化'
        elif self.service_type == 'process_optimization':
            details['T1']['value'] = Decimal('1.5')
            details['T1']['description'] = '过程优化'
        else:
            details['T1']['description'] = '未设置'
        
        # T2: 项目业态调整
        project_type_map = {
            'residential': (Decimal('1.0'), '住宅'),
            'complex': (Decimal('1.2'), '综合体'),
            'industrial': (Decimal('1.10'), '工业厂房'),
            'office': (Decimal('1.15'), '写字楼'),
            'commercial': (Decimal('1.3'), '商业'),
            'school': (Decimal('1.05'), '学校'),
            'hospital': (Decimal('1.25'), '医院'),
            'municipal': (Decimal('1.4'), '市政'),
            'other': (Decimal('1.0'), '其他'),
        }
        if self.project_type:
            value, name = project_type_map.get(self.project_type, (Decimal('1.0'), '其他'))
            details['T2']['value'] = value
            details['T2']['description'] = name
        else:
            details['T2']['description'] = '未设置'
        
        # T3: 服务专业调整
        t3 = Decimal('0.0')
        profession_coefficients = {
            'structure': Decimal('0.32'),
            'construction': Decimal('0.48'),
            'electrical': Decimal('0.14'),
            'plumbing': Decimal('0.06'),
        }
        profession_names = {
            'structure': '结构',
            'construction': '构造',
            'electrical': '电气',
            'plumbing': '给排水',
        }
        selected_professions = []
        
        if self.service_professions:
            for profession in self.service_professions:
                if profession in profession_coefficients:
                    t3 += profession_coefficients[profession]
                    selected_professions.append(profession_names.get(profession, profession))
                elif profession.startswith('other_'):
                    t3 += Decimal('0.1')
                    selected_professions.append('其他专业')
                else:
                    t3 += Decimal('0.1')
                    selected_professions.append('其他专业')
        
        if t3 > Decimal('1.5'):
            t3 = Decimal('1.5')
        
        if t3 == Decimal('0.0'):
            t3 = Decimal('1.0')
            details['T3']['description'] = '未设置'
        else:
            details['T3']['description'] = ', '.join(selected_professions) if selected_professions else '未设置'
        
        details['T3']['value'] = t3
        
        # T4: 设计质量调整
        design_category_map = {
            'class_1': (Decimal('1.0'), '一类设计院'),
            'class_2': (Decimal('1.1'), '二类设计院'),
            'class_3': (Decimal('1.2'), '三类设计院'),
            'class_4': (Decimal('1.3'), '四类设计院'),
        }
        if self.design_unit_category:
            value, name = design_category_map.get(self.design_unit_category, (Decimal('1.0'), '未设置'))
            details['T4']['value'] = value
            details['T4']['description'] = name
        else:
            details['T4']['description'] = '未设置'
        
        # T5: 图纸阶段调整
        drawing_stage_map = {
            'construction_unaudited': (Decimal('1.0'), '施工图（未审图）'),
            'construction_audited': (Decimal('0.6'), '施工图（已审图）'),
            'preliminary_scheme': (Decimal('1.5'), '初步方案'),
            'detailed_scheme': (Decimal('1.4'), '详细方案'),
            'preliminary_design': (Decimal('1.3'), '初步设计'),
            'extended_preliminary': (Decimal('1.2'), '扩初设计'),
            'construction_stage': (Decimal('0.5'), '施工阶段'),
            'special_design': (Decimal('1.0'), '专项设计'),
        }
        if self.drawing_stage:
            value, name = drawing_stage_map.get(self.drawing_stage, (Decimal('1.0'), '未设置'))
            details['T5']['value'] = value
            details['T5']['description'] = name
        else:
            details['T5']['description'] = '未设置'
        
        # T6: 地下面积占比调整
        if self.basement_area and self.total_building_area and self.total_building_area > 0:
            ratio = self.basement_area / self.total_building_area
            if ratio > Decimal('0.20'):
                details['T6']['value'] = Decimal('1.2')
                details['T6']['description'] = f'占比 {ratio:.2%}（>20%）'
            else:
                details['T6']['value'] = Decimal('1.0')
                details['T6']['description'] = f'占比 {ratio:.2%}（≤20%）'
        else:
            details['T6']['description'] = '未设置'
        
        # T7: 结构类型调整
        structure_type_map = {
            'shear_wall': (Decimal('1.0'), '剪力墙结构'),
            'frame': (Decimal('0.6'), '框架结构'),
            'steel': (Decimal('1.2'), '钢结构'),
            'other': (Decimal('0.9'), '其他'),
        }
        if self.structure_type:
            value, name = structure_type_map.get(self.structure_type, (Decimal('1.0'), '未设置'))
            details['T7']['value'] = value
            details['T7']['description'] = name
        else:
            details['T7']['description'] = '未设置'
        
        # 计算最终系数
        coefficient = details['T1']['value'] * details['T2']['value'] * details['T3']['value'] * \
                     details['T4']['value'] * details['T5']['value'] * details['T6']['value'] * \
                     details['T7']['value']
        
        if coefficient > Decimal('2.0'):
            coefficient = Decimal('2.0')
        
        details['final'] = {
            'name': '综合调整系数',
            'value': coefficient,
            'formula': 'T1 × T2 × T3 × T4 × T5 × T6 × T7',
        }
        
        return details
    
    def save(self, *args, **kwargs):
        # 自动生成项目编号：HT-YYYY-NNNN
        # 如果关联的商机已有业务委托书，则继承其项目编号
        if not self.project_number:
            from django.db.models import Max
            from datetime import datetime
            from backend.apps.customer_management.models import AuthorizationLetter
            
            # 检查是否有关联的项目，通过项目查找关联的商机
            authorization_letter = None
            if self.project_id:
                # 通过项目查找关联的业务委托书
                authorization_letter = AuthorizationLetter.objects.filter(
                    project_id=self.project_id,
                    project_number__isnull=False
                ).exclude(project_number='').first()
            
            if authorization_letter and authorization_letter.project_number:
                # 继承业务委托书的项目编号
                self.project_number = authorization_letter.project_number
            else:
                # 如果没有业务委托书，自动生成项目编号
                current_year = datetime.now().strftime('%Y')
                year_prefix = f'HT-{current_year}-'
                
                # 查找当年最大项目编号（从业务委托书和合同中查找）
                max_letter = AuthorizationLetter.objects.filter(
                    project_number__startswith=year_prefix
                ).aggregate(max_num=Max('project_number'))['max_num']
                
                max_contract = BusinessContract.objects.filter(
                    project_number__startswith=year_prefix
                ).exclude(id=self.id if self.id else None).aggregate(max_num=Max('project_number'))['max_num']
                
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
        
        # 自动计算不含税金额和税额
        if self.contract_amount:
            tax_rate_decimal = (self.tax_rate or 0) / 100
            if tax_rate_decimal > 0:
                self.contract_amount_excl_tax = self.contract_amount / (1 + tax_rate_decimal)
                self.contract_amount_tax = self.contract_amount - self.contract_amount_excl_tax
            else:
                self.contract_amount_excl_tax = self.contract_amount
                self.contract_amount_tax = 0
        
        # 自动计算未回款金额
        if self.contract_amount:
            self.unpaid_amount = (self.contract_amount or 0) - (self.payment_amount or 0)
        
        # 自动计算合同期限
        if self.start_date and self.end_date:
            from datetime import timedelta
            self.contract_period = (self.end_date - self.start_date).days
        
        # 自动计算综合调整系数
        try:
            self.comprehensive_adjustment_coefficient = self.calculate_comprehensive_adjustment_coefficient()
        except Exception:
            # 如果计算失败，设置为None
            self.comprehensive_adjustment_coefficient = None
        
        # 记录状态变更（暂时注释，因为ContractStatusLog仍在customer_success）
        # TODO: 如果需要状态日志功能，需要迁移ContractStatusLog或移除此功能
        # if self.pk:
        #     try:
        #         old_instance = BusinessContract.objects.get(pk=self.pk)
        #         if old_instance.status != self.status:
        #             from django.apps import apps
        #             ContractStatusLog = apps.get_model('customer_success', 'ContractStatusLog')
        #             ContractStatusLog.objects.create(...)
        #     except Exception:
        #         pass
        
        super().save(*args, **kwargs)
    
    @classmethod
    def get_valid_transitions(cls, current_status):
        """获取当前状态可以流转到的状态列表
        
        创建合同流程：
        1. 合同草稿 (draft) -> 合同争议 (dispute)
        2. 合同争议 (dispute) -> 合同定稿 (finalized)
        
        合同签署流程：
        3. 合同定稿 (finalized) -> 我方签章 (party_b_signed)
        4. 我方签章 (party_b_signed) -> 对方签章 (signed)
        
        合同执行流程：
        5. 对方签章 (signed) -> 已生效 (effective)
        6. 已生效 (effective) -> 执行中 (executing)
        7. 执行中 (executing) -> 已完成 (completed) / 已终止 (terminated)
        """
        transitions = {
            # 创建合同流程
            'draft': ['dispute', 'cancelled'],  # 合同草稿 -> 合同争议
            'dispute': ['finalized', 'draft', 'cancelled'],  # 合同争议 -> 合同定稿（可退回草稿）
            'finalized': ['party_b_signed', 'dispute', 'cancelled'],  # 合同定稿 -> 我方签章（可退回争议）
            # 合同签署流程
            'party_b_signed': ['signed', 'finalized', 'cancelled'],  # 我方签章 -> 对方签章（可退回定稿）
            'signed': ['effective', 'cancelled'],  # 对方签章 -> 已生效
            # 合同执行流程
            'effective': ['executing', 'terminated'],
            'executing': ['completed', 'terminated', 'cancelled'],
            'completed': [],
            'terminated': [],
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
            raise ValueError(f"无法从 {self.get_status_display()} 流转到 {dict(self.CONTRACT_STATUS_CHOICES).get(target_status, target_status)}")
        
        old_status = self.status
        self.status = target_status
        
        # 特殊处理：如果是签署操作，设置签署人和签署日期
        if target_status == 'signed' and not self.contract_date:
                # 对方签章完成时设置合同签订日期
                from django.utils import timezone
                self.contract_date = timezone.now().date()
        
        self.save()
        
        # 记录状态流转日志
        try:
            from django.apps import apps
            ContractStatusLog = apps.get_model('customer_management', 'ContractStatusLog')
            ContractStatusLog.objects.create(
                contract=self,
                from_status=old_status,
                to_status=target_status,
                actor=actor,
                comment=comment
            )
        except Exception:
            # 如果记录日志失败，不影响状态流转
            pass
        
        return True


class ComprehensiveAdjustmentCoefficient(BusinessContract):
    """综合调整系数管理（代理模型）"""
    class Meta:
        proxy = True
        verbose_name = '综合调整系数'
        verbose_name_plural = '综合调整系数'
        app_label = 'production_management'


class BusinessPaymentPlan(models.Model):
    """商务合同回款计划"""
    STATUS_CHOICES = [
        ('pending', '待回款'),
        ('partial', '部分回款'),
        ('completed', '已完成'),
        ('overdue', '已逾期'),
        ('cancelled', '已取消'),
    ]

    contract = models.ForeignKey(BusinessContract, on_delete=models.CASCADE, related_name='payment_plans', verbose_name='合同')
    phase_name = models.CharField(max_length=100, verbose_name='回款阶段')
    phase_description = models.TextField(blank=True, verbose_name='阶段描述')
    planned_amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='计划金额')
    planned_date = models.DateField(verbose_name='计划日期')
    actual_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, verbose_name='实际金额')
    actual_date = models.DateField(null=True, blank=True, verbose_name='实际日期')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='状态')
    trigger_condition = models.CharField(max_length=100, blank=True, verbose_name='触发条件')
    condition_detail = models.CharField(max_length=200, blank=True, verbose_name='付款条件详情')
    notes = models.TextField(blank=True, verbose_name='备注')
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    updated_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'business_payment_plan'  # 保持原表名
        verbose_name = '商务回款计划'
        verbose_name_plural = verbose_name
        ordering = ['planned_date']

    def __str__(self):
        return f"{self.contract_id} - {self.phase_name}"


# ========== 服务信息功能已删除（作为备份保留）==========
# 以下ContractServiceContent模型定义已注释，数据库表保留
# 
# class ContractServiceContent(models.Model):
#     """合同服务内容"""
#     contract = models.ForeignKey(BusinessContract, on_delete=models.CASCADE, related_name='service_contents', verbose_name='合同')
#     service_type = models.ForeignKey(ServiceType, on_delete=models.SET_NULL, null=True, blank=True, related_name='contract_service_contents', verbose_name='服务类型')
#     design_stage = models.ForeignKey(DesignStage, on_delete=models.SET_NULL, null=True, blank=True, related_name='contract_service_contents', verbose_name='图纸阶段')
#     building_area = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, verbose_name='建筑面积（㎡）')
#     business_type = models.ForeignKey(BusinessType, on_delete=models.SET_NULL, null=True, blank=True, related_name='contract_service_contents', verbose_name='项目业态')
#     service_professions = models.ManyToManyField(ServiceProfession, blank=True, related_name='contract_service_contents', verbose_name='服务专业')
#     description = models.TextField(blank=True, verbose_name='服务内容描述')
#     order = models.IntegerField(default=0, verbose_name='排序', help_text='数字越小越靠前')
#     is_active = models.BooleanField(default=True, verbose_name='是否启用')
#     created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
#     updated_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')
#     
#     class Meta:
#         db_table = 'contract_service_content'
#         verbose_name = '合同服务内容'
#         verbose_name_plural = verbose_name
#         ordering = ['order', 'id']
#         indexes = [
#             models.Index(fields=['contract', 'is_active']),
#         ]
#     
#     def __str__(self):
#         service_type_name = self.service_type.name if self.service_type else '未设置'
#         return f"{self.contract.contract_number or self.contract.id} - {service_type_name}"
# ========== 服务信息功能删除结束 ==========


class ContractParty(models.Model):
    """合同签约主体"""
    PARTY_TYPE_CHOICES = [
        ('party_a', '甲方'),
        ('party_b', '乙方'),
        ('party_c', '丙方'),
        ('other', '其他'),
    ]
    
    contract = models.ForeignKey(BusinessContract, on_delete=models.CASCADE, related_name='parties', verbose_name='合同')
    party_type = models.CharField(max_length=20, choices=PARTY_TYPE_CHOICES, default='party_a', verbose_name='单位类型')
    party_name = models.CharField(max_length=200, verbose_name='单位名称')
    credit_code = models.CharField(max_length=50, blank=True, verbose_name='统一社会信用代码')
    legal_representative = models.CharField(max_length=100, blank=True, verbose_name='法定代表人')
    project_manager = models.CharField(max_length=100, blank=True, verbose_name='项目负责人')
    party_contact = models.CharField(max_length=100, blank=True, verbose_name='联系人')
    contact_phone = models.CharField(max_length=20, blank=True, verbose_name='联系电话')
    contact_email = models.EmailField(blank=True, verbose_name='联系邮箱')
    address = models.CharField(max_length=500, blank=True, verbose_name='办公地址')
    order = models.IntegerField(default=0, verbose_name='排序', help_text='数字越小越靠前')
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    created_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    updated_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        db_table = 'contract_party'
        verbose_name = '合同签约主体'
        verbose_name_plural = verbose_name
        ordering = ['order', 'id']
        indexes = [
            models.Index(fields=['contract', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.contract.contract_number or self.contract.id} - {self.get_party_type_display()} - {self.party_name}"


class ResultFileType(models.Model):
    """成果文件类型明细"""
    
    SERVICE_CATEGORY_CHOICES = [
        ('result_optimization', '结果优化'),
        ('process_optimization', '过程优化'),
        ('full_process_consulting', '全过程咨询'),
    ]
    
    service_category = models.CharField(
        max_length=50,
        choices=SERVICE_CATEGORY_CHOICES,
        verbose_name='服务类别',
        db_index=True
    )
    
    code = models.CharField(
        max_length=100,
        verbose_name='文件类型代码',
        help_text='唯一标识，如：pre_optimization_disc_application（同一服务类别内唯一）'
    )
    
    name = models.CharField(
        max_length=200,
        verbose_name='文件类型名称',
        help_text='显示名称，如：优化前刻盘申请'
    )
    
    order = models.IntegerField(
        default=0,
        verbose_name='排序',
        help_text='数字越小越靠前'
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name='是否启用',
        help_text='禁用后不会在前端显示'
    )
    
    description = models.TextField(
        blank=True,
        verbose_name='描述',
        help_text='文件类型的详细说明'
    )
    
    created_time = models.DateTimeField(
        default=timezone.now,
        verbose_name='创建时间'
    )
    
    updated_time = models.DateTimeField(
        auto_now=True,
        verbose_name='更新时间'
    )
    
    class Meta:
        db_table = 'production_management_result_file_type'
        verbose_name = '成果文件类型'
        verbose_name_plural = '成果文件类型'
        ordering = ['service_category', 'order', 'id']
        indexes = [
            models.Index(fields=['service_category', 'is_active']),
            models.Index(fields=['service_category', 'order']),
        ]
        unique_together = [['service_category', 'code']]
    
    def __str__(self):
        return f"{self.get_service_category_display()} - {self.name}"


