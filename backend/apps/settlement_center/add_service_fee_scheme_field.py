#!/usr/bin/env python
"""
添加service_fee_scheme_id字段到ProjectSettlement表

使用方法：
    cd /home/devbox/project/vihhi/weihai_tech_production_system
    source venv/bin/activate
    python manage.py shell < backend/apps/settlement_center/add_service_fee_scheme_field.py
    
或者：
    python backend/apps/settlement_center/add_service_fee_scheme_field.py
"""
import os
import sys

# 尝试从manage.py所在目录运行
manage_py_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
if os.path.exists(os.path.join(manage_py_dir, 'manage.py')):
    os.chdir(manage_py_dir)
    sys.path.insert(0, manage_py_dir)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.config.settings')

import django
try:
    django.setup()
except Exception as e:
    print(f"Django setup失败: {e}")
    print("\n请使用以下方式运行:")
    print("  cd /home/devbox/project/vihhi/weihai_tech_production_system")
    print("  source venv/bin/activate")
    print("  python manage.py shell")
    print("  >>> exec(open('backend/apps/settlement_center/add_service_fee_scheme_field.py').read())")
    sys.exit(1)

from django.db import connection

def add_service_fee_scheme_field():
    """添加service_fee_scheme_id字段"""
    print("检查settlement_project_settlement表是否存在...")
    
    with connection.cursor() as cursor:
        # 检查表是否存在
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'settlement_project_settlement'
            )
        """)
        table_exists = cursor.fetchone()[0]
        
        if not table_exists:
            print("⚠ settlement_project_settlement表不存在，跳过字段添加")
            print("   提示: 请先运行settlement_center的其他迁移创建此表")
            return False
        
        # 检查字段是否已存在
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.columns 
                WHERE table_name = 'settlement_project_settlement' 
                AND column_name = 'service_fee_scheme_id'
            )
        """)
        field_exists = cursor.fetchone()[0]
        
        if field_exists:
            print("✓ service_fee_scheme_id字段已存在")
            return True
        
        # 检查settlement_service_fee_scheme表是否存在
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'settlement_service_fee_scheme'
            )
        """)
        scheme_table_exists = cursor.fetchone()[0]
        
        if not scheme_table_exists:
            print("❌ settlement_service_fee_scheme表不存在，无法添加外键")
            return False
        
        # 添加字段
        print("正在添加service_fee_scheme_id字段...")
        try:
            cursor.execute("""
                ALTER TABLE settlement_project_settlement 
                ADD COLUMN service_fee_scheme_id BIGINT 
                REFERENCES settlement_service_fee_scheme(id) 
                ON DELETE SET NULL
            """)
            
            # 创建索引
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS settlement_project_settlement_service_fee_scheme_id_idx 
                ON settlement_project_settlement(service_fee_scheme_id)
            """)
            
            print("✓ 字段添加成功")
            return True
            
        except Exception as e:
            print(f"❌ 添加字段失败: {str(e)}")
            return False

if __name__ == '__main__':
    success = add_service_fee_scheme_field()
    sys.exit(0 if success else 1)

