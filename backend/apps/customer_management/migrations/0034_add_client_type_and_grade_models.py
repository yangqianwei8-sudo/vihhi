# Generated migration for ClientType and ClientGrade models

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('customer_management', '0033_fix_responsible_user_from_created_by'),
    ]

    operations = [
        # 创建ClientType模型
        migrations.CreateModel(
            name='ClientType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(help_text='唯一标识，如：developer', max_length=50, unique=True, verbose_name='类型代码')),
                ('name', models.CharField(help_text='显示名称，如：开发商', max_length=100, verbose_name='类型名称')),
                ('display_order', models.IntegerField(default=0, help_text='数字越小越靠前', verbose_name='显示顺序')),
                ('is_active', models.BooleanField(default=True, verbose_name='是否启用')),
                ('description', models.TextField(blank=True, verbose_name='描述')),
                ('created_time', models.DateTimeField(default=django.utils.timezone.now, verbose_name='创建时间')),
                ('updated_time', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
            ],
            options={
                'verbose_name': '客户类型',
                'verbose_name_plural': '客户类型',
                'db_table': 'customer_client_type',
                'ordering': ['display_order', 'name'],
            },
        ),
        # 创建ClientGrade模型
        migrations.CreateModel(
            name='ClientGrade',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(help_text='唯一标识，如：strategic', max_length=50, unique=True, verbose_name='分级代码')),
                ('name', models.CharField(help_text='显示名称，如：战略客户', max_length=100, verbose_name='分级名称')),
                ('display_order', models.IntegerField(default=0, help_text='数字越小越靠前', verbose_name='显示顺序')),
                ('is_active', models.BooleanField(default=True, verbose_name='是否启用')),
                ('description', models.TextField(blank=True, verbose_name='描述')),
                ('created_time', models.DateTimeField(default=django.utils.timezone.now, verbose_name='创建时间')),
                ('updated_time', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
            ],
            options={
                'verbose_name': '客户分级',
                'verbose_name_plural': '客户分级',
                'db_table': 'customer_client_grade',
                'ordering': ['display_order', 'name'],
            },
        ),
        # 添加索引
        migrations.AddIndex(
            model_name='clienttype',
            index=models.Index(fields=['code'], name='customer_cl_type_code_idx'),
        ),
        migrations.AddIndex(
            model_name='clienttype',
            index=models.Index(fields=['is_active'], name='customer_cl_type_active_idx'),
        ),
        migrations.AddIndex(
            model_name='clientgrade',
            index=models.Index(fields=['code'], name='customer_cl_grade_code_idx'),
        ),
        migrations.AddIndex(
            model_name='clientgrade',
            index=models.Index(fields=['is_active'], name='customer_cl_grade_active_idx'),
        ),
        # 修改Client模型的client_type和grade字段为ForeignKey
        migrations.AlterField(
            model_name='client',
            name='client_type',
            field=models.ForeignKey(
                blank=True,
                help_text='客户类型',
                null=True,
                on_delete=models.SET_NULL,
                related_name='clients',
                to='customer_management.clienttype',
                verbose_name='客户类型'
            ),
        ),
        migrations.AlterField(
            model_name='client',
            name='grade',
            field=models.ForeignKey(
                blank=True,
                help_text='用于商机管理的客户分级',
                null=True,
                on_delete=models.SET_NULL,
                related_name='clients',
                to='customer_management.clientgrade',
                verbose_name='客户分级'
            ),
        ),
    ]

