"""
标记0022迁移为已应用
"""
from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = '标记0022迁移为已应用'

    def handle(self, *args, **options):
        self.stdout.write('标记迁移0022为已应用...')
        
        with connection.cursor() as cursor:
            try:
                # 检查迁移记录是否已存在
                cursor.execute("""
                    SELECT id FROM django_migrations 
                    WHERE app = 'customer_success' AND name = '0022_add_opportunity_type_and_service_type'
                """)
                if cursor.fetchone():
                    self.stdout.write(self.style.WARNING('迁移记录已存在'))
                else:
                    # 插入迁移记录
                    cursor.execute("""
                        INSERT INTO django_migrations (app, name, applied)
                        VALUES ('customer_success', '0022_add_opportunity_type_and_service_type', NOW())
                    """)
                    self.stdout.write(self.style.SUCCESS('✅ 迁移0022已标记为已应用'))
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'❌ 操作失败：{str(e)}'))
                import traceback
                traceback.print_exc()
                raise

