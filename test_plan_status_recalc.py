#!/usr/bin/env python
"""
A3-3-5 状态重算功能测试脚本
"""
import os
import sys
import django

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.config.settings')
django.setup()

from django.utils import timezone
from datetime import timedelta
from backend.apps.plan_management.models import Plan
from backend.apps.plan_management.services import recalc_plan_status
from backend.apps.system_management.models import AuditLog, AuditAction

def test_status_recalc():
    """测试状态重算功能"""
    print("=" * 60)
    print("A3-3-5 状态重算功能测试")
    print("=" * 60)
    
    # 获取一个计划
    plan = Plan.objects.first()
    if not plan:
        print("没有找到计划，跳过测试")
        return
    
    print(f"\n测试计划: {plan.plan_number} - {plan.name}")
    print(f"当前状态: {plan.status}")
    print(f"当前进度: {plan.progress}%")
    print(f"开始时间: {plan.start_time}")
    print(f"结束时间: {plan.end_time}")
    
    # 测试 1: 进度 >= 100 应该变成 completed
    print("\n" + "-" * 60)
    print("测试 1: 进度 >= 100 -> completed")
    print("-" * 60)
    old_progress = plan.progress
    plan.progress = 100
    result = recalc_plan_status(plan)
    print(f"结果: {result.old} -> {result.new}, changed={result.changed}")
    if result.changed and result.new == "completed":
        print("✓ 测试通过：进度100%自动变为已完成")
    else:
        print("✗ 测试失败")
    plan.progress = old_progress  # 恢复
    
    # 测试 2: 结束时间已过且进度 < 100 -> overdue
    print("\n" + "-" * 60)
    print("测试 2: 结束时间已过且进度 < 100 -> overdue")
    print("-" * 60)
    old_end_time = plan.end_time
    plan.end_time = timezone.now() - timedelta(days=1)  # 昨天结束
    plan.progress = 50  # 进度50%
    result = recalc_plan_status(plan)
    print(f"结果: {result.old} -> {result.new}, changed={result.changed}")
    if result.changed and result.new == "overdue":
        print("✓ 测试通过：已逾期自动变为overdue")
    else:
        print("✗ 测试失败")
    plan.end_time = old_end_time  # 恢复
    plan.progress = old_progress
    
    # 测试 3: cancelled/paused/delayed 应该保持不变
    print("\n" + "-" * 60)
    print("测试 3: cancelled/paused/delayed 保持不变")
    print("-" * 60)
    old_status = plan.status
    plan.status = "cancelled"
    result = recalc_plan_status(plan)
    print(f"结果: {result.old} -> {result.new}, changed={result.changed}")
    if not result.changed:
        print("✓ 测试通过：cancelled状态保持不变")
    else:
        print("✗ 测试失败")
    plan.status = old_status  # 恢复
    
    # 测试 4: 检查 AuditLog
    print("\n" + "-" * 60)
    print("测试 4: 检查 AuditLog 记录")
    print("-" * 60)
    plan_audit_logs = AuditLog.objects.filter(
        action=AuditAction.PLAN_ACTION,
        object_type="plan_management.Plan"
    ).order_by('-created_at')[:5]
    print(f"找到 {plan_audit_logs.count()} 条 PLAN_ACTION 审计日志")
    for log in plan_audit_logs:
        print(f"  - {log.created_at}: {log.changes}")
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)

if __name__ == '__main__':
    test_status_recalc()

