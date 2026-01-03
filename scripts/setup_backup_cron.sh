#!/bin/bash
# 设置自动备份定时任务

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# 备份脚本路径
AGENT_BACKUP_SCRIPT="$SCRIPT_DIR/backup_agent_conversations.py"
DB_BACKUP_SCRIPT="$SCRIPT_DIR/backup_database.sh"

# 检查脚本是否存在
if [ ! -f "$AGENT_BACKUP_SCRIPT" ]; then
    echo "错误: Agent备份脚本不存在: $AGENT_BACKUP_SCRIPT"
    exit 1
fi

if [ ! -f "$DB_BACKUP_SCRIPT" ]; then
    echo "错误: 数据库备份脚本不存在: $DB_BACKUP_SCRIPT"
    exit 1
fi

# Python路径
PYTHON_PATH=$(which python3)

echo "=========================================="
echo "设置自动备份定时任务"
echo "=========================================="
echo ""
echo "备份脚本:"
echo "  - Agent对话备份: $AGENT_BACKUP_SCRIPT"
echo "  - 数据库完整备份: $DB_BACKUP_SCRIPT"
echo ""

# 检查是否已有cron任务
CRON_CMD_AGENT="0 2 * * * cd $PROJECT_DIR && $PYTHON_PATH $AGENT_BACKUP_SCRIPT >> $PROJECT_DIR/backups/agent_conversations/backup.log 2>&1"
CRON_CMD_DB="0 3 * * * cd $PROJECT_DIR && $DB_BACKUP_SCRIPT >> $PROJECT_DIR/backups/database_dumps/backup.log 2>&1"

# 检查是否已存在
if crontab -l 2>/dev/null | grep -q "$AGENT_BACKUP_SCRIPT"; then
    echo "⚠️  Agent对话备份任务已存在"
else
    echo "添加Agent对话备份任务（每天凌晨2点）..."
    (crontab -l 2>/dev/null; echo "$CRON_CMD_AGENT") | crontab -
    echo "✅ Agent对话备份任务已添加"
fi

if crontab -l 2>/dev/null | grep -q "$DB_BACKUP_SCRIPT"; then
    echo "⚠️  数据库完整备份任务已存在"
else
    echo "添加数据库完整备份任务（每天凌晨3点）..."
    (crontab -l 2>/dev/null; echo "$CRON_CMD_DB") | crontab -
    echo "✅ 数据库完整备份任务已添加"
fi

echo ""
echo "=========================================="
echo "当前定时任务列表:"
echo "=========================================="
crontab -l | grep -E "(backup_agent|backup_database)" || echo "（无相关任务）"
echo ""
echo "✅ 自动备份设置完成!"
echo ""
echo "备份计划:"
echo "  - Agent对话数据: 每天 02:00"
echo "  - 数据库完整备份: 每天 03:00"
echo ""
echo "备份目录:"
echo "  - Agent对话: $PROJECT_DIR/backups/agent_conversations/"
echo "  - 数据库: $PROJECT_DIR/backups/database_dumps/"
echo ""
echo "查看备份日志:"
echo "  tail -f $PROJECT_DIR/backups/agent_conversations/backup.log"
echo "  tail -f $PROJECT_DIR/backups/database_dumps/backup.log"

