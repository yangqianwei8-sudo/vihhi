"""
P2-1 模型统一校验脚本

用于验证模型统一后的数据完整性：
- Plan/StrategicGoal 的 status 分布
- Plan/StrategicGoal 的 level 分布
- 异常数据检查（level 为空、status 不在枚举内）
"""

from django.core.management.base import BaseCommand
from django.db.models import Count, Q
from django.db import connection

from backend.apps.plan_management.models import Plan, StrategicGoal


class Command(BaseCommand):
    help = 'P2-1 模型统一校验：检查 status/level 分布和异常数据'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS('P2-1 模型统一校验报告'))
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write('')

        # ========== Plan 模型统计 ==========
        self.stdout.write(self.style.WARNING('【Plan 模型统计】'))
        self.stdout.write('-' * 60)
        
        # Plan status 分布
        plan_status_dist = Plan.objects.values('status').annotate(
            count=Count('id')
        ).order_by('status')
        
        self.stdout.write('状态分布：')
        total_plans = 0
        for item in plan_status_dist:
            self.stdout.write(f"  {item['status']:20s}: {item['count']:5d}")
            total_plans += item['count']
        self.stdout.write(f"  总计: {total_plans}")
        self.stdout.write('')

        # Plan level 分布
        plan_level_dist = Plan.objects.values('level').annotate(
            count=Count('id')
        ).order_by('level')
        
        self.stdout.write('层级分布：')
        for item in plan_level_dist:
            level_display = item['level'] if item['level'] else '(空)'
            self.stdout.write(f"  {level_display:20s}: {item['count']:5d}")
        self.stdout.write('')

        # Plan 异常检查
        plan_null_level = Plan.objects.filter(level__isnull=True).count()
        plan_invalid_status = Plan.objects.exclude(
            status__in=['draft', 'published', 'accepted', 'in_progress', 'completed', 'cancelled']
        ).count()
        
        self.stdout.write('异常检查：')
        if plan_null_level > 0:
            self.stdout.write(self.style.ERROR(f"  ⚠ level 为空的记录: {plan_null_level}"))
        else:
            self.stdout.write(self.style.SUCCESS(f"  ✓ level 为空: 0"))
        
        if plan_invalid_status > 0:
            invalid_statuses = Plan.objects.exclude(
                status__in=['draft', 'published', 'accepted', 'in_progress', 'completed', 'cancelled']
            ).values_list('status', flat=True).distinct()
            self.stdout.write(self.style.ERROR(f"  ⚠ status 不在枚举内的记录: {plan_invalid_status}"))
            self.stdout.write(self.style.ERROR(f"    异常状态值: {', '.join(invalid_statuses)}"))
        else:
            self.stdout.write(self.style.SUCCESS(f"  ✓ status 不在枚举内: 0"))
        
        self.stdout.write('')

        # ========== StrategicGoal 模型统计 ==========
        self.stdout.write(self.style.WARNING('【StrategicGoal 模型统计】'))
        self.stdout.write('-' * 60)
        
        # Goal status 分布
        goal_status_dist = StrategicGoal.objects.values('status').annotate(
            count=Count('id')
        ).order_by('status')
        
        self.stdout.write('状态分布：')
        total_goals = 0
        for item in goal_status_dist:
            self.stdout.write(f"  {item['status']:20s}: {item['count']:5d}")
            total_goals += item['count']
        self.stdout.write(f"  总计: {total_goals}")
        self.stdout.write('')

        # Goal level 分布
        goal_level_dist = StrategicGoal.objects.values('level').annotate(
            count=Count('id')
        ).order_by('level')
        
        self.stdout.write('层级分布：')
        for item in goal_level_dist:
            level_display = item['level'] if item['level'] else '(空)'
            self.stdout.write(f"  {level_display:20s}: {item['count']:5d}")
        self.stdout.write('')

        # Goal 异常检查
        goal_null_level = StrategicGoal.objects.filter(level__isnull=True).count()
        goal_invalid_status = StrategicGoal.objects.exclude(
            status__in=['draft', 'published', 'accepted', 'in_progress', 'completed', 'cancelled']
        ).count()
        
        self.stdout.write('异常检查：')
        if goal_null_level > 0:
            self.stdout.write(self.style.ERROR(f"  ⚠ level 为空的记录: {goal_null_level}"))
        else:
            self.stdout.write(self.style.SUCCESS(f"  ✓ level 为空: 0"))
        
        if goal_invalid_status > 0:
            invalid_statuses = StrategicGoal.objects.exclude(
                status__in=['draft', 'published', 'accepted', 'in_progress', 'completed', 'cancelled']
            ).values_list('status', flat=True).distinct()
            self.stdout.write(self.style.ERROR(f"  ⚠ status 不在枚举内的记录: {goal_invalid_status}"))
            self.stdout.write(self.style.ERROR(f"    异常状态值: {', '.join(invalid_statuses)}"))
        else:
            self.stdout.write(self.style.SUCCESS(f"  ✓ status 不在枚举内: 0"))
        
        self.stdout.write('')

        # ========== 时间戳字段检查 ==========
        self.stdout.write(self.style.WARNING('【时间戳字段检查】'))
        self.stdout.write('-' * 60)
        
        # Plan 时间戳
        plan_published_count = Plan.objects.filter(published_at__isnull=False).count()
        plan_accepted_count = Plan.objects.filter(accepted_at__isnull=False).count()
        plan_completed_count = Plan.objects.filter(completed_at__isnull=False).count()
        
        self.stdout.write('Plan 时间戳：')
        self.stdout.write(f"  published_at 已填充: {plan_published_count}/{total_plans}")
        self.stdout.write(f"  accepted_at 已填充: {plan_accepted_count}/{total_plans}")
        self.stdout.write(f"  completed_at 已填充: {plan_completed_count}/{total_plans}")
        self.stdout.write('')

        # Goal 时间戳
        goal_published_count = StrategicGoal.objects.filter(published_at__isnull=False).count()
        goal_accepted_count = StrategicGoal.objects.filter(accepted_at__isnull=False).count()
        goal_completed_count = StrategicGoal.objects.filter(completed_at__isnull=False).count()
        
        self.stdout.write('StrategicGoal 时间戳：')
        self.stdout.write(f"  published_at 已填充: {goal_published_count}/{total_goals}")
        self.stdout.write(f"  accepted_at 已填充: {goal_accepted_count}/{total_goals}")
        self.stdout.write(f"  completed_at 已填充: {goal_completed_count}/{total_goals}")
        self.stdout.write('')

        # ========== owner 字段检查 ==========
        self.stdout.write(self.style.WARNING('【owner 字段检查】'))
        self.stdout.write('-' * 60)
        
        plan_owner_count = Plan.objects.filter(owner__isnull=False).count()
        goal_owner_count = StrategicGoal.objects.filter(owner__isnull=False).count()
        
        self.stdout.write(f"Plan owner 已填充: {plan_owner_count}/{total_plans}")
        self.stdout.write(f"StrategicGoal owner 已填充: {goal_owner_count}/{total_goals}")
        self.stdout.write('')

        # ========== 安全断言（P2-1 收口）==========
        self.stdout.write(self.style.WARNING('【安全断言检查】'))
        self.stdout.write('-' * 60)
        
        warnings = []
        
        # 检查 level 字段是否为空（警告级别）
        if plan_null_level > 0:
            warnings.append(f'Plan level 为空: {plan_null_level} 条记录（建议检查数据迁移）')
        
        if goal_null_level > 0:
            warnings.append(f'StrategicGoal level 为空: {goal_null_level} 条记录（建议检查数据迁移）')
        
        if warnings:
            for warning in warnings:
                self.stdout.write(self.style.WARNING(f'  ⚠ {warning}'))
        else:
            self.stdout.write(self.style.SUCCESS('  ✓ level 字段完整性检查通过'))
        
        self.stdout.write('')

        # ========== 总结 ==========
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS('校验完成'))
        self.stdout.write(self.style.SUCCESS('=' * 60))
        
        # 汇总异常
        total_issues = plan_null_level + plan_invalid_status + goal_null_level + goal_invalid_status
        if total_issues > 0:
            self.stdout.write(self.style.ERROR(f'\n发现 {total_issues} 个异常项，请检查上述报告'))
            return 1
        else:
            self.stdout.write(self.style.SUCCESS('\n✓ 未发现异常'))
            if warnings:
                self.stdout.write(self.style.WARNING(f'\n⚠ 发现 {len(warnings)} 个警告项，建议关注'))
            return 0

