#!/usr/bin/env python
"""
检查总工作台菜单与各功能模块的连接情况
"""
import os
import sys
import django

# 设置Django环境
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.config.settings')
django.setup()

from django.urls import reverse, NoReverseMatch
from backend.core.views import HOME_NAV_STRUCTURE

def check_menu_connections():
    """检查菜单连接"""
    print("=" * 80)
    print("总工作台菜单连接检查报告")
    print("=" * 80)
    print()
    
    errors = []
    warnings = []
    success_count = 0
    
    for item in HOME_NAV_STRUCTURE:
        label = item.get('label', '未知')
        icon = item.get('icon', '')
        url_name = item.get('url_name')
        permission = item.get('permission')
        
        print(f"\n【{icon} {label}】")
        print(f"  权限: {permission if permission else '无权限限制'}")
        
        if url_name and url_name != '#':
            try:
                url = reverse(url_name)
                print(f"  ✅ URL路由: {url_name} -> {url}")
                success_count += 1
            except NoReverseMatch as e:
                error_msg = f"  ❌ URL路由解析失败: {url_name}"
                print(error_msg)
                print(f"     错误: {str(e)}")
                errors.append({
                    'label': label,
                    'url_name': url_name,
                    'error': str(e)
                })
        elif url_name == '#':
            print(f"  ⚠️  URL路由: 待实现 (标记为 '#')")
            warnings.append({
                'label': label,
                'url_name': url_name
            })
        else:
            print(f"  ⚠️  URL路由: 未配置")
            warnings.append({
                'label': label,
                'url_name': None
            })
        
        # 检查子菜单
        if item.get('children'):
            print(f"  子菜单:")
            for child in item.get('children', []):
                child_label = child.get('label', '未知')
                child_icon = child.get('icon', '')
                child_url_name = child.get('url_name')
                child_permission = child.get('permission')
                
                if child_url_name and child_url_name != '#':
                    try:
                        child_url = reverse(child_url_name)
                        print(f"    ✅ {child_icon} {child_label}: {child_url_name} -> {child_url}")
                        success_count += 1
                    except NoReverseMatch as e:
                        error_msg = f"    ❌ {child_icon} {child_label}: {child_url_name}"
                        print(error_msg)
                        print(f"       错误: {str(e)}")
                        errors.append({
                            'label': f"{label} > {child_label}",
                            'url_name': child_url_name,
                            'error': str(e)
                        })
                elif child_url_name == '#':
                    print(f"    ⚠️  {child_icon} {child_label}: 待实现 (标记为 '#')")
                    warnings.append({
                        'label': f"{label} > {child_label}",
                        'url_name': child_url_name
                    })
                else:
                    print(f"    ⚠️  {child_icon} {child_label}: 未配置")
                    warnings.append({
                        'label': f"{label} > {child_label}",
                        'url_name': None
                    })
    
    # 汇总报告
    print("\n" + "=" * 80)
    print("检查结果汇总")
    print("=" * 80)
    print(f"✅ 成功连接: {success_count} 个")
    print(f"❌ 连接失败: {len(errors)} 个")
    print(f"⚠️  待实现/未配置: {len(warnings)} 个")
    print()
    
    if errors:
        print("❌ 连接失败详情:")
        for i, error in enumerate(errors, 1):
            print(f"  {i}. {error['label']}")
            print(f"     URL名称: {error['url_name']}")
            print(f"     错误: {error['error']}")
        print()
    
    if warnings:
        print("⚠️  待实现/未配置菜单项:")
        for i, warning in enumerate(warnings, 1):
            print(f"  {i}. {warning['label']}")
            if warning['url_name'] == '#':
                print(f"     状态: 已标记为待实现")
            else:
                print(f"     状态: URL未配置")
        print()
    
    # 检查报表管理模块路由是否存在
    print("=" * 80)
    print("特殊检查: 报表管理模块")
    print("=" * 80)
    report_urls = [
        'report_pages:report_list',
    ]
    
    for url_name in report_urls:
        try:
            url = reverse(url_name)
            print(f"✅ {url_name} -> {url}")
        except NoReverseMatch as e:
            print(f"❌ {url_name} - 路由不存在")
            print(f"   说明: 报表管理模块可能尚未实现或未在urls.py中配置")
            print(f"   建议: 检查 backend/config/urls.py 是否包含报表管理模块的路由配置")
    
    print()
    print("=" * 80)
    
    return len(errors) == 0

if __name__ == '__main__':
    try:
        success = check_menu_connections()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ 检查过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)



