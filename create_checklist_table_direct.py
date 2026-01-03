#!/usr/bin/env python
"""直接创建客户沟通准备清单表的脚本（绕过迁移依赖问题）"""
import os
import sys
import django

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.config.settings')
django.setup()

from django.db import connection

def create_table_directly():
    """直接使用SQL创建表"""
    cursor = connection.cursor()
    db_backend = connection.vendor
    
    print(f"检测到数据库类型: {db_backend}")
    
    # 检查表是否已存在
    if db_backend == 'postgresql':
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'customer_communication_checklist'
            )
        """)
        table_exists = cursor.fetchone()[0]
    elif db_backend == 'sqlite':
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='customer_communication_checklist'
        """)
        table_exists = cursor.fetchone() is not None
    else:  # MySQL
        cursor.execute("""
            SELECT COUNT(*) FROM information_schema.tables 
            WHERE table_schema = DATABASE() AND table_name = 'customer_communication_checklist'
        """)
        table_exists = cursor.fetchone()[0] > 0
    
    if table_exists:
        print("✓ 表已存在，跳过创建")
        return True
    
    print("正在创建表...")
    
    # 根据数据库类型生成不同的SQL
    if db_backend == 'postgresql':
        sql = """
        CREATE TABLE customer_communication_checklist (
            id BIGSERIAL PRIMARY KEY,
            checklist_number VARCHAR(50) UNIQUE,
            title VARCHAR(200) NOT NULL,
            communication_date TIMESTAMP NOT NULL,
            location VARCHAR(200),
            status VARCHAR(20) NOT NULL DEFAULT 'before',
            part1_q1_client_info VARCHAR(20) NOT NULL DEFAULT 'unknown',
            part1_q1_note_before TEXT,
            part1_q1_note_after TEXT,
            part1_q2_business_model VARCHAR(20) NOT NULL DEFAULT 'unknown',
            part1_q2_note_before TEXT,
            part1_q2_note_after TEXT,
            part1_q3_design_stage VARCHAR(20) NOT NULL DEFAULT 'unknown',
            part1_q3_note_before TEXT,
            part1_q3_note_after TEXT,
            part1_q4_key_nodes VARCHAR(20) NOT NULL DEFAULT 'unknown',
            part1_q4_note_before TEXT,
            part1_q4_note_after TEXT,
            part1_q5_design_unit VARCHAR(20) NOT NULL DEFAULT 'unknown',
            part1_q5_note_before TEXT,
            part1_q5_note_after TEXT,
            part1_q6_pain_points VARCHAR(20) NOT NULL DEFAULT 'unknown',
            part1_q6_note_before TEXT,
            part1_q6_note_after TEXT,
            part1_q7_decision_makers VARCHAR(20) NOT NULL DEFAULT 'unknown',
            part1_q7_note_before TEXT,
            part1_q7_note_after TEXT,
            part2_q1_core_goal VARCHAR(20) NOT NULL DEFAULT 'unknown',
            part2_q1_note_before TEXT,
            part2_q1_note_after TEXT,
            part2_q2_secondary_goals VARCHAR(20) NOT NULL DEFAULT 'unknown',
            part2_q2_note_before TEXT,
            part2_q2_note_after TEXT,
            part2_q3_success_cases VARCHAR(20) NOT NULL DEFAULT 'unknown',
            part2_q3_note_before TEXT,
            part2_q3_note_after TEXT,
            part2_q4_unique_value VARCHAR(20) NOT NULL DEFAULT 'unknown',
            part2_q4_note_before TEXT,
            part2_q4_note_after TEXT,
            part2_q5_company_intro VARCHAR(20) NOT NULL DEFAULT 'unknown',
            part2_q5_note_before TEXT,
            part2_q5_note_after TEXT,
            part2_q6_visual_tools VARCHAR(20) NOT NULL DEFAULT 'unknown',
            part2_q6_note_before TEXT,
            part2_q6_note_after TEXT,
            part2_q7_technical_specs VARCHAR(20) NOT NULL DEFAULT 'unknown',
            part2_q7_note_before TEXT,
            part2_q7_note_after TEXT,
            part3_q1_opening VARCHAR(20) NOT NULL DEFAULT 'unknown',
            part3_q1_note_before TEXT,
            part3_q1_note_after TEXT,
            part3_q2_ice_breaking VARCHAR(20) NOT NULL DEFAULT 'unknown',
            part3_q2_note_before TEXT,
            part3_q2_note_after TEXT,
            part3_q3_core_questions VARCHAR(20) NOT NULL DEFAULT 'unknown',
            part3_q3_note_before TEXT,
            part3_q3_note_after TEXT,
            part3_q4_follow_up VARCHAR(20) NOT NULL DEFAULT 'unknown',
            part3_q4_note_before TEXT,
            part3_q4_note_after TEXT,
            part3_q5_concerns VARCHAR(20) NOT NULL DEFAULT 'unknown',
            part3_q5_note_before TEXT,
            part3_q5_note_after TEXT,
            part3_q6_backup_plan VARCHAR(20) NOT NULL DEFAULT 'unknown',
            part3_q6_note_before TEXT,
            part3_q6_note_after TEXT,
            part3_q7_action_items VARCHAR(20) NOT NULL DEFAULT 'unknown',
            part3_q7_note_before TEXT,
            part3_q7_note_after TEXT,
            part4_q1_logistics VARCHAR(20) NOT NULL DEFAULT 'unknown',
            part4_q1_note_before TEXT,
            part4_q1_note_after TEXT,
            part4_q2_materials VARCHAR(20) NOT NULL DEFAULT 'unknown',
            part4_q2_note_before TEXT,
            part4_q2_note_after TEXT,
            part4_q3_role_division VARCHAR(20) NOT NULL DEFAULT 'unknown',
            part4_q3_note_before TEXT,
            part4_q3_note_after TEXT,
            part4_q4_mindset VARCHAR(20) NOT NULL DEFAULT 'unknown',
            part4_q4_note_before TEXT,
            part4_q4_note_after TEXT,
            part5_key_info_updates TEXT,
            part5_priority_requirement TEXT,
            part5_goal_assessment TEXT,
            part5_next_action_ours TEXT,
            part5_next_action_client TEXT,
            part5_followup_schedule TEXT,
            part5_challenges TEXT,
            part5_improvement_suggestions TEXT,
            created_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            client_id BIGINT NOT NULL,
            created_by_id BIGINT NOT NULL,
            opportunity_id BIGINT
        );
        
        CREATE INDEX customer_co_client__d4fab3_idx ON customer_communication_checklist(client_id, communication_date DESC);
        CREATE INDEX customer_co_opportu_1e8e11_idx ON customer_communication_checklist(opportunity_id, communication_date DESC);
        CREATE INDEX customer_co_status_b59455_idx ON customer_communication_checklist(status, communication_date DESC);
        CREATE INDEX customer_co_checkli_dd54e8_idx ON customer_communication_checklist(checklist_number);
        
        ALTER TABLE customer_communication_checklist 
            ADD CONSTRAINT customer_commu_client_id_fk 
            FOREIGN KEY (client_id) REFERENCES customer_client(id) ON DELETE RESTRICT;
        
        ALTER TABLE customer_communication_checklist 
            ADD CONSTRAINT customer_commu_created_by_id_fk 
            FOREIGN KEY (created_by_id) REFERENCES system_user(id) ON DELETE RESTRICT;
        
        ALTER TABLE customer_communication_checklist 
            ADD CONSTRAINT customer_commu_opportunity_id_fk 
            FOREIGN KEY (opportunity_id) REFERENCES business_opportunity(id) ON DELETE SET NULL;
        """
    elif db_backend == 'sqlite':
        sql = """
        CREATE TABLE customer_communication_checklist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            checklist_number VARCHAR(50) UNIQUE,
            title VARCHAR(200) NOT NULL,
            communication_date DATETIME NOT NULL,
            location VARCHAR(200),
            status VARCHAR(20) NOT NULL DEFAULT 'before',
            part1_q1_client_info VARCHAR(20) NOT NULL DEFAULT 'unknown',
            part1_q1_note_before TEXT,
            part1_q1_note_after TEXT,
            part1_q2_business_model VARCHAR(20) NOT NULL DEFAULT 'unknown',
            part1_q2_note_before TEXT,
            part1_q2_note_after TEXT,
            part1_q3_design_stage VARCHAR(20) NOT NULL DEFAULT 'unknown',
            part1_q3_note_before TEXT,
            part1_q3_note_after TEXT,
            part1_q4_key_nodes VARCHAR(20) NOT NULL DEFAULT 'unknown',
            part1_q4_note_before TEXT,
            part1_q4_note_after TEXT,
            part1_q5_design_unit VARCHAR(20) NOT NULL DEFAULT 'unknown',
            part1_q5_note_before TEXT,
            part1_q5_note_after TEXT,
            part1_q6_pain_points VARCHAR(20) NOT NULL DEFAULT 'unknown',
            part1_q6_note_before TEXT,
            part1_q6_note_after TEXT,
            part1_q7_decision_makers VARCHAR(20) NOT NULL DEFAULT 'unknown',
            part1_q7_note_before TEXT,
            part1_q7_note_after TEXT,
            part2_q1_core_goal VARCHAR(20) NOT NULL DEFAULT 'unknown',
            part2_q1_note_before TEXT,
            part2_q1_note_after TEXT,
            part2_q2_secondary_goals VARCHAR(20) NOT NULL DEFAULT 'unknown',
            part2_q2_note_before TEXT,
            part2_q2_note_after TEXT,
            part2_q3_success_cases VARCHAR(20) NOT NULL DEFAULT 'unknown',
            part2_q3_note_before TEXT,
            part2_q3_note_after TEXT,
            part2_q4_unique_value VARCHAR(20) NOT NULL DEFAULT 'unknown',
            part2_q4_note_before TEXT,
            part2_q4_note_after TEXT,
            part2_q5_company_intro VARCHAR(20) NOT NULL DEFAULT 'unknown',
            part2_q5_note_before TEXT,
            part2_q5_note_after TEXT,
            part2_q6_visual_tools VARCHAR(20) NOT NULL DEFAULT 'unknown',
            part2_q6_note_before TEXT,
            part2_q6_note_after TEXT,
            part2_q7_technical_specs VARCHAR(20) NOT NULL DEFAULT 'unknown',
            part2_q7_note_before TEXT,
            part2_q7_note_after TEXT,
            part3_q1_opening VARCHAR(20) NOT NULL DEFAULT 'unknown',
            part3_q1_note_before TEXT,
            part3_q1_note_after TEXT,
            part3_q2_ice_breaking VARCHAR(20) NOT NULL DEFAULT 'unknown',
            part3_q2_note_before TEXT,
            part3_q2_note_after TEXT,
            part3_q3_core_questions VARCHAR(20) NOT NULL DEFAULT 'unknown',
            part3_q3_note_before TEXT,
            part3_q3_note_after TEXT,
            part3_q4_follow_up VARCHAR(20) NOT NULL DEFAULT 'unknown',
            part3_q4_note_before TEXT,
            part3_q4_note_after TEXT,
            part3_q5_concerns VARCHAR(20) NOT NULL DEFAULT 'unknown',
            part3_q5_note_before TEXT,
            part3_q5_note_after TEXT,
            part3_q6_backup_plan VARCHAR(20) NOT NULL DEFAULT 'unknown',
            part3_q6_note_before TEXT,
            part3_q6_note_after TEXT,
            part3_q7_action_items VARCHAR(20) NOT NULL DEFAULT 'unknown',
            part3_q7_note_before TEXT,
            part3_q7_note_after TEXT,
            part4_q1_logistics VARCHAR(20) NOT NULL DEFAULT 'unknown',
            part4_q1_note_before TEXT,
            part4_q1_note_after TEXT,
            part4_q2_materials VARCHAR(20) NOT NULL DEFAULT 'unknown',
            part4_q2_note_before TEXT,
            part4_q2_note_after TEXT,
            part4_q3_role_division VARCHAR(20) NOT NULL DEFAULT 'unknown',
            part4_q3_note_before TEXT,
            part4_q3_note_after TEXT,
            part4_q4_mindset VARCHAR(20) NOT NULL DEFAULT 'unknown',
            part4_q4_note_before TEXT,
            part4_q4_note_after TEXT,
            part5_key_info_updates TEXT,
            part5_priority_requirement TEXT,
            part5_goal_assessment TEXT,
            part5_next_action_ours TEXT,
            part5_next_action_client TEXT,
            part5_followup_schedule TEXT,
            part5_challenges TEXT,
            part5_improvement_suggestions TEXT,
            created_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            client_id INTEGER NOT NULL,
            created_by_id INTEGER NOT NULL,
            opportunity_id INTEGER,
            FOREIGN KEY (client_id) REFERENCES customer_client(id),
            FOREIGN KEY (created_by_id) REFERENCES system_user(id),
            FOREIGN KEY (opportunity_id) REFERENCES business_opportunity(id)
        );
        
        CREATE INDEX customer_co_client__d4fab3_idx ON customer_communication_checklist(client_id, communication_date DESC);
        CREATE INDEX customer_co_opportu_1e8e11_idx ON customer_communication_checklist(opportunity_id, communication_date DESC);
        CREATE INDEX customer_co_status_b59455_idx ON customer_communication_checklist(status, communication_date DESC);
        CREATE INDEX customer_co_checkli_dd54e8_idx ON customer_communication_checklist(checklist_number);
        """
    else:  # MySQL
        sql = """
        CREATE TABLE customer_communication_checklist (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            checklist_number VARCHAR(50) UNIQUE,
            title VARCHAR(200) NOT NULL,
            communication_date DATETIME NOT NULL,
            location VARCHAR(200),
            status VARCHAR(20) NOT NULL DEFAULT 'before',
            part1_q1_client_info VARCHAR(20) NOT NULL DEFAULT 'unknown',
            part1_q1_note_before TEXT,
            part1_q1_note_after TEXT,
            part1_q2_business_model VARCHAR(20) NOT NULL DEFAULT 'unknown',
            part1_q2_note_before TEXT,
            part1_q2_note_after TEXT,
            part1_q3_design_stage VARCHAR(20) NOT NULL DEFAULT 'unknown',
            part1_q3_note_before TEXT,
            part1_q3_note_after TEXT,
            part1_q4_key_nodes VARCHAR(20) NOT NULL DEFAULT 'unknown',
            part1_q4_note_before TEXT,
            part1_q4_note_after TEXT,
            part1_q5_design_unit VARCHAR(20) NOT NULL DEFAULT 'unknown',
            part1_q5_note_before TEXT,
            part1_q5_note_after TEXT,
            part1_q6_pain_points VARCHAR(20) NOT NULL DEFAULT 'unknown',
            part1_q6_note_before TEXT,
            part1_q6_note_after TEXT,
            part1_q7_decision_makers VARCHAR(20) NOT NULL DEFAULT 'unknown',
            part1_q7_note_before TEXT,
            part1_q7_note_after TEXT,
            part2_q1_core_goal VARCHAR(20) NOT NULL DEFAULT 'unknown',
            part2_q1_note_before TEXT,
            part2_q1_note_after TEXT,
            part2_q2_secondary_goals VARCHAR(20) NOT NULL DEFAULT 'unknown',
            part2_q2_note_before TEXT,
            part2_q2_note_after TEXT,
            part2_q3_success_cases VARCHAR(20) NOT NULL DEFAULT 'unknown',
            part2_q3_note_before TEXT,
            part2_q3_note_after TEXT,
            part2_q4_unique_value VARCHAR(20) NOT NULL DEFAULT 'unknown',
            part2_q4_note_before TEXT,
            part2_q4_note_after TEXT,
            part2_q5_company_intro VARCHAR(20) NOT NULL DEFAULT 'unknown',
            part2_q5_note_before TEXT,
            part2_q5_note_after TEXT,
            part2_q6_visual_tools VARCHAR(20) NOT NULL DEFAULT 'unknown',
            part2_q6_note_before TEXT,
            part2_q6_note_after TEXT,
            part2_q7_technical_specs VARCHAR(20) NOT NULL DEFAULT 'unknown',
            part2_q7_note_before TEXT,
            part2_q7_note_after TEXT,
            part3_q1_opening VARCHAR(20) NOT NULL DEFAULT 'unknown',
            part3_q1_note_before TEXT,
            part3_q1_note_after TEXT,
            part3_q2_ice_breaking VARCHAR(20) NOT NULL DEFAULT 'unknown',
            part3_q2_note_before TEXT,
            part3_q2_note_after TEXT,
            part3_q3_core_questions VARCHAR(20) NOT NULL DEFAULT 'unknown',
            part3_q3_note_before TEXT,
            part3_q3_note_after TEXT,
            part3_q4_follow_up VARCHAR(20) NOT NULL DEFAULT 'unknown',
            part3_q4_note_before TEXT,
            part3_q4_note_after TEXT,
            part3_q5_concerns VARCHAR(20) NOT NULL DEFAULT 'unknown',
            part3_q5_note_before TEXT,
            part3_q5_note_after TEXT,
            part3_q6_backup_plan VARCHAR(20) NOT NULL DEFAULT 'unknown',
            part3_q6_note_before TEXT,
            part3_q6_note_after TEXT,
            part3_q7_action_items VARCHAR(20) NOT NULL DEFAULT 'unknown',
            part3_q7_note_before TEXT,
            part3_q7_note_after TEXT,
            part4_q1_logistics VARCHAR(20) NOT NULL DEFAULT 'unknown',
            part4_q1_note_before TEXT,
            part4_q1_note_after TEXT,
            part4_q2_materials VARCHAR(20) NOT NULL DEFAULT 'unknown',
            part4_q2_note_before TEXT,
            part4_q2_note_after TEXT,
            part4_q3_role_division VARCHAR(20) NOT NULL DEFAULT 'unknown',
            part4_q3_note_before TEXT,
            part4_q3_note_after TEXT,
            part4_q4_mindset VARCHAR(20) NOT NULL DEFAULT 'unknown',
            part4_q4_note_before TEXT,
            part4_q4_note_after TEXT,
            part5_key_info_updates TEXT,
            part5_priority_requirement TEXT,
            part5_goal_assessment TEXT,
            part5_next_action_ours TEXT,
            part5_next_action_client TEXT,
            part5_followup_schedule TEXT,
            part5_challenges TEXT,
            part5_improvement_suggestions TEXT,
            created_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            client_id BIGINT NOT NULL,
            created_by_id BIGINT NOT NULL,
            opportunity_id BIGINT,
            FOREIGN KEY (client_id) REFERENCES customer_client(id) ON DELETE RESTRICT,
            FOREIGN KEY (created_by_id) REFERENCES system_user(id) ON DELETE RESTRICT,
            FOREIGN KEY (opportunity_id) REFERENCES business_opportunity(id) ON DELETE SET NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        
        CREATE INDEX customer_co_client__d4fab3_idx ON customer_communication_checklist(client_id, communication_date DESC);
        CREATE INDEX customer_co_opportu_1e8e11_idx ON customer_communication_checklist(opportunity_id, communication_date DESC);
        CREATE INDEX customer_co_status_b59455_idx ON customer_communication_checklist(status, communication_date DESC);
        CREATE INDEX customer_co_checkli_dd54e8_idx ON customer_communication_checklist(checklist_number);
        """
    
    try:
        # 执行SQL语句
        cursor.execute(sql)
        connection.commit()
        print("✓ 表创建成功")
        
        # 标记迁移为已应用
        if db_backend == 'postgresql':
            cursor.execute("""
                INSERT INTO django_migrations (app, name, applied)
                VALUES ('customer_success', '0025_add_communication_checklist', CURRENT_TIMESTAMP)
                ON CONFLICT DO NOTHING
            """)
        else:
            cursor.execute("""
                INSERT OR IGNORE INTO django_migrations (app, name, applied)
                VALUES ('customer_success', '0025_add_communication_checklist', CURRENT_TIMESTAMP)
            """)
        connection.commit()
        print("✓ 迁移记录已标记为已应用")
        return True
    except Exception as e:
        connection.rollback()
        print(f"✗ 创建表失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("=" * 60)
    print("直接创建客户沟通准备清单表")
    print("=" * 60)
    
    success = create_table_directly()
    
    if success:
        print("\n" + "=" * 60)
        print("✓ 完成！表已创建，迁移已标记")
        print("=" * 60)
        sys.exit(0)
    else:
        print("\n" + "=" * 60)
        print("✗ 失败！请检查错误信息")
        print("=" * 60)
        sys.exit(1)

