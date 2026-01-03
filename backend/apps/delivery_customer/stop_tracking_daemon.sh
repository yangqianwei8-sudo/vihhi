#!/bin/bash
# 停止发文跟踪更新守护进程

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"
PID_FILE="$PROJECT_DIR/logs/tracking_update_daemon.pid"

if [ ! -f "$PID_FILE" ]; then
    echo "守护进程未运行（PID 文件不存在）"
    exit 1
fi

PID=$(cat "$PID_FILE")

if ! ps -p "$PID" > /dev/null 2>&1; then
    echo "守护进程未运行（进程不存在）"
    rm -f "$PID_FILE"
    exit 1
fi

echo "正在停止守护进程（PID: $PID）..."
kill "$PID"

# 等待进程结束
for i in {1..10}; do
    if ! ps -p "$PID" > /dev/null 2>&1; then
        break
    fi
    sleep 1
done

# 如果还在运行，强制杀死
if ps -p "$PID" > /dev/null 2>&1; then
    echo "强制停止守护进程..."
    kill -9 "$PID"
fi

rm -f "$PID_FILE"
echo "守护进程已停止"
