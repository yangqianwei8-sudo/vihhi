#!/usr/bin/env python
"""检查数据库中的会话数据"""
import os
import sys
import django
from datetime import datetime, timedelta
from pathlib import Path
from django.utils import timezone

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.config.settings')
django.setup()

from backend.apps.workflow_engine.models import AgentConversation

now = timezone.now()
yesterday_start = (now - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
day_before_yesterday_start = (now - timedelta(days=2)).replace(hour=0, minute=0, second=0, microsecond=0)

print(f"当前时间: {now}")
print(f"昨天开始: {yesterday_start}")
print(f"前天开始: {day_before_yesterday_start}")
print(f"\n总会话数: {AgentConversation.objects.count()}")

print(f"\n最近10个会话:")
for c in AgentConversation.objects.order_by('-created_time')[:10]:
    print(f"  ID:{c.id} 标题:{c.title[:30]} 创建时间:{c.created_time} 用户:{c.user.username}")

