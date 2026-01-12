# Generated migration for B3-1: Add pending_approval status to StrategicGoal

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('plan_management', '0009_plan_company_plan_org_department_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='strategicgoal',
            name='status',
            field=models.CharField(
                choices=[
                    ('draft', '制定中'),
                    ('pending_approval', '审批中'),
                    ('published', '已发布'),
                    ('in_progress', '执行中'),
                    ('completed', '已完成'),
                    ('cancelled', '已取消'),
                ],
                default='draft',
                max_length=20,
                verbose_name='目标状态'
            ),
        ),
    ]

