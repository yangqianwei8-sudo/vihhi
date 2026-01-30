# Generated manually for document_management migration
# These models were migrated from delivery_customer app

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('production_management', '0001_initial'),
        ('customer_management', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # These tables already exist in the database from delivery_customer app
        # We use RunSQL to ensure they exist, but don't create them again
        migrations.RunSQL(
            sql="SELECT 1",  # No-op SQL
            reverse_sql="SELECT 1",
        ),
    ]
