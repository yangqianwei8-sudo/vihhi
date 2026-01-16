#!/bin/bash
# 检查服务器IP地址，用于配置启信宝IP白名单

echo "=========================================="
echo "  服务器IP地址检查（用于启信宝IP白名单）"
echo "=========================================="
echo ""

echo "1. 公网IP地址（需要添加到启信宝白名单）："
PUBLIC_IP=$(curl -s ifconfig.me 2>/dev/null || curl -s ipinfo.io/ip 2>/dev/null || echo "无法获取")
echo "   $PUBLIC_IP"
echo ""

echo "2. 内网IP地址（仅供参考）："
LOCAL_IP=$(hostname -I 2>/dev/null | awk '{print $1}' || ip addr show 2>/dev/null | grep -E "inet.*global" | awk '{print $2}' | cut -d/ -f1 | head -1 || echo "无法获取")
echo "   $LOCAL_IP"
echo ""

echo "3. 网络接口信息："
ip addr show 2>/dev/null | grep -E "inet " | grep -v "127.0.0.1" | awk '{print "   " $2}' || ifconfig 2>/dev/null | grep "inet " | grep -v "127.0.0.1" | awk '{print "   " $2}' || echo "   无法获取"
echo ""

echo "=========================================="
echo "  配置说明"
echo "=========================================="
echo "请在启信宝开放平台添加以下IP地址到白名单："
echo ""
echo "  $PUBLIC_IP"
echo ""
echo "配置路径："
echo "  启信宝开放平台 → 我的API → APP KEY → 配置 → IP白名单"
echo ""
echo "配置完成后，运行以下命令测试："
echo "  cd /home/devbox/project/vihhi/weihai_tech_production_system"
echo "  python test_qixinbao_api.py"
echo "=========================================="
