#!/bin/bash
# 数据库完整备份脚本
# 使用pg_dump备份PostgreSQL数据库

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
BACKUP_DIR="$PROJECT_DIR/backups/database_dumps"

# 创建备份目录
mkdir -p "$BACKUP_DIR"

# 从环境变量获取数据库连接信息
DATABASE_URL="${DATABASE_URL:-postgresql://postgres:zdg7xx28@dbconn.sealosbja.site:38013/postgres}"

# 解析数据库URL
# 格式: postgresql://user:password@host:port/database
if [[ $DATABASE_URL =~ postgresql://([^:]+):([^@]+)@([^:]+):([^/]+)/(.+)$ ]]; then
    DB_USER="${BASH_REMATCH[1]}"
    DB_PASS="${BASH_REMATCH[2]}"
    DB_HOST="${BASH_REMATCH[3]}"
    DB_PORT="${BASH_REMATCH[4]}"
    DB_NAME="${BASH_REMATCH[5]}"
    # 移除可能的查询参数
    DB_NAME="${DB_NAME%%\?*}"
else
    echo "错误: 无法解析 DATABASE_URL"
    exit 1
fi

# 生成备份文件名
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/postgres_${DB_NAME}_${TIMESTAMP}.sql"
COMPRESSED_BACKUP_FILE="${BACKUP_FILE}.gz"

echo "=========================================="
echo "数据库备份"
echo "=========================================="
echo "数据库: $DB_NAME"
echo "主机: $DB_HOST:$DB_PORT"
echo "备份文件: $BACKUP_FILE"
echo ""

# 设置密码环境变量
export PGPASSWORD="$DB_PASS"

# 执行备份
echo "开始备份..."
if pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
    --no-owner --no-privileges --clean --if-exists \
    -f "$BACKUP_FILE" 2>&1; then
    
    # 压缩备份文件
    echo "压缩备份文件..."
    gzip "$BACKUP_FILE"
    
    FILE_SIZE=$(du -h "$COMPRESSED_BACKUP_FILE" | cut -f1)
    echo ""
    echo "✅ 备份完成!"
    echo "   文件: $COMPRESSED_BACKUP_FILE"
    echo "   大小: $FILE_SIZE"
    
    # 清理30天前的备份
    echo ""
    echo "清理旧备份（30天前）..."
    find "$BACKUP_DIR" -name "postgres_${DB_NAME}_*.sql.gz" -type f -mtime +30 -delete
    echo "✅ 清理完成"
    
else
    echo "❌ 备份失败"
    exit 1
fi

# 清理密码环境变量
unset PGPASSWORD

