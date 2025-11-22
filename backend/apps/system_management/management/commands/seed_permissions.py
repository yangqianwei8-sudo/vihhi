from django.core.management.base import BaseCommand
from django.db import transaction

from backend.apps.system_management.models import Role
from backend.apps.permission_management.models import PermissionItem


PERMISSION_DEFINITIONS = [
    # 项目中心
    {"code": "project_center.view_all", "module": "项目中心", "action": "view_all", "name": "项目中心-查看全部", "description": "查看所有项目及统计信息"},
    {"code": "project_center.view_assigned", "module": "项目中心", "action": "view_assigned", "name": "项目中心-查看负责项目", "description": "查看本人相关项目数据"},
    {"code": "project_center.create", "module": "项目中心", "action": "create", "name": "项目中心-创建项目", "description": "创建新项目、录入基础信息"},
    {"code": "project_center.initiation.create", "module": "项目中心", "action": "initiation.create", "name": "项目立项-创建立项", "description": "创建项目立项申请，填写立项信息"},
    {"code": "project_center.initiation.edit", "module": "项目中心", "action": "initiation.edit", "name": "项目立项-编辑立项", "description": "编辑项目立项信息（草稿状态）"},
    {"code": "project_center.initiation.view", "module": "项目中心", "action": "initiation.view", "name": "项目立项-查看立项", "description": "查看项目立项列表和详情"},
    {"code": "project_center.initiation.submit", "module": "项目中心", "action": "initiation.submit", "name": "项目立项-提交审批", "description": "提交项目立项审批申请"},
    {"code": "project_center.initiation.approve_business", "module": "项目中心", "action": "initiation.approve_business", "name": "项目立项-商务部经理审批", "description": "商务部经理审批项目立项"},
    {"code": "project_center.initiation.approve_technical", "module": "项目中心", "action": "initiation.approve_technical", "name": "项目立项-技术部经理审批", "description": "技术部经理审批并接收项目立项"},
    {"code": "project_center.initiation.withdraw", "module": "项目中心", "action": "initiation.withdraw", "name": "项目立项-撤回审批", "description": "撤回已提交的项目立项审批"},
    {"code": "project_center.initiation.delete", "module": "项目中心", "action": "initiation.delete", "name": "项目立项-删除立项", "description": "删除草稿状态的项目立项"},
    {"code": "project_center.configure_team", "module": "项目中心", "action": "configure_team", "name": "项目中心-团队配置", "description": "配置项目团队成员及角色"},
    {"code": "project_center.monitor", "module": "项目中心", "action": "monitor", "name": "项目中心-项目监控", "description": "监控项目进度、风险、里程碑"},
    {"code": "project_center.archive", "module": "项目中心", "action": "archive", "name": "项目中心-项目归档", "description": "归档项目资料、导出报表"},
    {"code": "project_center.manage_finance", "module": "项目中心", "action": "manage_finance", "name": "项目中心-财务管理", "description": "管理项目合同、费用、回款计划"},
    {"code": "project_center.delete", "module": "项目中心", "action": "delete", "name": "项目中心-项目删除终止", "description": "删除或终止项目，需要审批"},
    {"code": "project_center.approve_stage", "module": "项目中心", "action": "approve_stage", "name": "项目中心-阶段审批", "description": "审批项目阶段流转"},
    {"code": "project_center.export", "module": "项目中心", "action": "export", "name": "项目中心-数据导出", "description": "导出项目数据并记录审计"},

    # 任务协作
    {"code": "task_collaboration.manage", "module": "任务协作", "action": "manage", "name": "任务协作-流程配置", "description": "配置任务流程、模板、审批节点"},
    {"code": "task_collaboration.assign", "module": "任务协作", "action": "assign", "name": "任务协作-任务分配", "description": "分配任务、调整进度、指派责任人"},
    {"code": "task_collaboration.execute", "module": "任务协作", "action": "execute", "name": "任务协作-任务执行", "description": "领取任务、提交成果、更新进度"},
    {"code": "task_collaboration.audit_timesheet", "module": "任务协作", "action": "audit_timesheet", "name": "任务协作-工时审核", "description": "审核工时填报与任务消耗"},
    {"code": "task_collaboration.view_all", "module": "任务协作", "action": "view_all", "name": "任务协作-查看全部", "description": "查看全局任务和协作动态"},
    {"code": "task_collaboration.comment", "module": "任务协作", "action": "comment", "name": "任务协作-留言沟通", "description": "在任务中留言、协作沟通"},

    # 生产质量
    {"code": "production_quality.submit_feedback", "module": "生产质量", "action": "submit_feedback", "name": "生产质量-意见填报", "description": "提交优化意见、质量问题、检查结果"},
    {"code": "production_quality.professional_review", "module": "生产质量", "action": "professional_review", "name": "生产质量-专业审核", "description": "对专业意见与成果进行审核"},
    {"code": "production_quality.project_review", "module": "生产质量", "action": "project_review", "name": "生产质量-项目审核", "description": "项目负责人对整体质量成果进行审核"},
    {"code": "production_quality.generate_report", "module": "生产质量", "action": "generate_report", "name": "生产质量-生成报告", "description": "生成质量报告、优化成果"},
    {"code": "production_quality.view_statistics", "module": "生产质量", "action": "view_statistics", "name": "生产质量-统计分析", "description": "查看质量统计、指标分析"},
    {"code": "production_quality.manage_standard", "module": "生产质量", "action": "manage_standard", "name": "生产质量-质量设置", "description": "维护质量标准、检查清单"},

    # 交付客户
    {"code": "delivery_center.view", "module": "交付客户", "action": "view", "name": "交付中心-访问", "description": "查看交付中心导航与相关功能入口"},
    {"code": "delivery_portal.view", "module": "交付客户", "action": "view", "name": "交付门户-查看", "description": "查看交付成果、客户协同记录"},
    {"code": "delivery_portal.submit", "module": "交付客户", "action": "submit", "name": "交付门户-成果提交", "description": "提交交付成果、上传报告"},
    {"code": "delivery_portal.approve", "module": "交付客户", "action": "approve", "name": "交付门户-成果审核", "description": "审核或确认交付成果"},
    {"code": "delivery_portal.configure", "module": "交付客户", "action": "configure", "name": "交付门户-配置管理", "description": "配置客户门户、访问权限"},
    {"code": "delivery_portal.sign", "module": "交付客户", "action": "sign", "name": "交付门户-电子签章", "description": "完成交付电子签章确认"},

    # 结算中心
    {"code": "settlement_center.initiate", "module": "结算中心", "action": "initiate", "name": "结算中心-发起结算", "description": "发起项目结算流程"},
    {"code": "settlement_center.manage_output", "module": "结算中心", "action": "manage_output", "name": "结算中心-产值管理", "description": "管理项目产值与成本"},
    {"code": "settlement_center.manage_finance", "module": "结算中心", "action": "manage_finance", "name": "结算中心-财务管理", "description": "处理财务台账、开票、收款"},
    {"code": "settlement_center.approve", "module": "结算中心", "action": "approve", "name": "结算中心-审批", "description": "审批结算、确认款项"},
    {"code": "settlement_center.view_analysis", "module": "结算中心", "action": "view_analysis", "name": "结算中心-统计分析", "description": "查看结算统计与分析报表"},
    {"code": "settlement_center.configure", "module": "结算中心", "action": "configure", "name": "结算中心-财务设置", "description": "维护财务参数、审批流程"},
    {"code": "settlement_center.view_sensitive", "module": "结算中心", "action": "view_sensitive", "name": "结算中心-敏感金额查看", "description": "查看敏感财务金额与利润"},
    # 结算管理细化权限
    {"code": "settlement_center.settlement.view", "module": "结算中心", "action": "settlement.view", "name": "结算管理-查看", "description": "查看项目结算和合同结算单"},
    {"code": "settlement_center.settlement.create", "module": "结算中心", "action": "settlement.create", "name": "结算管理-创建", "description": "创建项目结算和合同结算单"},
    {"code": "settlement_center.settlement.manage", "module": "结算中心", "action": "settlement.manage", "name": "结算管理-管理", "description": "管理结算单，编辑和删除"},
    {"code": "settlement_center.settlement.finance_review", "module": "结算中心", "action": "settlement.finance_review", "name": "结算管理-财务审核", "description": "财务审核结算单"},
    {"code": "settlement_center.settlement.manager_approve", "module": "结算中心", "action": "settlement.manager_approve", "name": "结算管理-部门经理审批", "description": "部门经理审批结算单"},
    {"code": "settlement_center.settlement.gm_approve", "module": "结算中心", "action": "settlement.gm_approve", "name": "结算管理-总经理审批", "description": "总经理审批结算单"},
    {"code": "settlement_center.settlement.confirm", "module": "结算中心", "action": "settlement.confirm", "name": "结算管理-确认结算", "description": "确认结算单，更新合同结算金额"},
    {"code": "settlement_center.settlement_statistics.view", "module": "结算中心", "action": "settlement_statistics.view", "name": "结算管理-统计查看", "description": "查看结算统计报表"},

    # 资源标准
    {"code": "resource_center.manage_library", "module": "资源标准", "action": "manage_library", "name": "资源中心-标准库维护", "description": "维护企业标准、模板、指标库"},
    {"code": "resource_center.manage_template", "module": "资源标准", "action": "manage_template", "name": "资源中心-模板管理", "description": "维护模板资源"},
    {"code": "resource_center.manage_professional", "module": "资源标准", "action": "manage_professional", "name": "资源中心-专业标准维护", "description": "维护各专业标准数据"},
    {"code": "resource_center.view", "module": "资源标准", "action": "view", "name": "资源中心-查看", "description": "查看知识库与参考资料"},
    {"code": "resource_center.contribute", "module": "资源标准", "action": "contribute", "name": "资源中心-知识贡献", "description": "提交知识库案例与资料"},
    {"code": "resource_center.data_maintenance", "module": "资源标准", "action": "data_maintenance", "name": "资源中心-数据维护", "description": "维护数据字典与基础数据"},

    # 客户成功
    {"code": "customer_success.manage", "module": "客户成功", "action": "manage", "name": "客户成功-客户管理", "description": "管理客户档案、商机跟踪"},
    {"code": "customer_success.view", "module": "客户成功", "action": "view", "name": "客户成功-查看", "description": "查看客户信息、跟踪记录"},
    {"code": "customer_success.analyze", "module": "客户成功", "action": "analyze", "name": "客户成功-价值分析", "description": "分析客户价值、满意度"},
    {"code": "customer_success.opportunity", "module": "客户成功", "action": "opportunity", "name": "客户成功-商机挖掘", "description": "商机识别与跟进"},

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
]
