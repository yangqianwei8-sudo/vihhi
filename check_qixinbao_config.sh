#!/bin/bash
# 启信宝API配置检查脚本
# 根据 docs/启信宝API配置说明.md 进行配置验证

echo "=========================================="
echo "启信宝API配置检查"
echo "=========================================="
echo ""

# 获取当前服务器公网IP
echo "1. 当前服务器公网IP："
PUBLIC_IP=$(curl -s ifconfig.me 2>/dev/null || curl -s ipinfo.io/ip 2>/dev/null || echo "无法获取")
echo "   $PUBLIC_IP"
echo ""

echo "2. 需要添加到启信宝IP白名单的IP："
echo "   $PUBLIC_IP"
echo "   配置路径：启信宝开放平台 -> 个人中心 -> 安全中心 -> API IP白名单设置"
echo ""

# 检查.env文件中的配置
echo "3. 检查.env文件配置："
cd "$(dirname "$0")" || exit 1

if [ ! -f .env ]; then
    echo "   ❌ .env文件不存在，请先创建：cp env.example .env"
    exit 1
fi

# 检查配置项
APP_KEY=$(grep "^QIXINBAO_APP_KEY=" .env | cut -d'=' -f2 | tr -d '"' | tr -d "'")
APP_SECRET=$(grep "^QIXINBAO_APP_SECRET=" .env | cut -d'=' -f2 | tr -d '"' | tr -d "'")
API_BASE_URL=$(grep "^QIXINBAO_API_BASE_URL=" .env | cut -d'=' -f2 | tr -d '"' | tr -d "'")
API_TIMEOUT=$(grep "^QIXINBAO_API_TIMEOUT=" .env | cut -d'=' -f2 | tr -d '"' | tr -d "'")

if [ -z "$APP_KEY" ] || [ "$APP_KEY" = "your_app_key_here" ]; then
    echo "   ❌ QIXINBAO_APP_KEY 未配置或使用默认值"
else
    echo "   ✓ QIXINBAO_APP_KEY: ${APP_KEY:0:20}..."
fi

if [ -z "$APP_SECRET" ] || [ "$APP_SECRET" = "your_app_secret_here" ]; then
    echo "   ❌ QIXINBAO_APP_SECRET 未配置或使用默认值"
else
    echo "   ✓ QIXINBAO_APP_SECRET: 已配置"
fi

if [ -z "$API_BASE_URL" ]; then
    echo "   ⚠️  QIXINBAO_API_BASE_URL 未配置，将使用默认值"
else
    echo "   ✓ QIXINBAO_API_BASE_URL: $API_BASE_URL"
fi

if [ -z "$API_TIMEOUT" ]; then
    echo "   ⚠️  QIXINBAO_API_TIMEOUT 未配置，将使用默认值10秒"
else
    echo "   ✓ QIXINBAO_API_TIMEOUT: ${API_TIMEOUT}秒"
fi

echo ""

# 使用Django验证配置
echo "4. Django配置验证："
source /home/devbox/project/.venv/bin/activate 2>/dev/null || echo "   警告：无法激活虚拟环境"
python3 << PYTHON_SCRIPT
import os
import sys
sys.path.insert(0, '/home/devbox/project/vihhi/weihai_tech_production_system')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.config.settings')

try:
    import django
    django.setup()
    from django.conf import settings
    
    app_key = getattr(settings, 'QIXINBAO_APP_KEY', '')
    app_secret = getattr(settings, 'QIXINBAO_APP_SECRET', '')
    api_base_url = getattr(settings, 'QIXINBAO_API_BASE_URL', '')
    api_timeout = getattr(settings, 'QIXINBAO_API_TIMEOUT', '')
    
    if app_key and app_secret:
        print(f"   ✓ Django配置已加载")
        print(f"   ✓ AppKey: {app_key[:20]}...")
        print(f"   ✓ AppSecret: 已配置")
        print(f"   ✓ API Base URL: {api_base_url}")
        print(f"   ✓ API Timeout: {api_timeout}秒")
    else:
        print("   ❌ Django配置未完整")
        print(f"   AppKey: {'已配置' if app_key else '未配置'}")
        print(f"   AppSecret: {'已配置' if app_secret else '未配置'}")
except Exception as e:
    print(f"   ❌ Django配置验证失败: {str(e)}")
PYTHON_SCRIPT

echo ""
echo "=========================================="
echo "配置检查完成"
echo "=========================================="
echo ""
echo "重要提示："
echo "1. 如果API调用失败，请检查IP白名单配置"
echo "2. 需要在启信宝平台添加IP白名单：$PUBLIC_IP"
echo "3. IP白名单配置后需要等待5-10分钟生效"
echo "4. 详细配置说明请参考：docs/启信宝API配置说明.md"
echo ""

