#!/bin/bash
# Gunicorn服务监控脚本

PROJECT_DIR="/home/devbox/project/vihhi/weihai_tech_production_system"
LOG_FILE="/tmp/service_monitor.log"

cd "$PROJECT_DIR" || exit 1

while true; do
    # 检查服务是否运行
    if ! ps aux | grep -E "gunicorn.*wsgi" | grep -v grep > /dev/null; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] 服务已停止，正在重启..." >> "$LOG_FILE"
        export PORT=8001
        bash start_services.sh >> "$LOG_FILE" 2>&1
        sleep 5
    fi
    
    # 检查健康检查
    if ! curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8001/health/ | grep -q "200"; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] 健康检查失败，重启服务..." >> "$LOG_FILE"
        pkill -f "gunicorn.*wsgi" 2>/dev/null
        sleep 2
        export PORT=8001
        bash start_services.sh >> "$LOG_FILE" 2>&1
        sleep 5
    fi
    
    sleep 30
done

