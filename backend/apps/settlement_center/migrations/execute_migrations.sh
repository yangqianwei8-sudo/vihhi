#!/bin/bash
# 服务费结算方案迁移执行脚本
# 如果Django迁移命令无法运行，可以使用此脚本手动执行SQL

set -e

echo "=========================================="
echo "服务费结算方案迁移脚本"
echo "=========================================="

# 检查数据库连接参数（从环境变量或配置文件读取）
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-postgres}"
DB_USER="${DB_USER:-postgres}"

echo "数据库: $DB_NAME@$DB_HOST:$DB_PORT"
echo "用户: $DB_USER"
echo ""

# 提示确认
read -p "确认执行迁移？(y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "已取消"
    exit 1
fi

# 执行迁移SQL
echo "执行迁移SQL..."
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f "$(dirname "$0")/run_migrations.sql"

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ SQL执行成功！"
    echo ""
    echo "接下来需要标记迁移为已应用："
    echo "python manage.py migrate settlement_center 0007 --fake"
    echo "python manage.py migrate settlement_center 0008 --fake"
else
    echo ""
    echo "❌ SQL执行失败，请检查错误信息"
    exit 1
fi

