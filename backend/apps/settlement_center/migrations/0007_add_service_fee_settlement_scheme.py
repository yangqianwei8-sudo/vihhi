# Generated manually for service fee settlement scheme

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('production_management', '0004_create_design_stage_model'),
        ('settlement_center', '0006_alter_outputvaluerecord_project_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='ServiceFeeSettlementScheme',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='结算方案的名称', max_length=200, verbose_name='方案名称')),
                ('code', models.CharField(blank=True, help_text='可选，用于系统识别', max_length=50, null=True, unique=True, verbose_name='方案代码')),
                ('description', models.TextField(blank=True, verbose_name='方案描述')),
                ('settlement_method', models.CharField(choices=[('fixed_total', '固定总价'), ('fixed_unit', '固定单价'), ('cumulative_commission', '累计提成'), ('segmented_commission', '分段递增提成'), ('jump_point_commission', '跳点提成'), ('combined', '固定价款 + 按实结算')], max_length=30, verbose_name='结算方式')),
                ('fixed_total_price', models.DecimalField(blank=True, decimal_places=2, help_text='方式一：固定总价', max_digits=14, null=True, verbose_name='固定总价')),
                ('fixed_unit_price', models.DecimalField(blank=True, decimal_places=2, help_text='方式一：固定单价（元/平方米）', max_digits=12, null=True, verbose_name='固定单价')),
                ('area_type', models.CharField(blank=True, choices=[('drawing_building_area', '图纸建筑面积'), ('drawing_structure_area', '图纸结构面积'), ('planning_building_area', '报规建筑面积'), ('completion_building_area', '竣工建筑面积'), ('survey_area', '测绘面积')], help_text='方式一：固定单价时使用的面积类型', max_length=30, null=True, verbose_name='面积类型')),
                ('cumulative_rate', models.DecimalField(blank=True, decimal_places=2, help_text='方式二：累计提成的取费系数，例如：10.5 表示 10.5%', max_digits=5, null=True, verbose_name='累计提成系数(%)')),
                ('combined_fixed_method', models.CharField(blank=True, choices=[('fixed_total', '固定总价'), ('fixed_unit', '固定单价')], help_text='方式三：固定部分采用的方式', max_length=20, null=True, verbose_name='组合-固定部分方式')),
                ('combined_fixed_total', models.DecimalField(blank=True, decimal_places=2, help_text='方式三：固定部分为固定总价时的金额', max_digits=14, null=True, verbose_name='组合-固定总价')),
                ('combined_fixed_unit', models.DecimalField(blank=True, decimal_places=2, help_text='方式三：固定部分为固定单价时的单价', max_digits=12, null=True, verbose_name='组合-固定单价')),
                ('combined_fixed_area_type', models.CharField(blank=True, choices=[('drawing_building_area', '图纸建筑面积'), ('drawing_structure_area', '图纸结构面积'), ('planning_building_area', '报规建筑面积'), ('completion_building_area', '竣工建筑面积'), ('survey_area', '测绘面积')], help_text='方式三：固定部分为固定单价时的面积类型', max_length=30, null=True, verbose_name='组合-固定面积类型')),
                ('combined_actual_method', models.CharField(blank=True, choices=[('cumulative_commission', '累计提成'), ('segmented_commission', '分段递增提成'), ('jump_point_commission', '跳点提成')], help_text='方式三：按实结算部分采用的方式', max_length=30, null=True, verbose_name='组合-按实结算方式')),
                ('combined_cumulative_rate', models.DecimalField(blank=True, decimal_places=2, help_text='方式三：按实结算部分为累计提成时的系数', max_digits=5, null=True, verbose_name='组合-累计提成系数(%)')),
                ('combined_deduct_fixed', models.BooleanField(default=False, help_text='方式三：按实结算计算时是否应扣除固定价款部分', verbose_name='组合-按实结算是否扣除固定部分')),
                ('has_cap_fee', models.BooleanField(default=False, verbose_name='是否设置封顶费')),
                ('cap_type', models.CharField(blank=True, choices=[('total_cap', '总价封顶'), ('unit_cap', '单价封顶'), ('no_cap', '不设置封顶')], help_text='总价封顶或单价封顶', max_length=20, null=True, verbose_name='封顶费类型')),
                ('total_cap_amount', models.DecimalField(blank=True, decimal_places=2, help_text='封顶费为总价封顶时的金额', max_digits=14, null=True, verbose_name='总价封顶金额')),
                ('has_minimum_fee', models.BooleanField(default=False, verbose_name='是否设置保底费')),
                ('minimum_fee_amount', models.DecimalField(blank=True, decimal_places=2, help_text='保底费金额', max_digits=14, null=True, verbose_name='保底费金额')),
                ('is_active', models.BooleanField(db_index=True, default=True, verbose_name='是否启用')),
                ('is_default', models.BooleanField(default=False, help_text='设为默认后，创建结算时自动选中', verbose_name='是否默认')),
                ('sort_order', models.IntegerField(default=0, help_text='数字越小越靠前', verbose_name='排序')),
                ('created_time', models.DateTimeField(db_index=True, default=django.utils.timezone.now, verbose_name='创建时间')),
                ('updated_time', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('contract', models.ForeignKey(blank=True, help_text='如果为空，则为全局方案模板', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='service_fee_schemes', to='production_management.businesscontract', verbose_name='关联合同')),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='created_service_fee_schemes', to=settings.AUTH_USER_MODEL, verbose_name='创建人')),
                ('project', models.ForeignKey(blank=True, help_text='可选，用于项目特定的结算方案', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='service_fee_schemes', to='production_management.project', verbose_name='关联项目')),
            ],
            options={
                'verbose_name': '服务费结算方案',
                'verbose_name_plural': '服务费结算方案',
                'db_table': 'settlement_service_fee_scheme',
                'ordering': ['sort_order', '-created_time'],
            },
        ),
        migrations.AddIndex(
            model_name='servicefeesettlementscheme',
            index=models.Index(fields=['contract', 'is_active'], name='settlement__contract_idx'),
        ),
        migrations.AddIndex(
            model_name='servicefeesettlementscheme',
            index=models.Index(fields=['project', 'is_active'], name='settlement__project_idx'),
        ),
        migrations.AddIndex(
            model_name='servicefeesettlementscheme',
            index=models.Index(fields=['settlement_method', 'is_active'], name='settlement__method_idx'),
        ),
        migrations.AddIndex(
            model_name='servicefeesettlementscheme',
            index=models.Index(fields=['is_default', 'is_active'], name='settlement__default_idx'),
        ),
        migrations.CreateModel(
            name='ServiceFeeSegmentedRate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('threshold', models.DecimalField(decimal_places=2, help_text='该分段的上限阈值，例如：500000 表示50万元', max_digits=14, verbose_name='分段阈值')),
                ('rate', models.DecimalField(decimal_places=2, help_text='该分段对应的取费系数，例如：10.5 表示 10.5%', max_digits=5, verbose_name='取费系数(%)')),
                ('description', models.TextField(blank=True, verbose_name='分段说明')),
                ('order', models.IntegerField(default=0, help_text='数字越小越靠前', verbose_name='排序')),
                ('is_active', models.BooleanField(default=True, verbose_name='是否启用')),
                ('created_time', models.DateTimeField(default=django.utils.timezone.now, verbose_name='创建时间')),
                ('updated_time', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('scheme', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='segmented_rates', to='settlement_center.servicefeesettlementscheme', verbose_name='关联结算方案')),
            ],
            options={
                'verbose_name': '分段递增提成配置',
                'verbose_name_plural': '分段递增提成配置',
                'db_table': 'settlement_service_fee_segmented_rate',
                'ordering': ['scheme', 'order', 'threshold'],
            },
        ),
        migrations.AddIndex(
            model_name='servicefeesegmentedrate',
            index=models.Index(fields=['scheme', 'is_active', 'order'], name='settlement__scheme_idx'),
        ),
        migrations.CreateModel(
            name='ServiceFeeJumpPointRate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('threshold', models.DecimalField(decimal_places=2, help_text='当节省金额超过此阈值时，全部节省金额适用该系数', max_digits=14, verbose_name='跳点阈值')),
                ('rate', models.DecimalField(decimal_places=2, help_text='该阈值对应的取费系数，例如：15.0 表示 15%', max_digits=5, verbose_name='取费系数(%)')),
                ('description', models.TextField(blank=True, verbose_name='跳点说明')),
                ('order', models.IntegerField(default=0, help_text='数字越小越靠前', verbose_name='排序')),
                ('is_active', models.BooleanField(default=True, verbose_name='是否启用')),
                ('created_time', models.DateTimeField(default=django.utils.timezone.now, verbose_name='创建时间')),
                ('updated_time', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('scheme', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='jump_point_rates', to='settlement_center.servicefeesettlementscheme', verbose_name='关联结算方案')),
            ],
            options={
                'verbose_name': '跳点提成配置',
                'verbose_name_plural': '跳点提成配置',
                'db_table': 'settlement_service_fee_jump_point_rate',
                'ordering': ['scheme', 'order', 'threshold'],
            },
        ),
        migrations.AddIndex(
            model_name='servicefeejumppointrate',
            index=models.Index(fields=['scheme', 'is_active', 'order'], name='settlement__scheme_jump_idx'),
        ),
        migrations.CreateModel(
            name='ServiceFeeUnitCapDetail',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('unit_name', models.CharField(help_text='单体名称，例如：1#楼、2#楼等', max_length=200, verbose_name='单体名称')),
                ('cap_unit_price', models.DecimalField(decimal_places=2, help_text='该单体的封顶单价（元/平方米）', max_digits=12, verbose_name='封顶单价')),
                ('description', models.TextField(blank=True, verbose_name='备注')),
                ('order', models.IntegerField(default=0, help_text='数字越小越靠前', verbose_name='排序')),
                ('created_time', models.DateTimeField(default=django.utils.timezone.now, verbose_name='创建时间')),
                ('updated_time', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('scheme', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='unit_cap_details', to='settlement_center.servicefeesettlementscheme', verbose_name='关联结算方案')),
            ],
            options={
                'verbose_name': '单价封顶费明细',
                'verbose_name_plural': '单价封顶费明细',
                'db_table': 'settlement_service_fee_unit_cap_detail',
                'ordering': ['scheme', 'order', 'unit_name'],
            },
        ),
        migrations.AddIndex(
            model_name='servicefeeunitcapdetail',
            index=models.Index(fields=['scheme', 'order'], name='settlement__scheme_unit_idx'),
        ),
    ]

