#!/bin/bash
# 执行SQL脚本添加定位字段
# 使用方法：bash apply_location_fields.sh

cd "$(dirname "$0")/../../../../"

# 激活虚拟环境
source venv/bin/activate 2>/dev/null || source ../venv/bin/activate 2>/dev/null

# 使用Django的dbshell执行SQL
echo "正在执行SQL脚本..."
python manage.py dbshell < backend/apps/customer_success/migrations/0021_manual_sql.sql

if [ $? -eq 0 ]; then
    echo "✅ SQL脚本执行成功！"
    echo "字段已添加到 customer_relationship 表："
    echo "  - latitude (NUMERIC(10, 7))"
    echo "  - longitude (NUMERIC(10, 7))"
    echo "  - location_address (VARCHAR(500))"
else
    echo "❌ SQL脚本执行失败，请检查错误信息"
    exit 1
fi

