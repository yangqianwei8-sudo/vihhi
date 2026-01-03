# Generated migration for BusinessType model and initial data

from django.db import migrations, models
import django.db.models.deletion


def seed_business_types(apps, schema_editor):
    """初始化项目业态选项"""
    BusinessType = apps.get_model('production_management', 'BusinessType')
    
    # 根据 Project.BUSINESS_TYPES 常量定义的项目业态选项
    business_types_data = [
        ('residential', '住宅', 1),
        ('complex', '综合体', 2),
        ('commercial', '商业', 3),
        ('office', '写字楼', 4),
        ('school', '学校', 5),
        ('hospital', '医院', 6),
        ('industrial', '工业厂房', 7),
        ('municipal', '市政', 8),
        ('other', '其他', 9),
    ]
    
    for code, name, order in business_types_data:
        BusinessType.objects.update_or_create(
            code=code,
            defaults={
                'name': name,
                'order': order,
                'is_active': True,
            }
        )


def migrate_business_type_data(apps, schema_editor):
    """将 Project 中的 business_type 字符串值迁移到外键"""
    Project = apps.get_model('production_management', 'Project')
    BusinessType = apps.get_model('production_management', 'BusinessType')
    
    # 创建映射字典
    code_to_business_type = {}
    for bt in BusinessType.objects.all():
        code_to_business_type[bt.code] = bt.id
    
    # 使用原始 SQL 查询来获取 business_type 的字符串值
    from django.db import connection
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT id, business_type 
            FROM production_management_project 
            WHERE business_type IS NOT NULL AND business_type != ''
        """)
        rows = cursor.fetchall()
        
        for project_id, business_type_code in rows:
            if business_type_code and business_type_code in code_to_business_type:
                bt_id = code_to_business_type[business_type_code]
                cursor.execute("""
                    UPDATE production_management_project 
                    SET business_type_new_id = %s 
                    WHERE id = %s
                """, [bt_id, project_id])


def reverse_migrate_business_type_data(apps, schema_editor):
    """回滚：将外键值转换回字符串（如果需要）"""
    # 这个操作比较复杂，通常不需要实现
    pass


def reverse_seed_business_types(apps, schema_editor):
    """回滚：删除所有项目业态数据"""
    BusinessType = apps.get_model('production_management', 'BusinessType')
    BusinessType.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('production_management', '0001_initial'),
    ]

    operations = [
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
                'verbose_name': '项目业态',
                'verbose_name_plural': '项目业态',
                'db_table': 'production_management_business_type',
                'ordering': ['order', 'id'],
            },
        ),
        migrations.RunPython(seed_business_types, reverse_seed_business_types),
        # 先将 business_type 字段改为可空的外键（临时字段）
        migrations.AddField(
            model_name='project',
            name='business_type_new',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='projects_new',
                to='production_management.businesstype',
                verbose_name='项目业态（新）',
            ),
        ),
        # 迁移数据
        migrations.RunPython(migrate_business_type_data, reverse_migrate_business_type_data),
        # 删除旧字段
        migrations.RemoveField(
            model_name='project',
            name='business_type',
        ),
        # 重命名新字段
        migrations.RenameField(
            model_name='project',
            old_name='business_type_new',
            new_name='business_type',
        ),
        # 更新字段属性
        migrations.AlterField(
            model_name='project',
            name='business_type',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='projects',
                to='production_management.businesstype',
                verbose_name='项目业态',
                db_column='business_type',
            ),
        ),
    ]

