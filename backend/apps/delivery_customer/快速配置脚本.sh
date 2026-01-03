#!/bin/bash
# 发文跟踪定时任务快速配置脚本

PROJECT_DIR="/home/devbox/project/vihhi/weihai_tech_production_system"
VENV_PYTHON="$PROJECT_DIR/venv/bin/python"
SERVICE_NAME="delivery-tracking-update"

echo "=========================================="
echo "发文跟踪定时任务配置脚本"
echo "=========================================="
echo ""

# 检查 systemd 是否可用
if ! command -v systemctl &> /dev/null; then
    echo "❌ 系统不支持 systemd，请使用其他方式配置"
    exit 1
fi

echo "✅ 检测到 systemd 可用"
echo ""

# 选择配置方式
echo "请选择配置方式："
echo "1. 使用 Systemd Timer（推荐）"
echo "2. 安装并使用 Crontab"
echo "3. 仅创建配置文件，不启用"
read -p "请输入选项 (1-3): " choice

case $choice in
    1)
        echo ""
        echo "正在配置 Systemd Timer..."
        
        # 创建 Service 文件
        sudo tee /etc/systemd/system/${SERVICE_NAME}.service > /dev/null <<EOF
[Unit]
Description=发文跟踪状态更新服务
After=network.target

[Service]
Type=oneshot
User=$(whoami)
WorkingDirectory=${PROJECT_DIR}
Environment="PATH=${PROJECT_DIR}/venv/bin"
ExecStart=${VENV_PYTHON} manage.py update_tracking_status --limit 50
StandardOutput=journal
StandardError=journal
EOF

        # 创建 Timer 文件
        sudo tee /etc/systemd/system/${SERVICE_NAME}.timer > /dev/null <<EOF
[Unit]
Description=发文跟踪状态更新定时器
Requires=${SERVICE_NAME}.service

[Timer]
OnCalendar=*:0/30
Persistent=true

[Install]
WantedBy=timers.target
EOF

        # 重新加载并启用
        sudo systemctl daemon-reload
        sudo systemctl enable ${SERVICE_NAME}.timer
        sudo systemctl start ${SERVICE_NAME}.timer
        
        echo ""
        echo "✅ Systemd Timer 配置完成！"
        echo ""
        echo "查看状态："
        echo "  sudo systemctl status ${SERVICE_NAME}.timer"
        echo ""
        echo "查看日志："
        echo "  sudo journalctl -u ${SERVICE_NAME}.service -f"
        ;;
        
    2)
        echo ""
        echo "正在安装 cron..."
        
        if command -v apt-get &> /dev/null; then
            sudo apt-get update
            sudo apt-get install -y cron
            sudo systemctl enable cron
            sudo systemctl start cron
        elif command -v yum &> /dev/null; then
            sudo yum install -y cronie
            sudo systemctl enable crond
            sudo systemctl start crond
        else
            echo "❌ 无法自动安装 cron，请手动安装"
            exit 1
        fi
        
        echo ""
        echo "✅ cron 安装完成"
        echo ""
        echo "请手动编辑 crontab："
        echo "  crontab -e"
        echo ""
        echo "添加以下内容："
        echo "  */30 * * * * cd ${PROJECT_DIR} && ${VENV_PYTHON} manage.py update_tracking_status --limit 50 >> /tmp/delivery_tracking.log 2>&1"
        ;;
        
    3)
        echo ""
        echo "正在创建配置文件..."
        
        # 创建 Service 文件（不启用）
        sudo tee /etc/systemd/system/${SERVICE_NAME}.service > /dev/null <<EOF
[Unit]
Description=发文跟踪状态更新服务
After=network.target

[Service]
Type=oneshot
User=$(whoami)
WorkingDirectory=${PROJECT_DIR}
Environment="PATH=${PROJECT_DIR}/venv/bin"
ExecStart=${VENV_PYTHON} manage.py update_tracking_status --limit 50
StandardOutput=journal
StandardError=journal
EOF

        # 创建 Timer 文件（不启用）
        sudo tee /etc/systemd/system/${SERVICE_NAME}.timer > /dev/null <<EOF
[Unit]
Description=发文跟踪状态更新定时器
Requires=${SERVICE_NAME}.service

[Timer]
OnCalendar=*:0/30
Persistent=true

[Install]
WantedBy=timers.target
EOF

        sudo systemctl daemon-reload
        
        echo ""
        echo "✅ 配置文件已创建"
        echo ""
        echo "手动启用："
        echo "  sudo systemctl enable ${SERVICE_NAME}.timer"
        echo "  sudo systemctl start ${SERVICE_NAME}.timer"
        ;;
        
    *)
        echo "❌ 无效选项"
        exit 1
        ;;
esac

echo ""
echo "=========================================="
echo "配置完成！"
echo "=========================================="
