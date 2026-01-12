#!/bin/bash
# 数据库同步配置脚本
# 在所有电脑上运行此脚本，确保连接到同一个数据库

echo "=========================================="
echo "数据库同步配置"
echo "=========================================="
echo ""

# 数据库连接信息（根据实际情况修改）
DB_HOST="dbconn.sealosbja.site"
DB_PORT="38013"
DB_NAME="postgres"
DB_USER="postgres"
DB_PASSWORD="zdg7xx28"

# 构建连接字符串
DATABASE_URL="postgresql://${DB_USER}:${DB_PASSWORD}@${DB_HOST}:${DB_PORT}/${DB_NAME}"

echo "配置数据库连接..."
echo "主机: ${DB_HOST}"
echo "端口: ${DB_PORT}"
echo "数据库: ${DB_NAME}"
echo "用户: ${DB_USER}"
echo ""

# 设置环境变量（当前会话）
export DATABASE_URL="${DATABASE_URL}"
echo "✅ 已设置当前会话的 DATABASE_URL 环境变量"

# 添加到 ~/.bashrc（永久保存）
if ! grep -q "DATABASE_URL.*${DB_HOST}" ~/.bashrc 2>/dev/null; then
    echo "" >> ~/.bashrc
    echo "# 数据库连接配置 - 维海科技系统" >> ~/.bashrc
    echo "export DATABASE_URL=\"${DATABASE_URL}\"" >> ~/.bashrc
    echo "✅ 已添加到 ~/.bashrc（永久保存）"
else
    echo "⚠️  ~/.bashrc 中已存在 DATABASE_URL 配置"
fi

# 添加到 ~/.zshrc（如果使用 zsh）
if [ -f ~/.zshrc ] && ! grep -q "DATABASE_URL.*${DB_HOST}" ~/.zshrc 2>/dev/null; then
    echo "" >> ~/.zshrc
    echo "# 数据库连接配置 - 维海科技系统" >> ~/.zshrc
    echo "export DATABASE_URL=\"${DATABASE_URL}\"" >> ~/.zshrc
    echo "✅ 已添加到 ~/.zshrc（永久保存）"
fi

echo ""
echo "=========================================="
echo "验证配置"
echo "=========================================="
echo ""

# 检查项目目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

if [ -f "${PROJECT_DIR}/manage.py" ]; then
    cd "${PROJECT_DIR}"
    echo "运行配置检查脚本..."
    python scripts/check_database_sync.py
else
    echo "⚠️  未找到项目目录，请手动运行:"
    echo "   cd /path/to/project"
    echo "   python scripts/check_database_sync.py"
fi

echo ""
echo "=========================================="
echo "配置完成！"
echo "=========================================="
echo ""
echo "下一步："
echo "1. 重新打开终端，或运行: source ~/.bashrc"
echo "2. 运行验证脚本: python scripts/sync_verification.py"
echo "3. 在其他电脑上重复此配置"
echo ""

