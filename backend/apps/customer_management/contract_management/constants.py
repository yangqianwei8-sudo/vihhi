"""
合同管理模块常量定义
"""

# 合同状态
CONTRACT_STATUS_DRAFT = 'draft'  # 合同草稿
CONTRACT_STATUS_DISPUTE = 'dispute'  # 合同争议
CONTRACT_STATUS_FINALIZED = 'finalized'  # 合同定稿
CONTRACT_STATUS_PARTY_B_SIGNED = 'party_b_signed'  # 我方签章
CONTRACT_STATUS_SIGNED = 'signed'  # 对方签章（双方都已签章）
CONTRACT_STATUS_EFFECTIVE = 'effective'  # 已生效
CONTRACT_STATUS_EXECUTING = 'executing'  # 执行中
CONTRACT_STATUS_COMPLETED = 'completed'  # 已完成
CONTRACT_STATUS_TERMINATED = 'terminated'  # 已终止
CONTRACT_STATUS_CANCELLED = 'cancelled'  # 已取消

CONTRACT_STATUS_CHOICES = [
    (CONTRACT_STATUS_DRAFT, '合同草稿'),
    (CONTRACT_STATUS_DISPUTE, '合同争议'),
    (CONTRACT_STATUS_FINALIZED, '合同定稿'),
    (CONTRACT_STATUS_PARTY_B_SIGNED, '我方签章'),
    (CONTRACT_STATUS_SIGNED, '对方签章'),
    (CONTRACT_STATUS_EFFECTIVE, '已生效'),
    (CONTRACT_STATUS_EXECUTING, '执行中'),
    (CONTRACT_STATUS_COMPLETED, '已完成'),
    (CONTRACT_STATUS_TERMINATED, '已终止'),
    (CONTRACT_STATUS_CANCELLED, '已取消'),
]

# 合同类型
CONTRACT_TYPE_STRATEGIC = 'strategic'
CONTRACT_TYPE_FRAMEWORK = 'framework'
CONTRACT_TYPE_PROJECT = 'project'
CONTRACT_TYPE_INTENT = 'intent'
CONTRACT_TYPE_SUPPLEMENT = 'supplement'
CONTRACT_TYPE_CHANGE = 'change'
CONTRACT_TYPE_TERMINATION = 'termination'
CONTRACT_TYPE_OTHER = 'other'

CONTRACT_TYPE_CHOICES = [
    (CONTRACT_TYPE_STRATEGIC, '战略合同'),
    (CONTRACT_TYPE_FRAMEWORK, '框架合同'),
    (CONTRACT_TYPE_PROJECT, '项目合同'),
    (CONTRACT_TYPE_INTENT, '意向合同'),
    (CONTRACT_TYPE_SUPPLEMENT, '补充协议'),
    (CONTRACT_TYPE_CHANGE, '变更协议'),
    (CONTRACT_TYPE_TERMINATION, '终止协议'),
    (CONTRACT_TYPE_OTHER, '其他'),
]

# 审核状态
APPROVAL_STATUS_PENDING = 'pending'
APPROVAL_STATUS_APPROVED = 'approved'
APPROVAL_STATUS_REJECTED = 'rejected'
APPROVAL_STATUS_CANCELLED = 'cancelled'

APPROVAL_STATUS_CHOICES = [
    (APPROVAL_STATUS_PENDING, '待审核'),
    (APPROVAL_STATUS_APPROVED, '已通过'),
    (APPROVAL_STATUS_REJECTED, '已拒绝'),
    (APPROVAL_STATUS_CANCELLED, '已取消'),
]

# 文件类型
FILE_TYPE_CONTRACT = 'contract'
FILE_TYPE_ATTACHMENT = 'attachment'
FILE_TYPE_CHANGE = 'change'
FILE_TYPE_APPROVAL = 'approval'
FILE_TYPE_SIGNATURE = 'signature'
FILE_TYPE_OTHER = 'other'

FILE_TYPE_CHOICES = [
    (FILE_TYPE_CONTRACT, '合同原件'),
    (FILE_TYPE_ATTACHMENT, '附件'),
    (FILE_TYPE_CHANGE, '变更文件'),
    (FILE_TYPE_APPROVAL, '审核文件'),
    (FILE_TYPE_SIGNATURE, '签署文件'),
    (FILE_TYPE_OTHER, '其他'),
]

# 提醒类型
REMINDER_TYPE_EXPIRY = 'expiry'
REMINDER_TYPE_PAYMENT = 'payment'
REMINDER_TYPE_RISK = 'risk'
REMINDER_TYPE_TASK = 'task'

REMINDER_TYPE_CHOICES = [
    (REMINDER_TYPE_EXPIRY, '到期提醒'),
    (REMINDER_TYPE_PAYMENT, '付款提醒'),
    (REMINDER_TYPE_RISK, '风险预警'),
    (REMINDER_TYPE_TASK, '任务提醒'),
]

# 权限代码
PERMISSION_VIEW = 'contract_management.contract.view'
PERMISSION_CREATE = 'contract_management.contract.create'
PERMISSION_EDIT = 'contract_management.contract.edit'
PERMISSION_DELETE = 'contract_management.contract.delete'
PERMISSION_APPROVE = 'contract_management.contract.approve'
PERMISSION_SIGN = 'contract_management.contract.sign'
PERMISSION_CHANGE = 'contract_management.contract.change'
PERMISSION_FILE_MANAGE = 'contract_management.contract.file.manage'

# 合同编号前缀
CONTRACT_NUMBER_PREFIX = 'VIH-CON'

# 分页设置
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100

