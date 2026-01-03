# Generated manually
# 
# 注意：此迁移由于迁移依赖链问题，字段已通过SQL直接添加
# 字段：customer_contact.tracking_cycle_days
# SQL: ALTER TABLE customer_contact ADD COLUMN tracking_cycle_days INTEGER NULL;
# 
# 如果需要回滚，执行：
# ALTER TABLE customer_contact DROP COLUMN tracking_cycle_days;
# DELETE FROM django_migrations WHERE app = 'customer_management' AND name = '0044_add_tracking_cycle_days';

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('customer_management', '0043_make_contact_fields_required'),
    ]

    operations = [
        migrations.AddField(
            model_name='clientcontact',
            name='tracking_cycle_days',
            field=models.IntegerField(
                blank=True,
                choices=[(7, '每周'), (14, '每2周'), (21, '每3周'), (28, '每月'), (42, '每6周'), (56, '每8周'), (90, '每季度')],
                help_text='建议的拜访跟踪周期，留空则根据角色和关系等级自动计算',
                null=True,
                verbose_name='跟踪周期（天）'
            ),
        ),
    ]

