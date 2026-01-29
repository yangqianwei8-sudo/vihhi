"""
根据新的状态流转规则更新数据库中的计划状态

新的状态流转规则：
1. 员工提交计划，系统自动标记为"草稿"（draft）
2. 审批完成后，系统自动标记为"已发布"（published）
3. 员工启动工作任务，或到达计划开始时间，系统自动标记为"执行中"（in_progress）
   - 若系统时间到达任务的"计划开始日期"的上午9点时，若任务仍处于"已发布"的状态，则自动变更为"执行中"
4. 工作任务完成后，自动标记为"已完成"（completed）
5. 若任务在截止日未完成，自动标记为"逾期X天"（通过 is_overdue 字段标记）
6. 若任务已取消、已暂停、已延期，系统自动标记（cancelled, paused, delayed）

更新规则：
1. published 状态的计划：
   - 如果 start_time <= 今天上午9点，且当前时间 >= 今天上午9点，则更新为 in_progress
2. in_progress 状态的计划：
   - 如果 progress >= 100，则更新为 completed
   - 如果 end_time < now 且 progress < 100，标记为逾期（is_overdue）
3. 检查所有计划的状态是否符合规则

使用方法：
    python manage.py update_plan_status_by_rules
    
选项：
    --dry-run: 试运行模式，只显示将要更新的计划，不实际更新
    --force: 强制更新，即使有错误也继续
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from datetime import datetime, timedelta
import logging

from backend.apps.plan_management.models import Plan, PlanStatusLog

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = '根据新的状态流转规则更新数据库中的计划状态'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='试运行模式：不实际更新，只显示将要更新的计划',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='强制更新：即使有错误也继续',
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)
        force = options.get('force', False)
        
        self.stdout.write(f'开始根据规则更新计划状态（时间：{timezone.now()}）...')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('【DRY RUN 模式】仅检查，不更新'))
        
        try:
            now = timezone.now()
            today = now.date()
            # 今天上午9点
            today_9am = timezone.make_aware(
                datetime.combine(today, datetime.min.time().replace(hour=9))
            )
            
            updated_count = 0
            errors = []
            
            # 1. 更新 published 状态的计划（如果开始时间已到）
            self.stdout.write('')
            self.stdout.write(self.style.SUCCESS('=' * 60))
            self.stdout.write('1. 检查已发布状态的计划...')
            
            published_plans = Plan.objects.filter(status='published')
            self.stdout.write(f'   找到 {published_plans.count()} 个已发布的计划')
            
            for plan in published_plans:
                try:
                    should_update = False
                    new_status = None
                    reason = None
                    
                    if plan.start_time:
                        plan_start_date = plan.start_time.date()
                        # 如果计划开始日期是今天或之前，且当前时间已过上午9点
                        if plan_start_date <= today and now >= today_9am:
                            should_update = True
                            new_status = 'in_progress'
                            reason = f'计划开始时间已到达（{plan.start_time.strftime("%Y-%m-%d %H:%M")}），且当前时间已过上午9点'
                    
                    if should_update:
                        if dry_run:
                            self.stdout.write(
                                self.style.WARNING(
                                    f'  [DRY RUN] 计划 {plan.plan_number} - {plan.name} '
                                    f'将更新为 {new_status} ({reason})'
                                )
                            )
                            updated_count += 1
                        else:
                            try:
                                with transaction.atomic():
                                    old_status = plan.status
                                    plan.transition_to(new_status, user=None)
                                    
                                    # 记录状态转换日志
                                    PlanStatusLog.objects.create(
                                        plan=plan,
                                        old_status=old_status,
                                        new_status=new_status,
                                        changed_by=None,
                                        change_reason=f'自动状态更新：{reason}'
                                    )
                                    
                                    self.stdout.write(
                                        self.style.SUCCESS(
                                            f'  ✓ 计划 {plan.plan_number} - {plan.name} '
                                            f'已更新为 {new_status}'
                                        )
                                    )
                                    updated_count += 1
                            except Exception as e:
                                error_msg = f'计划 {plan.plan_number} - {plan.name}: {str(e)}'
                                logger.error(error_msg, exc_info=True)
                                errors.append(error_msg)
                                if force:
                                    self.stdout.write(
                                        self.style.ERROR(f'  ✗ {error_msg} (继续处理...)')
                                    )
                                else:
                                    raise
                
                except Exception as e:
                    error_msg = f'计划 {plan.plan_number} - {plan.name}: {str(e)}'
                    logger.error(error_msg, exc_info=True)
                    errors.append(error_msg)
                    if not force:
                        raise
            
            # 2. 更新 in_progress 状态的计划（如果进度100%则完成）
            self.stdout.write('')
            self.stdout.write(self.style.SUCCESS('=' * 60))
            self.stdout.write('2. 检查执行中状态的计划...')
            
            in_progress_plans = Plan.objects.filter(status='in_progress')
            self.stdout.write(f'   找到 {in_progress_plans.count()} 个执行中的计划')
            
            completed_count = 0
            overdue_count = 0
            
            for plan in in_progress_plans:
                try:
                    # 检查是否应该完成
                    progress = float(plan.progress) if plan.progress else 0.0
                    if progress >= 100:
                        if dry_run:
                            self.stdout.write(
                                self.style.WARNING(
                                    f'  [DRY RUN] 计划 {plan.plan_number} - {plan.name} '
                                    f'(进度: {progress}%) 将更新为 completed'
                                )
                            )
                            completed_count += 1
                        else:
                            try:
                                with transaction.atomic():
                                    old_status = plan.status
                                    plan.transition_to('completed', user=None)
                                    
                                    PlanStatusLog.objects.create(
                                        plan=plan,
                                        old_status=old_status,
                                        new_status='completed',
                                        changed_by=None,
                                        change_reason='自动状态更新：进度已达到100%'
                                    )
                                    
                                    self.stdout.write(
                                        self.style.SUCCESS(
                                            f'  ✓ 计划 {plan.plan_number} - {plan.name} '
                                            f'已更新为 completed（进度: {progress}%）'
                                        )
                                    )
                                    completed_count += 1
                                    updated_count += 1
                            except Exception as e:
                                error_msg = f'计划 {plan.plan_number} - {plan.name}: {str(e)}'
                                logger.error(error_msg, exc_info=True)
                                errors.append(error_msg)
                                if force:
                                    self.stdout.write(
                                        self.style.ERROR(f'  ✗ {error_msg} (继续处理...)')
                                    )
                                else:
                                    raise
                    
                    # 检查是否逾期
                    elif plan.end_time and plan.end_time < now:
                        if not plan.is_overdue:
                            if dry_run:
                                self.stdout.write(
                                    self.style.WARNING(
                                        f'  [DRY RUN] 计划 {plan.plan_number} - {plan.name} '
                                        f'将标记为逾期（截止时间: {plan.end_time.strftime("%Y-%m-%d %H:%M")}）'
                                    )
                                )
                                overdue_count += 1
                            else:
                                try:
                                    plan.check_overdue_status()
                                    plan.save()
                                    self.stdout.write(
                                        self.style.WARNING(
                                            f'  ⚠ 计划 {plan.plan_number} - {plan.name} '
                                            f'已标记为逾期（逾期 {plan.overdue_days} 天）'
                                        )
                                    )
                                    overdue_count += 1
                                except Exception as e:
                                    error_msg = f'计划 {plan.plan_number} - {plan.name}: {str(e)}'
                                    logger.error(error_msg, exc_info=True)
                                    if force:
                                        self.stdout.write(
                                            self.style.ERROR(f'  ✗ {error_msg} (继续处理...)')
                                        )
                                    else:
                                        raise
                
                except Exception as e:
                    error_msg = f'计划 {plan.plan_number} - {plan.name}: {str(e)}'
                    logger.error(error_msg, exc_info=True)
                    errors.append(error_msg)
                    if not force:
                        raise
            
            # 3. 检查是否有 accepted 状态的计划（应该迁移）
            self.stdout.write('')
            self.stdout.write(self.style.SUCCESS('=' * 60))
            self.stdout.write('3. 检查是否有需要迁移的 accepted 状态计划...')
            
            accepted_plans = Plan.objects.filter(status='accepted')
            accepted_count = accepted_plans.count()
            
            if accepted_count > 0:
                self.stdout.write(
                    self.style.WARNING(f'   发现 {accepted_count} 个 accepted 状态的计划，需要迁移')
                )
                
                migrated_to_published = 0
                migrated_to_in_progress = 0
                
                for plan in accepted_plans:
                    try:
                        # 判断应该转换到哪个状态
                        if plan.start_time and plan.start_time <= now:
                            new_status = 'in_progress'
                            reason = f'计划开始时间已到达'
                        else:
                            new_status = 'published'
                            reason = f'计划未开始或没有开始时间'
                        
                        if dry_run:
                            self.stdout.write(
                                self.style.WARNING(
                                    f'  [DRY RUN] 计划 {plan.plan_number} - {plan.name} '
                                    f'将从 accepted 迁移到 {new_status} ({reason})'
                                )
                            )
                            if new_status == 'published':
                                migrated_to_published += 1
                            else:
                                migrated_to_in_progress += 1
                        else:
                            try:
                                with transaction.atomic():
                                    old_status = plan.status
                                    plan.status = new_status
                                    
                                    # 如果转换到 published，确保 published_at 有值
                                    if new_status == 'published' and not plan.published_at:
                                        plan.published_at = plan.accepted_at or now
                                    
                                    plan.save()
                                    
                                    PlanStatusLog.objects.create(
                                        plan=plan,
                                        old_status=old_status,
                                        new_status=new_status,
                                        changed_by=None,
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
                                    
                                    updated_count += 1
                            except Exception as e:
                                error_msg = f'计划 {plan.plan_number} - {plan.name}: {str(e)}'
                                logger.error(error_msg, exc_info=True)
                                errors.append(error_msg)
                                if force:
                                    self.stdout.write(
                                        self.style.ERROR(f'  ✗ {error_msg} (继续处理...)')
                                    )
                                else:
                                    raise
                    
                    except Exception as e:
                        error_msg = f'计划 {plan.plan_number} - {plan.name}: {str(e)}'
                        logger.error(error_msg, exc_info=True)
                        errors.append(error_msg)
                        if not force:
                            raise
                
                if not dry_run:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'   迁移完成：→ published: {migrated_to_published} 个, '
                            f'→ in_progress: {migrated_to_in_progress} 个'
                        )
                    )
            else:
                self.stdout.write(self.style.SUCCESS('   ✓ 没有 accepted 状态的计划'))
            
            # 输出统计信息
            self.stdout.write('')
            self.stdout.write(self.style.SUCCESS('=' * 60))
            self.stdout.write(self.style.SUCCESS('更新完成统计：'))
            self.stdout.write(self.style.SUCCESS(f'  状态更新: {updated_count} 个计划'))
            if completed_count > 0:
                self.stdout.write(self.style.SUCCESS(f'  → completed: {completed_count} 个'))
            if overdue_count > 0:
                self.stdout.write(self.style.WARNING(f'  → 逾期标记: {overdue_count} 个'))
            
            if errors:
                self.stdout.write(self.style.ERROR(f'  错误: {len(errors)} 个'))
                for error in errors[:10]:
                    self.stdout.write(self.style.ERROR(f'    - {error}'))
                if len(errors) > 10:
                    self.stdout.write(
                        self.style.ERROR(f'    ... 还有 {len(errors) - 10} 个错误')
                    )
            
            self.stdout.write(self.style.SUCCESS('=' * 60))
            
            if dry_run:
                self.stdout.write(self.style.WARNING('\n这是试运行模式，未实际更新数据'))
                self.stdout.write(self.style.WARNING('运行不带 --dry-run 参数来执行实际更新'))
            else:
                # 验证更新结果
                remaining_accepted = Plan.objects.filter(status='accepted').count()
                if remaining_accepted > 0:
                    self.stdout.write(
                        self.style.WARNING(
                            f'\n警告：仍有 {remaining_accepted} 个计划状态为 accepted'
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.SUCCESS('\n✓ 所有计划状态已符合新的流转规则')
                    )
            
        except Exception as e:
            logger.error(f"状态更新失败: {str(e)}", exc_info=True)
            self.stdout.write(self.style.ERROR(f'更新失败：{str(e)}'))
            if not force:
                raise
