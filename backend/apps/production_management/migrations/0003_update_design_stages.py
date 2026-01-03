# Generated migration for updating design_stage choices

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('production_management', '0002_create_business_type_and_seed_data'),
    ]

    operations = [
        migrations.AlterField(
            model_name='project',
            name='design_stage',
            field=models.CharField(
                blank=True,
                choices=[
                    ('preliminary_scheme', '初步方案'),
                    ('detailed_scheme', '详细方案'),
                    ('preliminary_design', '初步设计'),
                    ('extended_preliminary_design', '扩初设计'),
                    ('construction_drawing_design', '施工图设计'),
                    ('construction_drawing_review', '施工图审查'),
                    ('construction_phase', '施工阶段'),
                    ('special_design', '专项设计'),
                    # 保留旧选项以兼容历史数据
                    ('construction_drawing_unreviewed', '施工图（未审图）'),
                    ('construction_drawing_reviewed', '施工图（已审图）'),
                    ('extended_preliminary', '扩初阶段'),
                    ('detailed_planning', '详规阶段'),
                ],
                max_length=50,
                null=True,
                verbose_name='图纸阶段'
            ),
        ),
    ]

