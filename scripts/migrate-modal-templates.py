#!/usr/bin/env python3
"""
模态框模板迁移脚本
将分散在各处的模态框 HTML 代码替换为 {% include %} 标签
"""

import os
import re
import sys
from pathlib import Path

# 需要迁移的文件列表
FILES_TO_MIGRATE = [
    "backend/templates/customer_management/contact_list.html",
    "backend/templates/customer_management/customer_public_sea.html",
    "backend/templates/customer_management/customer_relationship_upgrade.html",
    "backend/templates/customer_management/business_expense_application_list.html",
    "backend/templates/customer_management/customer_relationship_collaboration.html",
    "backend/templates/customer_management/customer_visit.html",
]

# 模态框代码的正则表达式模式
MODAL_PATTERN = re.compile(
    r'<div\s+class="modal\s+fade"\s+id="filterFieldsSettingsModal".*?</div>\s*</div>\s*</div>',
    re.DOTALL
)

# 替换内容
REPLACEMENT = "{% include 'shared/modals/filter_fields_settings_modal.html' %}"


def backup_file(file_path):
    """备份文件"""
    backup_path = f"{file_path}.backup_before_modal_migration"
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ 已备份: {backup_path}")
        return True
    return False


def migrate_file(file_path):
    """迁移单个文件"""
    project_root = Path(__file__).parent.parent
    full_path = project_root / file_path
    
    if not full_path.exists():
        print(f"⚠️  文件不存在: {file_path}")
        return False
    
    # 备份文件
    backup_file(str(full_path))
    
    # 读取文件内容
    with open(full_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查是否包含模态框代码
    if 'filterFieldsSettingsModal' not in content:
        print(f"ℹ️  文件不包含模态框代码: {file_path}")
        return False
    
    # 检查是否已经使用 include
    if "{% include 'shared/modals/filter_fields_settings_modal.html' %}" in content:
        print(f"ℹ️  文件已使用 include: {file_path}")
        return False
    
    # 尝试匹配并替换
    new_content = MODAL_PATTERN.sub(REPLACEMENT, content)
    
    # 如果内容有变化，写入文件
    if new_content != content:
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"✅ 已迁移: {file_path}")
        return True
    else:
        print(f"⚠️  未找到匹配的模态框代码: {file_path}")
        print("   请手动检查文件内容")
        return False


def main():
    """主函数"""
    print("🚀 开始迁移模态框模板...")
    print("=" * 60)
    
    success_count = 0
    fail_count = 0
    skip_count = 0
    
    for file_path in FILES_TO_MIGRATE:
        print(f"\n📄 处理: {file_path}")
        result = migrate_file(file_path)
        if result:
            success_count += 1
        elif "已使用 include" in str(result) or "不包含" in str(result):
            skip_count += 1
        else:
            fail_count += 1
    
    print("\n" + "=" * 60)
    print("📊 迁移结果:")
    print(f"  ✅ 成功: {success_count} 个文件")
    print(f"  ⚠️  跳过: {skip_count} 个文件")
    print(f"  ❌ 失败: {fail_count} 个文件")
    print(f"  📝 总计: {len(FILES_TO_MIGRATE)} 个文件")
    
    if success_count > 0:
        print("\n✅ 迁移完成！请测试所有页面确保功能正常。")
        print("💡 提示: 如果遇到问题，可以使用 .backup_before_modal_migration 文件恢复")


if __name__ == "__main__":
    main()

