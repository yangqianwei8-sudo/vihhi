# 商机权限统一检查测试
# 验证：view_all 用户能看全部；普通用户只能看自己 business_manager 的商机；详情/编辑/流转/删除权限判定一致

import unittest
from unittest.mock import Mock

from backend.apps.opportunity_management.perm_check import (
    opportunity_can_view,
    opportunity_can_view_all,
    opportunity_can_create,
    opportunity_can_edit,
    opportunity_can_delete,
    opportunity_can_manage,
    opportunity_can_access_detail,
    opportunity_can_access_edit,
    expand_permission_set_for_nav,
    PREFIX,
    LEGACY_PREFIX,
)


class OpportunityPermCheckTests(unittest.TestCase):
    """商机权限检查单元测试"""

    def test_view_all_user_sees_all(self):
        """view_all 用户能看全部商机"""
        permission_set = {
            f'{PREFIX}.view',
            f'{PREFIX}.view_all',
        }
        user = Mock(id=1)
        opportunity = Mock(business_manager_id=999)  # 其他用户负责的商机
        self.assertTrue(opportunity_can_view_all(permission_set))
        self.assertTrue(opportunity_can_access_detail(user, opportunity, permission_set))

    def test_view_all_legacy_code_works(self):
        """兼容 customer_management.opportunity.view_all"""
        permission_set = {f'{LEGACY_PREFIX}.view_all'}
        self.assertTrue(opportunity_can_view_all(permission_set))

    def test_normal_user_only_sees_own_opportunities(self):
        """普通用户只能看自己 business_manager 的商机"""
        permission_set = {f'{PREFIX}.view'}  # 无 view_all
        user = Mock(id=1)
        # 自己负责的商机 -> 可查看
        own_opp = Mock(business_manager_id=1)
        self.assertTrue(opportunity_can_access_detail(user, own_opp, permission_set))
        # 他人负责的商机 -> 不可查看
        other_opp = Mock(business_manager_id=999)
        self.assertFalse(opportunity_can_access_detail(user, other_opp, permission_set))

    def test_normal_user_without_view_cannot_access(self):
        """无 view 权限的用户不能查看任何商机"""
        permission_set = set()
        user = Mock(id=1)
        own_opp = Mock(business_manager_id=1)
        self.assertFalse(opportunity_can_access_detail(user, own_opp, permission_set))

    def test_all_permission_grants_full_access(self):
        """__all__ 权限拥有全部能力"""
        permission_set = {'__all__'}
        user = Mock(id=1)
        opp = Mock(business_manager_id=999)
        self.assertTrue(opportunity_can_view_all(permission_set))
        self.assertTrue(opportunity_can_access_detail(user, opp, permission_set))
        self.assertTrue(opportunity_can_access_edit(user, opp, permission_set))
        self.assertTrue(opportunity_can_edit(permission_set))
        self.assertTrue(opportunity_can_delete(permission_set))

    def test_detail_edit_delete_consistent(self):
        """详情/编辑/流转/删除权限判定一致：edit 或负责人可操作"""
        # 有 edit 权限的用户可操作任意商机
        perm_edit = {f'{PREFIX}.edit'}
        user = Mock(id=1)
        other_opp = Mock(business_manager_id=999)
        self.assertTrue(opportunity_can_access_edit(user, other_opp, perm_edit))

        # 无 edit 权限但为负责人的用户可操作自己的商机
        perm_view_only = {f'{PREFIX}.view'}
        own_opp = Mock(business_manager_id=1)
        self.assertTrue(opportunity_can_access_edit(user, own_opp, perm_view_only))

        # 无 edit 且非负责人 -> 不可操作
        self.assertFalse(opportunity_can_access_edit(user, other_opp, perm_view_only))

    def test_legacy_edit_code_works(self):
        """兼容 customer_management.opportunity.edit"""
        permission_set = {f'{LEGACY_PREFIX}.edit'}
        self.assertTrue(opportunity_can_edit(permission_set))

    def test_expand_permission_set_for_nav(self):
        """菜单权限集扩展：legacy 码视为 canonical"""
        permission_set = {f'{LEGACY_PREFIX}.view'}
        expanded = expand_permission_set_for_nav(permission_set)
        self.assertIn(f'{PREFIX}.view', expanded)
        self.assertIn(f'{LEGACY_PREFIX}.view', expanded)
