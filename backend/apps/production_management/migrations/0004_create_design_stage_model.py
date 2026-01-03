# Generated migration for creating DesignStage model and migrating data

from django.db import migrations, models
import django.db.models.deletion


def create_design_stages(apps, schema_editor):
    """初始化图纸阶段数据"""
    DesignStage = apps.get_model('production_management', 'DesignStage')
    
    # 根据 Project.DESIGN_STAGES 常量定义的图纸阶段选项
    design_stages_data = [
        ('preliminary_scheme', '初步方案', 1),
        ('detailed_scheme', '详细方案', 2),
        ('preliminary_design', '初步设计', 3),
        ('extended_preliminary_design', '扩初设计', 4),
        ('construction_drawing_design', '施工图设计', 5),
        ('construction_drawing_review', '施工图审查', 6),
        ('construction_phase', '施工阶段', 7),
        ('special_design', '专项设计', 8),
        # 保留旧选项以兼容历史数据
        ('construction_drawing_unreviewed', '施工图（未审图）', 9),
        ('construction_drawing_reviewed', '施工图（已审图）', 10),
        ('extended_preliminary', '扩初阶段', 11),
        ('detailed_planning', '详规阶段', 12),
    ]
    
    for code, name, order in design_stages_data:
        DesignStage.objects.update_or_create(
            code=code,
            defaults={
                'name': name,
                'order': order,
                'is_active': True,
            }
        )


def migrate_design_stage_data(apps, schema_editor):
    """将 Project 中的 design_stage 字符串值迁移到外键"""
    Project = apps.get_model('production_management', 'Project')
    DesignStage = apps.get_model('production_management', 'DesignStage')
    
    # 创建映射字典
    code_to_design_stage = {}
    for ds in DesignStage.objects.all():
        code_to_design_stage[ds.code] = ds.id
    
    # 使用原始 SQL 查询来获取 design_stage 的字符串值
    from django.db import connection
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT id, design_stage 
            FROM production_management_project 
            WHERE design_stage IS NOT NULL AND design_stage != ''
        """)
        rows = cursor.fetchall()
        
        for project_id, design_stage_code in rows:
            if design_stage_code and design_stage_code in code_to_design_stage:
                ds_id = code_to_design_stage[design_stage_code]
                cursor.execute("""
                    UPDATE production_management_project 
                    SET design_stage_id = %s 
                    WHERE id = %s
                """, [ds_id, project_id])


def reverse_migrate_design_stage_data(apps, schema_editor):
    """回滚：将外键值转换回字符串（如果需要）"""
    # 这个操作比较复杂，通常不需要实现
    pass


def reverse_create_design_stages(apps, schema_editor):
    """回滚：删除所有图纸阶段数据"""
    DesignStage = apps.get_model('production_management', 'DesignStage')
    DesignStage.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('production_management', '0003_update_design_stages'),
    ]

    operations = [
        migrations.CreateModel(
            name='DesignStage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=50, unique=True, verbose_name='阶段编码')),
                ('name', models.CharField(max_length=100, verbose_name='阶段名称')),
                ('order', models.PositiveIntegerField(default=0, verbose_name='排序')),
                ('is_active', models.BooleanField(default=True, verbose_name='是否启用')),
                ('description', models.TextField(blank=True, verbose_name='阶段描述')),
            ],
            options={
                'verbose_name': '图纸阶段',
                'verbose_name_plural': '图纸阶段',
                'db_table': 'production_management_design_stage',
                'ordering': ['order', 'id'],
            },
        ),
        migrations.RunPython(create_design_stages, reverse_create_design_stages),
        # 先将 design_stage 字段改为可空的外键（临时字段）
        migrations.AddField(
            model_name='project',
            name='design_stage_new',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='projects_new',
                to='production_management.designstage',
                verbose_name='图纸阶段（新）',
            ),
        ),
        # 迁移数据
        migrations.RunPython(migrate_design_stage_data, reverse_migrate_design_stage_data),
        # 删除旧字段
        migrations.RemoveField(
            model_name='project',
            name='design_stage',
        ),
        # 重命名新字段
        migrations.RenameField(
            model_name='project',
            old_name='design_stage_new',
            new_name='design_stage',
        ),
        # 更新字段属性
        migrations.AlterField(
            model_name='project',
            name='design_stage',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='projects',
                to='production_management.designstage',
                verbose_name='图纸阶段',
                db_column='design_stage',
            ),
        ),
    ]

