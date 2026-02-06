# -*- coding: utf-8 -*-
"""
CI 守门测试入口：公司隔离（P0 范围）。

本模块为 CI 守门测试占位入口，用于断言 P0 范围内关键模型
（User、Department、Role、Plan、StrategicGoal、ApprovalInstance）
的查询必须带公司隔离（company_id 或 apply_company_scope / apply_goal_company_scope）。

具体测试用例由负责人提供后填入下方，可包括但不限于：
- ViewSet get_queryset 是否应用 company 过滤
- 列表/选人接口是否按 request.user.company_id 隔离
- recent_approvals 是否按 applicant__company_id 过滤
"""
from django.test import TestCase


class TestCompanyIsolationGuard(TestCase):
    """公司隔离守门测试（占位：此处接入用户提供的测试代码）。"""

    def test_placeholder_company_isolation_guard(self):
        """占位：此处接入 CI 守门测试（用户提供测试代码）。"""
        # 预留：断言 User/Department/Role/Plan/StrategicGoal/recent_approvals 等
        # 业务入口查询均带 company 隔离
        pass
