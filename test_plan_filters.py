#!/usr/bin/env python
"""
A3-3-1 过滤功能测试脚本
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
from backend.apps.plan_management.models import Plan, StrategicGoal

User = get_user_model()

def test_filters():
    """测试过滤功能"""
    client = Client(enforce_csrf_checks=False)
    client.defaults['HTTP_HOST'] = 'localhost'
    
    # 登录 tester1
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
    
    tester = User.objects.get(username='tester1')
    
    # 测试计划列表过滤
    print("=" * 60)
    print("测试计划列表过滤")
    print("=" * 60)
    
    # 1. 全部计划
    response = client.get('/api/plan/plans/')
    if response.status_code == 200:
        data = json.loads(response.content)
        total = data.get('count', len(data.get('results', [])))
        print(f"1. 全部计划: {total} 条")
    
    # 2. 只看我负责
    response = client.get('/api/plan/plans/?mine=1')
    if response.status_code == 200:
        data = json.loads(response.content)
        count = data.get('count', len(data.get('results', [])))
        print(f"2. 只看我负责 (mine=1): {count} 条")
    
    # 3. 只看我参与
    response = client.get('/api/plan/plans/?participating=1')
    if response.status_code == 200:
        data = json.loads(response.content)
        count = data.get('count', len(data.get('results', [])))
        print(f"3. 只看我参与 (participating=1): {count} 条")
    
    # 4. 只看逾期
    response = client.get('/api/plan/plans/?overdue=1')
    if response.status_code == 200:
        data = json.loads(response.content)
        count = data.get('count', len(data.get('results', [])))
        print(f"4. 只看逾期 (overdue=1): {count} 条")
    
    # 5. 本周
    response = client.get('/api/plan/plans/?range=week')
    if response.status_code == 200:
        data = json.loads(response.content)
        count = data.get('count', len(data.get('results', [])))
        print(f"5. 本周 (range=week): {count} 条")
    
    # 6. 本月
    response = client.get('/api/plan/plans/?range=month')
    if response.status_code == 200:
        data = json.loads(response.content)
        count = data.get('count', len(data.get('results', [])))
        print(f"6. 本月 (range=month): {count} 条")
    
    # 测试目标列表过滤
    print("\n" + "=" * 60)
    print("测试目标列表过滤")
    print("=" * 60)
    
    # 1. 全部目标
    response = client.get('/api/plan/strategic-goals/')
    if response.status_code == 200:
        data = json.loads(response.content)
        total = data.get('count', len(data.get('results', [])))
        print(f"1. 全部目标: {total} 条")
    
    # 2. 只看我负责
    response = client.get('/api/plan/strategic-goals/?mine=1')
    if response.status_code == 200:
        data = json.loads(response.content)
        count = data.get('count', len(data.get('results', [])))
        print(f"2. 只看我负责 (mine=1): {count} 条")
    
    # 3. 只看我参与
    response = client.get('/api/plan/strategic-goals/?participating=1')
    if response.status_code == 200:
        data = json.loads(response.content)
        count = data.get('count', len(data.get('results', [])))
        print(f"3. 只看我参与 (participating=1): {count} 条")
    
    # 4. 本周
    response = client.get('/api/plan/strategic-goals/?range=week')
    if response.status_code == 200:
        data = json.loads(response.content)
        count = data.get('count', len(data.get('results', [])))
        print(f"4. 本周 (range=week): {count} 条")
    
    # 5. 本月
    response = client.get('/api/plan/strategic-goals/?range=month')
    if response.status_code == 200:
        data = json.loads(response.content)
        count = data.get('count', len(data.get('results', [])))
        print(f"5. 本月 (range=month): {count} 条")
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)

if __name__ == '__main__':
    test_filters()

