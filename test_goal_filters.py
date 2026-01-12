#!/usr/bin/env python
"""
A3-3-3 目标列表筛选功能测试脚本
"""
import os
import sys
import django

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.config.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model

User = get_user_model()

def test_goal_filters():
    """测试目标列表筛选功能"""
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
    
    # 测试目标列表筛选
    print("=" * 60)
    print("测试目标列表筛选（页面视图）")
    print("=" * 60)
    
    # 1. 默认（mine=1）
    response = client.get('/plan/strategic-goals/')
    if response.status_code == 200:
        # 从响应中提取目标数量（需要解析 HTML 或检查 context）
        print("1. 默认（mine=1）: 页面加载成功")
        # 实际数量需要从页面内容或 context 中提取
    else:
        print(f"1. 默认（mine=1）: 状态码 {response.status_code}")
    
    # 2. 明确指定 mine=1
    response = client.get('/plan/strategic-goals/?mine=1')
    print(f"2. 只看我负责 (mine=1): 状态码 {response.status_code}")
    
    # 3. 关闭 mine（全部）
    response = client.get('/plan/strategic-goals/?mine=0')
    print(f"3. 全部目标 (mine=0): 状态码 {response.status_code}")
    
    # 4. 只看我参与
    response = client.get('/plan/strategic-goals/?participating=1')
    print(f"4. 只看我参与 (participating=1): 状态码 {response.status_code}")
    
    # 5. 本周
    response = client.get('/plan/strategic-goals/?range=week')
    print(f"5. 本周 (range=week): 状态码 {response.status_code}")
    
    # 6. 本月
    response = client.get('/plan/strategic-goals/?range=month')
    print(f"6. 本月 (range=month): 状态码 {response.status_code}")
    
    # 使用 API 测试（更准确）
    print("\n" + "=" * 60)
    print("测试目标列表筛选（API 视图）")
    print("=" * 60)
    
    # 1. 全部目标
    response = client.get('/api/plan/strategic-goals/')
    if response.status_code == 200:
        import json
        data = json.loads(response.content)
        total = data.get('count', len(data.get('results', [])))
        print(f"1. 全部目标: {total} 条")
    
    # 2. 只看我负责
    response = client.get('/api/plan/strategic-goals/?mine=1')
    if response.status_code == 200:
        import json
        data = json.loads(response.content)
        count = data.get('count', len(data.get('results', [])))
        print(f"2. 只看我负责 (mine=1): {count} 条")
    
    # 3. 只看我参与
    response = client.get('/api/plan/strategic-goals/?participating=1')
    if response.status_code == 200:
        import json
        data = json.loads(response.content)
        count = data.get('count', len(data.get('results', [])))
        print(f"3. 只看我参与 (participating=1): {count} 条")
    
    # 4. 本周
    response = client.get('/api/plan/strategic-goals/?range=week')
    if response.status_code == 200:
        import json
        data = json.loads(response.content)
        count = data.get('count', len(data.get('results', [])))
        print(f"4. 本周 (range=week): {count} 条")
    
    # 5. 本月
    response = client.get('/api/plan/strategic-goals/?range=month')
    if response.status_code == 200:
        import json
        data = json.loads(response.content)
        count = data.get('count', len(data.get('results', [])))
        print(f"5. 本月 (range=month): {count} 条")
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)

if __name__ == '__main__':
    test_goal_filters()

