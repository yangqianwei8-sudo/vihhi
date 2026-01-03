# Generated manually

from django.db import migrations, models


def remove_short_name_if_exists(apps, schema_editor):
    """安全删除short_name字段（如果存在）"""
    db_table = 'customer_client'
    with schema_editor.connection.cursor() as cursor:
        # 检查字段是否存在
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = %s AND column_name = 'short_name'
        """, [db_table])
        if cursor.fetchone():
            # 字段存在，删除它
            cursor.execute(f'ALTER TABLE {db_table} DROP COLUMN short_name')


def reverse_remove_short_name(apps, schema_editor):
    """恢复short_name字段"""
    # 如果需要回滚，可以在这里添加恢复逻辑
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('customer_management', '0012_add_quotation_mode_fields'),
    ]

    operations = [
        # 添加从启信宝获取的企业信息字段
        migrations.AddField(
            model_name='client',
            name='legal_representative',
            field=models.CharField(blank=True, help_text='从启信宝API获取', max_length=100, verbose_name='法定代表人'),
        ),
        migrations.AddField(
            model_name='client',
            name='established_date',
            field=models.DateField(blank=True, help_text='从启信宝API获取', null=True, verbose_name='成立日期'),
        ),
        migrations.AddField(
            model_name='client',
            name='registered_capital',
            field=models.DecimalField(blank=True, decimal_places=2, help_text='从启信宝API获取', max_digits=15, null=True, verbose_name='注册资本（万元）'),
        ),
        migrations.AddField(
            model_name='client',
            name='company_phone',
            field=models.CharField(blank=True, help_text='从启信宝API获取', max_length=20, verbose_name='联系电话'),
        ),
        migrations.AddField(
            model_name='client',
            name='company_email',
            field=models.EmailField(blank=True, help_text='从启信宝API获取', max_length=254, verbose_name='邮箱'),
        ),
        migrations.AddField(
            model_name='client',
            name='company_address',
            field=models.CharField(blank=True, help_text='从启信宝API获取', max_length=500, verbose_name='地址'),
        ),
        migrations.AddField(
            model_name='client',
            name='company_industry',
            field=models.CharField(blank=True, help_text='从启信宝API获取', max_length=100, verbose_name='所属行业'),
        ),
        migrations.AddField(
            model_name='client',
            name='company_group',
            field=models.CharField(blank=True, help_text='从启信宝API获取', max_length=200, verbose_name='所属集团'),
        ),
        # 删除客户简称字段（如果存在）
        migrations.RunPython(
            code=remove_short_name_if_exists,
            reverse_code=reverse_remove_short_name,
        ),
    ]
