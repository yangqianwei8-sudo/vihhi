# Generated migration for adding opportunity_type and service_type fields

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('customer_management', '0021_add_location_fields_to_customer_relationship'),
        ('production_management', '0001_initial'),
        ('permission_management', '0001_initial'),  # 添加permission_management依赖，解决system_management.Role的依赖问题
        ('system_management', '0001_initial'),  # 添加system_management依赖，确保Role模型已加载
    ]

    operations = [
        migrations.AddField(
            model_name='businessopportunity',
            name='opportunity_type',
            field=models.CharField(blank=True, choices=[('project_cooperation', '项目合作'), ('centralized_procurement', '集中采购')], max_length=30, verbose_name='商机类型'),
        ),
        migrations.AddField(
            model_name='businessopportunity',
            name='service_type',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='opportunities', to='production_management.servicetype', verbose_name='服务类型'),
        ),
    ]

