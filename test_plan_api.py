#!/usr/bin/env python
"""
A3-1 API 自测脚本
使用 Django test client 模拟登录和 API 调用
"""
import os
import sys
import django
import json

# 设置 Django 环境
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.config.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from backend.apps.plan_management.models import Plan, StrategicGoal

User = get_user_model()

def test_api():
    """测试 API 接口"""
    client = Client(enforce_csrf_checks=False)
    # 设置正确的 host
    client.defaults['HTTP_HOST'] = 'localhost'
    
    # 1. 登录 tester1
    print("=" * 60)
    print("1. 登录 tester1")
    print("=" * 60)
    login_response = client.post('/api/system/users/login/', {
        'username': 'tester1',
        'password': '123456'
    })
    print(f"登录状态码: {login_response.status_code}")
    if login_response.status_code == 200:
        print("✓ 登录成功")
        login_data = json.loads(login_response.content)
        print(f"用户信息: {login_data.get('user', {}).get('username')}")
    else:
        print(f"✗ 登录失败: {login_response.content}")
        return
    
    # 2. 测试目标列表
    print("\n" + "=" * 60)
    print("2. 测试目标列表 (GET /api/plan/strategic-goals/)")
    print("=" * 60)
    goals_response = client.get('/api/plan/strategic-goals/')
    print(f"状态码: {goals_response.status_code}")
    if goals_response.status_code == 200:
        goals_data = json.loads(goals_response.content)
        print(f"✓ 成功获取目标列表")
        print(f"总数: {goals_data.get('count', len(goals_data.get('results', [])))}")
        if goals_data.get('results'):
            first_goal = goals_data['results'][0]
            print(f"第一个目标: {first_goal.get('goal_number')} - {first_goal.get('indicator_name')}")
            print(f"  company: {first_goal.get('company')}")
            print(f"  org_department: {first_goal.get('org_department')}")
    else:
        print(f"✗ 获取失败: {goals_response.content}")
    
    # 3. 测试计划列表
    print("\n" + "=" * 60)
    print("3. 测试计划列表 (GET /api/plan/plans/)")
    print("=" * 60)
    plans_response = client.get('/api/plan/plans/')
    print(f"状态码: {plans_response.status_code}")
    if plans_response.status_code == 200:
        plans_data = json.loads(plans_response.content)
        print(f"✓ 成功获取计划列表")
        print(f"总数: {plans_data.get('count', len(plans_data.get('results', [])))}")
        if plans_data.get('results'):
            first_plan = plans_data['results'][0]
            print(f"第一个计划: {first_plan.get('plan_number')} - {first_plan.get('name')}")
            print(f"  company: {first_plan.get('company')}")
            print(f"  org_department: {first_plan.get('org_department')}")
    else:
        print(f"✗ 获取失败: {plans_response.content}")
    
    # 4. 创建目标（不传 company/org_department）
    print("\n" + "=" * 60)
    print("4. 创建目标 (POST /api/plan/strategic-goals/) - 不传 company/org_department")
    print("=" * 60)
    tester = User.objects.get(username='tester1')
    create_goal_data = {
        'goal_type': 'personal',
        'goal_period': 'annual',
        'indicator_name': 'A3联调目标',
        'indicator_type': 'numeric',
        'indicator_unit': '次',
        'target_value': '10',
        'current_value': '0',
        'status': 'draft',
        'responsible_person': tester.id,
        'created_by': tester.id
    }
    create_goal_response = client.post(
        '/api/plan/strategic-goals/',
        json.dumps(create_goal_data),
        content_type='application/json'
    )
    print(f"状态码: {create_goal_response.status_code}")
    if create_goal_response.status_code in [200, 201]:
        goal_data = json.loads(create_goal_response.content)
        print("✓ 创建目标成功")
        print(f"目标ID: {goal_data.get('id')}")
        print(f"目标编号: {goal_data.get('goal_number')}")
        print(f"company: {goal_data.get('company')}")
        print(f"org_department: {goal_data.get('org_department')}")
        goal_id = goal_data.get('id')
    else:
        print(f"✗ 创建失败: {create_goal_response.content}")
        goal_id = None
    
    # 5. 创建计划（关联目标）
    if goal_id:
        print("\n" + "=" * 60)
        print("5. 创建计划 (POST /api/plan/plans/) - 关联目标")
        print("=" * 60)
        create_plan_data = {
            'name': 'A3联调计划',
            'plan_type': 'personal',
            'plan_period': 'weekly',
            'status': 'draft',
            'related_goal': goal_id,
            'content': '联调用',
            'plan_objective': '把计划模块跑通',
            'start_time': '2026-01-08T09:00:00+08:00',
            'end_time': '2026-01-15T18:00:00+08:00',
            'responsible_person': tester.id,
            'created_by': tester.id,
            'progress': '0'
        }
        create_plan_response = client.post(
            '/api/plan/plans/',
            json.dumps(create_plan_data),
            content_type='application/json'
        )
        print(f"状态码: {create_plan_response.status_code}")
        if create_plan_response.status_code in [200, 201]:
            plan_data = json.loads(create_plan_response.content)
            print("✓ 创建计划成功")
            print(f"计划ID: {plan_data.get('id')}")
            print(f"计划编号: {plan_data.get('plan_number')}")
            print(f"company: {plan_data.get('company')}")
            print(f"org_department: {plan_data.get('org_department')}")
            print(f"duration_days: {plan_data.get('duration_days')}")
            plan_id = plan_data.get('id')
        else:
            print(f"✗ 创建失败: {create_plan_response.content}")
            plan_id = None
        
        # 6. 验证普通用户禁止改归属
        if plan_id:
            print("\n" + "=" * 60)
            print("6. 验证禁止修改归属 (PATCH /api/plan/plans/{id}/) - 尝试改 company")
            print("=" * 60)
            # 获取一个不同的 company ID（如果有的话）
            from backend.apps.org.models import Company
            companies = Company.objects.all()
            if companies.count() > 1:
                other_company_id = companies.exclude(code='VIHHI').first().id
            else:
                other_company_id = 999  # 不存在的 ID
            
            patch_data = {'company': other_company_id}
            patch_response = client.patch(
                f'/api/plan/plans/{plan_id}/',
                json.dumps(patch_data),
                content_type='application/json'
            )
            print(f"状态码: {patch_response.status_code}")
            if patch_response.status_code == 403:
                print("✓ 正确拒绝修改归属（403 Forbidden）")
                error_data = json.loads(patch_response.content)
                print(f"错误信息: {error_data}")
            elif patch_response.status_code == 400:
                print("✓ 正确拒绝修改归属（400 Bad Request）")
                error_data = json.loads(patch_response.content)
                print(f"错误信息: {error_data}")
            else:
                print(f"✗ 未正确拒绝（应该返回 403 或 400）")
                print(f"响应: {patch_response.content}")
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)

if __name__ == '__main__':
    test_api()

