#!/bin/bash
#
# 启信宝自动填充功能快速测试脚本
# 用于快速验证企业搜索和自动填充功能是否正常
#
# 使用方法:
#   bash quick_test_autofill.sh
#   或
#   ./quick_test_autofill.sh
#

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 项目路径
PROJECT_DIR="/home/devbox/project/vihhi/weihai_tech_production_system"
VENV_PATH="/home/devbox/project/.venv"

echo -e "${BLUE}"
echo "╔════════════════════════════════════════════════════════════════════╗"
echo "║         启信宝企业自动填充功能 - 快速测试                         ║"
echo "╚════════════════════════════════════════════════════════════════════╝"
echo -e "${NC}"
echo ""

# 步骤1: 检查项目目录
echo -e "${YELLOW}[1/6] 检查项目目录...${NC}"
if [ -d "$PROJECT_DIR" ]; then
    echo -e "${GREEN}✓${NC} 项目目录存在: $PROJECT_DIR"
else
    echo -e "${RED}✗${NC} 项目目录不存在: $PROJECT_DIR"
    exit 1
fi
echo ""

# 步骤2: 检查虚拟环境
echo -e "${YELLOW}[2/6] 检查虚拟环境...${NC}"
if [ -d "$VENV_PATH" ]; then
    echo -e "${GREEN}✓${NC} 虚拟环境存在: $VENV_PATH"
    
    # 激活虚拟环境
    source "$VENV_PATH/bin/activate"
    echo -e "${GREEN}✓${NC} 虚拟环境已激活"
else
    echo -e "${RED}✗${NC} 虚拟环境不存在: $VENV_PATH"
    exit 1
fi
echo ""

# 步骤3: 检查API配置
echo -e "${YELLOW}[3/6] 检查API配置...${NC}"
cd "$PROJECT_DIR"

# 检查.env文件
if [ -f ".env" ]; then
    echo -e "${GREEN}✓${NC} .env文件存在"
    
    # 检查API密钥配置
    if grep -q "QIXINBAO_APP_KEY=" .env && grep -q "QIXINBAO_APP_SECRET=" .env; then
        APP_KEY=$(grep "QIXINBAO_APP_KEY=" .env | cut -d '=' -f2 | cut -c1-15)
        if [ -n "$APP_KEY" ] && [ "$APP_KEY" != "your_app_key" ]; then
            echo -e "${GREEN}✓${NC} 启信宝API密钥已配置 ($APP_KEY...)"
        else
            echo -e "${RED}✗${NC} 启信宝API密钥未配置或使用默认值"
            echo "  请在.env文件中设置正确的API密钥"
            exit 1
        fi
    else
        echo -e "${RED}✗${NC} .env文件中缺少API密钥配置"
        exit 1
    fi
else
    echo -e "${RED}✗${NC} .env文件不存在"
    exit 1
fi
echo ""

# 步骤4: 检查IP地址和白名单
echo -e "${YELLOW}[4/6] 检查服务器IP地址...${NC}"
PUBLIC_IP=$(curl -s ifconfig.me 2>/dev/null || curl -s ipinfo.io/ip 2>/dev/null)
if [ -n "$PUBLIC_IP" ]; then
    echo -e "${GREEN}✓${NC} 服务器公网IP: $PUBLIC_IP"
    echo -e "${YELLOW}⚠${NC}  请确保此IP已添加到启信宝API白名单"
else
    echo -e "${YELLOW}⚠${NC}  无法获取公网IP，请手动检查"
fi
echo ""

# 步骤5: 运行基础API测试
echo -e "${YELLOW}[5/6] 运行基础API测试...${NC}"
echo "  测试API配置和企业搜索功能..."
echo ""

# 运行测试脚本（只显示关键输出）
python test_qixinbao_api.py 2>&1 | grep -E "(测试|✓|✗|❌|通过|失败|警告)" | head -20

if [ ${PIPESTATUS[0]} -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✓${NC} 基础API测试完成"
else
    echo ""
    echo -e "${RED}✗${NC} 基础API测试失败"
    echo "  请查看上方错误信息"
fi
echo ""

# 步骤6: 提供完整测试选项
echo -e "${YELLOW}[6/6] 完整功能测试（可选）${NC}"
echo ""
echo "是否运行完整的企业自动填充功能测试？"
echo "  这将测试从搜索到填充的完整流程（大约需要10-30秒）"
echo ""
read -p "运行完整测试？[y/N] " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo -e "${BLUE}开始完整功能测试...${NC}"
    echo ""
    python test_auto_fill_customer.py
    
    if [ $? -eq 0 ]; then
        echo ""
        echo -e "${GREEN}═══════════════════════════════════════════════════════════════════${NC}"
        echo -e "${GREEN}  🎉 完整功能测试通过！企业自动填充功能运行正常。${NC}"
        echo -e "${GREEN}═══════════════════════════════════════════════════════════════════${NC}"
    else
        echo ""
        echo -e "${RED}═══════════════════════════════════════════════════════════════════${NC}"
        echo -e "${RED}  ⚠️  完整功能测试失败，请检查上述错误信息。${NC}"
        echo -e "${RED}═══════════════════════════════════════════════════════════════════${NC}"
    fi
else
    echo ""
    echo -e "${BLUE}跳过完整功能测试${NC}"
    echo ""
    echo "如需稍后运行完整测试，使用以下命令："
    echo "  cd $PROJECT_DIR"
    echo "  source $VENV_PATH/bin/activate"
    echo "  python test_auto_fill_customer.py"
fi

echo ""
echo -e "${BLUE}════════════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  测试完成！${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════════════${NC}"
echo ""
echo "📚 相关文档："
echo "  • 使用指南: docs/启信宝IP白名单配置指南.md"
echo "  • 测试指南: docs/启信宝自动填充功能测试指南.md"
echo "  • API文档: docs/企业信息查询API使用指南.md"
echo ""
echo "🔧 常用命令："
echo "  • 检查API配置: bash check_qixinbao_config.sh"
echo "  • 运行基础测试: python test_qixinbao_api.py"
echo "  • 运行完整测试: python test_auto_fill_customer.py"
echo ""

