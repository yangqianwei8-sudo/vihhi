#!/bin/bash
# 设置自动同步的安装脚本

PROJECT_DIR="/home/devbox/project/vihhi/weihai_tech_production_system"
SCRIPT_PATH="$PROJECT_DIR/auto_sync.sh"
CRON_JOB="*/5 * * * * cd $PROJECT_DIR && $SCRIPT_PATH once >> /tmp/git_auto_sync_cron.log 2>&1"

echo "=========================================="
echo "  GitHub自动同步设置"
echo "=========================================="
echo ""
echo "请选择同步方式："
echo "1. 定时任务（Cron）- 每5分钟自动同步"
echo "2. 后台监控进程 - 实时监控（每30秒检查）"
echo "3. 手动执行 - 需要时手动运行脚本"
echo ""
read -p "请选择 (1/2/3): " choice

case $choice in
    1)
        echo ""
        echo "设置定时任务（每5分钟同步一次）..."
        # 检查是否已存在
        if crontab -l 2>/dev/null | grep -q "auto_sync.sh"; then
            echo "⚠ 定时任务已存在，先移除旧的..."
            crontab -l 2>/dev/null | grep -v "auto_sync.sh" | crontab -
        fi
        # 添加新的定时任务
        (crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -
        echo "✓ 定时任务已设置"
        echo ""
        echo "当前定时任务："
        crontab -l | grep "auto_sync"
        echo ""
        echo "查看日志: tail -f /tmp/git_auto_sync_cron.log"
        ;;
    2)
        echo ""
        echo "启动后台监控进程..."
        nohup "$SCRIPT_PATH" watch > /tmp/git_auto_sync_watch.log 2>&1 &
        PID=$!
        echo "✓ 监控进程已启动 (PID: $PID)"
        echo ""
        echo "查看日志: tail -f /tmp/git_auto_sync.log"
        echo "停止监控: kill $PID"
        echo "$PID" > /tmp/git_auto_sync.pid
        ;;
    3)
        echo ""
        echo "手动执行模式"
        echo ""
        echo "使用方法："
        echo "  执行一次同步: $SCRIPT_PATH once"
        echo "  监控模式:     $SCRIPT_PATH watch"
        echo "  自定义间隔:   $SCRIPT_PATH interval 60  # 每60秒"
        ;;
    *)
        echo "无效选择"
        exit 1
        ;;
esac

echo ""
echo "=========================================="
echo "  设置完成"
echo "=========================================="

