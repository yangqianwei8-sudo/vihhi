#!/usr/bin/env python
"""
修复 customer_success 的遗留引用

修复范围：
1. 迁移文件中的依赖声明
2. 迁移文件中的外键引用
3. 其他代码中的引用
"""
import os
import sys
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

def fix_migration_files():
    """修复迁移文件中的引用"""
    print("=" * 70)
    print("修复迁移文件中的引用")
    print("=" * 70)
    print()
    
    migration_dirs = [
        PROJECT_ROOT / 'backend' / 'apps' / 'customer_management' / 'migrations',
        PROJECT_ROOT / 'backend' / 'apps' / 'delivery_customer' / 'migrations',
        PROJECT_ROOT / 'backend' / 'apps' / 'production_management' / 'migrations',
    ]
    
    fixed_count = 0
    
    for migration_dir in migration_dirs:
        if not migration_dir.exists():
            continue
        
        print(f"处理 {migration_dir.relative_to(PROJECT_ROOT)}...")
        
        for migration_file in migration_dir.glob('*.py'):
            if migration_file.name == '__init__.py':
                continue
            
            try:
                with open(migration_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                original_content = content
                
                # 修复依赖声明
                content = re.sub(
                    r"\('customer_success',\s*'([^']+)'\)",
                    r"('customer_management', '\1')",
                    content
                )
                
                # 修复外键引用
                content = re.sub(
                    r"to='customer_success\.([^']+)'",
                    r"to='customer_management.\1'",
                    content
                )
                content = re.sub(
                    r'to="customer_success\.([^"]+)"',
                    r'to="customer_management.\1"',
                    content
                )
                
                # 修复迁移文件注释中的引用
                content = re.sub(
                    r'customer_success\.',
                    r'customer_management.',
                    content
                )
                
                if content != original_content:
                    with open(migration_file, 'w', encoding='utf-8') as f:
                        f.write(content)
                    fixed_count += 1
                    print(f"  ✅ 已修复: {migration_file.name}")
            
            except Exception as e:
                print(f"  ❌ 处理失败 {migration_file.name}: {e}")
        
        print()
    
    print(f"✅ 共修复 {fixed_count} 个迁移文件")
    print()
    return fixed_count

def check_template_usage():
    """检查模板文件是否仍在使用"""
    print("=" * 70)
    print("检查模板文件使用情况")
    print("=" * 70)
    print()
    
    customer_management_views = PROJECT_ROOT / 'backend' / 'apps' / 'customer_management' / 'views_pages.py'
    
    if not customer_management_views.exists():
        print("⚠️  customer_management/views_pages.py 不存在")
        return
    
    with open(customer_management_views, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查是否使用了 customer_success 模板
    if 'customer_success/' in content:
        print("⚠️  发现 customer_management/views_pages.py 中仍在使用 customer_success 模板")
        print("   需要更新模板路径")
    else:
        print("✅ customer_management 未使用 customer_success 模板")
    
    print()

def main():
    """主函数"""
    print("=" * 70)
    print("修复 customer_success 遗留引用")
    print("=" * 70)
    print()
    
    # 修复迁移文件
    fixed_count = fix_migration_files()
    
    # 检查模板使用
    check_template_usage()
    
    print("=" * 70)
    print("✅ 修复完成")
    print("=" * 70)
    print()
    print(f"修复了 {fixed_count} 个迁移文件")
    print()
    print("⚠️  注意：")
    print("   1. 模板文件需要手动处理（87个文件）")
    print("   2. 建议检查 customer_management 是否仍在使用 customer_success 模板")
    print("   3. 如果不再使用，可以删除 backend/templates/customer_success 目录")

if __name__ == '__main__':
    main()

