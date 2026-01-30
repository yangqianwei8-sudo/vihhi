# Generated manually

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('administrative_management', '0009_loanapplication'),
    ]

    operations = [
        # 添加借款日期字段
        migrations.AddField(
            model_name='loanapplication',
            name='loan_date',
            field=models.DateField(default=django.utils.timezone.now, verbose_name='借款日期'),
        ),
        # 添加借条附件字段
        migrations.AddField(
            model_name='loanapplication',
            name='iou_file',
            field=models.FileField(blank=True, null=True, upload_to='loan_applications/iou/', verbose_name='手写借条'),
        ),
        # 注意：loan_type 的 choices 更新（添加备用金）不需要数据库迁移，因为这只是 Python 级别的选择
        # 数据库中的 CharField 已经可以存储 'reserve_fund' 值
    ]
