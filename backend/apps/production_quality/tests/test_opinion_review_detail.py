from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from backend.apps.production_quality.models import Opinion, OpinionReview
from backend.apps.project_center.models import Project
from backend.apps.resource_standard.models import ProfessionalCategory


class OpinionReviewDetailTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.User = get_user_model()
        self.project_manager = self.User.objects.create_user(
            username="13800002000",
            password="Test@123456",
            first_name="项目",
            last_name="经理",
        )
        self.other_user = self.User.objects.create_user(
            username="13800002001",
            password="Test@123456",
            first_name="其他",
            last_name="审核",
        )
        self.creator = self.User.objects.create_user(
            username="13800002002",
            password="Test@123456",
            first_name="提出",
            last_name="人",
        )
        self.category = ProfessionalCategory.objects.create(
            code="structure",
            name="结构专业",
            category="structure",
            service_types=["result_optimization"],
        )
        self.project = Project.objects.create(
            project_number="VIH-UT-001",
            name="测试项目",
            created_by=self.project_manager,
            project_manager=self.project_manager,
        )
        self.counter = 1

    def make_opinion(self, **overrides):
        number = f"OPIN-UT-{self.counter:03d}"
        self.counter += 1
        defaults = {
            "opinion_number": number,
            "project": self.project,
            "professional_category": self.category,
            "created_by": self.creator,
            "location_name": "负一层结构柱",
            "issue_description": "结构钢筋与设计不符",
            "recommendation": "按优化方案调整钢筋配置",
            "issue_category": Opinion.IssueCategory.ERROR,
            "severity_level": Opinion.SeverityLevel.NORMAL,
            "status": Opinion.OpinionStatus.SUBMITTED,
            "submitted_at": timezone.now(),
        }
        defaults.update(overrides)
        return Opinion.objects.create(**defaults)

    def test_review_requires_assignment_when_other_reviewer(self):
        opinion = self.make_opinion(current_reviewer=self.other_user)
        self.client.login(username=self.project_manager.username, password="Test@123456")
        url = reverse("production_quality:opinion-review-list", kwargs={"opinion_pk": opinion.id})
        response = self.client.post(
            url,
            data={
                "opinion": opinion.id,
                "status": OpinionReview.ReviewStatus.APPROVED,
            },
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("请先将该意见指派给自己", response.json()["detail"])
        opinion.refresh_from_db()
        self.assertEqual(opinion.status, Opinion.OpinionStatus.SUBMITTED)
        self.assertEqual(OpinionReview.objects.filter(opinion=opinion).count(), 0)

    def test_review_success_sets_status_and_role(self):
        opinion = self.make_opinion(current_reviewer=self.project_manager)
        self.client.login(username=self.project_manager.username, password="Test@123456")
        url = reverse("production_quality:opinion-review-list", kwargs={"opinion_pk": opinion.id})
        response = self.client.post(
            url,
            data={
                "opinion": opinion.id,
                "status": OpinionReview.ReviewStatus.APPROVED,
                "comments": "审核通过。",
                "technical_score": 5,
                "economic_score": 4,
            },
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 201)
        opinion.refresh_from_db()
        self.assertEqual(opinion.status, Opinion.OpinionStatus.APPROVED)
        self.assertIsNone(opinion.current_reviewer)
        self.assertIsNotNone(opinion.first_response_at)
        review = OpinionReview.objects.get(opinion=opinion, reviewer=self.project_manager)
        self.assertEqual(review.role, OpinionReview.ReviewRole.PROJECT_LEAD)
        self.assertEqual(review.status, OpinionReview.ReviewStatus.APPROVED)

        # 再次提交同角色应提示不可重复
        response_repeat = self.client.post(
            url,
            data={
                "opinion": opinion.id,
                "status": OpinionReview.ReviewStatus.APPROVED,
            },
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response_repeat.status_code, 400)
        detail_msg = response_repeat.json()["detail"]
        self.assertTrue(
            "无法重复提交" in detail_msg or "当前状态不可提交" in detail_msg,
            msg=detail_msg,
        )

    def test_review_rejected_requires_comment(self):
        opinion = self.make_opinion(current_reviewer=self.project_manager)
        self.client.login(username=self.project_manager.username, password="Test@123456")
        url = reverse("production_quality:opinion-review-list", kwargs={"opinion_pk": opinion.id})
        response = self.client.post(
            url,
            data={
                "opinion": opinion.id,
                "status": OpinionReview.ReviewStatus.REJECTED,
            },
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("必须填写审核意见", response.json()["comments"][0])

