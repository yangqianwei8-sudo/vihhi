#!/bin/bash
# 修复所有模块首页模板文件
# 移除冲突的 {% extends %} 和重复的 {% load static %}

cd "$(dirname "$0")/.." || exit 1

modules=(
    "settlement_center"
    "production_management"
    "plan_management"
    "task_collaboration"
    "delivery_customer"
    "archive_management"
    "resource_standard"
    "workflow_engine"
    "system_management"
    "api_management"
    "risk_management"
)

echo "开始修复模板文件..."
echo ""

for module in "${modules[@]}"; do
    template_file="backend/templates/${module}/home.html"
    
    if [ ! -f "$template_file" ]; then
        echo "⚠️  $module: 模板文件不存在"
        continue
    fi
    
    # 检查文件开头是否有冲突的extends
    if head -3 "$template_file" | grep -q "{% extends"; then
        # 创建临时文件，移除前3行（extends和重复的load static）
        tail -n +4 "$template_file" > "${template_file}.tmp"
        mv "${template_file}.tmp" "$template_file"
        echo "✅ $module: 已移除冲突的extends语句"
    else
        echo "✓  $module: 无需修复"
    fi
done

echo ""
echo "修复完成！"

