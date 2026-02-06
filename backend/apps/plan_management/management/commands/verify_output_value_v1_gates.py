# -*- coding: utf-8 -*-
"""
上线验收：产值 V1 门禁强制验证。任一门禁失效则退出码非 0。
"""
import sys
from django.core.management.base import BaseCommand
from django.utils import timezone


class Command(BaseCommand):
    help = '验证 PlanOutputMilestoneCompletion 写入门禁、FactEvent 白名单与 record_fact_event 幂等，任一项失败则非 0 退出'

    def add_arguments(self, parser):
        parser.add_argument('--no-cleanup', action='store_true', help='不删除验证过程中创建的测试数据')

    def run_check(self, name, fn):
        try:
            fn()
            self.stdout.write(self.style.SUCCESS('[PASS] %s' % name))
            return True
        except Exception as e:
            self.stdout.write(self.style.ERROR('[FAIL] %s: %s' % (name, e)))
            return False

    def handle(self, *args, **options):
        no_cleanup = options.get('no_cleanup', False)
        ok = True

        # A. 直接写 PlanOutputMilestoneCompletion（不走 allow）应抛 PermissionError
        def check_completion_gate():
            from backend.apps.plan_management.models import PlanOutputMilestoneCompletion
            # 确保未设置允许写入
            from backend.apps.plan_management.models import _set_completion_write_allowed
            _set_completion_write_allowed(False)
            obj = PlanOutputMilestoneCompletion(
                opportunity_id=1,
                milestone_code='_verify_gate_nonexist',
                created_via='rule_engine',
                rule_code='_verify',
                rule_snapshot={},
            )
            try:
                obj.save()
            except PermissionError as e:
                if '仅允许由评估服务' in str(e) or 'evaluate_milestone_completion' in str(e):
                    return
            raise AssertionError('直接 save() 应抛 PermissionError')
        ok &= self.run_check('A. PlanOutputMilestoneCompletion 直写抛 PermissionError', check_completion_gate)

        # B. 通过 evaluate_milestone_completion 写完成记录应成功，且 created_via/rule_code/rule_snapshot 非空
        _verify_opp_id = 999998
        _verify_milestone_code = '_verify_gate_m'

        def check_evaluate_writes_audit():
            from backend.apps.plan_management.models import (
                PlanOutputMilestoneCompletion,
                MilestoneEvidenceRule,
            )
            from backend.apps.plan_management.services.fact_event import record_fact_event
            from backend.apps.plan_management.services.milestone_completion import evaluate_milestone_completion
            MilestoneEvidenceRule.objects.get_or_create(
                milestone_code=_verify_milestone_code,
                defaults={'required_event_types': ['CONSULT_OPINION_SUBMITTED'], 'enabled': True},
            )
            record_fact_event(
                'CONSULT_OPINION_SUBMITTED',
                ref_model='opportunity',
                ref_id=str(_verify_opp_id),
                source_app='verify_gates',
            )
            if not evaluate_milestone_completion(_verify_opp_id, _verify_milestone_code):
                raise AssertionError('evaluate_milestone_completion 应返回 True')
            c = PlanOutputMilestoneCompletion.objects.filter(
                opportunity_id=_verify_opp_id,
                milestone_code=_verify_milestone_code,
            ).first()
            if not c:
                raise AssertionError('完成记录应存在')
            if c.created_via != 'rule_engine':
                raise AssertionError('created_via 应为 rule_engine，实际: %s' % c.created_via)
            if not (c.rule_code or '').strip():
                raise AssertionError('rule_code 应非空')
            if not (c.rule_snapshot is not None and (c.rule_snapshot or {})):
                raise AssertionError('rule_snapshot 应非空')
            if not no_cleanup:
                c.delete()
                from backend.apps.plan_management.models import FactEvent
                FactEvent.objects.filter(ref_model='opportunity', ref_id=str(_verify_opp_id), source_app='verify_gates').delete()

        ok &= self.run_check('B. evaluate_milestone_completion 写入且审计字段齐全', check_evaluate_writes_audit)

        # C1. 直接 FactEvent.objects.create 必须抛 PermissionError（模型层阻断）
        def check_fact_event_direct_create_blocked():
            from backend.apps.plan_management.models import FactEvent
            try:
                FactEvent.objects.create(
                    type='CONSULT_OPINION_SUBMITTED',
                    ref_model='opportunity',
                    ref_id='0',
                    source_app='verify_gates',
                )
            except PermissionError as e:
                if 'record_fact_event' in str(e) or '禁止' in str(e):
                    return
                raise
            raise AssertionError('FactEvent.objects.create 直写应抛 PermissionError')
        ok &= self.run_check('C1. FactEvent 直写 create 抛 PermissionError', check_fact_event_direct_create_blocked)

        # C2. record_fact_event 必须可写成功
        def check_record_fact_event_writes():
            from backend.apps.plan_management.services.fact_event import record_fact_event
            from backend.apps.plan_management.models import FactEvent
            ev = record_fact_event(
                type='CONSULT_OPINION_SUBMITTED',
                ref_model='opportunity',
                ref_id='999997',
                source_app='verify_gates',
            )
            if not ev or not ev.pk:
                raise AssertionError('record_fact_event 应返回已保存实例')
            if not no_cleanup:
                # 删除需经 Manager；delete() 不触 save()，可直接删
                FactEvent.objects.filter(pk=ev.pk).delete()
        ok &= self.run_check('C2. record_fact_event 可写成功', check_record_fact_event_writes)

        # D. 白名单：不在白名单的 type 必须抛 ValueError
        def check_whitelist_enforced():
            from backend.apps.plan_management.services.fact_event import record_fact_event
            try:
                record_fact_event(
                    type='_NOT_IN_WHITELIST_',
                    ref_model='opportunity',
                    ref_id='0',
                    source_app='verify_gates',
                )
            except ValueError as e:
                if '白名单' in str(e) or 'whitelist' in str(e).lower():
                    return
                raise
            raise AssertionError('不在白名单的 type 应抛 ValueError')
        ok &= self.run_check('D. record_fact_event 非白名单 type 抛 ValueError', check_whitelist_enforced)

        # E. 幂等：相同 idempotency_key 重复写入返回同一条记录（id 相同）
        def check_idempotency():
            from backend.apps.plan_management.services.fact_event import record_fact_event
            from backend.apps.plan_management.models import FactEvent
            key = 'verify_gate_idem_%s' % timezone.now().timestamp()
            ev1 = record_fact_event(
                type='CONSULT_OPINION_SUBMITTED',
                ref_model='opportunity',
                ref_id='999996',
                source_app='verify_gates',
                idempotency_key=key,
            )
            ev2 = record_fact_event(
                type='CONSULT_OPINION_SUBMITTED',
                ref_model='opportunity',
                ref_id='999996',
                source_app='verify_gates',
                idempotency_key=key,
            )
            if ev1.id != ev2.id:
                raise AssertionError('相同 idempotency_key 应返回同一条记录，id1=%s id2=%s' % (ev1.id, ev2.id))
            if not no_cleanup:
                FactEvent.objects.filter(pk=ev1.pk).delete()
        ok &= self.run_check('E. record_fact_event 幂等（同 idempotency_key 同 id）', check_idempotency)

        if ok:
            self.stdout.write(self.style.SUCCESS('All gate checks passed.'))
            sys.exit(0)
        else:
            self.stdout.write(self.style.ERROR('One or more gate checks failed.'))
            sys.exit(1)
