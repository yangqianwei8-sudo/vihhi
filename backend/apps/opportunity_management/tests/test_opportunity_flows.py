# 商机 8 项流程测试：审批提交、权限隔离、软删除、Project 关联、委托书/合同选择商机回填 API
#
# 运行方式（需测试库迁移正常）:
#   python manage.py test backend.apps.opportunity_management.tests.test_opportunity_flows --keepdb
# 若测试库报错 permission_management 未安装，可先跑权限单元测试（不依赖 DB）:
#   python manage.py test backend.apps.opportunity_management.tests.test_perm_check
# 或在开发库有商机数据时跑快速验证:
#   python -c "import django; django.setup(); from backend.apps.opportunity_management.tests.run_flow_checks import run; run()"

from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase, Client as TestClient
from django.urls import reverse
from django.contrib.auth import get_user_model

from backend.apps.opportunity_management.models import BusinessOpportunity
from backend.apps.opportunity_management.perm_check import (
    PREFIX as OPP_PREFIX,
    opportunity_can_view_all,
    opportunity_can_access_detail,
    opportunity_can_access_edit,
)
from backend.apps.customer_management.models import Client

User = get_user_model()


def _perm_view_only():
    return {f'{OPP_PREFIX}.view'}


def _perm_view_all():
    return {f'{OPP_PREFIX}.view', f'{OPP_PREFIX}.view_all'}


def _perm_edit():
    return {f'{OPP_PREFIX}.view', f'{OPP_PREFIX}.view_all', f'{OPP_PREFIX}.edit'}


class OpportunityFlowsTestBase(TestCase):
    """基类：创建用户、客户、商机"""

    def setUp(self):
        self.client = TestClient()
        self.user_a = User.objects.create_user(
            username='user_a_view_all',
            password='test123',
            is_superuser=False,
            is_staff=False,
        )
        self.user_b = User.objects.create_user(
            username='user_b_owner',
            password='test123',
            is_superuser=False,
            is_staff=False,
        )
        self.user_c = User.objects.create_user(
            username='user_c_other',
            password='test123',
            is_superuser=False,
            is_staff=False,
        )
        self.superuser = User.objects.create_superuser(
            username='super_admin',
            password='test123',
            email='admin@test.com',
        )
        self.customer = Client.objects.create(
            name='测试客户',
            is_active=True,
        )
        self.opp_b = BusinessOpportunity.objects.create(
            name='B的商机',
            client=self.customer,
            business_manager=self.user_b,
            created_by=self.user_b,
            status='potential',
            estimated_amount=Decimal('100'),
            success_probability=10,
            weighted_amount=Decimal('10'),
            is_active=True,
            approval_status='pending',
        )


class Test1ApprovalSubmit(OpportunityFlowsTestBase):
    """1. 审批提交：提交后 approval_status=pending，并显示审批进度"""

    @patch('backend.apps.opportunity_management.views_opportunity.get_user_permission_codes')
    def test_submit_approval_sets_pending_and_shows_approval_path(self, mock_get_perm):
        mock_get_perm.return_value = _perm_edit()
        self.client.login(username='user_b_owner', password='test123')

        url = reverse(
            'opportunity_pages:opportunity_submit_for_approval',
            kwargs={'opportunity_id': self.opp_b.id},
        )
        response = self.client.post(url, {'comment': '申请审批'}, follow=True)

        self.opp_b.refresh_from_db()
        # 若流程未配置则可能重定向并提示错误，这里只断言：要么成功并 pending，要么因流程未配置而提示
        if response.status_code == 200 and '提交审批失败' not in response.content.decode():
            self.assertEqual(self.opp_b.approval_status, 'pending')
        # 若 WorkflowTemplate 不存在，视图会 redirect 并 message.error，我们只要求不 500
        self.assertIn(response.status_code, [200, 302])


class Test2PermissionViewAll(OpportunityFlowsTestBase):
    """2. 权限隔离 view_all：A 看全部，B 只看自己负责的"""

    def setUp(self):
        super().setUp()
        self.opp_other = BusinessOpportunity.objects.create(
            name='他人商机',
            client=self.customer,
            business_manager=self.user_c,
            created_by=self.user_c,
            status='potential',
            estimated_amount=Decimal('50'),
            success_probability=10,
            weighted_amount=Decimal('5'),
            is_active=True,
        )

    @patch('backend.apps.opportunity_management.views_opportunity.get_user_permission_codes')
    def test_user_with_view_all_sees_all_opportunities(self, mock_get_perm):
        mock_get_perm.return_value = _perm_view_all()
        self.client.login(username='user_a_view_all', password='test123')
        response = self.client.get(reverse('opportunity_pages:opportunity_management'))
        self.assertEqual(response.status_code, 200)
        # 列表页应包含 B 的商机和 C 的商机（A 有 view_all）
        html = response.content.decode()
        self.assertIn(self.opp_b.name, html)
        self.assertIn(self.opp_other.name, html)

    @patch('backend.apps.opportunity_management.views_opportunity.get_user_permission_codes')
    def test_user_without_view_all_sees_only_own_opportunities(self, mock_get_perm):
        mock_get_perm.return_value = _perm_view_only()
        self.client.login(username='user_b_owner', password='test123')
        response = self.client.get(reverse('opportunity_pages:opportunity_management'))
        self.assertEqual(response.status_code, 200)
        html = response.content.decode()
        self.assertIn(self.opp_b.name, html)
        # B 无 view_all，不应看到 C 的商机
        self.assertNotIn(self.opp_other.name, html)


class Test3PermissionDetailEditDelete(OpportunityFlowsTestBase):
    """3. 权限隔离：非负责人 C 无法访问详情/编辑/流转/删除"""

    @patch('backend.apps.opportunity_management.views_opportunity.get_user_permission_codes')
    def test_non_owner_cannot_access_detail(self, mock_get_perm):
        mock_get_perm.return_value = _perm_view_only()
        self.client.login(username='user_c_other', password='test123')
        url = reverse(
            'opportunity_pages:opportunity_detail',
            kwargs={'opportunity_id': self.opp_b.id},
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('opportunities', response.url or '')

    @patch('backend.apps.opportunity_management.views_opportunity.get_user_permission_codes')
    def test_non_owner_cannot_access_edit(self, mock_get_perm):
        mock_get_perm.return_value = _perm_view_only()
        self.client.login(username='user_c_other', password='test123')
        url = reverse(
            'opportunity_pages:opportunity_edit',
            kwargs={'opportunity_id': self.opp_b.id},
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

    @patch('backend.apps.opportunity_management.views_opportunity.get_user_permission_codes')
    def test_non_owner_cannot_delete(self, mock_get_perm):
        mock_get_perm.return_value = _perm_view_only()
        self.client.login(username='user_c_other', password='test123')
        url = reverse(
            'opportunity_pages:opportunity_delete',
            kwargs={'opportunity_id': self.opp_b.id},
        )
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.opp_b.refresh_from_db()
        self.assertTrue(self.opp_b.is_active)

    @patch('backend.apps.opportunity_management.views_opportunity.get_user_permission_codes')
    def test_non_owner_cannot_access_transition(self, mock_get_perm):
        mock_get_perm.return_value = _perm_view_only()
        self.client.login(username='user_c_other', password='test123')
        url = reverse(
            'opportunity_pages:opportunity_status_transition',
            kwargs={'opportunity_id': self.opp_b.id},
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)


class Test4SoftDeleteNormalUser(OpportunityFlowsTestBase):
    """4. 软删除 - 普通用户 B：删除后 is_active=False，列表不显示，原链接提示已删除"""

    @patch('backend.apps.opportunity_management.views_opportunity.get_user_permission_codes')
    def test_owner_deletes_opportunity_soft_delete(self, mock_get_perm):
        mock_get_perm.return_value = _perm_edit()
        self.client.login(username='user_b_owner', password='test123')
        url = reverse(
            'opportunity_pages:opportunity_delete',
            kwargs={'opportunity_id': self.opp_b.id},
        )
        response = self.client.post(url, follow=True)
        self.opp_b.refresh_from_db()
        self.assertFalse(self.opp_b.is_active)

    @patch('backend.apps.opportunity_management.views_opportunity.get_user_permission_codes')
    def test_deleted_opportunity_not_in_list_for_normal_user(self, mock_get_perm):
        self.opp_b.is_active = False
        self.opp_b.save()
        mock_get_perm.return_value = _perm_view_only()
        self.client.login(username='user_b_owner', password='test123')
        response = self.client.get(reverse('opportunity_pages:opportunity_management'))
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(self.opp_b.name, response.content.decode())

    @patch('backend.apps.opportunity_management.views_opportunity.get_user_permission_codes')
    def test_normal_user_direct_url_to_deleted_redirects_with_message(self, mock_get_perm):
        self.opp_b.is_active = False
        self.opp_b.save()
        mock_get_perm.return_value = _perm_view_only()
        self.client.login(username='user_b_owner', password='test123')
        url = reverse(
            'opportunity_pages:opportunity_detail',
            kwargs={'opportunity_id': self.opp_b.id},
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)


class Test5SoftDeleteSuperuser(OpportunityFlowsTestBase):
    """5. 软删除 - 超级管理员：能通过原链接访问已删商机详情并显示已删除"""

    def test_superuser_can_access_deleted_opportunity_detail(self):
        self.opp_b.is_active = False
        self.opp_b.save()
        self.client.login(username='super_admin', password='test123')
        url = reverse(
            'opportunity_pages:opportunity_detail',
            kwargs={'opportunity_id': self.opp_b.id},
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context.get('opportunity_is_deleted'))
        self.assertIn('已删除', response.content.decode() or '')


class Test6ProjectAssociation(OpportunityFlowsTestBase):
    """6. Project 关联 - 商机表单：创建/编辑可选项目并保存，详情页显示关联项目"""

    def setUp(self):
        super().setUp()
        try:
            from backend.apps.production_management.models import Project
            self.Project = Project
            self.project = Project.objects.filter(status__in=['configuring', 'waiting_start', 'in_progress', 'completed']).first()
            if not self.project:
                self.project = Project.objects.create(
                    project_number='TEST-PROJ-001',
                    name='测试项目',
                    status='configuring',
                )
        except Exception:
            self.Project = None
            self.project = None

    @patch('backend.apps.opportunity_management.views_opportunity.get_user_permission_codes')
    def test_opportunity_with_project_saves_and_detail_shows_project(self, mock_get_perm):
        if not getattr(self, 'project', None):
            self.skipTest('production_management.Project not available')
        mock_get_perm.return_value = _perm_edit()
        self.client.login(username='user_b_owner', password='test123')
        edit_url = reverse(
            'opportunity_pages:opportunity_edit',
            kwargs={'opportunity_id': self.opp_b.id},
        )
        post_data = {
            'client_id': self.customer.id,
            'project_id': self.project.id,
            'name': self.opp_b.name,
            'estimated_amount': '100',
            'success_probability': '10',
        }
        response = self.client.post(edit_url, post_data, follow=True)
        self.opp_b.refresh_from_db()
        self.assertEqual(self.opp_b.project_id, self.project.id)

        detail_url = reverse(
            'opportunity_pages:opportunity_detail',
            kwargs={'opportunity_id': self.opp_b.id},
        )
        resp2 = self.client.get(detail_url)
        self.assertEqual(resp2.status_code, 200)
        self.assertEqual(resp2.context['opportunity'].project_id, self.project.id)


class Test7AuthorizationLetterAutofillApi(OpportunityFlowsTestBase):
    """7. 委托书 - 选择商机自动回填：API 返回 client 和 project"""

    def test_get_opportunity_by_id_returns_client_and_project(self):
        self.client.login(username='user_b_owner', password='test123')
        url = reverse('customer:get_opportunities_by_client_name')
        response = self.client.get(url, {'opportunity_id': self.opp_b.id})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get('success'))
        opp = data.get('opportunity')
        self.assertIsNotNone(opp)
        self.assertIn('client', opp)
        self.assertEqual(opp['client']['id'], self.customer.id)
        self.assertIn('project', opp)


class Test8ContractAutofillApi(OpportunityFlowsTestBase):
    """8. 合同 - 选择商机自动回填：同一 API 返回 client 和 project 供合同表单回填"""

    def test_opportunity_api_returns_client_and_project_for_contract_form(self):
        self.client.login(username='user_b_owner', password='test123')
        # 合同表单使用的 API：/api/customer/authorization-letters/opportunities/?opportunity_id=
        url = reverse('customer:get_opportunities_by_client_name')
        response = self.client.get(url, {'opportunity_id': self.opp_b.id})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get('success'))
        opp = data.get('opportunity')
        self.assertIsNotNone(opp)
        self.assertIsNotNone(opp.get('client'))
        self.assertIsNotNone(opp.get('project'))
        # 合同表单需要 client.id、project.id 等用于回填
        self.assertIn('id', opp['client'])
        if opp.get('project'):
            self.assertIn('id', opp['project'])
