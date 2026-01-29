"""
计划状态迁移命令：将 accepted 状态迁移到新的状态流转规则

新的状态流转规则：
- draft → published → in_progress → completed
- 不再有 accepted 状态

迁移规则：
1. 如果计划状态是 accepted：
   - 如果计划已开始（start_time <= now），转换为 in_progress
   - 如果计划未开始（start_time > now 或 start_time 为空），转换为 published
2. 更新相关的时间戳和状态日志

使用方法：
    python manage.py migrate_plan_status_from_accepted
    
选项：
    --dry-run: 试运行模式，只显示将要迁移的计划，不实际更新
    --force: 强制迁移，即使有错误也继续
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from datetime import datetime
import logging

from backend.apps.plan_management.models import Plan, PlanStatusLog

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = '将计划状态从 accepted 迁移到新的状态流转规则（published 或 in_progress）'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='试运行模式：不实际更新，只显示将要迁移的计划',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='强制迁移：即使有错误也继续',
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)
        force = options.get('force', False)
        
        self.stdout.write(f'开始检查计划状态迁移（时间：{timezone.now()}）...')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('【DRY RUN 模式】仅检查，不更新'))
        
        try:
            # 查找所有状态为 accepted 的计划
            accepted_plans = Plan.objects.filter(status='accepted')
            total_count = accepted_plans.count()
            
            self.stdout.write(f'找到 {total_count} 个状态为 accepted 的计划')
            
            if total_count == 0:
                self.stdout.write(self.style.SUCCESS('没有需要迁移的计划'))
                return
            
            now = timezone.now()
            migrated_to_published = 0
            migrated_to_in_progress = 0
            errors = []
            
            for plan in accepted_plans:
                try:
                    # 判断应该转换到哪个状态
                    if plan.start_time and plan.start_time <= now:
                        # 计划已开始，转换为 in_progress
                        new_status = 'in_progress'
                        reason = f'计划开始时间 {plan.start_time.strftime("%Y-%m-%d %H:%M")} 已到达'
                    else:
                        # 计划未开始或没有开始时间，转换为 published
                        new_status = 'published'
                        if plan.start_time:
                            reason = f'计划开始时间 {plan.start_time.strftime("%Y-%m-%d %H:%M")} 未到达'
                        else:
                            reason = '计划没有设置开始时间'
                    
                    if dry_run:
                        self.stdout.write(
                            self.style.WARNING(
                                f'  [DRY RUN] 计划 {plan.plan_number} - {plan.name} '
                                f'(当前: accepted) → {new_status} ({reason})'
                            )
                        )
                        if new_status == 'published':
                            migrated_to_published += 1
                        else:
                            migrated_to_in_progress += 1
                    else:
                        # 实际迁移
                        with transaction.atomic():
                            old_status = plan.status
                            plan.status = new_status
                            
                            # 如果转换到 published，确保 published_at 有值
                            if new_status == 'published' and not plan.published_at:
                                plan.published_at = plan.accepted_at or now
                            
                            plan.save()
                            
                            # 记录状态转换日志
                            PlanStatusLog.objects.create(
                                plan=plan,
                                old_status=old_status,
                                new_status=new_status,
                                changed_by=None,  # 系统自动迁移
                                change_reason=f'状态迁移：{reason}'
                            )
                            
                            self.stdout.write(
                                self.style.SUCCESS(
                                    f'  ✓ 计划 {plan.plan_number} - {plan.name} '
                                    f'已从 accepted 迁移到 {new_status}'
                                )
                            )
                            
                            if new_status == 'published':
                                migrated_to_published += 1
                            else:
                                migrated_to_in_progress += 1
                
                except Exception as e:
                    error_msg = f'计划 {plan.plan_number} - {plan.name}: {str(e)}'
                    logger.error(error_msg, exc_info=True)
                    errors.append(error_msg)
                    
                    if force:
                        self.stdout.write(
                            self.style.ERROR(f'  ✗ {error_msg} (继续处理...)')
                        )
                    else:
                        self.stdout.write(
                            self.style.ERROR(f'  ✗ {error_msg}')
                        )
                        raise
            
            # 输出统计信息
            self.stdout.write('')
            self.stdout.write(self.style.SUCCESS('=' * 60))
            self.stdout.write(self.style.SUCCESS('迁移完成统计：'))
            self.stdout.write(self.style.SUCCESS(f'  总计: {total_count} 个计划'))
            self.stdout.write(self.style.SUCCESS(f'  → published: {migrated_to_published} 个'))
            self.stdout.write(self.style.SUCCESS(f'  → in_progress: {migrated_to_in_progress} 个'))
            
            if errors:
                self.stdout.write(self.style.ERROR(f'  错误: {len(errors)} 个'))
                for error in errors:
                    self.stdout.write(self.style.ERROR(f'    - {error}'))
            
            self.stdout.write(self.style.SUCCESS('=' * 60))
            
            if dry_run:
                self.stdout.write(self.style.WARNING('\n这是试运行模式，未实际更新数据'))
                self.stdout.write(self.style.WARNING('运行不带 --dry-run 参数来执行实际迁移'))
            else:
                # 验证迁移结果
                remaining_accepted = Plan.objects.filter(status='accepted').count()
                if remaining_accepted > 0:
                    self.stdout.write(
                        self.style.WARNING(
                            f'\n警告：仍有 {remaining_accepted} 个计划状态为 accepted'
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.SUCCESS('\n✓ 所有 accepted 状态的计划已成功迁移')
                    )
            
        except Exception as e:
            logger.error(f"状态迁移失败: {str(e)}", exc_info=True)
            self.stdout.write(self.style.ERROR(f'迁移失败：{str(e)}'))
            if not force:
                raise
