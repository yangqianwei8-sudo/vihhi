# Generated manually - models use existing tables from production_management

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.CreateModel(
                    name='ServiceType',
                    fields=[
                        ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                        ('code', models.CharField(max_length=50, unique=True, verbose_name='服务类型编码')),
                        ('name', models.CharField(max_length=100, verbose_name='服务类型名称')),
                        ('order', models.PositiveIntegerField(default=0, verbose_name='排序')),
                    ],
                    options={
                        'db_table': 'production_management_service_type',
                        'verbose_name': '服务类型',
                        'verbose_name_plural': '服务类型',
                        'ordering': ['order', 'id'],
                    },
                ),
                migrations.CreateModel(
                    name='BusinessType',
                    fields=[
                        ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                        ('code', models.CharField(max_length=50, unique=True, verbose_name='业态编码')),
                        ('name', models.CharField(max_length=100, verbose_name='业态名称')),
                        ('order', models.PositiveIntegerField(default=0, verbose_name='排序')),
                        ('is_active', models.BooleanField(default=True, verbose_name='是否启用')),
                        ('description', models.TextField(blank=True, verbose_name='业态描述')),
                    ],
                    options={
                        'db_table': 'production_management_business_type',
                        'verbose_name': '项目业态',
                        'verbose_name_plural': '项目业态',
                        'ordering': ['order', 'id'],
                    },
                ),
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
                        'db_table': 'production_management_design_stage',
                        'verbose_name': '图纸阶段',
                        'verbose_name_plural': '图纸阶段',
                        'ordering': ['order', 'id'],
                    },
                ),
                migrations.CreateModel(
                    name='StructureType',
                    fields=[
                        ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                        ('code', models.CharField(max_length=50, unique=True, verbose_name='结构形式编码')),
                        ('name', models.CharField(max_length=100, verbose_name='结构形式名称')),
                        ('order', models.PositiveIntegerField(default=0, verbose_name='排序')),
                        ('is_active', models.BooleanField(default=True, verbose_name='是否启用')),
                        ('description', models.TextField(blank=True, verbose_name='结构形式描述')),
                    ],
                    options={
                        'db_table': 'production_management_structure_type',
                        'verbose_name': '结构形式',
                        'verbose_name_plural': '结构形式',
                        'ordering': ['order', 'id'],
                    },
                ),
                migrations.CreateModel(
                    name='DesignUnitCategory',
                    fields=[
                        ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                        ('code', models.CharField(max_length=50, unique=True, verbose_name='分类编码')),
                        ('name', models.CharField(max_length=100, verbose_name='分类名称')),
                        ('order', models.PositiveIntegerField(default=0, verbose_name='排序')),
                        ('is_active', models.BooleanField(default=True, verbose_name='是否启用')),
                        ('description', models.TextField(blank=True, verbose_name='分类描述')),
                    ],
                    options={
                        'db_table': 'production_management_design_unit_category',
                        'verbose_name': '设计单位分类',
                        'verbose_name_plural': '设计单位分类',
                        'ordering': ['order', 'id'],
                    },
                ),
                migrations.CreateModel(
                    name='ServiceProfession',
                    fields=[
                        ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                        ('code', models.CharField(max_length=50, verbose_name='服务专业编码')),
                        ('name', models.CharField(max_length=100, verbose_name='服务专业名称')),
                        ('order', models.PositiveIntegerField(default=0, verbose_name='排序')),
                        ('service_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='professions', to='base_data.servicetype', verbose_name='所属服务类型')),
                    ],
                    options={
                        'db_table': 'production_management_service_profession',
                        'verbose_name': '服务专业',
                        'verbose_name_plural': '服务专业',
                        'ordering': ['service_type__order', 'order', 'id'],
                        'unique_together': {('service_type', 'code')},
                    },
                ),
            ],
            database_operations=[],
        ),
    ]
