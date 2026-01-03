#!/bin/bash
# 查看发文跟踪更新守护进程状态

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"
PID_FILE="$PROJECT_DIR/logs/tracking_update_daemon.pid"
LOG_FILE="$PROJECT_DIR/logs/tracking_update_daemon.log"

if [ ! -f "$PID_FILE" ]; then
    echo "状态：未运行"
    exit 0
fi

PID=$(cat "$PID_FILE")

if ps -p "$PID" > /dev/null 2>&1; then
    echo "状态：运行中"
    echo "PID: $PID"
    echo ""
    echo "进程信息："
    ps -p "$PID" -o pid,ppid,cmd,etime,pcpu,pmem
    echo ""
    echo "最近日志（最后20行）："
    if [ -f "$LOG_FILE" ]; then
        tail -20 "$LOG_FILE"
    else
        echo "日志文件不存在"
    fi
else
    echo "状态：未运行（PID 文件存在但进程不存在）"
    rm -f "$PID_FILE"
fi
