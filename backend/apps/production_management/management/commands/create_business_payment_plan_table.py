"""
Django管理命令：创建 business_payment_plan 表
使用方法：python manage.py create_business_payment_plan_table
"""
from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = '创建 business_payment_plan 表（如果不存在）'

    def handle(self, *args, **options):
        sql = """
        -- 创建 business_payment_plan 表
        CREATE TABLE IF NOT EXISTS business_payment_plan (
            id BIGSERIAL PRIMARY KEY,
            phase_name VARCHAR(100) NOT NULL,
            phase_description TEXT,
            planned_amount NUMERIC(12, 2) NOT NULL,
            planned_date DATE NOT NULL,
            actual_amount NUMERIC(12, 2),
            actual_date DATE,
            status VARCHAR(20) NOT NULL DEFAULT 'pending',
            trigger_condition VARCHAR(100),
            condition_detail VARCHAR(200),
            notes TEXT,
            created_time TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_time TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
            contract_id BIGINT NOT NULL,
            CONSTRAINT business_payment_plan_contract_id_fkey 
                FOREIGN KEY (contract_id) 
                REFERENCES business_contract(id) 
                ON DELETE CASCADE
        );

        -- 创建索引
        CREATE INDEX IF NOT EXISTS business_payment_plan_contract_id_idx 
            ON business_payment_plan(contract_id);
        CREATE INDEX IF NOT EXISTS business_payment_plan_status_idx 
            ON business_payment_plan(status);
        CREATE INDEX IF NOT EXISTS business_payment_plan_planned_date_idx 
            ON business_payment_plan(planned_date);
        """
        
        try:
            with connection.cursor() as cursor:
                # 执行SQL语句
                cursor.execute(sql)
                self.stdout.write(self.style.SUCCESS('✅ business_payment_plan 表创建成功！'))
                
                # 验证表是否存在
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = 'business_payment_plan'
                    );
                """)
                exists = cursor.fetchone()[0]
                
                if exists:
                    self.stdout.write(self.style.SUCCESS('✅ 表验证成功：business_payment_plan 表已存在'))
                else:
                    self.stdout.write(self.style.WARNING('⚠️  警告：表可能未创建成功'))
                    
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ 创建表时出错：{str(e)}'))
            import traceback
            traceback.print_exc()
            return

