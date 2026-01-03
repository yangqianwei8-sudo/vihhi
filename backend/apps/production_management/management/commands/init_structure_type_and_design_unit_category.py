"""
初始化结构形式和设计单位分类数据
"""
from django.core.management.base import BaseCommand
from backend.apps.production_management.models import StructureType, DesignUnitCategory


class Command(BaseCommand):
    help = '初始化结构形式和设计单位分类的基础数据'

    def handle(self, *args, **options):
        # 初始化结构形式
        structure_types = [
            {'code': 'shear_wall', 'name': '剪力墙结构', 'order': 1},
            {'code': 'frame', 'name': '框架结构', 'order': 2},
            {'code': 'steel', 'name': '钢结构', 'order': 3},
            {'code': 'brick_concrete', 'name': '砖混结构', 'order': 4},
            {'code': 'tube', 'name': '筒体结构', 'order': 5},
            {'code': 'frame_core_tube', 'name': '框架-核心筒结构', 'order': 6},
            {'code': 'tube_in_tube', 'name': '筒中筒结构', 'order': 7},
            {'code': 'slab_column_shear_wall', 'name': '板柱-剪力墙结构', 'order': 8},
            {'code': 'truss', 'name': '桁架结构', 'order': 9},
            {'code': 'arch', 'name': '拱结构', 'order': 10},
            {'code': 'space_shell', 'name': '空间薄壳结构', 'order': 11},
            {'code': 'grid', 'name': '网架结构', 'order': 12},
            {'code': 'cable_suspended', 'name': '悬索结构', 'order': 13},
            {'code': 'membrane', 'name': '膜结构', 'order': 14},
            {'code': 'other', 'name': '其他', 'order': 99},
        ]
        
        for st_data in structure_types:
            structure_type, created = StructureType.objects.get_or_create(
                code=st_data['code'],
                defaults={
                    'name': st_data['name'],
                    'order': st_data['order'],
                    'is_active': True,
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'✓ 创建结构形式: {structure_type.name}'))
            else:
                self.stdout.write(self.style.WARNING(f'- 结构形式已存在: {structure_type.name}'))
        
        # 初始化设计单位分类
        design_unit_categories = [
            {'code': 'class_1', 'name': '一类设计院', 'order': 1},
            {'code': 'class_2', 'name': '二类设计院', 'order': 2},
            {'code': 'class_3', 'name': '三类设计院', 'order': 3},
            {'code': 'class_4', 'name': '四类设计院', 'order': 4},
        ]
        
        for duc_data in design_unit_categories:
            design_unit_category, created = DesignUnitCategory.objects.get_or_create(
                code=duc_data['code'],
                defaults={
                    'name': duc_data['name'],
                    'order': duc_data['order'],
                    'is_active': True,
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'✓ 创建设计单位分类: {design_unit_category.name}'))
            else:
                self.stdout.write(self.style.WARNING(f'- 设计单位分类已存在: {design_unit_category.name}'))
        
        self.stdout.write(self.style.SUCCESS('\n初始化完成！'))

