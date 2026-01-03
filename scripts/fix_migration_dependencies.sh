#!/bin/bash
# 统一的迁移依赖修复脚本
# 自动检测并修复Django迁移依赖问题

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

# 激活虚拟环境
if [ -d "venv" ]; then
    source venv/bin/activate
elif [ -d ".venv" ]; then
    source .venv/bin/activate
fi

echo "============================================================"
echo "Django 迁移依赖修复工具"
echo "============================================================"
echo ""

# 检查参数
AUTO_FIX=false
APP_NAME=""
DRY_RUN=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --auto-fix)
            AUTO_FIX=true
            shift
            ;;
        --app)
            APP_NAME="$2"
            shift 2
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        *)
            echo "未知参数: $1"
            echo "用法: $0 [--auto-fix] [--app APP_NAME] [--dry-run]"
            exit 1
            ;;
    esac
done

# 运行修复工具
if [ "$AUTO_FIX" = true ]; then
    echo "🔧 自动修复模式"
    python fix_migration_dependencies.py --auto-fix ${APP_NAME:+--app $APP_NAME} ${DRY_RUN:+--dry-run}
else
    echo "🔍 检查模式（只检测，不修复）"
    echo "💡 使用 --auto-fix 参数可以自动修复问题"
    python fix_migration_dependencies.py ${APP_NAME:+--app $APP_NAME} ${DRY_RUN:+--dry-run}
fi

echo ""
echo "============================================================"
echo "完成！"
echo "============================================================"

