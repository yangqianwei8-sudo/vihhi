"""
检测计划不作为并生成 PlanInactivityLog 记录

规则（最小实现）：
1. 当前时间 > plan.end_time
2. plan.status ≠ completed
3. 最近 N 天（默认 7 天）：
   - 无状态变更（PlanStatusLog）
   - 无进度记录（PlanProgressRecord）
   - 无延期申请（PlanAdjustment）
4. 若该时间段已存在不作为记录，则不重复生成
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from django.db.models import Q, Max

from backend.apps.plan_management.models import (
    Plan,
    PlanStatusLog,
    PlanProgressRecord,
    PlanAdjustment,
    PlanInactivityLog,
)


class Command(BaseCommand):
    help = '检测计划不作为并生成 PlanInactivityLog 记录'

    def add_arguments(self, parser):
        parser.add_argument(
            '--silent-days',
            type=int,
            default=7,
            help='检测最近 N 天无操作（默认 7 天）',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='只检测，不生成记录',
        )

    def handle(self, *args, **options):
        silent_days = options['silent_days']
        dry_run = options['dry_run']
        
        now = timezone.now()
        silent_threshold = now - timedelta(days=silent_days)
        
        # 1. 找出所有逾期且未完成的计划
        overdue_plans = Plan.objects.filter(
            end_time__lt=now,
            status__in=['draft', 'in_progress'],  # 排除 completed 和 cancelled
        ).select_related('responsible_person')
        
        self.stdout.write(f'找到 {overdue_plans.count()} 个逾期计划')
        
        generated_count = 0
        skipped_count = 0
        
        for plan in overdue_plans:
            # 2. 检查最近 N 天是否有任何操作
            has_status_change = PlanStatusLog.objects.filter(
                plan=plan,
                changed_time__gte=silent_threshold,
            ).exists()
            
            has_progress_record = PlanProgressRecord.objects.filter(
                plan=plan,
                recorded_time__gte=silent_threshold,
            ).exists()
            
            has_adjustment = PlanAdjustment.objects.filter(
                plan=plan,
                created_time__gte=silent_threshold,
            ).exists()
            
            # 如果最近 N 天有任何操作，跳过
            if has_status_change or has_progress_record or has_adjustment:
                skipped_count += 1
                continue
            
            # 3. 确定检测区间
            # 区间开始：最近一次操作时间，或计划截止时间，取较晚者
            last_status_time = PlanStatusLog.objects.filter(
                plan=plan
            ).aggregate(Max('changed_time'))['changed_time__max']
            
            last_progress_time = PlanProgressRecord.objects.filter(
                plan=plan
            ).aggregate(Max('recorded_time'))['recorded_time__max']
            
            last_action_time = max(
                filter(None, [last_status_time, last_progress_time, plan.end_time])
            ) if any([last_status_time, last_progress_time]) else plan.end_time
            
            period_start = max(last_action_time, plan.end_time)
            period_end = now
            
            # 4. 检查是否已存在重叠时间段的不作为记录（防止重复生成）
            # 区间重叠条件：新区间开始 < 旧区间结束 且 新区间结束 > 旧区间开始
            existing_log = PlanInactivityLog.objects.filter(
                plan=plan,
                reason='overdue_and_silent',
                period_start__lt=period_end,
                period_end__gt=period_start,
            ).exists()
            
            if existing_log:
                skipped_count += 1
                continue
            
            # 5. 生成快照
            snapshot = {
                'plan_number': plan.plan_number,
                'plan_name': plan.name,
                'status': plan.status,
                'end_time': plan.end_time.isoformat(),
                'responsible_person_id': plan.responsible_person_id,
                'responsible_person_username': plan.responsible_person.username if plan.responsible_person else None,
                'detected_at': now.isoformat(),
            }
            
            # 6. 生成不作为记录
            if not dry_run:
                try:
                    PlanInactivityLog.objects.create(
                        plan=plan,
                        detected_at=now,
                        period_start=period_start,
                        period_end=period_end,
                        reason='overdue_and_silent',
                        reason_detail=(
                            f'计划已逾期 {(now - plan.end_time).days} 天，'
                            f'且在 {period_start.strftime("%Y-%m-%d")} 至 {period_end.strftime("%Y-%m-%d")} '
                            f'期间（{silent_days} 天）无任何状态变更、进度记录或延期申请'
                        ),
                        snapshot=snapshot,
                        is_confirmed=True,  # 系统自动确认的不作为记录
                    )
                    generated_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'✅ 已生成不作为记录: {plan.plan_number} - {plan.name}'
                        )
                    )
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(
                            f'❌ 生成记录失败: {plan.plan_number} - {str(e)}'
                        )
                    )
            else:
                generated_count += 1
                self.stdout.write(
                    self.style.WARNING(
                        f'[DRY-RUN] 将生成不作为记录: {plan.plan_number} - {plan.name}'
                    )
                )
        
        # 输出统计
        self.stdout.write('')
        self.stdout.write('=' * 50)
        if dry_run:
            self.stdout.write(self.style.WARNING(f'[DRY-RUN] 将生成 {generated_count} 条不作为记录'))
        else:
            self.stdout.write(self.style.SUCCESS(f'✅ 成功生成 {generated_count} 条不作为记录'))
        self.stdout.write(f'⏭️  跳过 {skipped_count} 个计划（有操作或已存在记录）')
