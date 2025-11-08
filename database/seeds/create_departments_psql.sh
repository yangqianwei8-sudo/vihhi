#!/bin/bash
# PostgreSQL 部门数据创建脚本
# 使用方法：./create_departments_psql.sh

# 数据库连接参数（从环境变量或默认值）
DB_HOST=${DB_HOST:-localhost}
DB_PORT=${DB_PORT:-5432}
DB_NAME=${DB_NAME:-weihai_tech}
DB_USER=${DB_USER:-postgres}
DB_PASSWORD=${DB_PASSWORD:-password}

# 如果使用 docker-compose，可以使用以下方式连接
# PGHOST=db PGPORT=5432 PGDATABASE=weihai_tech PGUSER=postgres PGPASSWORD=password

echo "=========================================="
echo "创建部门数据到 PostgreSQL"
echo "=========================================="
echo "数据库: $DB_NAME"
echo "主机: $DB_HOST:$DB_PORT"
echo "用户: $DB_USER"
echo ""

# 设置密码环境变量（避免交互式输入）
export PGPASSWORD=$DB_PASSWORD

# 执行 SQL 脚本
psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -f "$(dirname "$0")/create_departments.sql"

if [ $? -eq 0 ]; then
    echo ""
    echo "=========================================="
    echo "✓ 部门数据创建成功！"
    echo "=========================================="
    
    # 显示创建的部门
    echo ""
    echo "当前所有部门："
    psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "SELECT id, code, name, \"order\", is_active FROM system_department ORDER BY \"order\", id;"
else
    echo ""
    echo "=========================================="
    echo "✗ 部门数据创建失败！"
    echo "=========================================="
    exit 1
fi

# 清除密码环境变量
unset PGPASSWORD

