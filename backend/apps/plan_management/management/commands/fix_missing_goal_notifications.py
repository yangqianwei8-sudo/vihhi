"""
修复缺失的目标发布通知

用于为已发布但未发送通知的目标补发通知。
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

from backend.apps.plan_management.models import StrategicGoal
from backend.apps.plan_management.notifications import notify_personal_goal_published, notify_company_goal_published
from backend.apps.plan_management.compat import get_approval_notification_model

User = get_user_model()


class Command(BaseCommand):
    help = "为已发布但未发送通知的目标补发通知"

    def add_arguments(self, parser):
        parser.add_argument(
            '--goal-number',
            type=str,
            help='目标编号（如：GOAL-20260121-0002），如果不指定则处理所有已发布但未通知的目标'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='仅检查，不实际发送通知'
        )

    def handle(self, *args, **options):
        goal_number = options.get('goal_number')
        dry_run = options.get('dry_run', False)
        
        ApprovalNotification = get_approval_notification_model()
        
        self.stdout.write("=" * 80)
        self.stdout.write(self.style.SUCCESS("修复缺失的目标发布通知"))
        self.stdout.write("=" * 80)
        if dry_run:
            self.stdout.write(self.style.WARNING("【DRY RUN 模式 - 不会实际发送通知】"))
        self.stdout.write("")
        
        # 查找目标
        if goal_number:
            try:
                goals = [StrategicGoal.objects.get(goal_number=goal_number)]
            except StrategicGoal.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"❌ 找不到目标 {goal_number}"))
                return
        else:
            # 查找所有已发布的目标
            goals = StrategicGoal.objects.filter(status='published')
            self.stdout.write(f"找到 {goals.count()} 个已发布的目标")
        
        self.stdout.write("")
        
        fixed_count = 0
        skipped_count = 0
        error_count = 0
        
        for goal in goals:
            self.stdout.write(f"检查目标: {goal.goal_number} - {goal.name}")
            self.stdout.write(f"  级别: {goal.level}, 状态: {goal.status}")
            
            # 检查是否已有通知
            has_notification = False
            if ApprovalNotification:
                if goal.level == 'personal':
                    notifications = ApprovalNotification.objects.filter(
                        object_type='goal',
                        object_id=str(goal.id),
                        event='personal_goal_published'
                    )
                    has_notification = notifications.exists()
                elif goal.level == 'company':
                    # 公司目标可能有多个通知，检查是否有任何通知
                    notifications = ApprovalNotification.objects.filter(
                        object_type='goal',
                        object_id=str(goal.id),
                        event='company_goal_published'
                    )
                    has_notification = notifications.exists()
            
            if has_notification:
                self.stdout.write(self.style.WARNING(f"  ⚠️  目标已有通知记录，跳过"))
                skipped_count += 1
                self.stdout.write("")
                continue
            
            # 检查目标是否满足通知条件
            if goal.level == 'personal':
                if not goal.owner:
                    self.stdout.write(self.style.ERROR(f"  ❌ 个人目标没有 owner，无法发送通知"))
                    error_count += 1
                    self.stdout.write("")
                    continue
                
                self.stdout.write(f"  Owner: {goal.owner.username}")
                
                if not dry_run:
                    try:
                        result = notify_personal_goal_published(goal)
                        if result:
                            self.stdout.write(self.style.SUCCESS(f"  ✓ 已为 {goal.owner.username} 发送通知"))
                            fixed_count += 1
                        else:
                            self.stdout.write(self.style.ERROR(f"  ❌ 发送通知失败"))
                            error_count += 1
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f"  ❌ 发送通知时出错: {str(e)}"))
                        error_count += 1
                else:
                    self.stdout.write(self.style.WARNING(f"  [DRY RUN] 将为 {goal.owner.username} 发送通知"))
                    fixed_count += 1
                    
            elif goal.level == 'company':
                self.stdout.write(f"  公司目标，将通知所有员工")
                
                if not dry_run:
                    try:
                        count = notify_company_goal_published(goal)
                        if count > 0:
                            self.stdout.write(self.style.SUCCESS(f"  ✓ 已发送 {count} 条通知"))
                            fixed_count += 1
                        else:
                            self.stdout.write(self.style.WARNING(f"  ⚠️  没有发送任何通知（可能没有符合条件的用户）"))
                            skipped_count += 1
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f"  ❌ 发送通知时出错: {str(e)}"))
                        error_count += 1
                else:
                    self.stdout.write(self.style.WARNING(f"  [DRY RUN] 将发送公司目标发布通知"))
                    fixed_count += 1
            else:
                self.stdout.write(self.style.WARNING(f"  ⚠️  未知的目标级别: {goal.level}"))
                skipped_count += 1
            
            self.stdout.write("")
        
        # 总结
        self.stdout.write("=" * 80)
        self.stdout.write(self.style.SUCCESS("【处理结果】"))
        self.stdout.write(f"  已修复: {fixed_count}")
        self.stdout.write(f"  已跳过: {skipped_count}")
        self.stdout.write(f"  错误: {error_count}")
        self.stdout.write("=" * 80)
