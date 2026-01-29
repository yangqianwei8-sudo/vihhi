"""
Django管理命令：删除指定目标编号的目标，并更新对齐这些目标的计划
删除目标：GOAL-20260127-0002、GOAL-20260127-0003、GOAL-20260127-0004、GOAL-20260127-0005
如果有分解目标，也全部删除
存在对齐这些需删除的目标的工作计划，调整对齐对象为GOAL-20260127-0001或GOAL-20260115-0001
注意对齐时的销售回款与诉讼回款区分
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from backend.apps.plan_management.models import StrategicGoal, Plan


class Command(BaseCommand):
    help = '删除指定目标编号的目标，并更新对齐这些目标的计划'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='仅显示将要执行的操作，不实际执行'
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        # 要删除的目标编号
        target_goal_numbers = [
            'GOAL-20260127-0002',
            'GOAL-20260127-0003',
            'GOAL-20260127-0004',
            'GOAL-20260127-0005',
        ]
        
        # 替代目标编号
        alternative_goal_1 = 'GOAL-20260127-0001'
        alternative_goal_2 = 'GOAL-20260115-0001'
        
        self.stdout.write('='*60)
        self.stdout.write('开始处理目标删除和计划对齐更新')
        self.stdout.write('='*60)
        
        # 查找要删除的目标
        goals_to_delete = StrategicGoal.objects.filter(goal_number__in=target_goal_numbers)
        
        if not goals_to_delete.exists():
            self.stdout.write(self.style.WARNING('未找到需要删除的目标'))
            return
        
        self.stdout.write(f'\n找到 {goals_to_delete.count()} 个需要删除的目标：')
        for goal in goals_to_delete:
            self.stdout.write(f'  - {goal.goal_number}: {goal.name} (类型: {goal.goal_type}, 指标: {goal.indicator_name})')
        
        # 查找替代目标
        alt_goal_1 = StrategicGoal.objects.filter(goal_number=alternative_goal_1).first()
        alt_goal_2 = StrategicGoal.objects.filter(goal_number=alternative_goal_2).first()
        
        if not alt_goal_1 and not alt_goal_2:
            self.stdout.write(self.style.ERROR('未找到替代目标！'))
            return
        
        self.stdout.write(f'\n替代目标：')
        if alt_goal_1:
            self.stdout.write(f'  - {alt_goal_1.goal_number}: {alt_goal_1.name} (类型: {alt_goal_1.goal_type}, 指标: {alt_goal_1.indicator_name})')
        if alt_goal_2:
            self.stdout.write(f'  - {alt_goal_2.goal_number}: {alt_goal_2.name} (类型: {alt_goal_2.goal_type}, 指标: {alt_goal_2.indicator_name})')
        
        # 查找所有子目标（递归）
        all_child_goals = []
        for goal in goals_to_delete:
            children = self._get_all_descendants(goal)
            all_child_goals.extend(children)
        
        # 去重子目标（使用 id 去重）
        seen_ids = set()
        unique_child_goals = []
        for child in all_child_goals:
            if child.id not in seen_ids:
                seen_ids.add(child.id)
                unique_child_goals.append(child)
        all_child_goals = unique_child_goals
        
        # 排除替代目标（如果它们在子目标列表中）
        alternative_goal_ids = set()
        if alt_goal_1:
            alternative_goal_ids.add(alt_goal_1.id)
        if alt_goal_2:
            alternative_goal_ids.add(alt_goal_2.id)
        
        all_child_goals = [g for g in all_child_goals if g.id not in alternative_goal_ids]
        
        if all_child_goals:
            self.stdout.write(f'\n找到 {len(all_child_goals)} 个子目标需要删除：')
            for child in all_child_goals:
                self.stdout.write(f'  - {child.goal_number}: {child.name} (类型: {child.goal_type}, 指标: {child.indicator_name})')
        
        # 查找对齐这些目标的计划
        all_goals_to_delete = list(goals_to_delete) + all_child_goals
        goal_ids_to_delete = [g.id for g in all_goals_to_delete]
        
        plans_to_update = Plan.objects.filter(related_goal_id__in=goal_ids_to_delete)
        
        if plans_to_update.exists():
            self.stdout.write(f'\n找到 {plans_to_update.count()} 个需要更新对齐目标的计划：')
            for plan in plans_to_update:
                goal = plan.related_goal
                self.stdout.write(f'  - {plan.plan_number}: {plan.name} -> 对齐到 {goal.goal_number} ({goal.name}, 类型: {goal.goal_type}, 指标: {goal.indicator_name})')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('\n这是模拟运行，不会实际执行删除和更新操作'))
            return
        
        # 确认执行
        self.stdout.write('\n' + '='*60)
        self.stdout.write('开始执行操作...')
        self.stdout.write('='*60)
        
        try:
            with transaction.atomic():
                # 1. 更新计划的对齐目标
                updated_count = 0
                for plan in plans_to_update:
                    old_goal = plan.related_goal
                    
                    # 根据目标类型和计划名称选择合适的替代目标
                    # 判断是否为销售回款或诉讼回款（通过指标名称或目标名称判断）
                    is_sales_payment = self._is_sales_payment(old_goal) or self._is_sales_payment_from_plan(plan)
                    is_litigation_payment = self._is_litigation_payment(old_goal) or self._is_litigation_payment_from_plan(plan)
                    
                    # 选择替代目标
                    new_goal = None
                    if is_sales_payment:
                        # 销售回款：优先使用 GOAL-20260115-0001（销售回款）
                        if alt_goal_2 and self._is_sales_payment(alt_goal_2):
                            new_goal = alt_goal_2
                        elif alt_goal_1 and self._is_sales_payment(alt_goal_1):
                            new_goal = alt_goal_1
                    elif is_litigation_payment:
                        # 诉讼回款：优先使用 GOAL-20260127-0001（诉讼回款）
                        if alt_goal_1 and self._is_litigation_payment(alt_goal_1):
                            new_goal = alt_goal_1
                        elif alt_goal_2 and self._is_litigation_payment(alt_goal_2):
                            new_goal = alt_goal_2
                    
                    # 如果无法根据类型匹配，优先使用 alt_goal_1，否则使用 alt_goal_2
                    if not new_goal:
                        new_goal = alt_goal_1 if alt_goal_1 else alt_goal_2
                    
                    if new_goal:
                        plan.related_goal = new_goal
                        plan.save()
                        updated_count += 1
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'已更新计划 {plan.plan_number}: {old_goal.goal_number} -> {new_goal.goal_number}'
                            )
                        )
                    else:
                        self.stdout.write(
                            self.style.ERROR(
                                f'无法为计划 {plan.plan_number} 找到合适的替代目标'
                            )
                        )
                
                self.stdout.write(f'\n已更新 {updated_count} 个计划的对齐目标')
                
                # 2. 删除子目标
                child_deleted_count = 0
                for child in all_child_goals:
                    try:
                        child_number = child.goal_number
                        child_name = child.name
                        child.delete()
                        child_deleted_count += 1
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'已删除子目标: {child_number} - {child_name}'
                            )
                        )
                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(
                                f'删除子目标失败 {child.goal_number}: {str(e)}'
                            )
                        )
                
                # 3. 删除主目标
                main_deleted_count = 0
                for goal in goals_to_delete:
                    try:
                        goal_number = goal.goal_number
                        goal_name = goal.name
                        goal.delete()
                        main_deleted_count += 1
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'已删除目标: {goal_number} - {goal_name}'
                            )
                        )
                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(
                                f'删除目标失败 {goal.goal_number}: {str(e)}'
                            )
                        )
                
                # 输出总结
                self.stdout.write('\n' + '='*60)
                self.stdout.write('操作完成！')
                self.stdout.write('='*60)
                self.stdout.write(f'更新计划: {updated_count} 个')
                self.stdout.write(f'删除子目标: {child_deleted_count} 个')
                self.stdout.write(f'删除主目标: {main_deleted_count} 个')
                self.stdout.write('='*60)
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'操作失败: {str(e)}'))
            raise
    
    def _get_all_descendants(self, goal):
        """递归获取所有子目标"""
        descendants = []
        for child in goal.child_goals.all():
            descendants.append(child)
            descendants.extend(self._get_all_descendants(child))
        return descendants
    
    def _is_sales_payment(self, goal):
        """判断目标是否为销售回款"""
        if not goal:
            return False
        indicator_name = goal.indicator_name or ''
        goal_name = goal.name or ''
        combined = (indicator_name + goal_name).lower()
        # 检查是否包含销售回款相关关键词
        sales_keywords = ['销售回款', '销售', '回款']
        # 排除诉讼回款
        if '诉讼' in combined:
            return False
        return any(keyword in combined for keyword in sales_keywords)
    
    def _is_litigation_payment(self, goal):
        """判断目标是否为诉讼回款"""
        if not goal:
            return False
        indicator_name = goal.indicator_name or ''
        goal_name = goal.name or ''
        combined = (indicator_name + goal_name).lower()
        # 检查是否包含诉讼回款相关关键词
        litigation_keywords = ['诉讼回款', '诉讼']
        return any(keyword in combined for keyword in litigation_keywords)
    
    def _is_sales_payment_from_plan(self, plan):
        """从计划名称判断是否为销售回款"""
        if not plan:
            return False
        plan_name = plan.name or ''
        combined = plan_name.lower()
        # 检查是否包含销售回款相关关键词，排除诉讼
        if '诉讼' in combined:
            return False
        sales_keywords = ['销售回款', '销售']
        return any(keyword in combined for keyword in sales_keywords)
    
    def _is_litigation_payment_from_plan(self, plan):
        """从计划名称判断是否为诉讼回款"""
        if not plan:
            return False
        plan_name = plan.name or ''
        combined = plan_name.lower()
        # 检查是否包含诉讼回款相关关键词
        litigation_keywords = ['诉讼回款', '诉讼', '起诉', '立案', '胜诉', '执行']
        return any(keyword in combined for keyword in litigation_keywords)
