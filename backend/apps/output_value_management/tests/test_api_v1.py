"""
产值管理 V1 API 联调测试
依据：docs/output_value_v1_execution.md 八、output_value_v1_api.md
验证 GET /api/output/v1/opportunity/{id}/ 返回结构与计算逻辑一致；
验收：产值只认计划管理完成状态，仅有业务 FactEvent 未完成计划时 milestone_weight 不变。
"""
from decimal import Decimal

from django.test import TestCase, Client as TestClient
from django.urls import reverse

from backend.apps.opportunity_management.models import BusinessOpportunity
from backend.apps.customer_management.models import Client
from backend.apps.output_value_management.models import (
    OutputValueStage,
    OutputValueMilestone,
    OutputValuePolicy,
)
from backend.apps.plan_management.models import PlanOutputMilestoneCompletion, MilestoneEvidenceRule
from backend.apps.plan_management.services.fact_event import record_fact_event
from backend.apps.plan_management.services.milestone_completion import evaluate_milestone_completion

try:
    from django.contrib.auth import get_user_model
    User = get_user_model()
except Exception:
    User = None


def _ensure_output_value_policy():
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


class OutputValueV1APITest(TestCase):
    def setUp(self):
        if User is None:
            return
        _ensure_output_value_policy()
        self.client = TestClient()
        self.user = User.objects.create_user(
            username='api_test_user',
            password='test123',
            is_staff=False,
        )
        self.customer = Client.objects.create(name='API测试客户', is_active=True)
        self.opp = BusinessOpportunity.objects.create(
            name='API测试商机',
            client=self.customer,
            business_manager=self.user,
            created_by=self.user,
            status='potential',
            estimated_amount=Decimal('100'),
            success_probability=10,
            is_active=True,
            approval_status='pending',
        )

    def test_v1_opportunity_401_when_not_authenticated(self):
        """未登录请求返回 401。"""
        url = reverse('output_api:v1_opportunity_dynamic_output', kwargs={'id': 1})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 401)

    def test_v1_opportunity_404_when_not_found(self):
        """商机不存在时返回 404。"""
        self.client.login(username='api_test_user', password='test123')
        url = reverse('output_api:v1_opportunity_dynamic_output', kwargs={'id': 999999})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)
        self.assertIn('detail', response.json())

    def test_v1_opportunity_200_and_structure_when_authenticated(self):
        """已登录且商机存在时返回 200，且包含 dynamic_output、milestone_weight、confidence。"""
        if User is None:
            self.skipTest('User not available')
        self.client.login(username='api_test_user', password='test123')
        url = reverse('output_api:v1_opportunity_dynamic_output', kwargs={'id': self.opp.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('dynamic_output', data)
        self.assertIn('milestone_weight', data)
        self.assertIn('confidence', data)
        self.assertIn('stage', data)
        self.assertIn('milestone', data)
        self.assertIn(data['confidence'], ('low', 'medium', 'high'))

    def test_v1_plan_milestone_completed_then_milestone_weight_and_output_change(self):
        """构造：计划里程碑完成 -> 调 V1 API -> milestone_weight/产值变化。"""
        if User is None:
            self.skipTest('User not available')
        stage = OutputValueStage.objects.create(
            name='生产阶段', code='production', stage_type='production',
            stage_percentage=Decimal('100'), base_amount_type='contract_amount',
            order=0, is_active=True,
        )
        milestone = OutputValueMilestone.objects.create(
            stage=stage, name='咨询意见提交', code='consult_done',
            milestone_percentage=Decimal('30'), order=0, is_active=True,
        )
        self.opp.current_stage = stage
        self.opp.save()
        MilestoneEvidenceRule.objects.get_or_create(
            milestone_code=milestone.code,
            defaults={'required_event_types': ['CONSULT_OPINION_SUBMITTED'], 'enabled': True},
        )
        record_fact_event('CONSULT_OPINION_SUBMITTED', ref_model='opportunity', ref_id=str(self.opp.id), source_app='test')
        evaluate_milestone_completion(self.opp.id, milestone.code)
        self.client.login(username='api_test_user', password='test123')
        url = reverse('output_api:v1_opportunity_dynamic_output', kwargs={'id': self.opp.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertGreater(Decimal(str(data['milestone_weight'])), 0)
        self.assertGreater(Decimal(str(data['dynamic_output'])), 0)
        self.assertEqual(data['milestone'], '咨询意见提交')

    def test_v1_only_fact_event_plan_not_completed_then_milestone_weight_unchanged(self):
        """构造：仅有业务 FactEvent 但计划未完成 -> 调 V1 API -> milestone_weight 不变（仍按计划状态）。"""
        if User is None:
            self.skipTest('User not available')
        record_fact_event(
            'CONSULT_OPINION_SUBMITTED',
            ref_model='opportunity',
            ref_id=str(self.opp.id),
            source_app='production_management',
        )
        PlanOutputMilestoneCompletion.objects.filter(
            opportunity_id=self.opp.id,
        ).delete()
        self.client.login(username='api_test_user', password='test123')
        url = reverse('output_api:v1_opportunity_dynamic_output', kwargs={'id': self.opp.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(Decimal(str(data['milestone_weight'])), Decimal('0'))
        self.assertEqual(Decimal(str(data['dynamic_output'])), Decimal('0'))
