#!/bin/bash
# 发票OCR识别功能依赖安装脚本
# 使用方法: bash install_ocr_dependencies.sh

set -e

echo "=========================================="
echo "发票OCR识别功能 - 依赖安装脚本"
echo "=========================================="
echo ""

# 检查是否为root用户
if [ "$EUID" -ne 0 ]; then 
    echo "⚠️  需要sudo权限来安装系统依赖"
    echo ""
fi

# 步骤1: 安装系统依赖
echo "📦 步骤1: 安装系统依赖..."
echo ""

# 检测操作系统类型
if [ -f /etc/debian_version ]; then
    # Debian/Ubuntu系统
    echo "检测到 Debian/Ubuntu 系统"
    echo "安装 poppler-utils (PDF转图片)..."
    sudo apt-get update
    sudo apt-get install -y poppler-utils
    
    echo "安装 tesseract-ocr (可选，备选OCR引擎)..."
    sudo apt-get install -y tesseract-ocr tesseract-ocr-chi-sim
    
elif [ -f /etc/redhat-release ]; then
    # CentOS/RHEL系统
    echo "检测到 CentOS/RHEL 系统"
    echo "安装 poppler-utils..."
    sudo yum install -y poppler-utils
    
    echo "安装 tesseract-ocr..."
    sudo yum install -y tesseract tesseract-langpack-chi_sim
    
elif [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS系统
    echo "检测到 macOS 系统"
    echo "请使用 Homebrew 安装:"
    echo "  brew install poppler"
    echo "  brew install tesseract tesseract-lang"
    echo ""
    read -p "是否已安装上述依赖? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "请先安装依赖后再运行此脚本"
        exit 1
    fi
else
    echo "⚠️  未识别的操作系统，请手动安装以下依赖:"
    echo "  - poppler-utils (PDF转图片)"
    echo "  - tesseract-ocr (可选)"
    echo ""
fi

echo ""
echo "✅ 系统依赖安装完成"
echo ""

# 步骤2: 检查Python虚拟环境
echo "📦 步骤2: 检查Python环境..."
echo ""

if [ -d "venv" ]; then
    echo "找到虚拟环境: venv"
    VENV_PATH="venv"
elif [ -d ".venv" ]; then
    echo "找到虚拟环境: .venv"
    VENV_PATH=".venv"
else
    echo "⚠️  未找到虚拟环境，将使用系统Python"
    VENV_PATH=""
fi

# 步骤3: 安装Python依赖
echo ""
echo "📦 步骤3: 安装Python依赖..."
echo ""

if [ -n "$VENV_PATH" ]; then
    echo "激活虚拟环境: $VENV_PATH"
    source "$VENV_PATH/bin/activate"
fi

echo "安装 paddleocr..."
pip install paddleocr

echo "安装 paddlepaddle (PaddleOCR依赖)..."
pip install paddlepaddle

echo "安装 pdf2image..."
pip install pdf2image

echo "安装 pytesseract..."
pip install pytesseract

echo ""
echo "✅ Python依赖安装完成"
echo ""

# 步骤4: 验证安装
echo "📦 步骤4: 验证安装..."
echo ""

echo "检查 poppler-utils..."
if command -v pdftoppm &> /dev/null; then
    echo "  ✅ poppler-utils 已安装"
else
    echo "  ❌ poppler-utils 未安装"
fi

echo "检查 tesseract..."
if command -v tesseract &> /dev/null; then
    echo "  ✅ tesseract 已安装"
    tesseract --version | head -1
else
    echo "  ⚠️  tesseract 未安装（可选）"
fi

echo "检查 Python 模块..."
python3 -c "import paddleocr; print('  ✅ paddleocr 已安装')" 2>/dev/null || echo "  ❌ paddleocr 未安装"
python3 -c "import pdf2image; print('  ✅ pdf2image 已安装')" 2>/dev/null || echo "  ❌ pdf2image 未安装"
python3 -c "import pytesseract; print('  ✅ pytesseract 已安装')" 2>/dev/null || echo "  ❌ pytesseract 未安装"

echo ""
echo "=========================================="
echo "✅ 安装完成！"
echo "=========================================="
echo ""
echo "📝 注意事项:"
echo "1. PaddleOCR首次使用时会自动下载模型（约100MB），需要几分钟时间"
echo "2. 如果PaddleOCR初始化失败，系统会自动使用Tesseract OCR作为备选"
echo "3. 详细使用说明请查看: docs/发票智能识别功能说明.md"
echo ""
echo "🚀 现在可以在发票管理页面使用智能识别功能了！"
echo ""

