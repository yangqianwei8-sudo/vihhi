from django.db import migrations, models


def set_default_notification_preferences(apps, schema_editor):
    User = apps.get_model("system_management", "User")
    for user in User.objects.all():
        if not user.notification_preferences:
            user.notification_preferences = {
                "inbox": True,
                "email": False,
                "wecom": False,
            }
            user.save(update_fields=["notification_preferences"])


class Migration(migrations.Migration):

    dependencies = [
        ("system_management", "0004_remove_registrationrequest_company_name_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="notification_preferences",
            field=models.JSONField(
                blank=True,
                default=dict,
                verbose_name="通知偏好",
            ),
        ),
        migrations.RunPython(
            set_default_notification_preferences,
            migrations.RunPython.noop,
        ),
    ]


