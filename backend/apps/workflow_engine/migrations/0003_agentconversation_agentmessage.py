# Generated manually for Agent conversation storage

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('system_management', '0001_initial'),  # 假设system_management已经有初始迁移
        ('workflow_engine', '0002_alter_approvalinstance_content_type_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='AgentConversation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(help_text='对话的标题或主题', max_length=200, verbose_name='对话标题')),
                ('description', models.TextField(blank=True, help_text='对话的简要描述', verbose_name='对话描述')),
                ('metadata', models.JSONField(blank=True, default=dict, help_text='存储对话的额外信息，如模型类型、参数等', verbose_name='元数据')),
                ('is_active', models.BooleanField(default=True, help_text='是否正在进行的对话', verbose_name='是否活跃')),
                ('is_archived', models.BooleanField(default=False, help_text='是否已归档', verbose_name='是否归档')),
                ('created_time', models.DateTimeField(default=django.utils.timezone.now, verbose_name='创建时间')),
                ('updated_time', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('last_message_time', models.DateTimeField(blank=True, null=True, verbose_name='最后消息时间')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='agent_conversations', to='system_management.user', verbose_name='用户')),
            ],
            options={
                'verbose_name': 'Agent对话会话',
                'verbose_name_plural': 'Agent对话会话',
                'db_table': 'workflow_agent_conversation',
                'ordering': ['-last_message_time', '-created_time'],
            },
        ),
        migrations.CreateModel(
            name='AgentMessage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('role', models.CharField(choices=[('user', '用户'), ('assistant', '助手'), ('system', '系统')], default='user', max_length=20, verbose_name='角色')),
                ('content', models.TextField(verbose_name='消息内容')),
                ('metadata', models.JSONField(blank=True, default=dict, help_text='存储消息的额外信息', verbose_name='元数据')),
                ('sequence', models.IntegerField(default=0, help_text='消息在对话中的顺序', verbose_name='消息顺序')),
                ('created_time', models.DateTimeField(default=django.utils.timezone.now, verbose_name='创建时间')),
                ('conversation', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='messages', to='workflow_engine.agentconversation', verbose_name='对话会话')),
            ],
            options={
                'verbose_name': 'Agent对话消息',
                'verbose_name_plural': 'Agent对话消息',
                'db_table': 'workflow_agent_message',
                'ordering': ['conversation', 'sequence', 'created_time'],
            },
        ),
        migrations.AddIndex(
            model_name='agentconversation',
            index=models.Index(fields=['user', '-last_message_time'], name='workflow_ag_user_id_idx'),
        ),
        migrations.AddIndex(
            model_name='agentconversation',
            index=models.Index(fields=['is_active', 'is_archived'], name='workflow_ag_is_acti_idx'),
        ),
        migrations.AddIndex(
            model_name='agentmessage',
            index=models.Index(fields=['conversation', 'sequence'], name='workflow_ag_convers_idx'),
        ),
        migrations.AddIndex(
            model_name='agentmessage',
            index=models.Index(fields=['created_time'], name='workflow_ag_created_idx'),
        ),
    ]

