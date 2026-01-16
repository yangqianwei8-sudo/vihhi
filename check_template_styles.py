#!/usr/bin/env python3
"""
验证共享模板和基础模板的样式一致性

使用方法：
    python3 check_template_styles.py
"""

import re
import sys

def extract_css_properties(css_content, selector):
    """提取指定选择器的CSS属性"""
    pattern = rf'{re.escape(selector)}\s*\{{([^}}]+)\}}'
    matches = re.findall(pattern, css_content, re.DOTALL)
    if matches:
        return matches[0]
    return None

def check_required_properties(css_content, selector, required_props):
    """检查必需的CSS属性是否存在"""
    props = extract_css_properties(css_content, selector)
    if not props:
        return False, f"选择器 {selector} 不存在"
    
    missing = []
    for prop in required_props:
        if prop not in props:
            missing.append(prop)
    
    if missing:
        return False, f"缺少属性: {', '.join(missing)}"
    return True, "OK"

def main():
    print("=== 检查模板样式一致性 ===
")
    
    # 读取文件
    try:
        with open('backend/templates/shared/_partials/_shared_form_wrapper_customer.html', 'r', encoding='utf-8') as f:
            shared_content = f.read()
        
        with open('backend/templates/customer_management/_base.html', 'r', encoding='utf-8') as f:
            base_content = f.read()
    except FileNotFoundError as e:
        print(f"❌ 文件未找到: {e}")
        return 1
    
    # 检查必需的样式
    checks = [
        ('.pm-page-header::after', ['content', 'position', 'background-color']),
        ('.pm-page-header .pm-page-header-title-wrapper h1', ['font-size: 24px']),
        ('.pm-page-header .pm-page-header-title-wrapper .pm-subtitle', ['font-size: 12px']),
        ('.pm-page-header .pm-actions', ['align-self: flex-end']),
    ]
    
    all_ok = True
    for selector, required in checks:
        # 检查共享模板
        ok, msg = check_required_properties(shared_content, selector, required)
        if not ok:
            print(f"❌ 共享模板 {selector}: {msg}")
            all_ok = False
        else:
            print(f"✓ 共享模板 {selector}: {msg}")
        
        # 检查基础模板
        ok, msg = check_required_properties(base_content, selector, required)
        if not ok:
            print(f"❌ 基础模板 {selector}: {msg}")
            all_ok = False
        else:
            print(f"✓ 基础模板 {selector}: {msg}")
    
    print()
    if all_ok:
        print("✅ 所有样式检查通过")
        return 0
    else:
        print("❌ 发现样式不一致，请修复")
        return 1

if __name__ == '__main__':
    sys.exit(main())
