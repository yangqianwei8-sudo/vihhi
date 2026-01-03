#!/bin/bash
# 测试进度显示功能

echo "🔍 测试进度显示功能..."
echo ""

# 1. 检查所有 material 记录
echo "1. 检查所有优化前资料记录："
python3 /app/manage.py shell -c "
from backend.apps.production_management.models import PreOptimizationMaterial
materials = PreOptimizationMaterial.objects.all().order_by('-id')[:10]
if materials:
    print('  最近10条记录：')
    for m in materials:
        print(f'    ID: {m.id}, 文件名: {m.file_name[:30]}, 状态: {m.parse_status}, 进度: {m.parse_progress}%, 消息: {m.parse_progress_message[:30] if m.parse_progress_message else \"无\"}')
else:
    print('  没有找到任何记录')
" 2>/dev/null || echo "  无法检查（可能需要设置 DATABASE_URL）"

echo ""
echo "2. 检查是否有 pending 或 processing 状态的记录："
python3 /app/manage.py shell -c "
from backend.apps.production_management.models import PreOptimizationMaterial
materials = PreOptimizationMaterial.objects.filter(parse_status__in=['pending', 'processing']).order_by('-id')
if materials:
    print(f'  找到 {materials.count()} 条记录：')
    for m in materials:
        print(f'    ID: {m.id}, 状态: {m.parse_status}, 进度: {m.parse_progress}%, 消息: {m.parse_progress_message[:30] if m.parse_progress_message else \"无\"}')
else:
    print('  没有找到 pending 或 processing 状态的记录')
" 2>/dev/null || echo "  无法检查（可能需要设置 DATABASE_URL）"

echo ""
echo "3. 测试 API 端点（如果有记录）："
python3 /app/manage.py shell -c "
from backend.apps.production_management.models import PreOptimizationMaterial
from backend.apps.production_management.views_pages import pre_optimization_materials_progress
from django.test import RequestFactory
from django.contrib.auth import get_user_model

# 获取任意一个 material（优先选择 processing 或 pending）
material = PreOptimizationMaterial.objects.filter(parse_status__in=['processing', 'pending']).first()
if not material:
    material = PreOptimizationMaterial.objects.first()

if material:
    print(f'  测试 Material ID: {material.id}')
    print(f'  文件名: {material.file_name}')
    print(f'  当前状态: {material.parse_status}')
    print(f'  当前进度: {material.parse_progress}%')
    print(f'  当前消息: {material.parse_progress_message or \"无\"}')
    print('')
    
    # 创建测试请求
    factory = RequestFactory()
    request = factory.get(f'/production/pre-optimization-materials/{material.id}/progress/')
    User = get_user_model()
    admin_user = User.objects.filter(is_superuser=True).first() or User.objects.first()
    if admin_user:
        request.user = admin_user
        
        # 调用视图
        try:
            response = pre_optimization_materials_progress(request, material.id)
            print(f'  API 响应状态码: {response.status_code}')
            print(f'  API 响应内容: {response.content.decode()}')
        except Exception as e:
            print(f'  API 调用失败: {e}')
    else:
        print('  无法找到用户进行测试')
else:
    print('  没有找到任何 material 记录')
    print('  请先上传一个 CAD 文件进行测试')
" 2>/dev/null || echo "  无法测试（可能需要设置 DATABASE_URL）"

echo ""
echo "4. 检查解析任务是否在运行："
ps aux | grep -i "python.*manage.py\|gunicorn\|cad\|parse" | grep -v grep || echo "  没有找到相关进程"

echo ""
echo "✅ 测试完成！"
echo ""
echo "💡 下一步操作："
echo "   1. 如果没有记录，请上传一个新的 CAD 文件"
echo "   2. 如果有记录但状态不是 processing，可以尝试重新解析"
echo "   3. 在浏览器中打开详情页面，查看进度显示"
echo "   4. 打开浏览器开发者工具（F12），检查："
echo "      - Console 标签：是否有 JavaScript 错误"
echo "      - Network 标签：/progress/ 请求是否成功"
echo "      - 检查 /progress/ 请求的响应内容"

