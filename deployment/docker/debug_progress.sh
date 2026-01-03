#!/bin/bash
# 调试进度显示问题

echo "🔍 调试进度显示问题..."
echo ""

# 1. 检查是否有正在解析的任务
echo "1. 检查正在解析的任务："
python3 /app/manage.py shell -c "
from backend.apps.production_management.models import PreOptimizationMaterial
materials = PreOptimizationMaterial.objects.filter(parse_status__in=['processing', 'pending']).order_by('-id')[:5]
if materials:
    for m in materials:
        print(f'  ID: {m.id}, 状态: {m.parse_status}, 进度: {m.parse_progress}%, 消息: {m.parse_progress_message}')
else:
    print('  没有正在解析的任务')
" 2>/dev/null || echo "  无法检查（可能需要设置 DATABASE_URL）"

echo ""
echo "2. 测试 API 端点（需要替换 <material_id>）："
echo "   curl -H 'Cookie: sessionid=...' http://localhost:8000/production/pre-optimization-materials/<material_id>/progress/"

echo ""
echo "3. 检查浏览器控制台："
echo "   - 打开浏览器开发者工具（F12）"
echo "   - 查看 Console 标签，检查是否有 JavaScript 错误"
echo "   - 查看 Network 标签，检查 /progress/ 请求是否成功"
echo "   - 检查 /progress/ 请求的响应内容"

echo ""
echo "4. 检查容器日志："
echo "   - 查看是否有 [CAD解析任务] 相关的日志"
echo "   - 查看是否有进度更新的日志"

echo ""
echo "5. 手动测试 API（在容器中执行）："
echo "   python3 /app/manage.py shell -c \"
from backend.apps.production_management.models import PreOptimizationMaterial
from backend.apps.production_management.views_pages import pre_optimization_materials_progress
from django.test import RequestFactory
from django.contrib.auth import get_user_model

# 获取一个测试 material
material = PreOptimizationMaterial.objects.filter(parse_status__in=['processing', 'pending']).first()
if material:
    print(f'测试 Material ID: {material.id}')
    print(f'当前状态: {material.parse_status}')
    print(f'当前进度: {material.parse_progress}%')
    print(f'当前消息: {material.parse_progress_message}')
    
    # 创建测试请求
    factory = RequestFactory()
    request = factory.get(f'/production/pre-optimization-materials/{material.id}/progress/')
    User = get_user_model()
    request.user = User.objects.first()  # 使用第一个用户
    
    # 调用视图
    response = pre_optimization_materials_progress(request, material.id)
    print(f'API 响应: {response.content.decode()}')
else:
    print('没有找到测试 material')
\""

echo ""
echo "✅ 调试信息收集完成！"

