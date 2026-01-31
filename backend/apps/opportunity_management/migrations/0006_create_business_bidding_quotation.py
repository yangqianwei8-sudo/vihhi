# 创建缺失的 business_bidding_quotation 表（与 0001_initial 一致）

from django.db import migrations

CREATE_BUSINESS_BIDDING_QUOTATION_SQL = """
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.tables
        WHERE table_schema = 'public' AND table_name = 'business_bidding_quotation'
    ) THEN
        CREATE TABLE business_bidding_quotation (
            id BIGSERIAL PRIMARY KEY,
            bidding_number VARCHAR(100) NULL,
            bidding_date DATE NOT NULL,
            submission_deadline DATE NOT NULL,
            status VARCHAR(20) NOT NULL DEFAULT 'draft',
            tender_requirements TEXT NOT NULL,
            technical_proposal JSONB NOT NULL DEFAULT '{}',
            commercial_proposal JSONB NOT NULL DEFAULT '{}',
            personnel_certificates JSONB NOT NULL DEFAULT '[]',
            company_certificates JSONB NOT NULL DEFAULT '[]',
            bidding_documents JSONB NOT NULL DEFAULT '[]',
            notes TEXT NULL,
            created_time TIMESTAMP WITH TIME ZONE NOT NULL,
            updated_time TIMESTAMP WITH TIME ZONE NOT NULL,
            created_by_id BIGINT NOT NULL REFERENCES system_user(id) ON DELETE RESTRICT,
            opportunity_id BIGINT NOT NULL REFERENCES business_opportunity(id) ON DELETE CASCADE
        );
        CREATE INDEX business_bidding_quotation_opportunity_id_idx ON business_bidding_quotation (opportunity_id);
        CREATE INDEX business_bidding_quotation_bidding_date_idx ON business_bidding_quotation (bidding_date);
        CREATE INDEX business_bidding_quotation_status_idx ON business_bidding_quotation (status);
    END IF;
END $$;
"""

# M2M 中间表：similar_projects（Django 默认命名为 <db_table>_<field_name>）
CREATE_BIDDING_QUOTATION_SIMILAR_PROJECTS_SQL = """
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.tables
        WHERE table_schema = 'public' AND table_name = 'business_bidding_quotation_similar_projects'
    ) THEN
        CREATE TABLE business_bidding_quotation_similar_projects (
            id BIGSERIAL PRIMARY KEY,
            biddingquotation_id BIGINT NOT NULL REFERENCES business_bidding_quotation(id) ON DELETE CASCADE,
            project_id BIGINT NOT NULL REFERENCES production_management_project(id) ON DELETE CASCADE,
            UNIQUE (biddingquotation_id, project_id)
        );
        CREATE INDEX business_bidding_quotation_similar_projects_biddingquotation_id_idx
            ON business_bidding_quotation_similar_projects (biddingquotation_id);
        CREATE INDEX business_bidding_quotation_similar_projects_project_id_idx
            ON business_bidding_quotation_similar_projects (project_id);
    END IF;
END $$;
"""


class Migration(migrations.Migration):

    dependencies = [
        ('opportunity_management', '0005_create_missing_tables'),
    ]

    operations = [
        migrations.RunSQL(CREATE_BUSINESS_BIDDING_QUOTATION_SQL, migrations.RunSQL.noop),
        migrations.RunSQL(CREATE_BIDDING_QUOTATION_SIMILAR_PROJECTS_SQL, migrations.RunSQL.noop),
    ]
