# Generated migration for changing DishonestyExecutionRecord to ExecutionRecord

from django.db import migrations, models
import django.utils.timezone
from django.db.models import Sum
from decimal import Decimal


def migrate_dishonesty_to_execution_records(apps, schema_editor):
    """
    将DishonestyExecutionRecord数据迁移到ExecutionRecord
    注意：由于字段结构不同，只迁移可以映射的字段
    """
    DishonestyExecutionRecord = apps.get_model('customer_management', 'DishonestyExecutionRecord')
    ExecutionRecord = apps.get_model('customer_management', 'ExecutionRecord')
    Client = apps.get_model('customer_management', 'Client')
    
    # 迁移记录
    migrated_count = 0
    for old_record in DishonestyExecutionRecord.objects.all():
        # 尝试从execution_target中提取金额（如果格式是"XX万元"或数字）
        execution_amount = Decimal('0')
        if old_record.execution_target:
            import re
            # 尝试提取数字
            numbers = re.findall(r'\d+\.?\d*', old_record.execution_target)
            if numbers:
                try:
                    amount = float(numbers[0])
                    # 如果包含"万"，乘以10000
                    if '万' in old_record.execution_target:
                        amount = amount * 10000
                    execution_amount = Decimal(str(amount))
                except (ValueError, TypeError):
                    pass
        
        ExecutionRecord.objects.create(
            client=old_record.client,
            case_number=old_record.case_number or '',
            execution_status='unknown',  # 默认状态，因为旧数据没有这个字段
            execution_court=old_record.execution_court or '',
            filing_date=old_record.filing_date,
            execution_amount=execution_amount,
            source=old_record.source,
            created_time=old_record.created_time,
            updated_time=old_record.updated_time,
        )
        migrated_count += 1
    
    # 更新客户的总执行金额
    for client in Client.objects.all():
        total = ExecutionRecord.objects.filter(client=client).aggregate(
            total=Sum('execution_amount')
        )['total'] or Decimal('0')
        client.total_execution_amount = total
        client.save(update_fields=['total_execution_amount'])
    
    print(f'✓ 已迁移 {migrated_count} 条记录到 ExecutionRecord')


def reverse_migration(apps, schema_editor):
    """
    反向迁移：将ExecutionRecord数据迁移回DishonestyExecutionRecord
    """
    ExecutionRecord = apps.get_model('customer_management', 'ExecutionRecord')
    DishonestyExecutionRecord = apps.get_model('customer_management', 'DishonestyExecutionRecord')
    
    migrated_count = 0
    for new_record in ExecutionRecord.objects.all():
        # 将执行金额转换为执行标的格式
        execution_target = ''
        if new_record.execution_amount and new_record.execution_amount > 0:
            if new_record.execution_amount >= 10000:
                execution_target = f'{new_record.execution_amount / 10000}万元'
            else:
                execution_target = f'{new_record.execution_amount}元'
        
        DishonestyExecutionRecord.objects.create(
            client=new_record.client,
            case_number=new_record.case_number or '',
            execution_target=execution_target,
            execution_court=new_record.execution_court or '',
            filing_date=new_record.filing_date,
            source=new_record.source,
            created_time=new_record.created_time,
            updated_time=new_record.updated_time,
        )
        migrated_count += 1
    
    print(f'✓ 已反向迁移 {migrated_count} 条记录到 DishonestyExecutionRecord')


class Migration(migrations.Migration):

    dependencies = [
        ('customer_management', '0019_customerrelationshipcollaboration_and_more'),
    ]

    operations = [
        # 1. 在Client模型中添加total_execution_amount字段
        migrations.AddField(
            model_name='client',
            name='total_execution_amount',
            field=models.DecimalField(decimal_places=2, default=0, help_text='所有被执行记录的执行金额总和', max_digits=12, verbose_name='执行总金额'),
        ),
        
        # 2. 创建新的ExecutionRecord模型
        migrations.CreateModel(
            name='ExecutionRecord',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('case_number', models.CharField(blank=True, max_length=200, verbose_name='案号')),
                ('execution_status', models.CharField(choices=[('pending', '待执行'), ('executing', '执行中'), ('completed', '已执行'), ('terminated', '已终止'), ('unknown', '未知')], default='unknown', max_length=50, verbose_name='执行状态')),
                ('execution_court', models.CharField(blank=True, max_length=200, verbose_name='执行法院')),
                ('filing_date', models.DateField(blank=True, null=True, verbose_name='立案日期')),
                ('execution_amount', models.DecimalField(decimal_places=2, default=0, max_digits=12, verbose_name='执行金额')),
                ('source', models.CharField(choices=[('qixinbao', '启信宝API'), ('manual', '手动录入')], default='qixinbao', max_length=50, verbose_name='数据来源')),
                ('created_time', models.DateTimeField(default=django.utils.timezone.now, verbose_name='创建时间')),
                ('updated_time', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('client', models.ForeignKey(on_delete=models.CASCADE, related_name='execution_records', to='customer_management.client', verbose_name='客户')),
            ],
            options={
                'verbose_name': '被执行记录',
                'verbose_name_plural': '被执行记录',
                'db_table': 'customer_execution_record',
                'ordering': ['-filing_date', '-created_time'],
            },
        ),
        
        # 3. 添加索引
        migrations.AddIndex(
            model_name='executionrecord',
            index=models.Index(fields=['client', '-filing_date'], name='customer_ex_client__idx'),
        ),
        migrations.AddIndex(
            model_name='executionrecord',
            index=models.Index(fields=['case_number'], name='customer_ex_case_nu_idx'),
        ),
        
        # 4. 迁移数据（如果有旧数据）
        migrations.RunPython(
            migrate_dishonesty_to_execution_records,
            reverse_migration,
        ),
        
        # 5. 删除旧的DishonestyExecutionRecord模型
        migrations.DeleteModel(
            name='DishonestyExecutionRecord',
        ),
    ]

