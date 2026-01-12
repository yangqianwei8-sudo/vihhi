#!/usr/bin/env python
"""
A3-3-7 筛选口径一致性测试
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

def test_consistency():
    """测试列表与统计的一致性"""
    client = Client(enforce_csrf_checks=False)
    client.defaults['HTTP_HOST'] = 'localhost'
    
    # 登录 tester1
    login_response = client.post('/api/system/users/login/', {
        'username': 'tester1',
        'password': '123456'
    })
    if login_response.status_code != 200:
        print(f"登录失败: {login_response.status_code}")
        return
    
    print("=" * 70)
    print("A3-3-7 筛选口径一致性测试")
    print("=" * 70)
    
    test_cases = [
        # (描述, plans_url, goals_url)
        ("mine=1", "?mine=1", "?mine=1"),
        ("mine=1&range=week", "?mine=1&range=week", "?mine=1&range=week"),
        ("mine=1&range=month", "?mine=1&range=month", "?mine=1&range=month"),
        ("mine=1&participating=1", "?mine=1&participating=1", "?mine=1&participating=1"),
        ("mine=1&overdue=1", "?mine=1&overdue=1", None),  # goals 不支持 overdue
    ]
    
    for desc, plans_params, goals_params in test_cases:
        print(f"\n测试: {desc}")
        print("-" * 70)
        
        # 测试计划（强制刷新缓存）
        r1 = client.get(f'/api/plan/plans/{plans_params}')
        d1 = json.loads(r1.content)
        count1 = d1.get('count', len(d1.get('results', []))) if 'count' in d1 else len(d1.get('results', []))
        
        stats_params = f'{plans_params}&no_cache=1' if plans_params else '?no_cache=1'
        r2 = client.get(f'/api/plan/stats/plans/{stats_params}')
        d2 = json.loads(r2.content)
        total2 = d2.get('data', {}).get('total', 0)
        
        match1 = "✓" if count1 == total2 else "✗"
        print(f"  计划列表: {count1} | 统计 total: {total2} | {match1}")
        if count1 != total2:
            print(f"    ⚠️  不一致！")
        
        # 测试目标（如果有参数，强制刷新缓存）
        if goals_params:
            r3 = client.get(f'/api/plan/strategic-goals/{goals_params}')
            d3 = json.loads(r3.content)
            count3 = d3.get('count', len(d3.get('results', []))) if 'count' in d3 else len(d3.get('results', []))
            
            stats_params = f'{goals_params}&no_cache=1' if goals_params else '?no_cache=1'
            r4 = client.get(f'/api/plan/stats/goals/{stats_params}')
            d4 = json.loads(r4.content)
            total4 = d4.get('data', {}).get('total', 0)
            
            match2 = "✓" if count3 == total4 else "✗"
            print(f"  目标列表: {count3} | 统计 total: {total4} | {match2}")
            if count3 != total4:
                print(f"    ⚠️  不一致！")
    
    print("\n" + "=" * 70)
    print("测试完成")
    print("=" * 70)

if __name__ == '__main__':
    test_consistency()

