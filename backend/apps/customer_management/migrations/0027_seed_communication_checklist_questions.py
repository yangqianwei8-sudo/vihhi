# Generated manually to seed communication checklist questions

from django.db import migrations


def seed_questions(apps, schema_editor):
    """初始化沟通清单问题数据"""
    CommunicationChecklistQuestion = apps.get_model('customer_management', 'CommunicationChecklistQuestion')
    
    questions_data = [
        # 第一部分：客户与项目背景信息
        {'part': 'part1', 'order': 1, 'question_code': 'part1_q1_client_info', 'question_text': '是否明确客户全称及企业类型（如国企、上市房企等）？'},
        {'part': 'part1', 'order': 2, 'question_code': 'part1_q2_business_model', 'question_text': '是否了解客户的核心商业模式或近期战略重点（如高周转、精品等）？'},
        {'part': 'part1', 'order': 3, 'question_code': 'part1_q3_design_stage', 'question_text': '是否清楚项目当前具体的设计阶段（如方案、施工图等）？'},
        {'part': 'part1', 'order': 4, 'question_code': 'part1_q4_key_nodes', 'question_text': '是否知晓项目是否存在关键节点压力（如报批、开工日期）？'},
        {'part': 'part1', 'order': 5, 'question_code': 'part1_q5_design_unit', 'question_text': '是否了解原设计单位及其技术特点？'},
        {'part': 'part1', 'order': 6, 'question_code': 'part1_q6_pain_points', 'question_text': '是否已推测客户可能存在的至少两个核心成本/技术痛点？'},
        {'part': 'part1', 'order': 7, 'question_code': 'part1_q7_decision_makers', 'question_text': '是否已初步识别客户内部的决策者、发起者及关键影响者？'},
        
        # 第二部分：沟通目标与内容准备
        {'part': 'part2', 'order': 1, 'question_code': 'part2_q1_core_goal', 'question_text': '是否设定了本次沟通必须达成的唯一核心目标？'},
        {'part': 'part2', 'order': 2, 'question_code': 'part2_q2_secondary_goals', 'question_text': '是否准备了2-3个次要目标？'},
        {'part': 'part2', 'order': 3, 'question_code': 'part2_q3_success_cases', 'question_text': '是否准备了针对客户痛点的相关成功案例？'},
        {'part': 'part2', 'order': 4, 'question_code': 'part2_q4_unique_value', 'question_text': '是否能用一句话清晰阐述我司在此项目上的独特价值？'},
        {'part': 'part2', 'order': 5, 'question_code': 'part2_q5_company_intro', 'question_text': '是否有清晰的5分钟公司业务介绍提纲？'},
        {'part': 'part2', 'order': 6, 'question_code': 'part2_q6_visual_tools', 'question_text': '是否准备了辅助说明的"设计-成本"可视化工具或数据？'},
        {'part': 'part2', 'order': 7, 'question_code': 'part2_q7_technical_specs', 'question_text': '是否复习了该项目业态的关键技术规范与经济指标？'},
        
        # 第三部分：沟通策略与风险预案
        {'part': 'part3', 'order': 1, 'question_code': 'part3_q1_opening', 'question_text': '是否设计好了专业开场白？'},
        {'part': 'part3', 'order': 2, 'question_code': 'part3_q2_ice_breaking', 'question_text': '是否了解参会人员背景并准备了破冰方式？'},
        {'part': 'part3', 'order': 3, 'question_code': 'part3_q3_core_questions', 'question_text': '是否列出了至少5个必须提问的核心问题？'},
        {'part': 'part3', 'order': 4, 'question_code': 'part3_q4_follow_up', 'question_text': '是否准备了追问话术以挖掘深层动机？'},
        {'part': 'part3', 'order': 5, 'question_code': 'part3_q5_concerns', 'question_text': '是否预判了客户可能的两个主要顾虑并准备了应对答案？'},
        {'part': 'part3', 'order': 6, 'question_code': 'part3_q6_backup_plan', 'question_text': '是否准备了关键信息无法获取时的备选方案？'},
        {'part': 'part3', 'order': 7, 'question_code': 'part3_q7_action_items', 'question_text': '是否明确了沟通后希望双方执行的立即行动项？'},
        
        # 第四部分：后勤与状态
        {'part': 'part4', 'order': 1, 'question_code': 'part4_q1_logistics', 'question_text': '会议时间、地点、链接等后勤细节是否万无一失？'},
        {'part': 'part4', 'order': 2, 'question_code': 'part4_q2_materials', 'question_text': '设备、资料、名片等物料是否齐备？'},
        {'part': 'part4', 'order': 3, 'question_code': 'part4_q3_role_division', 'question_text': '内部角色分工是否明确？'},
        {'part': 'part4', 'order': 4, 'question_code': 'part4_q4_mindset', 'question_text': '个人心态是否已调整为"协作解决问题"的合作伙伴状态？'},
    ]
    
    for q_data in questions_data:
        CommunicationChecklistQuestion.objects.get_or_create(
            question_code=q_data['question_code'],
            defaults={
                'part': q_data['part'],
                'order': q_data['order'],
                'question_text': q_data['question_text'],
                'is_active': True,
            }
        )


def reverse_seed_questions(apps, schema_editor):
    """回滚：删除所有问题"""
    CommunicationChecklistQuestion = apps.get_model('customer_management', 'CommunicationChecklistQuestion')
    CommunicationChecklistQuestion.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('customer_management', '0026_add_communication_checklist_questions'),
    ]

    operations = [
        migrations.RunPython(seed_questions, reverse_seed_questions),
    ]

