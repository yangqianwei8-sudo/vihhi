"""
审批流程引擎常量：适用模型选项等，供 Admin 与业务前端共用。
"""
# 定义每个模型对应的需要审批的表单列表（用于 Admin 具体表单筛选）
# 使用表单的主标题名称（用户在页面上看到的标题）
MODEL_FORM_MAP = {
    'plan': [
        ('plan', '创建计划'),
        ('strategicgoal', '创建战略目标'),
        ('plandecision', '计划决策'),
        ('planadjustment', '申请调整'),
        ('goaladjustment', '目标调整申请'),
    ],
    'businesscontract': [
        ('businesscontract', '创建合同'),
    ],
    'businessopportunity': [
        ('businessopportunity', '创建商机'),
    ],
    'project': [
        ('project', '创建项目'),
    ],
    'client': [
        ('client', '创建客户'),
    ],
    'strategicgoal': [
        ('strategicgoal', '创建战略目标'),
        ('goaladjustment', '目标调整申请'),
    ],
    'case': [
        ('case', '创建诉讼案件'),
    ],
    'litigationexpense': [
        ('litigationexpense', '创建诉讼费用'),
    ],
    'sealborrowing': [
        ('sealborrowing', '申请借用印章'),
    ],
    'sealusage': [
        ('sealusage', '申请用印'),
    ],
}

# 定义可用的业务模型选项（流程可绑定的用例）
# 模型名称使用小写，对应 Django ContentType 的 model 字段值
APPLICABLE_MODEL_CHOICES = [
    # 客户管理模块
    ('client', '客户 (Client)'),
    ('businesscontract', '合同 (BusinessContract)'),
    ('businessopportunity', '商机 (BusinessOpportunity)'),
    # 项目管理模块
    ('project', '项目 (Project)'),
    # 计划管理模块
    ('plan', '计划 (Plan)'),
    ('strategicgoal', '战略目标 (StrategicGoal)'),
    # 诉讼管理模块
    ('case', '诉讼案件 (Case)'),
    ('litigationexpense', '诉讼费用 (LitigationExpense)'),
    # 生产管理模块
    ('productiontask', '生产任务 (ProductionTask)'),
    ('productionplan', '生产计划 (ProductionPlan)'),
    # 结算管理模块
    ('settlement', '结算单 (Settlement)'),
    ('payment', '付款单 (Payment)'),
    # 财务管理模块
    ('invoice', '发票 (Invoice)'),
    ('fundflow', '资金流水 (FundFlow)'),
    # 行政管理模块
    ('vehiclebooking', '车辆预订 (VehicleBooking)'),
    ('meetingroombooking', '会议室预订 (MeetingRoomBooking)'),
    ('sealborrowing', '印章借用 (SealBorrowing)'),
    ('sealusage', '用印申请 (SealUsage)'),
    # 人事管理模块
    ('employee', '员工 (Employee)'),
    ('attendance', '考勤记录 (Attendance)'),
    # 档案管理模块
    ('archive', '档案 (Archive)'),
    ('document', '文档 (Document)'),
    # 任务协作模块
    ('task', '任务 (Task)'),
    ('collaborationtask', '协作任务 (CollaborationTask)'),
    # 交付客户模块
    ('deliveryrecord', '交付记录 (DeliveryRecord)'),
    ('deliveryfile', '交付文件 (DeliveryFile)'),
]
