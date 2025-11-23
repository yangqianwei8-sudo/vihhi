from django.core.management.base import BaseCommand
from backend.core.test_data import create_test_data

class Command(BaseCommand):
    help = '初始化测试数据'
    
    def handle(self, *args, **options):
        create_test_data()
        self.stdout.write(
            self.style.SUCCESS('测试数据初始化完成！')
        )
