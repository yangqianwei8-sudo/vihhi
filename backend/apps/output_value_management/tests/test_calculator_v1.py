"""
产值管理 V1 计算内核单元测试
依据：docs/output_value_v1_execution.md
覆盖：calculate_dynamic_output、is_milestone_completed 的常见场景与边界情况。

运行前提：测试库需已完整迁移（含 production_management、output_value_management 等），例如：
  python manage.py test backend.apps.output_value_management.tests.test_calculator_v1 --keepdb
"""
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone

from backend.apps.output_value_management.services.calculator_v1 import (
    calculate_dynamic_output,
    is_milestone_completed,
    _confidence,
)
from backend.apps.opportunity_management.models import BusinessOpportunity
from backend.apps.customer_management.models import Client
from backend.apps.output_value_management.models import (
    OutputValueStage,
    OutputValueMilestone,
    OutputValueEvent,
    OutputValuePolicy,
)
# 里程碑完成度只读计划管理；测试通过 record_fact_event + evaluate_milestone_completion 构造“已完成”
from backend.apps.plan_management.models import PlanOutputMilestoneCompletion, MilestoneEvidenceRule
from backend.apps.plan_management.services.fact_event import record_fact_event
from backend.apps.plan_management.services.milestone_completion import evaluate_milestone_completion

try:
    from django.contrib.auth import get_user_model
    User = get_user_model()
except Exception:
    User = None


def _make_user():
    if User is None:
        return None
    return User.objects.create_user(
        username='test_output_user_%s' % timezone.now().timestamp(),
        password='test123',
        is_staff=False,
    )


def _make_client():
    return Client.objects.create(name='测试客户-产值', is_active=True)


def _make_opportunity(client, user, **kwargs):
    return BusinessOpportunity.objects.create(
        name=kwargs.get('name', '测试商机'),
        client=client,
        business_manager=user,
        created_by=user,
        status=kwargs.get('status', 'potential'),
        estimated_amount=kwargs.get('estimated_amount', Decimal('0')),
        success_probability=kwargs.get('success_probability', 10),
        is_active=True,
        approval_status='pending',
        **{k: v for k, v in kwargs.items() if k not in ('name', 'status', 'estimated_amount', 'success_probability')}
    )


def _make_stage(code='production', name='生产阶段', order=0):
    return OutputValueStage.objects.create(
        name=name,
        code=code,
        stage_type='production',
        stage_percentage=Decimal('100'),
        base_amount_type='contract_amount',
        order=order,
        is_active=True,
    )


def _make_milestone(stage, code='m1', name='里程碑一', milestone_percentage=30):
    return OutputValueMilestone.objects.create(
        stage=stage,
        name=name,
        code=code,
        milestone_percentage=Decimal(str(milestone_percentage)),
        order=0,
        is_active=True,
    )


def _make_event(milestone, code='e1', name='事件一', event_percentage=100):
    return OutputValueEvent.objects.create(
        milestone=milestone,
        name=name,
        code=code,
        event_percentage=Decimal(str(event_percentage)),
        responsible_role_code='project_manager',
        trigger_condition='',
        order=0,
        is_active=True,
    )


class CalculatorV1MinimalTest(TestCase):
    """不依赖完整 DB 链的纯逻辑与边界测试。"""

    def setUp(self):
        _ensure_output_value_policy()

    def test_calculate_dynamic_output_missing_opportunity(self):
        """边界：无商机时返回 0 与 low。"""
        out = calculate_dynamic_output(999999)
        self.assertIn('dynamic_output', out)
        self.assertIn('stage', out)
        self.assertIn('milestone', out)
        self.assertIn('milestone_weight', out)
        self.assertIn('confidence', out)
        self.assertEqual(out['dynamic_output'], Decimal('0'))
        self.assertEqual(out['confidence'], 'low')

    def test_calculate_dynamic_output_return_structure(self):
        """常见：返回结构必须包含文档规定的五字段。"""
        out = calculate_dynamic_output(999999)
        self.assertEqual(
            set(out.keys()),
            {'dynamic_output', 'stage', 'milestone', 'milestone_weight', 'confidence'},
        )

    def test_confidence_rules(self):
        """文档 八：confidence 判定规则 high/medium/low，阈值 0.30 来源于 policy。"""
        threshold = Decimal('0.30')
        self.assertEqual(_confidence(Decimal('0'), threshold), 'low')
        self.assertEqual(_confidence(Decimal('0.01'), threshold), 'medium')
        self.assertEqual(_confidence(Decimal('0.29'), threshold), 'medium')
        self.assertEqual(_confidence(threshold, threshold), 'high')
        self.assertEqual(_confidence(Decimal('0.30'), threshold), 'high')
        self.assertEqual(_confidence(Decimal('1'), threshold), 'high')

    def test_is_milestone_completed_milestone_not_found(self):
        """边界：里程碑不存在 → False。"""
        self.assertFalse(is_milestone_completed(999999, 1))

    def test_is_milestone_completed_opportunity_not_found(self):
        """边界：商机不存在 → False。"""
        stage = _make_stage()
        m = _make_milestone(stage)
        self.assertFalse(is_milestone_completed(m.id, 999999))


def _ensure_output_value_policy():
    """确保存在一条 enabled 的产值口径配置，供计算与测试使用。"""
    if not OutputValuePolicy.objects.filter(enabled=True).exists():
        OutputValuePolicy.objects.create(
            name='V1 测试默认口径',
            service_type_weights={
                '转化阶段': '0.02', '合同阶段': '0.02', '生产阶段': '0.10',
                '结算阶段': '0.05', '回款阶段': '0.06', '售后阶段': '0.02',
                'conversion': '0.02', 'contract': '0.02', 'production': '0.10',
                'settlement': '0.05', 'payment': '0.06', 'after_sales': '0.02',
            },
            stage_weight=Decimal('1.0'),
            event_modifier_min=Decimal('0.2'),
            event_modifier_max=Decimal('1.2'),
            confidence_high_threshold=Decimal('0.30'),
            enabled=True,
        )


class CalculatorV1WithDataTest(TestCase):
    """依赖商机/阶段/里程碑数据的场景与边界测试。"""

    def setUp(self):
        if User is None:
            self.skipTest('User model not available')
        _ensure_output_value_policy()
        self.user = _make_user()
        self.client_entity = _make_client()
        self.opp = _make_opportunity(
            self.client_entity, self.user,
            estimated_amount=Decimal('100'),
            name='产值测试商机',
        )

    def test_calculate_dynamic_output_zero_amount(self):
        """边界：商机金额为 0（estimated 与 actual 均无）→ dynamic_output=0。"""
        opp = _make_opportunity(
            self.client_entity, self.user,
            estimated_amount=Decimal('0'),
            actual_amount=None,
            name='零金额商机',
        )
        out = calculate_dynamic_output(opp.id)
        self.assertEqual(out['dynamic_output'], Decimal('0'))
        self.assertEqual(out['confidence'], 'low')

    def test_calculate_dynamic_output_with_stage_no_project(self):
        """常见：有阶段、商机无 project → 无已完成里程碑，milestone_weight=0，产值=0。"""
        _make_stage(code='prod1', order=0)
        out = calculate_dynamic_output(self.opp.id)
        self.assertEqual(out['milestone_weight'], Decimal('0'))
        self.assertIsNone(out['milestone'])
        self.assertEqual(out['dynamic_output'], Decimal('0'))
        self.assertEqual(out['confidence'], 'low')

    def test_calculate_dynamic_output_with_stage_no_milestones(self):
        """边界：阶段下无里程碑 → 无已完成里程碑，milestone_weight=0。"""
        stage = _make_stage(code='empty_stage', name='空阶段', order=1)
        # 不创建 milestone，仅保证有阶段
        out = calculate_dynamic_output(self.opp.id)
        self.assertEqual(out['milestone_weight'], Decimal('0'))
        self.assertEqual(out['dynamic_output'], Decimal('0'))

    def test_calculate_dynamic_output_uses_estimated_amount(self):
        """常见：商机使用 estimated_amount 作为 base。"""
        _make_stage(code='s1', order=0)
        out = calculate_dynamic_output(self.opp.id)
        # base=100, service_weight=0.02, stage=1, milestone=0, modifier=1 → 0
        self.assertEqual(out['dynamic_output'], Decimal('0'))
        self.assertEqual(out['milestone_weight'], Decimal('0'))


class CalculatorV1MilestoneCompletionTest(TestCase):
    """is_milestone_completed：事件完成度 Σ >= 100% 的判定。"""

    def setUp(self):
        if User is None:
            self.skipTest('User model not available')
        _ensure_output_value_policy()
        self.user = _make_user()
        self.client_entity = _make_client()
        self.stage = _make_stage(code='stage_m', order=0)
        self.milestone = _make_milestone(self.stage, code='milestone_m', milestone_percentage=30)
        self.opp = _make_opportunity(
            self.client_entity, self.user,
            estimated_amount=Decimal('200'),
            name='里程碑测试商机',
        )

    def test_is_milestone_completed_no_project(self):
        """边界：商机无 project → False。"""
        self.opp.project_id = None
        self.opp.save()
        self.assertFalse(is_milestone_completed(self.milestone.id, self.opp.id))

    def test_is_milestone_completed_events_sum_below_100(self):
        """边界：计划管理未标记完成 → False（产值只认计划完成状态）。"""
        PlanOutputMilestoneCompletion.objects.filter(
            opportunity_id=self.opp.id,
            milestone_code=self.milestone.code,
        ).delete()
        self.assertFalse(is_milestone_completed(self.milestone.id, self.opp.id))

    def test_is_milestone_completed_events_sum_100(self):
        """常见：计划管理已标记该里程碑完成 → True（产值只读计划完成状态）。"""
        MilestoneEvidenceRule.objects.get_or_create(
            milestone_code=self.milestone.code,
            defaults={'required_event_types': ['CONSULT_OPINION_SUBMITTED'], 'enabled': True},
        )
        record_fact_event('CONSULT_OPINION_SUBMITTED', ref_model='opportunity', ref_id=str(self.opp.id), source_app='test')
        evaluate_milestone_completion(self.opp.id, self.milestone.code)
        self.assertTrue(is_milestone_completed(self.milestone.id, self.opp.id))

    def test_is_milestone_completed_events_sum_above_100(self):
        """常见：计划管理已标记该里程碑完成 → True。"""
        MilestoneEvidenceRule.objects.get_or_create(
            milestone_code=self.milestone.code,
            defaults={'required_event_types': ['CONSULT_OPINION_SUBMITTED'], 'enabled': True},
        )
        record_fact_event('CONSULT_OPINION_SUBMITTED', ref_model='opportunity', ref_id=str(self.opp.id), source_app='test')
        evaluate_milestone_completion(self.opp.id, self.milestone.code)
        self.assertTrue(is_milestone_completed(self.milestone.id, self.opp.id))

    def test_milestone_completion_only_from_plan_not_business(self):
        """硬约束：仅有业务 FactEvent 但计划未完成 → milestone 未完成，产值不变。"""
        record_fact_event(
            'CONSULT_OPINION_SUBMITTED',
            ref_model='opportunity',
            ref_id=str(self.opp.id),
            source_app='production_management',
        )
        # 未运行评估，故未写入 PlanOutputMilestoneCompletion，里程碑未完成
        self.assertFalse(is_milestone_completed(self.milestone.id, self.opp.id))
        out = calculate_dynamic_output(self.opp.id)
        self.assertEqual(out['milestone_weight'], Decimal('0'))
        self.assertEqual(out['dynamic_output'], Decimal('0'))


class CalculatorV1FormulaWithCompletedMilestoneTest(TestCase):
    """有已完成里程碑时，动态产值公式与 confidence 的集成测试。"""

    def setUp(self):
        if User is None:
            self.skipTest('User model not available')
        try:
            from backend.apps.production_management.models import Project
        except Exception:
            self.skipTest('Project model not available')
        _ensure_output_value_policy()
        self.user = _make_user()
        self.client_entity = _make_client()
        self.stage = _make_stage(code='formula_stage', order=0)
        self.milestone = _make_milestone(
            self.stage, code='formula_m', name='咨询意见提交', milestone_percentage=30,
        )
        self.event = _make_event(self.milestone, code='formula_e', event_percentage=100)
        self.project = Project.objects.create(
            project_number='TEST-OUT-FORMULA-%s' % timezone.now().timestamp(),
            name='公式测试项目',
            status='configuring',
        )
        self.opp = _make_opportunity(
            self.client_entity, self.user,
            estimated_amount=Decimal('100'),
            name='公式测试商机',
        )
        self.opp.project = self.project
        self.opp.save()
        MilestoneEvidenceRule.objects.get_or_create(
            milestone_code=self.milestone.code,
            defaults={'required_event_types': ['CONSULT_OPINION_SUBMITTED'], 'enabled': True},
        )
        record_fact_event('CONSULT_OPINION_SUBMITTED', ref_model='opportunity', ref_id=str(self.opp.id), source_app='test')
        evaluate_milestone_completion(self.opp.id, self.milestone.code)

    def test_dynamic_output_formula_with_completed_milestone(self):
        """常见：有已完成里程碑 → dynamic_output = amount × service_weight × 1 × milestone_weight × 1。"""
        out = calculate_dynamic_output(self.opp.id)
        # base=100, service_weight=0.02, stage_weight=1, milestone_weight=0.30, modifier=1
        expected = Decimal('100') * Decimal('0.02') * Decimal('1') * Decimal('0.30') * Decimal('1')
        self.assertEqual(out['dynamic_output'].quantize(Decimal('0.01')), expected.quantize(Decimal('0.01')))
        self.assertEqual(out['milestone_weight'], Decimal('0.30'))
        self.assertEqual(out['milestone'], '咨询意见提交')

    def test_confidence_high_when_milestone_weight_ge_030(self):
        """常见：milestone_weight >= 0.30 → confidence=high。"""
        out = calculate_dynamic_output(self.opp.id)
        self.assertEqual(out['confidence'], 'high')

    def test_extreme_amount_still_applies_formula(self):
        """边界：大额商机仍按公式计算，不溢出。"""
        self.opp.estimated_amount = Decimal('9999999.99')
        self.opp.save()
        out = calculate_dynamic_output(self.opp.id)
        expected = Decimal('9999999.99') * Decimal('0.02') * Decimal('1') * Decimal('0.30') * Decimal('1')
        self.assertEqual(out['dynamic_output'].quantize(Decimal('0.01')), expected.quantize(Decimal('0.01')))
