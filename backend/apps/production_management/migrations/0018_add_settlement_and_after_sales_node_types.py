# Generated migration for SettlementNodeType and AfterSalesNodeType

from django.db import migrations, models


def create_initial_data(apps, schema_editor):
    """初始化结算节点类型和售后节点类型数据"""
    SettlementNodeType = apps.get_model('production_management', 'SettlementNodeType')
    AfterSalesNodeType = apps.get_model('production_management', 'AfterSalesNodeType')
    
    # 创建结算节点类型
    settlement_nodes = [
        {'code': 'submit_settlement_application', 'name': '报送结算申请', 'order': 1},
        {'code': 'settlement_preliminary_review', 'name': '结算初审', 'order': 2},
        {'code': 'preliminary_objection_list', 'name': '初审异议清单', 'order': 3},
        {'code': 'settlement_finalization', 'name': '结算定案', 'order': 4},
    ]
    
    for node_data in settlement_nodes:
        SettlementNodeType.objects.get_or_create(
            code=node_data['code'],
            defaults={
                'name': node_data['name'],
                'order': node_data['order'],
                'is_active': True,
            }
        )
    
    # 创建售后节点类型
    after_sales_nodes = [
        {'code': 'official_drawing', 'name': '正式出图', 'order': 1},
        {'code': 'foundation_completed', 'name': '基础施工完成', 'order': 2},
        {'code': 'basement_completed', 'name': '地下室施工完成', 'order': 3},
        {'code': 'main_structure_completed', 'name': '主体封顶完成', 'order': 4},
        {'code': 'presale_permit_obtained', 'name': '取得预售证', 'order': 5},
        {'code': 'predicted_area_obtained', 'name': '取得预测面积', 'order': 6},
        {'code': 'completion_acceptance_completed', 'name': '竣工验收完成', 'order': 7},
        {'code': 'completion_acceptance_filed', 'name': '竣工验收备案', 'order': 8},
    ]
    
    for node_data in after_sales_nodes:
        AfterSalesNodeType.objects.get_or_create(
            code=node_data['code'],
            defaults={
                'name': node_data['name'],
                'order': node_data['order'],
                'is_active': True,
            }
        )


class Migration(migrations.Migration):

    dependencies = [
        ('production_management', '0017_remove_result_file_model'),
    ]

    operations = [
        migrations.CreateModel(
            name='SettlementNodeType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=50, unique=True, verbose_name='节点编码')),
                ('name', models.CharField(max_length=100, verbose_name='节点名称')),
                ('order', models.PositiveIntegerField(default=0, verbose_name='排序')),
                ('is_active', models.BooleanField(default=True, verbose_name='是否启用')),
                ('description', models.TextField(blank=True, verbose_name='节点描述')),
            ],
            options={
                'verbose_name': '结算节点类型',
                'verbose_name_plural': '结算节点类型',
                'db_table': 'production_management_settlement_node_type',
                'ordering': ['order', 'id'],
            },
        ),
        migrations.CreateModel(
            name='AfterSalesNodeType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=50, unique=True, verbose_name='节点编码')),
                ('name', models.CharField(max_length=100, verbose_name='节点名称')),
                ('order', models.PositiveIntegerField(default=0, verbose_name='排序')),
                ('is_active', models.BooleanField(default=True, verbose_name='是否启用')),
                ('description', models.TextField(blank=True, verbose_name='节点描述')),
            ],
            options={
                'verbose_name': '售后节点类型',
                'verbose_name_plural': '售后节点类型',
                'db_table': 'production_management_after_sales_node_type',
                'ordering': ['order', 'id'],
            },
        ),
        migrations.RunPython(
            code=create_initial_data,
            reverse_code=migrations.RunPython.noop,
        ),
    ]

