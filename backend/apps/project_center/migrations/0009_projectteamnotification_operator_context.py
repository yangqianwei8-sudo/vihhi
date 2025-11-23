from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('system_management', '0001_initial'),
        ('project_center', '0008_projectteamnotification'),
    ]

    operations = [
        migrations.AddField(
            model_name='projectteamnotification',
            name='context',
            field=models.JSONField(blank=True, default=dict, verbose_name='上下文信息'),
        ),
        migrations.AddField(
            model_name='projectteamnotification',
            name='operator',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='team_notifications_sent', to='system_management.user', verbose_name='操作人'),
        ),
    ]

