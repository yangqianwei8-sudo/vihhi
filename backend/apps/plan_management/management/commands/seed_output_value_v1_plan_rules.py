# -*- coding: utf-8 -*-
"""
V1 产值依据种子数据：创建/更新 OutputValueStage、OutputValueMilestone、MilestoneEvidenceRule（幂等）。
至少覆盖：生产阶段、咨询意见提交(0.30)、准备工作(0.02)；规则 CONSULT_OPINION_SUBMITTED → 咨询意见提交。
"""
from decimal import Decimal

from django.core.management.base import BaseCommand

from backend.apps.output_value_management.models import OutputValueStage, OutputValueMilestone
from backend.apps.plan_management.models import MilestoneEvidenceRule


# 阶段：生产阶段
STAGE_CODE = 'production'
STAGE_NAME = '生产阶段'
# 里程碑：咨询意见提交 30%、准备工作 2%
MILESTONES = [
    {'code': 'consult_opinion_submitted', 'name': '咨询意见提交', 'milestone_percentage': 30},
    {'code': 'preparation_work', 'name': '准备工作', 'milestone_percentage': 2},
]
# 规则：CONSULT_OPINION_SUBMITTED 事件 → 咨询意见提交 完成
CONSULT_RULE_EVENT_TYPES = ['CONSULT_OPINION_SUBMITTED']


class Command(BaseCommand):
    help = '创建/更新 V1 产值阶段、里程碑与计划证据规则（幂等），输出创建/更新数量'

    def handle(self, *args, **options):
        created_stages, updated_stages = 0, 0
        created_milestones, updated_milestones = 0, 0
        created_rules, updated_rules = 0, 0

        # 1) OutputValueStage：生产阶段
        stage, stage_created = OutputValueStage.objects.get_or_create(
            code=STAGE_CODE,
            defaults={
                'name': STAGE_NAME,
                'stage_type': 'production',
                'stage_percentage': Decimal('100'),
                'base_amount_type': 'contract_amount',
                'order': -1,
                'is_active': True,
            },
        )
        if stage_created:
            created_stages += 1
        else:
            updated = False
            if stage.name != STAGE_NAME:
                stage.name = STAGE_NAME
                updated = True
            if stage.stage_type != 'production':
                stage.stage_type = 'production'
                updated = True
            if stage.order != -1:
                stage.order = -1
                updated = True
            if stage.is_active is not True:
                stage.is_active = True
                updated = True
            if updated:
                stage.save()
                updated_stages += 1

        # 2) OutputValueMilestone：咨询意见提交、准备工作
        for idx, m in enumerate(MILESTONES):
            obj, created = OutputValueMilestone.objects.get_or_create(
                stage=stage,
                code=m['code'],
                defaults={
                    'name': m['name'],
                    'milestone_percentage': Decimal(str(m['milestone_percentage'])),
                    'order': idx,
                    'is_active': True,
                },
            )
            if created:
                created_milestones += 1
            else:
                if obj.name != m['name'] or obj.milestone_percentage != Decimal(str(m['milestone_percentage'])):
                    obj.name = m['name']
                    obj.milestone_percentage = Decimal(str(m['milestone_percentage']))
                    obj.save()
                    updated_milestones += 1

        # 3) MilestoneEvidenceRule：咨询意见提交 = CONSULT_OPINION_SUBMITTED
        rule, rule_created = MilestoneEvidenceRule.objects.get_or_create(
            milestone_code='consult_opinion_submitted',
            defaults={
                'required_event_types': CONSULT_RULE_EVENT_TYPES,
                'enabled': True,
            },
        )
        if rule_created:
            created_rules += 1
        else:
            if rule.required_event_types != CONSULT_RULE_EVENT_TYPES or rule.enabled is not True:
                rule.required_event_types = CONSULT_RULE_EVENT_TYPES
                rule.enabled = True
                rule.save()
                updated_rules += 1

        self.stdout.write(self.style.SUCCESS(
            'Seed done: stages created=%s updated=%s | milestones created=%s updated=%s | rules created=%s updated=%s'
            % (created_stages, updated_stages, created_milestones, updated_milestones, created_rules, updated_rules)
        ))
