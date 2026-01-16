#!/usr/bin/env python
"""检查permission_management应用是否正确安装"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.config.settings')
django.setup()

from django.apps import apps

try:
    app = apps.get_app_config('permission_management')
    print(f'✓ permission_management 应用已安装: {app.name}')
    print(f'  路径: {app.path}')
    print(f'  标签: {app.label}')
except LookupError as e:
    print(f'✗ permission_management 应用未找到: {e}')

# 检查所有已安装的应用
print('\n已安装的应用:')
for app_config in apps.get_app_configs():
    if 'permission' in app_config.label.lower():
        print(f'  - {app_config.label}: {app_config.name}')

