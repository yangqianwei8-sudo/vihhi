# Generated manually to disable Django default permissions

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('plan_management', '0018_fix_pending_approval_status'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='plan',
            options={
                'verbose_name': '计划',
                'verbose_name_plural': '计划',
                'ordering': ['-created_time'],
                'default_permissions': (),  # 禁用 Django 默认权限生成
            },
        ),
        migrations.AlterModelOptions(
            name='strategicgoal',
            options={
                'verbose_name': '战略目标',
                'verbose_name_plural': '战略目标',
                'ordering': ['-created_time'],
                'default_permissions': (),  # 禁用 Django 默认权限生成
            },
        ),
    ]

