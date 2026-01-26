"""
管理命令：删除指定用户的所有计划

用法：
    python manage.py delete_user_plans 杨乾维 tester1
    python manage.py delete_user_plans 杨乾维 tester1 --force  # 跳过确认提示
    
警告：此操作将删除指定用户的所有计划（无论状态），不可恢复！
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from django.contrib.auth import get_user_model
from backend.apps.plan_management.models import Plan

User = get_user_model()


class Command(BaseCommand):
    help = '删除指定用户的所有计划（包括已发布和草稿状态）'

    def add_arguments(self, parser):
        parser.add_argument(
            'usernames',
            nargs='+',
            help='要删除计划的用户名列表（如：杨乾维 tester1）',
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
        
        # 统计要删除的计划
        plans_to_delete = Plan.objects.filter(
            responsible_person__in=users
        ) | Plan.objects.filter(
            owner__in=users
        ) | Plan.objects.filter(
            created_by__in=users
        )
        
        # 去重（使用 distinct()）
        plans_to_delete = plans_to_delete.distinct()
        
        plan_count = plans_to_delete.count()
        
        if plan_count == 0:
            self.stdout.write(self.style.SUCCESS('没有找到要删除的计划'))
            return
        
        # 按状态统计
        status_counts = {}
        for plan in plans_to_delete:
            status = plan.status
            status_counts[status] = status_counts.get(status, 0) + 1
        
        self.stdout.write(self.style.WARNING('=' * 70))
        self.stdout.write(self.style.WARNING('警告：此操作将删除指定用户的所有计划！'))
        self.stdout.write(self.style.WARNING('=' * 70))
        self.stdout.write('')
        self.stdout.write('将删除的计划统计：')
        self.stdout.write(f'  - 总计划数：{plan_count} 条')
        self.stdout.write('  - 按状态分布：')
        for status, count in status_counts.items():
            status_display = dict(Plan.STATUS_CHOICES).get(status, status)
            self.stdout.write(f'    * {status_display}：{count} 条')
        self.stdout.write('')
        self.stdout.write('涉及的用户：')
        for user in users:
            responsible_count = Plan.objects.filter(responsible_person=user).count()
            owner_count = Plan.objects.filter(owner=user).count()
            created_count = Plan.objects.filter(created_by=user).count()
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
                self.stdout.write('开始删除计划...')
                self.stdout.write('')
                
                # 先清除多对多关系
                self.stdout.write('清除计划的多对多关系（参与者）...')
                for plan in plans_to_delete:
                    plan.participants.clear()
                self.stdout.write(self.style.SUCCESS('  ✓ 已清除所有计划的多对多关系'))
                
                # 删除计划（使用数据库级别的删除，绕过模型的 delete() 方法限制）
                self.stdout.write('删除计划...')
                from django.db import connection
                with connection.cursor() as cursor:
                    # 获取所有要删除的计划ID
                    plan_ids = list(plans_to_delete.values_list('id', flat=True))
                    
                    if plan_ids:
                        # 删除关联数据
                        # 1. 删除计划决策记录
                        try:
                            cursor.execute(
                                "DELETE FROM plan_decision WHERE plan_id IN %s",
                                [tuple(plan_ids)]
                            )
                            self.stdout.write(f'  ✓ 已删除 {cursor.rowcount} 条计划决策记录')
                        except Exception as e:
                            self.stdout.write(f'  - 计划决策记录表可能不存在，跳过: {e}')
                        
                        # 2. 删除计划状态日志
                        try:
                            cursor.execute(
                                "DELETE FROM plan_plan_status_log WHERE plan_id IN %s",
                                [tuple(plan_ids)]
                            )
                            self.stdout.write(f'  ✓ 已删除 {cursor.rowcount} 条计划状态日志')
                        except Exception as e:
                            self.stdout.write(f'  - 计划状态日志表可能不存在，跳过: {e}')
                        
                        # 3. 删除计划进度记录
                        try:
                            cursor.execute(
                                "DELETE FROM plan_plan_progress_record WHERE plan_id IN %s",
                                [tuple(plan_ids)]
                            )
                            self.stdout.write(f'  ✓ 已删除 {cursor.rowcount} 条计划进度记录')
                        except Exception as e:
                            self.stdout.write(f'  - 计划进度记录表可能不存在，跳过: {e}')
                        
                        # 4. 删除计划调整申请
                        try:
                            cursor.execute(
                                "DELETE FROM plan_plan_adjustment WHERE plan_id IN %s",
                                [tuple(plan_ids)]
                            )
                            self.stdout.write(f'  ✓ 已删除 {cursor.rowcount} 条计划调整申请')
                        except Exception as e:
                            self.stdout.write(f'  - 计划调整申请表可能不存在，跳过: {e}')
                        
                        # 5. 删除计划问题
                        try:
                            cursor.execute(
                                "DELETE FROM plan_plan_issue WHERE plan_id IN %s",
                                [tuple(plan_ids)]
                            )
                            self.stdout.write(f'  ✓ 已删除 {cursor.rowcount} 条计划问题')
                        except Exception as e:
                            self.stdout.write(f'  - 计划问题表可能不存在，跳过: {e}')
                        
                        # 6. 删除计划不作为记录（如果表存在）
                        try:
                            cursor.execute(
                                "DELETE FROM plan_plan_inactivity_log WHERE plan_id IN %s",
                                [tuple(plan_ids)]
                            )
                            self.stdout.write(f'  ✓ 已删除 {cursor.rowcount} 条计划不作为记录')
                        except Exception as e:
                            self.stdout.write(f'  - 计划不作为记录表可能不存在，跳过: {e}')
                        
                        # 7. 删除计划的多对多关系（参与者）- 已经在前面清除了，这里跳过
                        # 注意：多对多关系已经在前面通过 Django ORM 清除了
                        
                        # 8. 最后删除计划本身
                        cursor.execute(
                            "DELETE FROM plan_plan WHERE id IN %s",
                            [tuple(plan_ids)]
                        )
                        deleted_count = cursor.rowcount
                        self.stdout.write(f'  ✓ 已删除 {deleted_count} 条计划')
                
                self.stdout.write('')
                self.stdout.write(self.style.SUCCESS('=' * 70))
                self.stdout.write(self.style.SUCCESS(f'成功删除 {deleted_count} 条计划！'))
                self.stdout.write(self.style.SUCCESS('=' * 70))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR('=' * 70))
            self.stdout.write(self.style.ERROR(f'删除失败：{str(e)}'))
            self.stdout.write(self.style.ERROR('=' * 70))
            import traceback
            self.stdout.write(traceback.format_exc())
            raise
