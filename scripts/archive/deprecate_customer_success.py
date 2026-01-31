#!/usr/bin/env python
"""
customer_success 模块废弃脚本

此脚本用于将 customer_success 模块的功能迁移到 customer_management 模块

执行前请确保：
1. 已备份数据库
2. 已在测试环境验证
3. 已创建 customer_management 模块基础结构
"""

import os
import sys
import re
import shutil
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).resolve().parent.parent
BACKEND_APPS = PROJECT_ROOT / 'backend' / 'apps'
CUSTOMER_SUCCESS = BACKEND_APPS / 'customer_success'
CUSTOMER_MANAGEMENT = BACKEND_APPS / 'customer_management'

# 需要更新的文件模式
FILES_TO_UPDATE = [
    '**/*.py',
    '**/*.md',
]

# 需要排除的目录
EXCLUDE_DIRS = [
    '__pycache__',
    '.git',
    'node_modules',
    'venv',
    '.venv',
    'migrations',  # 迁移文件需要单独处理
]

def find_files_to_update():
    """查找需要更新的文件"""
    files = []
    for pattern in FILES_TO_UPDATE:
        for file_path in PROJECT_ROOT.rglob(pattern):
            # 排除特定目录
            if any(exclude in str(file_path) for exclude in EXCLUDE_DIRS):
                continue
            # 排除 customer_success 和 customer_management 目录本身
            if 'customer_success' in str(file_path) or 'customer_management' in str(file_path):
                continue
            if file_path.suffix == '.py' or file_path.suffix == '.md':
                files.append(file_path)
    return files

def update_imports(file_path):
    """更新文件中的导入语句"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # 更新导入语句
        patterns = [
            # from backend.apps.customer_success.models import
            (r'from\s+backend\.apps\.customer_success\.models\s+import', 
             'from backend.apps.customer_management.models import'),
            
            # from backend.apps.customer_success import
            (r'from\s+backend\.apps\.customer_success\s+import', 
             'from backend.apps.customer_management import'),
            
            # from .models import (在 customer_success 目录内)
            (r'from\s+\.models\s+import', 
             'from backend.apps.customer_management.models import'),
            
            # customer_success.Client
            (r'customer_success\.Client', 
             'customer_management.Client'),
            
            # 'customer_success.client'
            (r"'customer_success\.client'", 
             "'customer_management.client'"),
            (r'"customer_success\.client"', 
             '"customer_management.client"'),
        ]
        
        for pattern, replacement in patterns:
            content = re.sub(pattern, replacement, content)
        
        # 如果内容有变化，写回文件
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        return False
    except Exception as e:
        print(f"❌ 更新文件失败 {file_path}: {e}")
        return False

def main():
    """主函数"""
    print("=" * 70)
    print("customer_success 模块废弃脚本")
    print("=" * 70)
    print()
    
    # 检查 customer_management 是否存在
    if not CUSTOMER_MANAGEMENT.exists():
        print("❌ customer_management 模块不存在，请先创建")
        return
    
    # 检查 customer_success 是否存在
    if not CUSTOMER_SUCCESS.exists():
        print("❌ customer_success 模块不存在")
        return
    
    print("📋 步骤1: 查找需要更新的文件...")
    files = find_files_to_update()
    print(f"   找到 {len(files)} 个文件需要检查")
    print()
    
    print("📋 步骤2: 更新导入语句...")
    updated_count = 0
    for file_path in files:
        if update_imports(file_path):
            updated_count += 1
            print(f"   ✓ 已更新: {file_path.relative_to(PROJECT_ROOT)}")
    
    print()
    print(f"✅ 完成！共更新 {updated_count} 个文件")
    print()
    print("⚠️  注意：")
    print("   1. 请检查更新后的文件是否正确")
    print("   2. 迁移文件需要单独处理")
    print("   3. 需要手动更新 settings.py 和 urls.py")
    print("   4. 需要创建数据库迁移")

if __name__ == '__main__':
    main()

