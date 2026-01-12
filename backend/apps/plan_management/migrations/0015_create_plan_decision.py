# Generated migration for P1: Create PlanDecision model

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('plan_management', '0014_alter_approvalnotification_event'),
    ]

    operations = [
        migrations.CreateModel(
            name='PlanDecision',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('request_type', models.CharField(choices=[('start', '启动计划'), ('cancel', '取消计划')], max_length=20, verbose_name='请求类型')),
                ('decision', models.CharField(blank=True, choices=[('approve', '通过'), ('reject', '驳回')], max_length=20, null=True, verbose_name='决策结果')),
                ('requested_at', models.DateTimeField(auto_now_add=True, verbose_name='请求时间')),
                ('decided_at', models.DateTimeField(blank=True, null=True, verbose_name='决策时间')),
                ('reason', models.TextField(blank=True, verbose_name='原因说明')),
                ('decided_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='decided_plan_decisions', to=settings.AUTH_USER_MODEL, verbose_name='决策人')),
                ('plan', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='decisions', to='plan_management.plan', verbose_name='计划')),
                ('requested_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='requested_plan_decisions', to=settings.AUTH_USER_MODEL, verbose_name='请求人')),
            ],
            options={
                'verbose_name': '计划决策记录',
                'verbose_name_plural': '计划决策记录',
                'db_table': 'plan_decision',
                'ordering': ['-requested_at'],
            },
        ),
        migrations.AddIndex(
            model_name='plandecision',
            index=models.Index(fields=['plan', '-requested_at'], name='plan_decisi_plan_id_idx'),
        ),
        migrations.AddIndex(
            model_name='plandecision',
            index=models.Index(fields=['request_type', 'decided_at'], name='plan_decisi_request_idx'),
        ),
        migrations.AddConstraint(
            model_name='plandecision',
            constraint=models.UniqueConstraint(condition=models.Q(('decided_at__isnull', True)), fields=('plan', 'request_type'), name='unique_pending_decision_per_plan_request_type'),
        ),
    ]
