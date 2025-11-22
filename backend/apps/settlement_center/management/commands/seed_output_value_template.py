"""
初始化产值计算模板数据
根据用户提供的产值计算表创建阶段、里程碑和事件配置
"""
from django.core.management.base import BaseCommand
from backend.apps.settlement_center.models import OutputValueStage, OutputValueMilestone, OutputValueEvent


# 产值模板数据结构
# 格式: (阶段名称, 阶段编码, 阶段比例, 基数类型, 里程碑列表)
OUTPUT_VALUE_TEMPLATE = [
    {
        'stage_name': '转化阶段',
        'stage_code': 'conversion',
        'stage_percentage': 0.20,
        'base_amount_type': 'registration_amount',
        'milestones': [
            {
                'name': '商机成就',
                'code': 'opportunity_achievement',
                'percentage': 10.00,
                'events': [
                    {'name': '首次拜访', 'code': 'first_visit', 'percentage': 20.00, 'role': 'business_manager'},
                    {'name': '需求沟通', 'code': 'requirement_communication', 'percentage': 30.00, 'role': 'business_manager'},
                    {'name': '商机备案', 'code': 'opportunity_registration', 'percentage': 50.00, 'role': 'business_manager'},
                ]
            },
            {
                'name': '技术支持',
                'code': 'technical_support',
                'percentage': 10.00,
                'events': [
                    {'name': '获取图纸', 'code': 'obtain_drawings', 'percentage': 20.00, 'role': 'business_manager'},
                    {'name': '图纸评估', 'code': 'drawing_evaluation', 'percentage': 30.00, 'role': 'professional_engineer'},
                    {'name': '技术交流会', 'code': 'technical_meeting', 'percentage': 50.00, 'role': 'technical_manager'},
                ]
            },
            {
                'name': '客户关系升级',
                'code': 'customer_relationship_upgrade',
                'percentage': 50.00,
                'events': [
                    {'name': '获对接人支持', 'code': 'get_contact_support', 'percentage': 20.00, 'role': 'business_manager'},
                    {'name': '获推动人支持', 'code': 'get_promoter_support', 'percentage': 30.00, 'role': 'business_manager'},
                    {'name': '获决策人支持', 'code': 'get_decision_maker_support', 'percentage': 50.00, 'role': 'business_manager'},
                ]
            },
            {
                'name': '意向成就',
                'code': 'intention_achievement',
                'percentage': 30.00,
                'base_amount_type': 'intention_amount',  # 覆盖阶段基数类型
                'events': [
                    {'name': '投标或报价或商务洽谈', 'code': 'bid_quote_negotiation', 'percentage': 20.00, 'role': 'cost_manager'},
                    {'name': '合作意向', 'code': 'cooperation_intention', 'percentage': 30.00, 'role': 'business_manager'},
                    {'name': '赢单或输单', 'code': 'win_or_lose', 'percentage': 50.00, 'role': 'business_manager'},
                ]
            },
        ]
    },
    {
        'stage_name': '合同阶段',
        'stage_code': 'contract',
        'stage_percentage': 1.00,
        'base_amount_type': 'contract_amount',
        'milestones': [
            {
                'name': '合同定稿',
                'code': 'contract_finalization',
                'percentage': 50.00,
                'events': [
                    {'name': '发送合同', 'code': 'send_contract', 'percentage': 20.00, 'role': 'business_manager'},
                    {'name': '获取回复', 'code': 'get_reply', 'percentage': 30.00, 'role': 'business_manager'},
                    {'name': '争议解决', 'code': 'dispute_resolution', 'percentage': 50.00, 'role': 'business_manager'},
                ]
            },
            {
                'name': '合同生效',
                'code': 'contract_effectiveness',
                'percentage': 50.00,
                'events': [
                    {'name': '合同盖章', 'code': 'contract_seal', 'percentage': 99.00, 'role': 'business_manager'},
                    {'name': '合同归档', 'code': 'contract_archiving', 'percentage': 1.00, 'role': 'admin_office'},
                ]
            },
        ]
    },
    {
        'stage_name': '生产阶段',
        'stage_code': 'production',
        'stage_percentage': 8.00,
        'base_amount_type': 'contract_amount',
        'milestones': [
            {
                'name': '准备工作',
                'code': 'preparation',
                'percentage': 2.00,
                'events': [
                    {'name': '创建新项目', 'code': 'create_project', 'percentage': 10.00, 'role': 'business_manager'},
                    {'name': '配置项目团队', 'code': 'configure_team', 'percentage': 90.00, 'role': 'project_manager'},
                ]
            },
            {
                'name': '优化前资料',
                'code': 'pre_optimization_materials',
                'percentage': 5.00,
                'events': [
                    {'name': '优化前资料申请', 'code': 'apply_pre_materials', 'percentage': 10.00, 'role': 'project_manager'},
                    {'name': '优化前资料复核', 'code': 'review_pre_materials', 'percentage': 20.00, 'role': 'professional_engineer'},
                    {'name': '优化前资料刻盘', 'code': 'burn_pre_materials', 'percentage': 5.00, 'role': 'admin_office'},
                ]
            },
            {
                'name': '咨询意见提交',
                'code': 'consultation_opinion_submission',
                'percentage': 30.00,
                'events': [
                    {'name': '获取开工通知', 'code': 'get_start_notice', 'percentage': 2.00, 'role': 'project_manager'},
                    {'name': '编制专业咨询意见书', 'code': 'prepare_opinion_book', 'percentage': 86.00, 'role': 'professional_engineer'},
                    {'name': '专业校核', 'code': 'professional_review', 'percentage': 4.00, 'role': 'professional_lead'},
                    {'name': '审批', 'code': 'approve', 'percentage': 2.00, 'role': 'project_manager'},
                    {'name': '全专业咨询意见书签字', 'code': 'sign_opinion_book', 'percentage': 5.00, 'role': 'business_manager'},
                    {'name': '全专业咨询意见书归档', 'code': 'archive_opinion_book', 'percentage': 1.00, 'role': 'admin_office'},
                ]
            },
            {
                'name': '沟通完成',
                'code': 'communication_completion',
                'percentage': 15.00,
                'events': [
                    {'name': '获取设计单位回复', 'code': 'get_design_reply', 'percentage': 24.00, 'role': 'project_manager'},
                    {'name': '三方会议纪要', 'code': 'three_party_meeting', 'percentage': 14.00, 'role': 'professional_engineer'},
                    {'name': '编制三方沟通成果', 'code': 'prepare_communication_result', 'percentage': 50.00, 'role': 'professional_engineer'},
                    {'name': '专业校核', 'code': 'professional_review_communication', 'percentage': 4.00, 'role': 'professional_lead'},
                    {'name': '审批', 'code': 'approve_communication', 'percentage': 2.00, 'role': 'project_manager'},
                    {'name': '三方沟通成果签署', 'code': 'sign_communication_result', 'percentage': 5.00, 'role': 'business_manager'},
                    {'name': '三方沟通成果归档', 'code': 'archive_communication_result', 'percentage': 1.00, 'role': 'admin_office'},
                ]
            },
            {
                'name': '落地咨询意见',
                'code': 'implement_opinion',
                'percentage': 10.00,
                'events': [
                    {'name': '优化前资料签署', 'code': 'sign_pre_materials', 'percentage': 64.00, 'role': 'business_manager'},
                    {'name': '设计院坐班跟踪改图', 'code': 'track_design_changes', 'percentage': 74.00, 'role': 'professional_engineer'},
                    {'name': '编制意见落实报告', 'code': 'prepare_implementation_report', 'percentage': 20.00, 'role': 'professional_engineer'},
                    {'name': '意见落实报告签署', 'code': 'sign_implementation_report', 'percentage': 5.00, 'role': 'business_manager'},
                    {'name': '意见落实报告归档', 'code': 'archive_implementation_report', 'percentage': 1.00, 'role': 'admin_office'},
                ]
            },
            {
                'name': '最终成果交付',
                'code': 'final_delivery',
                'percentage': 30.00,
                'events': [
                    {'name': '优化前资料归档', 'code': 'archive_pre_materials', 'percentage': 1.00, 'role': 'admin_office'},
                    {'name': '获取修改后图纸', 'code': 'get_modified_drawings', 'percentage': 20.00, 'role': 'project_manager'},
                    {'name': '编制专业核图意见书', 'code': 'prepare_review_opinion', 'percentage': 68.00, 'role': 'professional_engineer'},
                    {'name': '专业校核', 'code': 'professional_review_final', 'percentage': 4.00, 'role': 'professional_lead'},
                    {'name': '审批', 'code': 'approve_final', 'percentage': 2.00, 'role': 'project_manager'},
                    {'name': '核图意见书签署', 'code': 'sign_review_opinion', 'percentage': 5.00, 'role': 'business_manager'},
                    {'name': '核图意见书归档', 'code': 'archive_review_opinion', 'percentage': 1.00, 'role': 'admin_office'},
                ]
            },
            {
                'name': '项目完工确认',
                'code': 'project_completion',
                'percentage': 8.00,
                'events': [
                    {'name': '优化后资料确认', 'code': 'confirm_post_materials', 'percentage': 30.00, 'role': 'professional_engineer'},
                    {'name': '专业校核', 'code': 'professional_review_completion', 'percentage': 4.00, 'role': 'professional_lead'},
                    {'name': '审批', 'code': 'approve_completion', 'percentage': 2.00, 'role': 'project_manager'},
                    {'name': '优化后资料刻盘', 'code': 'burn_post_materials', 'percentage': 2.00, 'role': 'admin_office'},
                    {'name': '优化后资料归档', 'code': 'archive_post_materials', 'percentage': 1.00, 'role': 'admin_office'},
                    {'name': '优化后刻盘签署', 'code': 'sign_burned_materials', 'percentage': 20.00, 'role': 'business_manager'},
                    {'name': '完工确认函签署', 'code': 'sign_completion_letter', 'percentage': 40.00, 'role': 'business_manager'},
                    {'name': '完工确认函归档', 'code': 'archive_completion_letter', 'percentage': 1.00, 'role': 'admin_office'},
                ]
            },
        ]
    },
    {
        'stage_name': '结算阶段',
        'stage_code': 'settlement',
        'stage_percentage': 5.00,
        'base_amount_type': 'contract_amount',
        'milestones': [
            {
                'name': '结算申请书',
                'code': 'settlement_application',
                'percentage': 30.00,
                'events': [
                    {'name': '整理结算资料', 'code': 'organize_settlement_data', 'percentage': 2.00, 'role': 'admin_office'},
                    {'name': '结算资料复核', 'code': 'review_settlement_data', 'percentage': 3.00, 'role': 'technical_manager'},
                    {'name': '算量计价', 'code': 'calculate_quantity_price', 'percentage': 80.00, 'role': 'cost_engineer'},
                    {'name': '专业审核', 'code': 'professional_audit', 'percentage': 5.00, 'role': 'cost_team'},
                    {'name': '编制结算申请书', 'code': 'prepare_settlement_application', 'percentage': 5.00, 'role': 'cost_manager'},
                    {'name': '结算申请书报送', 'code': 'submit_settlement_application', 'percentage': 2.00, 'role': 'business_manager'},
                    {'name': '结算申请书签署', 'code': 'sign_settlement_application', 'percentage': 3.00, 'role': 'business_manager'},
                ]
            },
            {
                'name': '结算初审',
                'code': 'settlement_preliminary',
                'percentage': 10.00,
                'events': [
                    {'name': '获取初审意见', 'code': 'get_preliminary_opinion', 'percentage': 18.00, 'role': 'business_manager'},
                    {'name': '编制回复意见', 'code': 'prepare_reply_opinion', 'percentage': 80.00, 'role': 'cost_engineer'},
                    {'name': '初审回复意见报送', 'code': 'submit_reply_opinion', 'percentage': 2.00, 'role': 'admin_office'},
                ]
            },
            {
                'name': '结算对账',
                'code': 'settlement_reconciliation',
                'percentage': 30.00,
                'events': [
                    {'name': '预约对量', 'code': 'schedule_reconciliation', 'percentage': 20.00, 'role': 'business_manager'},
                    {'name': '消除争议', 'code': 'resolve_disputes', 'percentage': 80.00, 'role': 'cost_engineer'},
                ]
            },
            {
                'name': '结算定案',
                'code': 'settlement_finalization',
                'percentage': 30.00,
                'base_amount_type': 'settlement_amount',  # 覆盖阶段基数类型
                'events': [
                    {'name': '形成结算报告', 'code': 'form_settlement_report', 'percentage': 5.00, 'role': 'cost_manager'},
                    {'name': '结算报告签署', 'code': 'sign_settlement_report', 'percentage': 93.00, 'role': 'cost_engineer'},
                    {'name': '结算报告归档', 'code': 'archive_settlement_report', 'percentage': 2.00, 'role': 'admin_office'},
                ]
            },
        ]
    },
    {
        'stage_name': '回款阶段',
        'stage_code': 'payment',
        'stage_percentage': 5.00,
        'base_amount_type': 'payment_amount',
        'milestones': [
            {
                'name': '回款达30%',
                'code': 'payment_30_percent',
                'percentage': 30.00,
                'events': [
                    {'name': '付款申请书编制', 'code': 'prepare_payment_application', 'percentage': 10.00, 'role': 'business_manager'},
                    {'name': '付款申请书报送', 'code': 'submit_payment_application', 'percentage': 1.00, 'role': 'admin_office'},
                    {'name': '发票开具', 'code': 'issue_invoice', 'percentage': 1.00, 'role': 'finance_supervisor'},
                    {'name': '回款到账', 'code': 'payment_received', 'percentage': 88.00, 'role': 'business_manager'},
                ]
            },
            {
                'name': '回款达70%',
                'code': 'payment_70_percent',
                'percentage': 40.00,
                'events': [
                    {'name': '付款申请书编制', 'code': 'prepare_payment_application_70', 'percentage': 10.00, 'role': 'business_manager'},
                    {'name': '付款申请书报送', 'code': 'submit_payment_application_70', 'percentage': 1.00, 'role': 'admin_office'},
                    {'name': '发票开具', 'code': 'issue_invoice_70', 'percentage': 1.00, 'role': 'finance_supervisor'},
                    {'name': '回款到账', 'code': 'payment_received_70', 'percentage': 88.00, 'role': 'business_manager'},
                ]
            },
            {
                'name': '回款达100%',
                'code': 'payment_100_percent',
                'percentage': 30.00,
                'events': [
                    {'name': '付款申请书编制', 'code': 'prepare_payment_application_100', 'percentage': 10.00, 'role': 'business_manager'},
                    {'name': '付款申请书报送', 'code': 'submit_payment_application_100', 'percentage': 1.00, 'role': 'admin_office'},
                    {'name': '发票开具', 'code': 'issue_invoice_100', 'percentage': 1.00, 'role': 'finance_supervisor'},
                    {'name': '回款到账', 'code': 'payment_received_100', 'percentage': 88.00, 'role': 'business_manager'},
                ]
            },
        ]
    },
    {
        'stage_name': '售后阶段',
        'stage_code': 'after_sales',
        'stage_percentage': 1.00,
        'base_amount_type': 'payment_amount',
        'milestones': [
            {
                'name': '成果验证',
                'code': 'result_verification',
                'percentage': 10.00,
                'events': [
                    {'name': '最终汇报', 'code': 'final_report', 'percentage': 50.00, 'role': 'project_manager'},
                    {'name': '项目应用情况回访', 'code': 'application_follow_up', 'percentage': 50.00, 'role': 'project_manager'},
                ]
            },
            {
                'name': '客户关系维护',
                'code': 'customer_relationship_maintenance',
                'percentage': 40.00,
                'events': [
                    {'name': '客户满意度调研', 'code': 'satisfaction_survey', 'percentage': 40.00, 'role': 'project_manager'},
                    {'name': '客户重大事件关怀', 'code': 'major_event_care', 'percentage': 30.00, 'role': 'project_manager'},
                    {'name': '竣工复盘会议', 'code': 'completion_review_meeting', 'percentage': 30.00, 'role': 'project_manager'},
                ]
            },
            {
                'name': '问题响应与解决',
                'code': 'issue_response_resolution',
                'percentage': 30.00,
                'events': [
                    {'name': '问题接收与工单创建', 'code': 'issue_received_created', 'percentage': 30.00, 'role': 'project_manager'},
                    {'name': '问题分析与解决方案', 'code': 'issue_analysis_solution', 'percentage': 30.00, 'role': 'project_manager'},
                    {'name': '问题关闭与回访', 'code': 'issue_closed_follow_up', 'percentage': 40.00, 'role': 'project_manager'},
                ]
            },
            {
                'name': '续约与增购引导',
                'code': 'renewal_upsell_guidance',
                'percentage': 20.00,
                'events': [
                    {'name': '客户新需求挖掘', 'code': 'new_requirement_mining', 'percentage': 50.00, 'role': 'project_manager'},
                    {'name': '续约/增购意向确认', 'code': 'renewal_upsell_intention', 'percentage': 40.00, 'role': 'project_manager'},
                    {'name': '成功续约/增购', 'code': 'successful_renewal_upsell', 'percentage': 10.00, 'role': 'project_manager'},
                ]
            },
        ]
    },
]


class Command(BaseCommand):
    help = '初始化产值计算模板数据（阶段、里程碑、事件）'

    def handle(self, *args, **options):
        stages_created = 0
        stages_updated = 0
        milestones_created = 0
        milestones_updated = 0
        events_created = 0
        events_updated = 0

        for stage_order, stage_data in enumerate(OUTPUT_VALUE_TEMPLATE, start=1):
            # 创建或更新阶段
            stage, created = OutputValueStage.objects.update_or_create(
                code=stage_data['stage_code'],
                defaults={
                    'name': stage_data['stage_name'],
                    'stage_type': stage_data['stage_code'],
                    'stage_percentage': stage_data['stage_percentage'],
                    'base_amount_type': stage_data['base_amount_type'],
                    'order': stage_order,
                    'is_active': True,
                }
            )
            if created:
                stages_created += 1
            else:
                stages_updated += 1

            # 创建或更新里程碑
            for milestone_order, milestone_data in enumerate(stage_data['milestones'], start=1):
                milestone, created = OutputValueMilestone.objects.update_or_create(
                    stage=stage,
                    code=milestone_data['code'],
                    defaults={
                        'name': milestone_data['name'],
                        'milestone_percentage': milestone_data['percentage'],
                        'order': milestone_order,
                        'is_active': True,
                    }
                )
                if created:
                    milestones_created += 1
                else:
                    milestones_updated += 1

                # 创建或更新事件
                for event_order, event_data in enumerate(milestone_data['events'], start=1):
                    # 确定基数类型（里程碑覆盖阶段，否则使用阶段默认）
                    base_amount_type = milestone_data.get('base_amount_type', stage_data['base_amount_type'])
                    
                    event, created = OutputValueEvent.objects.update_or_create(
                        milestone=milestone,
                        code=event_data['code'],
                        defaults={
                            'name': event_data['name'],
                            'event_percentage': event_data['percentage'],
                            'responsible_role_code': event_data['role'],
                            'order': event_order,
                            'is_active': True,
                        }
                    )
                    if created:
                        events_created += 1
                    else:
                        events_updated += 1

        self.stdout.write(self.style.SUCCESS(
            f'产值模板初始化完成：\n'
            f'  阶段：新增 {stages_created} 个，更新 {stages_updated} 个\n'
            f'  里程碑：新增 {milestones_created} 个，更新 {milestones_updated} 个\n'
            f'  事件：新增 {events_created} 个，更新 {events_updated} 个'
        ))
