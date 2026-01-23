"""
通用审批流程服务使用示例

这个文件展示了如何在各个业务模块中使用 UniversalApprovalService
"""

# ==================== 示例1：合同审批服务 ====================

from backend.apps.workflow_engine.services.universal_approval import UniversalApprovalService
# from backend.apps.customer_management.models import BusinessContract


class ContractApprovalService(UniversalApprovalService):
    """合同审批服务示例"""
    
    WORKFLOW_CODE = 'contract_approval'
    # CONTENT_MODEL = BusinessContract
    
    def validate_before_submit(self, obj, applicant):
        """提交审批前的验证"""
        # 检查合同状态
        if hasattr(obj, 'status') and obj.status != 'draft':
            raise ValueError('只有草稿状态的合同可以提交审批')
        
        # 检查必填字段
        if hasattr(obj, 'contract_amount') and not obj.contract_amount:
            raise ValueError('合同金额不能为空')
        
        # 检查金额阈值
        if hasattr(obj, 'contract_amount') and obj.contract_amount > 1000000:
            raise ValueError('金额超过100万需要特殊审批流程')


# ==================== 示例2：计划审批服务 ====================

class PlanApprovalService(UniversalApprovalService):
    """计划审批服务示例"""
    
    WORKFLOW_CODE = 'plan_start_approval'
    
    def validate_before_submit(self, obj, applicant):
        """提交审批前的验证"""
        # 检查计划状态
        if hasattr(obj, 'status') and obj.status not in ['draft', 'cancelled']:
            raise ValueError('只有草稿或已取消状态的计划可以提交审批')
        
        # 检查验收标准
        if hasattr(obj, 'acceptance_criteria') and not obj.acceptance_criteria:
            raise ValueError('提交审批前必须填写验收标准')


# ==================== 示例3：使用方式 ====================

def example_submit_approval():
    """提交审批示例"""
    # 假设有一个合同对象
    # contract = BusinessContract.objects.get(id=1)
    # user = User.objects.get(username='tester1')
    
    # 创建服务实例
    service = ContractApprovalService()
    
    # 提交审批
    # instance = service.submit_approval(
    #     obj=contract,
    #     applicant=user,
    #     comment='申请审批合同'
    # )
    
    # if instance:
    #     print(f'审批编号：{instance.instance_number}')
    # else:
    #     print('审批流程未配置')


def example_approve():
    """审批操作示例"""
    service = ContractApprovalService()
    # user = User.objects.get(username='approver')
    
    # 审批通过
    # success = service.approve(
    #     instance_id=1,
    #     approver=user,
    #     comment='同意，合同条款符合要求'
    # )
    
    # 审批驳回
    # success = service.reject(
    #     instance_id=1,
    #     approver=user,
    #     comment='合同金额超出预算'
    # )


def example_get_status():
    """查询审批状态示例"""
    service = ContractApprovalService()
    # contract = BusinessContract.objects.get(id=1)
    
    # 获取审批状态
    # status = service.get_approval_status(contract)
    # 
    # print(f'是否有待审批：{status["has_pending"]}')
    # print(f'当前节点：{status["current_node"]}')
    # print(f'待审批人：{status["approvers"]}')
    # print(f'审批状态：{status["status"]}')


def example_create_workflow():
    """创建审批流程示例"""
    from backend.apps.system_management.models import User, Role
    
    # 获取创建人
    # creator = User.objects.filter(is_superuser=True).first()
    # finance_role = Role.objects.get(code='finance_director')
    # manager_role = Role.objects.get(code='general_manager')
    
    # 创建审批流程
    # workflow = UniversalApprovalService.create_workflow_from_config(
    #     code='contract_approval',
    #     name='合同审批流程',
    #     description='合同审批流程：部门经理 -> 财务总监 -> 总经理',
    #     category='合同管理',
    #     creator=creator,
    #     nodes_config=[
    #         {
    #             'name': '部门经理审批',
    #             'node_type': 'approval',
    #             'sequence': 1,
    #             'approver_type': 'department_manager',
    #             'approval_mode': 'single',
    #             'timeout_hours': 24,
    #         },
    #         {
    #             'name': '财务总监审批',
    #             'node_type': 'approval',
    #             'sequence': 2,
    #             'approver_type': 'role',
    #             'approval_mode': 'single',
    #             'approver_roles': [finance_role],
    #             'timeout_hours': 48,
    #         },
    #         {
    #             'name': '总经理审批',
    #             'node_type': 'approval',
    #             'sequence': 3,
    #             'approver_type': 'role',
    #             'approval_mode': 'single',
    #             'approver_roles': [manager_role],
    #             'timeout_hours': 72,
    #         },
    #     ]
    # )
    pass

