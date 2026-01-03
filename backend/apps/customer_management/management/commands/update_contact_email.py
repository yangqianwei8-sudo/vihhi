from django.core.management.base import BaseCommand
from backend.apps.customer_management.models import ClientContact, Client


class Command(BaseCommand):
    help = '更新指定客户联系人的邮箱'

    def handle(self, *args, **options):
        # 客户名称和联系人姓名
        client_name = '四川广汇蜀信实业有限公司'
        contact_name = '张经理'
        new_email = '31972849@qq.com'

        try:
            # 查找客户
            client = Client.objects.filter(name__icontains=client_name).first()
            if not client:
                self.stdout.write(self.style.ERROR(f'未找到客户：{client_name}'))
                return

            self.stdout.write(f'找到客户：{client.name} (ID: {client.id})')

            # 查找联系人
            contact = ClientContact.objects.filter(
                client=client,
                name__icontains=contact_name
            ).first()

            if not contact:
                self.stdout.write(self.style.ERROR(f'未找到联系人：{contact_name}'))
                return

            self.stdout.write(f'找到联系人：{contact.name} (ID: {contact.id})')
            self.stdout.write(f'当前邮箱：{contact.email or "(空)"}')

            # 更新邮箱
            contact.email = new_email
            contact.save(update_fields=['email'])

            self.stdout.write(self.style.SUCCESS(
                f'✓ 成功更新联系人邮箱：{contact.name} -> {new_email}'
            ))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'更新失败：{str(e)}'))

