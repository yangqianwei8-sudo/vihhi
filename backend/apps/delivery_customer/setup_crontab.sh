#!/bin/bash
# 配置 Crontab 定时任务

PROJECT_DIR="/home/devbox/project/vihhi/weihai_tech_production_system"
VENV_PYTHON="$PROJECT_DIR/venv/bin/python"
LOG_DIR="$PROJECT_DIR/logs"
LOG_FILE="$LOG_DIR/delivery_tracking.log"

echo "=========================================="
echo "发文跟踪 Crontab 定时任务配置"
echo "=========================================="
echo ""

# 创建日志目录
mkdir -p "$LOG_DIR"

# 生成 crontab 条目
CRON_ENTRY="*/30 * * * * cd $PROJECT_DIR && $VENV_PYTHON manage.py update_tracking_status --limit 50 >> $LOG_FILE 2>&1"

echo "将添加以下 crontab 条目："
echo ""
echo "$CRON_ENTRY"
echo ""
echo "日志文件：$LOG_FILE"
echo ""

read -p "确认添加？(y/n): " confirm

if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
    echo "已取消"
    exit 0
fi

# 获取当前 crontab
CURRENT_CRONTAB=$(crontab -l 2>/dev/null)

# 检查是否已存在
if echo "$CURRENT_CRONTAB" | grep -q "update_tracking_status"; then
    echo "⚠️  检测到已存在 update_tracking_status 任务"
    read -p "是否替换？(y/n): " replace
    if [ "$replace" = "y" ] || [ "$replace" = "Y" ]; then
        # 删除旧条目
        (echo "$CURRENT_CRONTAB" | grep -v "update_tracking_status") | crontab -
        echo "已删除旧任务"
    else
        echo "已取消"
        exit 0
    fi
fi

# 添加新条目
(crontab -l 2>/dev/null; echo ""; echo "# 发文跟踪状态更新任务（每30分钟执行一次）"; echo "$CRON_ENTRY") | crontab -

echo ""
echo "✅ Crontab 任务已添加！"
echo ""
echo "查看当前 crontab："
echo "  crontab -l"
echo ""
echo "查看日志："
echo "  tail -f $LOG_FILE"
echo ""
echo "测试执行："
echo "  cd $PROJECT_DIR && $VENV_PYTHON manage.py update_tracking_status --limit 10"
echo ""
echo "删除任务："
echo "  crontab -e  # 然后删除相关行"
