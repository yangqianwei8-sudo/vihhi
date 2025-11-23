# Generated manually to use existing table

from django.db import migrations
from django.conf import settings


class Migration(migrations.Migration):
    """由于表 system_permission_item 已经存在，此迁移仅用于标记"""

    initial = True

    dependencies = [
        ('system_management', '0006_alter_user_user_type'),
    ]

    operations = [
        # 表已经存在，不需要创建
        # 我们使用 RunSQL 的 noop 来标记迁移已完成
        migrations.RunSQL(
            sql=migrations.RunSQL.noop,
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]
