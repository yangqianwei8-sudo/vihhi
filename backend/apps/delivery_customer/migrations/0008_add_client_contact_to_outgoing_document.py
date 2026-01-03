# Generated manually for adding client, client_contact and recipient_email fields to OutgoingDocument

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('customer_management', '0001_initial'),  # 确保 Client 和 ClientContact 模型已存在
        ('delivery_customer', '0003_alter_deliveryrecord_project_and_more'),  # 确保0003先应用
        ('delivery_customer', '0007_add_project_to_outgoing_document'),
    ]

    operations = [
        migrations.AddField(
            model_name='outgoingdocument',
            name='client',
            field=models.ForeignKey(
                blank=True,
                db_constraint=True,
                help_text='关联的客户，用于自动填充办公地址',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='outgoing_documents',
                to='customer_management.client',
                verbose_name='关联客户',
            ),
        ),
        migrations.AddField(
            model_name='outgoingdocument',
            name='client_contact',
            field=models.ForeignKey(
                blank=True,
                db_constraint=True,
                help_text='从客户管理-人员有关系管理中获取，用于自动填充联系人、联系电话和联系邮箱',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='outgoing_documents',
                to='customer_management.clientcontact',
                verbose_name='签约主体代表',
            ),
        ),
        migrations.AddField(
            model_name='outgoingdocument',
            name='recipient_email',
            field=models.EmailField(
                blank=True,
                help_text='可从客户联系人中自动填充',
                max_length=255,
                verbose_name='联系邮箱',
            ),
        ),
        migrations.AlterField(
            model_name='outgoingdocument',
            name='recipient_contact',
            field=models.CharField(
                blank=True,
                help_text='签约主体代表姓名，可从客户联系人中自动填充',
                max_length=100,
                verbose_name='联系人',
            ),
        ),
        migrations.AlterField(
            model_name='outgoingdocument',
            name='recipient_phone',
            field=models.CharField(
                blank=True,
                help_text='可从客户联系人中自动填充',
                max_length=20,
                verbose_name='联系电话',
            ),
        ),
        migrations.AlterField(
            model_name='outgoingdocument',
            name='recipient_address',
            field=models.TextField(
                blank=True,
                help_text='办公地址，可从客户信息中自动填充',
                verbose_name='收文地址',
            ),
        ),
    ]

