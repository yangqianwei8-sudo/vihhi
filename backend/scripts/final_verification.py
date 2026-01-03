#!/usr/bin/env python3
"""
最终验证：检查所有模板文件是否符合规范
1. 100%使用模板继承
2. 100%引用common.css（列表/详情/表单页面）
3. common.css在{% block extra_css %}中
"""

from pathlib import Path
import re

BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = BASE_DIR / 'templates'

def should_exclude_file(file_path):
    """检查文件是否应该被排除"""
    file_str = str(file_path)
    exclude_patterns = [
        '.backup', '.bak', '.deleted',
        'admin/', 'registration/', 'shared/',
        'partials/', 'includes/',
        'login.html', 'api/docs.html', 'base.html'
    ]
    return any(pattern in file_str for pattern in exclude_patterns)

def check_file(file_path):
    """检查单个文件"""
    try:
        content = file_path.read_text(encoding='utf-8')
    except:
        return None, "无法读取文件"
    
    issues = []
    file_name = file_path.name
    
    # 检查模板继承
    if not should_exclude_file(file_path):
        if '{% extends' not in content:
            issues.append("未使用模板继承")
    
    # 检查列表/详情/表单页面的common.css
    if any(x in file_name for x in ['_list.html', '_detail.html', '_form.html']):
        if 'common.css' not in content:
            issues.append("未引用common.css")
        else:
            # 检查是否在block中
            if '{% block extra_css %}' in content:
                block_pattern = r'{% block extra_css %}.*?{% endblock %}'
                matches = re.findall(block_pattern, content, re.DOTALL)
                in_block = any('common.css' in match for match in matches)
                if not in_block:
                    issues.append("common.css不在{% block extra_css %}中")
            else:
                # 检查是否在block外
                lines_before_block = content.split('{% block')[0] if '{% block' in content else content
                if 'common.css' in lines_before_block:
                    issues.append("common.css不在{% block extra_css %}中")
    
    return issues, None

def main():
    """主函数"""
    print("="*60)
    print("最终验证：检查所有模板文件是否符合规范")
    print("="*60 + "\n")
    
    total_files = 0
    files_with_issues = 0
    all_issues = []
    
    # 遍历所有HTML文件
    for html_file in TEMPLATES_DIR.rglob('*.html'):
        if should_exclude_file(html_file):
            continue
        
        total_files += 1
        relative_path = html_file.relative_to(TEMPLATES_DIR)
        
        issues, error = check_file(html_file)
        if error:
            print(f"✗ {relative_path}: {error}")
            files_with_issues += 1
        elif issues:
            files_with_issues += 1
            all_issues.append((relative_path, issues))
            print(f"✗ {relative_path}")
            for issue in issues:
                print(f"  - {issue}")
    
    print("\n" + "="*60)
    print("验证结果统计")
    print("="*60)
    print(f"总文件数: {total_files}")
    print(f"符合规范: {total_files - files_with_issues} ({100*(total_files-files_with_issues)/total_files:.1f}%)")
    print(f"需要修复: {files_with_issues} ({100*files_with_issues/total_files:.1f}%)")
    
    if all_issues:
        print(f"\n需要修复的文件列表 ({len(all_issues)} 个):")
        for path, issues in all_issues[:20]:  # 只显示前20个
            print(f"  - {path}: {', '.join(issues)}")
        if len(all_issues) > 20:
            print(f"  ... 还有 {len(all_issues) - 20} 个文件需要修复")

if __name__ == '__main__':
    main()

