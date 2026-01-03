# 统一编号生成服务使用文档

## 概述

统一编号生成服务（`NumberGeneratorService`）提供了系统统一的编号生成功能，支持多种编号格式和序列号策略，确保编号的唯一性和并发安全。

## 功能特性

1. **多种编号格式支持**
   - 前缀 + 日期 + 序列号
   - 前缀 + 日期
   - 前缀 + 序列号
   - 前缀 + 关联对象编号 + 序列号
   - 自定义模板格式

2. **多种序列号策略**
   - `daily`: 按日期重置（每天从1开始）
   - `monthly`: 按月重置（每月从1开始）
   - `yearly`: 按年重置（每年从1开始）
   - `global`: 全局累计（永不重置）
   - `related`: 按关联对象分组累计

3. **并发安全**
   - 使用数据库事务和锁确保并发安全
   - 自动检测并处理编号冲突

4. **易于扩展**
   - 支持自定义模板
   - 支持灵活的过滤条件
   - 可配置的序列号长度

## 使用方法

### 基础用法

```python
from backend.core.number_generator import NumberGeneratorService
from backend.apps.delivery_customer.models import DeliveryRecord

# 生成交付单号：VIH-JF-20250101-0001
delivery_number = NumberGeneratorService.generate(
    model_class=DeliveryRecord,
    field_name='delivery_number',
    prefix='VIH-JF',
    date_format='%Y%m%d',
    seq_strategy='daily',
    seq_length=4
)
```

### 常用场景示例

#### 1. 交付单号（按日重置）

```python
# 格式：VIH-JF-20250101-0001
delivery_number = NumberGeneratorService.generate(
    model_class=DeliveryRecord,
    field_name='delivery_number',
    prefix='VIH-JF',
    date_format='%Y%m%d',
    seq_strategy='daily',
    seq_length=4
)
```

#### 2. 收文编号（按年重置）

```python
# 格式：SW20250001
from backend.apps.delivery_customer.models import IncomingDocument

document_number = NumberGeneratorService.generate(
    model_class=IncomingDocument,
    field_name='document_number',
    prefix='SW',
    date_format='%Y',
    seq_strategy='yearly',
    seq_length=4
)
```

#### 3. 发文编号（按年重置）

```python
# 格式：FW20250001
from backend.apps.delivery_customer.models import OutgoingDocument

document_number = NumberGeneratorService.generate(
    model_class=OutgoingDocument,
    field_name='document_number',
    prefix='FW',
    date_format='%Y',
    seq_strategy='yearly',
    seq_length=4
)
```

#### 4. 结算单号（按关联对象分组）

```python
# 格式：VIH-JS-项目编号-0001
from backend.apps.settlement_center.models import ProjectSettlement

settlement_number = NumberGeneratorService.generate(
    model_class=ProjectSettlement,
    field_name='settlement_number',
    prefix='VIH-JS',
    related_field='project__project_number',
    related_value=project.project_number,
    seq_strategy='related',
    seq_length=4
)
```

#### 5. 审批实例编号（按日重置）

```python
# 格式：{workflow_code}-20250101-0001
from backend.apps.workflow_engine.models import ApprovalInstance

instance_number = NumberGeneratorService.generate(
    model_class=ApprovalInstance,
    field_name='instance_number',
    prefix=workflow.code,
    date_format='%Y%m%d',
    seq_strategy='daily',
    seq_length=4
)
```

#### 6. 客户编号（全局累计）

```python
# 格式：KH-20250101-0001
from backend.apps.customer_management.models import Client

customer_number = NumberGeneratorService.generate(
    model_class=Client,
    field_name='customer_number',
    prefix='KH',
    date_format='%Y%m%d',
    seq_strategy='global',  # 全局累计
    seq_length=4
)
```

#### 7. 使用自定义模板

```python
# 格式：CUSTOM-2025-01-01-0001
custom_number = NumberGeneratorService.generate(
    model_class=YourModel,
    field_name='custom_number',
    prefix='CUSTOM',
    date_format='%Y-%m-%d',
    seq_strategy='daily',
    seq_length=4,
    template='{prefix}-{year}-{month}-{day}-{seq_formatted}'
)
```

### 便捷方法

系统提供了一些便捷方法，可以直接使用：

```python
from backend.core.number_generator import (
    generate_delivery_number,
    generate_incoming_document_number,
    generate_outgoing_document_number,
    generate_settlement_number,
    generate_approval_instance_number,
)

# 使用便捷方法
delivery_number = generate_delivery_number(DeliveryRecord)
document_number = generate_incoming_document_number(IncomingDocument)
settlement_number = generate_settlement_number(ProjectSettlement, project_number)
instance_number = generate_approval_instance_number(ApprovalInstance, workflow_code)
```

## 在模型中使用

### 方法1：在save方法中调用

```python
from django.db import models
from backend.core.number_generator import NumberGeneratorService

class DeliveryRecord(models.Model):
    delivery_number = models.CharField(max_length=50, unique=True)
    
    def save(self, *args, **kwargs):
        if not self.delivery_number:
            self.delivery_number = NumberGeneratorService.generate(
                model_class=DeliveryRecord,
                field_name='delivery_number',
                prefix='VIH-JF',
                date_format='%Y%m%d',
                seq_strategy='daily',
                seq_length=4
            )
        super().save(*args, **kwargs)
```

### 方法2：使用便捷方法

```python
from backend.core.number_generator import generate_delivery_number

class DeliveryRecord(models.Model):
    delivery_number = models.CharField(max_length=50, unique=True)
    
    def save(self, *args, **kwargs):
        if not self.delivery_number:
            self.delivery_number = generate_delivery_number(DeliveryRecord)
        super().save(*args, **kwargs)
```

## 参数说明

### 必需参数

- `model_class`: 模型类（Django Model类）
- `field_name`: 编号字段名（字符串）

### 可选参数

- `prefix`: 编号前缀（字符串，默认为空）
- `date_format`: 日期格式（字符串，如'%Y%m%d'，None表示不使用日期）
- `seq_length`: 序列号长度（整数，默认4位）
- `seq_strategy`: 序列号策略（字符串，可选值：'daily'、'monthly'、'yearly'、'global'、'related'）
- `related_field`: 关联字段名（字符串，用于related策略）
- `related_value`: 关联字段值（任意类型，用于related策略）
- `template`: 自定义模板（字符串，如'{prefix}-{date}-{seq:04d}'）
- `filter_conditions`: 额外的过滤条件（字典）
- `cache_key_prefix`: 缓存键前缀（字符串，用于提高性能）

## 日期格式说明

支持的日期格式字符串（Python strftime格式）：

- `%Y`: 4位年份（如2025）
- `%m`: 2位月份（01-12）
- `%d`: 2位日期（01-31）
- `%Y%m%d`: 年月日（20250101）
- `%Y-%m-%d`: 年月日（2025-01-01）
- 其他strftime支持的格式

## 序列号策略说明

### daily（按日重置）

每天从1开始计数，格式示例：
- 2025-01-01: VIH-JF-20250101-0001, VIH-JF-20250101-0002, ...
- 2025-01-02: VIH-JF-20250102-0001, VIH-JF-20250102-0002, ...

### monthly（按月重置）

每月从1开始计数，格式示例：
- 2025-01: VIH-JF-202501-0001, VIH-JF-202501-0002, ...
- 2025-02: VIH-JF-202502-0001, VIH-JF-202502-0002, ...

### yearly（按年重置）

每年从1开始计数，格式示例：
- 2025: SW20250001, SW20250002, ...
- 2026: SW20260001, SW20260002, ...

### global（全局累计）

永不重置，全局累计，格式示例：
- KH-20250101-0001, KH-20250101-0002, ..., KH-20251231-9999, KH-20260101-10000, ...

### related（按关联对象分组）

按关联对象分组累计，格式示例：
- 项目A: VIH-JS-PROJ001-0001, VIH-JS-PROJ001-0002, ...
- 项目B: VIH-JS-PROJ002-0001, VIH-JS-PROJ002-0002, ...

## 错误处理

服务会自动处理以下情况：

1. **编号冲突**：自动重试生成新编号（最多100次）
2. **序列号溢出**：抛出`ValueError`异常，提示调整规则
3. **并发冲突**：使用数据库事务和锁确保安全

## 性能优化

1. **使用缓存**：可以通过`cache_key_prefix`参数启用缓存
2. **批量生成**：对于批量生成场景，可以考虑预生成编号池
3. **索引优化**：确保编号字段有数据库索引

## 迁移现有代码

### 迁移步骤

1. 导入编号生成服务
2. 替换现有的编号生成逻辑
3. 测试验证编号生成正确性
4. 更新相关文档

### 迁移示例

**原代码：**
```python
def generate_delivery_number(self):
    prefix = 'VIH-JF'
    date_str = timezone.now().strftime('%Y%m%d')
    pattern = f"{prefix}-{date_str}-"
    max_number = DeliveryRecord.objects.filter(
        delivery_number__startswith=pattern
    ).aggregate(max_num=Max('delivery_number'))['max_num']
    # ... 复杂的序列号提取逻辑
```

**新代码：**
```python
from backend.core.number_generator import generate_delivery_number

def save(self, *args, **kwargs):
    if not self.delivery_number:
        self.delivery_number = generate_delivery_number(DeliveryRecord)
    super().save(*args, **kwargs)
```

## 最佳实践

1. **统一使用服务**：所有编号生成都应使用`NumberGeneratorService`
2. **合理选择策略**：根据业务需求选择合适的序列号策略
3. **设置合适长度**：根据业务量设置合适的序列号长度
4. **添加索引**：为编号字段添加数据库索引
5. **记录规则**：在`NumberRule`模型中记录编号规则配置

## 扩展开发

### 添加新的便捷方法

在`number_generator.py`中添加新的便捷方法：

```python
def generate_custom_number(model_class, instance=None):
    """生成自定义编号"""
    return NumberGeneratorService.generate(
        model_class=model_class,
        field_name='custom_number',
        prefix='CUSTOM',
        date_format='%Y%m%d',
        seq_strategy='daily',
        seq_length=4
    )
```

### 自定义模板变量

模板支持以下变量：
- `{prefix}`: 前缀
- `{date}`: 日期字符串
- `{seq}`: 序列号（整数）
- `{seq_formatted}`: 格式化后的序列号（如0001）
- `{related}`: 关联值
- `{year}`: 年份（4位）
- `{month}`: 月份（2位）
- `{day}`: 日期（2位）

## 常见问题

### Q: 如何修改现有编号规则？

A: 可以通过修改`NumberGeneratorService.generate()`的调用参数，或者更新`NumberRule`模型中的配置。

### Q: 编号冲突怎么办？

A: 服务会自动处理冲突，最多重试100次。如果仍然冲突，请检查编号规则配置。

### Q: 如何支持更复杂的编号格式？

A: 使用`template`参数定义自定义模板，支持所有Python字符串格式化功能。

### Q: 性能如何？

A: 服务使用数据库事务和锁确保并发安全，对于高并发场景，建议使用缓存或预生成编号池。

## 更新日志

- **v1.0.0** (2025-01-XX): 初始版本，支持基础编号生成功能

