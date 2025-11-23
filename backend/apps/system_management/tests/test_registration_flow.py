from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from backend.apps.system_management.models import Department, RegistrationRequest, Role


class RegistrationFlowTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.User = get_user_model()
        self.registration_password = "Reg@123456"
        self.registration_phone = "13900001234"

        self.staff_user = self.User.objects.create_user(
            username="admin_staff",
            password="Admin@123456",
            is_staff=True,
            email="admin@example.com",
        )

        self.department = Department.objects.create(
            name="技术部",
            code="tech",
        )

        self.role = Role.objects.create(
            name="技术助理",
            code="technical_assistant",
        )

    def test_registration_to_profile_completion_flow(self):
        response = self.client.post(
            reverse("register"),
            data={
                "phone": self.registration_phone,
                "client_type": "service_provider",
                "password": self.registration_password,
                "confirm_password": self.registration_password,
            },
            follow=True,
        )
        self.assertRedirects(response, reverse("registration_submitted"))

        reg_request = RegistrationRequest.objects.get(phone=self.registration_phone)
        self.assertEqual(reg_request.status, RegistrationRequest.STATUS_PENDING)

        admin_client = Client()
        admin_client.force_login(self.staff_user)
        approve_response = admin_client.post(
            reverse("admin_registration_detail", args=[reg_request.pk]),
            data={
                "status": RegistrationRequest.STATUS_APPROVED,
                "feedback": "通过",
            },
            follow=False,
        )
        self.assertRedirects(approve_response, reverse("admin_registration_list"))

        reg_request.refresh_from_db()
        self.assertEqual(reg_request.status, RegistrationRequest.STATUS_APPROVED)
        self.assertEqual(reg_request.processed_by, self.staff_user)

        created_user = self.User.objects.get(username=self.registration_phone)
        self.assertTrue(created_user.check_password(self.registration_password))
        self.assertIn(
            "technical_assistant",
            list(created_user.roles.values_list("code", flat=True)),
        )
        self.assertFalse(created_user.profile_completed)

        user_client = Client()
        login_success = user_client.login(
            username=self.registration_phone,
            password=self.registration_password,
        )
        self.assertTrue(login_success)

        complete_profile_url = reverse("complete_profile")
        profile_page = user_client.get(complete_profile_url)
        self.assertEqual(profile_page.status_code, 200)

        complete_response = user_client.post(
            complete_profile_url,
            data={
                "full_name": "测试用户",
                "email": "test_user@example.com",
                "position": "technical_assistant",
                "department": self.department.id,
            },
        )
        self.assertRedirects(complete_response, reverse("home"))

        created_user.refresh_from_db()
        self.assertTrue(created_user.profile_completed)
        self.assertEqual(created_user.first_name, "测试用户")
        self.assertEqual(created_user.email, "test_user@example.com")
        self.assertEqual(created_user.department, self.department)
        self.assertIn(
            "technical_assistant",
            list(created_user.roles.values_list("code", flat=True)),
        )

