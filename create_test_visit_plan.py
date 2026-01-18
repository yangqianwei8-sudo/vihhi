#!/usr/bin/env python
"""创建测试拜访计划数据"""
import os
import sys
import django

# 设置Django环境
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.config.settings')
django.setup()

from django.contrib.auth import get_user_model
from backend.apps.customer_management.models import VisitPlan, Client
from django.utils import timezone
from datetime import timedelta

User = get_user_model()

# 获取第一个用户（通常是admin）
user = User.objects.first()
if not user:
    print("❌ 没有找到用户，请先创建用户")
    sys.exit(1)

print(f"✅ 使用用户: {user.username}")

# 获取第一个客户
client = Client.objects.filter(is_active=True).first()
if not client:
    print("❌ 没有找到客户，请先创建客户")
    sys.exit(1)

print(f"✅ 使用客户: {client.name}")

# 创建测试拜访计划
visit_plan = VisitPlan.objects.create(
    client=client,
    plan_date=timezone.now() + timedelta(days=1),  # 明天的日期
    location=client.address or "测试地点",
    plan_title=f"测试拜访计划 - {timezone.now().strftime('%Y%m%d%H%M%S')}",
    plan_purpose="这是一条测试数据，用于查看打卡列表页面效果",
    status='planned',
    created_by=user,
    checklist_prepared=False  # 未准备沟通清单，测试过滤条件是否已清除
)

print(f"\n✅ 已创建测试拜访计划:")
print(f"   ID: {visit_plan.id}")
print(f"   标题: {visit_plan.plan_title}")
print(f"   客户: {visit_plan.client.name}")
print(f"   计划日期: {visit_plan.plan_date}")
print(f"   状态: {visit_plan.get_status_display()}")
print(f"   沟通清单已准备: {visit_plan.checklist_prepared}")
print(f"\n现在可以在打卡列表页面看到这条数据了！")
print(f"访问: http://localhost:8001/customers/visit-checkin/select/")

