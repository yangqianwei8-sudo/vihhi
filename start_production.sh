#!/bin/bash
# 启动生产环境服务脚本（端口8000，对应 dbjhjowayeto.sealosbja.site）

PROJECT_DIR="/home/devbox/project/vihhi/weihai_tech_production_system"
VENV_DIR="/home/devbox/project/.venv"
LOG_DIR="/tmp"

cd "$PROJECT_DIR" || exit 1

# 激活虚拟环境
source "$VENV_DIR/bin/activate" || exit 1

# 停止旧的服务（包括8000和8001端口的服务）
pkill -f "gunicorn.*wsgi" 2>/dev/null
sleep 2

# 生产环境配置
export PORT=8000
export BIND_ADDRESS=0.0.0.0
export DEBUG=False

# 加载 .env 文件中的配置（如果存在）
if [ -f "$PROJECT_DIR/.env" ]; then
    set -a
    source "$PROJECT_DIR/.env"
    set +a
fi

# 确保生产环境域名在配置中
export ALLOWED_HOSTS="${ALLOWED_HOSTS:-localhost,127.0.0.1,dbjhjowayeto.sealosbja.site,*.sealosbja.site}"
export CSRF_TRUSTED_ORIGINS="${CSRF_TRUSTED_ORIGINS:-https://dbjhjowayeto.sealosbja.site,http://dbjhjowayeto.sealosbja.site,http://localhost:8000,http://127.0.0.1:8000}"

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

echo "=========================================="
echo "   启动生产环境服务"
echo "=========================================="
echo "启动 Gunicorn 服务..."
echo "  - 端口: $PORT"
echo "  - 绑定地址: $BIND_ADDRESS"
echo "  - Workers: $WORKERS (CPU核心数: $CPU_CORES)"
echo "  - 环境: 生产环境 (DEBUG=False)"
echo ""

nohup gunicorn \
    --bind "$BIND_ADDRESS:$PORT" \
    --workers $WORKERS \
    --worker-class sync \
    --timeout 120 \
    --max-requests 1000 \
    --max-requests-jitter 50 \
    --access-logfile "$LOG_DIR/gunicorn_production_access.log" \
    --error-logfile "$LOG_DIR/gunicorn_production_error.log" \
    backend.config.wsgi:application > "$LOG_DIR/gunicorn_production.log" 2>&1 &

sleep 3

# 检查服务状态
if ps aux | grep -E "gunicorn.*wsgi" | grep -v grep > /dev/null; then
    echo "✓ Gunicorn 生产环境服务已启动"
    echo "  - 绑定: $BIND_ADDRESS:$PORT"
    echo "  - Workers: $WORKERS"
    echo "  - 日志: $LOG_DIR/gunicorn_production_*.log"
else
    echo "✗ Gunicorn 服务启动失败"
    echo "  请查看日志: $LOG_DIR/gunicorn_production_error.log"
    exit 1
fi

echo ""
echo "=========================================="
echo "   生产环境服务启动完成"
echo "=========================================="
echo "访问地址:"
echo "  - http://localhost:8000/login/"
echo "  - http://127.0.0.1:8000/login/"
echo "  - https://dbjhjowayeto.sealosbja.site/login/"
echo ""
echo "测试账号:"
echo "  - tx / 123456 (商务经理)"
echo "  - yx / 123456 (专业工程师)"
echo "=========================================="

