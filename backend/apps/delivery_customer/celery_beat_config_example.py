"""
Celery Beat 定时任务配置示例
用于配置发文跟踪的定时任务

使用方法：
1. 如果项目已有 celery.py 配置文件，将以下内容添加到 CELERYBEAT_SCHEDULE 中
2. 如果使用 Django settings，在 settings.py 中添加 CELERY_BEAT_SCHEDULE 配置
"""

# ============================================
# 方式1：在 celery.py 中配置（推荐）
# ============================================

# 在项目的 celery.py 文件中（通常是 backend/config/celery.py 或 backend/celery.py）
# 添加以下配置：

"""
from celery.schedules import crontab

app.conf.beat_schedule = {
    # 其他定时任务...
    
    # 发文跟踪状态更新任务
    'update-outgoing-document-tracking-status': {
        'task': 'backend.apps.delivery_customer.tasks.update_outgoing_document_tracking_status',
        'schedule': 30.0 * 60.0,  # 每30分钟执行一次（单位：秒）
        # 或者使用 crontab：
        # 'schedule': crontab(minute='*/30'),  # 每30分钟执行一次
        # 'schedule': crontab(minute=0, hour='*'),  # 每小时执行一次
    },
}
"""

# ============================================
# 方式2：在 settings.py 中配置
# ============================================

# 在 settings.py 中添加：

"""
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    # 其他定时任务...
    
    # 发文跟踪状态更新任务
    'update-outgoing-document-tracking-status': {
        'task': 'backend.apps.delivery_customer.tasks.update_outgoing_document_tracking_status',
        'schedule': 30.0 * 60.0,  # 每30分钟执行一次（单位：秒）
        # 或者使用 crontab：
        # 'schedule': crontab(minute='*/30'),  # 每30分钟执行一次
        # 'schedule': crontab(minute=0, hour='*'),  # 每小时执行一次
    },
}
"""

# ============================================
# 执行时间配置说明
# ============================================

# 1. 使用秒数（推荐用于开发环境）
#    'schedule': 30.0 * 60.0,  # 30分钟 = 1800秒

# 2. 使用 crontab 格式（推荐用于生产环境）
#    'schedule': crontab(minute='*/30'),  # 每30分钟执行一次
#    'schedule': crontab(minute=0, hour='*'),  # 每小时的第0分钟执行
#    'schedule': crontab(minute=0, hour='*/2'),  # 每2小时执行一次
#    'schedule': crontab(minute=0, hour=9),  # 每天上午9点执行

# ============================================
# 启动 Celery Beat
# ============================================

# 1. 启动 Celery Worker（如果还没有运行）
#    celery -A backend.config worker -l info

# 2. 启动 Celery Beat
#    celery -A backend.config beat -l info

# 3. 或者使用 supervisor/systemd 管理（生产环境推荐）

# ============================================
# Supervisor 配置示例
# ============================================

"""
[program:celery_beat]
command=/path/to/venv/bin/celery -A backend.config beat -l info
directory=/path/to/project
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/celery_beat.log
"""

# ============================================
# Systemd 配置示例
# ============================================

"""
[Unit]
Description=Celery Beat Service
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/project
Environment="PATH=/path/to/venv/bin"
ExecStart=/path/to/venv/bin/celery -A backend.config beat -l info
Restart=always

[Install]
WantedBy=multi-user.target
"""
