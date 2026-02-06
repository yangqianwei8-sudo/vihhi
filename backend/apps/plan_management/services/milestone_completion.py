# -*- coding: utf-8 -*-
"""
产值里程碑完成度评估：根据 FactEvent + MilestoneEvidenceRule 更新 PlanOutputMilestoneCompletion。
业务模块只写 FactEvent；本模块评估后写完成状态；产值模块只读完成状态。
"""
import logging
from django.utils import timezone

logger = logging.getLogger(__name__)


def evaluate_milestone_completion(opportunity_id: int, milestone_code: str, dry_run: bool = False) -> bool:
    """
    根据证据规则与 FactEvent 评估某商机下某产值里程碑是否完成；
    若满足规则且非 dry_run 则创建/更新 PlanOutputMilestoneCompletion 并返回 True。
    约定：FactEvent 关联商机时 ref_model='opportunity', ref_id=str(opportunity_id)。
    """
    report = evaluate_milestone_completion_with_report(opportunity_id, milestone_code, dry_run=dry_run)
    return report['written'] if not dry_run else report['would_write']


def evaluate_milestone_completion_with_report(opportunity_id: int, milestone_code: str, dry_run: bool = False):
    """
    评估并返回报告：rule_matched, event_counts (dict type -> count), would_write, written。
    dry_run=True 时不落库，written 恒为 False。
    """
    from backend.apps.plan_management.models import (
        MilestoneEvidenceRule,
        PlanOutputMilestoneCompletion,
        FactEvent,
    )
    report = {
        'rule_matched': False,
        'event_counts': {},
        'would_write': False,
        'written': False,
    }
    rule = MilestoneEvidenceRule.objects.filter(
        milestone_code=milestone_code,
        enabled=True,
    ).first()
    if not rule or not rule.required_event_types:
        return report
    report['rule_matched'] = True
    required = list(rule.required_event_types)
    for event_type in required:
        cnt = FactEvent.objects.filter(
            type=event_type,
            ref_model='opportunity',
            ref_id=str(opportunity_id),
        ).count()
        report['event_counts'][event_type] = cnt
    if any(report['event_counts'].get(t, 0) < 1 for t in required):
        return report
    report['would_write'] = True
    if dry_run:
        return report
    from backend.apps.plan_management.models import allow_plan_completion_write, reset_plan_completion_write
    snapshot = {
        'evaluated_at': timezone.now().isoformat(),
        'required_event_types': required,
    }
    rule_snapshot = {
        'milestone_code': rule.milestone_code,
        'required_event_types': rule.required_event_types,
        'rule_id': getattr(rule, 'pk', None),
    }
    token = allow_plan_completion_write()
    try:
        obj, created = PlanOutputMilestoneCompletion.objects.update_or_create(
            opportunity_id=opportunity_id,
            milestone_code=milestone_code,
            defaults={
                'completed_at': timezone.now(),
                'evidence_snapshot': snapshot,
                'created_via': 'rule_engine',
                'rule_code': rule.milestone_code,
                'rule_snapshot': rule_snapshot,
            },
        )
    finally:
        reset_plan_completion_write(token)
    report['written'] = True
    if created:
        logger.info('PlanOutputMilestoneCompletion created: opportunity_id=%s, milestone_code=%s', opportunity_id, milestone_code)
    return report


def get_evaluation_candidates(opportunity_id=None, milestone_code=None, hours=24):
    """
    返回待评估的 (opportunity_id, milestone_code) 列表。
    若指定 opportunity_id，只返回该商机（及可选 milestone_code）；否则最近 hours 内有 FactEvent 的商机 × 所有启用规则。
    """
    from datetime import timedelta
    from backend.apps.plan_management.models import FactEvent, MilestoneEvidenceRule

    if opportunity_id is not None:
        opp_ids = [opportunity_id]
    else:
        since = timezone.now() - timedelta(hours=hours)
        events = FactEvent.objects.filter(occurred_at__gte=since, ref_model='opportunity').values_list('ref_id', flat=True).distinct()
        opp_ids = [int(x) for x in events if x and str(x).isdigit()]

    if milestone_code is not None:
        codes = [milestone_code]
    else:
        codes = list(MilestoneEvidenceRule.objects.filter(enabled=True).values_list('milestone_code', flat=True).distinct())

    return [(opp_id, code) for opp_id in opp_ids for code in codes]


def evaluate_recent_fact_events(hours: int = 24, opportunity_id=None, milestone_code=None):
    """
    批量评估；若传 opportunity_id / milestone_code 则只评估指定范围。
    """
    candidates = get_evaluation_candidates(opportunity_id=opportunity_id, milestone_code=milestone_code, hours=hours)
    evaluated = 0
    for opp_id, code in candidates:
        if evaluate_milestone_completion(opp_id, code, dry_run=False):
            evaluated += 1
    return evaluated
