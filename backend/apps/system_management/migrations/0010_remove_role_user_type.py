# Generated manually to fix database schema mismatch
# The database has a user_type field in system_role table that doesn't exist in the model
# This migration removes the user_type field directly from the database using SQL

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('system_management', '0009_merge_20251208_1445'),
    ]

    operations = [
        # Use RunSQL to directly remove the column from database
        # This is necessary because the field doesn't exist in Django's model state
        migrations.RunSQL(
            sql="ALTER TABLE system_role DROP COLUMN IF EXISTS user_type;",
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]
