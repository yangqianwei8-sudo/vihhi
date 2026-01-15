"""
管理命令：清除计划管理模块的所有数据

用法：
    python manage.py clear_plan_management_data
    python manage.py clear_plan_management_data --force  # 跳过确认提示
    
警告：此操作将删除计划管理模块的所有数据，包括：
    - 所有计划（Plan）及其关联数据
    - 所有战略目标（StrategicGoal）及其关联数据
    - 所有审批/决策记录（PlanDecision）
    - 所有状态日志（PlanStatusLog, GoalStatusLog）
    - 所有进度记录（PlanProgressRecord, GoalProgressRecord）
    - 所有调整申请（PlanAdjustment, GoalAdjustment）
    - 所有计划问题（PlanIssue）
    - 所有不作为记录（PlanInactivityLog）
    - 所有对齐记录（GoalAlignmentRecord）
    
此操作不可恢复！
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from backend.apps.plan_management.models import (
    # 计划相关模型
    Plan,
    PlanStatusLog,
    PlanProgressRecord,
    PlanAdjustment,
    PlanInactivityLog,
    PlanIssue,
    PlanDecision,
    # 目标相关模型
    StrategicGoal,
    GoalStatusLog,
    GoalProgressRecord,
    GoalAdjustment,
    GoalAlignmentRecord,
)


class Command(BaseCommand):
    help = '清除计划管理模块的所有数据（包括计划、目标、审批等所有相关数据）'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='跳过确认提示，直接删除',
        )

    def handle(self, *args, **options):
        force = options.get('force', False)
        
        # 统计要删除的数据
        plan_count = Plan.objects.count()
        plan_status_log_count = PlanStatusLog.objects.count()
        plan_progress_count = PlanProgressRecord.objects.count()
        plan_adjustment_count = PlanAdjustment.objects.count()
        plan_inactivity_count = PlanInactivityLog.objects.count()
        plan_issue_count = PlanIssue.objects.count()
        plan_decision_count = PlanDecision.objects.count()
        
        goal_count = StrategicGoal.objects.count()
        goal_status_log_count = GoalStatusLog.objects.count()
        goal_progress_count = GoalProgressRecord.objects.count()
        goal_adjustment_count = GoalAdjustment.objects.count()
        goal_alignment_count = GoalAlignmentRecord.objects.count()
        
        total_count = (
            plan_count + plan_status_log_count + plan_progress_count +
            plan_adjustment_count + plan_inactivity_count + plan_issue_count +
            plan_decision_count + goal_count + goal_status_log_count +
            goal_progress_count + goal_adjustment_count + goal_alignment_count
        )
        
        self.stdout.write(self.style.WARNING('=' * 70))
        self.stdout.write(self.style.WARNING('警告：此操作将删除计划管理模块的所有数据！'))
        self.stdout.write(self.style.WARNING('=' * 70))
        self.stdout.write('')
        self.stdout.write('将删除的数据统计：')
        self.stdout.write('')
        self.stdout.write('【计划相关数据】')
        self.stdout.write(f'  - 计划（Plan）：{plan_count} 条')
        self.stdout.write(f'  - 计划状态日志（PlanStatusLog）：{plan_status_log_count} 条')
        self.stdout.write(f'  - 计划进度记录（PlanProgressRecord）：{plan_progress_count} 条')
        self.stdout.write(f'  - 计划调整申请（PlanAdjustment）：{plan_adjustment_count} 条')
        self.stdout.write(f'  - 计划不作为记录（PlanInactivityLog）：{plan_inactivity_count} 条')
        self.stdout.write(f'  - 计划问题（PlanIssue）：{plan_issue_count} 条')
        self.stdout.write(f'  - 计划决策记录（PlanDecision）：{plan_decision_count} 条')
        self.stdout.write('')
        self.stdout.write('【目标相关数据】')
        self.stdout.write(f'  - 战略目标（StrategicGoal）：{goal_count} 条')
        self.stdout.write(f'  - 目标状态日志（GoalStatusLog）：{goal_status_log_count} 条')
        self.stdout.write(f'  - 目标进度记录（GoalProgressRecord）：{goal_progress_count} 条')
        self.stdout.write(f'  - 目标调整申请（GoalAdjustment）：{goal_adjustment_count} 条')
        self.stdout.write(f'  - 目标对齐记录（GoalAlignmentRecord）：{goal_alignment_count} 条')
        self.stdout.write('')
        self.stdout.write(f'总计：{total_count} 条记录')
        self.stdout.write('')
        
        if not force:
            confirm = input('确认删除所有数据？输入 "YES" 继续：')
            if confirm != 'YES':
                self.stdout.write(self.style.ERROR('操作已取消'))
                return
        
        try:
            with transaction.atomic():
                self.stdout.write('')
                self.stdout.write('开始清除数据...')
                self.stdout.write('')
                
                # ========== 第一步：清除计划相关数据 ==========
                self.stdout.write('【第一步】清除计划相关数据...')
                
                # 1.1 清除计划的多对多关系
                self.stdout.write('  1.1 清除计划的多对多关系（参与者）...')
                for plan in Plan.objects.all():
                    plan.participants.clear()
                self.stdout.write(self.style.SUCCESS('    ✓ 已清除所有计划的多对多关系'))
                
                # 1.2 删除计划不作为记录（注意：PlanInactivityLog 的 delete() 方法被重写，不允许删除）
                # 需要使用数据库级别的删除来绕过 Python 的 delete() 方法
                self.stdout.write('  1.2 删除计划不作为记录（PlanInactivityLog）...')
                from django.db import connection
                with connection.cursor() as cursor:
                    cursor.execute("DELETE FROM plan_plan_inactivity_log")
                    inactivity_deleted = cursor.rowcount
                self.stdout.write(self.style.SUCCESS(f'    ✓ 已删除 {inactivity_deleted} 条计划不作为记录'))
                
                # 1.3 删除计划决策记录（审批记录）
                self.stdout.write('  1.3 删除计划决策记录（PlanDecision）...')
                decision_deleted = PlanDecision.objects.all().delete()[0]
                self.stdout.write(self.style.SUCCESS(f'    ✓ 已删除 {decision_deleted} 条计划决策记录'))
                
                # 1.4 删除计划问题
                self.stdout.write('  1.4 删除计划问题（PlanIssue）...')
                issue_deleted = PlanIssue.objects.all().delete()[0]
                self.stdout.write(self.style.SUCCESS(f'    ✓ 已删除 {issue_deleted} 条计划问题'))
                
                # 1.5 删除计划调整申请
                self.stdout.write('  1.5 删除计划调整申请（PlanAdjustment）...')
                adjustment_deleted = PlanAdjustment.objects.all().delete()[0]
                self.stdout.write(self.style.SUCCESS(f'    ✓ 已删除 {adjustment_deleted} 条计划调整申请'))
                
                # 1.6 删除所有计划（CASCADE会自动删除PlanStatusLog和PlanProgressRecord）
                self.stdout.write('  1.6 删除所有计划（将自动删除关联的状态日志和进度记录）...')
                plan_deleted = Plan.objects.all().delete()[0]
                self.stdout.write(self.style.SUCCESS(f'    ✓ 已删除 {plan_deleted} 条计划'))
                
                # ========== 第二步：清除目标相关数据 ==========
                self.stdout.write('')
                self.stdout.write('【第二步】清除目标相关数据...')
                
                # 2.1 清除目标的多对多关系
                self.stdout.write('  2.1 清除目标的多对多关系（参与人员、关联项目）...')
                for goal in StrategicGoal.objects.all():
                    goal.participants.clear()
                    goal.related_projects.clear()
                self.stdout.write(self.style.SUCCESS('    ✓ 已清除所有目标的多对多关系'))
                
                # 2.2 删除目标对齐记录
                self.stdout.write('  2.2 删除目标对齐记录（GoalAlignmentRecord）...')
                alignment_deleted = GoalAlignmentRecord.objects.all().delete()[0]
                self.stdout.write(self.style.SUCCESS(f'    ✓ 已删除 {alignment_deleted} 条目标对齐记录'))
                
                # 2.3 删除目标调整申请
                self.stdout.write('  2.3 删除目标调整申请（GoalAdjustment）...')
                goal_adjustment_deleted = GoalAdjustment.objects.all().delete()[0]
                self.stdout.write(self.style.SUCCESS(f'    ✓ 已删除 {goal_adjustment_deleted} 条目标调整申请'))
                
                # 2.4 删除所有战略目标（CASCADE会自动删除GoalProgressRecord和GoalStatusLog）
                self.stdout.write('  2.4 删除所有战略目标（将自动删除关联的进度记录和状态日志）...')
                goal_deleted = StrategicGoal.objects.all().delete()[0]
                self.stdout.write(self.style.SUCCESS(f'    ✓ 已删除 {goal_deleted} 条战略目标'))
                
                # ========== 第三步：验证清除结果 ==========
                self.stdout.write('')
                self.stdout.write('【第三步】验证清除结果...')
                
                remaining_plans = Plan.objects.count()
                remaining_goals = StrategicGoal.objects.count()
                remaining_decisions = PlanDecision.objects.count()
                remaining_plan_status_logs = PlanStatusLog.objects.count()
                remaining_goal_status_logs = GoalStatusLog.objects.count()
                
                if (remaining_plans == 0 and remaining_goals == 0 and 
                    remaining_decisions == 0 and remaining_plan_status_logs == 0 and 
                    remaining_goal_status_logs == 0):
                    self.stdout.write(self.style.SUCCESS('    ✓ 所有数据已成功清除'))
                else:
                    self.stdout.write(self.style.WARNING('    ⚠ 仍有部分数据残留：'))
                    if remaining_plans > 0:
                        self.stdout.write(self.style.WARNING(f'      - 计划：{remaining_plans} 条'))
                    if remaining_goals > 0:
                        self.stdout.write(self.style.WARNING(f'      - 目标：{remaining_goals} 条'))
                    if remaining_decisions > 0:
                        self.stdout.write(self.style.WARNING(f'      - 决策记录：{remaining_decisions} 条'))
                    if remaining_plan_status_logs > 0:
                        self.stdout.write(self.style.WARNING(f'      - 计划状态日志：{remaining_plan_status_logs} 条'))
                    if remaining_goal_status_logs > 0:
                        self.stdout.write(self.style.WARNING(f'      - 目标状态日志：{remaining_goal_status_logs} 条'))
                
                self.stdout.write('')
                self.stdout.write(self.style.SUCCESS('=' * 70))
                self.stdout.write(self.style.SUCCESS('数据清除操作完成！'))
                self.stdout.write(self.style.SUCCESS('=' * 70))
                self.stdout.write('')
                self.stdout.write('现在可以开始进行新的联合测试了。')
                
        except Exception as e:
            self.stdout.write('')
            self.stdout.write(self.style.ERROR('=' * 70))
            self.stdout.write(self.style.ERROR('数据清除失败！'))
            self.stdout.write(self.style.ERROR('=' * 70))
            self.stdout.write(self.style.ERROR(f'错误信息：{str(e)}'))
            import traceback
            self.stdout.write(self.style.ERROR(traceback.format_exc()))
            raise

