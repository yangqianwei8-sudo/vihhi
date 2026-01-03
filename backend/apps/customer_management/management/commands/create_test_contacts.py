"""
为攀枝花山水铜锣置业有限公司创建5条测试联系人信息
使用方法: python manage.py create_test_contacts
"""
from django.core.management.base import BaseCommand
from backend.apps.customer_management.models import Client, ClientContact
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = '为攀枝花山水铜锣置业有限公司创建5条测试联系人信息'

    def handle(self, *args, **options):
        client_name = "攀枝花山水铜锣置业有限公司"
        
        try:
            client = Client.objects.get(name=client_name)
            self.stdout.write(self.style.SUCCESS(f'✓ 找到客户: {client.name} (ID: {client.id})'))
            
            # 获取第一个用户作为创建人
            creator = User.objects.filter(is_active=True).first()
            if not creator:
                creator = User.objects.first()
            
            if creator:
                self.stdout.write(f'  使用创建人: {creator.username}')
            
            # 创建5条联系人信息
            contacts_data = [
                {"name": "张三", "phone": "13800138001", "email": "zhangsan@example.com", "office_address": "攀枝花市东区"},
                {"name": "李四", "phone": "13800138002", "email": "lisi@example.com", "office_address": "攀枝花市西区"},
                {"name": "王五", "phone": "13800138003", "email": "wangwu@example.com", "office_address": "攀枝花市仁和区"},
                {"name": "赵六", "phone": "13800138004", "email": "zhaoliu@example.com", "office_address": "攀枝花市米易县"},
                {"name": "钱七", "phone": "13800138005", "email": "qianqi@example.com", "office_address": "攀枝花市盐边县"},
            ]
            
            created_count = 0
            for contact_data in contacts_data:
                # 检查是否已存在同名联系人
                existing = ClientContact.objects.filter(client=client, name=contact_data["name"]).first()
                if existing:
                    self.stdout.write(self.style.WARNING(f'  ⚠ 联系人 "{contact_data["name"]}" 已存在 (ID: {existing.id})，跳过'))
                    continue
                
                contact = ClientContact.objects.create(
                    client=client,
                    name=contact_data["name"],
                    phone=contact_data["phone"],
                    email=contact_data["email"],
                    office_address=contact_data["office_address"],
                    role='contact_person',  # 对接人
                    relationship_level='requirement_communication',  # 需求沟通
                    decision_influence='medium',  # 中
                    contact_frequency='weekly',  # 每周
                    is_primary=False,
                    created_by=creator
                )
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'  ✓ 创建联系人: {contact.name} (ID: {contact.id}, 电话: {contact.phone})'))
            
            self.stdout.write(self.style.SUCCESS(f'\n✓ 成功创建 {created_count} 条联系人信息'))
            self.stdout.write(f'  客户: {client.name}')
            self.stdout.write(f'  总联系人数量: {ClientContact.objects.filter(client=client).count()}')
            
            # 列出所有联系人
            self.stdout.write('\n所有联系人列表:')
            for contact in ClientContact.objects.filter(client=client).order_by('name'):
                self.stdout.write(f'  - {contact.name} (电话: {contact.phone}, 邮箱: {contact.email})')
            
        except Client.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'✗ 未找到客户: {client_name}'))
            self.stdout.write('  请先创建该客户，或检查客户名称是否正确')
            self.stdout.write('\n可用的客户列表（前10个）:')
            for client in Client.objects.all()[:10]:
                self.stdout.write(f'  - {client.name}')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ 创建联系人失败: {str(e)}'))
            import traceback
            traceback.print_exc()

