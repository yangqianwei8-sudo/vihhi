from django.core.management.base import BaseCommand
from django.db import transaction

from backend.apps.system_management.models import Role
from backend.apps.permission_management.models import PermissionItem


PERMISSION_DEFINITIONS = [
    # 生产管理（原项目中心）
    {"code": "production_management.view_all", "module": "生产管理", "action": "view_all", "name": "生产管理-查看全部", "description": "查看所有项目及统计信息"},
    {"code": "production_management.view_assigned", "module": "生产管理", "action": "view_assigned", "name": "生产管理-查看负责项目", "description": "查看本人相关项目数据"},
    {"code": "production_management.create", "module": "生产管理", "action": "create", "name": "生产管理-创建项目", "description": "创建新项目、录入基础信息"},
    {"code": "production_management.configure_team", "module": "生产管理", "action": "configure_team", "name": "生产管理-团队配置", "description": "配置项目团队成员及角色"},
    {"code": "production_management.monitor", "module": "生产管理", "action": "monitor", "name": "生产管理-项目监控", "description": "监控项目进度、风险、里程碑"},
    {"code": "production_management.archive", "module": "生产管理", "action": "archive", "name": "生产管理-项目归档", "description": "归档项目资料、导出报表"},
    {"code": "production_management.delete", "module": "生产管理", "action": "delete", "name": "生产管理-项目删除终止", "description": "删除或终止项目，需要审批"},
    {"code": "production_management.export", "module": "生产管理", "action": "export", "name": "生产管理-数据导出", "description": "导出项目数据并记录审计"},

    # 任务协作
    {"code": "task_collaboration.manage", "module": "任务协作", "action": "manage", "name": "任务协作-流程配置", "description": "配置任务流程、模板、审批节点"},
    {"code": "task_collaboration.assign", "module": "任务协作", "action": "assign", "name": "任务协作-任务分配", "description": "分配任务、调整进度、指派责任人"},
    {"code": "task_collaboration.execute", "module": "任务协作", "action": "execute", "name": "任务协作-任务执行", "description": "领取任务、提交成果、更新进度"},
    {"code": "task_collaboration.audit_timesheet", "module": "任务协作", "action": "audit_timesheet", "name": "任务协作-工时审核", "description": "审核工时填报与任务消耗"},
    {"code": "task_collaboration.view_all", "module": "任务协作", "action": "view_all", "name": "任务协作-查看全部", "description": "查看全局任务和协作动态"},
    {"code": "task_collaboration.comment", "module": "任务协作", "action": "comment", "name": "任务协作-留言沟通", "description": "在任务中留言、协作沟通"},

    # 交付客户
    {"code": "delivery_center.view", "module": "交付客户", "action": "view", "name": "收发管理-访问", "description": "查看收发管理导航与相关功能入口"},
    {"code": "delivery_center.view_all", "module": "交付客户", "action": "view_all", "name": "收发管理-查看全部", "description": "查看所有交付记录（不限创建人）"},
    {"code": "delivery_center.create", "module": "交付客户", "action": "create", "name": "收发管理-创建", "description": "创建交付记录"},
    {"code": "delivery_center.edit", "module": "交付客户", "action": "edit", "name": "收发管理-编辑", "description": "编辑交付记录"},
    {"code": "delivery_center.edit_assigned", "module": "交付客户", "action": "edit_assigned", "name": "收发管理-编辑分配", "description": "编辑自己创建的交付记录"},
    {"code": "delivery_center.view_statistics", "module": "交付客户", "action": "view_statistics", "name": "收发管理-查看统计", "description": "查看交付统计信息"},
    {"code": "delivery_portal.view", "module": "交付客户", "action": "view", "name": "交付门户-查看", "description": "查看交付成果、客户协同记录"},
    {"code": "delivery_portal.submit", "module": "交付客户", "action": "submit", "name": "交付门户-成果提交", "description": "提交交付成果、上传报告"},
    {"code": "delivery_portal.approve", "module": "交付客户", "action": "approve", "name": "交付门户-成果审核", "description": "审核或确认交付成果"},
    {"code": "delivery_portal.configure", "module": "交付客户", "action": "configure", "name": "交付门户-配置管理", "description": "配置客户门户、访问权限"},
    {"code": "delivery_portal.sign", "module": "交付客户", "action": "sign", "name": "交付门户-电子签章", "description": "完成交付电子签章确认"},

    # 结算管理
    {"code": "settlement_management.initiate", "module": "结算管理", "action": "initiate", "name": "结算管理-发起结算", "description": "发起项目结算流程"},
    {"code": "settlement_management.manage_output", "module": "结算管理", "action": "manage_output", "name": "结算管理-产值管理", "description": "管理项目产值与成本"},
    {"code": "settlement_management.view", "module": "结算管理", "action": "view", "name": "结算管理-查看", "description": "查看项目结算和合同结算单"},
    {"code": "settlement_management.settlement.view", "module": "结算管理", "action": "settlement.view", "name": "结算管理-查看结算", "description": "查看项目结算和合同结算单"},
    {"code": "settlement_management.settlement.create", "module": "结算管理", "action": "settlement.create", "name": "结算管理-创建结算", "description": "创建项目结算和合同结算单"},
    {"code": "settlement_management.settlement.manage", "module": "结算管理", "action": "settlement.manage", "name": "结算管理-管理结算", "description": "管理结算单，编辑和删除"},
    {"code": "settlement_management.settlement.finance_review", "module": "结算管理", "action": "settlement.finance_review", "name": "结算管理-财务审核", "description": "财务审核结算单"},
    {"code": "settlement_management.settlement.manager_approve", "module": "结算管理", "action": "settlement.manager_approve", "name": "结算管理-部门经理审批", "description": "部门经理审批结算单"},
    {"code": "settlement_management.settlement.gm_approve", "module": "结算管理", "action": "settlement.gm_approve", "name": "结算管理-总经理审批", "description": "总经理审批结算单"},
    {"code": "settlement_management.settlement.confirm", "module": "结算管理", "action": "settlement.confirm", "name": "结算管理-确认结算", "description": "确认结算单，更新合同结算金额"},
    {"code": "settlement_management.view_analysis", "module": "结算管理", "action": "view_analysis", "name": "结算管理-统计分析", "description": "查看结算统计与分析报表"},
    {"code": "settlement_management.payment_record.create", "module": "结算管理", "action": "payment_record.create", "name": "结算管理-创建回款记录", "description": "创建回款记录"},

    # 结算管理（结算相关权限，回款管理已独立为 payment_management）
    {"code": "settlement_center.view", "module": "结算管理", "action": "view", "name": "结算管理-查看", "description": "查看结算和回款管理"},
    {"code": "settlement_center.payment_record.create", "module": "结算管理", "action": "payment_record.create", "name": "结算管理-创建回款记录", "description": "创建回款记录"},
    {"code": "settlement_center.payment_record.view", "module": "结算管理", "action": "payment_record.view", "name": "结算管理-查看回款记录", "description": "查看回款记录"},
    {"code": "settlement_center.payment_record.confirm", "module": "结算管理", "action": "payment_record.confirm", "name": "结算管理-确认回款记录", "description": "确认回款记录"},
    
    # 回款管理（独立模块）
    {"code": "payment_management.view", "module": "回款管理", "action": "view", "name": "回款管理-查看", "description": "查看回款管理模块"},
    {"code": "payment_management.payment_plan.view", "module": "回款管理", "action": "payment_plan.view", "name": "回款管理-查看回款计划", "description": "查看回款计划列表和详情"},
    {"code": "payment_management.payment_plan.create", "module": "回款管理", "action": "payment_plan.create", "name": "回款管理-创建回款计划", "description": "创建回款计划"},
    {"code": "payment_management.payment_plan.manage", "module": "回款管理", "action": "payment_plan.manage", "name": "回款管理-管理回款计划", "description": "编辑和删除回款计划"},
    {"code": "payment_management.payment_record.view", "module": "回款管理", "action": "payment_record.view", "name": "回款管理-查看回款记录", "description": "查看回款记录列表和详情"},
    {"code": "payment_management.payment_record.create", "module": "回款管理", "action": "payment_record.create", "name": "回款管理-创建回款记录", "description": "创建回款记录"},
    {"code": "payment_management.payment_record.confirm", "module": "回款管理", "action": "payment_record.confirm", "name": "回款管理-确认回款记录", "description": "确认回款记录"},
    {"code": "payment_management.statistics.view", "module": "回款管理", "action": "statistics.view", "name": "回款管理-查看统计", "description": "查看回款统计和分析报表"},

    # 资源标准
    {"code": "resource_center.manage_library", "module": "资源标准", "action": "manage_library", "name": "资源标准-标准库维护", "description": "维护企业标准、模板、指标库"},
    {"code": "resource_center.manage_template", "module": "资源标准", "action": "manage_template", "name": "资源标准-模板管理", "description": "维护模板资源"},
    {"code": "resource_center.manage_professional", "module": "资源标准", "action": "manage_professional", "name": "资源标准-专业标准维护", "description": "维护各专业标准数据"},
    {"code": "resource_center.view", "module": "资源标准", "action": "view", "name": "资源标准-查看", "description": "查看知识库与参考资料"},
    {"code": "resource_center.contribute", "module": "资源标准", "action": "contribute", "name": "资源标准-知识贡献", "description": "提交知识库案例与资料"},
    {"code": "resource_center.data_maintenance", "module": "资源标准", "action": "data_maintenance", "name": "资源标准-数据维护", "description": "维护数据字典与基础数据"},

    # 客户管理（按《客户管理详细设计方案 v1.12》实现）
    # 客户信息管理
    {"code": "customer_management.client.view_assigned", "module": "客户管理", "action": "client.view_assigned", "name": "客户信息-查看本人负责", "description": "查看本人负责的客户"},
    {"code": "customer_management.client.view_department", "module": "客户管理", "action": "client.view_department", "name": "客户信息-查看本部门", "description": "查看本部门负责的客户"},
    {"code": "customer_management.client.view_all", "module": "客户管理", "action": "client.view_all", "name": "客户信息-查看全部", "description": "查看所有客户（不限负责人）"},
    {"code": "customer_management.client.view", "module": "客户管理", "action": "client.view", "name": "客户信息-查看", "description": "查看客户信息（根据权限自动分级：本人/本部门/全部）"},
    {"code": "customer_management.client.create", "module": "客户管理", "action": "client.create", "name": "客户信息-创建", "description": "创建新客户"},
    {"code": "customer_management.client.edit", "module": "客户管理", "action": "client.edit", "name": "客户信息-编辑", "description": "编辑客户信息"},
    {"code": "customer_management.client.delete", "module": "客户管理", "action": "client.delete", "name": "客户信息-删除", "description": "删除客户"},
    {"code": "customer_management.client.export", "module": "客户管理", "action": "client.export", "name": "客户信息-导出", "description": "导出客户数据"},
    {"code": "customer_management.client.approve", "module": "客户管理", "action": "client.approve", "name": "客户信息-审批", "description": "审批客户创建/修改申请"},
    
    # 客户人员管理
    {"code": "customer_management.contact.view", "module": "客户管理", "action": "contact.view", "name": "客户人员-查看", "description": "查看客户联系人信息"},
    {"code": "customer_management.contact.create", "module": "客户管理", "action": "contact.create", "name": "客户人员-创建", "description": "创建客户联系人"},
    {"code": "customer_management.contact.edit", "module": "客户管理", "action": "contact.edit", "name": "客户人员-编辑", "description": "编辑客户联系人信息"},
    {"code": "customer_management.contact.delete", "module": "客户管理", "action": "contact.delete", "name": "客户人员-删除", "description": "删除客户联系人"},
    
    # 客户关系管理
    {"code": "customer_management.relationship.view", "module": "客户管理", "action": "relationship.view", "name": "客户关系-查看", "description": "查看跟进与拜访记录"},
    {"code": "customer_management.relationship.create", "module": "客户管理", "action": "relationship.create", "name": "客户关系-创建", "description": "创建跟进与拜访记录"},
    {"code": "customer_management.relationship.edit", "module": "客户管理", "action": "relationship.edit", "name": "客户关系-编辑", "description": "编辑跟进与拜访记录"},
    {"code": "customer_management.relationship.delete", "module": "客户管理", "action": "relationship.delete", "name": "客户关系-删除", "description": "删除跟进与拜访记录"},
    {"code": "customer_management.relationship.upgrade", "module": "客户管理", "action": "relationship.upgrade", "name": "客户关系-关系升级", "description": "管理客户关系升级"},
    
    # 客户公海
    {"code": "customer_management.public_sea.view", "module": "客户管理", "action": "public_sea.view", "name": "客户公海-查看", "description": "查看客户公海列表"},
    {"code": "customer_management.public_sea.claim", "module": "客户管理", "action": "public_sea.claim", "name": "客户公海-认领", "description": "认领公海客户"},
    
    # 客户分析
    {"code": "customer_management.analysis.view", "module": "客户管理", "action": "analysis.view", "name": "客户分析-查看", "description": "查看客户价值分析、满意度分析"},
    
    
    # 商机管理
    {"code": "customer_management.opportunity", "module": "商机管理", "action": "opportunity", "name": "商机管理-商机挖掘", "description": "商机识别与跟进"},
    {"code": "customer_management.opportunity.view", "module": "商机管理", "action": "opportunity.view", "name": "商机管理-查看", "description": "查看商机列表和详情"},
    {"code": "customer_management.opportunity.view_all", "module": "商机管理", "action": "opportunity.view_all", "name": "商机管理-查看全部", "description": "查看所有商机（不限负责商务）"},
    {"code": "customer_management.opportunity.create", "module": "商机管理", "action": "opportunity.create", "name": "商机管理-创建", "description": "创建新商机"},
    {"code": "customer_management.opportunity.manage", "module": "商机管理", "action": "opportunity.manage", "name": "商机管理-管理", "description": "编辑和删除商机"},
    {"code": "customer_management.opportunity.approve", "module": "商机管理", "action": "opportunity.approve", "name": "商机管理-审批", "description": "审批商机报价"},
    {"code": "customer_management.quotation.view", "module": "商机管理", "action": "quotation.view", "name": "报价管理-查看", "description": "查看报价记录"},
    {"code": "customer_management.quotation.create", "module": "商机管理", "action": "quotation.create", "name": "报价管理-创建", "description": "创建报价记录"},
    {"code": "customer_management.quotation.manage", "module": "商机管理", "action": "quotation.manage", "name": "报价管理-管理", "description": "管理报价记录"},
    
    # 合同管理
    {"code": "customer_management.contract.view", "module": "合同管理", "action": "contract.view", "name": "合同管理-查看", "description": "查看合同信息、合同列表"},
    {"code": "customer_management.contract.create", "module": "合同管理", "action": "contract.create", "name": "合同管理-创建", "description": "创建合同"},
    {"code": "customer_management.contract.manage", "module": "合同管理", "action": "contract.manage", "name": "合同管理-管理", "description": "编辑和删除合同"},

    # 风险管理
    {"code": "risk_management.view", "module": "风险管理", "action": "view", "name": "风控中心-查看", "description": "查看风险事件、预警信息"},
    {"code": "risk_management.manage", "module": "风险管理", "action": "manage", "name": "风控中心-处理", "description": "处理风险事件、制定方案"},
    {"code": "risk_management.analyze", "module": "风险管理", "action": "analyze", "name": "风控中心-风险分析", "description": "分析风险趋势、生成报告"},
    {"code": "risk_management.configure", "module": "风险管理", "action": "configure", "name": "风控中心-配置", "description": "维护风险规则、预警设置"},

    # 系统管理
    {"code": "system_management.manage_users", "module": "系统管理", "action": "manage_users", "name": "系统管理-用户管理", "description": "管理用户账号、角色、组织"},
    {"code": "system_management.manage_settings", "module": "系统管理", "action": "manage_settings", "name": "系统管理-配置管理", "description": "维护系统配置、参数设置"},
    {"code": "system_management.view_settings", "module": "系统管理", "action": "view_settings", "name": "系统管理-查看设置", "description": "查看系统配置、参数"},
    {"code": "system_management.audit", "module": "系统管理", "action": "audit", "name": "系统管理-权限审计", "description": "执行权限审计、操作日志"},
    {"code": "system_management.backup", "module": "系统管理", "action": "backup", "name": "系统管理-数据备份", "description": "执行数据备份与恢复"},

    # 人事管理
    {"code": "personnel_management.view", "module": "人事管理", "action": "view", "name": "人事管理-查看", "description": "查看人事管理模块"},
    {"code": "personnel_management.manage", "module": "人事管理", "action": "manage", "name": "人事管理-管理", "description": "管理人事管理模块"},
    {"code": "personnel_management.employee.view", "module": "人事管理", "action": "employee.view", "name": "员工档案-查看", "description": "查看员工档案信息"},
    {"code": "personnel_management.employee.create", "module": "人事管理", "action": "employee.create", "name": "员工档案-创建", "description": "创建员工档案"},
    {"code": "personnel_management.employee.manage", "module": "人事管理", "action": "employee.manage", "name": "员工档案-管理", "description": "管理员工档案信息"},
    {"code": "personnel_management.attendance.view", "module": "人事管理", "action": "attendance.view", "name": "考勤-查看", "description": "查看考勤记录"},
    {"code": "personnel_management.attendance.manage", "module": "人事管理", "action": "attendance.manage", "name": "考勤-管理", "description": "管理考勤记录"},
    {"code": "personnel_management.leave.view", "module": "人事管理", "action": "leave.view", "name": "请假-查看", "description": "查看请假申请"},
    {"code": "personnel_management.leave.apply", "module": "人事管理", "action": "leave.apply", "name": "请假-申请", "description": "提交请假申请"},
    {"code": "personnel_management.leave.approve", "module": "人事管理", "action": "leave.approve", "name": "请假-审批", "description": "审批请假申请"},
    {"code": "personnel_management.training.view", "module": "人事管理", "action": "training.view", "name": "培训-查看", "description": "查看培训记录"},
    {"code": "personnel_management.training.create", "module": "人事管理", "action": "training.create", "name": "培训-创建", "description": "创建培训记录"},
    {"code": "personnel_management.training.manage", "module": "人事管理", "action": "training.manage", "name": "培训-管理", "description": "管理培训记录"},
    {"code": "personnel_management.performance.view", "module": "人事管理", "action": "performance.view", "name": "绩效-查看", "description": "查看绩效考核"},
    {"code": "personnel_management.performance.create", "module": "人事管理", "action": "performance.create", "name": "绩效-创建", "description": "创建绩效考核"},
    {"code": "personnel_management.performance.review", "module": "人事管理", "action": "performance.review", "name": "绩效-评价", "description": "评价绩效考核"},
    {"code": "personnel_management.salary.view", "module": "人事管理", "action": "salary.view", "name": "薪资-查看", "description": "查看薪资记录"},
    {"code": "personnel_management.salary.manage", "module": "人事管理", "action": "salary.manage", "name": "薪资-管理", "description": "管理薪资记录"},
    {"code": "personnel_management.contract.view", "module": "人事管理", "action": "contract.view", "name": "合同-查看", "description": "查看劳动合同"},
    {"code": "personnel_management.contract.create", "module": "人事管理", "action": "contract.create", "name": "合同-创建", "description": "创建劳动合同"},
    {"code": "personnel_management.contract.manage", "module": "人事管理", "action": "contract.manage", "name": "合同-管理", "description": "管理劳动合同"},
    
    # 档案管理
    {"code": "archive_management.view", "module": "档案管理", "action": "view", "name": "档案管理-查看", "description": "查看档案管理模块"},
    {"code": "archive_management.archive.view", "module": "档案管理", "action": "archive.view", "name": "档案管理-查看档案", "description": "查看档案列表和详情"},
    {"code": "archive_management.archive.create", "module": "档案管理", "action": "archive.create", "name": "档案管理-创建档案", "description": "创建档案"},
    {"code": "archive_management.archive.manage", "module": "档案管理", "action": "archive.manage", "name": "档案管理-管理档案", "description": "编辑和删除档案"},
    {"code": "archive_management.borrow.view", "module": "档案管理", "action": "borrow.view", "name": "档案管理-查看借阅", "description": "查看档案借阅记录"},
    {"code": "archive_management.borrow.create", "module": "档案管理", "action": "borrow.create", "name": "档案管理-创建借阅", "description": "创建档案借阅申请"},
    
    # 计划管理
    {"code": "plan_management.view", "module": "计划管理", "action": "view", "name": "计划管理-查看", "description": "查看计划管理模块"},
    {"code": "plan_management.plan.view", "module": "计划管理", "action": "plan.view", "name": "计划管理-查看计划", "description": "查看计划列表和详情"},
    {"code": "plan_management.plan.create", "module": "计划管理", "action": "plan.create", "name": "计划管理-创建计划", "description": "创建计划"},
    {"code": "plan_management.plan.manage", "module": "计划管理", "action": "plan.manage", "name": "计划管理-管理计划", "description": "编辑和删除计划"},
    {"code": "plan_management.approve_plan", "module": "计划管理", "action": "approve_plan", "name": "计划管理-审批计划", "description": "审批计划的启动/取消请求"},
    {"code": "plan_management.approve", "module": "计划管理", "action": "approve", "name": "计划管理-审批", "description": "审批计划（兼容别名）"},
    {"code": "plan_management.goal.view", "module": "计划管理", "action": "goal.view", "name": "计划管理-查看目标", "description": "查看战略目标"},
    {"code": "plan_management.goal.create", "module": "计划管理", "action": "goal.create", "name": "计划管理-创建目标", "description": "创建战略目标"},
    {"code": "plan_management.manage_goal", "module": "计划管理", "action": "manage_goal", "name": "计划管理-管理目标", "description": "管理战略目标（创建、编辑、删除、分解）"},
    
    # 诉讼管理
    {"code": "litigation_management.view", "module": "诉讼管理", "action": "view", "name": "诉讼管理-查看", "description": "查看诉讼管理模块"},
    {"code": "litigation_management.case.view", "module": "诉讼管理", "action": "case.view", "name": "诉讼管理-查看案件", "description": "查看诉讼案件列表和详情"},
    {"code": "litigation_management.case.create", "module": "诉讼管理", "action": "case.create", "name": "诉讼管理-创建案件", "description": "创建诉讼案件"},
    {"code": "litigation_management.case.manage", "module": "诉讼管理", "action": "case.manage", "name": "诉讼管理-管理案件", "description": "编辑和删除诉讼案件"},
    {"code": "litigation_management.expense.view", "module": "诉讼管理", "action": "expense.view", "name": "诉讼管理-查看费用", "description": "查看诉讼费用"},
    {"code": "litigation_management.expense.create", "module": "诉讼管理", "action": "expense.create", "name": "诉讼管理-创建费用", "description": "创建诉讼费用记录"},
    
    # 财务管理
    {"code": "financial_management.view", "module": "财务管理", "action": "view", "name": "财务管理-查看", "description": "查看财务管理模块"},
    {"code": "financial_management.account.view", "module": "财务管理", "action": "account.view", "name": "财务管理-查看科目", "description": "查看会计科目"},
    {"code": "financial_management.account.manage", "module": "财务管理", "action": "account.manage", "name": "财务管理-管理科目", "description": "管理会计科目"},
    {"code": "financial_management.voucher.view", "module": "财务管理", "action": "voucher.view", "name": "财务管理-查看凭证", "description": "查看记账凭证"},
    {"code": "financial_management.voucher.create", "module": "财务管理", "action": "voucher.create", "name": "财务管理-创建凭证", "description": "创建记账凭证"},
    {"code": "financial_management.budget.view", "module": "财务管理", "action": "budget.view", "name": "财务管理-查看预算", "description": "查看预算管理"},
    {"code": "financial_management.budget.manage", "module": "财务管理", "action": "budget.manage", "name": "财务管理-管理预算", "description": "管理预算"},
    
    # 行政管理
    {"code": "administrative_management.view", "module": "行政管理", "action": "view", "name": "行政管理-查看", "description": "查看行政管理模块"},
    {"code": "administrative_management.affair.view", "module": "行政管理", "action": "affair.view", "name": "行政管理-查看事务", "description": "查看行政事务列表和详情"},
    {"code": "administrative_management.affair.create", "module": "行政管理", "action": "affair.create", "name": "行政管理-创建事务", "description": "创建行政事务"},
    {"code": "administrative_management.supplies.view", "module": "行政管理", "action": "supplies.view", "name": "行政管理-查看用品", "description": "查看办公用品管理"},
    {"code": "administrative_management.supplies.manage", "module": "行政管理", "action": "supplies.manage", "name": "行政管理-管理用品", "description": "管理办公用品"},
    {"code": "administrative_management.meeting.view", "module": "行政管理", "action": "meeting.view", "name": "行政管理-查看会议", "description": "查看会议管理"},
    {"code": "administrative_management.meeting.manage", "module": "行政管理", "action": "meeting.manage", "name": "行政管理-管理会议", "description": "管理会议和会议室"},
]


class Command(BaseCommand):
    help = "Seed permission items from PERMISSION_DEFINITIONS"

    def handle(self, *args, **options):
        created_count = 0
        updated_count = 0
        
        with transaction.atomic():
            for perm_def in PERMISSION_DEFINITIONS:
                perm_item, created = PermissionItem.objects.update_or_create(
                    code=perm_def['code'],
                    defaults={
                        'module': perm_def['module'],
                        'action': perm_def['action'],
                        'name': perm_def['name'],
                        'description': perm_def['description'],
                        'is_active': perm_def.get('is_active', True),  # 支持 is_active 字段
                    }
                )
                if created:
                    created_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'✓ 创建权限: {perm_def["code"]}')
                    )
                else:
                    updated_count += 1
                    self.stdout.write(
                        self.style.WARNING(f'↻ 更新权限: {perm_def["code"]}')
                    )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n完成！创建 {created_count} 个权限，更新 {updated_count} 个权限。'
            )
        )
