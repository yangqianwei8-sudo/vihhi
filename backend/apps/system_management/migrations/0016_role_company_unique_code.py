# P0-4: Role 增加 company 外键（NULL=全局角色），code 改为 (company, code) 联合唯一

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('system_management', '0015_department_company_unique_code'),
    ]

    operations = [
        migrations.AddField(
            model_name='role',
            name='company',
            field=models.ForeignKey(
                blank=True,
                help_text='P0-4: 为空表示全局角色，非空表示公司专属角色',
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='roles',
                to='system_management.ourcompany',
                verbose_name='所属公司',
            ),
        ),
        migrations.AlterField(
            model_name='role',
            name='code',
            field=models.CharField(max_length=50, verbose_name='角色编码'),
        ),
        migrations.AddConstraint(
            model_name='role',
            constraint=models.UniqueConstraint(
                fields=('company', 'code'),
                name='system_role_company_code_uniq',
            ),
        ),
    ]
