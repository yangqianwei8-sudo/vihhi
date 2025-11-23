"""
生产启动相关服务函数
"""
from django.db import transaction
from django.utils import timezone
from backend.apps.production_quality.models_startup import ProjectDrawingDirectory


def create_default_drawing_directories(project, created_by=None):
    """
    为项目创建默认的图纸目录结构
    
    标准目录结构：
    项目图纸库/
    ├── 01-建筑专业/
    │   ├── 平面图/
    │   ├── 立面图/
    │   ├── 剖面图/
    │   └── 详图/
    ├── 02-结构专业/
    │   ├── 基础图/
    │   ├── 梁板柱配筋图/
    │   └── 节点详图/
    ├── 03-机电专业/
    │   ├── 给排水/
    │   ├── 电气/
    │   └── 暖通/
    └── 04-其他图纸/
        ├── 总图/
        └── 专项图纸/
    """
    default_structure = [
        {
            'name': '01-建筑专业',
            'path': '01-建筑专业',
            'order': 1,
            'children': [
                {'name': '平面图', 'path': '01-建筑专业/平面图', 'order': 1},
                {'name': '立面图', 'path': '01-建筑专业/立面图', 'order': 2},
                {'name': '剖面图', 'path': '01-建筑专业/剖面图', 'order': 3},
                {'name': '详图', 'path': '01-建筑专业/详图', 'order': 4},
            ]
        },
        {
            'name': '02-结构专业',
            'path': '02-结构专业',
            'order': 2,
            'children': [
                {'name': '基础图', 'path': '02-结构专业/基础图', 'order': 1},
                {'name': '梁板柱配筋图', 'path': '02-结构专业/梁板柱配筋图', 'order': 2},
                {'name': '节点详图', 'path': '02-结构专业/节点详图', 'order': 3},
            ]
        },
        {
            'name': '03-机电专业',
            'path': '03-机电专业',
            'order': 3,
            'children': [
                {'name': '给排水', 'path': '03-机电专业/给排水', 'order': 1},
                {'name': '电气', 'path': '03-机电专业/电气', 'order': 2},
                {'name': '暖通', 'path': '03-机电专业/暖通', 'order': 3},
            ]
        },
        {
            'name': '04-其他图纸',
            'path': '04-其他图纸',
            'order': 4,
            'children': [
                {'name': '总图', 'path': '04-其他图纸/总图', 'order': 1},
                {'name': '专项图纸', 'path': '04-其他图纸/专项图纸', 'order': 2},
            ]
        },
    ]
    
    with transaction.atomic():
        for parent_data in default_structure:
            parent, _ = ProjectDrawingDirectory.objects.get_or_create(
                project=project,
                path=parent_data['path'],
                defaults={
                    'name': parent_data['name'],
                    'order': parent_data['order'],
                    'created_by': created_by,
                }
            )
            
            for child_data in parent_data.get('children', []):
                ProjectDrawingDirectory.objects.get_or_create(
                    project=project,
                    path=child_data['path'],
                    defaults={
                        'name': child_data['name'],
                        'parent': parent,
                        'order': child_data['order'],
                        'created_by': created_by,
                    }
                )
    
    return ProjectDrawingDirectory.objects.filter(project=project).count()


def calculate_task_saving_target(building_area, saving_per_sqm):
    """
    计算任务节省目标
    
    Args:
        building_area: 建筑面积（平方米）
        saving_per_sqm: 每平方米节省金额（元/平方米）
    
    Returns:
        节省目标金额（元）
    """
    from decimal import Decimal
    if building_area and saving_per_sqm:
        return Decimal(str(building_area)) * Decimal(str(saving_per_sqm))
    return None


def validate_startup_submission(startup):
    """
    验证生产启动提交是否满足条件
    
    Returns:
        (is_valid, error_messages)
    """
    errors = []
    
    # 检查图纸是否已上传
    if not startup.drawings_uploaded:
        errors.append('请先上传图纸')
    
    # 检查团队是否已配置
    if not startup.team_configured:
        errors.append('请先配置团队')
    
    # 检查任务是否已创建
    if not startup.tasks_created:
        errors.append('请先创建任务清单')
    
    # 检查节省目标
    if startup.tasks_created and startup.project.estimated_savings:
        contract_target = startup.project.estimated_savings
        required_target = contract_target * 1.5
        
        if not startup.total_saving_target or startup.total_saving_target < required_target:
            errors.append(
                f'任务节省目标总额（{startup.total_saving_target or 0:.2f}元）'
                f'低于合同目标的1.5倍（{required_target:.2f}元），请重新分解任务'
            )
    
    return len(errors) == 0, errors

