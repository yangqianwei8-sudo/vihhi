#!/usr/bin/env python
"""
测试 A3-3-8-1 审计封装功能
"""
import os
import sys
import django
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.config.settings')
django.setup()

from django.test import RequestFactory
from django.contrib.auth import get_user_model
from backend.apps.plan_management.models import Plan, PlanStatusLog
from backend.apps.plan_management.audit import audit_plan_event
from backend.apps.system_management.models import AuditLog

User = get_user_model()

def test_audit_event():
    """测试审计事件记录"""
    print("=" * 70)
    print("A3-3-8-1 审计封装测试")
    print("=" * 70)
    
    # 获取测试用户和计划
    user = User.objects.filter(is_active=True).first()
    if not user:
        print("❌ 未找到测试用户")
        return
    
    plan = Plan.objects.filter(company__isnull=False).first()
    if not plan:
        print("❌ 未找到测试计划")
        return
    
    print(f"\n测试用户: {user.username}")
    print(f"测试计划: {plan.plan_number} ({plan.name})")
    print(f"当前进度: {plan.progress}%")
    print(f"当前状态: {plan.status}")
    
    # 创建模拟请求（用于提取 IP/UA）
    factory = RequestFactory()
    request = factory.get('/')
    request.META['REMOTE_ADDR'] = '127.0.0.1'
    request.META['HTTP_USER_AGENT'] = 'Test-Agent/1.0'
    
    # 记录旧值
    old_progress = plan.progress
    old_status = plan.status
    
    # 模拟进度更新：0 -> 30
    plan.progress = 30
    plan.save(update_fields=['progress'])
    
    # 记录审计事件
    print("\n" + "-" * 70)
    print("记录 progress_update 审计事件")
    print("-" * 70)
    
    audit_log = audit_plan_event(
        actor=user,
        plan=plan,
        event="progress_update",
        changes={
            "progress": {"from": float(old_progress) if old_progress else 0, "to": 30.0}
        },
        meta={
            "description": "测试进度更新：从 0% 更新到 30%"
        },
        request=request
    )
    
    if audit_log:
        print("✓ 审计日志创建成功")
        print(f"\n审计日志详情:")
        print(f"  ID: {audit_log.id}")
        print(f"  操作者: {audit_log.actor.username if audit_log.actor else 'None'}")
        print(f"  操作类型: {audit_log.action}")
        print(f"  对象类型: {audit_log.object_type}")
        print(f"  对象ID: {audit_log.object_id}")
        print(f"  事件: {audit_log.meta.get('event')}")
        print(f"  变更内容:")
        print(json.dumps(audit_log.changes, indent=4, ensure_ascii=False))
        print(f"  元数据:")
        print(json.dumps(audit_log.meta, indent=4, ensure_ascii=False))
        print(f"  创建时间: {audit_log.created_at}")
    else:
        print("❌ 审计日志创建失败")
        return
    
    # 检查状态日志（如果有状态变化）
    print("\n" + "-" * 70)
    print("检查状态日志")
    print("-" * 70)
    
    status_logs = PlanStatusLog.objects.filter(plan=plan).order_by('-changed_time')[:5]
    if status_logs.exists():
        print(f"✓ 找到 {status_logs.count()} 条状态日志（最近5条）")
        for log in status_logs:
            print(f"\n  状态日志:")
            print(f"    旧状态: {log.old_status}")
            print(f"    新状态: {log.new_status}")
            print(f"    变更人: {log.changed_by.username if log.changed_by else 'None'}")
            print(f"    变更原因: {log.change_reason}")
            print(f"    变更时间: {log.changed_time}")
    else:
        print("ℹ 暂无状态日志（进度更新未触发状态变化）")
    
    print("\n" + "=" * 70)
    print("测试完成")
    print("=" * 70)
    
    # 输出 JSON 格式的样例（用于验收）
    print("\n" + "=" * 70)
    print("审计日志 JSON 样例（用于验收）")
    print("=" * 70)
    print(json.dumps({
        "id": audit_log.id,
        "actor": audit_log.actor.username if audit_log.actor else None,
        "action": audit_log.action,
        "object_type": audit_log.object_type,
        "object_id": audit_log.object_id,
        "event": audit_log.meta.get("event"),
        "changes": audit_log.changes,
        "meta": audit_log.meta,
        "created_at": audit_log.created_at.isoformat(),
    }, indent=2, ensure_ascii=False))

if __name__ == '__main__':
    test_audit_event()

