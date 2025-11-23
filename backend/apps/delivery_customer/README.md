# 交付管理模块开发文档

## 📋 模块概述

交付管理模块实现了成果文件交付的完整流程管理，支持邮件、快递、送达三种交付方式，包含从报送、跟踪、反馈到归档的全流程管理，并提供逾期风险预警功能。

## 🗄️ 数据库表结构

### 1. delivery_record（交付记录表）
主要字段：
- `delivery_number`: 交付单号（唯一索引）
- `delivery_method`: 交付方式（email/express/hand_delivery）
- `status`: 交付状态（draft/submitted/sent/delivered/confirmed/archived等）
- `project_id`: 关联项目（外键）
- `client_id`: 关联客户（外键）
- `deadline`: 交付期限（用于逾期判断）
- `is_overdue`: 是否逾期
- `risk_level`: 风险等级

### 2. delivery_file（交付文件表）
主要字段：
- `delivery_record_id`: 关联交付记录（外键）
- `file`: 文件路径
- `file_name`: 原始文件名
- `file_size`: 文件大小
- `file_type`: 文件类型

### 3. delivery_feedback（交付反馈表）
主要字段：
- `delivery_record_id`: 关联交付记录（外键）
- `feedback_type`: 反馈类型（received/confirmed/question等）
- `content`: 反馈内容
- `feedback_by`: 反馈人

### 4. delivery_tracking（交付跟踪表）
主要字段：
- `delivery_record_id`: 关联交付记录（外键）
- `event_type`: 事件类型（submitted/sent/delivered等）
- `event_description`: 事件描述
- `location`: 位置（快递跟踪时使用）
- `event_time`: 事件时间

## 🚀 部署步骤

### 1. 创建数据库迁移

```bash
cd /home/devbox/project/vihhi/weihai_tech_production_system
python manage.py makemigrations delivery_customer
python manage.py migrate delivery_customer
```

### 2. 验证数据库表

迁移成功后，在PostgreSQL数据库中会创建以下表：
- `delivery_record`
- `delivery_file`
- `delivery_feedback`
- `delivery_tracking`

### 3. 访问功能

- **交付管理首页**: `/delivery/` 或 `/delivery/report/`
- **交付记录列表**: `/delivery/list/`
- **创建交付单**: `/delivery/create/`
- **交付详情**: `/delivery/{id}/`
- **交付统计**: `/delivery/statistics/`
- **风险预警**: `/delivery/warnings/`

### 4. API接口

- **交付记录API**: `/api/delivery/delivery/`
- **文件API**: `/api/delivery/files/`
- **统计API**: `/api/delivery/delivery/statistics/`
- **预警API**: `/api/delivery/delivery/warnings/`

## 📝 API使用示例

### 创建交付记录（邮件方式）
```bash
POST /api/delivery/delivery/
Content-Type: application/json

{
    "title": "项目A成果文件交付",
    "delivery_method": "email",
    "recipient_name": "张三",
    "recipient_email": "zhangsan@example.com",
    "email_subject": "项目成果文件",
    "email_message": "您好，请查收项目成果文件。",
    "project": 1,
    "client": 1,
    "deadline": "2024-01-10T18:00:00Z"
}
```

### 提交报送
```bash
POST /api/delivery/delivery/{id}/submit/
```

### 发送邮件
```bash
POST /api/delivery/delivery/{id}/send/
```

### 更新跟踪状态（快递）
```bash
POST /api/delivery/delivery/{id}/tracking/
{
    "event_type": "in_transit",
    "event_description": "快件已发出",
    "location": "北京分拨中心"
}
```

### 提交客户反馈
```bash
POST /api/delivery/delivery/{id}/feedback/
{
    "feedback_type": "confirmed",
    "content": "文件已收到，内容确认无误",
    "feedback_by": "张三",
    "feedback_email": "zhangsan@example.com"
}
```

### 归档交付记录
```bash
POST /api/delivery/delivery/{id}/archive/
```

## 🔍 数据库查询示例

### 查询所有交付记录
```sql
SELECT * FROM delivery_record ORDER BY created_at DESC;
```

### 查询逾期交付记录
```sql
SELECT * FROM delivery_record 
WHERE is_overdue = true 
ORDER BY overdue_days DESC;
```

### 查询某个项目的交付记录
```sql
SELECT * FROM delivery_record 
WHERE project_id = 1 
ORDER BY created_at DESC;
```

### 查询交付跟踪记录
```sql
SELECT * FROM delivery_tracking 
WHERE delivery_record_id = 1 
ORDER BY event_time DESC;
```

## ⚙️ 配置说明

### 邮件配置（settings.py）
```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.group.com.cn'
EMAIL_PORT = 587
EMAIL_HOST_USER = 'whkj@group.com.cn'
EMAIL_HOST_PASSWORD = 'your_password'
EMAIL_USE_TLS = True
DEFAULT_FROM_EMAIL = 'whkj@group.com.cn'
```

### 文件存储配置
文件存储在 `media/delivery_files/` 目录下，按日期和交付单号组织：
```
media/
└── delivery_files/
    └── 2024/
        └── 01/
            └── 01/
                └── DEL202401010001/
                    ├── file1.pdf
                    └── file2.docx
```

## 📊 功能特性

1. **三种交付方式**
   - 邮件：支持附件、抄送、密送
   - 快递：快递单号管理、物流跟踪
   - 送达：送达人记录、送达确认

2. **全流程管理**
   - 报送：创建交付记录
   - 跟踪：状态跟踪、时间线记录
   - 反馈：客户反馈接收和处理
   - 归档：自动归档条件配置

3. **风险预警**
   - 逾期检测：基于交付期限自动检测
   - 风险等级：低/中/高/严重
   - 预警通知：自动发送预警

4. **数据库优化**
   - 所有外键都设置了 `db_constraint=True`
   - 关键字段设置了数据库索引
   - 使用PostgreSQL数据库

## 🔗 相关链接

- 设计方案文档：`/home/devbox/project/成果文件交付工具设计方案.md`
- Django Admin：`/admin/delivery_customer/`
- API文档：`/api/docs/`

