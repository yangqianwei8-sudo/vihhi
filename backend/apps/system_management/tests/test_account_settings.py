import json

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse


class AccountSettingsAPITests(TestCase):
    def setUp(self):
        self.client = Client()
        self.User = get_user_model()
        self.password = "T3stP@ssw0rd!"
        self.user = self.User.objects.create_user(
            username="13800009999",
            password=self.password,
            email="old@example.com",
            first_name="Old",
            position="旧职位",
        )
        logged_in = self.client.login(username=self.user.username, password=self.password)
        assert logged_in, "Precondition failed: unable to log in test user."

    def test_update_profile_via_api(self):
        url = reverse("system:user-update-profile")
        payload = {
            "first_name": "新名",
            "last_name": "测试",
            "email": "new_email@example.com",
            "position": "新职位",
        }
        response = self.client.put(
            url,
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get("success"))

        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "新名")
        self.assertEqual(self.user.last_name, "测试")
        self.assertEqual(self.user.email, "new_email@example.com")
        self.assertEqual(self.user.position, "新职位")
        self.assertTrue(self.user.profile_completed)

    def test_update_notification_preferences_requires_at_least_one(self):
        url = reverse("system:user-notification-preferences")

        response = self.client.put(
            url,
            data=json.dumps({"inbox": True, "email": False, "wecom": True}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        prefs = self.user.get_notification_preferences()
        self.assertTrue(prefs["inbox"])
        self.assertTrue(prefs["wecom"])

        response = self.client.put(
            url,
            data=json.dumps({"inbox": False, "email": False, "wecom": False}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        error_body = response.json()
        self.assertIn("至少需开启一种通知方式。", str(error_body))

    def test_change_password_via_api(self):
        url = reverse("system:user-change-password")
        new_password = "NewP@ssword123"

        response = self.client.post(
            url,
            data=json.dumps(
                {
                    "old_password": self.password,
                    "new_password": new_password,
                    "confirm_password": new_password,
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json().get("success"))

        # Session should be cleared after password change
        page_response = self.client.get(reverse("system_pages:account_settings"))
        self.assertEqual(page_response.status_code, 302)

        login_old = self.client.login(username=self.user.username, password=self.password)
        self.assertFalse(login_old)
        login_new = self.client.login(username=self.user.username, password=new_password)
        self.assertTrue(login_new)


class AccountSettingsPageTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.User = get_user_model()
        self.password = "PageP@ssword!"
        self.user = self.User.objects.create_user(
            username="13800008888",
            password=self.password,
            first_name="页面",
            last_name="测试",
        )

    def test_account_settings_page_context(self):
        logged_in = self.client.login(username=self.user.username, password=self.password)
        self.assertTrue(logged_in)

        response = self.client.get(reverse("system_pages:account_settings"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("profile_data", response.context)
        self.assertIn("notification_values", response.context)
        self.assertIn("roles", response.context)
        self.assertIn("permission_codes", response.context)

