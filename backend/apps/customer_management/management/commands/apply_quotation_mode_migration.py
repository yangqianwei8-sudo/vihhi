"""
手动应用报价模式字段迁移
由于permission_management迁移问题，使用此命令手动添加字段
"""
from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = '手动应用报价模式字段迁移'

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            try:
                # 检查表是否存在
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = 'business_opportunity_quotation'
                    );
                """)
                table_exists = cursor.fetchone()[0]
                
                if not table_exists:
                    self.stdout.write(self.style.ERROR('表 business_opportunity_quotation 不存在'))
                    return
                
                # 检查字段是否已存在
                cursor.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'business_opportunity_quotation' 
                    AND column_name = 'quotation_mode';
                """)
                if cursor.fetchone():
                    self.stdout.write(self.style.WARNING('字段已存在，跳过迁移'))
                    return
                
                self.stdout.write('开始添加报价模式字段...')
                
                # 添加 quotation_mode 字段
                cursor.execute("""
                    ALTER TABLE business_opportunity_quotation 
                    ADD COLUMN quotation_mode VARCHAR(30) DEFAULT 'rate' NOT NULL;
                """)
                self.stdout.write(self.style.SUCCESS('✓ 添加 quotation_mode 字段'))
                
                # 添加 mode_params 字段（JSONB类型，PostgreSQL）
                cursor.execute("""
                    ALTER TABLE business_opportunity_quotation 
                    ADD COLUMN mode_params JSONB DEFAULT '{}' NOT NULL;
                """)
                self.stdout.write(self.style.SUCCESS('✓ 添加 mode_params 字段'))
                
                # 添加 cap_fee 字段
                cursor.execute("""
                    ALTER TABLE business_opportunity_quotation 
                    ADD COLUMN cap_fee NUMERIC(15, 2) NULL;
                """)
                self.stdout.write(self.style.SUCCESS('✓ 添加 cap_fee 字段'))
                
                # 添加 saved_amount 字段
                cursor.execute("""
                    ALTER TABLE business_opportunity_quotation 
                    ADD COLUMN saved_amount NUMERIC(15, 2) DEFAULT 0 NULL;
                """)
                self.stdout.write(self.style.SUCCESS('✓ 添加 saved_amount 字段'))
                
                # 添加 service_fee 字段
                cursor.execute("""
                    ALTER TABLE business_opportunity_quotation 
                    ADD COLUMN service_fee NUMERIC(15, 2) DEFAULT 0 NOT NULL;
                """)
                self.stdout.write(self.style.SUCCESS('✓ 添加 service_fee 字段'))
                
                # 添加 calculation_steps 字段（JSONB类型）
                cursor.execute("""
                    ALTER TABLE business_opportunity_quotation 
                    ADD COLUMN calculation_steps JSONB DEFAULT '[]' NOT NULL;
                """)
                self.stdout.write(self.style.SUCCESS('✓ 添加 calculation_steps 字段'))
                
                # 标记迁移为已应用
                cursor.execute("""
                    INSERT INTO django_migrations (app, name, applied)
                    VALUES ('customer_success', '0012_add_quotation_mode_fields', NOW())
                    ON CONFLICT DO NOTHING;
                """)
                self.stdout.write(self.style.SUCCESS('✓ 标记迁移为已应用'))
                
                self.stdout.write(self.style.SUCCESS('\n所有字段添加成功！'))
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'执行失败: {str(e)}'))
                import traceback
                self.stdout.write(self.style.ERROR(traceback.format_exc()))

