#!/bin/bash

echo "=========================================="
echo "检查加载问题诊断脚本"
echo "=========================================="
echo ""

# 检查后端服务器状态
echo "1. 检查后端服务器（端口8001）..."
if curl -s --max-time 5 http://localhost:8001/health/ > /dev/null 2>&1; then
    echo "   ✅ 后端服务器运行正常"
    curl -s http://localhost:8001/health/ | head -5
else
    echo "   ❌ 后端服务器未运行或无法访问"
    echo "   请运行: cd /home/devbox/project/vihhi/weihai_tech_production_system"
    echo "   source venv/bin/activate"
    echo "   python manage.py runserver 0.0.0.0:8001"
fi
echo ""

# 检查前端服务器状态
echo "2. 检查前端服务器（端口8080）..."
if curl -s --max-time 5 http://localhost:8080/ > /dev/null 2>&1; then
    echo "   ✅ 前端服务器运行正常"
else
    echo "   ❌ 前端服务器未运行或无法访问"
    echo "   请运行: cd /home/devbox/project/vihhi/weihai_tech_production_system/frontend"
    echo "   npm run dev"
fi
echo ""

# 检查API端点
echo "3. 检查API端点..."
if curl -s --max-time 5 http://localhost:8001/api/ > /dev/null 2>&1; then
    echo "   ✅ API端点可访问"
    curl -s http://localhost:8001/api/ | head -5
else
    echo "   ❌ API端点无法访问"
fi
echo ""

# 检查端口占用
echo "4. 检查端口占用情况..."
if command -v lsof > /dev/null 2>&1; then
    echo "   端口8001:"
    lsof -i :8001 2>/dev/null || echo "   未发现进程占用8001端口"
    echo "   端口8080:"
    lsof -i :8080 2>/dev/null || echo "   未发现进程占用8080端口"
elif command -v netstat > /dev/null 2>&1; then
    echo "   端口8001:"
    netstat -tlnp 2>/dev/null | grep :8001 || echo "   未发现进程占用8001端口"
    echo "   端口8080:"
    netstat -tlnp 2>/dev/null | grep :8080 || echo "   未发现进程占用8080端口"
else
    echo "   无法检查端口占用（需要安装 lsof 或 netstat）"
fi
echo ""

# 检查网络连接
echo "5. 检查网络连接..."
if ping -c 1 localhost > /dev/null 2>&1; then
    echo "   ✅ 本地网络正常"
else
    echo "   ❌ 本地网络异常"
fi
echo ""

# 检查浏览器控制台错误提示
echo "6. 浏览器检查建议..."
echo "   请打开浏览器开发者工具（F12），检查："
echo "   - Console标签页：查看是否有JavaScript错误"
echo "   - Network标签页：查看API请求是否失败"
echo "   - 如果看到 'ECONNABORTED' 或 'Network Error'，说明后端服务器未启动"
echo ""

echo "=========================================="
echo "解决方案："
echo "=========================================="
echo ""
echo "如果后端服务器未运行："
echo "  cd /home/devbox/project/vihhi/weihai_tech_production_system"
echo "  source venv/bin/activate"
echo "  python manage.py runserver 0.0.0.0:8001"
echo ""
echo "如果前端服务器未运行："
echo "  cd /home/devbox/project/vihhi/weihai_tech_production_system/frontend"
echo "  npm run dev"
echo ""
echo "推荐：直接使用Django后端（更完整的功能）"
echo "  访问: http://localhost:8001/"
echo ""
















