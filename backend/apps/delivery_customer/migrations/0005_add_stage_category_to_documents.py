# Generated manually for adding stage and file_category fields to IncomingDocument and OutgoingDocument

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('delivery_customer', '0003_alter_deliveryrecord_project_and_more'),  # 确保 IncomingDocument 和 OutgoingDocument 已创建
        ('delivery_customer', '0004_filecategory_filetemplate'),
    ]

    operations = [
        migrations.AddField(
            model_name='incomingdocument',
            name='stage',
            field=models.CharField(
                blank=True,
                choices=[
                    ('conversion', '转化阶段'),
                    ('contract', '合同阶段'),
                    ('production', '生产阶段'),
                    ('settlement', '结算阶段'),
                    ('payment', '回款阶段'),
                    ('after_sales', '售后阶段'),
                    ('litigation', '诉讼阶段'),
                ],
                db_index=True,
                help_text='文件所属阶段',
                max_length=20,
                null=True,
                verbose_name='阶段',
            ),
        ),
        migrations.AddField(
            model_name='incomingdocument',
            name='file_category',
            field=models.ForeignKey(
                blank=True,
                db_constraint=True,
                help_text='关联的文件分类',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='incoming_documents',
                to='delivery_customer.filecategory',
                verbose_name='文件分类',
            ),
        ),
        migrations.AddField(
            model_name='outgoingdocument',
            name='stage',
            field=models.CharField(
                blank=True,
                choices=[
                    ('conversion', '转化阶段'),
                    ('contract', '合同阶段'),
                    ('production', '生产阶段'),
                    ('settlement', '结算阶段'),
                    ('payment', '回款阶段'),
                    ('after_sales', '售后阶段'),
                    ('litigation', '诉讼阶段'),
                ],
                db_index=True,
                help_text='文件所属阶段',
                max_length=20,
                null=True,
                verbose_name='阶段',
            ),
        ),
        migrations.AddField(
            model_name='outgoingdocument',
            name='file_category',
            field=models.ForeignKey(
                blank=True,
                db_constraint=True,
                help_text='关联的文件分类',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='outgoing_documents',
                to='delivery_customer.filecategory',
                verbose_name='文件分类',
            ),
        ),
        migrations.AddIndex(
            model_name='incomingdocument',
            index=models.Index(fields=['stage'], name='incoming_do_stage_idx'),
        ),
        migrations.AddIndex(
            model_name='outgoingdocument',
            index=models.Index(fields=['stage'], name='outgoing_do_stage_idx'),
        ),
    ]

