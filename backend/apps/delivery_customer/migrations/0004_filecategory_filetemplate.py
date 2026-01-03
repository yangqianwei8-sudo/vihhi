# Generated manually for FileCategory and FileTemplate models

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('delivery_customer', '0002_rename_delivery_fe_deliver_idx_delivery_fe_deliver_0bd1fe_idx_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='FileCategory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='分类名称')),
                ('code', models.CharField(blank=True, help_text='可选，用于系统识别', max_length=50, verbose_name='分类代码')),
                ('stage', models.CharField(choices=[('conversion', '转化阶段'), ('contract', '合同阶段'), ('production', '生产阶段'), ('settlement', '结算阶段'), ('payment', '回款阶段'), ('after_sales', '售后阶段'), ('litigation', '诉讼阶段')], db_index=True, max_length=20, verbose_name='所属阶段')),
                ('description', models.TextField(blank=True, verbose_name='分类描述')),
                ('sort_order', models.IntegerField(default=0, help_text='数字越小越靠前', verbose_name='排序')),
                ('is_active', models.BooleanField(db_index=True, default=True, verbose_name='是否启用')),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='创建时间')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_file_categories', to=settings.AUTH_USER_MODEL, verbose_name='创建人')),
            ],
            options={
                'verbose_name': '文件分类',
                'verbose_name_plural': '文件分类',
                'db_table': 'file_category',
                'ordering': ['stage', 'sort_order', 'name'],
                'unique_together': {('stage', 'name')},
            },
        ),
        migrations.CreateModel(
            name='FileTemplate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='模板名称')),
                ('code', models.CharField(blank=True, help_text='可选，用于系统识别', max_length=50, verbose_name='模板代码')),
                ('stage', models.CharField(choices=[('conversion', '转化阶段'), ('contract', '合同阶段'), ('production', '生产阶段'), ('settlement', '结算阶段'), ('payment', '回款阶段'), ('after_sales', '售后阶段'), ('litigation', '诉讼阶段')], db_index=True, max_length=20, verbose_name='所属阶段')),
                ('template_file', models.FileField(blank=True, help_text='上传模板文件（Word、Excel、PDF等）', null=True, upload_to='file_templates/%Y/%m/%d/<django.db.models.fields.CharField>/', verbose_name='模板文件')),
                ('description', models.TextField(blank=True, verbose_name='模板描述')),
                ('sort_order', models.IntegerField(default=0, help_text='数字越小越靠前', verbose_name='排序')),
                ('is_active', models.BooleanField(db_index=True, default=True, verbose_name='是否启用')),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='创建时间')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('category', models.ForeignKey(blank=True, help_text='可选，关联到文件分类', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='templates', to='delivery_customer.filecategory', verbose_name='关联分类')),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_file_templates', to=settings.AUTH_USER_MODEL, verbose_name='创建人')),
            ],
            options={
                'verbose_name': '文件模板',
                'verbose_name_plural': '文件模板',
                'db_table': 'file_template',
                'ordering': ['stage', 'sort_order', 'name'],
                'unique_together': {('stage', 'name')},
            },
        ),
        migrations.AddIndex(
            model_name='filecategory',
            index=models.Index(fields=['stage', 'sort_order'], name='file_catego_stage_s_idx'),
        ),
        migrations.AddIndex(
            model_name='filecategory',
            index=models.Index(fields=['stage', 'is_active'], name='file_catego_stage_i_idx'),
        ),
        migrations.AddIndex(
            model_name='filetemplate',
            index=models.Index(fields=['stage', 'sort_order'], name='file_templat_stage_s_idx'),
        ),
        migrations.AddIndex(
            model_name='filetemplate',
            index=models.Index(fields=['stage', 'is_active'], name='file_templat_stage_i_idx'),
        ),
    ]

