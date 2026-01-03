# Generated manually - 将opinion外键字段改为opinion_id IntegerField
# 已删除production_quality模块，需要将外键字段改为存储ID的IntegerField

from django.db import migrations, models


def convert_opinion_to_opinion_id_forward(apps, schema_editor):
    """将opinion外键字段改为opinion_id IntegerField"""
    from django.db import connection
    
    with connection.cursor() as cursor:
        # 检查并修改 ProjectDesignReply 表
        try:
            # 检查字段是否存在
            cursor.execute("""
                SELECT column_name FROM information_schema.columns 
                WHERE table_name = 'production_management_design_reply' 
                AND column_name = 'opinion_id'
            """)
            if cursor.fetchone():
                # 如果已经是opinion_id，删除外键约束（如果存在）
                try:
                    cursor.execute("""
                        ALTER TABLE production_management_design_reply 
                        DROP CONSTRAINT IF EXISTS production_management_design_reply_opinion_id_fkey
                    """)
                except:
                    pass
        except:
            pass
        
        # 检查并修改 ProjectMeetingDecision 表
        try:
            cursor.execute("""
                SELECT column_name FROM information_schema.columns 
                WHERE table_name = 'production_management_meeting_decision' 
                AND column_name = 'opinion_id'
            """)
            if cursor.fetchone():
                # 如果已经是opinion_id，删除外键约束（如果存在）
                try:
                    cursor.execute("""
                        ALTER TABLE production_management_meeting_decision 
                        DROP CONSTRAINT IF EXISTS production_management_meeting_decision_opinion_id_fkey
                    """)
                except:
                    pass
        except:
            pass


def convert_opinion_to_opinion_id_reverse(apps, schema_editor):
    """反向操作：不执行任何操作（因为Opinion模型已删除）"""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('production_management', '0029_add_comprehensive_adjustment_coefficient'),
    ]

    operations = [
        # 使用SeparateDatabaseAndState来分离数据库操作和状态操作
        migrations.SeparateDatabaseAndState(
            database_operations=[
                # 数据库操作：删除外键约束（如果存在）
                migrations.RunPython(
                    convert_opinion_to_opinion_id_forward,
                    convert_opinion_to_opinion_id_reverse,
                ),
            ],
            state_operations=[
                # 状态操作：更新模型字段定义
                migrations.AlterField(
                    model_name='projectdesignreply',
                    name='opinion_id',
                    field=models.IntegerField(null=True, blank=True, verbose_name='关联意见ID', help_text='已删除生产质量模块，此字段保留用于历史数据'),
                ),
                migrations.AlterField(
                    model_name='projectmeetingdecision',
                    name='opinion_id',
                    field=models.IntegerField(null=True, blank=True, verbose_name='关联意见ID', help_text='已删除生产质量模块，此字段保留用于历史数据'),
                ),
                # 更新索引
                migrations.AlterIndexTogether(
                    name='projectdesignreply',
                    index_together={('project', 'opinion_id')},
                ),
                migrations.AlterUniqueTogether(
                    name='projectmeetingdecision',
                    unique_together={('meeting', 'opinion_id')},
                ),
            ],
        ),
    ]

