#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试菜单排序功能
"""
import os
import sys
import django

# 设置Django环境
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from config.admin_menu_config import MAIN_MENU_ITEMS, build_menu_structure
from django.contrib import admin

print("=" * 60)
print("测试菜单排序功能")
print("=" * 60)

print("\n1. 检查 MAIN_MENU_ITEMS 的排序:")
for i, item in enumerate(MAIN_MENU_ITEMS, 1):
    print(f"   {i}. {item['label']} (path: {item['path']})")

print("\n2. 检查是否有 pypinyin 库:")
try:
    from pypinyin import lazy_pinyin, Style
    print("   ✓ pypinyin 已安装")
    
    # 测试排序
    test_labels = [item['label'] for item in MAIN_MENU_ITEMS[:5]]
    print(f"\n3. 测试前5个菜单项的拼音:")
    for label in test_labels:
        pinyin = ''.join(lazy_pinyin(label, style=Style.FIRST_LETTER)).lower()
        print(f"   {label} -> {pinyin}")
except ImportError:
    print("   ✗ pypinyin 未安装")

print("\n4. 测试 build_menu_structure 返回的顺序:")
try:
    # 模拟一个简单的 app_list
    app_list = admin.site.get_app_list(None)
    if app_list:
        menu_structure = build_menu_structure(app_list)
        print(f"   菜单结构中的主菜单顺序:")
        for i, (menu_path, sub_menus) in enumerate(menu_structure.items(), 1):
            print(f"   {i}. {menu_path}")
    else:
        print("   无法获取 app_list")
except Exception as e:
    print(f"   错误: {e}")

print("\n" + "=" * 60)

