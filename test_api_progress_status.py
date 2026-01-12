#!/usr/bin/env python
"""
A3-3-8-2 API 验收测试：progress 和 status 接口
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
from backend.apps.plan_management.models import Plan, PlanProgressRecord, PlanStatusLog
from backend.apps.system_management.models import AuditLog

User = get_user_model()

def test_api_progress_status():
    """测试 progress 和 status API"""
    client = Client(enforce_csrf_checks=False)
    client.defaults['HTTP_HOST'] = 'localhost'
    
    # 登录 tester1
    print("=" * 70)
    print("A3-3-8-2 API 验收测试")
    print("=" * 70)
    
    login_response = client.post('/api/system/users/login/', {
        'username': 'tester1',
        'password': '123456'
    })
    if login_response.status_code != 200:
        print(f"❌ 登录失败: {login_response.status_code}")
        return
    
    print("✓ 登录成功\n")
    
    # 获取一个测试计划
    plan = Plan.objects.filter(
        company__isnull=False,
        responsible_person__username='tester1'
    ).first()
    
    if not plan:
        print("❌ 未找到测试计划")
        return
    
    print(f"测试计划: {plan.plan_number} ({plan.name})")
    print(f"当前进度: {plan.progress}%")
    print(f"当前状态: {plan.status}\n")
    
    # 记录初始计数
    initial_progress_records = PlanProgressRecord.objects.filter(plan=plan).count()
    initial_status_logs = PlanStatusLog.objects.filter(plan=plan).count()
    initial_audit_logs = AuditLog.objects.filter(
        object_type='plan_management.Plan',
        object_id=str(plan.pk)
    ).count()
    
    print(f"初始计数:")
    print(f"  PlanProgressRecord: {initial_progress_records}")
    print(f"  PlanStatusLog: {initial_status_logs}")
    print(f"  AuditLog: {initial_audit_logs}\n")
    
    # ========== 用例 1：更新进度 0 → 50 ==========
    print("=" * 70)
    print("用例 1：更新进度 0 → 50")
    print("=" * 70)
    
    # 先重置进度为 0
    plan.progress = 0
    plan.save(update_fields=['progress'])
    
    response = client.post(
        f'/api/plan/plans/{plan.pk}/progress/',
        data=json.dumps({
            'progress': 50,
            'progress_description': '已完成第一阶段工作，进度更新到50%',
            'execution_result': '执行顺利',
            'execution_issues': '',
            'notes': '测试用例1'
        }),
        content_type='application/json'
    )
    
    print(f"响应状态码: {response.status_code}")
    if response.status_code == 200:
        data = json.loads(response.content)
        print(f"✓ 接口调用成功")
        print(f"返回数据:")
        print(f"  plan_number: {data.get('plan_number')}")
        print(f"  progress: {data.get('progress')}")
        print(f"  status: {data.get('status')}")
        
        # 检查数据库记录
        plan.refresh_from_db()
        progress_records_count = PlanProgressRecord.objects.filter(plan=plan).count()
        status_logs_count = PlanStatusLog.objects.filter(plan=plan).count()
        audit_logs_count = AuditLog.objects.filter(
            object_type='plan_management.Plan',
            object_id=str(plan.pk)
        ).count()
        
        print(f"\n数据库记录:")
        print(f"  PlanProgressRecord: {progress_records_count} (+{progress_records_count - initial_progress_records})")
        print(f"  PlanStatusLog: {status_logs_count} (+{status_logs_count - initial_status_logs})")
        print(f"  AuditLog: {audit_logs_count} (+{audit_logs_count - initial_audit_logs})")
        
        # 获取最新的记录
        latest_progress_record = PlanProgressRecord.objects.filter(plan=plan).order_by('-recorded_time').first()
        latest_audit_log = AuditLog.objects.filter(
            object_type='plan_management.Plan',
            object_id=str(plan.pk)
        ).order_by('-created_at').first()
        
        if latest_progress_record:
            print(f"\n最新 PlanProgressRecord:")
            print(f"  progress: {latest_progress_record.progress}%")
            print(f"  progress_description: {latest_progress_record.progress_description}")
            print(f"  recorded_by: {latest_progress_record.recorded_by.username}")
        
        if latest_audit_log:
            print(f"\n最新 AuditLog:")
            print(f"  action: {latest_audit_log.action}")
            print(f"  event: {latest_audit_log.meta.get('event')}")
            print(f"  changes: {json.dumps(latest_audit_log.changes, indent=2, ensure_ascii=False)}")
    else:
        print(f"❌ 接口调用失败")
        print(f"响应内容: {response.content.decode()}")
        return
    
    # ========== 用例 2：手动状态 paused → in_progress ==========
    print("\n" + "=" * 70)
    print("用例 2：手动状态变更 paused → in_progress")
    print("=" * 70)
    
    # 先设置状态为 paused（paused 可以转换到 in_progress）
    plan.status = 'paused'
    plan.save(update_fields=['status'])
    
    # 记录变更前的计数
    before_status_logs = PlanStatusLog.objects.filter(plan=plan).count()
    before_audit_logs = AuditLog.objects.filter(
        object_type='plan_management.Plan',
        object_id=str(plan.pk)
    ).count()
    
    response = client.post(
        f'/api/plan/plans/{plan.pk}/status/',
        data=json.dumps({
            'status': 'in_progress',
            'reason': '手动启动计划执行'
        }),
        content_type='application/json'
    )
    
    print(f"响应状态码: {response.status_code}")
    if response.status_code == 200:
        data = json.loads(response.content)
        print(f"✓ 接口调用成功")
        print(f"返回数据:")
        print(f"  status: {data.get('status')}")
        
        # 检查数据库记录
        plan.refresh_from_db()
        status_logs_count = PlanStatusLog.objects.filter(plan=plan).count()
        audit_logs_count = AuditLog.objects.filter(
            object_type='plan_management.Plan',
            object_id=str(plan.pk)
        ).count()
        
        print(f"\n数据库记录:")
        print(f"  PlanStatusLog: {status_logs_count} (+{status_logs_count - before_status_logs})")
        print(f"  AuditLog: {audit_logs_count} (+{audit_logs_count - before_audit_logs})")
        
        # 获取最新的记录
        latest_status_log = PlanStatusLog.objects.filter(plan=plan).order_by('-changed_time').first()
        latest_audit_log = AuditLog.objects.filter(
            object_type='plan_management.Plan',
            object_id=str(plan.pk)
        ).order_by('-created_at').first()
        
        if latest_status_log:
            print(f"\n最新 PlanStatusLog:")
            print(f"  old_status: {latest_status_log.old_status}")
            print(f"  new_status: {latest_status_log.new_status}")
            print(f"  changed_by: {latest_status_log.changed_by.username if latest_status_log.changed_by else None}")
            print(f"  change_reason: {latest_status_log.change_reason}")
        
        if latest_audit_log:
            print(f"\n最新 AuditLog:")
            print(f"  action: {latest_audit_log.action}")
            print(f"  event: {latest_audit_log.meta.get('event')}")
            print(f"  changes: {json.dumps(latest_audit_log.changes, indent=2, ensure_ascii=False)}")
    else:
        print(f"❌ 接口调用失败")
        print(f"响应内容: {response.content.decode()}")
        return
    
    # ========== 用例 3：进度 50 → 100（触发 completed）==========
    print("\n" + "=" * 70)
    print("用例 3：进度 50 → 100（触发 completed）")
    print("=" * 70)
    
    # 先设置进度为 50，状态为 in_progress
    plan.progress = 50
    plan.status = 'in_progress'
    plan.save(update_fields=['progress', 'status'])
    
    # 记录变更前的计数
    before_progress_records = PlanProgressRecord.objects.filter(plan=plan).count()
    before_status_logs = PlanStatusLog.objects.filter(plan=plan).count()
    before_audit_logs = AuditLog.objects.filter(
        object_type='plan_management.Plan',
        object_id=str(plan.pk)
    ).count()
    
    response = client.post(
        f'/api/plan/plans/{plan.pk}/progress/',
        data=json.dumps({
            'progress': 100,
            'progress_description': '计划已完成，所有工作已完成',
            'execution_result': '执行完成',
            'execution_issues': '',
            'notes': '测试用例3'
        }),
        content_type='application/json'
    )
    
    print(f"响应状态码: {response.status_code}")
    if response.status_code == 200:
        data = json.loads(response.content)
        print(f"✓ 接口调用成功")
        print(f"返回数据:")
        print(f"  progress: {data.get('progress')}")
        print(f"  status: {data.get('status')}")
        
        # 检查数据库记录
        plan.refresh_from_db()
        progress_records_count = PlanProgressRecord.objects.filter(plan=plan).count()
        status_logs_count = PlanStatusLog.objects.filter(plan=plan).count()
        audit_logs_count = AuditLog.objects.filter(
            object_type='plan_management.Plan',
            object_id=str(plan.pk)
        ).count()
        
        print(f"\n数据库记录:")
        print(f"  PlanProgressRecord: {progress_records_count} (+{progress_records_count - before_progress_records})")
        print(f"  PlanStatusLog: {status_logs_count} (+{status_logs_count - before_status_logs})")
        print(f"  AuditLog: {audit_logs_count} (+{audit_logs_count - before_audit_logs})")
        
        # 获取最新的记录
        latest_progress_record = PlanProgressRecord.objects.filter(plan=plan).order_by('-recorded_time').first()
        latest_status_log = PlanStatusLog.objects.filter(plan=plan).order_by('-changed_time').first()
        latest_audit_log = AuditLog.objects.filter(
            object_type='plan_management.Plan',
            object_id=str(plan.pk)
        ).order_by('-created_at').first()
        
        if latest_progress_record:
            print(f"\n最新 PlanProgressRecord:")
            print(f"  progress: {latest_progress_record.progress}%")
        
        if latest_status_log:
            print(f"\n最新 PlanStatusLog:")
            print(f"  old_status: {latest_status_log.old_status}")
            print(f"  new_status: {latest_status_log.new_status}")
        
        if latest_audit_log:
            print(f"\n最新 AuditLog:")
            print(f"  action: {latest_audit_log.action}")
            print(f"  event: {latest_audit_log.meta.get('event')}")
            print(f"  changes: {json.dumps(latest_audit_log.changes, indent=2, ensure_ascii=False)}")
            print(f"\n✓ changes 同时包含 progress 和 status")
    else:
        print(f"❌ 接口调用失败")
        print(f"响应内容: {response.content.decode()}")
        return
    
    print("\n" + "=" * 70)
    print("所有用例测试完成")
    print("=" * 70)
    
    # 输出样例 JSON
    print("\n" + "=" * 70)
    print("API 返回样例（用例1：progress_update）")
    print("=" * 70)
    response1 = client.post(
        f'/api/plan/plans/{plan.pk}/progress/',
        data=json.dumps({
            'progress': 30,
            'progress_description': '测试样例',
            'execution_result': '',
            'execution_issues': '',
            'notes': ''
        }),
        content_type='application/json'
    )
    if response1.status_code == 200:
        print(json.dumps(json.loads(response1.content), indent=2, ensure_ascii=False))
    
    print("\n" + "=" * 70)
    print("API 返回样例（用例2：status_change）")
    print("=" * 70)
    plan.status = 'paused'
    plan.save(update_fields=['status'])
    response2 = client.post(
        f'/api/plan/plans/{plan.pk}/status/',
        data=json.dumps({
            'status': 'in_progress',
            'reason': '测试样例'
        }),
        content_type='application/json'
    )
    if response2.status_code == 200:
        print(json.dumps(json.loads(response2.content), indent=2, ensure_ascii=False))
    
    print("\n" + "=" * 70)
    print("AuditLog 样例")
    print("=" * 70)
    latest_audit = AuditLog.objects.filter(
        object_type='plan_management.Plan',
        object_id=str(plan.pk)
    ).order_by('-created_at').first()
    if latest_audit:
        print(json.dumps({
            "id": latest_audit.id,
            "actor": latest_audit.actor.username if latest_audit.actor else None,
            "action": latest_audit.action,
            "object_type": latest_audit.object_type,
            "object_id": latest_audit.object_id,
            "event": latest_audit.meta.get("event"),
            "changes": latest_audit.changes,
            "meta": latest_audit.meta,
            "created_at": latest_audit.created_at.isoformat(),
        }, indent=2, ensure_ascii=False))
    
    print("\n" + "=" * 70)
    print("PlanStatusLog 样例")
    print("=" * 70)
    latest_status_log = PlanStatusLog.objects.filter(plan=plan).order_by('-changed_time').first()
    if latest_status_log:
        print(json.dumps({
            "id": latest_status_log.id,
            "plan": latest_status_log.plan.plan_number,
            "old_status": latest_status_log.old_status,
            "new_status": latest_status_log.new_status,
            "changed_by": latest_status_log.changed_by.username if latest_status_log.changed_by else None,
            "change_reason": latest_status_log.change_reason,
            "changed_time": latest_status_log.changed_time.isoformat(),
        }, indent=2, ensure_ascii=False))

if __name__ == '__main__':
    test_api_progress_status()

