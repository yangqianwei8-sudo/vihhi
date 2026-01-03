"""
初始化客户类型和客户分级的命令
使用方法：python manage.py init_client_types_and_grades
"""
from django.core.management.base import BaseCommand
from backend.apps.customer_management.models import ClientType, ClientGrade


class Command(BaseCommand):
    help = '初始化客户类型和客户分级数据'

    def handle(self, *args, **options):
        self.stdout.write('开始初始化客户类型和客户分级数据...')
        
        # 定义客户类型数据
        client_types = [
            {'code': 'developer', 'name': '开发商', 'display_order': 1, 'description': '房地产开发企业'},
            {'code': 'government', 'name': '政府机构', 'display_order': 2, 'description': '政府机关、事业单位'},
            {'code': 'enterprise', 'name': '企业', 'display_order': 3, 'description': '一般企业客户'},
            {'code': 'institution', 'name': '机构', 'display_order': 4, 'description': '其他机构客户'},
            {'code': 'individual', 'name': '个人', 'display_order': 5, 'description': '个人客户'},
        ]
        
        # 定义客户分级数据
        client_grades = [
            {'code': 'strategic', 'name': '战略客户', 'display_order': 1, 'description': '评分≥80分，重要战略合作伙伴'},
            {'code': 'core', 'name': '核心客户', 'display_order': 2, 'description': '评分≥60分，核心业务客户'},
            {'code': 'potential', 'name': '潜力客户', 'display_order': 3, 'description': '评分≥40分，有发展潜力的客户'},
            {'code': 'regular', 'name': '常规客户', 'display_order': 4, 'description': '评分≥20分，常规业务客户'},
            {'code': 'nurturing', 'name': '培育客户', 'display_order': 5, 'description': '评分≥10分，需要培育的客户'},
            {'code': 'observing', 'name': '观察客户', 'display_order': 6, 'description': '评分<10分，需要观察的客户'},
        ]
        
        # 创建或更新客户类型
        created_count = 0
        updated_count = 0
        for type_data in client_types:
            obj, created = ClientType.objects.update_or_create(
                code=type_data['code'],
                defaults={
                    'name': type_data['name'],
                    'display_order': type_data['display_order'],
                    'description': type_data['description'],
                    'is_active': True,
                }
            )
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'✓ 创建客户类型: {obj.name}'))
            else:
                updated_count += 1
                self.stdout.write(self.style.WARNING(f'~ 更新客户类型: {obj.name}'))
        
        self.stdout.write(f'\n客户类型处理完成：创建 {created_count} 个，更新 {updated_count} 个')
        
        # 创建或更新客户分级
        created_count = 0
        updated_count = 0
        for grade_data in client_grades:
            obj, created = ClientGrade.objects.update_or_create(
                code=grade_data['code'],
                defaults={
                    'name': grade_data['name'],
                    'display_order': grade_data['display_order'],
                    'description': grade_data['description'],
                    'is_active': True,
                }
            )
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'✓ 创建客户分级: {obj.name}'))
            else:
                updated_count += 1
                self.stdout.write(self.style.WARNING(f'~ 更新客户分级: {obj.name}'))
        
        self.stdout.write(f'\n客户分级处理完成：创建 {created_count} 个，更新 {updated_count} 个')
        self.stdout.write(self.style.SUCCESS('\n✓ 初始化完成！'))















