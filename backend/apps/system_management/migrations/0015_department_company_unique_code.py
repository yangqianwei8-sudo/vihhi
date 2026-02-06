# P0-3: Department 增加 company 外键，code 改为 (company, code) 联合唯一

from django.db import migrations, models
import django.db.models.deletion


def _noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('system_management', '0014_add_user_company_field'),
    ]

    operations = [
        migrations.AddField(
            model_name='department',
            name='company',
            field=models.ForeignKey(
                blank=True,
                help_text='P0-3: 部门所属公司，用于多公司数据隔离',
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='departments',
                to='system_management.ourcompany',
                verbose_name='所属公司',
            ),
        ),
        migrations.AlterField(
            model_name='department',
            name='code',
            field=models.CharField(max_length=50, verbose_name='部门编码'),
        ),
        migrations.AddConstraint(
            model_name='department',
            constraint=models.UniqueConstraint(
                fields=('company', 'code'),
                name='system_dept_company_code_uniq',
            ),
        ),
    ]
