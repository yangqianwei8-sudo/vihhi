#!/bin/bash
# 简单的邮件测试脚本

cd /home/devbox/project/vihhi/weihai_tech_production_system
source venv/bin/activate

echo "=========================================="
echo "邮件配置测试"
echo "=========================================="
echo ""

python manage.py shell << 'PYTHON_EOF'
from django.core.mail import send_mail
from django.conf import settings

print("当前邮件配置：")
print(f"  EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
print(f"  EMAIL_HOST: {settings.EMAIL_HOST}")
print(f"  EMAIL_PORT: {settings.EMAIL_PORT}")
print(f"  EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
print(f"  EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}")
print(f"  EMAIL_USE_SSL: {settings.EMAIL_USE_SSL}")
print(f"  DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")
print(f"  密码: {'已配置' if settings.EMAIL_HOST_PASSWORD else '未配置'}")
print("")

test_email = input("请输入测试邮箱地址: ").strip()

if not test_email:
    print("未输入测试邮箱地址")
    exit()

try:
    print(f"\n正在发送测试邮件到 {test_email}...")
    
    send_mail(
        subject='【测试】发文跟踪系统邮件配置测试',
        message='这是一封测试邮件，用于验证邮件配置是否正确。\n\n如果您收到这封邮件，说明邮件配置成功！',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[test_email],
        fail_silently=False,
    )
    
    print("✅ 测试邮件发送成功！")
    print(f"请检查 {test_email} 的收件箱（包括垃圾邮件文件夹）")
    
except Exception as e:
    print(f"❌ 邮件发送失败：{str(e)}")
    print("\n可能的原因：")
    print("  1. 邮箱密码错误")
    print("  2. 需要开启 IMAP/SMTP 服务（在邮箱设置中）")
    print("  3. 网络连接问题")
    print("  4. SMTP 服务器配置错误")
PYTHON_EOF
