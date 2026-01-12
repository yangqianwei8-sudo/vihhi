# 工作计划提醒功能说明

## 功能概述

系统提供四种工作计划提醒功能：

1. **日工作计划提醒**：每天上午9点，系统会自动向所有激活员工发送日工作计划编制提醒通知。
2. **周工作计划提醒**：每周五上午9点，系统会自动向所有激活员工发送周工作计划编制提醒通知。
3. **月度工作计划提醒**：每月28日上午9点，系统会自动向所有激活员工发送月度工作计划编制提醒通知。
4. **季度工作计划提醒**：每个自然季度的最后一个月15日上午9点（3月、6月、9月、12月的15日），系统会自动向所有激活员工发送季度工作计划编制提醒通知。

## 文件说明

- `management/commands/send_daily_plan_reminder.py` - 日提醒发送管理命令
- `management/commands/send_weekly_plan_reminder.py` - 周提醒发送管理命令
- `management/commands/send_monthly_plan_reminder.py` - 月度提醒发送管理命令
- `management/commands/send_quarterly_plan_reminder.py` - 季度提醒发送管理命令
- `crontab_example.txt` - Crontab配置示例
- `setup_crontab.sh` - 自动配置脚本

## 使用方法

### 方法1：使用自动配置脚本（推荐）

```bash
cd /home/devbox/project/vihhi/weihai_tech_production_system/backend/apps/plan_management
./setup_crontab.sh
```

### 方法2：手动配置 Crontab

1. 编辑 crontab：
```bash
crontab -e
```

2. 添加以下行（请根据实际路径修改）：
```bash
# 每天9点发送日工作计划提醒
0 9 * * * cd /home/devbox/project/vihhi/weihai_tech_production_system && /home/devbox/project/.venv/bin/python manage.py send_daily_plan_reminder >> /home/devbox/project/logs/daily_plan_reminder.log 2>&1

# 每周五9点发送周工作计划提醒
0 9 * * 5 cd /home/devbox/project/vihhi/weihai_tech_production_system && /home/devbox/project/.venv/bin/python manage.py send_weekly_plan_reminder >> /home/devbox/project/logs/weekly_plan_reminder.log 2>&1

# 每月28日9点发送月度工作计划提醒
0 9 28 * * cd /home/devbox/project/vihhi/weihai_tech_production_system && /home/devbox/project/.venv/bin/python manage.py send_monthly_plan_reminder >> /home/devbox/project/logs/monthly_plan_reminder.log 2>&1

# 每季度最后一个月15日9点发送季度工作计划提醒（3月、6月、9月、12月）
0 9 15 3,6,9,12 * cd /home/devbox/project/vihhi/weihai_tech_production_system && /home/devbox/project/.venv/bin/python manage.py send_quarterly_plan_reminder >> /home/devbox/project/logs/quarterly_plan_reminder.log 2>&1
```

### 方法3：使用 Celery Beat（如果项目已配置 Celery）

在 `celery.py` 或 `settings.py` 中添加：

```python
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    'send-monthly-plan-reminder': {
        'task': 'backend.apps.plan_management.tasks.send_monthly_plan_reminder',
        'schedule': crontab(hour=9, minute=0, day_of_month=28),
    },
    'send-daily-plan-reminder': {
        'task': 'backend.apps.plan_management.tasks.send_daily_plan_reminder',
        'schedule': crontab(hour=9, minute=0),  # 每天9点
    },
    'send-weekly-plan-reminder': {
        'task': 'backend.apps.plan_management.tasks.send_weekly_plan_reminder',
        'schedule': crontab(hour=9, minute=0, day_of_week=5),  # 周五
    },
    'send-monthly-plan-reminder': {
        'task': 'backend.apps.plan_management.tasks.send_monthly_plan_reminder',
        'schedule': crontab(hour=9, minute=0, day_of_month=28),  # 每月28日
    },
    'send-quarterly-plan-reminder': {
        'task': 'backend.apps.plan_management.tasks.send_quarterly_plan_reminder',
        'schedule': crontab(hour=9, minute=0, day_of_month=15, month_of_year='3,6,9,12'),  # 季度最后一个月15日
    },
}
```

## 测试命令

### 日提醒测试

#### 试运行（不实际发送）
```bash
python manage.py send_daily_plan_reminder --dry-run
```

#### 测试模式（只发送给前5个用户）
```bash
python manage.py send_daily_plan_reminder --test
```

#### 测试模式 + 试运行
```bash
python manage.py send_daily_plan_reminder --test --dry-run
```

### 周提醒测试

#### 试运行（不实际发送）
```bash
python manage.py send_weekly_plan_reminder --dry-run
```

#### 测试模式（只发送给前5个用户）
```bash
python manage.py send_weekly_plan_reminder --test
```

#### 测试模式 + 试运行
```bash
python manage.py send_weekly_plan_reminder --test --dry-run
```

### 月度提醒测试

#### 试运行（不实际发送）
```bash
python manage.py send_monthly_plan_reminder --dry-run
```

#### 测试模式（只发送给前5个用户）
```bash
python manage.py send_monthly_plan_reminder --test
```

#### 测试模式 + 试运行
```bash
python manage.py send_monthly_plan_reminder --test --dry-run
```

### 季度提醒测试

#### 试运行（不实际发送）
```bash
python manage.py send_quarterly_plan_reminder --dry-run
```

#### 测试模式（只发送给前5个用户）
```bash
python manage.py send_quarterly_plan_reminder --test
```

#### 测试模式 + 试运行
```bash
python manage.py send_quarterly_plan_reminder --test --dry-run
```

## 通知方式

提醒将通过以下方式发送：
1. **邮件通知** - 发送到用户的邮箱地址
2. **企业微信通知** - 如果用户配置了企微ID，也会发送企微通知

## 通知内容

### 日提醒
- 提醒标题：日工作计划提醒
- 提醒内容：要求每天上午9点前完成当日工作计划的编制
- 计划创建链接：直接跳转到计划创建页面（计划周期选择"日计划"）
- 日期信息：显示当天的日期

### 周提醒
- 提醒标题：周工作计划提醒
- 提醒内容：要求在每周五前完成下周工作计划的编制
- 计划创建链接：直接跳转到计划创建页面（计划周期选择"周计划"）
- 日期信息：显示下周的起止日期

### 月度提醒
- 提醒标题：月度工作计划提醒
- 提醒内容：要求在当月28日前完成下个月工作计划的编制
- 计划创建链接：直接跳转到计划创建页面（计划周期选择"月计划"）

### 季度提醒
- 提醒标题：季度工作计划提醒
- 提醒内容：要求在每个自然季度的最后一个月15日前完成下一个季度工作计划的编制
- 计划创建链接：直接跳转到计划创建页面（计划周期选择"季度计划"）
- 季度信息：自动计算并显示下一个季度的起止日期

## 日志查看

### 日提醒日志
```bash
# 查看日志
tail -f /home/devbox/project/logs/daily_plan_reminder.log

# 查看最近的日志
tail -n 100 /home/devbox/project/logs/daily_plan_reminder.log
```

### 周提醒日志
```bash
# 查看日志
tail -f /home/devbox/project/logs/weekly_plan_reminder.log

# 查看最近的日志
tail -n 100 /home/devbox/project/logs/weekly_plan_reminder.log
```

### 月度提醒日志
```bash
# 查看日志
tail -f /home/devbox/project/logs/monthly_plan_reminder.log

# 查看最近的日志
tail -n 100 /home/devbox/project/logs/monthly_plan_reminder.log
```

### 季度提醒日志
```bash
# 查看日志
tail -f /home/devbox/project/logs/quarterly_plan_reminder.log

# 查看最近的日志
tail -n 100 /home/devbox/project/logs/quarterly_plan_reminder.log
```

## 注意事项

1. **路径配置**：请根据实际项目路径和虚拟环境路径修改 crontab 配置
2. **权限检查**：确保 crontab 执行用户有权限访问项目目录和日志目录
3. **邮件配置**：确保 Django 的邮件配置正确（settings.py 中的 EMAIL_* 配置）
4. **企微配置**：如需发送企微通知，请配置 WECOM_* 相关设置

## 故障排查

### 1. 检查命令是否可执行
```bash
# 检查日提醒命令
python manage.py send_daily_plan_reminder --help

# 检查周提醒命令
python manage.py send_weekly_plan_reminder --help

# 检查月度提醒命令
python manage.py send_monthly_plan_reminder --help

# 检查季度提醒命令
python manage.py send_quarterly_plan_reminder --help
```

### 2. 检查用户数据
```bash
python manage.py shell
>>> from django.contrib.auth import get_user_model
>>> User = get_user_model()
>>> User.objects.filter(is_active=True).count()
```

### 3. 检查邮件配置
```bash
python manage.py shell
>>> from django.core.mail import send_mail
>>> send_mail('测试', '测试内容', 'from@example.com', ['to@example.com'], fail_silently=False)
```

### 4. 查看 crontab 日志
```bash
# 查看系统日志（如果配置了）
grep CRON /var/log/syslog

# 或查看 crontab 执行日志
tail -f /home/devbox/project/logs/daily_plan_reminder.log     # 日提醒
tail -f /home/devbox/project/logs/weekly_plan_reminder.log    # 周提醒
tail -f /home/devbox/project/logs/monthly_plan_reminder.log   # 月度提醒
tail -f /home/devbox/project/logs/quarterly_plan_reminder.log # 季度提醒

