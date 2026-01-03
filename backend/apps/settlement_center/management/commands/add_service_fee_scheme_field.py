"""
Django管理命令：添加service_fee_scheme_id字段到ProjectSettlement表

使用方法：
    python manage.py add_service_fee_scheme_field
"""
from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = '添加service_fee_scheme_id字段到ProjectSettlement表'

    def handle(self, *args, **options):
        self.stdout.write("检查settlement_project_settlement表是否存在...")
        
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
            
            if not table_exists:
                self.stdout.write(
                    self.style.WARNING(
                        "⚠ settlement_project_settlement表不存在，跳过字段添加\n"
                        "   提示: 请先运行settlement_center的其他迁移创建此表"
                    )
                )
                return
            
            # 检查字段是否已存在
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.columns 
                    WHERE table_name = 'settlement_project_settlement' 
                    AND column_name = 'service_fee_scheme_id'
                )
            """)
            field_exists = cursor.fetchone()[0]
            
            if field_exists:
                self.stdout.write(
                    self.style.SUCCESS("✓ service_fee_scheme_id字段已存在")
                )
                return
            
            # 检查settlement_service_fee_scheme表是否存在
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'settlement_service_fee_scheme'
                )
            """)
            scheme_table_exists = cursor.fetchone()[0]
            
            if not scheme_table_exists:
                self.stdout.write(
                    self.style.ERROR(
                        "❌ settlement_service_fee_scheme表不存在，无法添加外键"
                    )
                )
                return
            
            # 添加字段
            self.stdout.write("正在添加service_fee_scheme_id字段...")
            try:
                cursor.execute("""
                    ALTER TABLE settlement_project_settlement 
                    ADD COLUMN service_fee_scheme_id BIGINT 
                    REFERENCES settlement_service_fee_scheme(id) 
                    ON DELETE SET NULL
                """)
                
                # 创建索引
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS settlement_project_settlement_service_fee_scheme_id_idx 
                    ON settlement_project_settlement(service_fee_scheme_id)
                """)
                
                self.stdout.write(
                    self.style.SUCCESS("✓ 字段添加成功")
                )
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"❌ 添加字段失败: {str(e)}")
                )
                raise

