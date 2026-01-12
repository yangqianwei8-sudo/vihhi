#!/usr/bin/env python
"""
A3-3-6 统计 API 测试脚本
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

User = get_user_model()

def test_stats_api():
    """测试统计 API"""
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
    
    # 测试计划统计
    print("=" * 60)
    print("测试计划统计 API")
    print("=" * 60)
    
    # 1. tester1, mine=1
    response = client.get('/api/plan/stats/plans/?mine=1')
    if response.status_code == 200:
        data = json.loads(response.content)
        print("1. tester1, mine=1:")
        print(json.dumps(data, indent=2, ensure_ascii=False))
        print(f"   total={data.get('data', {}).get('total')}")
    
    # 2. 测试缓存
    print("\n2. 测试缓存:")
    r1 = client.get('/api/plan/stats/plans/?mine=1')
    d1 = json.loads(r1.content)
    print(f"   第一次: cached={d1.get('cached')}")
    
    r2 = client.get('/api/plan/stats/plans/?mine=1')
    d2 = json.loads(r2.content)
    print(f"   第二次: cached={d2.get('cached')}")
    
    r3 = client.get('/api/plan/stats/plans/?mine=1&no_cache=1')
    d3 = json.loads(r3.content)
    print(f"   no_cache=1: cached={d3.get('cached')}")
    
    # 测试目标统计
    print("\n" + "=" * 60)
    print("测试目标统计 API")
    print("=" * 60)
    
    # 1. tester1, mine=1
    response = client.get('/api/plan/stats/goals/?mine=1')
    if response.status_code == 200:
        data = json.loads(response.content)
        print("1. tester1, mine=1:")
        print(json.dumps(data, indent=2, ensure_ascii=False))
        print(f"   total={data.get('data', {}).get('total')}")
    
    # 测试 admin（超管）
    print("\n" + "=" * 60)
    print("测试 admin（超管）统计")
    print("=" * 60)
    
    admin = User.objects.filter(is_superuser=True).first()
    if admin:
        client.force_login(admin)
        
        r1 = client.get('/api/plan/stats/plans/')
        d1 = json.loads(r1.content)
        print("计划统计 (admin, 全部):")
        print(json.dumps(d1, indent=2, ensure_ascii=False))
        
        r2 = client.get('/api/plan/stats/goals/')
        d2 = json.loads(r2.content)
        print("\n目标统计 (admin, 全部):")
        print(json.dumps(d2, indent=2, ensure_ascii=False))
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)

if __name__ == '__main__':
    test_stats_api()

