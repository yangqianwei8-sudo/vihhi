#!/bin/bash
# 清理并完成所有迁移脚本

set -e

echo "=========================================="
echo "🔧 开始清理并完成所有迁移"
echo "=========================================="

# 1. 清理迁移缓存文件
echo ""
echo "1️⃣ 清理迁移缓存文件..."
find backend/apps -type d -name "__pycache__" -path "*/migrations/*" -exec rm -rf {} + 2>/dev/null || true
find backend/apps -name "*.pyc" -path "*/migrations/*" -delete 2>/dev/null || true
echo "✅ 迁移缓存文件已清理"

# 2. 检查未应用的迁移
echo ""
echo "2️⃣ 检查未应用的迁移..."
UNAPPLIED=$(python manage.py showmigrations 2>&1 | grep -E "\[ \]" | wc -l)
echo "   发现 $UNAPPLIED 个未应用的迁移"

# 3. 检查是否有新的迁移需要创建
echo ""
echo "3️⃣ 检查是否有新的迁移需要创建..."
if python manage.py makemigrations --dry-run 2>&1 | grep -q "No changes detected"; then
    echo "✅ 没有需要创建的新迁移"
else
    echo "⚠️  检测到模型变更，需要创建新迁移"
    echo "   运行: python manage.py makemigrations"
fi

# 4. 应用所有迁移
echo ""
echo "4️⃣ 应用所有迁移..."
python manage.py migrate --noinput
echo "✅ 所有迁移已应用"

# 5. 验证迁移状态
echo ""
echo "5️⃣ 验证迁移状态..."
REMAINING=$(python manage.py showmigrations 2>&1 | grep -E "\[ \]" | wc -l)
if [ "$REMAINING" -eq 0 ]; then
    echo "✅ 所有迁移已成功应用"
else
    echo "⚠️  仍有 $REMAINING 个未应用的迁移"
    echo "   请检查迁移文件是否有冲突"
fi

# 6. 检查迁移文件冲突
echo ""
echo "6️⃣ 检查迁移文件冲突..."
CONFLICTS=$(find backend/apps -name "*.py" -path "*/migrations/*" ! -name "__init__.py" -exec grep -l "conflict\|Conflict" {} \; 2>/dev/null | wc -l)
if [ "$CONFLICTS" -eq 0 ]; then
    echo "✅ 未发现迁移冲突"
else
    echo "⚠️  发现 $CONFLICTS 个可能的迁移冲突文件"
fi

echo ""
echo "=========================================="
echo "✅ 清理和迁移完成"
echo "=========================================="

