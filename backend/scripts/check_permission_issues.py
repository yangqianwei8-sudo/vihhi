#!/usr/bin/env python3
"""
权限问题全局排查脚本
找出所有页面视图中的权限问题
"""
import os
import re
from pathlib import Path
from collections import defaultdict

BASE_DIR = Path(__file__).parent.parent
APPS_DIR = BASE_DIR / "apps"

# 问题分类
issues = defaultdict(list)

def find_view_files():
    """Step 1: 找出所有页面视图文件"""
    view_files = []
    for app_dir in APPS_DIR.iterdir():
        if not app_dir.is_dir():
            continue
        for pattern in ["views_pages.py", "views_dashboard.py"]:
            view_file = app_dir / pattern
            if view_file.exists():
                view_files.append(view_file)
    return sorted(view_files)

def analyze_file(filepath):
    """分析单个文件"""
    module_name = filepath.parent.name
    content = filepath.read_text(encoding='utf-8')
    lines = content.split('\n')
    
    # 找出所有 @login_required 装饰的函数
    login_required_functions = []
    for i, line in enumerate(lines):
        if '@login_required' in line:
            # 找下一个 def 开头的行
            for j in range(i+1, min(i+10, len(lines))):
                if re.match(r'\s*def\s+\w+\(request', lines[j]):
                    func_match = re.search(r'def\s+(\w+)\(request', lines[j])
                    if func_match:
                        func_name = func_match.group(1)
                        login_required_functions.append((func_name, j+1))
                    break
    
    # 检查每个函数是否有 require_perm
    for func_name, line_num in login_required_functions:
        # 获取函数体（从 def 到下一个 def 或文件结束）
        func_start = line_num - 1
        func_end = len(lines)
        for j in range(func_start + 1, len(lines)):
            if re.match(r'\s*def\s+', lines[j]) and j > func_start + 5:
                func_end = j
                break
        
        func_body = '\n'.join(lines[func_start:func_end])
        
        # 检查是否有 require_perm
        has_require_perm = 'require_perm(' in func_body
        
        # 检查是否有 redirect + messages.error
        has_redirect_error = bool(re.search(r'messages\.(error|warning)\([^)]*\).*redirect\(|redirect\([^)]*\).*messages\.(error|warning)\(', func_body, re.DOTALL))
        
        # 检查是否有 PermissionDenied 或 HttpResponseForbidden
        has_proper_denial = 'PermissionDenied' in func_body or 'HttpResponseForbidden' in func_body
        
        # 检查是否有 _permission_granted 或 get_user_permission_codes（业务权限）
        has_business_perm_check = '_permission_granted(' in func_body or 'get_user_permission_codes(' in func_body
        
        # 找出 URL 路径（从 urls_pages.py）
        url_path = find_url_path(module_name, func_name)
        
        # 记录问题
        if not has_require_perm:
            risk = []
            if has_redirect_error:
                risk.append("302掩盖")
            if has_business_perm_check:
                risk.append("使用业务权限而非Django权限")
            if not has_proper_denial and not has_require_perm:
                risk.append("无require_perm")
            
            issues[module_name].append({
                'file': str(filepath.relative_to(BASE_DIR)),
                'function': func_name,
                'line': line_num,
                'url': url_path,
                'current_auth': 'login_required' + (' + redirect' if has_redirect_error else '') + (' + 业务权限' if has_business_perm_check else ''),
                'risk': risk if risk else ['无require_perm'],
            })

def find_url_path(module_name, func_name):
    """从 urls_pages.py 找出 URL 路径"""
    urls_file = APPS_DIR / module_name / "urls_pages.py"
    if not urls_file.exists():
        return "未知"
    
    content = urls_file.read_text(encoding='utf-8')
    # 查找包含 func_name 的 path
    pattern = rf'path\(["\']([^"\']+)["\'].*{func_name}'
    match = re.search(pattern, content)
    if match:
        return f"/{match.group(1)}"
    
    # 查找 name 参数
    pattern = rf'path\([^,]+,\s*[^,]+,\s*name=["\']([^"\']+)["\']'
    matches = re.findall(pattern, content)
    for name in matches:
        if func_name in name or name.replace('_', '') in func_name.replace('_', ''):
            return f"url_name: {module_name}_pages:{name}"
    
    return "未知"

def main():
    view_files = find_view_files()
    
    print("=" * 60)
    print("权限问题全局排查")
    print("=" * 60)
    print(f"\n找到 {len(view_files)} 个视图文件\n")
    
    for filepath in view_files:
        analyze_file(filepath)
    
    # 输出问题清单
    print("\n" + "=" * 60)
    print("问题清单（按模块）")
    print("=" * 60 + "\n")
    
    for module_name in sorted(issues.keys()):
        print(f"模块：{module_name}")
        for issue in issues[module_name]:
            print(f"  - 页面：{issue['url']}")
            print(f"    view：{issue['file']}::{issue['function']} (行 {issue['line']})")
            print(f"    当前鉴权：{issue['current_auth']}")
            print(f"    风险：{', '.join(issue['risk'])}")
            print(f"    建议最小修复：加 require_perm(...) + 无权限 403 + 菜单 permission 改为 Django codename")
            print()
    
    print("=" * 60)
    print(f"总计：{sum(len(v) for v in issues.values())} 个问题")
    print("=" * 60)

if __name__ == '__main__':
    main()

