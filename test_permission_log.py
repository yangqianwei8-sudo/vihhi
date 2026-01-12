#!/usr/bin/env python
"""
测试权限兜底日志 - 用于获取真实日志样例
使用方法：python manage.py shell < test_permission_log.py
"""
import logging
import sys
from io import StringIO

# 配置日志捕获
log_capture = StringIO()
handler = logging.StreamHandler(log_capture)
handler.setLevel(logging.INFO)
logger = logging.getLogger('backend.core.permissions')
logger.addHandler(handler)
logger.setLevel(logging.INFO)

# 导入权限检查函数
from backend.core.permissions import has_business_perm
from backend.apps.system_management.models import User

# 获取一个测试用户（需要有业务权限）
try:
    # 尝试获取一个有 __all__ 权限或业务权限的用户
    user = User.objects.filter(is_active=True).first()
    if not user:
        print("错误：没有找到测试用户")
        sys.exit(1)
    
    print(f"测试用户: {user.username} (ID: {user.id})")
    print("正在测试权限检查...")
    
    # 触发权限检查（模拟 plan_management.views_pages 中的调用）
    perm_codename = "plan_management.view_plan"
    result = has_business_perm(user, perm_codename)
    
    print(f"权限检查结果: {result}")
    print("\n" + "="*80)
    print("捕获的日志输出:")
    print("="*80)
    
    # 输出捕获的日志
    log_contents = log_capture.getvalue()
    if log_contents:
        print(log_contents)
    else:
        print("（未捕获到日志，可能需要检查日志配置）")
    
    print("="*80)
    
except Exception as e:
    print(f"错误: {e}")
    import traceback
    traceback.print_exc()

