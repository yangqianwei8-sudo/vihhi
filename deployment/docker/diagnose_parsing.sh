#!/bin/bash
# 全面诊断 CAD 解析问题

echo "🔍 全面诊断 CAD 解析问题..."
echo "=================================="
echo ""

# 1. 检查容器中的代码版本
echo "1. 检查代码版本和关键文件："
echo "-----------------------------------"
if [ -f /app/backend/apps/production_management/views_pages.py ]; then
    echo "✓ views_pages.py 存在"
    # 检查是否有 _update_parse_progress 函数
    if grep -q "def _update_parse_progress" /app/backend/apps/production_management/views_pages.py; then
        echo "✓ _update_parse_progress 函数存在"
        # 检查函数签名
        if grep -q "def _update_parse_progress(material_id" /app/backend/apps/production_management/views_pages.py; then
            echo "✓ 函数签名正确（使用 material_id）"
        else
            echo "✗ 函数签名可能不正确"
        fi
    else
        echo "✗ _update_parse_progress 函数不存在"
    fi
else
    echo "✗ views_pages.py 不存在"
fi

echo ""
echo "2. 检查数据库连接和迁移："
echo "-----------------------------------"
python3 /app/manage.py shell -c "
from django.db import connection
from backend.apps.production_management.models import PreOptimizationMaterial
try:
    # 测试数据库连接
    connection.ensure_connection()
    print('✓ 数据库连接正常')
    
    # 检查表是否存在
    from django.db import connection
    cursor = connection.cursor()
    cursor.execute(\"SELECT column_name FROM information_schema.columns WHERE table_name='production_management_pre_optimization_material' AND column_name='parse_progress_message'\")
    if cursor.fetchone():
        print('✓ parse_progress_message 字段存在')
    else:
        print('✗ parse_progress_message 字段不存在')
    
    # 检查最近的记录
    materials = PreOptimizationMaterial.objects.all().order_by('-id')[:5]
    print(f'✓ 找到 {materials.count()} 条记录')
    for m in materials:
        print(f'  ID: {m.id}, 状态: {m.parse_status}, 进度: {m.parse_progress}%, 消息: {m.parse_progress_message[:30] if m.parse_progress_message else \"无\"}')
except Exception as e:
    print(f'✗ 数据库检查失败: {e}')
" 2>&1

echo ""
echo "3. 检查解析任务是否在运行："
echo "-----------------------------------"
# 检查 Python 进程
ps aux | grep -E "python.*manage.py|gunicorn" | grep -v grep || echo "未找到 Python 进程"

# 检查是否有解析相关的进程
ps aux | grep -i "parse\|cad\|dwg" | grep -v grep || echo "未找到解析相关进程"

echo ""
echo "4. 检查 ODA File Converter："
echo "-----------------------------------"
if [ -f /opt/ODAFileConverter/ODAFileConverter ]; then
    echo "✓ ODAFileConverter 存在"
    ls -lh /opt/ODAFileConverter/ODAFileConverter
else
    echo "✗ ODAFileConverter 不存在"
fi

if [ -f /usr/local/bin/DWGConvert ]; then
    echo "✓ DWGConvert 符号链接存在"
    ls -lh /usr/local/bin/DWGConvert
else
    echo "✗ DWGConvert 符号链接不存在"
fi

# 检查 xvfb
if command -v xvfb-run >/dev/null 2>&1; then
    echo "✓ xvfb-run 可用"
else
    echo "✗ xvfb-run 不可用"
fi

echo ""
echo "5. 检查日志输出："
echo "-----------------------------------"
# 检查最近的日志
if [ -f /tmp/django_debug.log ]; then
    echo "✓ Django 日志文件存在"
    echo "最近 20 行日志："
    tail -20 /tmp/django_debug.log
else
    echo "✗ Django 日志文件不存在"
fi

# 检查系统日志
echo ""
echo "最近的系统日志（包含 CAD 或 parse）："
journalctl -u gunicorn --no-pager -n 50 2>/dev/null | grep -i "cad\|parse" | tail -10 || echo "未找到相关日志"

echo ""
echo "6. 检查环境变量："
echo "-----------------------------------"
echo "DATABASE_URL: ${DATABASE_URL:0:50}..."
echo "DISPLAY: $DISPLAY"
echo "QT_PLUGIN_PATH: $QT_PLUGIN_PATH"
echo "LD_LIBRARY_PATH: $LD_LIBRARY_PATH"

echo ""
echo "7. 检查解析任务触发："
echo "-----------------------------------"
python3 /app/manage.py shell -c "
from backend.apps.production_management.models import PreOptimizationMaterial
import threading

# 检查是否有 pending 或 processing 状态的记录
materials = PreOptimizationMaterial.objects.filter(parse_status__in=['pending', 'processing'])
print(f'找到 {materials.count()} 条待解析或解析中的记录：')
for m in materials:
    print(f'  ID: {m.id}, 状态: {m.parse_status}, 进度: {m.parse_progress}%, 创建时间: {m.uploaded_time}')
    print(f'    文件: {m.file_name}')

# 检查活跃线程
print(f'\\n活跃线程数: {threading.active_count()}')
for thread in threading.enumerate():
    if 'parse' in thread.name.lower() or 'cad' in thread.name.lower():
        print(f'  发现解析相关线程: {thread.name}')
" 2>&1

echo ""
echo "8. 测试解析服务初始化："
echo "-----------------------------------"
python3 /app/manage.py shell -c "
import sys
sys.path.insert(0, '/app')
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.config.settings')
import django
django.setup()

from backend.apps.production_management.services.cad_parser_service import CADParserService

try:
    parser = CADParserService()
    print(f'✓ CADParserService 初始化成功')
    print(f'  cad2image_available: {parser.cad2image_available}')
    print(f'  converter_cmd: {parser._get_converter_command()}')
except Exception as e:
    print(f'✗ CADParserService 初始化失败: {e}')
    import traceback
    traceback.print_exc()
" 2>&1

echo ""
echo "=================================="
echo "✅ 诊断完成！"
echo ""
echo "💡 根据诊断结果，可能的问题："
echo "   1. 如果代码版本不对，需要更新容器镜像"
echo "   2. 如果数据库字段不存在，需要运行迁移"
echo "   3. 如果解析任务没有运行，检查任务触发逻辑"
echo "   4. 如果日志没有输出，检查日志配置和输出重定向"

