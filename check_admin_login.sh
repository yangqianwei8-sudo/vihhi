#!/bin/bash
# Admin登录页面诊断脚本

echo "=========================================="
echo "  Admin登录页面诊断"
echo "=========================================="
echo ""

# 1. 检查服务器状态
echo "1. 检查服务器状态..."
if ps aux | grep -E "gunicorn.*wsgi" | grep -v grep > /dev/null; then
    echo "   ✓ Gunicorn服务器正在运行"
else
    echo "   ✗ Gunicorn服务器未运行"
    exit 1
fi

# 2. 检查端口监听
echo ""
echo "2. 检查端口监听..."
if netstat -tlnp 2>/dev/null | grep -q ":8001.*LISTEN" || ss -tlnp 2>/dev/null | grep -q ":8001.*LISTEN"; then
    echo "   ✓ 端口8001正在监听"
else
    echo "   ✗ 端口8001未监听"
fi

# 3. 测试本地连接
echo ""
echo "3. 测试本地连接..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8001/admin/login/?next=/admin/)
if [ "$HTTP_CODE" = "200" ]; then
    echo "   ✓ 本地连接正常 (HTTP $HTTP_CODE)"
else
    echo "   ✗ 本地连接失败 (HTTP $HTTP_CODE)"
fi

# 4. 检查HTML内容
echo ""
echo "4. 检查HTML内容..."
HTML_SIZE=$(curl -s http://localhost:8001/admin/login/?next=/admin/ | wc -c)
if [ "$HTML_SIZE" -gt 1000 ]; then
    echo "   ✓ HTML内容正常 (大小: $HTML_SIZE 字节)"
else
    echo "   ✗ HTML内容异常 (大小: $HTML_SIZE 字节)"
fi

# 5. 检查是否有表单
echo ""
echo "5. 检查登录表单..."
if curl -s http://localhost:8001/admin/login/?next=/admin/ | grep -q "<form"; then
    echo "   ✓ 登录表单存在"
else
    echo "   ✗ 登录表单不存在"
fi

# 6. 检查静态文件
echo ""
echo "6. 检查静态文件..."
STATIC_DIR="/home/devbox/project/vihhi/weihai_tech_production_system/backend/staticfiles"
if [ -d "$STATIC_DIR" ]; then
    STATIC_COUNT=$(find "$STATIC_DIR" -type f | wc -l)
    echo "   ✓ 静态文件目录存在 ($STATIC_COUNT 个文件)"
else
    echo "   ✗ 静态文件目录不存在"
fi

# 7. 检查最近的访问日志
echo ""
echo "7. 最近的访问记录..."
tail -5 /tmp/gunicorn_access.log | grep "admin/login" | tail -3 | while read line; do
    echo "   $line"
done

# 8. 检查错误日志
echo ""
echo "8. 检查错误日志..."
ERROR_COUNT=$(tail -50 /tmp/gunicorn_error.log | grep -i "error\|exception\|traceback" | grep -v "SIGHUP" | wc -l)
if [ "$ERROR_COUNT" -eq 0 ]; then
    echo "   ✓ 无严重错误"
else
    echo "   ⚠ 发现 $ERROR_COUNT 个错误（排除SIGHUP）"
    echo "   最近的错误："
    tail -50 /tmp/gunicorn_error.log | grep -i "error\|exception\|traceback" | grep -v "SIGHUP" | tail -3 | while read line; do
        echo "     $line"
    done
fi

echo ""
echo "=========================================="
echo "  诊断完成"
echo "=========================================="
echo ""
echo "访问地址："
echo "  - 公网: https://rasdmangrhdn.sealosbja.site/admin/login/?next=/admin/"
echo "  - 本地: http://localhost:8001/admin/login/?next=/admin/"
echo ""
echo "如果公网地址无法访问，请检查："
echo "  1. Sealos控制台中的应用状态"
echo "  2. 浏览器控制台的错误信息（F12）"
echo "  3. 浏览器网络标签页的请求状态"
echo "  4. 清除浏览器缓存后重试"
echo ""

