from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from rest_framework.test import APIClient

from backend.apps.plan_management.models import Plan, PlanDecision, StrategicGoal

User = get_user_model()


class PlanDecisionV2Tests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username="u1", password="pass123456")
        # 让用户具备裁决权限（你们 decide() 目前用 change_plan；若改了权限点这里同步）
        self.user.is_superuser = True
        self.user.save()

        # 创建必要的关联对象
        now = timezone.now()
        start_date = now.date()
        end_date = (now + timedelta(days=365)).date()
        
        self.goal = StrategicGoal.objects.create(
            goal_number="GOAL-TEST-001",
            name="测试目标",
            indicator_name="测试指标",
            indicator_type="numeric",
            goal_type="financial",
            goal_period="annual",
            status="published",
            target_value=100,
            current_value=0,
            responsible_person=self.user,
            description="测试目标描述",
            weight=50,
            start_date=start_date,
            end_date=end_date,
            created_by=self.user,
        )

        start_time = now
        end_time = now + timedelta(days=30)
        
        self.plan = Plan.objects.create(
            plan_number="PLAN-TEST-001",
            name="p1-test",
            plan_type="personal",
            plan_period="monthly",
            status="draft",
            progress=0,
            related_goal=self.goal,
            content="测试计划内容",
            plan_objective="测试计划目标",
            start_time=start_time,
            end_time=end_time,
            responsible_person=self.user,
            created_by=self.user,
        )

        self.client.force_authenticate(user=self.user)

    def test_start_request_creates_pending_decision(self):
        url = f"/api/plan/plans/{self.plan.id}/start-request/"
        r = self.client.post(url, {"reason": "start"}, format="json")
        self.assertEqual(r.status_code, 201)
        self.assertTrue(r.data["success"])
        decision_id = r.data["decision_id"]

        d = PlanDecision.objects.get(id=decision_id)
        self.assertEqual(d.plan_id, self.plan.id)
        self.assertEqual(d.request_type, "start")
        self.assertIsNone(d.decision)
        self.assertIsNone(d.decided_at)

    def test_duplicate_start_request_blocked(self):
        url = f"/api/plan/plans/{self.plan.id}/start-request/"
        self.client.post(url, {"reason": "start"}, format="json")
        r2 = self.client.post(url, {"reason": "start again"}, format="json")
        # P1 v2: 使用 409 Conflict 更语义化（重复请求/状态冲突）
        self.assertEqual(r2.status_code, 409)

    def test_reject_does_not_change_plan_status(self):
        start_url = f"/api/plan/plans/{self.plan.id}/start-request/"
        r = self.client.post(start_url, {"reason": "start"}, format="json")
        decision_id = r.data["decision_id"]

        decide_url = f"/api/plan/plan-decisions/{decision_id}/decide/"
        r2 = self.client.post(decide_url, {"approve": False, "reason": "no"}, format="json")
        self.assertEqual(r2.status_code, 200)

        self.plan.refresh_from_db()
        self.assertEqual(self.plan.status, "draft")

    def test_approve_start_changes_status_to_in_progress(self):
        start_url = f"/api/plan/plans/{self.plan.id}/start-request/"
        r = self.client.post(start_url, {"reason": "start"}, format="json")
        decision_id = r.data["decision_id"]

        decide_url = f"/api/plan/plan-decisions/{decision_id}/decide/"
        r2 = self.client.post(decide_url, {"approve": True, "reason": "ok"}, format="json")
        self.assertEqual(r2.status_code, 200)

        self.plan.refresh_from_db()
        self.assertEqual(self.plan.status, "in_progress")

    def test_approve_cancel_changes_status_to_cancelled(self):
        # 先让计划进入 in_progress
        self.plan.status = "in_progress"
        self.plan.save(update_fields=["status"])

        cancel_url = f"/api/plan/plans/{self.plan.id}/cancel-request/"
        r = self.client.post(cancel_url, {"reason": "cancel"}, format="json")
        self.assertEqual(r.status_code, 201)
        decision_id = r.data["decision_id"]

        decide_url = f"/api/plan/plan-decisions/{decision_id}/decide/"
        r2 = self.client.post(decide_url, {"approve": True, "reason": "ok"}, format="json")
        self.assertEqual(r2.status_code, 200)

        self.plan.refresh_from_db()
        self.assertEqual(self.plan.status, "cancelled")

    def test_progress_100_triggers_completed_via_recalc(self):
        """
        你们当前事实：progress>=100 → services/recalc_status.py 传 system_facts(all_tasks_completed=True)
        这里不直接调用 adjudicator 私有逻辑，调用你们 recalc 的公开函数入口。
        """
        # 先 in_progress
        self.plan.status = "in_progress"
        self.plan.progress = 100
        self.plan.save(update_fields=["status", "progress"])

        # 按你们真实函数名调整
        from backend.apps.plan_management.services import recalc_plan_status

        result = recalc_plan_status(self.plan)
        # recalc_plan_status 会修改 plan.status，但不会自动保存，需要手动保存
        if result.changed:
            self.plan.save(update_fields=["status"])

        self.plan.refresh_from_db()
        self.assertEqual(self.plan.status, "completed")

