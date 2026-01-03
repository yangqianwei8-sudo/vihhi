# Generated manually for ContactColleague model

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('customer_management', '0040_add_school_model'),
    ]

    operations = [
        migrations.CreateModel(
            name='ContactColleague',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('department', models.CharField(blank=True, max_length=100, verbose_name='部门')),
                ('name', models.CharField(max_length=100, verbose_name='姓名')),
                ('phone', models.CharField(blank=True, max_length=20, verbose_name='电话')),
                ('created_time', models.DateTimeField(default=django.utils.timezone.now, verbose_name='创建时间')),
                ('updated_time', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('career', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='colleagues', to='customer_management.contactcareer', verbose_name='职业信息')),
            ],
            options={
                'verbose_name': '联系人同事关系人员',
                'verbose_name_plural': '联系人同事关系人员',
                'db_table': 'customer_contact_colleague',
                'ordering': ['created_time'],
            },
        ),
        migrations.AddIndex(
            model_name='contactcolleague',
            index=models.Index(fields=['career'], name='customer_co_career_idx'),
        ),
    ]

