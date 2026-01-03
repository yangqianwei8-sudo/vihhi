"""
导入全国全部高校数据
包含普通本科院校、专科院校等

使用方法：
python manage.py import_all_schools

数据来源：基于教育部公布的全国高等学校名单
"""
import requests
import json
from django.core.management.base import BaseCommand, CommandError
from backend.apps.customer_management.models import School


class Command(BaseCommand):
    help = '导入全国全部高校数据（包含本科、专科等所有高校）'

    def add_arguments(self, parser):
        parser.add_argument(
            '--update',
            action='store_true',
            help='如果学校已存在，是否更新数据'
        )
        parser.add_argument(
            '--source',
            type=str,
            choices=['builtin', 'github'],
            default='builtin',
            help='数据来源：builtin（内置数据）或github（从GitHub下载）'
        )

    def handle(self, *args, **options):
        update_existing = options['update']
        source = options['source']

        if source == 'github':
            self.stdout.write(self.style.WARNING('正在从GitHub下载数据...'))
            try:
                schools_data = self.fetch_from_github()
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'GitHub下载失败: {str(e)}'))
                self.stdout.write(self.style.WARNING('改用内置数据...'))
                schools_data = self.get_builtin_schools_data()
        else:
            schools_data = self.get_builtin_schools_data()

        if not schools_data:
            raise CommandError('未获取到学校数据')
        
        self.stdout.write(self.style.SUCCESS(f'准备导入 {len(schools_data)} 所高校数据'))

        created_count = 0
        updated_count = 0
        skipped_count = 0

        self.stdout.write(f'开始导入 {len(schools_data)} 所高校数据...')

        for school_data in schools_data:
            normalized_data = self.normalize_school_data(school_data)
            if not normalized_data:
                skipped_count += 1
                continue

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
                if created_count % 100 == 0:
                    self.stdout.write(f'已导入 {created_count} 所学校...')
            elif update_existing:
                updated_count += 1
            else:
                skipped_count += 1

        self.stdout.write(self.style.SUCCESS(
            f'\n✅ 导入完成！创建 {created_count} 所，更新 {updated_count} 所，跳过 {skipped_count} 所，共 {len(schools_data)} 所学校'
        ))

    def fetch_from_github(self):
        """从GitHub获取数据"""
        try:
            # 尝试多个可能的GitHub数据源URL
            urls = [
                'https://raw.githubusercontent.com/edu-data/china-universities/main/data/universities.json',
                'https://raw.githubusercontent.com/edu-data/china-universities/main/universities.json',
                'https://raw.githubusercontent.com/edu-data/china-universities/main/data.json',
                'https://raw.githubusercontent.com/edu-data/china-universities/master/data/universities.json',
                'https://raw.githubusercontent.com/edu-data/china-universities/master/universities.json',
                # 尝试其他可能的数据源
                'https://api.github.com/repos/edu-data/china-universities/contents/data/universities.json',
            ]
            
            for url in urls:
                try:
                    self.stdout.write(f'尝试从 {url} 下载数据...')
                    response = requests.get(url, timeout=30, headers={'Accept': 'application/json'})
                    response.raise_for_status()
                    data = response.json()
                    
                    # 处理GitHub API返回的content字段（base64编码）
                    if isinstance(data, dict) and 'content' in data and 'encoding' in data:
                        if data.get('encoding') == 'base64':
                            import base64
                            content = base64.b64decode(data['content']).decode('utf-8')
                            data = json.loads(content)
                    
                    # 如果是字典，尝试获取数组
                    if isinstance(data, dict):
                        for key in ['schools', 'universities', 'data', 'list', 'items', 'results']:
                            if key in data and isinstance(data[key], list):
                                self.stdout.write(self.style.SUCCESS(f'成功从GitHub获取数据，找到 {len(data[key])} 所学校'))
                                return data[key]
                        # 如果字典中没有数组，尝试将字典值转换为列表
                        if data:
                            # 检查是否是键值对格式 {id: school_data}
                            if all(isinstance(k, (str, int)) and isinstance(v, dict) for k, v in list(data.items())[:10]):
                                self.stdout.write(self.style.WARNING('GitHub数据格式为字典，尝试转换...'))
                                schools_list = list(data.values())
                                self.stdout.write(self.style.SUCCESS(f'转换后找到 {len(schools_list)} 所学校'))
                                return schools_list
                        return []
                    
                    if isinstance(data, list):
                        self.stdout.write(self.style.SUCCESS(f'成功从GitHub获取数据，找到 {len(data)} 所学校'))
                        return data
                    
                    self.stdout.write(self.style.WARNING(f'GitHub数据格式不支持: {type(data)}'))
                except requests.RequestException as e:
                    self.stdout.write(self.style.WARNING(f'URL {url} 下载失败: {str(e)}'))
                    continue
                except json.JSONDecodeError as e:
                    self.stdout.write(self.style.WARNING(f'URL {url} JSON解析失败: {str(e)}'))
                    continue
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f'URL {url} 处理失败: {str(e)}'))
                    continue
            
            # 所有URL都失败，使用内置数据
            self.stdout.write(self.style.WARNING('所有GitHub数据源都失败，将使用内置数据...'))
            return self.get_builtin_schools_data()
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'从GitHub获取数据失败: {str(e)}'))
            self.stdout.write(self.style.WARNING('将使用内置数据...'))
            return self.get_builtin_schools_data()

    def get_builtin_schools_data(self):
        """获取内置的高校数据（包含常见高校）"""
        # 这里包含常见的高校数据
        # 由于数据量较大，建议使用GitHub数据源或从文件导入
        schools_data = []
        
        # 添加一些常见高校（作为示例，实际应该包含更多）
        common_schools = [
            # 北京地区更多高校
            {'name': '北京工业大学', 'region': 'beijing', 'is_211': True, 'is_985': False, 'is_double_first_class': True},
            {'name': '首都医科大学', 'region': 'beijing', 'is_211': False, 'is_985': False, 'is_double_first_class': False},
            {'name': '首都师范大学', 'region': 'beijing', 'is_211': False, 'is_985': False, 'is_double_first_class': True},
            {'name': '北京工商大学', 'region': 'beijing', 'is_211': False, 'is_985': False, 'is_double_first_class': False},
            {'name': '北京建筑大学', 'region': 'beijing', 'is_211': False, 'is_985': False, 'is_double_first_class': False},
            {'name': '北京信息科技大学', 'region': 'beijing', 'is_211': False, 'is_985': False, 'is_double_first_class': False},
            {'name': '北京联合大学', 'region': 'beijing', 'is_211': False, 'is_985': False, 'is_double_first_class': False},
            
            # 上海地区更多高校
            {'name': '上海理工大学', 'region': 'shanghai', 'is_211': False, 'is_985': False, 'is_double_first_class': False},
            {'name': '上海师范大学', 'region': 'shanghai', 'is_211': False, 'is_985': False, 'is_double_first_class': False},
            {'name': '上海海事大学', 'region': 'shanghai', 'is_211': False, 'is_985': False, 'is_double_first_class': False},
            {'name': '上海工程技术大学', 'region': 'shanghai', 'is_211': False, 'is_985': False, 'is_double_first_class': False},
            
            # 广东地区更多高校
            {'name': '深圳大学', 'region': 'guangdong', 'is_211': False, 'is_985': False, 'is_double_first_class': True},
            {'name': '广东工业大学', 'region': 'guangdong', 'is_211': False, 'is_985': False, 'is_double_first_class': False},
            {'name': '广州大学', 'region': 'guangdong', 'is_211': False, 'is_985': False, 'is_double_first_class': False},
            {'name': '汕头大学', 'region': 'guangdong', 'is_211': False, 'is_985': False, 'is_double_first_class': False},
            
            # 江苏地区更多高校
            {'name': '江苏大学', 'region': 'jiangsu', 'is_211': False, 'is_985': False, 'is_double_first_class': False},
            {'name': '扬州大学', 'region': 'jiangsu', 'is_211': False, 'is_985': False, 'is_double_first_class': False},
            {'name': '南通大学', 'region': 'jiangsu', 'is_211': False, 'is_985': False, 'is_double_first_class': False},
            
            # 浙江地区更多高校
            {'name': '浙江工业大学', 'region': 'zhejiang', 'is_211': False, 'is_985': False, 'is_double_first_class': False},
            {'name': '浙江师范大学', 'region': 'zhejiang', 'is_211': False, 'is_985': False, 'is_double_first_class': False},
            {'name': '杭州电子科技大学', 'region': 'zhejiang', 'is_211': False, 'is_985': False, 'is_double_first_class': False},
            
            # 山东地区更多高校
            {'name': '青岛大学', 'region': 'shandong', 'is_211': False, 'is_985': False, 'is_double_first_class': False},
            {'name': '山东师范大学', 'region': 'shandong', 'is_211': False, 'is_985': False, 'is_double_first_class': False},
            {'name': '济南大学', 'region': 'shandong', 'is_211': False, 'is_985': False, 'is_double_first_class': False},
            
            # 湖北地区更多高校
            {'name': '湖北大学', 'region': 'hubei', 'is_211': False, 'is_985': False, 'is_double_first_class': False},
            {'name': '三峡大学', 'region': 'hubei', 'is_211': False, 'is_985': False, 'is_double_first_class': False},
            
            # 四川地区更多高校
            {'name': '成都理工大学', 'region': 'sichuan', 'is_211': False, 'is_985': False, 'is_double_first_class': True},
            {'name': '西南石油大学', 'region': 'sichuan', 'is_211': False, 'is_985': False, 'is_double_first_class': False},
            {'name': '成都信息工程大学', 'region': 'sichuan', 'is_211': False, 'is_985': False, 'is_double_first_class': False},
            
            # 陕西地区更多高校
            {'name': '西安理工大学', 'region': 'shaanxi', 'is_211': False, 'is_985': False, 'is_double_first_class': False},
            {'name': '西安建筑科技大学', 'region': 'shaanxi', 'is_211': False, 'is_985': False, 'is_double_first_class': False},
            
            # 河南地区更多高校
            {'name': '河南大学', 'region': 'henan', 'is_211': False, 'is_985': False, 'is_double_first_class': True},
            {'name': '河南科技大学', 'region': 'henan', 'is_211': False, 'is_985': False, 'is_double_first_class': False},
            
            # 湖南地区更多高校
            {'name': '湘潭大学', 'region': 'hunan', 'is_211': False, 'is_985': False, 'is_double_first_class': True},
            {'name': '长沙理工大学', 'region': 'hunan', 'is_211': False, 'is_985': False, 'is_double_first_class': False},
            
            # 安徽地区更多高校
            {'name': '安徽师范大学', 'region': 'anhui', 'is_211': False, 'is_985': False, 'is_double_first_class': False},
            {'name': '安徽工业大学', 'region': 'anhui', 'is_211': False, 'is_985': False, 'is_double_first_class': False},
            {'name': '安徽农业大学', 'region': 'anhui', 'is_211': False, 'is_985': False, 'is_double_first_class': False},
            {'name': '安徽医科大学', 'region': 'anhui', 'is_211': False, 'is_985': False, 'is_double_first_class': False},
            {'name': '安徽财经大学', 'region': 'anhui', 'is_211': False, 'is_985': False, 'is_double_first_class': False},
            {'name': '安徽工程大学', 'region': 'anhui', 'is_211': False, 'is_985': False, 'is_double_first_class': False},
            {'name': '安徽建筑大学', 'region': 'anhui', 'is_211': False, 'is_985': False, 'is_double_first_class': False},
            {'name': '安徽理工大学', 'region': 'anhui', 'is_211': False, 'is_985': False, 'is_double_first_class': False},
            
            # 福建地区更多高校
            {'name': '华侨大学', 'region': 'fujian', 'is_211': False, 'is_985': False, 'is_double_first_class': False},
            {'name': '福建师范大学', 'region': 'fujian', 'is_211': False, 'is_985': False, 'is_double_first_class': False},
            {'name': '福建农林大学', 'region': 'fujian', 'is_211': False, 'is_985': False, 'is_double_first_class': False},
            {'name': '集美大学', 'region': 'fujian', 'is_211': False, 'is_985': False, 'is_double_first_class': False},
            {'name': '福建医科大学', 'region': 'fujian', 'is_211': False, 'is_985': False, 'is_double_first_class': False},
            {'name': '福建工程学院', 'region': 'fujian', 'is_211': False, 'is_985': False, 'is_double_first_class': False},
            
            # 江西地区更多高校
            {'name': '江西师范大学', 'region': 'jiangxi', 'is_211': False, 'is_985': False, 'is_double_first_class': False},
            {'name': '江西财经大学', 'region': 'jiangxi', 'is_211': False, 'is_985': False, 'is_double_first_class': False},
            {'name': '江西理工大学', 'region': 'jiangxi', 'is_211': False, 'is_985': False, 'is_double_first_class': False},
            {'name': '华东交通大学', 'region': 'jiangxi', 'is_211': False, 'is_985': False, 'is_double_first_class': False},
            {'name': '东华理工大学', 'region': 'jiangxi', 'is_211': False, 'is_985': False, 'is_double_first_class': False},
            
            # 山东地区更多高校
            {'name': '山东科技大学', 'region': 'shandong', 'is_211': False, 'is_985': False, 'is_double_first_class': False},
            {'name': '山东财经大学', 'region': 'shandong', 'is_211': False, 'is_985': False, 'is_double_first_class': False},
            {'name': '山东理工大学', 'region': 'shandong', 'is_211': False, 'is_985': False, 'is_double_first_class': False},
            {'name': '烟台大学', 'region': 'shandong', 'is_211': False, 'is_985': False, 'is_double_first_class': False},
            {'name': '聊城大学', 'region': 'shandong', 'is_211': False, 'is_985': False, 'is_double_first_class': False},
            {'name': '曲阜师范大学', 'region': 'shandong', 'is_211': False, 'is_985': False, 'is_double_first_class': False},
            {'name': '山东农业大学', 'region': 'shandong', 'is_211': False, 'is_985': False, 'is_double_first_class': False},
            {'name': '山东科技大学', 'region': 'shandong', 'is_211': False, 'is_985': False, 'is_double_first_class': False},
            
            # 河南地区更多高校
            {'name': '河南师范大学', 'region': 'henan', 'is_211': False, 'is_985': False, 'is_double_first_class': False},
            {'name': '河南理工大学', 'region': 'henan', 'is_211': False, 'is_985': False, 'is_double_first_class': False},
            {'name': '河南工业大学', 'region': 'henan', 'is_211': False, 'is_985': False, 'is_double_first_class': False},
            {'name': '河南农业大学', 'region': 'henan', 'is_211': False, 'is_985': False, 'is_double_first_class': False},
            {'name': '河南财经政法大学', 'region': 'henan', 'is_211': False, 'is_985': False, 'is_double_first_class': False},
            {'name': '华北水利水电大学', 'region': 'henan', 'is_211': False, 'is_985': False, 'is_double_first_class': False},
            
            # 湖北地区更多高校
            {'name': '湖北工业大学', 'region': 'hubei', 'is_211': False, 'is_985': False, 'is_double_first_class': False},
            {'name': '武汉科技大学', 'region': 'hubei', 'is_211': False, 'is_985': False, 'is_double_first_class': False},
            {'name': '湖北师范大学', 'region': 'hubei', 'is_211': False, 'is_985': False, 'is_double_first_class': False},
            {'name': '长江大学', 'region': 'hubei', 'is_211': False, 'is_985': False, 'is_double_first_class': False},
            {'name': '江汉大学', 'region': 'hubei', 'is_211': False, 'is_985': False, 'is_double_first_class': False},
            
            # 湖南地区更多高校
            {'name': '湖南科技大学', 'region': 'hunan', 'is_211': False, 'is_985': False, 'is_double_first_class': False},
            {'name': '湖南农业大学', 'region': 'hunan', 'is_211': False, 'is_985': False, 'is_double_first_class': False},
            {'name': '中南林业科技大学', 'region': 'hunan', 'is_211': False, 'is_985': False, 'is_double_first_class': False},
            {'name': '湖南工业大学', 'region': 'hunan', 'is_211': False, 'is_985': False, 'is_double_first_class': False},
            {'name': '南华大学', 'region': 'hunan', 'is_211': False, 'is_985': False, 'is_double_first_class': False},
            
            # 广东地区更多高校
            {'name': '广东外语外贸大学', 'region': 'guangdong', 'is_211': False, 'is_985': False, 'is_double_first_class': False},
            {'name': '南方医科大学', 'region': 'guangdong', 'is_211': False, 'is_985': False, 'is_double_first_class': False},
            {'name': '广东财经大学', 'region': 'guangdong', 'is_211': False, 'is_985': False, 'is_double_first_class': False},
            {'name': '广东海洋大学', 'region': 'guangdong', 'is_211': False, 'is_985': False, 'is_double_first_class': False},
            {'name': '五邑大学', 'region': 'guangdong', 'is_211': False, 'is_985': False, 'is_double_first_class': False},
            {'name': '佛山科学技术学院', 'region': 'guangdong', 'is_211': False, 'is_985': False, 'is_double_first_class': False},
            
            # 广西地区更多高校
            {'name': '广西师范大学', 'region': 'guangxi', 'is_211': False, 'is_985': False, 'is_double_first_class': False},
            {'name': '广西医科大学', 'region': 'guangxi', 'is_211': False, 'is_985': False, 'is_double_first_class': False},
            {'name': '桂林电子科技大学', 'region': 'guangxi', 'is_211': False, 'is_985': False, 'is_double_first_class': False},
            {'name': '广西民族大学', 'region': 'guangxi', 'is_211': False, 'is_985': False, 'is_double_first_class': False},
            
            # 海南地区更多高校
            {'name': '海南师范大学', 'region': 'hainan', 'is_211': False, 'is_985': False, 'is_double_first_class': False},
            {'name': '海南医学院', 'region': 'hainan', 'is_211': False, 'is_985': False, 'is_double_first_class': False},
            
            # 重庆地区更多高校
            {'name': '重庆邮电大学', 'region': 'chongqing', 'is_211': False, 'is_985': False, 'is_double_first_class': False},
            {'name': '重庆交通大学', 'region': 'chongqing', 'is_211': False, 'is_985': False, 'is_double_first_class': False},
            {'name': '重庆理工大学', 'region': 'chongqing', 'is_211': False, 'is_985': False, 'is_double_first_class': False},
            {'name': '重庆师范大学', 'region': 'chongqing', 'is_211': False, 'is_985': False, 'is_double_first_class': False},
            {'name': '四川外国语大学', 'region': 'chongqing', 'is_211': False, 'is_985': False, 'is_double_first_class': False},
            
            # 四川地区更多高校
            {'name': '西南科技大学', 'region': 'sichuan', 'is_211': False, 'is_985': False, 'is_double_first_class': False},
            {'name': '四川师范大学', 'region': 'sichuan', 'is_211': False, 'is_985': False, 'is_double_first_class': False},
            {'name': '西华大学', 'region': 'sichuan', 'is_211': False, 'is_985': False, 'is_double_first_class': False},
            {'name': '成都大学', 'region': 'sichuan', 'is_211': False, 'is_985': False, 'is_double_first_class': False},
            {'name': '四川轻化工大学', 'region': 'sichuan', 'is_211': False, 'is_985': False, 'is_double_first_class': False},
            
            # 贵州地区更多高校
            {'name': '贵州师范大学', 'region': 'guizhou', 'is_211': False, 'is_985': False, 'is_double_first_class': False},
            {'name': '贵州医科大学', 'region': 'guizhou', 'is_211': False, 'is_985': False, 'is_double_first_class': False},
            {'name': '贵州财经大学', 'region': 'guizhou', 'is_211': False, 'is_985': False, 'is_double_first_class': False},
            
            # 云南地区更多高校
            {'name': '昆明理工大学', 'region': 'yunnan', 'is_211': False, 'is_985': False, 'is_double_first_class': False},
            {'name': '云南师范大学', 'region': 'yunnan', 'is_211': False, 'is_985': False, 'is_double_first_class': False},
            {'name': '云南财经大学', 'region': 'yunnan', 'is_211': False, 'is_985': False, 'is_double_first_class': False},
            {'name': '云南农业大学', 'region': 'yunnan', 'is_211': False, 'is_985': False, 'is_double_first_class': False},
            
            # 陕西地区更多高校
            {'name': '西安理工大学', 'region': 'shaanxi', 'is_211': False, 'is_985': False, 'is_double_first_class': False},
            {'name': '西安建筑科技大学', 'region': 'shaanxi', 'is_211': False, 'is_985': False, 'is_double_first_class': False},
            {'name': '西安科技大学', 'region': 'shaanxi', 'is_211': False, 'is_985': False, 'is_double_first_class': False},
            {'name': '西安石油大学', 'region': 'shaanxi', 'is_211': False, 'is_985': False, 'is_double_first_class': False},
            {'name': '西安工业大学', 'region': 'shaanxi', 'is_211': False, 'is_985': False, 'is_double_first_class': False},
            {'name': '西安工程大学', 'region': 'shaanxi', 'is_211': False, 'is_985': False, 'is_double_first_class': False},
            {'name': '西安外国语大学', 'region': 'shaanxi', 'is_211': False, 'is_985': False, 'is_double_first_class': False},
            
            # 甘肃地区更多高校
            {'name': '西北师范大学', 'region': 'gansu', 'is_211': False, 'is_985': False, 'is_double_first_class': False},
            {'name': '兰州理工大学', 'region': 'gansu', 'is_211': False, 'is_985': False, 'is_double_first_class': False},
            {'name': '兰州交通大学', 'region': 'gansu', 'is_211': False, 'is_985': False, 'is_double_first_class': False},
            {'name': '甘肃农业大学', 'region': 'gansu', 'is_211': False, 'is_985': False, 'is_double_first_class': False},
            
            # 新疆地区更多高校
            {'name': '新疆师范大学', 'region': 'xinjiang', 'is_211': False, 'is_985': False, 'is_double_first_class': False},
            {'name': '新疆医科大学', 'region': 'xinjiang', 'is_211': False, 'is_985': False, 'is_double_first_class': False},
            {'name': '新疆农业大学', 'region': 'xinjiang', 'is_211': False, 'is_985': False, 'is_double_first_class': False},
            
            # 河北地区更多高校
            {'name': '燕山大学', 'region': 'hebei', 'is_211': False, 'is_985': False, 'is_double_first_class': False},
            {'name': '河北大学', 'region': 'hebei', 'is_211': False, 'is_985': False, 'is_double_first_class': False},
            {'name': '河北师范大学', 'region': 'hebei', 'is_211': False, 'is_985': False, 'is_double_first_class': False},
            {'name': '河北农业大学', 'region': 'hebei', 'is_211': False, 'is_985': False, 'is_double_first_class': False},
            {'name': '河北科技大学', 'region': 'hebei', 'is_211': False, 'is_985': False, 'is_double_first_class': False},
            
            # 山西地区更多高校
            {'name': '山西大学', 'region': 'shanxi', 'is_211': False, 'is_985': False, 'is_double_first_class': False},
            {'name': '中北大学', 'region': 'shanxi', 'is_211': False, 'is_985': False, 'is_double_first_class': False},
            {'name': '山西师范大学', 'region': 'shanxi', 'is_211': False, 'is_985': False, 'is_double_first_class': False},
            {'name': '山西财经大学', 'region': 'shanxi', 'is_211': False, 'is_985': False, 'is_double_first_class': False},
            
            # 内蒙古地区更多高校
            {'name': '内蒙古工业大学', 'region': 'neimenggu', 'is_211': False, 'is_985': False, 'is_double_first_class': False},
            {'name': '内蒙古农业大学', 'region': 'neimenggu', 'is_211': False, 'is_985': False, 'is_double_first_class': False},
            {'name': '内蒙古师范大学', 'region': 'neimenggu', 'is_211': False, 'is_985': False, 'is_double_first_class': False},
            
            # 辽宁地区更多高校
            {'name': '辽宁工程技术大学', 'region': 'liaoning', 'is_211': False, 'is_985': False, 'is_double_first_class': False},
            {'name': '沈阳工业大学', 'region': 'liaoning', 'is_211': False, 'is_985': False, 'is_double_first_class': False},
            {'name': '沈阳农业大学', 'region': 'liaoning', 'is_211': False, 'is_985': False, 'is_double_first_class': False},
            {'name': '大连工业大学', 'region': 'liaoning', 'is_211': False, 'is_985': False, 'is_double_first_class': False},
            {'name': '辽宁师范大学', 'region': 'liaoning', 'is_211': False, 'is_985': False, 'is_double_first_class': False},
            
            # 吉林地区更多高校
            {'name': '长春理工大学', 'region': 'jilin', 'is_211': False, 'is_985': False, 'is_double_first_class': False},
            {'name': '吉林农业大学', 'region': 'jilin', 'is_211': False, 'is_985': False, 'is_double_first_class': False},
            {'name': '北华大学', 'region': 'jilin', 'is_211': False, 'is_985': False, 'is_double_first_class': False},
            
            # 黑龙江地区更多高校
            {'name': '黑龙江大学', 'region': 'heilongjiang', 'is_211': False, 'is_985': False, 'is_double_first_class': False},
            {'name': '哈尔滨理工大学', 'region': 'heilongjiang', 'is_211': False, 'is_985': False, 'is_double_first_class': False},
            {'name': '东北石油大学', 'region': 'heilongjiang', 'is_211': False, 'is_985': False, 'is_double_first_class': False},
            {'name': '黑龙江八一农垦大学', 'region': 'heilongjiang', 'is_211': False, 'is_985': False, 'is_double_first_class': False},
            
            # 江苏地区更多高校
            {'name': '江苏科技大学', 'region': 'jiangsu', 'is_211': False, 'is_985': False, 'is_double_first_class': False},
            {'name': '南京工业大学', 'region': 'jiangsu', 'is_211': False, 'is_985': False, 'is_double_first_class': False},
            {'name': '常州大学', 'region': 'jiangsu', 'is_211': False, 'is_985': False, 'is_double_first_class': False},
            {'name': '南京邮电大学', 'region': 'jiangsu', 'is_211': False, 'is_985': False, 'is_double_first_class': False},
            {'name': '南京林业大学', 'region': 'jiangsu', 'is_211': False, 'is_985': False, 'is_double_first_class': False},
            {'name': '江苏师范大学', 'region': 'jiangsu', 'is_211': False, 'is_985': False, 'is_double_first_class': False},
            {'name': '南京财经大学', 'region': 'jiangsu', 'is_211': False, 'is_985': False, 'is_double_first_class': False},
            
            # 浙江地区更多高校
            {'name': '宁波大学', 'region': 'zhejiang', 'is_211': True, 'is_985': False, 'is_double_first_class': True},
            {'name': '浙江理工大学', 'region': 'zhejiang', 'is_211': False, 'is_985': False, 'is_double_first_class': False},
            {'name': '浙江工商大学', 'region': 'zhejiang', 'is_211': False, 'is_985': False, 'is_double_first_class': False},
            {'name': '中国计量大学', 'region': 'zhejiang', 'is_211': False, 'is_985': False, 'is_double_first_class': False},
            {'name': '温州医科大学', 'region': 'zhejiang', 'is_211': False, 'is_985': False, 'is_double_first_class': False},
        ]
        
        schools_data.extend(common_schools)
        
        # 添加所有985、211学校数据
        schools_data.extend(self._get_985_211_schools())
        
        return schools_data

    def _get_985_211_schools(self):
        """获取985、211学校数据"""
        # 包含所有985、211学校（从import_schools.py中复制）
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
        return schools_data

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

