#!/bin/bash
# 发票OCR识别功能依赖安装脚本

set -e

echo "=========================================="
echo "发票OCR识别功能 - 依赖安装脚本"
echo "=========================================="
echo ""

# 检查是否为root用户
if [ "$EUID" -eq 0 ]; then 
   echo "⚠️  请不要使用root用户运行此脚本"
   exit 1
fi

# 1. 检查并安装系统依赖
echo "步骤 1/4: 检查系统依赖..."
echo "----------------------------------------"

# 检查poppler-utils
if command -v pdftoppm &> /dev/null; then
    echo "✓ poppler-utils 已安装"
else
    echo "正在安装 poppler-utils..."
    sudo apt-get update
    sudo apt-get install -y poppler-utils
    echo "✓ poppler-utils 安装完成"
fi

# 检查tesseract（可选）
if command -v tesseract &> /dev/null; then
    echo "✓ tesseract 已安装"
    tesseract --version | head -1
else
    echo "⚠️  tesseract 未安装（可选，PaddleOCR是主要引擎）"
fi

echo ""

# 2. 检查Python虚拟环境
echo "步骤 2/4: 检查Python环境..."
echo "----------------------------------------"

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

if [ -d "$PROJECT_ROOT/venv" ]; then
    echo "✓ 找到虚拟环境: $PROJECT_ROOT/venv"
    VENV_PATH="$PROJECT_ROOT/venv"
elif [ -d "$PROJECT_ROOT/.venv" ]; then
    echo "✓ 找到虚拟环境: $PROJECT_ROOT/.venv"
    VENV_PATH="$PROJECT_ROOT/.venv"
else
    echo "❌ 未找到虚拟环境，请先创建虚拟环境"
    exit 1
fi

echo ""

# 3. 安装Python依赖
echo "步骤 3/4: 安装Python OCR依赖..."
echo "----------------------------------------"

source "$VENV_PATH/bin/activate"

echo "正在安装 paddleocr..."
pip install -q paddleocr>=2.7.0

echo "正在安装 pdf2image..."
pip install -q pdf2image>=1.16.3

echo "正在安装 pytesseract..."
pip install -q pytesseract>=0.3.10

echo "✓ Python依赖安装完成"
echo ""

# 4. 验证安装
echo "步骤 4/4: 验证安装..."
echo "----------------------------------------"

python -c "import paddleocr; print('✓ PaddleOCR 导入成功')" 2>/dev/null || echo "❌ PaddleOCR 导入失败"
python -c "import pdf2image; print('✓ pdf2image 导入成功')" 2>/dev/null || echo "❌ pdf2image 导入失败"
python -c "import pytesseract; print('✓ pytesseract 导入成功')" 2>/dev/null || echo "❌ pytesseract 导入失败"

echo ""
echo "=========================================="
echo "✓ 安装完成！"
echo "=========================================="
echo ""
echo "使用说明："
echo "1. 在发票创建/编辑页面，选择发票文件（PDF或图片）"
echo "2. 点击'智能识别'按钮"
echo "3. 系统会自动识别并填充发票信息"
echo ""
echo "注意事项："
echo "- 首次使用PaddleOCR时会下载模型文件（约80MB），需要一些时间"
echo "- 识别准确率受图片质量影响，建议使用清晰的发票图片"
echo "- 识别结果仅供参考，重要信息请人工核对"
echo ""

