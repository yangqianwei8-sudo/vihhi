#!/usr/bin/env python3
"""
自动集成服务信息表格模块到 contract_form.html
使用方法: python3 integrate_service_table.py
"""

import re
import sys
import os
from pathlib import Path

# 文件路径
BASE_DIR = Path(__file__).parent.parent.parent
TEMPLATE_FILE = BASE_DIR / 'templates' / 'customer_management' / 'contract_form.html'
BACKUP_FILE = BASE_DIR / 'templates' / 'customer_management' / 'contract_form.html.backup_before_integration'
DYNAMIC_TABLE_JS = BASE_DIR / 'static' / 'js' / 'dynamic-table.js'
INTEGRATION_CODE = BASE_DIR / 'static' / 'js' / 'contract-service-integration-complete.js'

def read_file(filepath):
    """读取文件内容"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(f"错误: 文件 {filepath} 不存在")
        return None

def write_file(filepath, content):
    """写入文件内容"""
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    except Exception as e:
        print(f"错误: 写入文件失败 - {e}")
        return False

def backup_file(filepath):
    """备份文件"""
    if filepath.exists():
        backup_path = filepath.with_suffix(filepath.suffix + '.backup_before_integration')
        try:
            with open(filepath, 'r', encoding='utf-8') as src:
                with open(backup_path, 'w', encoding='utf-8') as dst:
                    dst.write(src.read())
            print(f"✓ 已备份文件到: {backup_path}")
            return True
        except Exception as e:
            print(f"错误: 备份文件失败 - {e}")
            return False
    return False

def integrate_module(content):
    """集成dynamic-table.js模块"""
    # 检查是否已经引入
    if 'dynamic-table.js' in content:
        print("✓ dynamic-table.js 已经引入")
        return content
    
    # 查找script标签开始位置
    script_pattern = r'(<script[^>]*>)'
    matches = list(re.finditer(script_pattern, content))
    
    if not matches:
        # 如果没有找到script标签，在DOMContentLoaded之前添加
        dom_pattern = r'(document\.addEventListener\([\'"]DOMContentLoaded[\'"]\s*,\s*function\(\)\s*\{)'
        match = re.search(dom_pattern, content)
        if match:
            insert_pos = match.start()
            insert_code = '<script src="{% static \'js/dynamic-table.js\' %}"></script>\n<script>\n'
            content = content[:insert_pos] + insert_code + content[insert_pos:]
            print("✓ 已添加 dynamic-table.js 引用")
        else:
            print("⚠ 未找到DOMContentLoaded，请手动添加 dynamic-table.js 引用")
    else:
        # 在第一个script标签后添加
        first_script = matches[0]
        insert_pos = first_script.end()
        insert_code = '\n<script src="{% static \'js/dynamic-table.js\' %}"></script>'
        content = content[:insert_pos] + insert_code + content[insert_pos:]
        print("✓ 已添加 dynamic-table.js 引用")
    
    return content

def replace_add_service_function(content):
    """替换addServiceContent函数"""
    # 查找function addServiceContent的开始和结束
    pattern = r'function\s+addServiceContent\s*\([^)]*\)\s*\{[^}]*\{[^}]*\}'
    
    # 更精确的匹配：找到整个函数体
    start_pattern = r'function\s+addServiceContent\s*\([^)]*\)\s*\{'
    start_match = re.search(start_pattern, content)
    
    if not start_match:
        print("⚠ 未找到 addServiceContent 函数，可能已经替换或不存在")
        return content
    
    # 找到函数结束位置（匹配大括号）
    start_pos = start_match.start()
    brace_count = 0
    in_string = False
    string_char = None
    escape_next = False
    
    pos = start_match.end() - 1
    while pos < len(content):
        char = content[pos]
        
        if escape_next:
            escape_next = False
            pos += 1
            continue
        
        if char == '\\':
            escape_next = True
            pos += 1
            continue
        
        if char in ['"', "'"] and not in_string:
            in_string = True
            string_char = char
        elif char == string_char and in_string:
            in_string = False
            string_char = None
        
        if not in_string:
            if char == '{':
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count == 0:
                    end_pos = pos + 1
                    break
        
        pos += 1
    else:
        print("⚠ 无法找到函数结束位置")
        return content
    
    # 读取集成代码
    integration_code = read_file(INTEGRATION_CODE)
    if not integration_code:
        print("⚠ 无法读取集成代码文件")
        return content
    
    # 替换函数
    new_content = content[:start_pos] + integration_code + content[end_pos:]
    print("✓ 已替换 addServiceContent 函数")
    
    return new_content

def remove_old_event_listeners(content):
    """删除旧的事件监听器代码"""
    # 删除 addServiceContentBtn.addEventListener 相关代码
    pattern = r'const\s+addServiceContentBtn\s*=\s*document\.getElementById\([\'"]add-service-content-btn[\'"]\);\s*if\s*\(addServiceContentBtn\)\s*\{[^}]*addEventListener\([\'"]click[\'"]\s*,\s*function[^}]*\}\);\s*\}'
    
    content = re.sub(pattern, '', content, flags=re.DOTALL)
    
    # 删除 updateServiceContentRowNumbers 函数（如果存在）
    pattern2 = r'function\s+updateServiceContentRowNumbers\s*\([^)]*\)\s*\{[^}]*\}'
    content = re.sub(pattern2, '', content, flags=re.DOTALL)
    
    print("✓ 已删除旧的事件监听器代码")
    return content

def main():
    """主函数"""
    print("=" * 60)
    print("服务信息表格模块集成工具")
    print("=" * 60)
    
    # 检查文件是否存在
    if not TEMPLATE_FILE.exists():
        print(f"错误: 模板文件不存在: {TEMPLATE_FILE}")
        sys.exit(1)
    
    if not DYNAMIC_TABLE_JS.exists():
        print(f"错误: dynamic-table.js 不存在: {DYNAMIC_TABLE_JS}")
        sys.exit(1)
    
    if not INTEGRATION_CODE.exists():
        print(f"错误: 集成代码文件不存在: {INTEGRATION_CODE}")
        sys.exit(1)
    
    # 备份文件
    print("\n1. 备份文件...")
    if not backup_file(TEMPLATE_FILE):
        print("错误: 备份失败，终止操作")
        sys.exit(1)
    
    # 读取文件
    print("\n2. 读取模板文件...")
    content = read_file(TEMPLATE_FILE)
    if not content:
        sys.exit(1)
    
    # 集成模块
    print("\n3. 集成 dynamic-table.js 模块...")
    content = integrate_module(content)
    
    # 替换函数
    print("\n4. 替换 addServiceContent 函数...")
    content = replace_add_service_function(content)
    
    # 删除旧代码
    print("\n5. 删除旧的事件监听器...")
    content = remove_old_event_listeners(content)
    
    # 写入文件
    print("\n6. 保存文件...")
    if write_file(TEMPLATE_FILE, content):
        print("✓ 集成完成！")
        print("\n请测试以下功能：")
        print("  - 添加服务信息行")
        print("  - 删除服务信息行")
        print("  - 服务类型过滤服务专业")
        print("  - 表单提交")
    else:
        print("错误: 保存文件失败")
        sys.exit(1)

if __name__ == '__main__':
    main()

