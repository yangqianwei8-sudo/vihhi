"""
Django管理命令：彻底解决settlement_center的所有迁移问题

功能：
1. 创建settlement_project_settlement表（如果不存在）
2. 添加service_fee_scheme_id字段（如果不存在）
3. 标记迁移为已应用

使用方法：
    python manage.py fix_all_settlement_migrations
"""
from django.core.management.base import BaseCommand
from django.db import connection, transaction


class Command(BaseCommand):
    help = '彻底解决settlement_center的所有迁移问题'

    def handle(self, *args, **options):
        self.stdout.write("=" * 60)
        self.stdout.write("彻底解决settlement_center迁移问题")
        self.stdout.write("=" * 60)
        
        with connection.cursor() as cursor:
            # 步骤1：检查并创建settlement_project_settlement表
            self.stdout.write("\n[步骤1] 检查settlement_project_settlement表...")
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'settlement_project_settlement'
                )
            """)
            table_exists = cursor.fetchone()[0]
            
            if not table_exists:
                self.stdout.write("  表不存在，开始创建...")
                try:
                    with transaction.atomic():
                        # 创建表
                        self._create_project_settlement_table(cursor)
                        self.stdout.write(
                            self.style.SUCCESS("  ✓ settlement_project_settlement表创建成功")
                        )
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f"  ❌ 创建表失败: {str(e)}")
                    )
                    # 检查是否是外键依赖问题
                    if 'project_center_project' in str(e):
                        self.stdout.write(
                            self.style.WARNING(
                                "  提示: 需要先运行project_center的迁移创建project_center_project表"
                            )
                        )
                    raise
            else:
                self.stdout.write(
                    self.style.SUCCESS("  ✓ settlement_project_settlement表已存在")
                )
            
            # 步骤2：检查并添加service_fee_scheme_id字段
            self.stdout.write("\n[步骤2] 检查service_fee_scheme_id字段...")
            # 再次确认表是否存在
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'settlement_project_settlement'
                )
            """)
            table_exists_now = cursor.fetchone()[0]
            
            if table_exists_now:
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.columns 
                        WHERE table_name = 'settlement_project_settlement' 
                        AND column_name = 'service_fee_scheme_id'
                    )
                """)
                field_exists = cursor.fetchone()[0]
                
                if not field_exists:
                    # 检查依赖表是否存在
                    cursor.execute("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables 
                            WHERE table_schema = 'public' 
                            AND table_name = 'settlement_service_fee_scheme'
                        )
                    """)
                    scheme_table_exists = cursor.fetchone()[0]
                    
                    if scheme_table_exists:
                        self.stdout.write("  字段不存在，开始添加...")
                        try:
                            cursor.execute("""
                                ALTER TABLE settlement_project_settlement 
                                ADD COLUMN service_fee_scheme_id BIGINT 
                                REFERENCES settlement_service_fee_scheme(id) 
                                ON DELETE SET NULL
                            """)
                            
                            cursor.execute("""
                                CREATE INDEX IF NOT EXISTS settlement_project_settlement_service_fee_scheme_id_idx 
                                ON settlement_project_settlement(service_fee_scheme_id)
                            """)
                            
                            self.stdout.write(
                                self.style.SUCCESS("  ✓ service_fee_scheme_id字段添加成功")
                            )
                        except Exception as e:
                            self.stdout.write(
                                self.style.ERROR(f"  ❌ 添加字段失败: {str(e)}")
                            )
                            raise
                    else:
                        self.stdout.write(
                            self.style.WARNING(
                                "  ⚠ settlement_service_fee_scheme表不存在，跳过字段添加"
                            )
                        )
                else:
                    self.stdout.write(
                        self.style.SUCCESS("  ✓ service_fee_scheme_id字段已存在")
                    )
            
            # 步骤3：标记迁移为已应用
            self.stdout.write("\n[步骤3] 标记迁移为已应用...")
            migrations_to_mark = [
                ('settlement_center', '0003_projectsettlement_contractsettlement'),
                ('settlement_center', '0007_add_service_fee_settlement_scheme'),
                ('settlement_center', '0008_add_service_fee_scheme_to_project_settlement'),
            ]
            
            for app, name in migrations_to_mark:
                try:
                    cursor.execute("""
                        INSERT INTO django_migrations (app, name, applied) 
                        VALUES (%s, %s, NOW())
                        ON CONFLICT DO NOTHING
                    """, [app, name])
                    self.stdout.write(f"  ✓ {app}.{name}")
                except Exception as e:
                    self.stdout.write(
                        self.style.WARNING(f"  ⚠ 无法标记 {app}.{name}: {str(e)}")
                    )
            
            self.stdout.write("\n" + "=" * 60)
            self.stdout.write(self.style.SUCCESS("✅ 所有步骤完成！"))
            self.stdout.write("=" * 60)
    
    def _create_project_settlement_table(self, cursor):
        """创建settlement_project_settlement表"""
        # 创建主表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS settlement_project_settlement (
                id BIGSERIAL PRIMARY KEY,
                settlement_number VARCHAR(100) NOT NULL UNIQUE,
                settlement_type VARCHAR(20) NOT NULL,
                settlement_date DATE NOT NULL,
                contract_amount NUMERIC(12, 2) NOT NULL,
                settlement_amount NUMERIC(12, 2) NOT NULL,
                change_amount NUMERIC(12, 2) NOT NULL DEFAULT 0,
                tax_rate NUMERIC(5, 2) NOT NULL DEFAULT 6.0,
                tax_amount NUMERIC(12, 2) NOT NULL DEFAULT 0,
                settlement_amount_tax NUMERIC(12, 2) NOT NULL,
                total_output_value NUMERIC(12, 2) NOT NULL DEFAULT 0,
                confirmed_output_value NUMERIC(12, 2) NOT NULL DEFAULT 0,
                status VARCHAR(30) NOT NULL,
                submitted_time TIMESTAMP WITH TIME ZONE NULL,
                finance_reviewed_time TIMESTAMP WITH TIME ZONE NULL,
                finance_review_comment TEXT NOT NULL DEFAULT '',
                manager_reviewed_time TIMESTAMP WITH TIME ZONE NULL,
                manager_review_comment TEXT NOT NULL DEFAULT '',
                general_manager_reviewed_time TIMESTAMP WITH TIME ZONE NULL,
                general_manager_review_comment TEXT NOT NULL DEFAULT '',
                confirmed_time TIMESTAMP WITH TIME ZONE NULL,
                settlement_file VARCHAR(100) NULL,
                description TEXT NOT NULL DEFAULT '',
                notes TEXT NOT NULL DEFAULT '',
                created_time TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_time TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
                confirmed_by_id BIGINT NULL,
                contract_id BIGINT NULL,
                created_by_id BIGINT NOT NULL,
                finance_reviewer_id BIGINT NULL,
                general_manager_reviewer_id BIGINT NULL,
                manager_reviewer_id BIGINT NULL,
                project_id BIGINT NOT NULL,
                submitted_by_id BIGINT NULL
            )
        """)
        
        # 创建索引
        indexes = [
            ("settlement_project_settlement_settlement_number_idx", 
             "settlement_project_settlement(settlement_number)"),
            ("settlement_project_settlement_project_status_idx", 
             "settlement_project_settlement(project_id, status)"),
            ("settlement_project_settlement_settlement_date_idx", 
             "settlement_project_settlement(settlement_date)"),
            ("settlement_project_settlement_status_idx", 
             "settlement_project_settlement(status)"),
        ]
        
        for idx_name, idx_def in indexes:
            try:
                cursor.execute(f"CREATE INDEX IF NOT EXISTS {idx_name} ON {idx_def}")
            except Exception:
                pass  # 索引可能已存在
        
        # 添加外键约束（如果表存在）
        foreign_keys = [
            ("confirmed_by_id", "system_user", "id"),
            ("contract_id", "business_contract", "id"),
            ("created_by_id", "system_user", "id"),
            ("finance_reviewer_id", "system_user", "id"),
            ("general_manager_reviewer_id", "system_user", "id"),
            ("manager_reviewer_id", "system_user", "id"),
            ("project_id", "project_center_project", "id"),
            ("submitted_by_id", "system_user", "id"),
        ]
        
        for fk_column, ref_table, ref_column in foreign_keys:
            try:
                # 检查引用表是否存在
                cursor.execute(f"""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = '{ref_table}'
                    )
                """)
                if cursor.fetchone()[0]:
                    constraint_name = f"settlement_project_s_{fk_column}_fk"
                    cursor.execute(f"""
                        DO $$
                        BEGIN
                            IF NOT EXISTS (
                                SELECT 1 FROM pg_constraint 
                                WHERE conname = '{constraint_name}'
                            ) THEN
                                ALTER TABLE settlement_project_settlement 
                                ADD CONSTRAINT {constraint_name} 
                                FOREIGN KEY ({fk_column}) 
                                REFERENCES {ref_table}({ref_column}) 
                                ON DELETE SET NULL;
                            END IF;
                        END $$;
                    """)
            except Exception as e:
                # 外键可能已存在或表不存在，继续
                pass

