# 当迁移已标记为已应用但表未创建时（如数据库被替换或曾 --fake），创建缺失表

from django.db import migrations

# 仅当表不存在时创建（PostgreSQL 用 DO 块检查）
CREATE_BUSINESS_OPPORTUNITY_SQL = """
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.tables
        WHERE table_schema = 'public' AND table_name = 'business_opportunity'
    ) THEN
        CREATE TABLE business_opportunity (
            id BIGSERIAL PRIMARY KEY,
            opportunity_number VARCHAR(50) NULL UNIQUE,
            name VARCHAR(200) NOT NULL,
            opportunity_type VARCHAR(30) NULL,
            project_name VARCHAR(200) NULL,
            project_address VARCHAR(500) NULL,
            project_type VARCHAR(50) NULL,
            building_area NUMERIC(15, 2) NULL,
            estimated_amount NUMERIC(15, 2) NOT NULL DEFAULT 0,
            success_probability INTEGER NOT NULL DEFAULT 10,
            weighted_amount NUMERIC(15, 2) NOT NULL DEFAULT 0,
            status VARCHAR(30) NOT NULL DEFAULT 'potential',
            urgency VARCHAR(20) NOT NULL DEFAULT 'normal',
            expected_sign_date DATE NULL,
            actual_sign_date DATE NULL,
            approval_status VARCHAR(20) NOT NULL DEFAULT 'pending',
            approved_time TIMESTAMP WITH TIME ZONE NULL,
            approval_comment TEXT NULL,
            actual_amount NUMERIC(15, 2) NULL,
            contract_number VARCHAR(100) NULL,
            win_reason TEXT NULL,
            loss_reason TEXT NULL,
            health_score INTEGER NOT NULL DEFAULT 0,
            description TEXT NULL,
            notes TEXT NULL,
            is_active BOOLEAN NOT NULL DEFAULT TRUE,
            created_time TIMESTAMP WITH TIME ZONE NOT NULL,
            updated_time TIMESTAMP WITH TIME ZONE NOT NULL,
            approver_id BIGINT NULL REFERENCES system_user(id) ON DELETE SET NULL,
            business_manager_id BIGINT NOT NULL REFERENCES system_user(id) ON DELETE RESTRICT,
            client_id BIGINT NOT NULL REFERENCES customer_client(id) ON DELETE RESTRICT,
            created_by_id BIGINT NOT NULL REFERENCES system_user(id) ON DELETE RESTRICT,
            drawing_stage BIGINT NULL REFERENCES production_management_design_stage(id) ON DELETE SET NULL,
            service_type_id BIGINT NULL REFERENCES production_management_service_type(id) ON DELETE SET NULL
        );
        CREATE INDEX business_opportunity_opportunity_number_idx ON business_opportunity (opportunity_number);
        CREATE INDEX business_opportunity_status_idx ON business_opportunity (status);
        CREATE INDEX business_opportunity_business_manager_id_status_idx ON business_opportunity (business_manager_id, status);
        CREATE INDEX business_opportunity_expected_sign_date_idx ON business_opportunity (expected_sign_date);
    END IF;
END $$;
"""


class Migration(migrations.Migration):

    dependencies = [
        ('opportunity_management', '0004_alter_fks_to_base_data'),
    ]

    operations = [
        migrations.RunSQL(CREATE_BUSINESS_OPPORTUNITY_SQL, migrations.RunSQL.noop),
    ]
