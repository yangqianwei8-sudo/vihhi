#!/bin/bash
# 快速测试邮件发送到 31972849@qq.com

cd /home/devbox/project/vihhi/weihai_tech_production_system
source venv/bin/activate

echo "=========================================="
echo "测试邮件发送到 31972849@qq.com"
echo "=========================================="
echo ""

python manage.py shell << 'PYTHON_EOF'
from django.core.mail import send_mail
from django.conf import settings

print(f"发送方：{settings.DEFAULT_FROM_EMAIL}")
print(f"接收方：31972849@qq.com")
print(f"SMTP：{settings.EMAIL_HOST}:{settings.EMAIL_PORT}")
print("")

try:
    send_mail(
        subject='【测试】发文跟踪系统邮件配置测试',
        message='这是一封测试邮件，用于验证邮件配置是否正确。\n\n'
               f'发送方：{settings.DEFAULT_FROM_EMAIL}\n'
               '如果您收到这封邮件，说明邮件配置成功！\n\n'
               '此邮件由维海科技信息化管理平台自动发送。',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=['31972849@qq.com'],
        fail_silently=False,
    )
    
    print("✅ 测试邮件发送成功！")
    print("请检查 31972849@qq.com 的收件箱（包括垃圾邮件文件夹）")
    
except Exception as e:
    print(f"❌ 邮件发送失败：{str(e)}")
    print("")
    print("请确认：")
    print("  1. 已在邮箱后台开启 IMAP/SMTP 服务")
    print("  2. 等待 1-2 分钟让设置生效")
    print("  3. 密码是否正确")
PYTHON_EOF
