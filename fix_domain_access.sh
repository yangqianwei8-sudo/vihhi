#!/bin/bash
# 修复域名访问问题脚本

echo "=========================================="
echo "修复域名访问问题"
echo "=========================================="
echo ""

PROJECT_DIR="/home/devbox/project/vihhi/weihai_tech_production_system"
cd "$PROJECT_DIR" || exit 1

# 1. 检查当前服务状态
echo "1. 检查当前服务状态..."
if ps aux | grep -E "gunicorn.*wsgi|runserver.*8001" | grep -v grep > /dev/null; then
    echo "   ✅ 服务正在运行"
    ps aux | grep -E "gunicorn.*wsgi|runserver.*8001" | grep -v grep | head -2
else
    echo "   ❌ 服务未运行"
fi
echo ""

# 2. 检查端口监听
echo "2. 检查端口监听..."
if netstat -tlnp 2>/dev/null | grep -E ":8001" > /dev/null || ss -tlnp 2>/dev/null | grep -E ":8001" > /dev/null; then
    echo "   ✅ 端口 8001 正在监听"
    netstat -tlnp 2>/dev/null | grep ":8001" || ss -tlnp 2>/dev/null | grep ":8001"
else
    echo "   ❌ 端口 8001 未监听"
fi
echo ""

# 3. 测试本地访问
echo "3. 测试本地访问..."
if curl -s -o /dev/null -w "%{http_code}" http://localhost:8001/health/ | grep -E "200|302" > /dev/null; then
    echo "   ✅ 本地访问正常"
else
    echo "   ❌ 本地访问失败"
fi
echo ""

# 4. 测试域名访问（模拟）
echo "4. 测试域名访问（模拟 Host 头）..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -H "Host: rasdmangrhdn.sealosbja.site" http://localhost:8001/health/)
if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "302" ]; then
    echo "   ✅ 域名访问正常 (HTTP $HTTP_CODE)"
else
    echo "   ⚠️  域名访问返回 HTTP $HTTP_CODE（可能需要重启服务）"
fi
echo ""

# 5. 检查配置
echo "5. 检查配置..."
if grep -q "rasdmangrhdn.sealosbja.site" "$PROJECT_DIR/backend/config/settings.py"; then
    echo "   ✅ settings.py 中已配置域名"
else
    echo "   ❌ settings.py 中未找到域名配置"
fi

if grep -q "from django.conf import settings" "$PROJECT_DIR/backend/config/middleware.py"; then
    echo "   ✅ middleware.py 已修复（使用 Django settings）"
else
    echo "   ❌ middleware.py 需要修复"
fi
echo ""

# 6. 提示重启服务
echo "=========================================="
echo "修复建议："
echo "=========================================="
echo ""
echo "如果域名访问仍然失败，请重启 Django 服务："
echo ""
echo "方式1：如果使用 runserver（开发模式）"
echo "  1. 按 Ctrl+C 停止当前服务"
echo "  2. 运行: cd $PROJECT_DIR"
echo "  3. 运行: source /home/devbox/project/.venv/bin/activate"
echo "  4. 运行: python manage.py runserver 0.0.0.0:8001"
echo ""
echo "方式2：如果使用 Gunicorn（生产模式）"
echo "  1. 运行: cd $PROJECT_DIR"
echo "  2. 运行: bash start_services.sh"
echo ""
echo "方式3：在 Sealos DevBox 控制台"
echo "  1. 点击 '重启' 按钮"
echo ""
echo "=========================================="
echo "测试访问："
echo "=========================================="
echo "修复后，请访问："
echo "  - https://rasdmangrhdn.sealosbja.site"
echo "  - https://rasdmangrhdn.sealosbja.site/health/"
echo ""
