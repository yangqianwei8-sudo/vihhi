#!/bin/bash
# 测试模块首页的脚本
# 启动开发服务器并测试各模块首页

cd "$(dirname "$0")/.." || exit 1

# 激活虚拟环境
if [ -f venv/bin/activate ]; then
    source venv/bin/activate
fi

# 检查Django是否可用
if ! python manage.py check > /dev/null 2>&1; then
    echo "❌ Django配置检查失败，请先修复配置问题"
    python manage.py check
    exit 1
fi

echo "=========================================="
echo "模块首页测试"
echo "=========================================="
echo ""

# 获取服务器地址
PORT=${PORT:-8001}
HOST=${HOST:-0.0.0.0}

echo "启动开发服务器..."
echo "  地址: http://localhost:${PORT}"
echo "  或: http://127.0.0.1:${PORT}"
echo ""

# 模块URL列表
declare -A MODULE_URLS=(
    ["结算中心"]="/settlement/"
    ["生产管理"]="/production/"
    ["计划管理"]="/plan/"
    ["任务协作"]="/collaboration/"
    ["交付客户"]="/delivery/"
    ["档案管理"]="/archive/"
    ["资源标准"]="/resource/"
    ["工作流引擎"]="/workflow/"
    ["系统管理"]="/system-center/"
    ["API管理"]="/api-management/"
    ["风险管理"]="/risk/"
)

echo "可测试的模块首页："
for module in "${!MODULE_URLS[@]}"; do
    url="${MODULE_URLS[$module]}"
    echo "  - $module: http://localhost:${PORT}${url}"
done

echo ""
echo "=========================================="
echo "启动服务器..."
echo "=========================================="
echo ""
echo "提示："
echo "  1. 服务器启动后，在浏览器中访问上述URL"
echo "  2. 按 Ctrl+C 停止服务器"
echo "  3. 检查页面是否正常显示"
echo ""

# 启动服务器
python manage.py runserver "${HOST}:${PORT}"

