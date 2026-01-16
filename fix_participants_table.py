#!/usr/bin/env python
"""修复participants表创建问题"""

import os
import sys
import django

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.config.settings')
django.setup()

from django.db import connection

def fix_participants_table():
    """修复participants表"""
    cursor = connection.cursor()
    
    try:
        # 检查表是否存在
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'business_contract_negotiation_participants'
            );
        """)
        table_exists = cursor.fetchone()[0]
        
        if table_exists:
            print("✓ participants表已存在")
            return True
        
        # 检查是否有残留约束
        cursor.execute("""
            SELECT conname FROM pg_constraint 
            WHERE conname LIKE 'business_contract_negotiation_participants%'
            AND conrelid = 0;
        """)
        orphan_constraints = cursor.fetchall()
        
        # 创建表（不带约束）
        print("创建participants表（无约束）...")
        cursor.execute("""
            CREATE TABLE business_contract_negotiation_participants (
                id BIGSERIAL PRIMARY KEY,
                contractnegotiation_id BIGINT NOT NULL,
                user_id BIGINT NOT NULL
            );
        """)
        connection.commit()
        print("✓ 表创建成功")
        
        # 添加外键约束1
        try:
            cursor.execute("""
                ALTER TABLE business_contract_negotiation_participants
                ADD CONSTRAINT business_contract_negotiation_participants_contractnegotiation_id_fk 
                FOREIGN KEY (contractnegotiation_id) 
                REFERENCES business_contract_negotiation(id) 
                ON DELETE CASCADE;
            """)
            connection.commit()
            print("✓ 外键约束1添加成功")
        except Exception as e:
            if 'already exists' in str(e).lower():
                print("⚠ 外键约束1已存在")
            else:
                print(f"外键约束1添加失败: {e}")
        
        # 添加外键约束2
        try:
            cursor.execute("""
                ALTER TABLE business_contract_negotiation_participants
                ADD CONSTRAINT business_contract_negotiation_participants_user_id_fk 
                FOREIGN KEY (user_id) 
                REFERENCES system_user(id) 
                ON DELETE CASCADE;
            """)
            connection.commit()
            print("✓ 外键约束2添加成功")
        except Exception as e:
            if 'already exists' in str(e).lower():
                print("⚠ 外键约束2已存在")
            else:
                print(f"外键约束2添加失败: {e}")
        
        # 添加唯一约束
        try:
            cursor.execute("""
                ALTER TABLE business_contract_negotiation_participants
                ADD CONSTRAINT business_contract_negotiation_participants_contractnegotiation_id_user_id_uniq 
                UNIQUE (contractnegotiation_id, user_id);
            """)
            connection.commit()
            print("✓ 唯一约束添加成功")
        except Exception as e:
            if 'already exists' in str(e).lower():
                print("⚠ 唯一约束已存在")
            else:
                print(f"唯一约束添加失败: {e}")
        
        # 创建索引
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS business_contract_negotiation_participants_contractnegotiation_id_idx 
            ON business_contract_negotiation_participants(contractnegotiation_id);
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS business_contract_negotiation_participants_user_id_idx 
            ON business_contract_negotiation_participants(user_id);
        """)
        connection.commit()
        print("✓ 索引创建成功")
        
        return True
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        connection.rollback()
        return False

if __name__ == '__main__':
    print("修复participants表...")
    success = fix_participants_table()
    if success:
        print("\n✅ 修复完成！")
    else:
        print("\n❌ 修复失败！")

