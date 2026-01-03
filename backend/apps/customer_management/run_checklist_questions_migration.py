#!/usr/bin/env python
"""
直接执行SQL创建沟通清单问题管理相关的表
绕过Django迁移系统的依赖问题
"""
import os
import sys

# 添加项目根目录到Python路径
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, '../../../../'))
sys.path.insert(0, project_root)

import django

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.config.settings')
django.setup()

from django.db import connection
from django.utils import timezone

def execute_sql_file(sql_file_path):
    """执行SQL文件"""
    with open(sql_file_path, 'r', encoding='utf-8') as f:
        sql_content = f.read()
    
    # 移除注释和BEGIN/COMMIT
    sql_lines = []
    for line in sql_content.split('\n'):
        line = line.strip()
        # 跳过注释和空行
        if line and not line.startswith('--'):
            # 跳过BEGIN和COMMIT
            if line.upper() not in ['BEGIN', 'COMMIT']:
                sql_lines.append(line)
    
    # 按分号分割SQL语句
    sql_statements = []
    current_statement = []
    for line in sql_lines:
        current_statement.append(line)
        if line.endswith(';'):
            sql_statements.append(' '.join(current_statement))
            current_statement = []
    
    # 执行每个SQL语句
    cursor = connection.cursor()
    success_count = 0
    error_count = 0
    
    for sql in sql_statements:
        if sql.strip():
            try:
                cursor.execute(sql)
                success_count += 1
                print(f"✅ 执行成功: {sql[:60]}...")
            except Exception as e:
                error_msg = str(e).lower()
                # 如果是表已存在的错误，忽略
                if 'already exists' in error_msg or 'duplicate' in error_msg:
                    print(f"⚠️  已存在，跳过: {sql[:60]}...")
                    success_count += 1
                else:
                    error_count += 1
                    print(f"❌ 执行失败: {sql[:60]}...")
                    print(f"   错误: {e}")
    
    # 提交事务
    try:
        connection.commit()
        print(f"\n✅ SQL执行完成！成功: {success_count}, 失败: {error_count}")
        return error_count == 0
    except Exception as e:
        connection.rollback()
        print(f"\n❌ 提交失败: {e}")
        return False

def check_tables():
    """检查表是否创建成功"""
    cursor = connection.cursor()
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name IN ('communication_checklist_question', 'communication_checklist_answer')
        ORDER BY table_name
    """)
    tables = [row[0] for row in cursor.fetchall()]
    return tables

def mark_migrations_applied():
    """标记迁移为已应用"""
    cursor = connection.cursor()
    migrations = [
        ('customer_success', '0026_add_communication_checklist_questions'),
        ('customer_success', '0027_seed_communication_checklist_questions'),
    ]
    
    for app, migration_name in migrations:
        # 检查是否已存在
        cursor.execute("""
            SELECT COUNT(*) FROM django_migrations 
            WHERE app = %s AND name = %s
        """, [app, migration_name])
        
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
                INSERT INTO django_migrations (app, name, applied)
                VALUES (%s, %s, %s)
            """, [app, migration_name, timezone.now()])
            print(f"✓ 已标记迁移: {app}.{migration_name}")
        else:
            print(f"- 迁移已存在: {app}.{migration_name}")
    
    connection.commit()

def seed_questions():
    """初始化问题数据"""
    try:
        from backend.apps.customer_management.models import CommunicationChecklistQuestion
        
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
        
        count = 0
        for q_data in questions_data:
            obj, created = CommunicationChecklistQuestion.objects.get_or_create(
                question_code=q_data['question_code'],
                defaults={
                    'part': q_data['part'],
                    'order': q_data['order'],
                    'question_text': q_data['question_text'],
                    'is_active': True,
                }
            )
            if created:
                count += 1
        
        print(f"✓ 已初始化 {count} 个问题")
        return count
        
    except Exception as e:
        print(f"✗ 初始化问题失败: {e}")
        import traceback
        traceback.print_exc()
        return 0

if __name__ == '__main__':
    # 获取SQL文件路径
    script_dir = os.path.dirname(os.path.abspath(__file__))
    sql_file = os.path.join(script_dir, 'migrations', 'create_checklist_questions_tables.sql')
    
    if not os.path.exists(sql_file):
        print(f"❌ SQL文件不存在: {sql_file}")
        sys.exit(1)
    
    print("🚀 开始创建沟通清单问题管理相关的数据库表...")
    print(f"📄 SQL文件: {sql_file}\n")
    
    # 检查现有表
    existing_tables = check_tables()
    if existing_tables:
        print(f"⚠️  发现已存在的表: {', '.join(existing_tables)}")
        response = input("是否继续？(y/n): ")
        if response.lower() != 'y':
            print("已取消")
            sys.exit(0)
    
    # 执行SQL
    success = execute_sql_file(sql_file)
    
    # 检查结果
    print("\n📊 检查创建的表...")
    tables = check_tables()
    expected_tables = ['communication_checklist_question', 'communication_checklist_answer']
    
    if tables:
        print(f"✅ 已创建的表: {', '.join(tables)}")
        for table in expected_tables:
            if table in tables:
                print(f"  ✓ {table}")
            else:
                print(f"  ✗ {table} (缺失)")
    else:
        print("❌ 未找到任何表")
    
    if success and len(tables) >= len(expected_tables):
        print("\n📝 标记迁移为已应用...")
        mark_migrations_applied()
        
        print("\n🌱 初始化问题数据...")
        questions_count = seed_questions()
        
        if questions_count >= 25:
            print(f"\n🎉 迁移成功完成！已创建表并初始化 {questions_count} 个问题")
            sys.exit(0)
        else:
            print(f"\n⚠️  迁移完成，但问题数量不足（期望25个，实际{questions_count}个）")
            sys.exit(0)
    else:
        print("\n⚠️  迁移可能未完全成功，请检查错误信息")
        sys.exit(1)

