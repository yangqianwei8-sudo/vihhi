#!/bin/bash
# 切换到端口587配置（如果465不行）

ENV_FILE=".env"

echo "正在切换到端口587配置..."

# 备份当前配置
cp "$ENV_FILE" "${ENV_FILE}.backup.$(date +%Y%m%d_%H%M%S)"

# 更新配置
sed -i 's/EMAIL_PORT=465/EMAIL_PORT=587/' "$ENV_FILE"
sed -i 's/EMAIL_USE_SSL=True/EMAIL_USE_SSL=False/' "$ENV_FILE"
sed -i 's/EMAIL_USE_TLS=False/EMAIL_USE_TLS=True/' "$ENV_FILE"

echo "✅ 已切换到端口587 + TLS配置"
echo ""
echo "新配置："
grep "^EMAIL_" "$ENV_FILE"
echo ""
echo "请重启 Django 服务后重新测试"
