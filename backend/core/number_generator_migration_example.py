"""
编号生成服务迁移示例
展示如何将现有代码迁移到使用统一编号生成服务
"""

# ==================== 示例1：交付单号生成 ====================

# 原代码（在 models.py 中）
"""
def generate_delivery_number(self):
    \"\"\"生成交付单号：VIH-JF-{YYYYMMDD}-{序列号}\"\"\"
    from django.db import transaction
    from django.db.models import Max
    
    prefix = 'VIH-JF'
    date_str = timezone.now().strftime('%Y%m%d')
    pattern = f"{prefix}-{date_str}-"
    
    with transaction.atomic():
        max_number = DeliveryRecord.objects.filter(
            delivery_number__startswith=pattern
        ).aggregate(max_num=Max('delivery_number'))['max_num']
        
        if max_number:
            try:
                seq = int(max_number.split('-')[-1]) + 1
            except (ValueError, IndexError):
                seq = 1
        else:
            seq = 1
        
        return f"{pattern}{seq:04d}"
"""

# 新代码（使用统一编号生成服务）
from backend.core.number_generator import NumberGeneratorService

def generate_delivery_number_new(self):
    """生成交付单号：VIH-JF-{YYYYMMDD}-{序列号}"""
    return NumberGeneratorService.generate(
        model_class=DeliveryRecord,
        field_name='delivery_number',
        prefix='VIH-JF',
        date_format='%Y%m%d',
        seq_strategy='daily',
        seq_length=4
    )

# 或者使用便捷方法
from backend.core.number_generator import generate_delivery_number

def save(self, *args, **kwargs):
    if not self.delivery_number:
        self.delivery_number = generate_delivery_number(DeliveryRecord)
    super().save(*args, **kwargs)


# ==================== 示例2：收文编号生成 ====================

# 原代码（在 views_pages.py 中）
"""
today = timezone.now().date()
year = today.strftime('%Y')
count = IncomingDocument.objects.filter(
    document_number__startswith=f'SW{year}'
).count() + 1
document_number = f'SW{year}{count:04d}'

while IncomingDocument.objects.filter(document_number=document_number).exists():
    count += 1
    document_number = f'SW{year}{count:04d}'
"""

# 新代码
from backend.core.number_generator import NumberGeneratorService

document_number = NumberGeneratorService.generate(
    model_class=IncomingDocument,
    field_name='document_number',
    prefix='SW',
    date_format='%Y',
    seq_strategy='yearly',
    seq_length=4
)

# 或者使用便捷方法
from backend.core.number_generator import generate_incoming_document_number

document_number = generate_incoming_document_number(IncomingDocument)


# ==================== 示例3：结算单号生成 ====================

# 原代码（在 models.py 中）
"""
if not self.settlement_number and self.project_id:
    project_number = self.project.project_number
    max_settlement = ProjectSettlement.objects.filter(
        settlement_number__startswith=f'VIH-JS-{project_number}-'
    ).aggregate(max_num=Max('settlement_number'))['max_num']
    
    if max_settlement:
        try:
            seq_str = max_settlement.split('-')[-1]
            seq = int(seq_str) + 1
        except (ValueError, IndexError):
            seq = 1
    else:
        seq = 1
    self.settlement_number = f'VIH-JS-{project_number}-{seq:04d}'
"""

# 新代码
from backend.core.number_generator import NumberGeneratorService

if not self.settlement_number and self.project_id:
    self.settlement_number = NumberGeneratorService.generate(
        model_class=ProjectSettlement,
        field_name='settlement_number',
        prefix='VIH-JS',
        related_field='project__project_number',
        related_value=self.project.project_number,
        seq_strategy='related',
        seq_length=4
    )

# 或者使用便捷方法
from backend.core.number_generator import generate_settlement_number

if not self.settlement_number and self.project_id:
    self.settlement_number = generate_settlement_number(
        ProjectSettlement,
        self.project.project_number
    )


# ==================== 示例4：审批实例编号生成 ====================

# 原代码（在 services.py 中）
"""
@staticmethod
def generate_instance_number(workflow: WorkflowTemplate) -> str:
    \"\"\"生成审批实例编号\"\"\"
    from django.db.models import Count
    count = ApprovalInstance.objects.filter(workflow=workflow).count()
    return f"{workflow.code}-{timezone.now().strftime('%Y%m%d')}-{count + 1:04d}"
"""

# 新代码
from backend.core.number_generator import NumberGeneratorService

@staticmethod
def generate_instance_number(workflow: WorkflowTemplate) -> str:
    """生成审批实例编号"""
    return NumberGeneratorService.generate(
        model_class=ApprovalInstance,
        field_name='instance_number',
        prefix=workflow.code,
        date_format='%Y%m%d',
        seq_strategy='daily',
        seq_length=4,
        filter_conditions={'workflow': workflow}  # 添加额外过滤条件
    )

# 或者使用便捷方法
from backend.core.number_generator import generate_approval_instance_number

instance_number = generate_approval_instance_number(
    ApprovalInstance,
    workflow.code
)


# ==================== 示例5：客户编号生成 ====================

# 原代码（在 models.py 中，较复杂）
"""
def generate_customer_number(self):
    \"\"\"生成客户编号：KH-YYYYMMDD-NNNN（NNNN全局累计递增）\"\"\"
    from datetime import date
    from django.db import transaction
    import re
    
    today = date.today()
    date_prefix = today.strftime('%Y%m%d')
    prefix = f'KH-{date_prefix}-'
    
    with transaction.atomic():
        all_numbers = Client.objects.filter(
            customer_number__isnull=False
        ).exclude(customer_number='').filter(
            customer_number__startswith='KH-'
        ).select_for_update().values_list('customer_number', flat=True)
        
        max_num = 0
        for number in all_numbers:
            if number and '-' in number:
                try:
                    num_part = number.split('-')[-1]
                    if re.match(r'^\d{1,4}$', num_part):
                        num_value = int(num_part)
                        if num_value > max_num:
                            max_num = num_value
                except (ValueError, IndexError):
                    continue
        
        next_num = max_num + 1
        if next_num > 9999:
            raise ValueError(f"客户编号已达到最大值9999")
        
        number_suffix = str(next_num).zfill(4)
        customer_number = f'{prefix}{number_suffix}'
        
        # 再次检查是否已存在
        attempt_count = 0
        while Client.objects.filter(customer_number=customer_number).exists() and attempt_count < 100:
            next_num += 1
            if next_num > 9999:
                raise ValueError(f"客户编号已达到最大值9999")
            number_suffix = str(next_num).zfill(4)
            customer_number = f'{prefix}{number_suffix}'
            attempt_count += 1
        
        return customer_number
"""

# 新代码（简化版）
from backend.core.number_generator import NumberGeneratorService

def generate_customer_number_new(self):
    """生成客户编号：KH-YYYYMMDD-NNNN（全局累计）"""
    return NumberGeneratorService.generate(
        model_class=Client,
        field_name='customer_number',
        prefix='KH',
        date_format='%Y%m%d',
        seq_strategy='global',  # 全局累计
        seq_length=4
    )


# ==================== 迁移步骤建议 ====================

"""
1. 备份现有数据
   - 确保数据库已备份
   - 记录现有编号生成逻辑

2. 逐步迁移
   - 先在一个模块中测试
   - 验证编号生成正确性
   - 确认无并发问题

3. 更新代码
   - 替换编号生成逻辑
   - 更新相关测试
   - 更新文档

4. 监控验证
   - 监控编号生成情况
   - 检查是否有异常
   - 收集用户反馈

5. 完善规则
   - 在NumberRule模型中记录规则
   - 配置管理界面（可选）
   - 持续优化
"""

