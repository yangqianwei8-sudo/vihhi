#!/usr/bin/env python
"""
最终清理 customer_success 遗留内容

清理范围：
1. 删除旧模板目录
2. 检查代码中的引用
3. 生成清理报告
"""
import os
import shutil
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

def check_code_references():
    """检查代码中是否还有 customer_success 的引用"""
    print("=" * 70)
    print("检查代码中的 customer_success 引用")
    print("=" * 70)
    print()
    
    # 排除的文件和目录
    exclude_patterns = [
        'customer_success',  # 旧模块目录
        '__pycache__',
        '.pyc',
        'migrations',  # 迁移文件中的历史引用可以保留
        '.md',  # 文档文件
        'scripts',  # 脚本文件
    ]
    
    references = []
    
    # 检查 Python 文件
    for py_file in PROJECT_ROOT.rglob('*.py'):
        # 跳过排除的文件
        if any(pattern in str(py_file) for pattern in exclude_patterns):
            continue
        
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
                if 'customer_success' in content:
                    # 检查是否是注释或字符串中的引用
                    lines = content.split('\n')
                    for i, line in enumerate(lines, 1):
                        if 'customer_success' in line:
                            # 跳过注释行
                            stripped = line.strip()
                            if stripped.startswith('#'):
                                continue
                            # 跳过文档字符串
                            if '"""' in line or "'''" in line:
                                continue
                            references.append({
                                'file': str(py_file.relative_to(PROJECT_ROOT)),
                                'line': i,
                                'content': line.strip()[:100]
                            })
        except Exception as e:
            pass
    
    if references:
        print(f"⚠️  发现 {len(references)} 处引用：")
        for ref in references[:20]:  # 只显示前20个
            print(f"  - {ref['file']}:{ref['line']}")
            print(f"    {ref['content']}")
        if len(references) > 20:
            print(f"  ... 还有 {len(references) - 20} 处引用")
    else:
        print("✅ 未发现代码中的 customer_success 引用（排除文档和脚本）")
    
    print()
    return references

def delete_old_templates():
    """删除旧模板目录"""
    print("=" * 70)
    print("删除旧模板目录")
    print("=" * 70)
    print()
    
    old_template_dir = PROJECT_ROOT / 'backend' / 'templates' / 'customer_success'
    new_template_dir = PROJECT_ROOT / 'backend' / 'templates' / 'customer_management'
    
    if not old_template_dir.exists():
        print("✅ 旧模板目录不存在，无需删除")
        return True
    
    if not new_template_dir.exists():
        print("⚠️  新模板目录不存在，保留旧模板目录")
        return False
    
    # 统计文件数量
    old_count = len(list(old_template_dir.rglob('*.html')))
    new_count = len(list(new_template_dir.rglob('*.html')))
    
    print(f"旧模板目录文件数: {old_count}")
    print(f"新模板目录文件数: {new_count}")
    print()
    
    try:
        shutil.rmtree(old_template_dir)
        print(f"✅ 已删除旧模板目录: {old_template_dir}")
        return True
    except Exception as e:
        print(f"❌ 删除失败: {e}")
        return False

def main():
    """主函数"""
    print("=" * 70)
    print("最终清理 customer_success 遗留内容")
    print("=" * 70)
    print()
    
    # 检查代码引用
    references = check_code_references()
    
    # 删除旧模板目录
    deleted = delete_old_templates()
    
    print("=" * 70)
    print("清理完成")
    print("=" * 70)
    print()
    
    if references:
        print("⚠️  仍有代码引用需要处理（主要是文档和脚本）")
    else:
        print("✅ 代码引用检查通过")
    
    if deleted:
        print("✅ 旧模板目录已删除")
    else:
        print("⚠️  旧模板目录未删除（请手动检查）")
    
    print()
    print("📝 建议：")
    print("  1. 测试系统功能是否正常")
    print("  2. 检查数据库是否还有 customer_success 残留")
    print("  3. 根据需要清理历史文档和脚本")

if __name__ == '__main__':
    main()

