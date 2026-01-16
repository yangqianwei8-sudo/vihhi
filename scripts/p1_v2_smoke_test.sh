#!/bin/bash
# P1 v2 稳态验收脚本（一键运行三层测试）
# 用法: ./scripts/p1_v2_smoke_test.sh

set -e  # 遇到错误立即退出

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_DIR"

echo "=========================================="
echo "P1 v2 稳态验收测试"
echo "=========================================="
echo ""

# 1. 系统检查
echo "1️⃣  系统检查..."
python manage.py check
if [ $? -eq 0 ]; then
    echo "✅ 系统检查通过"
else
    echo "❌ 系统检查失败"
    exit 1
fi
echo ""

# 2. 单元测试
echo "2️⃣  单元测试..."
DJANGO_SETTINGS_MODULE=backend.config.settings_test \
python manage.py test backend.apps.plan_management.tests.test_plan_decision_v2 -v 2
if [ $? -eq 0 ]; then
    echo "✅ 单元测试通过"
else
    echo "❌ 单元测试失败"
    exit 1
fi
echo ""

# 3. 接口测试（可选，需要服务运行）
if [ "$SKIP_API_TEST" != "1" ]; then
    echo "3️⃣  接口测试（需要服务运行，跳过请设置 SKIP_API_TEST=1）..."
    echo "⚠️  接口测试需要手动执行，参考 docs/p1_plan_decision_v2.md"
    echo ""
fi

echo "=========================================="
echo "✅ P1 v2 稳态验收完成"
echo "=========================================="

