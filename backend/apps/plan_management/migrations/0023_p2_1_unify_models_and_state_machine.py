# Generated manually for P2-1: 统一模型与状态机

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


def migrate_plan_type_to_level(apps, schema_editor):
    """将 Plan 的 plan_type 字段迁移到 level 字段"""
    Plan = apps.get_model('plan_management', 'Plan')
    
    # 映射关系：plan_type -> level
    type_mapping = {
        'company': 'company',
        'personal': 'personal',
        'department': 'company',  # 部门计划归为公司计划
        'project': 'company',     # 项目计划归为公司计划
    }
    
    for plan in Plan.objects.all():
        old_type = plan.plan_type
        new_level = type_mapping.get(old_type, 'company')  # 默认 company
        plan.level = new_level
        plan.save(update_fields=['level'])


def migrate_goal_responsible_to_owner(apps, schema_editor):
    """将 StrategicGoal 的 responsible_person 迁移到 owner（个人目标）"""
    StrategicGoal = apps.get_model('plan_management', 'StrategicGoal')
    
    # 对于个人目标，将 responsible_person 复制到 owner
    for goal in StrategicGoal.objects.filter(parent_goal__isnull=False):
        # 如果有父目标，说明是个人目标
        if goal.responsible_person_id:
            goal.owner_id = goal.responsible_person_id
            goal.level = 'personal'
            goal.save(update_fields=['owner_id', 'level'])


def migrate_plan_responsible_to_owner(apps, schema_editor):
    """将 Plan 的 responsible_person 迁移到 owner（个人计划）"""
    Plan = apps.get_model('plan_management', 'Plan')
    
    # 对于个人计划，将 responsible_person 复制到 owner
    for plan in Plan.objects.filter(parent_plan__isnull=False):
        # 如果有父计划，说明是个人计划
        if plan.responsible_person_id:
            plan.owner_id = plan.responsible_person_id
            plan.level = 'personal'
            plan.save(update_fields=['owner_id', 'level'])


def backfill_owner_fields(apps, schema_editor):
    """
    P2-1 数据迁移：填充 owner 字段（保底规则）
    规则：owner = responsible_person（若存在），否则 owner = created_by，否则留空
    """
    StrategicGoal = apps.get_model('plan_management', 'StrategicGoal')
    Plan = apps.get_model('plan_management', 'Plan')
    
    # StrategicGoal: 填充 owner
    for goal in StrategicGoal.objects.filter(owner__isnull=True):
        if goal.responsible_person_id:
            goal.owner_id = goal.responsible_person_id
        elif goal.created_by_id:
            goal.owner_id = goal.created_by_id
        if goal.owner_id:
            goal.save(update_fields=['owner_id'])
    
    # Plan: 填充 owner
    for plan in Plan.objects.filter(owner__isnull=True):
        if plan.responsible_person_id:
            plan.owner_id = plan.responsible_person_id
        elif plan.created_by_id:
            plan.owner_id = plan.created_by_id
        if plan.owner_id:
            plan.save(update_fields=['owner_id'])


def backfill_timestamps(apps, schema_editor):
    """
    P2-1 数据迁移：回填 published_at 和 completed_at
    规则：
    - published_at: 如果 status in ['published', 'in_progress', 'completed'] 且 published_at 为空，则 published_at = updated_time
    - completed_at: 如果 status == 'completed' 且 completed_at 为空，则 completed_at = updated_time
    """
    StrategicGoal = apps.get_model('plan_management', 'StrategicGoal')
    Plan = apps.get_model('plan_management', 'Plan')
    
    # StrategicGoal: 回填时间戳
    for goal in StrategicGoal.objects.filter(
        status__in=['published', 'in_progress', 'completed'],
        published_at__isnull=True
    ):
        goal.published_at = goal.updated_time
        goal.save(update_fields=['published_at'])
    
    for goal in StrategicGoal.objects.filter(
        status='completed',
        completed_at__isnull=True
    ):
        goal.completed_at = goal.updated_time
        goal.save(update_fields=['completed_at'])
    
    # Plan: 回填时间戳
    for plan in Plan.objects.filter(
        status__in=['published', 'accepted', 'in_progress', 'completed'],
        published_at__isnull=True
    ):
        plan.published_at = plan.updated_time
        plan.save(update_fields=['published_at'])
    
    for plan in Plan.objects.filter(
        status='completed',
        completed_at__isnull=True
    ):
        plan.completed_at = plan.updated_time
        plan.save(update_fields=['completed_at'])


class Migration(migrations.Migration):

    dependencies = [
        ('plan_management', '0022_change_related_project_to_charfield'),
        ('system_management', '0001_initial'),  # 确保 User 模型存在
    ]

    operations = [
        # ==================== StrategicGoal 模型变更 ====================
        
        # 1. 添加 level 字段
        migrations.AddField(
            model_name='strategicgoal',
            name='level',
            field=models.CharField(
                choices=[('company', '公司目标'), ('personal', '个人目标')],
                default='company',
                help_text='company=公司目标, personal=个人目标',
                max_length=20,
                verbose_name='目标层级'
            ),
        ),
        
        # 2. 添加 owner 字段
        migrations.AddField(
            model_name='strategicgoal',
            name='owner',
            field=models.ForeignKey(
                blank=True,
                help_text='个人目标必填，公司目标可为空',
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='owned_goals',
                to='system_management.user',
                verbose_name='目标所有者'
            ),
        ),
        
        # 3. 添加状态时间戳字段
        migrations.AddField(
            model_name='strategicgoal',
            name='published_at',
            field=models.DateTimeField(
                blank=True,
                help_text='状态变为 published 时自动记录',
                null=True,
                verbose_name='发布时间'
            ),
        ),
        migrations.AddField(
            model_name='strategicgoal',
            name='accepted_at',
            field=models.DateTimeField(
                blank=True,
                help_text='状态变为 accepted 时自动记录',
                null=True,
                verbose_name='接收时间'
            ),
        ),
        migrations.AddField(
            model_name='strategicgoal',
            name='completed_at',
            field=models.DateTimeField(
                blank=True,
                help_text='状态变为 completed 时自动记录',
                null=True,
                verbose_name='完成时间'
            ),
        ),
        
        # 4. 更新状态选择（添加 accepted）
        # 注意：Django 迁移不会自动更新 choices，需要在代码中处理
        migrations.AlterField(
            model_name='strategicgoal',
            name='status',
            field=models.CharField(
                choices=[
                    ('draft', '制定中'),
                    ('published', '已发布'),
                    ('accepted', '已接收'),
                    ('in_progress', '执行中'),
                    ('completed', '已完成'),
                    ('cancelled', '已取消'),
                ],
                default='draft',
                max_length=20,
                verbose_name='目标状态'
            ),
        ),
        
        # 5. 添加索引
        migrations.AddIndex(
            model_name='strategicgoal',
            index=models.Index(fields=['level'], name='plan_strateg_level_idx'),
        ),
        migrations.AddIndex(
            model_name='strategicgoal',
            index=models.Index(fields=['owner'], name='plan_strateg_owner_idx'),
        ),
        
        # ==================== Plan 模型变更 ====================
        
        # 6. 添加 level 字段（临时，先添加再删除 plan_type）
        migrations.AddField(
            model_name='plan',
            name='level',
            field=models.CharField(
                choices=[('company', '公司计划'), ('personal', '个人计划')],
                default='company',
                help_text='company=公司计划, personal=个人计划',
                max_length=20,
                verbose_name='计划层级'
            ),
        ),
        
        # 7. 迁移 plan_type 数据到 level
        migrations.RunPython(
            migrate_plan_type_to_level,
            reverse_code=migrations.RunPython.noop,
        ),
        
        # 8. 添加 owner 字段（必须先添加字段，才能执行数据迁移）
        migrations.AddField(
            model_name='plan',
            name='owner',
            field=models.ForeignKey(
                blank=True,
                help_text='个人计划必填，公司计划可为空',
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='owned_plans',
                to='system_management.user',
                verbose_name='计划所有者'
            ),
        ),
        
        # 9. 添加状态时间戳字段
        migrations.AddField(
            model_name='plan',
            name='published_at',
            field=models.DateTimeField(
                blank=True,
                help_text='状态变为 published 时自动记录',
                null=True,
                verbose_name='发布时间'
            ),
        ),
        migrations.AddField(
            model_name='plan',
            name='accepted_at',
            field=models.DateTimeField(
                blank=True,
                help_text='状态变为 accepted 时自动记录',
                null=True,
                verbose_name='接收时间'
            ),
        ),
        migrations.AddField(
            model_name='plan',
            name='completed_at',
            field=models.DateTimeField(
                blank=True,
                help_text='状态变为 completed 时自动记录',
                null=True,
                verbose_name='完成时间'
            ),
        ),
        
        # 10. 更新状态选择（添加 published 和 accepted）
        migrations.AlterField(
            model_name='plan',
            name='status',
            field=models.CharField(
                choices=[
                    ('draft', '草稿'),
                    ('published', '已发布'),
                    ('accepted', '已接收'),
                    ('in_progress', '执行中'),
                    ('completed', '已完成'),
                    ('cancelled', '已取消'),
                ],
                default='draft',
                max_length=20,
                verbose_name='计划状态'
            ),
        ),
        
        # 11. 添加索引
        migrations.AddIndex(
            model_name='plan',
            index=models.Index(fields=['level'], name='plan_plan_level_idx'),
        ),
        migrations.AddIndex(
            model_name='plan',
            index=models.Index(fields=['owner'], name='plan_plan_owner_idx'),
        ),
        
        # 12. 数据迁移：填充 owner 字段（保底规则）
        migrations.RunPython(
            backfill_owner_fields,
            reverse_code=migrations.RunPython.noop,
        ),
        
        # 13. 数据迁移：回填时间戳
        migrations.RunPython(
            backfill_timestamps,
            reverse_code=migrations.RunPython.noop,
        ),
        
        # 14. 删除旧的 plan_type 字段（可选，保留以兼容旧代码）
        # 注意：暂时不删除 plan_type，避免破坏现有代码
        # migrations.RemoveField(
        #     model_name='plan',
        #     name='plan_type',
        # ),
    ]

