# Generated migration for updating BusinessOpportunity.drawing_stage to ForeignKey

from django.db import migrations, models
import django.db.models.deletion


def migrate_drawing_stage_data(apps, schema_editor):
    """将 BusinessOpportunity 中的 drawing_stage 字符串值迁移到外键"""
    BusinessOpportunity = apps.get_model('customer_management', 'BusinessOpportunity')
    DesignStage = apps.get_model('production_management', 'DesignStage')
    
    # 创建映射字典（通过编码匹配）
    code_to_design_stage = {}
    for ds in DesignStage.objects.all():
        code_to_design_stage[ds.code] = ds.id
    
    # 使用原始 SQL 查询来获取 drawing_stage 的字符串值
    from django.db import connection
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT id, drawing_stage 
            FROM business_opportunity 
            WHERE drawing_stage IS NOT NULL AND drawing_stage != ''
        """)
        rows = cursor.fetchall()
        
        for opportunity_id, drawing_stage_code in rows:
            if drawing_stage_code and drawing_stage_code in code_to_design_stage:
                ds_id = code_to_design_stage[drawing_stage_code]
                cursor.execute("""
                    UPDATE business_opportunity 
                    SET drawing_stage_id = %s 
                    WHERE id = %s
                """, [ds_id, opportunity_id])
            else:
                # 尝试通过名称匹配
                design_stage_obj = DesignStage.objects.filter(name=drawing_stage_code).first()
                if design_stage_obj:
                    cursor.execute("""
                        UPDATE business_opportunity 
                        SET drawing_stage_id = %s 
                        WHERE id = %s
                    """, [design_stage_obj.id, opportunity_id])


def reverse_migrate_drawing_stage_data(apps, schema_editor):
    """回滚：将外键值转换回字符串（如果需要）"""
    # 这个操作比较复杂，通常不需要实现
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('customer_management', '0022_add_opportunity_type_and_service_type'),
        ('production_management', '0004_create_design_stage_model'),
    ]

    operations = [
        # 先将 drawing_stage 字段改为可空的外键（临时字段）
        migrations.AddField(
            model_name='businessopportunity',
            name='drawing_stage_new',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='opportunities_new',
                to='production_management.designstage',
                verbose_name='图纸阶段（新）',
            ),
        ),
        # 迁移数据
        migrations.RunPython(migrate_drawing_stage_data, reverse_migrate_drawing_stage_data),
        # 删除旧字段
        migrations.RemoveField(
            model_name='businessopportunity',
            name='drawing_stage',
        ),
        # 重命名新字段
        migrations.RenameField(
            model_name='businessopportunity',
            old_name='drawing_stage_new',
            new_name='drawing_stage',
        ),
        # 更新字段属性
        migrations.AlterField(
            model_name='businessopportunity',
            name='drawing_stage',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='opportunities',
                to='production_management.designstage',
                verbose_name='图纸阶段',
                db_column='drawing_stage',
            ),
        ),
    ]

