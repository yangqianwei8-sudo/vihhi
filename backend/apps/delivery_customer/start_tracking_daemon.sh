#!/bin/bash
# 启动发文跟踪更新守护进程

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"
DAEMON_SCRIPT="$SCRIPT_DIR/run_tracking_update_daemon.py"
LOG_FILE="$PROJECT_DIR/logs/tracking_update_daemon.log"
PID_FILE="$PROJECT_DIR/logs/tracking_update_daemon.pid"

# 创建日志目录
mkdir -p "$(dirname "$LOG_FILE")"

# 检查是否已在运行
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p "$PID" > /dev/null 2>&1; then
        echo "守护进程已在运行（PID: $PID）"
        exit 1
    else
        # PID 文件存在但进程不存在，删除旧的 PID 文件
        rm -f "$PID_FILE"
    fi
fi

# 启动守护进程
echo "正在启动守护进程..."
cd "$PROJECT_DIR"
source venv/bin/activate

nohup python "$DAEMON_SCRIPT" > "$LOG_FILE" 2>&1 &
DAEMON_PID=$!

# 保存 PID
echo $DAEMON_PID > "$PID_FILE"

echo "守护进程已启动（PID: $DAEMON_PID）"
echo "日志文件：$LOG_FILE"
echo ""
echo "查看日志："
echo "  tail -f $LOG_FILE"
echo ""
echo "停止守护进程："
echo "  bash $SCRIPT_DIR/stop_tracking_daemon.sh"
echo ""
echo "查看状态："
echo "  bash $SCRIPT_DIR/status_tracking_daemon.sh"
