#!/bin/bash
# ODA File Converter 安装脚本
# 用于将DWG文件转换为DXF格式

set -e

echo "=========================================="
echo "ODA File Converter 安装脚本"
echo "=========================================="
echo ""

# 检查系统架构
ARCH=$(uname -m)
if [ "$ARCH" = "x86_64" ]; then
    ARCH_SUFFIX="x64"
elif [ "$ARCH" = "aarch64" ]; then
    ARCH_SUFFIX="arm64"
else
    echo "错误: 不支持的架构 $ARCH"
    exit 1
fi

# 安装目录
INSTALL_DIR="/opt/ODAFileConverter"
BIN_DIR="$INSTALL_DIR/bin"

echo "系统架构: $ARCH"
echo "安装目录: $INSTALL_DIR"
echo ""

# 检查是否已安装
if [ -f "$BIN_DIR/DWGConvert" ]; then
    echo "ODA File Converter 已安装在: $BIN_DIR/DWGConvert"
    echo "版本信息:"
    "$BIN_DIR/DWGConvert" --version 2>&1 || echo "无法获取版本信息"
    exit 0
fi

echo "ODA File Converter 未安装"
echo ""
echo "安装步骤："
echo "1. 访问 ODA 官网: https://www.opendesign.com/guestfiles"
echo "2. 注册账号（免费）"
echo "3. 下载 ODA File Converter Linux 版本"
echo "4. 解压文件到 $INSTALL_DIR"
echo ""
echo "或者，如果您已有下载的文件，请执行以下命令："
echo ""
echo "  sudo mkdir -p $INSTALL_DIR"
echo "  sudo tar -xzf ODAFileConverter_*.tar.gz -C $INSTALL_DIR --strip-components=1"
echo "  sudo chmod +x $BIN_DIR/DWGConvert"
echo ""
echo "然后创建符号链接到系统PATH："
echo "  sudo ln -s $BIN_DIR/DWGConvert /usr/local/bin/DWGConvert"
echo ""
echo "验证安装："
echo "  DWGConvert --version"
echo ""

# 检查是否有下载的文件在当前目录
if ls ODAFileConverter*.tar.gz 2>/dev/null; then
    echo "检测到ODA File Converter安装包，开始安装..."
    sudo mkdir -p "$INSTALL_DIR"
    sudo tar -xzf ODAFileConverter*.tar.gz -C "$INSTALL_DIR" --strip-components=1
    sudo chmod +x "$BIN_DIR/DWGConvert"
    
    # 创建符号链接
    if [ ! -f "/usr/local/bin/DWGConvert" ]; then
        sudo ln -s "$BIN_DIR/DWGConvert" /usr/local/bin/DWGConvert
        echo "已创建符号链接: /usr/local/bin/DWGConvert"
    fi
    
    echo ""
    echo "安装完成！"
    echo "验证安装："
    "$BIN_DIR/DWGConvert" --version || echo "请检查安装是否正确"
else
    echo "未找到安装包，请按照上述步骤手动安装"
fi

