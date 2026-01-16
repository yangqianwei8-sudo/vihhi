#!/usr/bin/env python3
"""
Django 模板语法检查工具
检查模板文件中的 block/endblock 是否匹配
"""

import re
import sys
from pathlib import Path

def check_template_syntax(file_path):
    """检查模板文件的语法"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    errors = []
    
    # 检查 block/endblock 匹配
    blocks = []
    for i, line in enumerate(content.split('\n'), 1):
        # 查找 {% block %}
        block_match = re.search(r'{%\s*block\s+(\w+)\s*%}', line)
        if block_match:
            blocks.append({
                'name': block_match.group(1),
                'line': i,
                'type': 'open'
            })
        
        # 查找 {% endblock %}
        endblock_match = re.search(r'{%\s*endblock\s*(?:\w+)?\s*%}', line)
        if endblock_match:
            if blocks:
                blocks.pop()
            else:
                errors.append("第 {} 行: 多余的 {{% endblock %}}".format(i))
    
    # 检查未闭合的 block
    for block in blocks:
        errors.append("第 {} 行: {{% block {} %}} 未闭合".format(block['line'], block['name']))
    
    return errors

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("用法: python3 check_template.py <模板文件路径>")
        sys.exit(1)
    
    file_path = Path(sys.argv[1])
    if not file_path.exists():
        print(f"错误: 文件不存在: {file_path}")
        sys.exit(1)
    
    errors = check_template_syntax(file_path)
    if errors:
        print(f"\n发现 {len(errors)} 个错误:")
        for error in errors:
            print(f"  ❌ {error}")
        sys.exit(1)
    else:
        print("✅ 模板语法检查通过")
        sys.exit(0)
