from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("plan_management", "0012_todotask_add_closure_audit_fields"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.AddField(
                    model_name="planadjustment",
                    name="adjustment_type",
                    field=models.CharField(
                        choices=[
                            ("time", "时间调整"),
                            ("content", "内容调整"),
                            ("responsible", "负责人调整"),
                            ("plan_objective", "计划目标调整"),
                            ("collaboration", "协作人员调整"),
                            ("acceptance_criteria", "验收标准调整"),
                        ],
                        default="content",
                        max_length=20,
                        verbose_name="调整类型",
                    ),
                ),
                migrations.AddField(
                    model_name="planadjustment",
                    name="new_acceptance_criteria",
                    field=models.TextField(blank=True, max_length=1000, verbose_name="新验收标准"),
                ),
                migrations.AddField(
                    model_name="planadjustment",
                    name="new_participants",
                    field=models.ManyToManyField(
                        blank=True,
                        related_name="adjusted_plan_participants",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="新协作人员",
                    ),
                ),
                migrations.AddField(
                    model_name="planadjustment",
                    name="new_plan_objective",
                    field=models.TextField(blank=True, max_length=1000, verbose_name="新计划目标"),
                ),
                migrations.AddField(
                    model_name="planadjustment",
                    name="new_responsible_person",
                    field=models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="adjusted_plans",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="新负责人",
                    ),
                ),
                migrations.AddField(
                    model_name="planadjustment",
                    name="new_start_time",
                    field=models.DateTimeField(blank=True, null=True, verbose_name="新开始时间"),
                ),
            ],
        ),
    ]

