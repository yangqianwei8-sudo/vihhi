#!/bin/bash
# 模态框迁移测试脚本

echo "🧪 模态框迁移测试"
echo "=================="
echo ""

# 检查文件是否使用新路径
echo "1. 检查文件路径..."
NEW_PATH_COUNT=$(grep -r "shared/modals/filter_fields_settings_modal" /home/devbox/project/vihhi/weihai_tech_production_system/backend/templates --include="*.html" -l 2>/dev/null | wc -l)
echo "   使用新路径的文件数: $NEW_PATH_COUNT"

OLD_PATH_COUNT=$(grep -r "customer_management/includes/filter_fields_settings_modal" /home/devbox/project/vihhi/weihai_tech_production_system/backend/templates --include="*.html" -l 2>/dev/null | wc -l)
echo "   仍使用旧路径的文件数: $OLD_PATH_COUNT"

if [ "$OLD_PATH_COUNT" -eq 0 ]; then
    echo "   ✅ 所有文件已迁移"
else
    echo "   ⚠️  仍有文件使用旧路径"
fi

echo ""

# 检查模板文件是否存在
echo "2. 检查共享模板文件..."
if [ -f "/home/devbox/project/vihhi/weihai_tech_production_system/backend/templates/shared/modals/filter_fields_settings_modal.html" ]; then
    echo "   ✅ 共享模板文件存在"
    LINES=$(wc -l < /home/devbox/project/vihhi/weihai_tech_production_system/backend/templates/shared/modals/filter_fields_settings_modal.html)
    echo "   文件行数: $LINES"
else
    echo "   ❌ 共享模板文件不存在"
fi

echo ""

# 检查备份文件
echo "3. 检查备份文件..."
BACKUP_COUNT=$(find /home/devbox/project/vihhi/weihai_tech_production_system/backend/templates -name "*.backup_before_modal_migration" 2>/dev/null | wc -l)
echo "   备份文件数: $BACKUP_COUNT"

echo ""
echo "✅ 测试完成"
