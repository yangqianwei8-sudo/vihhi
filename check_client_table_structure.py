#!/usr/bin/env python
"""
检查 customer_client 表的结构，确认是否有旧的 client_type 字段
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.config.settings')
django.setup()

from django.db import connection


def check_table_structure():
    """检查表结构"""
    with connection.cursor() as cursor:
        print("=" * 60)
        print("检查 customer_client 表结构...")
        print("=" * 60)
        
        # 检查所有列
        cursor.execute("""
            SELECT 
                column_name, 
                data_type,
                is_nullable,
                column_default
            FROM information_schema.columns 
            WHERE table_name = 'customer_client'
            AND (column_name LIKE '%client_type%' OR column_name LIKE '%type%')
            ORDER BY column_name;
        """)
        
        columns = cursor.fetchall()
        print("\n相关字段：")
        for col in columns:
            print(f"  - {col[0]}: {col[1]}, NULL={col[2]}, Default={col[3]}")
        
        # 检查是否有旧的 client_type 字段（VARCHAR）
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'customer_client' 
            AND column_name = 'client_type'
            AND data_type = 'character varying';
        """)
        
        old_field = cursor.fetchone()
        if old_field:
            print("\n⚠️  发现旧的 client_type 字段（VARCHAR）！")
            print("   这可能是导致问题的原因。")
            return True
        else:
            print("\n✓ 未发现旧的 client_type VARCHAR 字段")
            return False


if __name__ == '__main__':
    check_table_structure()

