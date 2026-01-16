# Generated migration to fix pending_approval status inconsistency
# 修复战略目标中 pending_approval 状态的数据不一致问题

from django.db import migrations


def fix_pending_approval_status(apps, schema_editor):
    """将 pending_approval 状态改为 draft"""
    StrategicGoal = apps.get_model('plan_management', 'StrategicGoal')
    
    # 查找所有状态为 pending_approval 的目标
    pending_goals = StrategicGoal.objects.filter(status='pending_approval')
    count = pending_goals.update(status='draft')
    
    print(f"已修复 {count} 个目标的状态：pending_approval -> draft")


def reverse_fix(apps, schema_editor):
    """回滚操作（如果需要）"""
    # 注意：这个回滚可能不准确，因为无法区分哪些是原本的 pending_approval
    # 所以回滚时不做任何操作
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('plan_management', '0017_update_goal_period_choices'),
    ]

    operations = [
        migrations.RunPython(fix_pending_approval_status, reverse_fix),
    ]
