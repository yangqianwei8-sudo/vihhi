from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from backend.apps.project_center.models import (
    Project,
    ProjectTeamNotification,
    ServiceProfession,
    ServiceType,
)


class TeamNotificationTests(TestCase):
    def setUp(self):
        self.User = get_user_model()
        self.client = Client()

        self.operator = self.User.objects.create_user(
            username='operator',
            password='test123456',
            is_superuser=True,
            position='项目负责人',
            user_type='internal',
        )
        self.member = self.User.objects.create_user(
            username='leader_user',
            password='test123456',
            position='专业负责人',
            user_type='internal',
        )

        self.service_type = ServiceType.objects.create(
            code='test_service_type',
            name='测试服务类型',
        )
        self.profession = ServiceProfession.objects.create(
            service_type=self.service_type,
            code='structural',
            name='结构专业',
        )

        self.project = Project.objects.create(
            project_number='TEST-001',
            name='测试项目',
            service_type=self.service_type,
            business_manager=self.operator,
            created_by=self.operator,
            status='configuring',
        )
        self.project.service_professions.add(self.profession)

    def test_notifications_created_for_team_changes(self):
        self.client.force_login(self.operator)

        url = reverse('project_pages:project_team', args=[self.project.id])
        response = self.client.post(
            url,
            data={
                'project_manager': str(self.operator.id),
                f'profession_{self.profession.code}_leader': str(self.member.id),
            },
        )

        self.assertEqual(response.status_code, 302)
        member_notifications = ProjectTeamNotification.objects.filter(
            recipient=self.member,
            title='团队新增成员',
        )
        self.assertTrue(member_notifications.exists())
        self.assertIn('TEST-001', member_notifications.first().message)
        self.assertEqual(member_notifications.first().context.get('action'), 'added')
        self.assertEqual(member_notifications.first().context.get('role'), '专业负责人')
        self.assertEqual(member_notifications.first().operator_id, self.operator.id)

        operator_notifications = ProjectTeamNotification.objects.filter(
            recipient=self.operator,
            title='团队变更提醒',
        )
        self.assertTrue(operator_notifications.exists())
        self.assertIn('新增', operator_notifications.first().message)
        summary_context = operator_notifications.first().context
        self.assertEqual(summary_context.get('action'), 'summary')
        self.assertTrue(summary_context.get('changed_roles'))


class TeamNotificationApiTests(TestCase):
    def setUp(self):
        self.User = get_user_model()
        self.api_client = APIClient()

        self.user = self.User.objects.create_user(
            username='api_user',
            password='test123456',
            user_type='internal',
        )

        self.other_user = self.User.objects.create_user(
            username='other_user',
            password='test123456',
            user_type='internal',
        )

        self.service_type = ServiceType.objects.create(
            code='api_service_type',
            name='API 服务类型',
        )
        self.project = Project.objects.create(
            project_number='TEST-API-001',
            name='API 项目',
            service_type=self.service_type,
            created_by=self.user,
            business_manager=self.user,
            status='waiting_start',
        )

        self.notification_unread = ProjectTeamNotification.objects.create(
            project=self.project,
            recipient=self.user,
            title='未读通知',
            message='这是一个未读通知',
            category='team_change',
        )
        self.notification_read = ProjectTeamNotification.objects.create(
            project=self.project,
            recipient=self.user,
            title='已读通知',
            message='这是一个已读通知',
            category='team_change',
            is_read=True,
            read_time=timezone.now(),
        )

    def test_list_unread_notifications(self):
        self.api_client.force_authenticate(self.user)
        url = reverse('project:notification-list')
        response = self.api_client.get(url, {'status': 'unread'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['title'], '未读通知')

    def test_mark_notification_as_read(self):
        self.api_client.force_authenticate(self.user)
        url = reverse('project:notification-mark-read', args=[self.notification_unread.id])
        response = self.api_client.post(url)
        self.assertEqual(response.status_code, 200)
        self.notification_unread.refresh_from_db()
        self.assertTrue(self.notification_unread.is_read)
        self.assertIsNotNone(self.notification_unread.read_time)

    def test_bulk_mark_read(self):
        self.api_client.force_authenticate(self.user)
        url = reverse('project:notification-bulk-mark-read')
        response = self.api_client.post(url, {'ids': [self.notification_unread.id]}, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['updated'], 1)
        self.notification_unread.refresh_from_db()
        self.assertTrue(self.notification_unread.is_read)

    def test_mark_all_read(self):
        self.api_client.force_authenticate(self.user)
        url = reverse('project:notification-mark-all-read')
        response = self.api_client.post(url)
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(response.data['updated'], 1)
        self.notification_unread.refresh_from_db()
        self.assertTrue(self.notification_unread.is_read)

    def test_user_cannot_access_others_notifications(self):
        self.api_client.force_authenticate(self.other_user)
        url = reverse('project:notification-mark-read', args=[self.notification_unread.id])
        response = self.api_client.post(url)
        self.assertEqual(response.status_code, 404)  # queryset filtered by user

