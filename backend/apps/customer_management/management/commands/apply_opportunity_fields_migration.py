"""
手动应用0022迁移：添加商机类型和服务类型字段
由于Django迁移依赖问题，使用此命令直接执行SQL
"""
from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = '手动应用0022迁移：添加商机类型和服务类型字段'

    def handle(self, *args, **options):
        self.stdout.write('开始应用0022迁移：添加商机类型和服务类型字段...')
        
        with connection.cursor() as cursor:
            try:
                # 检查opportunity_type字段是否存在
                cursor.execute("""
                    SELECT column_name FROM information_schema.columns 
                    WHERE table_name = 'business_opportunity' AND column_name = 'opportunity_type'
                """)
                if cursor.fetchone():
                    self.stdout.write(self.style.WARNING('  opportunity_type 字段已存在，跳过'))
                else:
                    # 添加opportunity_type字段
                    cursor.execute("""
                        ALTER TABLE "business_opportunity" 
                        ADD COLUMN "opportunity_type" varchar(30) NULL
                    """)
                    self.stdout.write(self.style.SUCCESS('  ✓ 添加 opportunity_type 字段'))
                
                # 检查service_type_id字段是否存在
                cursor.execute("""
                    SELECT column_name FROM information_schema.columns 
                    WHERE table_name = 'business_opportunity' AND column_name = 'service_type_id'
                """)
                if cursor.fetchone():
                    self.stdout.write(self.style.WARNING('  service_type_id 字段已存在，跳过'))
                else:
                    # 添加service_type_id字段
                    cursor.execute("""
                        ALTER TABLE "business_opportunity" 
                        ADD COLUMN "service_type_id" bigint NULL
                    """)
                    self.stdout.write(self.style.SUCCESS('  ✓ 添加 service_type_id 字段'))
                
                # 检查外键约束是否存在
                cursor.execute("""
                    SELECT constraint_name FROM information_schema.table_constraints 
                    WHERE constraint_name = 'business_opportunity_service_type_id_fk'
                    AND table_name = 'business_opportunity'
                """)
                if cursor.fetchone():
                    self.stdout.write(self.style.WARNING('  外键约束已存在，跳过'))
                else:
                    # 添加外键约束
                    cursor.execute("""
                        ALTER TABLE "business_opportunity" 
                        ADD CONSTRAINT "business_opportunity_service_type_id_fk" 
                        FOREIGN KEY ("service_type_id") 
                        REFERENCES "production_management_service_type" ("id") 
                        DEFERRABLE INITIALLY DEFERRED
                    """)
                    self.stdout.write(self.style.SUCCESS('  ✓ 添加外键约束'))
                
                # 创建索引
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS "business_opportunity_opportunity_type_idx" 
                    ON "business_opportunity" ("opportunity_type")
                """)
                self.stdout.write(self.style.SUCCESS('  ✓ 创建 opportunity_type 索引'))
                
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS "business_opportunity_service_type_id_idx" 
                    ON "business_opportunity" ("service_type_id")
                """)
                self.stdout.write(self.style.SUCCESS('  ✓ 创建 service_type_id 索引'))
                
                self.stdout.write(self.style.SUCCESS('\n✅ 迁移0022应用成功！'))
                
                # 标记迁移为已应用
                self.stdout.write('\n提示：请运行以下命令标记迁移为已应用：')
                self.stdout.write('  python manage.py migrate customer_success 0022 --fake')
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'\n❌ 迁移失败：{str(e)}'))
                import traceback
                traceback.print_exc()
                raise

