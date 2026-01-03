#!/bin/bash
# 测试解析任务启动

echo "🔍 测试解析任务启动..."
echo ""

# 1. 检查最新的 material
echo "1. 查找最新的优化前资料："
python3 /app/manage.py shell -c "
from backend.apps.production_management.models import PreOptimizationMaterial
material = PreOptimizationMaterial.objects.order_by('-id').first()
if material:
    print(f'找到 Material ID: {material.id}')
    print(f'文件名: {material.file_name}')
    print(f'状态: {material.parse_status}')
    print(f'进度: {material.parse_progress}%')
else:
    print('没有找到任何记录')
" 2>&1

echo ""
echo "2. 测试解析任务启动逻辑："
python3 /app/manage.py shell -c "
import sys
import threading
from backend.apps.production_management.models import PreOptimizationMaterial
from backend.apps.production_management.services.cad_parser_service import CADParserService

material = PreOptimizationMaterial.objects.order_by('-id').first()
if not material:
    print('没有找到记录')
    sys.exit(1)

print(f'测试 Material ID: {material.id}')

def test_parse():
    try:
        print('[测试] 解析任务开始', flush=True)
        sys.stdout.flush()
        
        # 更新状态
        material = PreOptimizationMaterial.objects.get(id=${material.id})
        material.parse_status = 'processing'
        material.parse_progress = 10
        material.parse_progress_message = '测试中...'
        material.save()
        print('[测试] 状态已更新', flush=True)
        sys.stdout.flush()
        
        # 测试 CADParserService
        parser = CADParserService()
        print(f'[测试] CADParserService 创建成功，cad2image_available: {parser.cad2image_available}', flush=True)
        sys.stdout.flush()
        
    except Exception as e:
        import traceback
        print(f'[测试] 异常: {e}', flush=True)
        print(f'[测试] 堆栈: {traceback.format_exc()}', flush=True)
        sys.stdout.flush()

# 启动线程
thread = threading.Thread(target=test_parse)
thread.daemon = True
thread.start()
print('[测试] 线程已启动', flush=True)
sys.stdout.flush()

# 等待一下
import time
time.sleep(3)

# 检查状态
material = PreOptimizationMaterial.objects.get(id=${material.id})
print(f'[测试] 最终状态: {material.parse_status}, 进度: {material.parse_progress}%', flush=True)
" 2>&1

echo ""
echo "3. 检查日志配置："
python3 /app/manage.py shell -c "
import logging
logger = logging.getLogger('backend.apps.production_management.views_pages')
print(f'Logger handlers: {logger.handlers}')
print(f'Logger level: {logger.level}')
print(f'Root logger handlers: {logging.root.handlers}')
" 2>&1

echo ""
echo "✅ 测试完成！"

