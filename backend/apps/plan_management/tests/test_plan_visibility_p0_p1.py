"""
P0/P1 权限与可见性修补的测试：跨公司/非可见计划·目标·决策的越权访问应返回 404。
"""
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta

from backend.apps.plan_management.models import Plan, PlanDecision, StrategicGoal
from backend.apps.plan_management.views_pages import (
    get_plan_qs_for_user,
    get_plan_or_404,
    get_pending_decision_or_404,
    get_goal_qs_for_user,
)

User = get_user_model()


def _make_goal(created_by, responsible_person, level="personal"):
    return StrategicGoal.objects.create(
        goal_number="GOAL-VIS-001",
        name="可见性测试目标",
        indicator_name="指标",
        indicator_type="numeric",
        goal_type="financial",
        goal_period="annual",
        status="published",
        target_value=100,
        current_value=0,
        responsible_person=responsible_person,
        description="描述",
        weight=50,
        start_date=timezone.now().date(),
        end_date=(timezone.now() + timedelta(days=365)).date(),
        created_by=created_by,
        level=level,
    )


def _make_plan(created_by, responsible_person, goal=None):
    now = timezone.now()
    return Plan.objects.create(
        plan_number="PLAN-VIS-001",
        name="可见性测试计划",
        level="personal",
        plan_period="monthly",
        status="draft",
        progress=0,
        related_goal=goal,
        content="内容",
        plan_objective="目标",
        start_time=now,
        end_time=now + timedelta(days=30),
        responsible_person=responsible_person,
        created_by=created_by,
    )


class GetPlanQsForUserTests(TestCase):
    """get_plan_qs_for_user：无 view_all 时仅返回本人负责/owner 的计划"""

    def setUp(self):
        self.user_a = User.objects.create_user(username="vis_a", password="pw")
        self.user_b = User.objects.create_user(username="vis_b", password="pw")
        self.goal_a = _make_goal(self.user_a, self.user_a)
        self.plan_a = _make_plan(self.user_a, self.user_a, self.goal_a)

    def test_user_sees_only_own_plan_without_view_all(self):
        """无 view_all 时，仅能看到 responsible_person=自己 或 owner=自己 的计划"""
        from django.test import RequestFactory
        from backend.apps.system_management.services import get_user_permission_codes

        rf = RequestFactory()
        req_a = rf.get("/")
        req_a.user = self.user_a
        req_b = rf.get("/")
        req_b.user = self.user_b
        qs_a = get_plan_qs_for_user(req_a)
        qs_b = get_plan_qs_for_user(req_b)
        self.assertIn(self.plan_a, qs_a)
        self.assertNotIn(self.plan_a, qs_b)


class GetPlanOr404Tests(TestCase):
    """get_plan_or_404：非可见计划应 404"""

    def setUp(self):
        self.user_a = User.objects.create_user(username="vis_a", password="pw")
        self.user_b = User.objects.create_user(username="vis_b", password="pw")
        self.goal_a = _make_goal(self.user_a, self.user_a)
        self.plan_a = _make_plan(self.user_a, self.user_a, self.goal_a)

    def test_other_user_plan_returns_404(self):
        """B 访问 A 的计划详情应 404（B 无 view_all 且计划非 B 的）"""
        from django.test import RequestFactory
        from django.http import Http404

        rf = RequestFactory()
        req = rf.get("/")
        req.user = self.user_b
        with self.assertRaises(Http404):
            get_plan_or_404(req, self.plan_a.id)

    def test_owner_sees_plan(self):
        """负责人访问自己的计划应成功"""
        from django.test import RequestFactory

        rf = RequestFactory()
        req = rf.get("/")
        req.user = self.user_a
        plan = get_plan_or_404(req, self.plan_a.id)
        self.assertEqual(plan.id, self.plan_a.id)


class PlanDetailEditDeleteVisibilityTests(TestCase):
    """plan_detail / plan_edit / plan_delete：非可见计划应 404"""

    def setUp(self):
        self.user_a = User.objects.create_user(username="vis_a", password="pw")
        self.user_b = User.objects.create_user(username="vis_b", password="pw")
        ct_plan = ContentType.objects.get_for_model(Plan)
        for codename in ("view_plan", "change_plan", "delete_plan"):
            perm = Permission.objects.get(content_type=ct_plan, codename=codename)
            self.user_b.user_permissions.add(perm)
        self.client_b = Client()
        self.client_b.force_login(self.user_b)
        self.goal_a = _make_goal(self.user_a, self.user_a)
        self.plan_a = _make_plan(self.user_a, self.user_a, self.goal_a)

    def test_plan_detail_other_user_returns_404(self):
        """B 访问 A 的计划详情页应 404"""
        url = reverse("plan_pages:plan_detail", args=[self.plan_a.id])
        r = self.client_b.get(url)
        self.assertEqual(r.status_code, 404)

    def test_plan_edit_other_user_returns_404(self):
        """B 访问 A 的计划编辑页应 404"""
        url = reverse("plan_pages:plan_edit", args=[self.plan_a.id])
        r = self.client_b.get(url)
        self.assertEqual(r.status_code, 404)

    def test_plan_delete_other_user_returns_404(self):
        """B 访问 A 的计划删除页应 404（GET 确认页）"""
        url = reverse("plan_pages:plan_delete", args=[self.plan_a.id])
        r = self.client_b.get(url)
        self.assertEqual(r.status_code, 404)


class DecisionApproveRejectVisibilityTests(TestCase):
    """decision_approve / decision_reject：非可见计划对应的决策应 404"""

    def setUp(self):
        self.user_a = User.objects.create_user(username="vis_a", password="pw")
        self.user_b = User.objects.create_user(username="vis_b", password="pw")
        ct_plan = ContentType.objects.get_for_model(Plan)
        try:
            perm = Permission.objects.get(content_type=ct_plan, codename="approve_plan")
            self.user_b.user_permissions.add(perm)
        except Permission.DoesNotExist:
            pass
        self.client_b = Client()
        self.client_b.force_login(self.user_b)
        self.goal_a = _make_goal(self.user_a, self.user_a)
        self.plan_a = _make_plan(self.user_a, self.user_a, self.goal_a)
        self.decision = PlanDecision.objects.create(
            plan=self.plan_a,
            request_type="start",
            decision=None,
            requested_by=self.user_a,
            reason="test",
        )

    def test_decision_approve_other_plan_returns_404(self):
        """B 有审批权限但决策属于 A 的计划（B 不可见），裁决应 404"""
        url = reverse("plan_pages:decision_approve", args=[self.decision.id])
        r = self.client_b.post(url, {"reason": "ok"})
        self.assertEqual(r.status_code, 404)


class GoalDetailEditDeleteVisibilityTests(TestCase):
    """strategic_goal_detail / edit / delete：列表不可见的目标直链访问应 404"""

    def setUp(self):
        self.user_a = User.objects.create_user(username="vis_a", password="pw")
        self.user_b = User.objects.create_user(username="vis_b", password="pw")
        ct_goal = ContentType.objects.get_for_model(StrategicGoal)
        perm = Permission.objects.get(content_type=ct_goal, codename="manage_goal")
        self.user_b.user_permissions.add(perm)
        self.client_b = Client()
        self.client_b.force_login(self.user_b)
        self.goal_a = _make_goal(self.user_a, self.user_a, level="personal")

    def test_goal_detail_other_user_personal_goal_returns_404(self):
        """B 有 manage_goal 但目标为 A 的个人目标（不在 B 的 get_goal_qs_for_user 内），详情应 404"""
        url = reverse("plan_pages:strategic_goal_detail", args=[self.goal_a.id])
        r = self.client_b.get(url)
        self.assertEqual(r.status_code, 404)

    def test_goal_edit_other_user_personal_goal_returns_404(self):
        """B 编辑 A 的个人目标应 404"""
        url = reverse("plan_pages:strategic_goal_edit", args=[self.goal_a.id])
        r = self.client_b.get(url)
        self.assertEqual(r.status_code, 404)

    def test_goal_delete_other_user_personal_goal_returns_404(self):
        """B 删除 A 的个人目标应 404"""
        url = reverse("plan_pages:strategic_goal_delete", args=[self.goal_a.id])
        r = self.client_b.get(url)
        self.assertEqual(r.status_code, 404)


class GetGoalQsForUserTests(TestCase):
    """get_goal_qs_for_user：无 view_all 时仅返回负责/参与/公司目标"""

    def setUp(self):
        self.user_a = User.objects.create_user(username="vis_a", password="pw")
        self.user_b = User.objects.create_user(username="vis_b", password="pw")
        self.goal_personal_a = _make_goal(self.user_a, self.user_a, level="personal")
        self.goal_company = _make_goal(self.user_a, self.user_a, level="company")

    def test_user_b_does_not_see_user_a_personal_goal(self):
        """B 的 goal qs 中不应包含 A 的个人目标"""
        from django.test import RequestFactory

        rf = RequestFactory()
        req = rf.get("/")
        req.user = self.user_b
        qs = get_goal_qs_for_user(req)
        self.assertNotIn(self.goal_personal_a, qs)

    def test_user_b_sees_company_goal(self):
        """B 的 goal qs 中应包含公司目标（当有 manage_goal 时的过滤逻辑）"""
        from django.test import RequestFactory

        rf = RequestFactory()
        req = rf.get("/")
        req.user = self.user_b
        qs = get_goal_qs_for_user(req)
        self.assertIn(self.goal_company, qs)
