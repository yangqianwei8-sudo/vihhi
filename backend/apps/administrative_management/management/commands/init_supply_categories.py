"""
初始化办公用品分类体系
按功能用途分类，包含7个大类和多个子类
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from backend.apps.administrative_management.models import SupplyCategory


class Command(BaseCommand):
    help = '初始化办公用品分类体系（按功能用途分类）'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='清除现有分类后重新创建',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        clear_existing = options.get('clear', False)
        
        if clear_existing:
            self.stdout.write(self.style.WARNING('清除现有分类...'))
            SupplyCategory.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('已清除现有分类'))
        
        self.stdout.write(self.style.WARNING('开始创建办公用品分类体系...'))
        
        # 定义分类结构
        categories_data = [
            {
                'name': '基础文具与耗材类',
                'description': '最核心、消耗最快的部分，管理重点是标准化和防浪费',
                'sort_order': 1,
                'children': [
                    {
                        'name': '书写工具',
                        'description': '中性笔（黑/红/蓝）、圆珠笔、钢笔、记号笔（荧光笔）、白板笔（多种颜色）、投影笔、铅笔（含自动铅笔）、彩色笔、笔芯',
                        'sort_order': 1,
                    },
                    {
                        'name': '纸张本册',
                        'description': '打印纸（A4/A3/彩打纸、照片纸、标签纸、信封、档案袋）、书写本（笔记本、便签纸、拍纸簿、速记本）、印刷品（公司信纸、稿纸、票据单、收据）',
                        'sort_order': 2,
                    },
                    {
                        'name': '修正与粘合工具',
                        'description': '修正带、修正液、橡皮、透明胶带（宽/窄）、双面胶、泡棉胶、固体胶、液体胶水、万能胶、点胶器',
                        'sort_order': 3,
                    },
                    {
                        'name': '装订与收纳工具',
                        'description': '装订：订书机（标准/重型）、订书针、起钉器、长尾夹（多种尺寸）、回形针、票据夹、推夹器；收纳：拉链袋、风琴包、文件袋、透明活页套、索引标签贴',
                        'sort_order': 4,
                    },
                    {
                        'name': '桌面工具',
                        'description': '计算器（普通/财务）、剪刀、美工刀、刀片、切割垫、尺子（直尺/三角尺）、放大镜、削笔器、打孔器（单孔/多孔）、号码机、日期章',
                        'sort_order': 5,
                    },
                ],
            },
            {
                'name': '文件管理与存储类',
                'description': '管理目标是让信息有序、易检索、安全保存',
                'sort_order': 2,
                'children': [
                    {
                        'name': '文件文件夹',
                        'description': '单页夹、快劳夹（抽杆夹）、报告夹、活页夹（多种规格）、悬挂文件夹、档案盒',
                        'sort_order': 1,
                    },
                    {
                        'name': '文件柜与收纳系统',
                        'description': '柜体：铁皮文件柜、木质档案柜、抽屉柜、活动柜；内部配件：文件夹挂架、分隔板、抽屉分隔盒',
                        'sort_order': 2,
                    },
                    {
                        'name': '标识与展示',
                        'description': '文件标识标签、索引卡、展示板、告示板、白板（小型桌面用）',
                        'sort_order': 3,
                    },
                ],
            },
            {
                'name': '办公设备与技术耗材类',
                'description': '资产管理的核心，价值高，需关注全生命周期',
                'sort_order': 3,
                'children': [
                    {
                        'name': '核心输出设备',
                        'description': '激光打印机、喷墨打印机、复印机、多功能一体机、扫描仪、传真机、大幅面绘图仪',
                        'sort_order': 1,
                    },
                    {
                        'name': '设备专用耗材',
                        'description': '墨盒、硒鼓、碳粉、色带、打印头、感光鼓、复印纸卷。严格管控，可推行部门预算、使用原装/通用耗材对比测试，回收空耗材',
                        'sort_order': 2,
                    },
                    {
                        'name': 'IT与网络配件',
                        'description': '连接与扩展：U盘、移动硬盘、SSD、读卡器、各种数据线（USB/HDMI等）、转换器/扩展坞、网线、交换机；电力：排插、UPS不间断电源、电池（5号/7号/纽扣）',
                        'sort_order': 3,
                    },
                    {
                        'name': '设备维护与支持',
                        'description': '碎纸机（及碎纸机油）、装订机（热熔/梳式）、支票打印机、标签打印机、点验钞机',
                        'sort_order': 4,
                    },
                ],
            },
            {
                'name': '办公家具与设施类',
                'description': '属于固定资产，关注人体工学、空间利用和员工健康',
                'sort_order': 4,
                'children': [
                    {
                        'name': '工作位系统',
                        'description': '办公桌（工位桌/L形桌/升降桌）、办公椅（人体工学椅）、抽屉柜、活动边柜、屏风/隔断',
                        'sort_order': 1,
                    },
                    {
                        'name': '会议与公共家具',
                        'description': '会议桌、会议椅、折叠椅、沙发、茶几、前台、接待区家具、文件柜、更衣柜',
                        'sort_order': 2,
                    },
                    {
                        'name': '环境设施',
                        'description': '白板（墙面/移动）、绿植、窗帘、地毯、置物架、衣帽架',
                        'sort_order': 3,
                    },
                ],
            },
            {
                'name': '通信、会议与展示类',
                'description': '目标是提升沟通和协作效率',
                'sort_order': 5,
                'children': [
                    {
                        'name': '传统会议用品',
                        'description': '白板及配套（白板擦、白板液）、激光笔、发言话筒、桌签、计时器',
                        'sort_order': 1,
                    },
                    {
                        'name': '现代音视频设备',
                        'description': '投影仪及幕布、视频会议摄像头、全向麦克风、会议音响、智能交互平板（如MAXHUB）',
                        'sort_order': 2,
                    },
                    {
                        'name': '展示与宣传',
                        'description': '易拉宝、X展架、海报架、宣传栏、黑板/公告栏',
                        'sort_order': 3,
                    },
                ],
            },
            {
                'name': '办公环境与维护类',
                'description': '保障办公场所安全、整洁、舒适，体现人文关怀',
                'sort_order': 6,
                'children': [
                    {
                        'name': '清洁用品',
                        'description': '洗手液、消毒液、洁厕剂、垃圾袋、抹布、拖把、扫帚、垃圾桶（桌面/脚踏）',
                        'sort_order': 1,
                    },
                    {
                        'name': '环境改善',
                        'description': '空气净化器、加湿器、电风扇/暖风机、饮水机/净水器、微波炉、冰箱',
                        'sort_order': 2,
                    },
                    {
                        'name': '安全与应急',
                        'description': '急救药箱（含常备药品）、灭火器、消防面具、应急手电、安全警示标识',
                        'sort_order': 3,
                    },
                ],
            },
            {
                'name': '个人便利与福利类',
                'description': '提升员工归属感和工作效率的"软性"用品',
                'sort_order': 7,
                'children': [
                    {
                        'name': '个人防护与健康',
                        'description': '防蓝光眼镜、颈椎托、腰靠、午睡枕、小毛毯、静音耳塞',
                        'sort_order': 1,
                    },
                    {
                        'name': '茶歇用品',
                        'description': '咖啡、茶叶、糖包、搅拌棒、纸杯、杯垫、纸巾、零食（可选）',
                        'sort_order': 2,
                    },
                ],
            },
        ]
        
        created_count = 0
        parent_count = 0
        child_count = 0
        
        # 创建分类
        for parent_data in categories_data:
            # 创建父分类
            parent_category, created = SupplyCategory.objects.get_or_create(
                name=parent_data['name'],
                defaults={
                    'description': parent_data['description'],
                    'sort_order': parent_data['sort_order'],
                    'parent': None,
                }
            )
            if created:
                parent_count += 1
                self.stdout.write(f'  ✓ 创建大类: {parent_category.name}')
            else:
                # 更新现有分类
                parent_category.description = parent_data['description']
                parent_category.sort_order = parent_data['sort_order']
                parent_category.save()
                self.stdout.write(f'  → 更新大类: {parent_category.name}')
            
            # 创建子分类
            for child_data in parent_data.get('children', []):
                child_category, created = SupplyCategory.objects.get_or_create(
                    name=child_data['name'],
                    parent=parent_category,
                    defaults={
                        'description': child_data['description'],
                        'sort_order': child_data['sort_order'],
                    }
                )
                if created:
                    child_count += 1
                    self.stdout.write(f'    ✓ 创建子类: {parent_category.name} > {child_category.name}')
                else:
                    # 更新现有子分类
                    child_category.description = child_data['description']
                    child_category.sort_order = child_data['sort_order']
                    child_category.save()
                    self.stdout.write(f'    → 更新子类: {parent_category.name} > {child_category.name}')
        
        created_count = parent_count + child_count
        
        # 输出统计信息
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS('分类创建完成！统计信息：'))
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(f'  大类数量: {len(categories_data)} 个')
        total_children = sum(len(cat.get('children', [])) for cat in categories_data)
        self.stdout.write(f'  子类数量: {total_children} 个')
        self.stdout.write(f'  本次创建: {created_count} 个分类')
        self.stdout.write(f'    - 大类: {parent_count} 个')
        self.stdout.write(f'    - 子类: {child_count} 个')
        self.stdout.write(self.style.SUCCESS('=' * 60))
        
        # 显示分类树
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('分类体系结构：'))
        for parent in SupplyCategory.objects.filter(parent__isnull=True).order_by('sort_order'):
            self.stdout.write(f'  {parent.name} ({parent.code})')
            for child in parent.children.all().order_by('sort_order'):
                self.stdout.write(f'    └─ {child.name} ({child.code})')
