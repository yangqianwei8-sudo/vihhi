"""
Django管理命令：创建settlement_project_settlement表（如果不存在）

使用方法：
    python manage.py create_settlement_project_settlement_table
"""
from django.core.management.base import BaseCommand
from django.db import connection
from django.core.management import call_command


class Command(BaseCommand):
    help = '创建settlement_project_settlement表（如果不存在）'

    def handle(self, *args, **options):
        self.stdout.write("=" * 60)
        self.stdout.write("创建settlement_project_settlement表")
        self.stdout.write("=" * 60)
        
        with connection.cursor() as cursor:
            # 检查表是否存在
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'settlement_project_settlement'
                )
            """)
            table_exists = cursor.fetchone()[0]
            
            if table_exists:
                self.stdout.write(
                    self.style.SUCCESS("✓ settlement_project_settlement表已存在")
                )
                return
            
            self.stdout.write("\n⚠ settlement_project_settlement表不存在")
            self.stdout.write("尝试运行迁移0003来创建此表...")
            
            try:
                # 尝试运行迁移
                call_command('migrate', 'settlement_center', '0003', verbosity=2)
                self.stdout.write(
                    self.style.SUCCESS("\n✓ 迁移执行成功")
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"\n❌ 迁移执行失败: {str(e)}")
                )
                self.stdout.write("\n建议手动执行SQL或解决迁移依赖问题")
                self.stdout.write("\n可以查看迁移文件:")
                self.stdout.write("  backend/apps/settlement_center/migrations/0003_projectsettlement_contractsettlement.py")
                raise

