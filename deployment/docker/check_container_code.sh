#!/bin/bash
# 检查容器中的代码是否与 GitHub 同步

echo "🔍 检查容器代码同步情况..."
echo ""

# 1. 检查关键文件是否存在
echo "1. 检查关键文件："
FILES=(
    "backend/apps/production_management/views_pages.py"
    "backend/apps/production_management/urls.py"
    "backend/templates/production_management/pre_optimization_materials_detail.html"
    "backend/apps/production_management/models.py"
)

for file in "${FILES[@]}"; do
    if [ -f "/app/$file" ]; then
        echo "  ✓ $file 存在"
    else
        echo "  ✗ $file 不存在"
    fi
done

echo ""
echo "2. 检查 API 端点函数："
if grep -q "def pre_optimization_materials_progress" /app/backend/apps/production_management/views_pages.py 2>/dev/null; then
    echo "  ✓ pre_optimization_materials_progress 函数存在"
    # 检查返回格式
    if grep -q "'status':" /app/backend/apps/production_management/views_pages.py 2>/dev/null; then
        echo "  ✓ API 返回格式正确（使用 'status' 字段）"
    else
        echo "  ✗ API 返回格式可能不正确（应使用 'status' 字段）"
    fi
    if grep -q "'is_finished':" /app/backend/apps/production_management/views_pages.py 2>/dev/null; then
        echo "  ✓ API 返回包含 'is_finished' 字段"
    else
        echo "  ✗ API 返回缺少 'is_finished' 字段"
    fi
else
    echo "  ✗ pre_optimization_materials_progress 函数不存在"
fi

echo ""
echo "3. 检查 URL 路由："
if grep -q "pre-optimization-materials.*progress" /app/backend/apps/production_management/urls.py 2>/dev/null; then
    echo "  ✓ progress 路由存在"
else
    echo "  ✗ progress 路由不存在"
fi

echo ""
echo "4. 检查模板元素 ID："
if grep -q "id=\"parse-progress-bar\"" /app/backend/templates/production_management/pre_optimization_materials_detail.html 2>/dev/null; then
    echo "  ✓ parse-progress-bar ID 存在"
else
    echo "  ✗ parse-progress-bar ID 不存在"
fi

if grep -q "id=\"parse-progress-text\"" /app/backend/templates/production_management/pre_optimization_materials_detail.html 2>/dev/null; then
    echo "  ✓ parse-progress-text ID 存在"
else
    echo "  ✗ parse-progress-text ID 不存在"
fi

if grep -q "id=\"parse-progress-message\"" /app/backend/templates/production_management/pre_optimization_materials_detail.html 2>/dev/null; then
    echo "  ✓ parse-progress-message ID 存在"
else
    echo "  ✗ parse-progress-message ID 不存在"
fi

if grep -q "id=\"parse-status-badge\"" /app/backend/templates/production_management/pre_optimization_materials_detail.html 2>/dev/null; then
    echo "  ✓ parse-status-badge ID 存在"
else
    echo "  ✗ parse-status-badge ID 不存在"
fi

echo ""
echo "5. 检查数据库字段："
python3 /app/manage.py shell -c "
from backend.apps.production_management.models import PreOptimizationMaterial
from django.db import connection
cursor = connection.cursor()
cursor.execute(\"SELECT column_name FROM information_schema.columns WHERE table_name='production_management_pre_optimization_material' AND column_name='parse_progress_message'\")
if cursor.fetchone():
    print('  ✓ parse_progress_message 字段存在')
else:
    print('  ✗ parse_progress_message 字段不存在')
" 2>/dev/null || echo "  ? 无法检查数据库字段（可能需要先设置 DATABASE_URL）"

echo ""
echo "6. 检查 JavaScript 代码："
if grep -q "checkParseStatus" /app/backend/templates/production_management/pre_optimization_materials_detail.html 2>/dev/null; then
    echo "  ✓ checkParseStatus 函数存在"
    # 检查是否使用正确的字段名
    if grep -q "data.status" /app/backend/templates/production_management/pre_optimization_materials_detail.html 2>/dev/null; then
        echo "  ✓ JavaScript 使用正确的字段名（data.status）"
    else
        echo "  ✗ JavaScript 可能使用了错误的字段名"
    fi
    if grep -q "data.is_finished" /app/backend/templates/production_management/pre_optimization_materials_detail.html 2>/dev/null; then
        echo "  ✓ JavaScript 检查 is_finished 字段"
    else
        echo "  ✗ JavaScript 未检查 is_finished 字段"
    fi
else
    echo "  ✗ checkParseStatus 函数不存在"
fi

echo ""
echo "✅ 检查完成！"
echo ""
echo "💡 如果发现问题："
echo "   1. 确保 GitHub Actions 构建已完成"
echo "   2. 在 Sealos 中更新应用（使用最新镜像）"
echo "   3. 检查容器日志：kubectl logs <pod-name> -n <namespace>"

