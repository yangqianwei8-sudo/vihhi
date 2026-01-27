"""
Django管理命令：关联两个目标
将 GOAL-20260127-0001 关联到 GOAL-20260127-0005
"""
from django.core.management.base import BaseCommand
from backend.apps.plan_management.models import StrategicGoal


class Command(BaseCommand):
    help = '关联两个目标：将 GOAL-20260127-0001 关联到 GOAL-20260127-0005'

    def add_arguments(self, parser):
        parser.add_argument(
            '--source',
            type=str,
            default='GOAL-20260127-0001',
            help='源目标编号（默认：GOAL-20260127-0001）'
        )
        parser.add_argument(
            '--target',
            type=str,
            default='GOAL-20260127-0005',
            help='目标目标编号（默认：GOAL-20260127-0005）'
        )

    def handle(self, *args, **options):
        source_number = options['source']
        target_number = options['target']
        
        # 查找目标
        source_goal = StrategicGoal.objects.filter(goal_number=source_number).first()
        target_goal = StrategicGoal.objects.filter(goal_number=target_number).first()
        
        if not source_goal:
            self.stdout.write(
                self.style.ERROR(f'错误：找不到目标 {source_number}')
            )
            return
        
        if not target_goal:
            self.stdout.write(
                self.style.ERROR(f'错误：找不到目标 {target_number}')
            )
            return
        
        self.stdout.write(f'找到源目标: {source_goal.goal_number} - {source_goal.name}')
        self.stdout.write(f'找到目标目标: {target_goal.goal_number} - {target_goal.name}')
        
        # 检查是否已经有关联关系
        if source_goal.parent_goal == target_goal:
            self.stdout.write(
                self.style.WARNING(
                    f'目标 {source_number} 已经是目标 {target_number} 的子目标'
                )
            )
            return
        
        if target_goal.parent_goal == source_goal:
            self.stdout.write(
                self.style.WARNING(
                    f'目标 {target_number} 已经是目标 {source_number} 的子目标'
                )
            )
            return
        
        # 检查是否会形成循环引用
        if self._would_create_cycle(source_goal, target_goal):
            self.stdout.write(
                self.style.ERROR(
                    f'错误：将 {source_number} 关联到 {target_number} 会形成循环引用'
                )
            )
            return
        
        # 设置关联：将 source_goal 设置为 target_goal 的子目标
        source_goal.parent_goal = target_goal
        source_goal.save()
        
        self.stdout.write(
            self.style.SUCCESS(
                f'成功：已将 {source_number} 关联到 {target_number}（设置为子目标）'
            )
        )
    
    def _would_create_cycle(self, source_goal, target_goal):
        """检查设置关联后是否会形成循环引用"""
        # 如果target_goal是source_goal的子孙节点，则会产生循环
        current = target_goal
        visited = set()
        
        while current and current.parent_goal:
            if current == source_goal:
                return True
            if current in visited:
                break  # 防止无限循环
            visited.add(current)
            current = current.parent_goal
        
        return False
