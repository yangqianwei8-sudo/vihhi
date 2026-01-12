#!/usr/bin/env python
"""
模拟真实视图函数调用链来获取权限兜底放行日志
模拟调用链：plan_management.views_pages -> require_perm -> has_perm2 -> has_business_perm
"""
import sys
import os
import django

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.config.settings')
django.setup()

import logging
from io import StringIO
from backend.core.permissions import require_perm
from backend.apps.system_management.models import User

# 配置日志捕获
log_stream = StringIO()
handler = logging.StreamHandler(log_stream)
handler.setLevel(logging.INFO)
perm_logger = logging.getLogger('backend.core.permissions')
perm_logger.addHandler(handler)
perm_logger.setLevel(logging.INFO)
perm_logger.propagate = False

# 模拟 plan_management.views_pages 中的调用
def simulate_view_function():
    """模拟 plan_management.views_pages.plan_management_home 中的权限检查"""
    user = User.objects.filter(is_active=True).first()
    if not user:
        print("错误：没有找到测试用户")
        return
    
    print(f"模拟视图函数调用: plan_management.views_pages.plan_management_home")
    print(f"测试用户: {user.username} (ID: {user.id})")
    print(f"权限检查: plan_management.view_plan")
    print()
    
    try:
        # 模拟视图函数中的权限检查
        require_perm(user, "plan_management.view_plan")
        print("权限检查通过")
    except Exception as e:
        print(f"权限检查失败: {e}")
    
    print()
    print("="*80)
    print("真实权限兜底放行日志样例:")
    print("="*80)
    
    # 输出捕获的日志
    log_contents = log_stream.getvalue()
    if log_contents:
        for line in log_contents.strip().split('\n'):
            if '权限兜底放行' in line:
                print(line)
                print()
                print("✅ 找到真实日志样例！")
                print()
                # 验证 caller_module
                if 'caller_module=' in line:
                    if 'plan_management' in line or 'backend.apps' in line:
                        print("✅ caller_module 正确显示业务模块")
                    elif 'django.core.management' in line:
                        print("⚠️ caller_module 显示为 Django shell，需要通过真实页面访问验证")
                    else:
                        print(f"⚠️ caller_module: {line.split('caller_module=')[1].split(',')[0] if 'caller_module=' in line else 'unknown'}")
                break
        else:
            print("（未找到权限兜底放行日志）")
            print("完整日志输出：")
            print(log_contents)
    else:
        print("（未捕获到日志）")
    
    print("="*80)

if __name__ == '__main__':
    simulate_view_function()

