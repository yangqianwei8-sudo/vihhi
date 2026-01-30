# Generated manually

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('administrative_management', '0010_add_loan_date_and_iou_file'),
    ]

    operations = [
        migrations.AddField(
            model_name='loanapplication',
            name='pending_repayment_amount',
            field=models.DecimalField(decimal_places=2, default=0, help_text='已提交但未确认的还款金额', max_digits=12, verbose_name='待确认还款金额'),
        ),
        migrations.AddField(
            model_name='loanapplication',
            name='pending_repayment_notes',
            field=models.TextField(blank=True, verbose_name='待确认还款备注'),
        ),
        migrations.AddField(
            model_name='loanapplication',
            name='pending_repayment_time',
            field=models.DateTimeField(blank=True, null=True, verbose_name='还款申请时间'),
        ),
        migrations.AddField(
            model_name='loanapplication',
            name='confirmed_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='confirmed_loan_repayments', to=settings.AUTH_USER_MODEL, verbose_name='确认人'),
        ),
        migrations.AddField(
            model_name='loanapplication',
            name='confirmed_time',
            field=models.DateTimeField(blank=True, null=True, verbose_name='确认时间'),
        ),
    ]
