# Generated manually for School model

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('customer_management', '0039_add_missing_authorization_letter_fields'),
    ]

    operations = [
        migrations.CreateModel(
            name='School',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(db_index=True, max_length=200, verbose_name='学校名称')),
                ('region', models.CharField(choices=[
                    ('beijing', '北京'), ('tianjin', '天津'), ('hebei', '河北'), ('shanxi', '山西'),
                    ('neimenggu', '内蒙古'), ('liaoning', '辽宁'), ('jilin', '吉林'), ('heilongjiang', '黑龙江'),
                    ('shanghai', '上海'), ('jiangsu', '江苏'), ('zhejiang', '浙江'), ('anhui', '安徽'),
                    ('fujian', '福建'), ('jiangxi', '江西'), ('shandong', '山东'), ('henan', '河南'),
                    ('hubei', '湖北'), ('hunan', '湖南'), ('guangdong', '广东'), ('guangxi', '广西'),
                    ('hainan', '海南'), ('chongqing', '重庆'), ('sichuan', '四川'), ('guizhou', '贵州'),
                    ('yunnan', '云南'), ('xizang', '西藏'), ('shaanxi', '陕西'), ('gansu', '甘肃'),
                    ('qinghai', '青海'), ('ningxia', '宁夏'), ('xinjiang', '新疆'),
                    ('hongkong', '香港'), ('macau', '澳门'), ('taiwan', '台湾')
                ], max_length=20, verbose_name='所在地区')),
                ('is_211', models.BooleanField(default=False, help_text='是否属于211工程院校', verbose_name='是否211')),
                ('is_985', models.BooleanField(default=False, help_text='是否属于985工程院校', verbose_name='是否985')),
                ('is_double_first_class', models.BooleanField(default=False, help_text='是否属于双一流建设高校', verbose_name='是否双一流')),
                ('display_order', models.IntegerField(default=0, help_text='数字越小越靠前', verbose_name='显示顺序')),
                ('is_active', models.BooleanField(default=True, verbose_name='是否启用')),
                ('notes', models.TextField(blank=True, verbose_name='备注')),
                ('created_time', models.DateTimeField(default=django.utils.timezone.now, verbose_name='创建时间')),
                ('updated_time', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
            ],
            options={
                'verbose_name': '学校管理',
                'verbose_name_plural': '学校管理',
                'db_table': 'customer_school',
                'ordering': ['display_order', 'region', 'name'],
            },
        ),
        migrations.AddIndex(
            model_name='school',
            index=models.Index(fields=['name'], name='customer_sc_name_idx'),
        ),
        migrations.AddIndex(
            model_name='school',
            index=models.Index(fields=['region'], name='customer_sc_region_idx'),
        ),
        migrations.AddIndex(
            model_name='school',
            index=models.Index(fields=['is_211', 'is_985'], name='customer_sc_tags_idx'),
        ),
        migrations.AddIndex(
            model_name='school',
            index=models.Index(fields=['is_active'], name='customer_sc_active_idx'),
        ),
        migrations.AddField(
            model_name='contacteducation',
            name='school',
            field=models.ForeignKey(
                blank=True,
                help_text='从后台管理的学校列表中选择',
                null=True,
                on_delete=models.SET_NULL,
                related_name='educations',
                to='customer_management.school',
                verbose_name='学校'
            ),
        ),
        migrations.AlterField(
            model_name='contacteducation',
            name='school_name',
            field=models.CharField(
                blank=True,
                help_text='如果学校不在列表中，可手动输入',
                max_length=200,
                verbose_name='学校名称（备用）'
            ),
        ),
    ]

