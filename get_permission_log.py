#!/usr/bin/env python
"""
快速获取权限兜底放行真实日志样例
使用方法：python manage.py shell < get_permission_log.py
"""
import sys
import os
import django

# 设置 Django 环境
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.config.settings')
django.setup()

import logging
from io import StringIO
from backend.core.permissions import has_business_perm
from backend.apps.system_management.models import User

# 配置日志捕获到内存
log_stream = StringIO()
handler = logging.StreamHandler(log_stream)
handler.setLevel(logging.INFO)

# 获取权限日志的 logger
perm_logger = logging.getLogger('backend.core.permissions')
perm_logger.addHandler(handler)
perm_logger.setLevel(logging.INFO)
perm_logger.propagate = False  # 防止传播到 root logger

print("="*80)
print("正在测试权限兜底放行日志...")
print("="*80)

# 获取一个测试用户
try:
    user = User.objects.filter(is_active=True).first()
    if not user:
        print("错误：没有找到测试用户")
        sys.exit(1)
    
    print(f"测试用户: {user.username} (ID: {user.id})")
    print(f"正在测试权限检查: plan_management.view_plan")
    print()
    
    # 触发权限检查（模拟 plan_management.views_pages 中的调用）
    perm_codename = "plan_management.view_plan"
    result = has_business_perm(user, perm_codename)
    
    print(f"权限检查结果: {result}")
    print()
    print("="*80)
    print("捕获的权限兜底放行日志:")
    print("="*80)
    
    # 输出捕获的日志
    log_contents = log_stream.getvalue()
    if log_contents:
        # 查找包含"权限兜底放行"的行
        for line in log_contents.strip().split('\n'):
            if '权限兜底放行' in line:
                print(line)
                print()
                print("✅ 找到真实日志样例！")
                break
        else:
            print("（未找到权限兜底放行日志，可能需要检查用户权限配置）")
            print("完整日志输出：")
            print(log_contents)
    else:
        print("（未捕获到日志）")
        print("提示：请确保用户有业务权限（__all__ 或 plan_management.view）")
    
    print("="*80)
    
except Exception as e:
    print(f"错误: {e}")
    import traceback
    traceback.print_exc()

