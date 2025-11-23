from __future__ import annotations

from datetime import date, timedelta
from unittest import mock

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from backend.apps.project_center.models import Project
from backend.apps.resource_standard.models import ProfessionalCategory
from backend.apps.production_quality.models import Opinion
from backend.apps.production_quality.services import dispatch_quality_alerts

User = get_user_model()


class DispatchQualityAlertsTests(TestCase):
    def setUp(self):
        self.project_manager = User.objects.create_user(
            username="manager",
            email="manager@example.com",
            password="pass1234",
        )
        self.business_manager = User.objects.create_user(
            username="business",
            email="business@example.com",
            password="pass1234",
        )
        self.creator = User.objects.create_user(
            username="creator",
            email="creator@example.com",
            password="pass1234",
        )
        self.project = Project.objects.create(
            name="测试项目",
            project_number="P-001",
            project_manager=self.project_manager,
            business_manager=self.business_manager,
        )
        self.professional_category = ProfessionalCategory.objects.create(
            name="结构",
            code="STRUCT",
        )
        self.opinion = Opinion.objects.create(
            opinion_number="OPIN-P-001-001",
            project=self.project,
            professional_category=self.professional_category,
            created_by=self.creator,
            status=Opinion.OpinionStatus.SUBMITTED,
            location_name="地下室结构",
            issue_description="描述",
            recommendation="优化建议",
            issue_category=Opinion.IssueCategory.ERROR,
            severity_level=Opinion.SeverityLevel.MAJOR,
            response_deadline=date.today() - timedelta(days=1),
        )

    @mock.patch("backend.apps.production_quality.services.send_wecom_notification", return_value=True)
    @mock.patch("backend.apps.production_quality.services.send_email_notification", return_value=True)
    def test_create_notifications_for_unassigned_and_overdue(self, mock_email, mock_wecom):
        result = dispatch_quality_alerts(as_of=timezone.now())

        self.assertGreaterEqual(result["created"], 3)
        self.assertEqual(result["email_sent"], mock_email.call_count)
        self.assertEqual(result["wecom_sent"], mock_wecom.call_count)

        notifications = self.project.team_notifications.filter(category="quality_alert")
        self.assertTrue(notifications.exists())
        codes = {notif.context.get("alert_type") for notif in notifications}
        self.assertIn("unassigned", codes)
        self.assertIn("overdue", codes)
