# Generated manually

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ExternalSystem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, unique=True, verbose_name='系统名称')),
                ('code', models.CharField(blank=True, max_length=50, unique=True, verbose_name='系统编码')),
                ('description', models.TextField(blank=True, verbose_name='系统描述')),
                ('base_url', models.URLField(verbose_name='基础URL')),
                ('contact_person', models.CharField(blank=True, max_length=100, verbose_name='联系人')),
                ('contact_phone', models.CharField(blank=True, max_length=50, verbose_name='联系电话')),
                ('contact_email', models.EmailField(blank=True, max_length=254, verbose_name='联系邮箱')),
                ('status', models.CharField(choices=[('active', '启用'), ('inactive', '停用')], default='active', max_length=20, verbose_name='状态')),
                ('is_active', models.BooleanField(default=True, verbose_name='是否启用')),
                ('created_time', models.DateTimeField(default=django.utils.timezone.now, verbose_name='创建时间')),
                ('updated_time', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='created_external_systems', to=settings.AUTH_USER_MODEL, verbose_name='创建人')),
            ],
            options={
                'verbose_name': '外部系统',
                'verbose_name_plural': '外部系统',
                'db_table': 'api_external_system',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='ApiInterface',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, verbose_name='接口名称')),
                ('code', models.CharField(blank=True, max_length=100, unique=True, verbose_name='接口编码')),
                ('url', models.CharField(max_length=500, verbose_name='接口URL')),
                ('method', models.CharField(choices=[('GET', 'GET'), ('POST', 'POST'), ('PUT', 'PUT'), ('PATCH', 'PATCH'), ('DELETE', 'DELETE')], default='GET', max_length=10, verbose_name='请求方法')),
                ('auth_type', models.CharField(choices=[('none', '无认证'), ('api_key', 'API Key'), ('bearer_token', 'Bearer Token'), ('basic_auth', 'Basic Auth'), ('oauth2', 'OAuth2'), ('custom', '自定义')], default='none', max_length=20, verbose_name='认证方式')),
                ('auth_config', models.JSONField(blank=True, default=dict, verbose_name='认证配置')),
                ('request_headers', models.JSONField(blank=True, default=dict, verbose_name='请求头')),
                ('request_params', models.JSONField(blank=True, default=dict, verbose_name='请求参数')),
                ('request_body_schema', models.JSONField(blank=True, default=dict, verbose_name='请求体结构')),
                ('response_schema', models.JSONField(blank=True, default=dict, verbose_name='响应结构')),
                ('description', models.TextField(blank=True, verbose_name='接口描述')),
                ('timeout', models.IntegerField(default=30, verbose_name='超时时间（秒）')),
                ('retry_count', models.IntegerField(default=0, verbose_name='重试次数')),
                ('status', models.CharField(choices=[('active', '启用'), ('inactive', '停用'), ('deprecated', '已废弃')], default='active', max_length=20, verbose_name='状态')),
                ('is_active', models.BooleanField(default=True, verbose_name='是否启用')),
                ('version', models.CharField(default='1.0', max_length=20, verbose_name='版本号')),
                ('created_time', models.DateTimeField(default=django.utils.timezone.now, verbose_name='创建时间')),
                ('updated_time', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='created_api_interfaces', to=settings.AUTH_USER_MODEL, verbose_name='创建人')),
                ('external_system', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='api_interfaces', to='api_management.externalsystem', verbose_name='所属系统')),
            ],
            options={
                'verbose_name': 'API接口',
                'verbose_name_plural': 'API接口',
                'db_table': 'api_interface',
                'ordering': ['-created_time'],
            },
        ),
        migrations.CreateModel(
            name='ApiCallLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('request_url', models.CharField(max_length=500, verbose_name='请求URL')),
                ('request_method', models.CharField(max_length=10, verbose_name='请求方法')),
                ('request_headers', models.JSONField(blank=True, default=dict, verbose_name='请求头')),
                ('request_params', models.JSONField(blank=True, default=dict, verbose_name='请求参数')),
                ('request_body', models.TextField(blank=True, verbose_name='请求体')),
                ('response_status', models.IntegerField(blank=True, null=True, verbose_name='响应状态码')),
                ('response_headers', models.JSONField(blank=True, default=dict, verbose_name='响应头')),
                ('response_body', models.TextField(blank=True, verbose_name='响应体')),
                ('status', models.CharField(choices=[('success', '成功'), ('failed', '失败'), ('timeout', '超时')], max_length=20, verbose_name='调用状态')),
                ('error_message', models.TextField(blank=True, verbose_name='错误信息')),
                ('duration', models.FloatField(blank=True, null=True, verbose_name='耗时（秒）')),
                ('called_time', models.DateTimeField(default=django.utils.timezone.now, verbose_name='调用时间')),
                ('api_interface', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='call_logs', to='api_management.apiinterface', verbose_name='API接口')),
                ('called_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='api_calls', to=settings.AUTH_USER_MODEL, verbose_name='调用人')),
            ],
            options={
                'verbose_name': 'API调用日志',
                'verbose_name_plural': 'API调用日志',
                'db_table': 'api_call_log',
                'ordering': ['-called_time'],
            },
        ),
        migrations.CreateModel(
            name='ApiTestRecord',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('test_name', models.CharField(max_length=200, verbose_name='测试名称')),
                ('test_params', models.JSONField(blank=True, default=dict, verbose_name='测试参数')),
                ('test_body', models.TextField(blank=True, verbose_name='测试请求体')),
                ('expected_status', models.IntegerField(blank=True, null=True, verbose_name='期望状态码')),
                ('expected_response', models.TextField(blank=True, verbose_name='期望响应')),
                ('actual_status', models.IntegerField(blank=True, null=True, verbose_name='实际状态码')),
                ('actual_response', models.TextField(blank=True, verbose_name='实际响应')),
                ('status', models.CharField(choices=[('pending', '待测试'), ('success', '成功'), ('failed', '失败')], default='pending', max_length=20, verbose_name='测试状态')),
                ('error_message', models.TextField(blank=True, verbose_name='错误信息')),
                ('test_duration', models.FloatField(blank=True, null=True, verbose_name='测试耗时（秒）')),
                ('tested_time', models.DateTimeField(default=django.utils.timezone.now, verbose_name='测试时间')),
                ('api_interface', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='test_records', to='api_management.apiinterface', verbose_name='API接口')),
                ('tested_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='api_tests', to=settings.AUTH_USER_MODEL, verbose_name='测试人')),
            ],
            options={
                'verbose_name': 'API测试记录',
                'verbose_name_plural': 'API测试记录',
                'db_table': 'api_test_record',
                'ordering': ['-tested_time'],
            },
        ),
        migrations.AddIndex(
            model_name='externalsystem',
            index=models.Index(fields=['code', 'status'], name='api_externa_code_123abc_idx'),
        ),
        migrations.AddIndex(
            model_name='externalsystem',
            index=models.Index(fields=['name', 'is_active'], name='api_externa_name_456def_idx'),
        ),
        migrations.AddIndex(
            model_name='apiinterface',
            index=models.Index(fields=['code', 'status'], name='api_interfa_code_789ghi_idx'),
        ),
        migrations.AddIndex(
            model_name='apiinterface',
            index=models.Index(fields=['external_system', 'is_active'], name='api_interfa_externa_jkl012_idx'),
        ),
        migrations.AddIndex(
            model_name='apiinterface',
            index=models.Index(fields=['method', 'status'], name='api_interfa_method_mno345_idx'),
        ),
        migrations.AddIndex(
            model_name='apicalllog',
            index=models.Index(fields=['api_interface', 'called_time'], name='api_call_lo_api_int_pqr678_idx'),
        ),
        migrations.AddIndex(
            model_name='apicalllog',
            index=models.Index(fields=['status', 'called_time'], name='api_call_lo_status_stu901_idx'),
        ),
        migrations.AddIndex(
            model_name='apicalllog',
            index=models.Index(fields=['called_by', 'called_time'], name='api_call_lo_called__vwx234_idx'),
        ),
        migrations.AddIndex(
            model_name='apitestrecord',
            index=models.Index(fields=['api_interface', 'tested_time'], name='api_test_re_api_int_yza567_idx'),
        ),
        migrations.AddIndex(
            model_name='apitestrecord',
            index=models.Index(fields=['status', 'tested_time'], name='api_test_re_status_bcd890_idx'),
        ),
    ]
