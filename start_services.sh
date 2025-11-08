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
echo "启动 Gunicorn 服务..."
nohup gunicorn \
    --bind 127.0.0.1:8000 \
    --workers 4 \
    --timeout 120 \
    --access-logfile "$LOG_DIR/gunicorn_access.log" \
    --error-logfile "$LOG_DIR/gunicorn_error.log" \
    backend.config.wsgi:application > "$LOG_DIR/gunicorn.log" 2>&1 &

sleep 3

# 检查服务状态
if ps aux | grep -E "gunicorn.*wsgi" | grep -v grep > /dev/null; then
    echo "✓ Gunicorn 服务已启动"
    echo "  - 绑定: 127.0.0.1:8000"
    echo "  - Workers: 4"
    echo "  - 日志: $LOG_DIR/gunicorn_*.log"
else
    echo "✗ Gunicorn 服务启动失败"
    echo "  请查看日志: $LOG_DIR/gunicorn_error.log"
    exit 1
fi

# 重新加载 Nginx 配置
echo "重新加载 Nginx 配置..."
if sudo nginx -s reload 2>/dev/null; then
    echo "✓ Nginx 配置已重新加载"
else
    echo "⚠ Nginx 重新加载失败，请手动检查"
fi

echo ""
echo "=========================================="
echo "   服务启动完成"
echo "=========================================="
echo "访问地址:"
echo "  - http://localhost/login/"
echo "  - http://127.0.0.1/login/"
echo "  - http://tivpdkrxyioz.sealosbja.site/login/"
echo ""
echo "测试账号:"
echo "  - tx / 123456 (商务经理)"
echo "  - yx / 123456 (专业工程师)"
echo "=========================================="

