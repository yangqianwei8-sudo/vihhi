"""
合同管理模块工具函数
"""

from django.utils import timezone
from datetime import datetime
from .constants import CONTRACT_NUMBER_PREFIX


def generate_contract_number():
    """
    生成合同编号
    格式：VIH-CON-YYYY-NNNN
    
    Returns:
        str: 合同编号
    """
    from backend.apps.production_management.models import BusinessContract
    
    current_year = timezone.now().year
    
    # 查找当前年度最大的合同编号
    max_contract = BusinessContract.objects.filter(
        contract_number__startswith=f'{CONTRACT_NUMBER_PREFIX}-{current_year}-'
    ).order_by('-contract_number').first()
    
    if max_contract and max_contract.contract_number:
        try:
            # 提取序号部分
            parts = max_contract.contract_number.split('-')
            if len(parts) >= 4:
                seq = int(parts[-1]) + 1
            else:
                seq = 1
        except (ValueError, IndexError):
            seq = 1
    else:
        seq = 1
    
    # 生成新编号
    contract_number = f'{CONTRACT_NUMBER_PREFIX}-{current_year}-{seq:04d}'
    
    return contract_number


def calculate_contract_period(start_date, end_date):
    """
    计算合同期限（天数）
    
    Args:
        start_date: 开始日期
        end_date: 结束日期
        
    Returns:
        int: 合同期限（天），如果日期无效返回None
    """
    if not start_date or not end_date:
        return None
    
    if end_date < start_date:
        return None
    
    delta = end_date - start_date
    return delta.days


def calculate_unpaid_amount(contract_amount, payment_amount):
    """
    计算未回款金额
    
    Args:
        contract_amount: 合同金额
        payment_amount: 已回款金额
        
    Returns:
        decimal.Decimal: 未回款金额
    """
    if not contract_amount:
        return 0
    
    if not payment_amount:
        payment_amount = 0
    
    unpaid = contract_amount - payment_amount
    return max(unpaid, 0)


def can_edit_contract(contract, user):
    """
    判断用户是否可以编辑合同
    
    Args:
        contract: 合同对象
        user: 用户对象
        
    Returns:
        bool: 是否可以编辑
    """
    if not user or not user.is_authenticated:
        return False
    
    # 超级用户可以编辑
    if user.is_superuser:
        return True
    
    # 创建人可以编辑（草稿状态）
    if contract.created_by == user and contract.status == 'draft':
        return True
    
    # 检查编辑权限
    from .permissions import check_contract_permission, PERMISSION_EDIT
    return check_contract_permission(user, PERMISSION_EDIT)


def can_delete_contract(contract, user):
    """
    判断用户是否可以删除合同
    
    Args:
        contract: 合同对象
        user: 用户对象
        
    Returns:
        bool: 是否可以删除
    """
    if not user or not user.is_authenticated:
        return False
    
    # 超级用户可以删除
    if user.is_superuser:
        return True
    
    # 只有草稿状态的合同可以被删除
    if contract.status != 'draft':
        return False
    
    # 创建人可以删除
    if contract.created_by == user:
        return True
    
    # 检查删除权限
    from .permissions import check_contract_permission, PERMISSION_DELETE
    return check_contract_permission(user, PERMISSION_DELETE)


def can_approve_contract(contract, user):
    """
    判断用户是否可以审核合同
    
    Args:
        contract: 合同对象
        user: 用户对象
        
    Returns:
        bool: 是否可以审核
    """
    if not user or not user.is_authenticated:
        return False
    
    # 超级用户可以审核
    if user.is_superuser:
        return True
    
    # 检查审核权限
    from .permissions import check_contract_permission, PERMISSION_APPROVE
    return check_contract_permission(user, PERMISSION_APPROVE)


def get_contract_status_display(status):
    """
    获取合同状态显示文本
    
    Args:
        status: 状态代码
        
    Returns:
        str: 状态显示文本
    """
    from .constants import CONTRACT_STATUS_CHOICES
    
    for code, label in CONTRACT_STATUS_CHOICES:
        if code == status:
            return label
    
    return status

