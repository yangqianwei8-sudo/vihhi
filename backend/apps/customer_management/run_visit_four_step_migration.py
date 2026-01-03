#!/usr/bin/env python
"""
直接执行SQL创建拜访四步流程相关的表
绕过Django迁移系统的依赖问题
"""
import os
import sys

# 添加项目根目录到Python路径
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, '../../../'))
sys.path.insert(0, project_root)

import django

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.config.settings')
django.setup()

from django.db import connection
from django.core.management import call_command

def execute_migration():
    """执行迁移"""
    cursor = connection.cursor()
    
    print("=" * 60)
    print("开始执行拜访四步流程迁移...")
    print("=" * 60)
    
    # SQL语句列表
    sql_statements = [
        # 创建VisitReview表
        """
        CREATE TABLE IF NOT EXISTS customer_visit_review (
            id BIGSERIAL PRIMARY KEY,
            visit_result TEXT NOT NULL,
            customer_feedback TEXT,
            key_points TEXT,
            next_actions TEXT,
            satisfaction_score INTEGER CHECK (satisfaction_score >= 1 AND satisfaction_score <= 10),
            effectiveness VARCHAR(20) CHECK (effectiveness IN ('excellent', 'good', 'average', 'poor')),
            created_time TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_time TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
            created_by_id BIGINT NOT NULL,
            visit_checkin_id BIGINT,
            visit_plan_id BIGINT NOT NULL UNIQUE,
            CONSTRAINT customer_visit_review_created_by_id_fk 
                FOREIGN KEY (created_by_id) REFERENCES system_user(id) ON DELETE RESTRICT,
            CONSTRAINT customer_visit_review_visit_checkin_id_fk 
                FOREIGN KEY (visit_checkin_id) REFERENCES customer_visit_checkin(id) ON DELETE SET NULL,
            CONSTRAINT customer_visit_review_visit_plan_id_fk 
                FOREIGN KEY (visit_plan_id) REFERENCES customer_visit_plan(id) ON DELETE CASCADE
        );
        """,
        
        # 添加索引
        """
        CREATE INDEX IF NOT EXISTS customer_visit_review_created_time_idx 
        ON customer_visit_review(created_time DESC);
        """,
        
        # 为VisitPlan表添加新字段
        """
        ALTER TABLE customer_visit_plan 
        ADD COLUMN IF NOT EXISTS communication_checklist TEXT;
        """,
        
        """
        ALTER TABLE customer_visit_plan 
        ADD COLUMN IF NOT EXISTS checklist_prepared BOOLEAN NOT NULL DEFAULT FALSE;
        """,
        
        """
        ALTER TABLE customer_visit_plan 
        ADD COLUMN IF NOT EXISTS checklist_prepared_time TIMESTAMP WITH TIME ZONE;
        """,
    ]
    
    success_count = 0
    error_count = 0
    
    for sql in sql_statements:
        sql_clean = ' '.join(sql.split())
        if not sql_clean:
            continue
            
        try:
            cursor.execute(sql_clean)
            success_count += 1
            print(f"✅ 执行成功")
        except Exception as e:
            error_msg = str(e).lower()
            # 如果是表或字段已存在的错误，忽略
            if 'already exists' in error_msg or 'duplicate' in error_msg or 'column' in error_msg and 'already' in error_msg:
                print(f"⚠️  已存在，跳过")
                success_count += 1
                error_count -= 1
            else:
                error_count += 1
                print(f"❌ 执行失败: {e}")
                print(f"   SQL: {sql_clean[:100]}...")
    
    # 提交事务
    try:
        connection.commit()
        print(f"\n{'=' * 60}")
        print(f"✅ 迁移完成！成功: {success_count}, 失败: {error_count}")
        print(f"{'=' * 60}")
    except Exception as e:
        connection.rollback()
        print(f"\n❌ 提交失败: {e}")
        return False
    
    # 标记迁移为已应用
    if error_count == 0:
        try:
            print("\n正在标记迁移为已应用...")
            call_command('migrate', 'customer_success', '0028', '--fake', verbosity=0)
            print("✅ 迁移已标记为已应用")
        except Exception as e:
            print(f"⚠️  标记迁移失败（不影响功能）: {e}")
            print("   您可以稍后手动运行: python manage.py migrate customer_success 0028 --fake")
    
    return error_count == 0

def check_tables():
    """检查表是否创建成功"""
    cursor = connection.cursor()
    
    # 检查VisitReview表
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name = 'customer_visit_review'
    """)
    review_table_exists = cursor.fetchone() is not None
    
    # 检查VisitPlan表的字段
    cursor.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_schema = 'public' 
        AND table_name = 'customer_visit_plan'
        AND column_name IN ('communication_checklist', 'checklist_prepared', 'checklist_prepared_time')
    """)
    plan_fields = [row[0] for row in cursor.fetchall()]
    
    return review_table_exists, plan_fields

if __name__ == '__main__':
    print("开始执行拜访四步流程迁移...\n")
    
    # 执行迁移
    success = execute_migration()
    
    if success:
        # 检查表
        print("\n检查迁移结果...")
        review_exists, plan_fields = check_tables()
        
        if review_exists:
            print("✅ customer_visit_review 表已创建")
        else:
            print("❌ customer_visit_review 表未创建")
        
        if len(plan_fields) == 3:
            print(f"✅ customer_visit_plan 表字段已添加: {', '.join(plan_fields)}")
        else:
            print(f"⚠️  customer_visit_plan 表字段部分添加: {', '.join(plan_fields) if plan_fields else '无'}")
        
        print("\n✅ 迁移完成！")
    else:
        print("\n❌ 迁移失败，请检查错误信息")
        sys.exit(1)

