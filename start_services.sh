#!/bin/bash
# 启动生产环境服务脚本

PROJECT_DIR="/home/devbox/project/vihhi/weihai_tech_production_system"
VENV_DIR="/home/devbox/project/.venv"
LOG_DIR="/tmp"

cd "$PROJECT_DIR" || exit 1

# 激活虚拟环境
source "$VENV_DIR/bin/activate" || exit 1

# 停止旧的服务
pkill -f "gunicorn.*wsgi" 2>/dev/null
sleep 2

# 启动 Gunicorn 服务
# 支持环境变量 PORT（Sealos 等云平台会设置此变量）
# 优先使用环境变量 PORT，其次尝试读取 .env.sealos 文件，最后默认 8001（Sealos 配置的端口）
if [ -z "$PORT" ] && [ -f "$PROJECT_DIR/../.env.sealos" ]; then
    source "$PROJECT_DIR/../.env.sealos"
fi
# Sealos DevBox 默认使用 8001 端口
PORT=${PORT:-8001}
BIND_ADDRESS=${BIND_ADDRESS:-0.0.0.0}

# 计算最优workers数量：通常是(2 * CPU核心数) + 1
# 但考虑到内存限制，设置最小值为2，最大值为8
CPU_CORES=$(nproc)
WORKERS=$((2 * CPU_CORES + 1))
# 限制最大workers数量，避免内存不足
if [ $WORKERS -gt 8 ]; then
    WORKERS=8
elif [ $WORKERS -lt 2 ]; then
    WORKERS=2
fi

# 允许通过环境变量覆盖workers数量
WORKERS=${GUNICORN_WORKERS:-$WORKERS}

echo "启动 Gunicorn 服务..."
echo "  - 端口: $PORT"
echo "  - 绑定地址: $BIND_ADDRESS"
echo "  - Workers: $WORKERS (CPU核心数: $CPU_CORES)"

nohup gunicorn \
    --bind "$BIND_ADDRESS:$PORT" \
    --workers $WORKERS \
    --worker-class sync \
    --timeout 120 \
    --max-requests 1000 \
    --max-requests-jitter 50 \
    --access-logfile "$LOG_DIR/gunicorn_access.log" \
    --error-logfile "$LOG_DIR/gunicorn_error.log" \
    backend.config.wsgi:application > "$LOG_DIR/gunicorn.log" 2>&1 &

sleep 3

# 检查服务状态
if ps aux | grep -E "gunicorn.*wsgi" | grep -v grep > /dev/null; then
    echo "✓ Gunicorn 服务已启动"
    echo "  - 绑定: $BIND_ADDRESS:$PORT"
    echo "  - Workers: $WORKERS"
    echo "  - 日志: $LOG_DIR/gunicorn_*.log"
else
    echo "✗ Gunicorn 服务启动失败"
    echo "  请查看日志: $LOG_DIR/gunicorn_error.log"
    exit 1
fi

# 重新加载 Nginx 配置（如果 Nginx 已安装且运行中）
if command -v nginx >/dev/null 2>&1 && pgrep nginx >/dev/null 2>&1; then
    echo "重新加载 Nginx 配置..."
    if sudo nginx -s reload 2>/dev/null; then
        echo "✓ Nginx 配置已重新加载"
    else
        echo "⚠ Nginx 重新加载失败，请手动检查"
        echo "  提示: 运行 'sudo nginx -t' 检查配置，或查看日志排查"
    fi
else
    echo "跳过 Nginx 重新加载（Nginx 未安装或未运行）"
fi

echo ""
echo "=========================================="
echo "   服务启动完成"
echo "=========================================="
echo "访问地址:"
echo "  - http://localhost:$PORT/login/"
echo "  - http://127.0.0.1:$PORT/login/"
echo "  - https://rasdmangrhdn.sealosbja.site/login/"
echo ""
echo "测试账号:"
echo "  - tx / 123456 (商务经理)"
echo "  - yx / 123456 (专业工程师)"
echo "=========================================="

