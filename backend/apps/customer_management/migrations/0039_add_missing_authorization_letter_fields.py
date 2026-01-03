# Generated manually to add missing fields to AuthorizationLetter model
# Using RunSQL to bypass Django migration dependency issues

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('customer_management', '0038_remove_service_content_fields'),
    ]

    operations = [
        # Add project_number field
        migrations.RunSQL(
            sql="""
                DO $$ 
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name='business_authorization_letter' AND column_name='project_number'
                    ) THEN
                        ALTER TABLE business_authorization_letter 
                        ADD COLUMN project_number VARCHAR(50) NULL;
                        CREATE UNIQUE INDEX IF NOT EXISTS business_authorization_letter_project_number_unique 
                        ON business_authorization_letter(project_number) WHERE project_number IS NOT NULL;
                    END IF;
                END $$;
            """,
            reverse_sql="""
                ALTER TABLE business_authorization_letter 
                DROP COLUMN IF EXISTS project_number;
            """
        ),
        # Add client_contact field
        migrations.RunSQL(
            sql="""
                DO $$ 
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name='business_authorization_letter' AND column_name='client_contact_id'
                    ) THEN
                        ALTER TABLE business_authorization_letter 
                        ADD COLUMN client_contact_id BIGINT NULL;
                        ALTER TABLE business_authorization_letter 
                        ADD CONSTRAINT business_authorization_letter_client_contact_id_fk 
                        FOREIGN KEY (client_contact_id) REFERENCES customer_contact(id) ON DELETE SET NULL;
                        CREATE INDEX business_authorization_letter_client_contact_id_idx 
                        ON business_authorization_letter(client_contact_id);
                    END IF;
                END $$;
            """,
            reverse_sql="""
                DROP INDEX IF EXISTS business_authorization_letter_client_contact_id_idx;
                ALTER TABLE business_authorization_letter 
                DROP CONSTRAINT IF EXISTS business_authorization_letter_client_contact_id_fk;
                ALTER TABLE business_authorization_letter 
                DROP COLUMN IF EXISTS client_contact_id;
            """
        ),
        # Add client field
        migrations.RunSQL(
            sql="""
                DO $$ 
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name='business_authorization_letter' AND column_name='client_id'
                    ) THEN
                        ALTER TABLE business_authorization_letter 
                        ADD COLUMN client_id BIGINT NULL;
                        ALTER TABLE business_authorization_letter 
                        ADD CONSTRAINT business_authorization_letter_client_id_fk 
                        FOREIGN KEY (client_id) REFERENCES customer_client(id) ON DELETE SET NULL;
                        CREATE INDEX business_authorization_letter_client_id_idx 
                        ON business_authorization_letter(client_id);
                    END IF;
                END $$;
            """,
            reverse_sql="""
                DROP INDEX IF EXISTS business_authorization_letter_client_id_idx;
                ALTER TABLE business_authorization_letter 
                DROP CONSTRAINT IF EXISTS business_authorization_letter_client_id_fk;
                ALTER TABLE business_authorization_letter 
                DROP COLUMN IF EXISTS client_id;
            """
        ),
        # Add business_manager field
        migrations.RunSQL(
            sql="""
                DO $$ 
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name='business_authorization_letter' AND column_name='business_manager_id'
                    ) THEN
                        ALTER TABLE business_authorization_letter 
                        ADD COLUMN business_manager_id BIGINT NULL;
                        ALTER TABLE business_authorization_letter 
                        ADD CONSTRAINT business_authorization_letter_business_manager_id_fk 
                        FOREIGN KEY (business_manager_id) REFERENCES system_user(id) ON DELETE RESTRICT;
                        CREATE INDEX business_authorization_letter_business_manager_id_idx 
                        ON business_authorization_letter(business_manager_id);
                    END IF;
                END $$;
            """,
            reverse_sql="""
                DROP INDEX IF EXISTS business_authorization_letter_business_manager_id_idx;
                ALTER TABLE business_authorization_letter 
                DROP CONSTRAINT IF EXISTS business_authorization_letter_business_manager_id_fk;
                ALTER TABLE business_authorization_letter 
                DROP COLUMN IF EXISTS business_manager_id;
            """
        ),
    ]

