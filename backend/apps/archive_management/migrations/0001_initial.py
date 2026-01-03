# Generated manually to fix missing table issue

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('production_management', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ArchiveProjectArchive',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('archive_number', models.CharField(db_index=True, max_length=100, unique=True, verbose_name='归档编号')),
                ('archive_reason', models.TextField(blank=True, verbose_name='归档原因')),
                ('archive_description', models.TextField(blank=True, verbose_name='归档说明')),
                ('status', models.CharField(choices=[('pending', '待归档'), ('approving', '归档审批中'), ('archiving', '归档执行中'), ('archived', '已归档'), ('rejected', '归档驳回')], default='pending', max_length=20, verbose_name='归档状态')),
                ('applied_time', models.DateTimeField(default=django.utils.timezone.now, verbose_name='申请时间')),
                ('executed_time', models.DateTimeField(blank=True, null=True, verbose_name='执行时间')),
                ('confirmed_time', models.DateTimeField(blank=True, null=True, verbose_name='确认时间')),
                ('file_list', models.JSONField(blank=True, default=list, verbose_name='归档文件清单')),
                ('created_time', models.DateTimeField(default=django.utils.timezone.now, verbose_name='创建时间')),
                ('updated_time', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('applicant', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='applied_project_archives', to=settings.AUTH_USER_MODEL, verbose_name='归档申请人')),
                ('confirmed_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='confirmed_project_archives', to=settings.AUTH_USER_MODEL, verbose_name='确认人')),
                ('executor', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='executed_project_archives', to=settings.AUTH_USER_MODEL, verbose_name='归档执行人')),
                ('project', models.ForeignKey(db_constraint=True, on_delete=django.db.models.deletion.CASCADE, related_name='archive_records', to='production_management.project', verbose_name='关联项目')),
            ],
            options={
                'verbose_name': '项目归档（档案管理）',
                'verbose_name_plural': '项目归档（档案管理）',
                'db_table': 'archive_project_archive',
                'ordering': ['-created_time'],
            },
        ),
        migrations.AddIndex(
            model_name='archiveprojectarchive',
            index=models.Index(fields=['project', 'status'], name='archive_pro_project_status_idx'),
        ),
        migrations.AddIndex(
            model_name='archiveprojectarchive',
            index=models.Index(fields=['archive_number'], name='archive_pro_archive_idx'),
        ),
        migrations.AddIndex(
            model_name='archiveprojectarchive',
            index=models.Index(fields=['status', '-created_time'], name='archive_pro_status_created_idx'),
        ),
    ]

