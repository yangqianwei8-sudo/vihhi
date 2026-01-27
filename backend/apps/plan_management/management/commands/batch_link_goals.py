"""
Django管理命令：批量关联多个目标到同一个父目标
"""
from django.core.management.base import BaseCommand
from backend.apps.plan_management.models import StrategicGoal


class Command(BaseCommand):
    help = '批量关联多个目标到同一个父目标'

    def add_arguments(self, parser):
        parser.add_argument(
            '--source',
            type=str,
            nargs='+',
            required=True,
            help='源目标编号列表（要关联的目标）'
        )
        parser.add_argument(
            '--target',
            type=str,
            required=True,
            help='目标目标编号（父目标）'
        )

    def handle(self, *args, **options):
        source_numbers = options['source']
        target_number = options['target']
        
        # 查找父目标
        target_goal = StrategicGoal.objects.filter(goal_number=target_number).first()
        if not target_goal:
            self.stdout.write(
                self.style.ERROR(f'错误：找不到目标 {target_number}')
            )
            return
        
        self.stdout.write(f'父目标: {target_goal.goal_number} - {target_goal.name}')
        
        # 查找所有源目标
        source_goals = StrategicGoal.objects.filter(goal_number__in=source_numbers)
        found_numbers = set(source_goals.values_list('goal_number', flat=True))
        missing_numbers = set(source_numbers) - found_numbers
        
        if missing_numbers:
            self.stdout.write(
                self.style.ERROR(f'错误：找不到以下目标: {", ".join(missing_numbers)}')
            )
        
        if not source_goals.exists():
            self.stdout.write(self.style.ERROR('没有找到任何源目标'))
            return
        
        self.stdout.write(f'\n找到 {source_goals.count()} 个源目标:')
        for goal in source_goals:
            self.stdout.write(f'  - {goal.goal_number}: {goal.name}')
        
        # 关联每个源目标
        success_count = 0
        skipped_count = 0
        
        for source_goal in source_goals:
            # 检查是否已经关联
            if source_goal.parent_goal == target_goal:
                self.stdout.write(
                    self.style.WARNING(
                        f'跳过 {source_goal.goal_number}: 已经是 {target_number} 的子目标'
                    )
                )
                skipped_count += 1
                continue
            
            # 检查是否会形成循环引用
            if self._would_create_cycle(source_goal, target_goal):
                self.stdout.write(
                    self.style.ERROR(
                        f'错误：将 {source_goal.goal_number} 关联到 {target_number} 会形成循环引用'
                    )
                )
                skipped_count += 1
                continue
            
            # 设置关联
            source_goal.parent_goal = target_goal
            source_goal.save()
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'成功：已将 {source_goal.goal_number} 关联到 {target_number}'
                )
            )
            success_count += 1
        
        # 输出总结
        self.stdout.write('\n' + '='*50)
        self.stdout.write(f'关联完成: 成功 {success_count} 个, 跳过 {skipped_count} 个')
        self.stdout.write('='*50)
    
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
