# Generated manually for adding project field to OutgoingDocument

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('production_management', '0001_initial'),  # 确保 Project 模型已存在
        ('delivery_customer', '0006_add_delivery_methods_to_outgoing_document'),
    ]

    operations = [
        migrations.AddField(
            model_name='outgoingdocument',
            name='project',
            field=models.ForeignKey(
                blank=True,
                db_constraint=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='outgoing_documents',
                to='production_management.project',
                verbose_name='关联项目',
            ),
        ),
    ]

