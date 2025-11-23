from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('system_management', '0001_initial'),
        ('project_center', '0007_projectteamchangelog'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProjectTeamNotification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200, verbose_name='标题')),
                ('message', models.TextField(verbose_name='内容')),
                ('category', models.CharField(choices=[('team_change', '团队变更')], default='team_change', max_length=50, verbose_name='通知分类')),
                ('action_url', models.CharField(blank=True, max_length=300, verbose_name='跳转链接')),
                ('is_read', models.BooleanField(default=False, verbose_name='是否已读')),
                ('created_time', models.DateTimeField(default=django.utils.timezone.now, verbose_name='创建时间')),
                ('read_time', models.DateTimeField(blank=True, null=True, verbose_name='读取时间')),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='team_notifications', to='project_center.project', verbose_name='项目')),
                ('recipient', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='team_notifications', to='system_management.user', verbose_name='接收人')),
            ],
            options={
                'verbose_name': '项目团队通知',
                'verbose_name_plural': '项目团队通知',
                'db_table': 'project_center_team_notification',
                'ordering': ['-created_time'],
            },
        ),
    ]

