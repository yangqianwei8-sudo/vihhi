"""
从文件导入高校数据
支持从GitHub项目 edu-data/china-universities 导入数据

使用方法：
1. 从GitHub下载数据文件（JSON或CSV格式）
   https://github.com/edu-data/china-universities

2. 导入JSON格式：
   python manage.py import_schools_from_file --file path/to/schools.json --format json

3. 导入CSV格式：
   python manage.py import_schools_from_file --file path/to/schools.csv --format csv

数据文件格式要求：
- JSON格式：数组，每个元素包含 name, province/city/region 等字段
- CSV格式：包含 name, province/city/region 等列
"""
import json
import csv
import os
from django.core.management.base import BaseCommand, CommandError
from backend.apps.customer_management.models import School


class Command(BaseCommand):
    help = '从文件导入高校数据（支持JSON和CSV格式）'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            required=True,
            help='数据文件路径'
        )
        parser.add_argument(
            '--format',
            type=str,
            choices=['json', 'csv'],
            default='json',
            help='文件格式（json或csv）'
        )
        parser.add_argument(
            '--update',
            action='store_true',
            help='如果学校已存在，是否更新数据'
        )

    def handle(self, *args, **options):
        file_path = options['file']
        file_format = options['format']
        update_existing = options['update']

        if not os.path.exists(file_path):
            raise CommandError(f'文件不存在: {file_path}')

        try:
            if file_format == 'json':
                schools_data = self.load_json(file_path)
            else:
                schools_data = self.load_csv(file_path)

            created_count = 0
            updated_count = 0
            skipped_count = 0

            for school_data in schools_data:
                # 标准化数据
                normalized_data = self.normalize_school_data(school_data)
                if not normalized_data:
                    skipped_count += 1
                    continue

                # 导入或更新
                school, created = School.objects.update_or_create(
                    name=normalized_data['name'],
                    defaults={
                        'region': normalized_data['region'],
                        'is_211': normalized_data.get('is_211', False),
                        'is_985': normalized_data.get('is_985', False),
                        'is_double_first_class': normalized_data.get('is_double_first_class', False),
                        'is_active': True,
                        'display_order': normalized_data.get('display_order', 0),
                    }
                )

                if created:
                    created_count += 1
                    self.stdout.write(self.style.SUCCESS(f'✓ 创建: {school.name}'))
                elif update_existing:
                    updated_count += 1
                    self.stdout.write(self.style.WARNING(f'↻ 更新: {school.name}'))
                else:
                    skipped_count += 1

            self.stdout.write(self.style.SUCCESS(
                f'\n✅ 导入完成！创建 {created_count} 所，更新 {updated_count} 所，跳过 {skipped_count} 所'
            ))

        except Exception as e:
            raise CommandError(f'导入失败: {str(e)}')

    def load_json(self, file_path):
        """加载JSON文件"""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 如果是字典，尝试获取数组
        if isinstance(data, dict):
            # 尝试常见的键名
            for key in ['schools', 'universities', 'data', 'list']:
                if key in data and isinstance(data[key], list):
                    return data[key]
            # 如果没有找到，返回空列表
            return []
        
        return data if isinstance(data, list) else []

    def load_csv(self, file_path):
        """加载CSV文件"""
        schools = []
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                schools.append(row)
        return schools

    def normalize_school_data(self, data):
        """标准化学校数据"""
        # 获取学校名称
        name = data.get('name') or data.get('school_name') or data.get('university_name') or data.get('学校名称')
        if not name or not name.strip():
            return None

        name = name.strip()

        # 获取地区
        region = self.get_region_from_data(data)
        if not region:
            # 如果无法确定地区，尝试从学校名称推断
            region = self.infer_region_from_name(name)
        
        if not region:
            # 默认使用北京
            region = 'beijing'

        # 获取标签信息
        is_211 = self.get_bool_value(data, 'is_211', '211', 'is211')
        is_985 = self.get_bool_value(data, 'is_985', '985', 'is985')
        is_double_first_class = self.get_bool_value(
            data, 'is_double_first_class', 'double_first_class', 
            '双一流', 'is_double_first'
        )

        return {
            'name': name,
            'region': region,
            'is_211': is_211,
            'is_985': is_985,
            'is_double_first_class': is_double_first_class,
            'display_order': int(data.get('display_order', data.get('order', 0)) or 0),
        }

    def get_region_from_data(self, data):
        """从数据中提取地区代码"""
        # 尝试多种可能的字段名
        region_fields = [
            'region', 'province', 'city', 'province_code', 'region_code',
            '省份', '地区', '省市', '所在地区'
        ]
        
        for field in region_fields:
            value = data.get(field)
            if value:
                # 如果是地区代码，直接返回
                if value in dict(School.REGION_CHOICES):
                    return value
                # 如果是地区名称，转换为代码
                region_code = self.region_name_to_code(value)
                if region_code:
                    return region_code
        
        return None

    def region_name_to_code(self, name):
        """将地区名称转换为代码"""
        name = name.strip()
        region_map = {
            '北京': 'beijing', '天津': 'tianjin', '河北': 'hebei', '山西': 'shanxi',
            '内蒙古': 'neimenggu', '辽宁': 'liaoning', '吉林': 'jilin', '黑龙江': 'heilongjiang',
            '上海': 'shanghai', '江苏': 'jiangsu', '浙江': 'zhejiang', '安徽': 'anhui',
            '福建': 'fujian', '江西': 'jiangxi', '山东': 'shandong', '河南': 'henan',
            '湖北': 'hubei', '湖南': 'hunan', '广东': 'guangdong', '广西': 'guangxi',
            '海南': 'hainan', '重庆': 'chongqing', '四川': 'sichuan', '贵州': 'guizhou',
            '云南': 'yunnan', '西藏': 'xizang', '陕西': 'shaanxi', '甘肃': 'gansu',
            '青海': 'qinghai', '宁夏': 'ningxia', '新疆': 'xinjiang',
            '香港': 'hongkong', '澳门': 'macau', '台湾': 'taiwan',
        }
        return region_map.get(name)

    def infer_region_from_name(self, name):
        """从学校名称推断地区"""
        # 常见地区关键词
        region_keywords = {
            '北京': 'beijing', '天津': 'tianjin', '河北': 'hebei', '山西': 'shanxi',
            '内蒙古': 'neimenggu', '辽宁': 'liaoning', '吉林': 'jilin', '黑龙江': 'heilongjiang',
            '上海': 'shanghai', '江苏': 'jiangsu', '浙江': 'zhejiang', '安徽': 'anhui',
            '福建': 'fujian', '江西': 'jiangxi', '山东': 'shandong', '河南': 'henan',
            '湖北': 'hubei', '湖南': 'hunan', '广东': 'guangdong', '广西': 'guangxi',
            '海南': 'hainan', '重庆': 'chongqing', '四川': 'sichuan', '贵州': 'guizhou',
            '云南': 'yunnan', '西藏': 'xizang', '陕西': 'shaanxi', '甘肃': 'gansu',
            '青海': 'qinghai', '宁夏': 'ningxia', '新疆': 'xinjiang',
            '香港': 'hongkong', '澳门': 'macau', '台湾': 'taiwan',
        }
        
        for keyword, code in region_keywords.items():
            if keyword in name:
                return code
        
        return None

    def get_bool_value(self, data, *keys):
        """从数据中获取布尔值"""
        for key in keys:
            value = data.get(key)
            if value is not None:
                if isinstance(value, bool):
                    return value
                if isinstance(value, str):
                    value_lower = value.lower().strip()
                    if value_lower in ('true', '1', 'yes', '是', '有'):
                        return True
                    if value_lower in ('false', '0', 'no', '否', '无'):
                        return False
                if isinstance(value, (int, float)):
                    return bool(value)
        return False

