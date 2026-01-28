from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("plan_management", "0011_planadjustment_adjustment_type_and_more"),
        ("system_management", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="todotask",
            name="completed_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="completed_todo_tasks",
                to="system_management.user",
                verbose_name="完成人",
            ),
        ),
        migrations.AddField(
            model_name="todotask",
            name="cancelled_at",
            field=models.DateTimeField(blank=True, null=True, verbose_name="取消时间"),
        ),
        migrations.AddField(
            model_name="todotask",
            name="cancelled_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="cancelled_todo_tasks",
                to="system_management.user",
                verbose_name="取消人",
            ),
        ),
        migrations.AddField(
            model_name="todotask",
            name="cancel_reason",
            field=models.TextField(blank=True, verbose_name="取消原因"),
        ),
    ]

