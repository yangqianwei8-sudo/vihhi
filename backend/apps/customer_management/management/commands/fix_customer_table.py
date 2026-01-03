"""
修复客户表结构，添加缺失的字段
"""
from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = '修复客户表结构，添加缺失的法律风险相关字段'

    def handle(self, *args, **options):
        self.stdout.write('开始修复客户表结构...')
        
        with connection.cursor() as cursor:
            # 检查并添加 legal_risk_level 字段
            try:
                cursor.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'customer_client' AND column_name = 'legal_risk_level'
                """)
                if not cursor.fetchone():
                    cursor.execute("""
                        ALTER TABLE customer_client 
                        ADD COLUMN legal_risk_level VARCHAR(20) DEFAULT 'unknown' 
                        CHECK (legal_risk_level IN ('low', 'medium_low', 'medium', 'medium_high', 'high', 'unknown'))
                    """)
                    self.stdout.write(self.style.SUCCESS('✓ 添加 legal_risk_level 字段'))
                else:
                    self.stdout.write('   legal_risk_level 字段已存在')
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'   ⚠ legal_risk_level: {str(e)}'))
            
            # 检查并添加 litigation_count 字段
            try:
                cursor.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'customer_client' AND column_name = 'litigation_count'
                """)
                if not cursor.fetchone():
                    cursor.execute("""
                        ALTER TABLE customer_client 
                        ADD COLUMN litigation_count INTEGER DEFAULT 0
                    """)
                    self.stdout.write(self.style.SUCCESS('✓ 添加 litigation_count 字段'))
                else:
                    self.stdout.write('   litigation_count 字段已存在')
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'   ⚠ litigation_count: {str(e)}'))
            
            # 检查并添加 executed_person_count 字段
            try:
                cursor.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'customer_client' AND column_name = 'executed_person_count'
                """)
                if not cursor.fetchone():
                    cursor.execute("""
                        ALTER TABLE customer_client 
                        ADD COLUMN executed_person_count INTEGER DEFAULT 0
                    """)
                    self.stdout.write(self.style.SUCCESS('✓ 添加 executed_person_count 字段'))
                else:
                    self.stdout.write('   executed_person_count 字段已存在')
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'   ⚠ executed_person_count: {str(e)}'))
            
            # 检查并添加 final_case_count 字段
            try:
                cursor.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'customer_client' AND column_name = 'final_case_count'
                """)
                if not cursor.fetchone():
                    cursor.execute("""
                        ALTER TABLE customer_client 
                        ADD COLUMN final_case_count INTEGER DEFAULT 0
                    """)
                    self.stdout.write(self.style.SUCCESS('✓ 添加 final_case_count 字段'))
                else:
                    self.stdout.write('   final_case_count 字段已存在')
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'   ⚠ final_case_count: {str(e)}'))
            
            # 检查并添加 consumption_limit_count 字段
            try:
                cursor.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'customer_client' AND column_name = 'consumption_limit_count'
                """)
                if not cursor.fetchone():
                    cursor.execute("""
                        ALTER TABLE customer_client 
                        ADD COLUMN consumption_limit_count INTEGER DEFAULT 0
                    """)
                    self.stdout.write(self.style.SUCCESS('✓ 添加 consumption_limit_count 字段'))
                else:
                    self.stdout.write('   consumption_limit_count 字段已存在')
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'   ⚠ consumption_limit_count: {str(e)}'))
            
            # 检查并添加 contact_name 字段
            try:
                cursor.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'customer_client' AND column_name = 'contact_name'
                """)
                if not cursor.fetchone():
                    cursor.execute("""
                        ALTER TABLE customer_client 
                        ADD COLUMN contact_name VARCHAR(100) DEFAULT ''
                    """)
                    self.stdout.write(self.style.SUCCESS('✓ 添加 contact_name 字段'))
                else:
                    self.stdout.write('   contact_name 字段已存在')
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'   ⚠ contact_name: {str(e)}'))
            
            # 检查并添加 contact_position 字段
            try:
                cursor.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'customer_client' AND column_name = 'contact_position'
                """)
                if not cursor.fetchone():
                    cursor.execute("""
                        ALTER TABLE customer_client 
                        ADD COLUMN contact_position VARCHAR(100) DEFAULT ''
                    """)
                    self.stdout.write(self.style.SUCCESS('✓ 添加 contact_position 字段'))
                else:
                    self.stdout.write('   contact_position 字段已存在')
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'   ⚠ contact_position: {str(e)}'))
        
        self.stdout.write(self.style.SUCCESS('\n✅ 客户表结构修复完成！'))

