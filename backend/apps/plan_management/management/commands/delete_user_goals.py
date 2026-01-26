"""
管理命令：删除指定用户的所有战略目标

用法：
    python manage.py delete_user_goals tester1
    python manage.py delete_user_goals tester1 --force  # 跳过确认提示
    
警告：此操作将删除指定用户的所有战略目标（无论状态），不可恢复！
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from django.contrib.auth import get_user_model
from backend.apps.plan_management.models import (
    StrategicGoal,
    GoalProgressRecord,
    GoalStatusLog,
    GoalAdjustment,
    GoalAlignmentRecord
)

User = get_user_model()


class Command(BaseCommand):
    help = '删除指定用户的所有战略目标（包括已发布和草稿状态）'

    def add_arguments(self, parser):
        parser.add_argument(
            'usernames',
            nargs='+',
            help='要删除战略目标的用户名列表（如：tester1）',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='跳过确认提示，直接删除',
        )

    def handle(self, *args, **options):
        usernames = options['usernames']
        force = options.get('force', False)
        
        # 查找用户
        users = []
        for username in usernames:
            try:
                user = User.objects.get(username=username)
                users.append(user)
                self.stdout.write(f'找到用户: {user.username} ({user.get_full_name() or user.username})')
            except User.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'用户 "{username}" 不存在，跳过'))
        
        if not users:
            self.stdout.write(self.style.ERROR('没有找到任何用户，退出'))
            return
        
        # 统计要删除的战略目标
        goals_to_delete = StrategicGoal.objects.filter(
            responsible_person__in=users
        ) | StrategicGoal.objects.filter(
            owner__in=users
        ) | StrategicGoal.objects.filter(
            created_by__in=users
        )
        
        # 去重（使用 distinct()）
        goals_to_delete = goals_to_delete.distinct()
        
        goal_count = goals_to_delete.count()
        
        if goal_count == 0:
            self.stdout.write(self.style.SUCCESS('没有找到要删除的战略目标'))
            return
        
        # 按状态统计
        status_counts = {}
        for goal in goals_to_delete:
            status = goal.status
            status_counts[status] = status_counts.get(status, 0) + 1
        
        # 统计关联数据
        goal_ids = list(goals_to_delete.values_list('id', flat=True))
        progress_count = GoalProgressRecord.objects.filter(goal_id__in=goal_ids).count()
        status_log_count = GoalStatusLog.objects.filter(goal_id__in=goal_ids).count()
        adjustment_count = GoalAdjustment.objects.filter(goal_id__in=goal_ids).count()
        # GoalAlignmentRecord有parent_goal和child_goal两个外键
        alignment_count = GoalAlignmentRecord.objects.filter(
            parent_goal_id__in=goal_ids
        ) | GoalAlignmentRecord.objects.filter(
            child_goal_id__in=goal_ids
        )
        alignment_count = alignment_count.distinct().count()
        
        self.stdout.write(self.style.WARNING('=' * 70))
        self.stdout.write(self.style.WARNING('警告：此操作将删除指定用户的所有战略目标！'))
        self.stdout.write(self.style.WARNING('=' * 70))
        self.stdout.write('')
        self.stdout.write('将删除的战略目标统计：')
        self.stdout.write(f'  - 总目标数：{goal_count} 条')
        self.stdout.write('  - 按状态分布：')
        for status, count in status_counts.items():
            status_display = dict(StrategicGoal.STATUS_CHOICES).get(status, status)
            self.stdout.write(f'    * {status_display}：{count} 条')
        self.stdout.write('')
        self.stdout.write('关联数据统计：')
        self.stdout.write(f'  - 进度记录：{progress_count} 条')
        self.stdout.write(f'  - 状态日志：{status_log_count} 条')
        self.stdout.write(f'  - 调整记录：{adjustment_count} 条')
        self.stdout.write(f'  - 对齐记录：{alignment_count} 条')
        self.stdout.write('')
        self.stdout.write('涉及的用户：')
        for user in users:
            responsible_count = StrategicGoal.objects.filter(responsible_person=user).count()
            owner_count = StrategicGoal.objects.filter(owner=user).count()
            created_count = StrategicGoal.objects.filter(created_by=user).count()
            self.stdout.write(f'  - {user.username} ({user.get_full_name() or user.username})：')
            self.stdout.write(f'    * 作为负责人：{responsible_count} 条')
            self.stdout.write(f'    * 作为所有者：{owner_count} 条')
            self.stdout.write(f'    * 作为创建人：{created_count} 条')
        self.stdout.write('')
        
        if not force:
            confirm = input('确认删除？(yes/no): ')
            if confirm.lower() != 'yes':
                self.stdout.write(self.style.WARNING('操作已取消'))
                return
        
        try:
            with transaction.atomic():
                self.stdout.write('')
                self.stdout.write('开始删除战略目标...')
                self.stdout.write('')
                
                # 1. 清除多对多关系（必须先清除，避免外键约束问题）
                self.stdout.write('清除战略目标的多对多关系（参与者）...')
                for goal in goals_to_delete:
                    goal.participants.clear()
                self.stdout.write(self.style.SUCCESS('  ✓ 已清除所有战略目标的多对多关系'))
                
                # 2. 删除对齐记录（独立的外键关系）
                # GoalAlignmentRecord有parent_goal和child_goal两个外键
                if alignment_count > 0:
                    self.stdout.write('删除对齐记录...')
                    alignment_records = GoalAlignmentRecord.objects.filter(
                        parent_goal_id__in=goal_ids
                    ) | GoalAlignmentRecord.objects.filter(
                        child_goal_id__in=goal_ids
                    )
                    alignment_deleted = alignment_records.distinct().delete()[0]
                    self.stdout.write(self.style.SUCCESS(f'  ✓ 已删除 {alignment_deleted} 条对齐记录'))
                
                # 3. 删除调整记录（独立的外键关系）
                if adjustment_count > 0:
                    self.stdout.write('删除调整记录...')
                    adjustment_deleted = GoalAdjustment.objects.filter(goal_id__in=goal_ids).delete()[0]
                    self.stdout.write(self.style.SUCCESS(f'  ✓ 已删除 {adjustment_deleted} 条调整记录'))
                
                # 4. 删除战略目标（CASCADE会自动删除GoalProgressRecord和GoalStatusLog）
                # 由于parent_goal是SET_NULL，可以安全删除所有目标
                # 注意：不能对distinct()后的queryset直接调用delete()，需要先获取ID列表
                self.stdout.write('删除战略目标（将自动删除关联的进度记录和状态日志）...')
                goal_ids_list = list(goals_to_delete.values_list('id', flat=True))
                deleted_count = StrategicGoal.objects.filter(id__in=goal_ids_list).delete()[0]
                self.stdout.write(self.style.SUCCESS(f'  ✓ 已删除 {deleted_count} 条战略目标'))
                
                self.stdout.write('')
                self.stdout.write(self.style.SUCCESS('=' * 70))
                self.stdout.write(self.style.SUCCESS(f'成功删除 {deleted_count} 条战略目标！'))
                self.stdout.write(self.style.SUCCESS('=' * 70))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR('=' * 70))
            self.stdout.write(self.style.ERROR(f'删除失败：{str(e)}'))
            self.stdout.write(self.style.ERROR('=' * 70))
            import traceback
            self.stdout.write(traceback.format_exc())
            raise
