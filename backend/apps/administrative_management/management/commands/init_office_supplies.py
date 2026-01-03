"""
初始化常规办公用品数据
使用方法：python manage.py init_office_supplies
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import models
from backend.apps.administrative_management.models import SupplyCategory, OfficeSupply
from django.utils import timezone
from decimal import Decimal

User = get_user_model()


class Command(BaseCommand):
    help = '初始化常规办公用品数据'

    def handle(self, *args, **options):
        self.stdout.write('开始初始化常规办公用品数据...')

        # 获取或创建管理员用户（用于创建人字段）
        admin_user = User.objects.filter(is_superuser=True).first()
        if not admin_user:
            admin_user = User.objects.first()
        if not admin_user:
            self.stdout.write(
                self.style.ERROR('❌ 未找到用户，请先创建用户！')
            )
            return

        # 创建或获取分类
        categories = {}
        
        # 1. 文具用品
        categories['文具用品'], created = SupplyCategory.objects.get_or_create(
            name='文具用品',
            defaults={
                'description': '日常办公文具用品',
                'sort_order': 1,
                'is_active': True,
            }
        )
        if created:
            self.stdout.write(f'✓ 创建分类：文具用品')

        # 2. 办公设备
        categories['办公设备'], created = SupplyCategory.objects.get_or_create(
            name='办公设备',
            defaults={
                'description': '办公设备和耗材',
                'sort_order': 2,
                'is_active': True,
            }
        )
        if created:
            self.stdout.write(f'✓ 创建分类：办公设备')

        # 3. 清洁用品
        categories['清洁用品'], created = SupplyCategory.objects.get_or_create(
            name='清洁用品',
            defaults={
                'description': '办公室清洁用品',
                'sort_order': 3,
                'is_active': True,
            }
        )
        if created:
            self.stdout.write(f'✓ 创建分类：清洁用品')

        # 4. 其他用品
        categories['其他用品'], created = SupplyCategory.objects.get_or_create(
            name='其他用品',
            defaults={
                'description': '其他办公用品',
                'sort_order': 4,
                'is_active': True,
            }
        )
        if created:
            self.stdout.write(f'✓ 创建分类：其他用品')

        # 定义常规办公用品数据
        supplies_data = [
            # 文具用品
            {
                'name': '黑色签字笔',
                'supply_category': categories['文具用品'],
                'unit': '支',
                'specification': '0.5mm',
                'brand': '晨光',
                'supplier': '晨光文具',
                'purchase_price': Decimal('2.50'),
                'current_stock': 100,
                'min_stock': 20,
                'max_stock': 200,
                'storage_location': 'A区-01-01',
                'description': '日常办公用黑色签字笔',
            },
            {
                'name': '红色签字笔',
                'supply_category': categories['文具用品'],
                'unit': '支',
                'specification': '0.5mm',
                'brand': '晨光',
                'supplier': '晨光文具',
                'purchase_price': Decimal('2.50'),
                'current_stock': 50,
                'min_stock': 10,
                'max_stock': 100,
                'storage_location': 'A区-01-01',
                'description': '日常办公用红色签字笔',
            },
            {
                'name': '蓝色签字笔',
                'supply_category': categories['文具用品'],
                'unit': '支',
                'specification': '0.5mm',
                'brand': '晨光',
                'supplier': '晨光文具',
                'purchase_price': Decimal('2.50'),
                'current_stock': 50,
                'min_stock': 10,
                'max_stock': 100,
                'storage_location': 'A区-01-01',
                'description': '日常办公用蓝色签字笔',
            },
            {
                'name': 'A4复印纸',
                'supply_category': categories['文具用品'],
                'unit': '包',
                'specification': '70g/㎡ 500张/包',
                'brand': '得力',
                'supplier': '得力办公',
                'purchase_price': Decimal('25.00'),
                'current_stock': 30,
                'min_stock': 10,
                'max_stock': 50,
                'storage_location': 'A区-01-02',
                'description': 'A4规格复印纸，70g标准重量',
            },
            {
                'name': 'A4打印纸',
                'supply_category': categories['文具用品'],
                'unit': '包',
                'specification': '80g/㎡ 500张/包',
                'brand': '得力',
                'supplier': '得力办公',
                'purchase_price': Decimal('28.00'),
                'current_stock': 20,
                'min_stock': 5,
                'max_stock': 40,
                'storage_location': 'A区-01-02',
                'description': 'A4规格打印纸，80g标准重量',
            },
            {
                'name': '笔记本',
                'supply_category': categories['文具用品'],
                'unit': '本',
                'specification': 'A5 80页',
                'brand': '得力',
                'supplier': '得力办公',
                'purchase_price': Decimal('8.00'),
                'current_stock': 50,
                'min_stock': 20,
                'max_stock': 100,
                'storage_location': 'A区-01-03',
                'description': 'A5规格笔记本，80页装订',
            },
            {
                'name': '文件夹',
                'supply_category': categories['文具用品'],
                'unit': '个',
                'specification': 'A4 蓝色',
                'brand': '得力',
                'supplier': '得力办公',
                'purchase_price': Decimal('5.00'),
                'current_stock': 40,
                'min_stock': 10,
                'max_stock': 80,
                'storage_location': 'A区-01-04',
                'description': 'A4规格文件夹，蓝色',
            },
            {
                'name': '订书机',
                'supply_category': categories['文具用品'],
                'unit': '个',
                'specification': '标准型',
                'brand': '得力',
                'supplier': '得力办公',
                'purchase_price': Decimal('15.00'),
                'current_stock': 10,
                'min_stock': 3,
                'max_stock': 20,
                'storage_location': 'A区-01-05',
                'description': '标准型订书机',
            },
            {
                'name': '订书钉',
                'supply_category': categories['文具用品'],
                'unit': '盒',
                'specification': '24/6 1000枚/盒',
                'brand': '得力',
                'supplier': '得力办公',
                'purchase_price': Decimal('3.00'),
                'current_stock': 30,
                'min_stock': 10,
                'max_stock': 50,
                'storage_location': 'A区-01-05',
                'description': '标准型订书钉，24/6规格',
            },
            {
                'name': '回形针',
                'supply_category': categories['文具用品'],
                'unit': '盒',
                'specification': '100枚/盒',
                'brand': '得力',
                'supplier': '得力办公',
                'purchase_price': Decimal('2.00'),
                'current_stock': 50,
                'min_stock': 20,
                'max_stock': 100,
                'storage_location': 'A区-01-06',
                'description': '标准回形针，100枚装',
            },
            {
                'name': '长尾夹',
                'supply_category': categories['文具用品'],
                'unit': '盒',
                'specification': '19mm 12个/盒',
                'brand': '得力',
                'supplier': '得力办公',
                'purchase_price': Decimal('6.00'),
                'current_stock': 20,
                'min_stock': 5,
                'max_stock': 40,
                'storage_location': 'A区-01-06',
                'description': '19mm长尾夹，12个装',
            },
            {
                'name': '透明胶带',
                'supply_category': categories['文具用品'],
                'unit': '卷',
                'specification': '18mm×30m',
                'brand': '得力',
                'supplier': '得力办公',
                'purchase_price': Decimal('3.50'),
                'current_stock': 30,
                'min_stock': 10,
                'max_stock': 60,
                'storage_location': 'A区-01-07',
                'description': '透明胶带，18mm宽，30米长',
            },
            {
                'name': '双面胶',
                'supply_category': categories['文具用品'],
                'unit': '卷',
                'specification': '12mm×10m',
                'brand': '得力',
                'supplier': '得力办公',
                'purchase_price': Decimal('2.50'),
                'current_stock': 25,
                'min_stock': 10,
                'max_stock': 50,
                'storage_location': 'A区-01-07',
                'description': '双面胶带，12mm宽，10米长',
            },
            {
                'name': '橡皮擦',
                'supply_category': categories['文具用品'],
                'unit': '个',
                'specification': '标准型',
                'brand': '得力',
                'supplier': '得力办公',
                'purchase_price': Decimal('1.50'),
                'current_stock': 40,
                'min_stock': 10,
                'max_stock': 80,
                'storage_location': 'A区-01-08',
                'description': '标准型橡皮擦',
            },
            {
                'name': '铅笔',
                'supply_category': categories['文具用品'],
                'unit': '支',
                'specification': 'HB',
                'brand': '得力',
                'supplier': '得力办公',
                'purchase_price': Decimal('1.00'),
                'current_stock': 60,
                'min_stock': 20,
                'max_stock': 120,
                'storage_location': 'A区-01-08',
                'description': 'HB铅笔',
            },
            {
                'name': '记号笔',
                'supply_category': categories['文具用品'],
                'unit': '支',
                'specification': '粗头',
                'brand': '得力',
                'supplier': '得力办公',
                'purchase_price': Decimal('3.00'),
                'current_stock': 30,
                'min_stock': 10,
                'max_stock': 60,
                'storage_location': 'A区-01-09',
                'description': '粗头记号笔',
            },
            {
                'name': '白板笔',
                'supply_category': categories['文具用品'],
                'unit': '支',
                'specification': '黑色',
                'brand': '得力',
                'supplier': '得力办公',
                'purchase_price': Decimal('4.00'),
                'current_stock': 20,
                'min_stock': 5,
                'max_stock': 40,
                'storage_location': 'A区-01-09',
                'description': '白板用黑色记号笔',
            },
            {
                'name': '便利贴',
                'supply_category': categories['文具用品'],
                'unit': '本',
                'specification': '76mm×76mm 100张/本',
                'brand': '得力',
                'supplier': '得力办公',
                'purchase_price': Decimal('5.00'),
                'current_stock': 25,
                'min_stock': 10,
                'max_stock': 50,
                'storage_location': 'A区-01-10',
                'description': '便利贴，76mm×76mm规格',
            },
            {
                'name': '文件袋',
                'supply_category': categories['文具用品'],
                'unit': '个',
                'specification': 'A4 透明',
                'brand': '得力',
                'supplier': '得力办公',
                'purchase_price': Decimal('1.50'),
                'current_stock': 100,
                'min_stock': 30,
                'max_stock': 200,
                'storage_location': 'A区-01-11',
                'description': 'A4规格透明文件袋',
            },
            {
                'name': '档案盒',
                'supply_category': categories['文具用品'],
                'unit': '个',
                'specification': 'A4 蓝色',
                'brand': '得力',
                'supplier': '得力办公',
                'purchase_price': Decimal('8.00'),
                'current_stock': 30,
                'min_stock': 10,
                'max_stock': 60,
                'storage_location': 'A区-01-11',
                'description': 'A4规格档案盒，蓝色',
            },
            
            # 办公设备
            {
                'name': '打印机墨盒',
                'supply_category': categories['办公设备'],
                'unit': '个',
                'specification': 'HP 803 黑色',
                'brand': 'HP',
                'supplier': 'HP官方',
                'purchase_price': Decimal('120.00'),
                'current_stock': 5,
                'min_stock': 2,
                'max_stock': 10,
                'storage_location': 'B区-01-01',
                'description': 'HP 803黑色墨盒',
            },
            {
                'name': '打印机墨盒',
                'supply_category': categories['办公设备'],
                'unit': '个',
                'specification': 'HP 803 彩色',
                'brand': 'HP',
                'supplier': 'HP官方',
                'purchase_price': Decimal('150.00'),
                'current_stock': 3,
                'min_stock': 1,
                'max_stock': 6,
                'storage_location': 'B区-01-01',
                'description': 'HP 803彩色墨盒',
            },
            {
                'name': '硒鼓',
                'supply_category': categories['办公设备'],
                'unit': '个',
                'specification': 'HP 88A 黑色',
                'brand': 'HP',
                'supplier': 'HP官方',
                'purchase_price': Decimal('280.00'),
                'current_stock': 4,
                'min_stock': 2,
                'max_stock': 8,
                'storage_location': 'B区-01-02',
                'description': 'HP 88A黑色硒鼓',
            },
            {
                'name': '打印纸',
                'supply_category': categories['办公设备'],
                'unit': '包',
                'specification': 'A4 70g 500张/包',
                'brand': '得力',
                'supplier': '得力办公',
                'purchase_price': Decimal('25.00'),
                'current_stock': 50,
                'min_stock': 20,
                'max_stock': 100,
                'storage_location': 'B区-01-03',
                'description': 'A4打印纸，70g标准重量',
            },
            {
                'name': 'U盘',
                'supply_category': categories['办公设备'],
                'unit': '个',
                'specification': '32GB USB3.0',
                'brand': '金士顿',
                'supplier': '金士顿官方',
                'purchase_price': Decimal('45.00'),
                'current_stock': 15,
                'min_stock': 5,
                'max_stock': 30,
                'storage_location': 'B区-01-04',
                'description': '32GB容量USB3.0接口U盘',
            },
            {
                'name': '移动硬盘',
                'supply_category': categories['办公设备'],
                'unit': '个',
                'specification': '1TB USB3.0',
                'brand': '希捷',
                'supplier': '希捷官方',
                'purchase_price': Decimal('380.00'),
                'current_stock': 3,
                'min_stock': 1,
                'max_stock': 5,
                'storage_location': 'B区-01-05',
                'description': '1TB容量USB3.0接口移动硬盘',
            },
            
            # 清洁用品
            {
                'name': '抽纸',
                'supply_category': categories['清洁用品'],
                'unit': '包',
                'specification': '200抽/包',
                'brand': '心相印',
                'supplier': '心相印官方',
                'purchase_price': Decimal('12.00'),
                'current_stock': 40,
                'min_stock': 15,
                'max_stock': 80,
                'storage_location': 'C区-01-01',
                'description': '200抽装抽纸',
            },
            {
                'name': '卷纸',
                'supply_category': categories['清洁用品'],
                'unit': '提',
                'specification': '10卷/提',
                'brand': '心相印',
                'supplier': '心相印官方',
                'purchase_price': Decimal('25.00'),
                'current_stock': 20,
                'min_stock': 8,
                'max_stock': 40,
                'storage_location': 'C区-01-02',
                'description': '10卷装卷纸',
            },
            {
                'name': '垃圾袋',
                'supply_category': categories['清洁用品'],
                'unit': '卷',
                'specification': '45cm×50cm 100个/卷',
                'brand': '得力',
                'supplier': '得力办公',
                'purchase_price': Decimal('15.00'),
                'current_stock': 30,
                'min_stock': 10,
                'max_stock': 60,
                'storage_location': 'C区-01-03',
                'description': '45cm×50cm规格垃圾袋，100个装',
            },
            {
                'name': '洗手液',
                'supply_category': categories['清洁用品'],
                'unit': '瓶',
                'specification': '500ml',
                'brand': '蓝月亮',
                'supplier': '蓝月亮官方',
                'purchase_price': Decimal('18.00'),
                'current_stock': 15,
                'min_stock': 5,
                'max_stock': 30,
                'storage_location': 'C区-01-04',
                'description': '500ml装洗手液',
            },
            {
                'name': '消毒液',
                'supply_category': categories['清洁用品'],
                'unit': '瓶',
                'specification': '500ml',
                'brand': '84',
                'supplier': '84官方',
                'purchase_price': Decimal('8.00'),
                'current_stock': 20,
                'min_stock': 5,
                'max_stock': 40,
                'storage_location': 'C区-01-05',
                'description': '500ml装84消毒液',
            },
            {
                'name': '抹布',
                'supply_category': categories['清洁用品'],
                'unit': '条',
                'specification': '标准型',
                'brand': '得力',
                'supplier': '得力办公',
                'purchase_price': Decimal('3.00'),
                'current_stock': 30,
                'min_stock': 10,
                'max_stock': 60,
                'storage_location': 'C区-01-06',
                'description': '标准型清洁抹布',
            },
            
            # 其他用品
            {
                'name': '一次性纸杯',
                'supply_category': categories['其他用品'],
                'unit': '包',
                'specification': '200ml 50个/包',
                'brand': '得力',
                'supplier': '得力办公',
                'purchase_price': Decimal('8.00'),
                'current_stock': 25,
                'min_stock': 10,
                'max_stock': 50,
                'storage_location': 'D区-01-01',
                'description': '200ml容量一次性纸杯，50个装',
            },
            {
                'name': '茶叶',
                'supply_category': categories['其他用品'],
                'unit': '包',
                'specification': '250g',
                'brand': '立顿',
                'supplier': '立顿官方',
                'purchase_price': Decimal('25.00'),
                'current_stock': 20,
                'min_stock': 5,
                'max_stock': 40,
                'storage_location': 'D区-01-02',
                'description': '250g装茶叶',
            },
            {
                'name': '咖啡',
                'supply_category': categories['其他用品'],
                'unit': '盒',
                'specification': '100g',
                'brand': '雀巢',
                'supplier': '雀巢官方',
                'purchase_price': Decimal('35.00'),
                'current_stock': 15,
                'min_stock': 5,
                'max_stock': 30,
                'storage_location': 'D区-01-03',
                'description': '100g装咖啡',
            },
            {
                'name': '计算器',
                'supply_category': categories['其他用品'],
                'unit': '个',
                'specification': '12位',
                'brand': '得力',
                'supplier': '得力办公',
                'purchase_price': Decimal('25.00'),
                'current_stock': 10,
                'min_stock': 3,
                'max_stock': 20,
                'storage_location': 'D区-01-04',
                'description': '12位计算器',
            },
            {
                'name': '剪刀',
                'supply_category': categories['其他用品'],
                'unit': '把',
                'specification': '标准型',
                'brand': '得力',
                'supplier': '得力办公',
                'purchase_price': Decimal('8.00'),
                'current_stock': 15,
                'min_stock': 5,
                'max_stock': 30,
                'storage_location': 'D区-01-05',
                'description': '标准型剪刀',
            },
            {
                'name': '美工刀',
                'supply_category': categories['其他用品'],
                'unit': '把',
                'specification': '标准型',
                'brand': '得力',
                'supplier': '得力办公',
                'purchase_price': Decimal('5.00'),
                'current_stock': 20,
                'min_stock': 5,
                'max_stock': 40,
                'storage_location': 'D区-01-06',
                'description': '标准型美工刀',
            },
        ]

        # 创建办公用品
        created_count = 0
        updated_count = 0
        
        for supply_data in supplies_data:
            # 生成编码（如果不存在）
            current_year = timezone.now().year
            code_prefix = f'SUPPLY-{current_year}-'
            
            # 检查是否已存在同名用品
            existing_supply = OfficeSupply.objects.filter(name=supply_data['name']).first()
            
            if existing_supply:
                # 更新现有用品
                for key, value in supply_data.items():
                    setattr(existing_supply, key, value)
                existing_supply.created_by = admin_user
                existing_supply.is_active = True
                existing_supply.save()
                updated_count += 1
                self.stdout.write(f'  ✓ 更新：{supply_data["name"]}')
            else:
                # 创建新用品
                # 生成编码
                max_supply = OfficeSupply.objects.filter(
                    code__startswith=code_prefix
                ).aggregate(max_num=models.Max('code'))['max_num']
                
                if max_supply:
                    try:
                        seq = int(max_supply.split('-')[-1]) + 1
                    except (ValueError, IndexError):
                        seq = 1
                else:
                    seq = 1
                
                code = f'{code_prefix}{seq:04d}'
                
                supply = OfficeSupply.objects.create(
                    code=code,
                    created_by=admin_user,
                    **supply_data
                )
                created_count += 1
                self.stdout.write(f'  ✓ 创建：{supply_data["name"]} ({code})')

        self.stdout.write('')
        self.stdout.write(
            self.style.SUCCESS(
                f'✅ 办公用品数据初始化完成！\n'
                f'   创建：{created_count} 个\n'
                f'   更新：{updated_count} 个\n'
                f'   总计：{created_count + updated_count} 个'
            )
        )

