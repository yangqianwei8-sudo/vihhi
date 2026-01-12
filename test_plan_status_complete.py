#!/usr/bin/env python
"""
测试计划状态变更和 AuditLog
"""
import os
import sys
import django
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.config.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from backend.apps.plan_management.models import Plan
from backend.apps.system_management.models import AuditLog, AuditAction

User = get_user_model()

def test_complete_status():
    """测试完成状态变更"""
    client = Client(enforce_csrf_checks=False)
    client.defaults['HTTP_HOST'] = 'localhost'
    
    # 登录
    print("=" * 60)
    print("登录 tester1")
    print("=" * 60)
    login_response = client.post('/api/system/users/login/', {
        'username': 'tester1',
        'password': '123456'
    })
    if login_response.status_code != 200:
        print(f"登录失败: {login_response.status_code}")
        return
    print("✓ 登录成功\n")
    
    # 获取一个计划
    tester = User.objects.get(username='tester1')
    plan = Plan.objects.filter(company=tester.profile.company).first()
    if not plan:
        plan = Plan.objects.first()
    
    if not plan:
        print("没有找到计划")
        return
    
    print(f"计划: {plan.plan_number} - {plan.name}")
    print(f"计划ID: {plan.id}")
    print(f"当前状态: {plan.status}")
    print(f"当前进度: {plan.progress}%")
    
    # 更新进度到100%（应该触发状态变更）
    print("\n" + "=" * 60)
    print("更新计划进度到 100%（应该触发状态变更）")
    print("=" * 60)
    old_audit_count = AuditLog.objects.filter(action=AuditAction.PLAN_ACTION).count()
    
    response = client.patch(
        f'/api/plan/plans/{plan.id}/',
        json.dumps({'progress': '100'}),
        content_type='application/json'
    )
    
    print(f"响应状态码: {response.status_code}")
    if response.status_code == 200:
        data = json.loads(response.content)
        print(f"✓ 更新成功")
        print(f"更新后进度: {data.get('progress')}%")
        print(f"更新后状态: {data.get('status')}")
        
        # 检查 AuditLog
        new_audit_count = AuditLog.objects.filter(action=AuditAction.PLAN_ACTION).count()
        print(f"\nAuditLog 数量变化: {old_audit_count} -> {new_audit_count}")
        
        if new_audit_count > old_audit_count:
            latest_log = AuditLog.objects.filter(action=AuditAction.PLAN_ACTION).order_by('-created_at').first()
            print(f"✓ 找到新的 AuditLog:")
            print(f"  - event: {latest_log.meta.get('event')}")
            print(f"  - changes: {latest_log.changes}")
            print(f"  - actor: {latest_log.actor.username if latest_log.actor else 'None'}")
        else:
            print("✗ 未找到新的 AuditLog（可能状态未变更）")
    else:
        print(f"✗ 更新失败: {response.content}")
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)

if __name__ == '__main__':
    test_complete_status()

