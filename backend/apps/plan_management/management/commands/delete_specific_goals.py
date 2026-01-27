"""
Django管理命令：删除指定名称的目标
删除名称为"周计划"、"计划管理第一次上线"、"计划管理上线实测"的目标
"""
from django.core.management.base import BaseCommand
from backend.apps.plan_management.models import StrategicGoal, Plan


class Command(BaseCommand):
    help = '删除指定名称的目标：周计划、计划管理第一次上线、计划管理上线实测'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='仅显示将要删除的目标，不实际删除'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='强制删除，即使有关联的计划也删除'
        )

    def handle(self, *args, **options):
        target_names = ['周计划', '计划管理第一次上线', '计划管理上线实测']
        dry_run = options['dry_run']
        force = options['force']
        
        # 查找所有匹配的目标
        goals = StrategicGoal.objects.filter(name__in=target_names)
        
        if not goals.exists():
            self.stdout.write(self.style.WARNING('未找到匹配的目标'))
            return
        
        self.stdout.write(f'找到 {goals.count()} 个目标需要删除：')
        for goal in goals:
            self.stdout.write(f'  - {goal.goal_number}: {goal.name}')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('\n这是模拟运行，不会实际删除目标'))
            return
        
        # 检查每个目标是否可以删除
        deleted_count = 0
        skipped_count = 0
        
        for goal in goals:
            # 检查是否有关联的计划
            related_plans_count = Plan.objects.filter(related_goal=goal).count()
            
            if related_plans_count > 0 and not force:
                self.stdout.write(
                    self.style.WARNING(
                        f'跳过 {goal.goal_number} ({goal.name}): 有关联的计划 ({related_plans_count} 个)'
                    )
                )
                skipped_count += 1
                continue
            
            # 检查是否有子目标
            child_goals_count = goal.child_goals.count()
            if child_goals_count > 0 and not force:
                self.stdout.write(
                    self.style.WARNING(
                        f'跳过 {goal.goal_number} ({goal.name}): 有子目标 ({child_goals_count} 个)'
                    )
                )
                skipped_count += 1
                continue
            
            # 如果强制删除，先删除关联的计划
            if force and related_plans_count > 0:
                related_plans = Plan.objects.filter(related_goal=goal)
                plans_deleted = related_plans.delete()[0]
                self.stdout.write(
                    self.style.WARNING(
                        f'强制删除 {goal.goal_number} 的关联计划: {plans_deleted} 个'
                    )
                )
            
            # 删除目标
            try:
                goal_number = goal.goal_number
                goal_name = goal.name
                goal.delete()
                self.stdout.write(
                    self.style.SUCCESS(
                        f'已删除: {goal_number} - {goal_name}'
                    )
                )
                deleted_count += 1
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f'删除失败 {goal.goal_number}: {str(e)}'
                    )
                )
        
        # 输出总结
        self.stdout.write('\n' + '='*50)
        self.stdout.write(f'删除完成: 成功 {deleted_count} 个, 跳过 {skipped_count} 个')
        self.stdout.write('='*50)
