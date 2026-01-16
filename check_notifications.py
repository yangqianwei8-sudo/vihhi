#!/usr/bin/env python
import os
import sys
import django

sys.path.insert(0, '/home/devbox/project/vihhi/weihai_tech_production_system')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from backend.apps.system_management.models import User, Role
from backend.apps.project_center.models import ProjectTeamNotification, Project

print("=" * 60)
print("检查通知系统")
print("=" * 60)

# 1. 检查技术部经理角色和用户
print("\n1. 技术部经理角色配置:")
tm_role = Role.objects.filter(code='technical_manager').first()
if tm_role:
    print(f"   角色: {tm_role.name} (code: {tm_role.code})")
    tm_users = tm_role.users.filter(is_active=True)
    print(f"   用户数: {tm_users.count()}")
    for u in tm_users:
        print(f"   - {u.username} ({u.get_full_name() or '未设置姓名'})")
else:
    print("   ❌ 未找到技术部经理角色")

# 2. 检查通知记录
print("\n3. 通知记录:")
all_notifications = ProjectTeamNotification.objects.all().order_by('-created_time')[:10]
print(f"   总数: {ProjectTeamNotification.objects.count()}")
print(f"   未读: {ProjectTeamNotification.objects.filter(is_read=False).count()}")
print("\n   最近10条通知:")
for n in all_notifications:
    read_status = "已读" if n.is_read else "未读"
    print(f"   - [{read_status}] {n.title}")
    print(f"     接收人: {n.recipient.username}")
    print(f"     项目: {n.project.name if n.project else 'N/A'}")
    print(f"     时间: {n.created_time}")
    print()

# 3. 检查周强的通知
print("\n4. 检查用户'周强'的通知:")
zhouqiang = User.objects.filter(username__icontains='周强').first() or User.objects.filter(username__icontains='zhou').first()
if zhouqiang:
    print(f"   找到用户: {zhouqiang.username} ({zhouqiang.get_full_name() or '未设置姓名'})")
    zq_notifications = ProjectTeamNotification.objects.filter(recipient=zhouqiang).order_by('-created_time')
    print(f"   总通知数: {zq_notifications.count()}")
    print(f"   未读通知数: {zq_notifications.filter(is_read=False).count()}")
    print("\n   通知列表:")
    for n in zq_notifications[:5]:
        read_status = "已读" if n.is_read else "未读"
        print(f"   - [{read_status}] {n.title}")
        print(f"     消息: {n.message[:50]}...")
        print(f"     时间: {n.created_time}")
        print()
else:
    print("   ❌ 未找到用户'周强'")

print("=" * 60)


