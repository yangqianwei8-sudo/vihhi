# Generated manually to make contact fields required
# 
# 本次迁移主要更新以下字段：
# 1. ClientContact: birthplace, role, decision_influence 设为必填（移除blank=True）
# 2. ClientContact: relationship_level 默认值改为 'first_contact'
# 3. ContactCareer: company, department, join_date 设为必填（移除blank=True和null=True）

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('customer_management', '0042_add_position_to_contact_colleague'),
    ]

    operations = [
        # ClientContact字段：设为必填并更新默认值
        migrations.AlterField(
            model_name='clientcontact',
            name='birthplace',
            field=models.CharField(max_length=100, verbose_name='籍贯'),
        ),
        migrations.AlterField(
            model_name='clientcontact',
            name='role',
            field=models.CharField(choices=[('contact_person', '对接人'), ('promoter', '推动人'), ('decision_maker', '决策人'), ('introducer', '介绍人')], max_length=20, verbose_name='人员角色'),
        ),
        migrations.AlterField(
            model_name='clientcontact',
            name='decision_influence',
            field=models.CharField(choices=[('high', '高'), ('medium', '中'), ('low', '低')], max_length=10, verbose_name='决策影响力'),
        ),
        migrations.AlterField(
            model_name='clientcontact',
            name='relationship_level',
            field=models.CharField(choices=[('first_contact', '首次沟通'), ('requirement_communication', '需求沟通'), ('cooperation_intention', '合作意向'), ('cooperation_recognition', '合作认可'), ('external_partner', '外部合伙人')], default='first_contact', max_length=30, verbose_name='关系等级'),
        ),
        # ContactCareer字段：设为必填
        migrations.AlterField(
            model_name='contactcareer',
            name='company',
            field=models.CharField(max_length=200, verbose_name='就职公司'),
        ),
        migrations.AlterField(
            model_name='contactcareer',
            name='department',
            field=models.CharField(max_length=100, verbose_name='部门'),
        ),
        migrations.AlterField(
            model_name='contactcareer',
            name='join_date',
            field=models.DateField(verbose_name='入职时间'),
        ),
    ]

