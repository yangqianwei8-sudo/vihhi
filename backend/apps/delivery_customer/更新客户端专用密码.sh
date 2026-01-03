#!/bin/bash
# 更新客户端专用密码到 .env 文件

ENV_FILE=".env"

if [ -z "$1" ]; then
    echo "用法: $0 <客户端专用密码>"
    echo ""
    echo "示例:"
    echo "  $0 abc123def456ghi7"
    echo ""
    echo "或者交互式输入："
    read -sp "请输入客户端专用密码: " CLIENT_PASSWORD
    echo ""
else
    CLIENT_PASSWORD="$1"
fi

if [ -z "$CLIENT_PASSWORD" ]; then
    echo "❌ 错误：未提供客户端专用密码"
    exit 1
fi

# 备份当前配置
cp "$ENV_FILE" "${ENV_FILE}.backup.$(date +%Y%m%d_%H%M%S)"

# 更新密码
if grep -q "^EMAIL_HOST_PASSWORD=" "$ENV_FILE"; then
    sed -i "s|^EMAIL_HOST_PASSWORD=.*|EMAIL_HOST_PASSWORD=$CLIENT_PASSWORD|" "$ENV_FILE"
else
    echo "EMAIL_HOST_PASSWORD=$CLIENT_PASSWORD" >> "$ENV_FILE"
fi

echo "✅ 客户端专用密码已更新"
echo ""
echo "当前邮件配置："
grep "^EMAIL_" "$ENV_FILE" | grep -v "PASSWORD"
echo "EMAIL_HOST_PASSWORD=***（已隐藏）"
echo ""
echo "请重新测试邮件发送："
echo "  bash backend/apps/delivery_customer/快速测试邮件_31972849.sh"
