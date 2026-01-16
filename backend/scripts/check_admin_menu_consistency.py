#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
检查Admin菜单配置的一致性和完整性
"""

import os
import sys
import django

# 设置Django环境
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from django.contrib import admin
from django.apps import apps
from backend.config.admin_menu_config import MENU_MAPPING, MAIN_MENU_ITEMS, MENU_URL_MAPPING, get_menu_path_for_model

def get_all_registered_models():
    """获取所有已注册的Admin模型"""
    registered = []
    for model in apps.get_models():
        if model in admin.site._registry:
            registered.append({
                'app_label': model._meta.app_label,
                'model_name': model.__name__,
                'verbose_name': model._meta.verbose_name,
            })
    return sorted(registered, key=lambda x: (x['app_label'], x['model_name']))

def check_menu_coverage():
    """检查菜单配置是否覆盖了所有已注册的模型"""
    registered_models = get_all_registered_models()
    missing_models = []
    covered_models = []
    
    for model in registered_models:
        app_label = model['app_label']
        model_name = model['model_name']
        
        menu_path = get_menu_path_for_model(app_label, model_name)
        
        if menu_path is None:
            missing_models.append(model)
        else:
            covered_models.append({
                **model,
                'menu_path': menu_path
            })
    
    return {
        'registered': registered_models,
        'covered': covered_models,
        'missing': missing_models,
    }

def check_menu_url_mapping():
    """检查菜单URL映射的完整性"""
    main_menu_labels = {item['path'] for item in MAIN_MENU_ITEMS}
    url_mapping_keys = set(MENU_URL_MAPPING.keys())
    
    missing_urls = main_menu_labels - url_mapping_keys
    extra_urls = url_mapping_keys - main_menu_labels
    
    return {
        'main_menus': main_menu_labels,
        'url_mappings': url_mapping_keys,
        'missing_urls': missing_urls,
        'extra_urls': extra_urls,
    }

def check_menu_structure():
    """检查菜单结构的完整性"""
    issues = []
    
    # 检查主菜单项是否都有URL映射
    for menu_item in MAIN_MENU_ITEMS:
        menu_path = menu_item.get('path', '')
        if menu_path and menu_path not in MENU_URL_MAPPING:
            issues.append(f"主菜单 '{menu_path}' 没有URL映射")
    
    # 检查URL映射是否都有对应的主菜单项
    for menu_path in MENU_URL_MAPPING.keys():
        if not any(item.get('path') == menu_path for item in MAIN_MENU_ITEMS):
            issues.append(f"URL映射 '{menu_path}' 没有对应的主菜单项")
    
    return issues

def main():
    print("=" * 80)
    print("Admin菜单配置一致性检查")
    print("=" * 80)
    print()
    
    # 1. 检查已注册模型
    print("1. 已注册的Admin模型统计")
    print("-" * 80)
    registered_models = get_all_registered_models()
    print(f"总模型数: {len(registered_models)}")
    
    # 按应用分组统计
    app_counts = {}
    for model in registered_models:
        app_label = model['app_label']
        app_counts[app_label] = app_counts.get(app_label, 0) + 1
    
    print("\n按应用分组:")
    for app_label, count in sorted(app_counts.items()):
        print(f"  {app_label}: {count} 个模型")
    print()
    
    # 2. 检查菜单覆盖
    print("2. 菜单配置覆盖检查")
    print("-" * 80)
    coverage = check_menu_coverage()
    print(f"已覆盖模型: {len(coverage['covered'])}")
    print(f"未覆盖模型: {len(coverage['missing'])}")
    
    if coverage['missing']:
        print("\n⚠️  未配置菜单的模型:")
        for model in coverage['missing']:
            print(f"  - {model['app_label']}.{model['model_name']} ({model['verbose_name']})")
    else:
        print("\n✅ 所有模型都已配置菜单")
    print()
    
    # 3. 检查菜单URL映射
    print("3. 菜单URL映射检查")
    print("-" * 80)
    url_check = check_menu_url_mapping()
    print(f"主菜单数: {len(url_check['main_menus'])}")
    print(f"URL映射数: {len(url_check['url_mappings'])}")
    
    if url_check['missing_urls']:
        print(f"\n⚠️  缺少URL映射的主菜单 ({len(url_check['missing_urls'])}):")
        for menu in sorted(url_check['missing_urls']):
            print(f"  - {menu}")
    else:
        print("\n✅ 所有主菜单都有URL映射")
    
    if url_check['extra_urls']:
        print(f"\n⚠️  多余的URL映射 ({len(url_check['extra_urls'])}):")
        for menu in sorted(url_check['extra_urls']):
            print(f"  - {menu}")
    print()
    
    # 4. 检查菜单结构
    print("4. 菜单结构完整性检查")
    print("-" * 80)
    structure_issues = check_menu_structure()
    if structure_issues:
        print(f"⚠️  发现 {len(structure_issues)} 个问题:")
        for issue in structure_issues:
            print(f"  - {issue}")
    else:
        print("✅ 菜单结构完整")
    print()
    
    # 5. 按菜单路径分组显示模型
    print("5. 按菜单路径分组的模型")
    print("-" * 80)
    menu_groups = {}
    for model in coverage['covered']:
        menu_path = model['menu_path']
        if menu_path not in menu_groups:
            menu_groups[menu_path] = []
        menu_groups[menu_path].append(model)
    
    for menu_path in sorted(menu_groups.keys()):
        models = menu_groups[menu_path]
        print(f"\n{menu_path} ({len(models)} 个模型):")
        for model in sorted(models, key=lambda x: x['model_name']):
            print(f"  - {model['app_label']}.{model['model_name']}")
    print()
    
    # 总结
    print("=" * 80)
    print("检查总结")
    print("=" * 80)
    total_issues = len(coverage['missing']) + len(url_check['missing_urls']) + len(url_check['extra_urls']) + len(structure_issues)
    
    if total_issues == 0:
        print("✅ 所有检查通过！菜单配置完整且一致。")
    else:
        print(f"⚠️  发现 {total_issues} 个问题需要修复:")
        if coverage['missing']:
            print(f"  - {len(coverage['missing'])} 个模型未配置菜单")
        if url_check['missing_urls']:
            print(f"  - {len(url_check['missing_urls'])} 个主菜单缺少URL映射")
        if url_check['extra_urls']:
            print(f"  - {len(url_check['extra_urls'])} 个多余的URL映射")
        if structure_issues:
            print(f"  - {len(structure_issues)} 个菜单结构问题")
    print()

if __name__ == '__main__':
    main()

