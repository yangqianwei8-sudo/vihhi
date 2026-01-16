# Generated migration for updating goal period choices

from django.db import migrations


def update_goal_period_choices(apps, schema_editor):
    """
    更新目标周期选项：
    - three_year (三年目标) -> half_year (半年目标)
    - five_year (五年目标) -> quarterly (季度目标)
    """
    StrategicGoal = apps.get_model('plan_management', 'StrategicGoal')
    
    # 将三年目标转换为半年目标
    StrategicGoal.objects.filter(goal_period='three_year').update(goal_period='half_year')
    
    # 将五年目标转换为季度目标
    StrategicGoal.objects.filter(goal_period='five_year').update(goal_period='quarterly')


def reverse_update_goal_period_choices(apps, schema_editor):
    """
    回滚操作：将新选项转换回旧选项
    """
    StrategicGoal = apps.get_model('plan_management', 'StrategicGoal')
    
    # 将半年目标转换回三年目标
    StrategicGoal.objects.filter(goal_period='half_year').update(goal_period='three_year')
    
    # 将季度目标转换回五年目标
    StrategicGoal.objects.filter(goal_period='quarterly').update(goal_period='five_year')


class Migration(migrations.Migration):

    dependencies = [
        ('plan_management', '0016_add_inactivity_evidence_models'),
    ]

    operations = [
        migrations.RunPython(
            update_goal_period_choices,
            reverse_update_goal_period_choices,
        ),
    ]
