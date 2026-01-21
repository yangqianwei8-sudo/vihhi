"""
诊断目标发布通知问题

用于诊断为什么某个用户没有收到目标发布通知。
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db.models import Q

from backend.apps.plan_management.models import StrategicGoal

User = get_user_model()


class Command(BaseCommand):
    help = "诊断目标发布通知问题 - 检查用户为什么没有收到通知"

    def add_arguments(self, parser):
        parser.add_argument(
            'goal_code',
            type=str,
            help='目标编号（如：GOAL-20260121-0001）'
        )
        parser.add_argument(
            'username',
            type=str,
            help='用户名（如：test1）'
        )

    def handle(self, *args, **options):
        goal_code = options['goal_code']
        username = options['username']
        
        self.stdout.write("=" * 80)
        self.stdout.write(self.style.SUCCESS(f"诊断目标发布通知问题"))
        self.stdout.write("=" * 80)
        self.stdout.write(f"目标编号: {goal_code}")
        self.stdout.write(f"用户名: {username}")
        self.stdout.write("")
        
        # 1. 查找目标
        try:
            goal = StrategicGoal.objects.get(goal_number=goal_code)
        except StrategicGoal.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"❌ 错误：找不到目标 {goal_code}"))
            return
        except StrategicGoal.MultipleObjectsReturned:
            goals = StrategicGoal.objects.filter(goal_number=goal_code)
            self.stdout.write(self.style.WARNING(f"⚠️  警告：找到多个目标（{goals.count()}个），使用第一个"))
            goal = goals.first()
        
        # 2. 查找用户
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"❌ 错误：找不到用户 {username}"))
            return
        
        # 3. 显示目标信息
        self.stdout.write(self.style.SUCCESS("【目标信息】"))
        self.stdout.write(f"  目标ID: {goal.id}")
        self.stdout.write(f"  目标名称: {goal.name}")
        self.stdout.write(f"  目标状态: {goal.status} ({goal.get_status_display()})")
        goal_level = goal.level
        goal_level_display = goal.get_level_display() if hasattr(goal, 'get_level_display') else goal_level
        self.stdout.write(f"  目标级别: {goal_level} ({goal_level_display})")
        self.stdout.write(f"  创建人: {goal.created_by.username if goal.created_by else 'N/A'} (ID: {goal.created_by_id})")
        
        # 关键检查：只有公司目标才会发送公司目标发布通知
        if goal_level != 'company':
            self.stdout.write("")
            self.stdout.write(self.style.ERROR("【⚠️  重要发现】"))
            self.stdout.write(self.style.ERROR(f"  ❌ 这是一个 {goal_level_display}，不是公司目标！"))
            self.stdout.write(self.style.ERROR(f"  ❌ notify_company_goal_published 函数只会在公司目标发布时调用"))
            self.stdout.write(self.style.ERROR(f"  ❌ 因此，所有用户都不会收到公司目标发布通知"))
            self.stdout.write("")
            self.stdout.write("  对于个人目标，应该使用 notify_personal_goal_published 函数")
            self.stdout.write("  该函数会通知目标的所有者（owner）接收目标")
            return
        
        # 检查目标公司
        goal_company = None
        if hasattr(goal, 'company'):
            goal_company = goal.company
            if goal_company:
                self.stdout.write(f"  目标公司: {goal_company.name} (ID: {goal_company.id})")
            else:
                self.stdout.write(self.style.WARNING(f"  ⚠️  目标没有关联公司"))
        else:
            self.stdout.write(self.style.WARNING(f"  ⚠️  目标模型没有 company 属性"))
        
        self.stdout.write("")
        
        # 4. 显示用户信息
        self.stdout.write(self.style.SUCCESS("【用户信息】"))
        self.stdout.write(f"  用户ID: {user.id}")
        self.stdout.write(f"  用户名: {user.username}")
        self.stdout.write(f"  是否活跃: {user.is_active}")
        self.stdout.write(f"  用户类型: {user.user_type}")
        
        # 检查用户是否是创建人
        is_creator = user.id == goal.created_by_id
        self.stdout.write(f"  是否创建人: {is_creator}")
        if is_creator:
            self.stdout.write(self.style.WARNING(f"  ⚠️  用户是目标创建人，会被排除在通知列表之外"))
        
        self.stdout.write("")
        
        # 5. 检查用户Profile
        self.stdout.write(self.style.SUCCESS("【用户Profile检查】"))
        has_profile = False
        user_profile_company = None
        
        # 尝试多种方式获取profile
        profile = None
        if hasattr(user, 'profile'):
            try:
                profile = user.profile
                has_profile = profile is not None
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"  ⚠️  无法访问 user.profile: {e}"))
        
        if not profile:
            # 尝试从accounts应用获取
            try:
                from backend.apps.accounts.models import UserProfile
                profile = UserProfile.objects.filter(user=user).first()
                has_profile = profile is not None
            except ImportError:
                self.stdout.write(self.style.WARNING(f"  ⚠️  无法导入 UserProfile 模型"))
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"  ⚠️  查询 UserProfile 失败: {e}"))
        
        if has_profile and profile:
            self.stdout.write(f"  ✓ 用户有 Profile")
            if hasattr(profile, 'company'):
                user_profile_company = profile.company
                if user_profile_company:
                    self.stdout.write(f"  Profile公司: {user_profile_company.name} (ID: {user_profile_company.id})")
                else:
                    self.stdout.write(self.style.WARNING(f"  ⚠️  Profile.company 为 None"))
            else:
                self.stdout.write(self.style.WARNING(f"  ⚠️  Profile 没有 company 属性"))
        else:
            self.stdout.write(self.style.ERROR(f"  ❌ 用户没有 Profile"))
            self.stdout.write(self.style.ERROR(f"  ❌ 这是导致无法收到通知的主要原因！"))
        
        self.stdout.write("")
        
        # 6. 检查公司匹配
        self.stdout.write(self.style.SUCCESS("【公司匹配检查】"))
        if goal_company and user_profile_company:
            company_match = goal_company.id == user_profile_company.id
            if company_match:
                self.stdout.write(f"  ✓ 公司匹配: {goal_company.name} == {user_profile_company.name}")
            else:
                self.stdout.write(self.style.ERROR(f"  ❌ 公司不匹配！"))
                self.stdout.write(self.style.ERROR(f"     目标公司: {goal_company.name} (ID: {goal_company.id})"))
                self.stdout.write(self.style.ERROR(f"     用户公司: {user_profile_company.name} (ID: {user_profile_company.id})"))
                self.stdout.write(self.style.ERROR(f"  ❌ 这是导致无法收到通知的主要原因！"))
        elif goal_company and not user_profile_company:
            self.stdout.write(self.style.WARNING(f"  ⚠️  目标有公司，但用户Profile没有公司"))
        elif not goal_company and user_profile_company:
            self.stdout.write(self.style.WARNING(f"  ⚠️  目标没有公司，但用户Profile有公司"))
        else:
            self.stdout.write(self.style.WARNING(f"  ⚠️  目标和用户都没有公司信息"))
        
        self.stdout.write("")
        
        # 7. 模拟通知筛选逻辑
        self.stdout.write(self.style.SUCCESS("【通知筛选逻辑模拟】"))
        self.stdout.write("  按照 notify_company_goal_published 函数的筛选逻辑：")
        self.stdout.write("")
        
        # 步骤1: 筛选活跃用户
        step1_users = User.objects.filter(is_active=True)
        step1_count = step1_users.count()
        user_in_step1 = step1_users.filter(id=user.id).exists()
        self.stdout.write(f"  步骤1: 筛选活跃用户 (is_active=True)")
        self.stdout.write(f"    符合条件的用户数: {step1_count}")
        if user_in_step1:
            self.stdout.write(self.style.SUCCESS(f"    ✓ 用户 {username} 在筛选结果中"))
        else:
            self.stdout.write(self.style.ERROR(f"    ❌ 用户 {username} 不在筛选结果中（用户不活跃）"))
            self.stdout.write(self.style.ERROR(f"    ❌ 这是导致无法收到通知的主要原因！"))
            return
        
        # 步骤2: 公司隔离筛选
        if goal_company:
            step2_users = step1_users.filter(profile__company=goal_company)
            step2_count = step2_users.count()
            user_in_step2 = step2_users.filter(id=user.id).exists()
            self.stdout.write(f"  步骤2: 公司隔离筛选 (profile__company={goal_company.name})")
            self.stdout.write(f"    符合条件的用户数: {step2_count}")
            if user_in_step2:
                self.stdout.write(self.style.SUCCESS(f"    ✓ 用户 {username} 在筛选结果中"))
            else:
                self.stdout.write(self.style.ERROR(f"    ❌ 用户 {username} 不在筛选结果中"))
                if not has_profile:
                    self.stdout.write(self.style.ERROR(f"      原因: 用户没有 Profile"))
                elif not user_profile_company:
                    self.stdout.write(self.style.ERROR(f"      原因: 用户 Profile 没有公司"))
                elif user_profile_company.id != goal_company.id:
                    self.stdout.write(self.style.ERROR(f"      原因: 用户公司 ({user_profile_company.name}) 与目标公司 ({goal_company.name}) 不匹配"))
                self.stdout.write(self.style.ERROR(f"    ❌ 这是导致无法收到通知的主要原因！"))
                return
        else:
            step2_users = step1_users
            step2_count = step1_count
            self.stdout.write(f"  步骤2: 目标没有公司，跳过公司隔离筛选")
            self.stdout.write(f"    符合条件的用户数: {step2_count}")
        
        # 步骤3: 排除创建人
        step3_users = step2_users.exclude(id=goal.created_by_id)
        step3_count = step3_users.count()
        user_in_step3 = step3_users.filter(id=user.id).exists()
        self.stdout.write(f"  步骤3: 排除创建人 (排除 ID={goal.created_by_id})")
        self.stdout.write(f"    符合条件的用户数: {step3_count}")
        if user_in_step3:
            self.stdout.write(self.style.SUCCESS(f"    ✓ 用户 {username} 在筛选结果中"))
        else:
            self.stdout.write(self.style.ERROR(f"    ❌ 用户 {username} 不在筛选结果中（用户是创建人）"))
            self.stdout.write(self.style.ERROR(f"    ❌ 这是导致无法收到通知的主要原因！"))
            return
        
        # 8. 最终结论
        self.stdout.write("")
        self.stdout.write("=" * 80)
        if user_in_step3:
            self.stdout.write(self.style.SUCCESS("【诊断结果】"))
            self.stdout.write(self.style.SUCCESS(f"  ✓ 用户 {username} 应该收到目标 {goal_code} 的发布通知"))
            self.stdout.write("")
            self.stdout.write("  如果用户确实没有收到通知，可能的原因：")
            self.stdout.write("  1. 通知创建过程中出现异常（检查日志）")
            self.stdout.write("  2. 通知被标记为已读或删除")
            self.stdout.write("  3. 通知系统配置问题")
        else:
            self.stdout.write(self.style.ERROR("【诊断结果】"))
            self.stdout.write(self.style.ERROR(f"  ❌ 用户 {username} 不会收到目标 {goal_code} 的发布通知"))
            self.stdout.write("")
            self.stdout.write("  主要原因：")
            if not user.is_active:
                self.stdout.write(self.style.ERROR("  - 用户不活跃 (is_active=False)"))
            if not has_profile:
                self.stdout.write(self.style.ERROR("  - 用户没有 Profile"))
            elif goal_company and (not user_profile_company or user_profile_company.id != goal_company.id):
                self.stdout.write(self.style.ERROR("  - 用户公司与目标公司不匹配"))
            if is_creator:
                self.stdout.write(self.style.ERROR("  - 用户是目标创建人（会被排除）"))
        
        self.stdout.write("=" * 80)
