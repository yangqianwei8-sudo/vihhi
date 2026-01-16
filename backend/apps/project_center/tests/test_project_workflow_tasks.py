from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from backend.apps.project_center.models import (
    Project,
    ProjectTask,
    ProjectTeam,
    ProjectDocument,
    ProjectMeetingRecord,
    ProjectMeetingDecision,
    ServiceType,
)


class ProjectWorkflowTaskTests(TestCase):
    def setUp(self):
        self.User = get_user_model()
        self.client = Client()

        self.design_lead = self.User.objects.create_user(
            username='design_lead',
            password='pwd123456',
            user_type='design_partner',
            is_superuser=True,
            is_staff=True,
        )
        self.project_manager = self.User.objects.create_user(
            username='pm_user',
            password='pwd123456',
            user_type='internal',
            is_superuser=True,
            is_staff=True,
        )
        self.client_leader = self.User.objects.create_user(
            username='client_lead',
            password='pwd123456',
            user_type='client_owner',
            is_superuser=True,
            is_staff=True,
        )

        self.service_type = ServiceType.objects.create(
            code='wf_service',
            name='流程测试服务',
        )
        self.project = Project.objects.create(
            project_number='WF-001',
            name='流程测试项目',
            service_type=self.service_type,
            project_manager=self.project_manager,
            business_manager=self.project_manager,
            client_leader=self.client_leader,
            design_leader=self.design_lead,
            created_by=self.project_manager,
            status='in_progress',
        )
        ProjectTeam.objects.create(project=self.project, user=self.design_lead, role='design_lead', unit='design_side')
        ProjectTeam.objects.create(project=self.project, user=self.project_manager, role='project_manager', unit='management')
        ProjectTeam.objects.create(project=self.project, user=self.client_leader, role='client_lead', unit='client_side')

    def test_design_upload_completes_and_spawns_tasks(self):
        ProjectTask.objects.create(
            project=self.project,
            task_type='design_upload_revisions',
            title='改图上传',
            status='pending',
        )
        url = reverse('production_pages:project_design_upload', args=[self.project.id])
        self.client.force_login(self.design_lead)
        upload_file = SimpleUploadedFile('rev.dwg', b'filecontent', content_type='application/octet-stream')
        response = self.client.post(url, {'note': '上传改图', 'files': upload_file})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(ProjectDocument.objects.filter(project=self.project, document_type='design').exists())
        self.assertFalse(
            ProjectTask.objects.filter(project=self.project, task_type='design_upload_revisions', status='pending').exists()
        )
        self.assertTrue(
            ProjectTask.objects.filter(project=self.project, task_type='internal_verify_revisions', status='pending').exists()
        )

    def test_internal_verify_approved_flows_to_client_confirm(self):
        ProjectTask.objects.create(
            project=self.project,
            task_type='internal_verify_revisions',
            title='核图任务',
            status='pending',
        )
        url = reverse('production_pages:project_internal_verify', args=[self.project.id])
        self.client.force_login(self.project_manager)
        response = self.client.post(url, {'result': 'approved', 'note': '一致'})
        self.assertEqual(response.status_code, 302)
        self.assertFalse(
            ProjectTask.objects.filter(project=self.project, task_type='internal_verify_revisions', status='pending').exists()
        )
        self.assertTrue(
            ProjectTask.objects.filter(project=self.project, task_type='client_confirm_outcome', status='pending').exists()
        )

    def test_internal_verify_requests_changes_returns_to_design(self):
        url = reverse('production_pages:project_internal_verify', args=[self.project.id])
        self.client.force_login(self.project_manager)
        response = self.client.post(url, {'result': 'changes', 'note': '需要补充'})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            ProjectTask.objects.filter(project=self.project, task_type='design_upload_revisions', status='pending').exists()
        )

    def test_client_confirm_outcome_completes_project(self):
        ProjectTask.objects.create(
            project=self.project,
            task_type='client_confirm_outcome',
            title='成果确认',
            status='pending',
        )
        url = reverse('production_pages:project_client_confirm_outcome', args=[self.project.id])
        self.client.force_login(self.client_leader)
        response = self.client.post(url, {'result': 'accepted', 'comment': '同意'})
        self.assertEqual(response.status_code, 302)
        self.assertFalse(
            ProjectTask.objects.filter(project=self.project, task_type='client_confirm_outcome', status='pending').exists()
        )
        self.project.refresh_from_db()
        self.assertEqual(self.project.status, 'completed')
        self.assertIsNotNone(self.project.actual_end_date)

    def test_full_meeting_to_client_confirmation_flow(self):
        """会议记录 -> 设计上传 -> 核图 -> 甲方确认 的任务串联。"""
        ProjectTask.objects.create(
            project=self.project,
            task_type='client_confirm_meeting',
            title='确认会议',
            status='pending',
        )
        ProjectTask.objects.create(
            project=self.project,
            task_type='organize_tripartite_meeting',
            title='组织会议',
            status='pending',
        )

        self.client.force_login(self.project_manager)
        meeting_url = reverse('production_pages:project_meeting_log', args=[self.project.id])
        response = self.client.post(
            meeting_url,
            {
                'form_type': 'meeting',
                'meeting_date': timezone.now().date().isoformat(),
                'topic': '全专业会议',
                'client_decision': '同意推进',
                'design_decision': '准备改图',
                'consultant_decision': '记录完成',
                'conclusions': '进入改图阶段',
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(
            ProjectTask.objects.filter(project=self.project, task_type='client_confirm_meeting', status='pending').exists()
        )
        self.assertFalse(
            ProjectTask.objects.filter(project=self.project, task_type='organize_tripartite_meeting', status='pending').exists()
        )
        self.assertTrue(
            ProjectTask.objects.filter(project=self.project, task_type='design_upload_revisions', status='pending').exists()
        )

        # 设计方上传改图
        self.client.logout()
        self.client.force_login(self.design_lead)
        upload_file = SimpleUploadedFile('rev2.dwg', b'filecontent', content_type='application/octet-stream')
        design_upload_url = reverse('production_pages:project_design_upload', args=[self.project.id])
        response = self.client.post(design_upload_url, {'note': '会议后的改图', 'files': upload_file})
        self.assertEqual(response.status_code, 302)
        self.assertFalse(
            ProjectTask.objects.filter(project=self.project, task_type='design_upload_revisions', status='pending').exists()
        )
        self.assertTrue(
            ProjectTask.objects.filter(project=self.project, task_type='internal_verify_revisions', status='pending').exists()
        )

        # 核图通过
        self.client.logout()
        self.client.force_login(self.project_manager)
        internal_verify_url = reverse('production_pages:project_internal_verify', args=[self.project.id])
        response = self.client.post(internal_verify_url, {'result': 'approved', 'note': '核图完成'})
        self.assertEqual(response.status_code, 302)
        self.assertFalse(
            ProjectTask.objects.filter(project=self.project, task_type='internal_verify_revisions', status='pending').exists()
        )
        self.assertTrue(
            ProjectTask.objects.filter(project=self.project, task_type='client_confirm_outcome', status='pending').exists()
        )

        # 甲方确认通过
        self.client.logout()
        self.client.force_login(self.client_leader)
        client_confirm_url = reverse('production_pages:project_client_confirm_outcome', args=[self.project.id])
        response = self.client.post(client_confirm_url, {'result': 'accepted', 'comment': '同意'})
        self.assertEqual(response.status_code, 302)
        self.assertFalse(
            ProjectTask.objects.filter(project=self.project, task_type='client_confirm_outcome', status='pending').exists()
        )

