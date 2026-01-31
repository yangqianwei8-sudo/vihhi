# 将 ServiceType, ServiceProfession, BusinessType, DesignStage, StructureType, DesignUnitCategory
# 从 production_management 迁移至 base_data，表结构不变（base_data 使用 db_table 指向原表）

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('base_data', '0001_initial'),
        ('opportunity_management', '0004_alter_fks_to_base_data'),
        ('production_management', '0042_alter_businesscontract_opportunity'),
    ]

    operations = [
        # 1. 先将 Project、ProjectTeam 等模型的 FK 指向 base_data
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AlterField(
                    model_name='project',
                    name='service_type',
                    field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='projects', to='base_data.servicetype', verbose_name='服务类型'),
                ),
                migrations.AlterField(
                    model_name='project',
                    name='business_type',
                    field=models.ForeignKey(blank=True, db_column='business_type', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='projects', to='base_data.businesstype', verbose_name='项目业态'),
                ),
                migrations.AlterField(
                    model_name='project',
                    name='design_stage',
                    field=models.ForeignKey(blank=True, db_column='design_stage', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='projects', to='base_data.designstage', verbose_name='图纸阶段'),
                ),
                migrations.AlterField(
                    model_name='project',
                    name='service_professions',
                    field=models.ManyToManyField(blank=True, related_name='projects', to='base_data.serviceprofession', verbose_name='服务专业'),
                ),
                migrations.AlterField(
                    model_name='projectteam',
                    name='service_profession',
                    field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='base_data.serviceprofession', verbose_name='所属专业'),
                ),
                migrations.AlterField(
                    model_name='projectteamchangelog',
                    name='service_profession',
                    field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='base_data.serviceprofession', verbose_name='所属专业'),
                ),
            ],
            database_operations=[],
        ),
        # 2. 再从 production_management 状态中移除基础数据模型
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.DeleteModel(name='DesignUnitCategory'),
                migrations.DeleteModel(name='StructureType'),
                migrations.DeleteModel(name='ServiceProfession'),
                migrations.DeleteModel(name='DesignStage'),
                migrations.DeleteModel(name='BusinessType'),
                migrations.DeleteModel(name='ServiceType'),
            ],
            database_operations=[],
        ),
    ]
