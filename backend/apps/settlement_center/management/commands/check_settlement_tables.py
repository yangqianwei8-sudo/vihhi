"""
Django管理命令：检查settlement相关表的状态

使用方法：
    python manage.py check_settlement_tables
"""
from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = '检查settlement相关表的状态'

    def handle(self, *args, **options):
        self.stdout.write("=" * 60)
        self.stdout.write("检查settlement相关表的状态")
        self.stdout.write("=" * 60)
        
        with connection.cursor() as cursor:
            # 检查所有settlement相关的表
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name LIKE '%settlement%'
                ORDER BY table_name
            """)
            tables = [row[0] for row in cursor.fetchall()]
            
            self.stdout.write(f"\n找到 {len(tables)} 个settlement相关表:")
            for table in tables:
                self.stdout.write(f"  ✓ {table}")
            
            # 检查关键表
            key_tables = {
                'settlement_project_settlement': '项目结算表',
                'settlement_service_fee_scheme': '服务费结算方案表',
            }
            
            self.stdout.write("\n" + "=" * 60)
            self.stdout.write("关键表状态检查")
            self.stdout.write("=" * 60)
            
            for table_name, description in key_tables.items():
                exists = table_name in tables
                status = "✓ 存在" if exists else "✗ 不存在"
                self.stdout.write(f"\n{table_name} ({description}): {status}")
                
                if exists:
                    # 检查字段
                    if table_name == 'settlement_project_settlement':
                        cursor.execute("""
                            SELECT column_name 
                            FROM information_schema.columns 
                            WHERE table_name = 'settlement_project_settlement' 
                            AND column_name = 'service_fee_scheme_id'
                        """)
                        has_field = cursor.fetchone() is not None
                        if has_field:
                            self.stdout.write(f"  ✓ service_fee_scheme_id字段已存在")
                        else:
                            self.stdout.write(f"  ⚠ service_fee_scheme_id字段不存在")
                            self.stdout.write(f"    运行: python manage.py add_service_fee_scheme_field")
            
            # 提供建议
            self.stdout.write("\n" + "=" * 60)
            self.stdout.write("建议操作")
            self.stdout.write("=" * 60)
            
            if 'settlement_project_settlement' not in tables:
                self.stdout.write("\n⚠ settlement_project_settlement表不存在")
                self.stdout.write("需要运行settlement_center的迁移来创建此表:")
                self.stdout.write("  python manage.py migrate settlement_center 0003")
                self.stdout.write("或者运行所有settlement_center迁移:")
                self.stdout.write("  python manage.py migrate settlement_center")
            
            if 'settlement_service_fee_scheme' not in tables:
                self.stdout.write("\n⚠ settlement_service_fee_scheme表不存在")
                self.stdout.write("需要运行迁移0007:")
                self.stdout.write("  python manage.py migrate settlement_center 0007")
            
            if 'settlement_project_settlement' in tables and 'settlement_service_fee_scheme' in tables:
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.columns 
                        WHERE table_name = 'settlement_project_settlement' 
                        AND column_name = 'service_fee_scheme_id'
                    )
                """)
                has_field = cursor.fetchone()[0]
                if not has_field:
                    self.stdout.write("\n✓ 两个表都存在，可以添加字段:")
                    self.stdout.write("  python manage.py add_service_fee_scheme_field")
                else:
                    self.stdout.write("\n✅ 所有表都已就绪！")

