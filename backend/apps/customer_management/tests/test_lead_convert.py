"""
线索转化单元测试 + 手工测试步骤

验证要点：
- Lead claim 人（responsible_user）转化后 Client.responsible_user 必须为该用户
- 幂等保护：已 converted 直接跳转

手工测试步骤（至少 6 条）：
1. 创建线索并认领：新建线索，认领为当前用户，转化后检查客户详情中负责人为当前用户
2. 未认领线索转化：新建线索不认领，以用户 A 登录转化，检查客户负责人为 A
3. 幂等：已转化线索再次点击转化，应提示「已转化为客户」并跳转到客户详情
4. 有跟进记录时创建 CustomerRelationship：线索填写 latest_followup_note 后转化，客户详情应有跟进记录
5. description 追溯：转化后客户描述中含【线索转化跟进 来源=Lead】及时间戳
6. 超长跟进内容截断：线索填写超长 latest_followup_note，转化后描述不超过限制长度
"""
from django.test import TestCase, Client as TestClient
from django.contrib.auth import get_user_model
from django.urls import reverse

from backend.apps.customer_management.models import (
    CustomerLead, Client, ClientType, CustomerRelationship,
)

User = get_user_model()


class LeadConvertTests(TestCase):
    """线索转化：负责人一致性 + 幂等保护"""

    def setUp(self):
        self.client = TestClient()
        self.user_a = User.objects.create_user(username="user_a", password="pass123")
        self.user_b = User.objects.create_user(username="user_b", password="pass123")
        self.client_type = ClientType.objects.create(
            code="test", name="测试类型", is_active=True
        )

    def test_convert_client_responsible_user_matches_lead_claimant(self):
        """Lead 认领人转化后，Client.responsible_user 必须为该用户"""
        lead = CustomerLead.objects.create(
            company_name="测试公司A",
            contact_name="张三",
            contact_phone="13800138000",
            lead_source="other",
            created_by=self.user_a,
            responsible_user=self.user_a,  # user_a 认领
        )
        self.client.force_login(self.user_a)
        url = reverse("customer_pages:customer_lead_convert", kwargs={"lead_id": lead.id})
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/customers/", resp.url)
        lead.refresh_from_db()
        self.assertIsNotNone(lead.converted_client_id)
        c = lead.converted_client
        self.assertEqual(c.responsible_user_id, self.user_a.id)

    def test_convert_unclaimed_lead_uses_current_user_as_responsible(self):
        """未认领线索转化时，Client.responsible_user 为当前用户"""
        lead = CustomerLead.objects.create(
            company_name="测试公司B",
            contact_name="李四",
            lead_source="other",
            created_by=self.user_a,
            responsible_user=None,  # 未认领
        )
        self.client.force_login(self.user_b)
        url = reverse("customer_pages:customer_lead_convert", kwargs={"lead_id": lead.id})
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, 302)
        lead.refresh_from_db()
        c = lead.converted_client
        self.assertEqual(c.responsible_user_id, self.user_b.id)

    def test_convert_idempotent_redirects_to_client(self):
        """已转化线索再次请求，直接跳转到 converted_client"""
        lead = CustomerLead.objects.create(
            company_name="测试公司C",
            contact_name="王五",
            lead_source="other",
            created_by=self.user_a,
            responsible_user=self.user_a,
        )
        c = Client.objects.create(
            name="测试公司C",
            client_type=self.client_type,
            created_by=self.user_a,
            responsible_user=self.user_a,
        )
        lead.converted_client = c
        lead.follow_status = "converted"
        lead.save()

        self.client.force_login(self.user_a)
        url = reverse("customer_pages:customer_lead_convert", kwargs={"lead_id": lead.id})
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, 302)
        self.assertIn(str(c.id), resp.url)
