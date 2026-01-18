# Generated manually on 2026-01-18

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('customer_management', '0054_add_department_responsible_user_to_visit_plan'),
    ]

    operations = [
        migrations.RunSQL(
            sql="ALTER TABLE customer_lead ADD COLUMN IF NOT EXISTS lead_number VARCHAR(50);",
            reverse_sql="ALTER TABLE customer_lead DROP COLUMN IF EXISTS lead_number;",
        ),
        migrations.RunSQL(
            sql="CREATE UNIQUE INDEX IF NOT EXISTS customer_lead_lead_number_unique ON customer_lead(lead_number) WHERE lead_number IS NOT NULL;",
            reverse_sql="DROP INDEX IF EXISTS customer_lead_lead_number_unique;",
        ),
    ]

