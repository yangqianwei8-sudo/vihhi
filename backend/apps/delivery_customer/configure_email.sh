#!/bin/bash
# 邮件配置脚本

ENV_FILE=".env"
ENV_EXAMPLE="env.example"

echo "=========================================="
echo "邮件配置向导 - whkj@vihgroup.com.cn"
echo "=========================================="
echo ""

# 检查 .env 文件是否存在
if [ ! -f "$ENV_FILE" ]; then
    if [ -f "$ENV_EXAMPLE" ]; then
        echo "正在从 $ENV_EXAMPLE 创建 $ENV_FILE..."
        cp "$ENV_EXAMPLE" "$ENV_FILE"
        echo "✅ 已创建 $ENV_FILE"
    else
        echo "❌ 找不到 $ENV_EXAMPLE 文件"
        exit 1
    fi
fi

echo ""
echo "请提供以下信息："
echo ""

# 读取邮箱密码
read -sp "邮箱密码（whkj@vihgroup.com.cn）: " EMAIL_PASSWORD
echo ""

# 读取 SMTP 服务器（可选，有默认值）
read -p "SMTP 服务器 [smtp.vihgroup.com.cn]: " EMAIL_HOST
EMAIL_HOST=${EMAIL_HOST:-smtp.vihgroup.com.cn}

# 读取 SMTP 端口（可选，有默认值）
read -p "SMTP 端口 [587]: " EMAIL_PORT
EMAIL_PORT=${EMAIL_PORT:-587}

# 读取是否使用 TLS
read -p "使用 TLS？(y/n) [y]: " USE_TLS
USE_TLS=${USE_TLS:-y}

if [ "$USE_TLS" = "y" ] || [ "$USE_TLS" = "Y" ]; then
    EMAIL_USE_TLS="True"
    EMAIL_USE_SSL="False"
else
    EMAIL_USE_TLS="False"
    EMAIL_USE_SSL="False"
fi

echo ""
echo "配置信息："
echo "  SMTP 服务器: $EMAIL_HOST"
echo "  SMTP 端口: $EMAIL_PORT"
echo "  使用 TLS: $EMAIL_USE_TLS"
echo ""

read -p "确认配置？(y/n): " confirm

if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
    echo "已取消"
    exit 0
fi

# 更新 .env 文件
sed -i "s|^EMAIL_BACKEND=.*|EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend|" "$ENV_FILE"
sed -i "s|^EMAIL_HOST=.*|EMAIL_HOST=$EMAIL_HOST|" "$ENV_FILE"
sed -i "s|^EMAIL_PORT=.*|EMAIL_PORT=$EMAIL_PORT|" "$ENV_FILE"
sed -i "s|^EMAIL_HOST_USER=.*|EMAIL_HOST_USER=whkj@vihgroup.com.cn|" "$ENV_FILE"
sed -i "s|^EMAIL_HOST_PASSWORD=.*|EMAIL_HOST_PASSWORD=$EMAIL_PASSWORD|" "$ENV_FILE"
sed -i "s|^EMAIL_USE_TLS=.*|EMAIL_USE_TLS=$EMAIL_USE_TLS|" "$ENV_FILE"
sed -i "s|^EMAIL_USE_SSL=.*|EMAIL_USE_SSL=False|" "$ENV_FILE"
sed -i "s|^DEFAULT_FROM_EMAIL=.*|DEFAULT_FROM_EMAIL=whkj@vihgroup.com.cn|" "$ENV_FILE"

echo ""
echo "✅ 邮件配置已更新到 $ENV_FILE"
echo ""
echo "测试邮件配置："
echo "  python manage.py shell"
echo "  然后执行："
echo "  from django.core.mail import send_mail"
echo "  send_mail('测试', '测试内容', 'whkj@vihgroup.com.cn', ['your-email@example.com'])"
