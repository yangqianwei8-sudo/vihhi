"""
手动发送测试通知

用于测试通知系统是否正常工作。
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

from backend.apps.plan_management.models import StrategicGoal
from backend.apps.plan_management.notifications import notify_personal_goal_published
from backend.apps.plan_management.compat import safe_approval_notification, get_approval_notification_model

User = get_user_model()


class Command(BaseCommand):
    help = "手动发送测试通知"

    def add_arguments(self, parser):
        parser.add_argument(
            '--goal-number',
            type=str,
            default='GOAL-20260121-0002',
            help='目标编号（默认：GOAL-20260121-0002）'
        )
        parser.add_argument(
            '--username',
            type=str,
            default='tester1',
            help='接收通知的用户名（默认：tester1）'
        )
        parser.add_argument(
            '--direct',
            action='store_true',
            help='直接创建通知记录，不通过通知函数'
        )

    def handle(self, *args, **options):
        goal_number = options.get('goal_number', 'GOAL-20260121-0002')
        username = options.get('username', 'tester1')
        direct = options.get('direct', False)
        
        self.stdout.write("=" * 80)
        self.stdout.write(self.style.SUCCESS("手动发送测试通知"))
        self.stdout.write("=" * 80)
        self.stdout.write("")
        
        # 获取目标
        try:
            goal = StrategicGoal.objects.get(goal_number=goal_number)
        except StrategicGoal.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"❌ 找不到目标 {goal_number}"))
            return
        
        # 获取用户
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"❌ 找不到用户 {username}"))
            return
        
        self.stdout.write(f"目标: {goal.goal_number} - {goal.name}")
        self.stdout.write(f"接收人: {user.username} (ID: {user.id})")
        self.stdout.write("")
        
        if direct:
            # 直接创建通知记录
            self.stdout.write(self.style.SUCCESS("【方式1：直接创建通知记录】"))
            try:
                ApprovalNotification = get_approval_notification_model()
                if not ApprovalNotification:
                    self.stdout.write(self.style.ERROR("❌ ApprovalNotification 模型不可用"))
                    return
                
                title = "[目标分配] 您有一个待接收的目标（测试通知）"
                content = f"您有一个待接收的目标《{goal.name}》，请及时接收。这是一条测试通知。"
                
                notification = ApprovalNotification.objects.create(
                    user=user,
                    title=title,
                    content=content,
                    object_type='goal',
                    object_id=str(goal.id),
                    event='personal_goal_published',
                    is_read=False
                )
                
                self.stdout.write(self.style.SUCCESS(f"✓ 通知已创建"))
                self.stdout.write(f"  通知ID: {notification.id}")
                self.stdout.write(f"  标题: {notification.title}")
                self.stdout.write(f"  内容: {notification.content}")
                self.stdout.write(f"  创建时间: {notification.created_at}")
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ 创建通知失败: {str(e)}"))
                import traceback
                self.stdout.write(traceback.format_exc())
        else:
            # 通过通知函数发送
            self.stdout.write(self.style.SUCCESS("【方式2：通过通知函数发送】"))
            try:
                # 临时设置目标的owner为用户（如果不同）
                original_owner = goal.owner
                if goal.owner_id != user.id:
                    self.stdout.write(self.style.WARNING(f"⚠️  目标owner是 {goal.owner.username if goal.owner else 'None'}，临时设置为 {user.username}"))
                    goal.owner = user
                    goal.save(update_fields=['owner'])
                
                result = notify_personal_goal_published(goal)
                
                # 恢复原始owner
                if original_owner != goal.owner:
                    goal.owner = original_owner
                    goal.save(update_fields=['owner'])
                
                if result:
                    self.stdout.write(self.style.SUCCESS(f"✓ 通知已发送"))
                else:
                    self.stdout.write(self.style.ERROR(f"❌ 通知发送失败（返回False）"))
                    
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ 发送通知失败: {str(e)}"))
                import traceback
                self.stdout.write(traceback.format_exc())
        
        # 检查通知记录
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("【检查通知记录】"))
        ApprovalNotification = get_approval_notification_model()
        if ApprovalNotification:
            notifications = ApprovalNotification.objects.filter(
                user=user,
                object_type='goal',
                object_id=str(goal.id),
                event='personal_goal_published'
            ).order_by('-created_at')[:5]
            
            count = notifications.count()
            self.stdout.write(f"找到 {count} 条相关通知记录")
            for i, n in enumerate(notifications, 1):
                self.stdout.write(f"  {i}. ID: {n.id}, 标题: {n.title}, 已读: {n.is_read}, 时间: {n.created_at}")
        else:
            self.stdout.write(self.style.WARNING("⚠️  ApprovalNotification 模型不可用，无法检查"))
        
        self.stdout.write("")
        self.stdout.write("=" * 80)
