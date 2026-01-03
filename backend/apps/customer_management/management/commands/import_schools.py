"""
导入211、985学校数据
使用方法：python manage.py import_schools
"""
from django.core.management.base import BaseCommand
from backend.apps.customer_management.models import School


class Command(BaseCommand):
    help = '导入全国211、985学校数据'

    def handle(self, *args, **options):
        # 211、985学校数据（按地区分类）
        schools_data = [
            # 北京
            {'name': '北京大学', 'region': 'beijing', 'is_211': True, 'is_985': True, 'is_double_first_class': True},
            {'name': '清华大学', 'region': 'beijing', 'is_211': True, 'is_985': True, 'is_double_first_class': True},
            {'name': '中国人民大学', 'region': 'beijing', 'is_211': True, 'is_985': True, 'is_double_first_class': True},
            {'name': '北京航空航天大学', 'region': 'beijing', 'is_211': True, 'is_985': True, 'is_double_first_class': True},
            {'name': '北京理工大学', 'region': 'beijing', 'is_211': True, 'is_985': True, 'is_double_first_class': True},
            {'name': '北京师范大学', 'region': 'beijing', 'is_211': True, 'is_985': True, 'is_double_first_class': True},
            {'name': '中国农业大学', 'region': 'beijing', 'is_211': True, 'is_985': True, 'is_double_first_class': True},
            {'name': '中央民族大学', 'region': 'beijing', 'is_211': True, 'is_985': True, 'is_double_first_class': True},
            {'name': '北京科技大学', 'region': 'beijing', 'is_211': True, 'is_985': False, 'is_double_first_class': True},
            {'name': '北京化工大学', 'region': 'beijing', 'is_211': True, 'is_985': False, 'is_double_first_class': True},
            {'name': '北京邮电大学', 'region': 'beijing', 'is_211': True, 'is_985': False, 'is_double_first_class': True},
            {'name': '北京林业大学', 'region': 'beijing', 'is_211': True, 'is_985': False, 'is_double_first_class': True},
            {'name': '北京中医药大学', 'region': 'beijing', 'is_211': True, 'is_985': False, 'is_double_first_class': True},
            {'name': '北京外国语大学', 'region': 'beijing', 'is_211': True, 'is_985': False, 'is_double_first_class': True},
            {'name': '中国传媒大学', 'region': 'beijing', 'is_211': True, 'is_985': False, 'is_double_first_class': True},
            {'name': '中央财经大学', 'region': 'beijing', 'is_211': True, 'is_985': False, 'is_double_first_class': True},
            {'name': '对外经济贸易大学', 'region': 'beijing', 'is_211': True, 'is_985': False, 'is_double_first_class': True},
            {'name': '北京体育大学', 'region': 'beijing', 'is_211': True, 'is_985': False, 'is_double_first_class': True},
            {'name': '中央音乐学院', 'region': 'beijing', 'is_211': True, 'is_985': False, 'is_double_first_class': True},
            {'name': '中国政法大学', 'region': 'beijing', 'is_211': True, 'is_985': False, 'is_double_first_class': True},
            {'name': '华北电力大学', 'region': 'beijing', 'is_211': True, 'is_985': False, 'is_double_first_class': True},
            {'name': '中国石油大学（北京）', 'region': 'beijing', 'is_211': True, 'is_985': False, 'is_double_first_class': True},
            {'name': '中国地质大学（北京）', 'region': 'beijing', 'is_211': True, 'is_985': False, 'is_double_first_class': True},
            {'name': '中国矿业大学（北京）', 'region': 'beijing', 'is_211': True, 'is_985': False, 'is_double_first_class': True},
            
            # 天津
            {'name': '南开大学', 'region': 'tianjin', 'is_211': True, 'is_985': True, 'is_double_first_class': True},
            {'name': '天津大学', 'region': 'tianjin', 'is_211': True, 'is_985': True, 'is_double_first_class': True},
            {'name': '天津医科大学', 'region': 'tianjin', 'is_211': True, 'is_985': False, 'is_double_first_class': True},
            {'name': '河北工业大学', 'region': 'tianjin', 'is_211': True, 'is_985': False, 'is_double_first_class': True},
            
            # 河北
            {'name': '华北电力大学（保定）', 'region': 'hebei', 'is_211': True, 'is_985': False, 'is_double_first_class': True},
            {'name': '河北工业大学', 'region': 'hebei', 'is_211': True, 'is_985': False, 'is_double_first_class': True},
            
            # 山西
            {'name': '太原理工大学', 'region': 'shanxi', 'is_211': True, 'is_985': False, 'is_double_first_class': True},
            
            # 内蒙古
            {'name': '内蒙古大学', 'region': 'neimenggu', 'is_211': True, 'is_985': False, 'is_double_first_class': True},
            
            # 辽宁
            {'name': '大连理工大学', 'region': 'liaoning', 'is_211': True, 'is_985': True, 'is_double_first_class': True},
            {'name': '东北大学', 'region': 'liaoning', 'is_211': True, 'is_985': True, 'is_double_first_class': True},
            {'name': '大连海事大学', 'region': 'liaoning', 'is_211': True, 'is_985': False, 'is_double_first_class': True},
            {'name': '辽宁大学', 'region': 'liaoning', 'is_211': True, 'is_985': False, 'is_double_first_class': True},
            
            # 吉林
            {'name': '吉林大学', 'region': 'jilin', 'is_211': True, 'is_985': True, 'is_double_first_class': True},
            {'name': '延边大学', 'region': 'jilin', 'is_211': True, 'is_985': False, 'is_double_first_class': True},
            {'name': '东北师范大学', 'region': 'jilin', 'is_211': True, 'is_985': False, 'is_double_first_class': True},
            
            # 黑龙江
            {'name': '哈尔滨工业大学', 'region': 'heilongjiang', 'is_211': True, 'is_985': True, 'is_double_first_class': True},
            {'name': '哈尔滨工程大学', 'region': 'heilongjiang', 'is_211': True, 'is_985': False, 'is_double_first_class': True},
            {'name': '东北农业大学', 'region': 'heilongjiang', 'is_211': True, 'is_985': False, 'is_double_first_class': True},
            {'name': '东北林业大学', 'region': 'heilongjiang', 'is_211': True, 'is_985': False, 'is_double_first_class': True},
            
            # 上海
            {'name': '复旦大学', 'region': 'shanghai', 'is_211': True, 'is_985': True, 'is_double_first_class': True},
            {'name': '上海交通大学', 'region': 'shanghai', 'is_211': True, 'is_985': True, 'is_double_first_class': True},
            {'name': '同济大学', 'region': 'shanghai', 'is_211': True, 'is_985': True, 'is_double_first_class': True},
            {'name': '华东师范大学', 'region': 'shanghai', 'is_211': True, 'is_985': True, 'is_double_first_class': True},
            {'name': '华东理工大学', 'region': 'shanghai', 'is_211': True, 'is_985': False, 'is_double_first_class': True},
            {'name': '东华大学', 'region': 'shanghai', 'is_211': True, 'is_985': False, 'is_double_first_class': True},
            {'name': '上海外国语大学', 'region': 'shanghai', 'is_211': True, 'is_985': False, 'is_double_first_class': True},
            {'name': '上海财经大学', 'region': 'shanghai', 'is_211': True, 'is_985': False, 'is_double_first_class': True},
            {'name': '上海大学', 'region': 'shanghai', 'is_211': True, 'is_985': False, 'is_double_first_class': True},
            {'name': '上海海洋大学', 'region': 'shanghai', 'is_211': True, 'is_985': False, 'is_double_first_class': True},
            {'name': '上海中医药大学', 'region': 'shanghai', 'is_211': True, 'is_985': False, 'is_double_first_class': True},
            {'name': '上海体育学院', 'region': 'shanghai', 'is_211': True, 'is_985': False, 'is_double_first_class': True},
            {'name': '上海音乐学院', 'region': 'shanghai', 'is_211': True, 'is_985': False, 'is_double_first_class': True},
            {'name': '第二军医大学', 'region': 'shanghai', 'is_211': True, 'is_985': False, 'is_double_first_class': True},
            
            # 江苏
            {'name': '南京大学', 'region': 'jiangsu', 'is_211': True, 'is_985': True, 'is_double_first_class': True},
            {'name': '东南大学', 'region': 'jiangsu', 'is_211': True, 'is_985': True, 'is_double_first_class': True},
            {'name': '苏州大学', 'region': 'jiangsu', 'is_211': True, 'is_985': False, 'is_double_first_class': True},
            {'name': '南京航空航天大学', 'region': 'jiangsu', 'is_211': True, 'is_985': False, 'is_double_first_class': True},
            {'name': '南京理工大学', 'region': 'jiangsu', 'is_211': True, 'is_985': False, 'is_double_first_class': True},
            {'name': '中国矿业大学', 'region': 'jiangsu', 'is_211': True, 'is_985': False, 'is_double_first_class': True},
            {'name': '河海大学', 'region': 'jiangsu', 'is_211': True, 'is_985': False, 'is_double_first_class': True},
            {'name': '江南大学', 'region': 'jiangsu', 'is_211': True, 'is_985': False, 'is_double_first_class': True},
            {'name': '南京农业大学', 'region': 'jiangsu', 'is_211': True, 'is_985': False, 'is_double_first_class': True},
            {'name': '中国药科大学', 'region': 'jiangsu', 'is_211': True, 'is_985': False, 'is_double_first_class': True},
            {'name': '南京师范大学', 'region': 'jiangsu', 'is_211': True, 'is_985': False, 'is_double_first_class': True},
            
            # 浙江
            {'name': '浙江大学', 'region': 'zhejiang', 'is_211': True, 'is_985': True, 'is_double_first_class': True},
            {'name': '宁波大学', 'region': 'zhejiang', 'is_211': True, 'is_985': False, 'is_double_first_class': True},
            
            # 安徽
            {'name': '中国科学技术大学', 'region': 'anhui', 'is_211': True, 'is_985': True, 'is_double_first_class': True},
            {'name': '安徽大学', 'region': 'anhui', 'is_211': True, 'is_985': False, 'is_double_first_class': True},
            {'name': '合肥工业大学', 'region': 'anhui', 'is_211': True, 'is_985': False, 'is_double_first_class': True},
            
            # 福建
            {'name': '厦门大学', 'region': 'fujian', 'is_211': True, 'is_985': True, 'is_double_first_class': True},
            {'name': '福州大学', 'region': 'fujian', 'is_211': True, 'is_985': False, 'is_double_first_class': True},
            
            # 江西
            {'name': '南昌大学', 'region': 'jiangxi', 'is_211': True, 'is_985': False, 'is_double_first_class': True},
            
            # 山东
            {'name': '山东大学', 'region': 'shandong', 'is_211': True, 'is_985': True, 'is_double_first_class': True},
            {'name': '中国海洋大学', 'region': 'shandong', 'is_211': True, 'is_985': True, 'is_double_first_class': True},
            {'name': '中国石油大学（华东）', 'region': 'shandong', 'is_211': True, 'is_985': False, 'is_double_first_class': True},
            
            # 河南
            {'name': '郑州大学', 'region': 'henan', 'is_211': True, 'is_985': False, 'is_double_first_class': True},
            
            # 湖北
            {'name': '武汉大学', 'region': 'hubei', 'is_211': True, 'is_985': True, 'is_double_first_class': True},
            {'name': '华中科技大学', 'region': 'hubei', 'is_211': True, 'is_985': True, 'is_double_first_class': True},
            {'name': '中国地质大学（武汉）', 'region': 'hubei', 'is_211': True, 'is_985': False, 'is_double_first_class': True},
            {'name': '武汉理工大学', 'region': 'hubei', 'is_211': True, 'is_985': False, 'is_double_first_class': True},
            {'name': '华中农业大学', 'region': 'hubei', 'is_211': True, 'is_985': False, 'is_double_first_class': True},
            {'name': '华中师范大学', 'region': 'hubei', 'is_211': True, 'is_985': False, 'is_double_first_class': True},
            {'name': '中南财经政法大学', 'region': 'hubei', 'is_211': True, 'is_985': False, 'is_double_first_class': True},
            
            # 湖南
            {'name': '湖南大学', 'region': 'hunan', 'is_211': True, 'is_985': True, 'is_double_first_class': True},
            {'name': '中南大学', 'region': 'hunan', 'is_211': True, 'is_985': True, 'is_double_first_class': True},
            {'name': '湖南师范大学', 'region': 'hunan', 'is_211': True, 'is_985': False, 'is_double_first_class': True},
            
            # 广东
            {'name': '中山大学', 'region': 'guangdong', 'is_211': True, 'is_985': True, 'is_double_first_class': True},
            {'name': '华南理工大学', 'region': 'guangdong', 'is_211': True, 'is_985': True, 'is_double_first_class': True},
            {'name': '暨南大学', 'region': 'guangdong', 'is_211': True, 'is_985': False, 'is_double_first_class': True},
            {'name': '华南师范大学', 'region': 'guangdong', 'is_211': True, 'is_985': False, 'is_double_first_class': True},
            
            # 广西
            {'name': '广西大学', 'region': 'guangxi', 'is_211': True, 'is_985': False, 'is_double_first_class': True},
            
            # 海南
            {'name': '海南大学', 'region': 'hainan', 'is_211': True, 'is_985': False, 'is_double_first_class': True},
            
            # 重庆
            {'name': '重庆大学', 'region': 'chongqing', 'is_211': True, 'is_985': True, 'is_double_first_class': True},
            {'name': '西南大学', 'region': 'chongqing', 'is_211': True, 'is_985': False, 'is_double_first_class': True},
            
            # 四川
            {'name': '四川大学', 'region': 'sichuan', 'is_211': True, 'is_985': True, 'is_double_first_class': True},
            {'name': '电子科技大学', 'region': 'sichuan', 'is_211': True, 'is_985': True, 'is_double_first_class': True},
            {'name': '西南交通大学', 'region': 'sichuan', 'is_211': True, 'is_985': False, 'is_double_first_class': True},
            {'name': '西南财经大学', 'region': 'sichuan', 'is_211': True, 'is_985': False, 'is_double_first_class': True},
            {'name': '四川农业大学', 'region': 'sichuan', 'is_211': True, 'is_985': False, 'is_double_first_class': True},
            
            # 贵州
            {'name': '贵州大学', 'region': 'guizhou', 'is_211': True, 'is_985': False, 'is_double_first_class': True},
            
            # 云南
            {'name': '云南大学', 'region': 'yunnan', 'is_211': True, 'is_985': False, 'is_double_first_class': True},
            
            # 西藏
            {'name': '西藏大学', 'region': 'xizang', 'is_211': True, 'is_985': False, 'is_double_first_class': True},
            
            # 陕西
            {'name': '西安交通大学', 'region': 'shaanxi', 'is_211': True, 'is_985': True, 'is_double_first_class': True},
            {'name': '西北工业大学', 'region': 'shaanxi', 'is_211': True, 'is_985': True, 'is_double_first_class': True},
            {'name': '西北农林科技大学', 'region': 'shaanxi', 'is_211': True, 'is_985': True, 'is_double_first_class': True},
            {'name': '西安电子科技大学', 'region': 'shaanxi', 'is_211': True, 'is_985': False, 'is_double_first_class': True},
            {'name': '长安大学', 'region': 'shaanxi', 'is_211': True, 'is_985': False, 'is_double_first_class': True},
            {'name': '陕西师范大学', 'region': 'shaanxi', 'is_211': True, 'is_985': False, 'is_double_first_class': True},
            {'name': '西北大学', 'region': 'shaanxi', 'is_211': True, 'is_985': False, 'is_double_first_class': True},
            
            # 甘肃
            {'name': '兰州大学', 'region': 'gansu', 'is_211': True, 'is_985': True, 'is_double_first_class': True},
            
            # 青海
            {'name': '青海大学', 'region': 'qinghai', 'is_211': True, 'is_985': False, 'is_double_first_class': True},
            
            # 宁夏
            {'name': '宁夏大学', 'region': 'ningxia', 'is_211': True, 'is_985': False, 'is_double_first_class': True},
            
            # 新疆
            {'name': '新疆大学', 'region': 'xinjiang', 'is_211': True, 'is_985': False, 'is_double_first_class': True},
            {'name': '石河子大学', 'region': 'xinjiang', 'is_211': True, 'is_985': False, 'is_double_first_class': True},
        ]
        
        created_count = 0
        updated_count = 0
        
        for school_data in schools_data:
            school, created = School.objects.update_or_create(
                name=school_data['name'],
                defaults={
                    'region': school_data['region'],
                    'is_211': school_data['is_211'],
                    'is_985': school_data['is_985'],
                    'is_double_first_class': school_data['is_double_first_class'],
                    'is_active': True,
                }
            )
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'✓ 创建: {school.name}'))
            else:
                updated_count += 1
                self.stdout.write(self.style.WARNING(f'↻ 更新: {school.name}'))
        
        self.stdout.write(self.style.SUCCESS(
            f'\n✅ 导入完成！创建 {created_count} 所，更新 {updated_count} 所，共 {len(schools_data)} 所学校'
        ))

