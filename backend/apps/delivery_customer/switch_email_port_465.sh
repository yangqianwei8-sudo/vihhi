#!/bin/bash
# 切换到端口465配置（SSL，根据页面推荐）

ENV_FILE=".env"

echo "正在切换到端口465配置（SSL）..."
echo "根据腾讯企业邮箱设置页面推荐：smtp.exmail.qq.com (使用SSL, 端口号465)"

# 备份当前配置
cp "$ENV_FILE" "${ENV_FILE}.backup.$(date +%Y%m%d_%H%M%S)"

# 更新配置
sed -i 's/EMAIL_PORT=587/EMAIL_PORT=465/' "$ENV_FILE"
sed -i 's/EMAIL_USE_SSL=False/EMAIL_USE_SSL=True/' "$ENV_FILE"
sed -i 's/EMAIL_USE_TLS=True/EMAIL_USE_TLS=False/' "$ENV_FILE"

echo "✅ 已切换到端口465 + SSL配置"
echo ""
echo "新配置："
grep "^EMAIL_" "$ENV_FILE"
echo ""
echo "请重启 Django 服务后重新测试"
