#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
检查菜单排序功能
"""
import os
import sys
import django

# 设置Django环境
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
project_dir = os.path.dirname(backend_dir)
sys.path.insert(0, project_dir)
os.chdir(project_dir)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from config.admin_menu_config import MAIN_MENU_ITEMS, build_menu_structure
from django.contrib import admin
from django.test import RequestFactory
from django.contrib.auth.models import AnonymousUser

print("=" * 70)
print("菜单排序功能检查")
print("=" * 70)

# 1. 检查 pypinyin
print("\n1. 检查 pypinyin 库:")
try:
    from pypinyin import lazy_pinyin, Style
    print("   ✓ pypinyin 已安装")
    pypinyin_available = True
except ImportError:
    print("   ✗ pypinyin 未安装")
    pypinyin_available = False

# 2. 检查 MAIN_MENU_ITEMS 的排序
print("\n2. MAIN_MENU_ITEMS 的排序:")
print("   " + "-" * 66)
for i, item in enumerate(MAIN_MENU_ITEMS, 1):
    label = item['label']
    if pypinyin_available:
        try:
            pinyin = ''.join(lazy_pinyin(label, style=Style.FIRST_LETTER)).lower()
            print(f"   {i:2d}. {label:15s} (拼音首字母: {pinyin})")
        except:
            print(f"   {i:2d}. {label:15s}")
    else:
        print(f"   {i:2d}. {label:15s} (order: {item.get('order', 'N/A')})")

# 3. 检查菜单结构的顺序
print("\n3. 菜单结构中的主菜单顺序:")
print("   " + "-" * 66)
try:
    factory = RequestFactory()
    request = factory.get('/admin/')
    request.user = AnonymousUser()
    
    app_list = admin.site.get_app_list(request)
    if app_list:
        menu_structure = build_menu_structure(app_list)
        for i, (menu_path, sub_menus) in enumerate(menu_structure.items(), 1):
            sub_count = len(sub_menus)
            model_count = sum(len(models) for models in sub_menus.values())
            print(f"   {i:2d}. {menu_path:15s} (子菜单: {sub_count}, 模型: {model_count})")
    else:
        print("   ✗ 无法获取 app_list")
except Exception as e:
    print(f"   ✗ 错误: {e}")
    import traceback
    traceback.print_exc()

# 4. 验证排序是否正确
print("\n4. 排序验证:")
print("   " + "-" * 66)
if pypinyin_available:
    # 检查首页是否在第一位
    if MAIN_MENU_ITEMS[0]['label'] == '首页':
        print("   ✓ 首页在第一位")
    else:
        print(f"   ✗ 首页不在第一位，第一位是: {MAIN_MENU_ITEMS[0]['label']}")
    
    # 检查其他菜单是否按拼音排序
    other_items = [item for item in MAIN_MENU_ITEMS if item['label'] != '首页']
    if len(other_items) > 1:
        pinyin_list = [''.join(lazy_pinyin(item['label'], style=Style.FIRST_LETTER)).lower() 
                      for item in other_items]
        is_sorted = pinyin_list == sorted(pinyin_list)
        if is_sorted:
            print("   ✓ 其他菜单按拼音排序正确")
        else:
            print("   ✗ 其他菜单未按拼音排序")
            print(f"      期望顺序: {sorted(pinyin_list)}")
            print(f"      实际顺序: {pinyin_list}")
else:
    print("   ⚠ pypinyin 未安装，使用 order 字段排序")

print("\n" + "=" * 70)

