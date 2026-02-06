# Generated manually: 门禁与审计字段

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('plan_management', '0018_fact_event_milestone_completion'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='factevent',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now, verbose_name='入库时间'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='factevent',
            name='idempotency_key',
            field=models.CharField(blank=True, db_index=True, max_length=255, null=True, verbose_name='幂等键'),
        ),
        migrations.AddField(
            model_name='planoutputmilestonecompletion',
            name='created_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL, verbose_name='创建人'),
        ),
        migrations.AddField(
            model_name='planoutputmilestonecompletion',
            name='created_via',
            field=models.CharField(default='rule_engine', max_length=50, verbose_name='创建途径'),
        ),
        migrations.AddField(
            model_name='planoutputmilestonecompletion',
            name='rule_code',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='命中规则编码'),
        ),
        migrations.AddField(
            model_name='planoutputmilestonecompletion',
            name='rule_snapshot',
            field=models.JSONField(blank=True, default=dict, verbose_name='规则快照'),
        ),
    ]
