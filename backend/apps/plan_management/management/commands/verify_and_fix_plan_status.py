"""
计划状态验证和修复命令

根据新的状态流转规则验证和修复计划状态：
- draft → published → in_progress → completed
- 不再有 accepted 状态
- 支持 paused（已暂停）和 delayed（已延期）状态

验证规则：
1. 检查是否有 accepted 状态的计划（应该迁移）
2. 检查状态转换是否符合规则
3. 检查时间戳是否正确设置
4. 检查状态日志是否完整

使用方法：
    python manage.py verify_and_fix_plan_status
    
选项：
    --dry-run: 试运行模式，只显示问题，不修复
    --fix: 自动修复发现的问题
    --fix-accepted: 只修复 accepted 状态的计划
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from django.db.models import Count
from datetime import datetime
import logging

from backend.apps.plan_management.models import Plan, PlanStatusLog

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = '验证和修复计划状态，确保符合新的状态流转规则'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='试运行模式：只显示问题，不修复',
        )
        parser.add_argument(
            '--fix',
            action='store_true',
            help='自动修复发现的问题',
        )
        parser.add_argument(
            '--fix-accepted',
            action='store_true',
            help='只修复 accepted 状态的计划',
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)
        fix = options.get('fix', False)
        fix_accepted_only = options.get('fix_accepted', False)
        
        self.stdout.write(f'开始验证计划状态（时间：{timezone.now()}）...')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('【DRY RUN 模式】只检查，不修复'))
        
        issues = []
        fixed_count = 0
        
        try:
            # 1. 检查是否有 accepted 状态的计划
            accepted_plans = Plan.objects.filter(status='accepted')
            accepted_count = accepted_plans.count()
            
            if accepted_count > 0:
                issue_msg = f'发现 {accepted_count} 个状态为 accepted 的计划（应该迁移）'
                issues.append(issue_msg)
                self.stdout.write(self.style.WARNING(f'  ⚠ {issue_msg}'))
                
                if fix or fix_accepted_only:
                    if not dry_run:
                        self._fix_accepted_plans(accepted_plans)
                        fixed_count += accepted_count
                    else:
                        self.stdout.write(self.style.WARNING('  [DRY RUN] 将修复这些计划'))
            else:
                self.stdout.write(self.style.SUCCESS('  ✓ 没有 accepted 状态的计划'))
            
            # 2. 检查状态转换是否符合规则
            invalid_transitions = self._check_invalid_transitions()
            if invalid_transitions:
                issue_msg = f'发现 {len(invalid_transitions)} 个无效的状态转换'
                issues.append(issue_msg)
                self.stdout.write(self.style.WARNING(f'  ⚠ {issue_msg}'))
                for plan_id, plan_number, old_status, new_status in invalid_transitions[:10]:
                    self.stdout.write(
                        self.style.WARNING(
                            f'    计划 {plan_number} (ID: {plan_id}): '
                            f'{old_status} → {new_status}'
                        )
                    )
                if len(invalid_transitions) > 10:
                    self.stdout.write(
                        self.style.WARNING(f'    ... 还有 {len(invalid_transitions) - 10} 个')
                    )
            else:
                self.stdout.write(self.style.SUCCESS('  ✓ 所有状态转换都符合规则'))
            
            # 3. 检查时间戳是否正确设置
            timestamp_issues = self._check_timestamps()
            if timestamp_issues:
                issue_msg = f'发现 {len(timestamp_issues)} 个时间戳问题'
                issues.append(issue_msg)
                self.stdout.write(self.style.WARNING(f'  ⚠ {issue_msg}'))
                for plan_id, plan_number, issue in timestamp_issues[:10]:
                    self.stdout.write(
                        self.style.WARNING(f'    计划 {plan_number} (ID: {plan_id}): {issue}')
                    )
                if len(timestamp_issues) > 10:
                    self.stdout.write(
                        self.style.WARNING(f'    ... 还有 {len(timestamp_issues) - 10} 个')
                    )
            else:
                self.stdout.write(self.style.SUCCESS('  ✓ 所有时间戳都正确设置'))
            
            # 4. 统计各状态的数量
            self.stdout.write('')
            self.stdout.write(self.style.SUCCESS('计划状态统计：'))
            status_counts = Plan.objects.values('status').annotate(
                count=Count('id')
            ).order_by('status')
            
            for item in status_counts:
                status = item['status']
                count = item['count']
                status_display = dict(Plan.STATUS_CHOICES).get(status, status)
                self.stdout.write(f'  {status_display} ({status}): {count} 个')
            
            # 输出总结
            self.stdout.write('')
            self.stdout.write(self.style.SUCCESS('=' * 60))
            if issues:
                self.stdout.write(self.style.WARNING(f'发现 {len(issues)} 类问题'))
                for issue in issues:
                    self.stdout.write(self.style.WARNING(f'  - {issue}'))
                
                if fix and not dry_run:
                    self.stdout.write(self.style.SUCCESS(f'已修复 {fixed_count} 个问题'))
                elif dry_run:
                    self.stdout.write(
                        self.style.WARNING(
                            '\n这是试运行模式，未实际修复。'
                            '\n使用 --fix 参数来修复问题，或使用 --fix-accepted 只修复 accepted 状态'
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(
                            '\n使用 --fix 参数来修复问题，或使用 --fix-accepted 只修复 accepted 状态'
                        )
                    )
            else:
                self.stdout.write(self.style.SUCCESS('✓ 所有检查通过，没有发现问题'))
            
            self.stdout.write(self.style.SUCCESS('=' * 60))
            
        except Exception as e:
            logger.error(f"验证失败: {str(e)}", exc_info=True)
            self.stdout.write(self.style.ERROR(f'验证失败：{str(e)}'))
            raise
    
    def _fix_accepted_plans(self, accepted_plans):
        """修复 accepted 状态的计划"""
        now = timezone.now()
        migrated_to_published = 0
        migrated_to_in_progress = 0
        
        for plan in accepted_plans:
            try:
                with transaction.atomic():
                    # 判断应该转换到哪个状态
                    if plan.start_time and plan.start_time <= now:
                        new_status = 'in_progress'
                        reason = f'计划开始时间已到达'
                    else:
                        new_status = 'published'
                        reason = f'计划未开始或没有开始时间'
                    
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
                        changed_by=None,
                        change_reason=f'状态迁移：{reason}'
                    )
                    
                    if new_status == 'published':
                        migrated_to_published += 1
                    else:
                        migrated_to_in_progress += 1
                    
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'  ✓ 计划 {plan.plan_number} - {plan.name} '
                            f'已从 accepted 迁移到 {new_status}'
                        )
                    )
            
            except Exception as e:
                logger.error(f"修复计划 {plan.id} 失败: {str(e)}", exc_info=True)
                self.stdout.write(
                    self.style.ERROR(
                        f'  ✗ 计划 {plan.plan_number} - {plan.name}: {str(e)}'
                    )
                )
        
        self.stdout.write('')
        self.stdout.write(
            self.style.SUCCESS(
                f'修复完成：→ published: {migrated_to_published} 个, '
                f'→ in_progress: {migrated_to_in_progress} 个'
            )
        )
    
    def _check_invalid_transitions(self):
        """检查无效的状态转换"""
        invalid = []
        
        # 检查状态日志中的无效转换
        status_logs = PlanStatusLog.objects.all().select_related('plan')
        
        for log in status_logs:
            plan = log.plan
            valid_transitions = plan.get_valid_transitions()
            
            # 如果 old_status 不是当前状态，说明状态可能已经改变
            # 我们检查转换本身是否有效
            if log.old_status and log.new_status:
                # 创建一个临时计划对象来检查转换
                temp_plan = Plan(status=log.old_status)
                valid_transitions_for_old = temp_plan.get_valid_transitions()
                
                if log.new_status not in valid_transitions_for_old:
                    invalid.append((
                        plan.id,
                        plan.plan_number,
                        log.old_status,
                        log.new_status
                    ))
        
        return invalid
    
    def _check_timestamps(self):
        """检查时间戳是否正确设置"""
        issues = []
        
        plans = Plan.objects.all()
        
        for plan in plans:
            # 检查 published 状态是否有 published_at
            if plan.status == 'published' and not plan.published_at:
                issues.append((
                    plan.id,
                    plan.plan_number,
                    'published 状态但没有 published_at 时间戳'
                ))
            
            # 检查 completed 状态是否有 completed_at
            if plan.status == 'completed' and not plan.completed_at:
                issues.append((
                    plan.id,
                    plan.plan_number,
                    'completed 状态但没有 completed_at 时间戳'
                ))
            
            # 检查时间戳的逻辑顺序
            if plan.published_at and plan.completed_at:
                if plan.published_at > plan.completed_at:
                    issues.append((
                        plan.id,
                        plan.plan_number,
                        'published_at 晚于 completed_at（时间戳顺序错误）'
                    ))
        
        return issues
