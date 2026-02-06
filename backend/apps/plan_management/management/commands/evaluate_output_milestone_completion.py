# -*- coding: utf-8 -*-
"""
批量评估产值里程碑完成：根据 FactEvent + 规则更新 PlanOutputMilestoneCompletion（幂等）。
支持指定商机/里程碑、dry-run 仅打印不落库。
"""
from django.core.management.base import BaseCommand
from backend.apps.plan_management.services.milestone_completion import (
    get_evaluation_candidates,
    evaluate_milestone_completion_with_report,
    evaluate_recent_fact_events,
)


class Command(BaseCommand):
    help = '根据 FactEvent 与 MilestoneEvidenceRule 评估并写入 PlanOutputMilestoneCompletion（支持 --opportunity-id/--milestone-code/--dry-run）'

    def add_arguments(self, parser):
        parser.add_argument('--hours', type=int, default=24, help='未指定商机时，统计最近多少小时内的证据事件，默认 24')
        parser.add_argument('--opportunity-id', type=int, default=None, help='只评估指定商机')
        parser.add_argument('--milestone-code', type=str, default=None, help='只评估指定里程碑编码')
        parser.add_argument('--dry-run', action='store_true', help='只打印将要写入的完成记录，不落库')

    def handle(self, *args, **options):
        opportunity_id = options.get('opportunity_id')
        milestone_code = options.get('milestone_code')
        dry_run = options.get('dry_run', False)
        hours = options.get('hours', 24)

        if opportunity_id is not None or milestone_code is not None:
            # 单商机/单里程碑模式：逐条评估并输出报告
            candidates = get_evaluation_candidates(
                opportunity_id=opportunity_id,
                milestone_code=milestone_code,
                hours=hours,
            )
            if not candidates:
                self.stdout.write('No (opportunity_id, milestone_code) to evaluate for given filters.')
                return
            written_count = 0
            for opp_id, code in candidates:
                report = evaluate_milestone_completion_with_report(opp_id, code, dry_run=dry_run)
                line = (
                    'opportunity_id=%s milestone_code=%s | rule_matched=%s event_counts=%s would_write=%s'
                    % (opp_id, code, report['rule_matched'], report['event_counts'], report['would_write'])
                )
                if report['written']:
                    line += ' written=yes'
                    written_count += 1
                elif report['would_write'] and dry_run:
                    line += ' (dry-run: would write)'
                self.stdout.write(line)
            if dry_run:
                self.stdout.write(self.style.WARNING('Dry-run: no PlanOutputMilestoneCompletion written.'))
            else:
                self.stdout.write(self.style.SUCCESS('Wrote %s PlanOutputMilestoneCompletion(s).' % written_count))
            return

        # 批量模式：按小时
        n = evaluate_recent_fact_events(hours=hours)
        self.stdout.write(self.style.SUCCESS(
            'Evaluated %s milestone completion(s) for events in last %s hour(s).' % (n, hours)
        ))
