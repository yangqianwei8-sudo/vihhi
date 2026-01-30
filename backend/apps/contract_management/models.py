from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
import logging
from backend.apps.system_management.models import User

logger = logging.getLogger(__name__)

# ==================== 合同管理模块模型 =====================

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
    project = models.ForeignKey('production_management.Project', on_delete=models.CASCADE, related_name='contracts', null=True, blank=True, verbose_name='关联项目')
    client = models.ForeignKey('customer_management.Client', on_delete=models.PROTECT, related_name='contracts', null=True, blank=True, verbose_name='客户')
    opportunity = models.ForeignKey('opportunity_management.BusinessOpportunity', on_delete=models.SET_NULL, null=True, blank=True, related_name='contracts', verbose_name='关联商机')
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
    signed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='signed_contracts', verbose_name='合同签订人')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_contracts', verbose_name='合同审批人')
    
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
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='created_contracts', null=True, blank=True, verbose_name='创建人')
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
        
        # 记录状态变更（在状态流转时通过 transition_to 方法处理）
        # 这里不处理状态变更日志，避免在 save 中重复记录
        
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
        app_label = 'contract_management'


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
        db_table = 'business_payment_plan'  # 保持原表名，避免数据迁移问题
        verbose_name = '商务回款计划'
        verbose_name_plural = verbose_name
        ordering = ['planned_date']

    def __str__(self):
        return f"{self.contract_id} - {self.phase_name}"


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
        db_table = 'production_management_result_file_type'  # 保持原表名
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
