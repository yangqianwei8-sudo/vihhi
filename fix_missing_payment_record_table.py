#!/usr/bin/env python
"""
修复缺失的 settlement_management_payment_record 表
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.config.settings')
django.setup()

from django.apps import apps
from django.db import connection
from django.db import models

def fix_missing_table():
    """创建缺失的 PaymentRecord 表"""
    print("=" * 80)
    print("修复缺失的 settlement_management_payment_record 表")
    print("=" * 80)
    
    try:
        # 获取 PaymentRecord 模型
        PaymentRecord = apps.get_model('settlement_management', 'PaymentRecord')
        table_name = PaymentRecord._meta.db_table
        
        print(f"\n模型: settlement_management.PaymentRecord")
        print(f"表名: {table_name}")
        
        # 检查表是否存在
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = %s
            """, [table_name])
            
            exists = cursor.fetchone() is not None
        
        if exists:
            print(f"\n✓ 表 {table_name} 已存在")
            return True
        
        print(f"\n✗ 表 {table_name} 不存在，开始创建...")
        
        # 创建表
        try:
            with connection.schema_editor() as schema_editor:
                schema_editor.create_model(PaymentRecord)
            print(f"✓ 成功创建表: {table_name}")
            
            # 验证表是否创建成功
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = %s
                """, [table_name])
                
                if cursor.fetchone():
                    print(f"✓ 验证成功: 表 {table_name} 已创建")
                    return True
                else:
                    print(f"✗ 验证失败: 表 {table_name} 创建后仍不存在")
                    return False
                    
        except Exception as e:
            error_msg = str(e)
            if 'already exists' in error_msg.lower() or 'duplicate' in error_msg.lower():
                print(f"- 表已存在: {table_name}")
                return True
            else:
                print(f"✗ 创建表失败: {error_msg}")
                return False
                
    except LookupError as e:
        print(f"✗ 无法找到模型: {e}")
        return False
    except Exception as e:
        print(f"✗ 发生错误: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_all_settlement_tables():
    """检查 settlement_management 应用的所有表"""
    print("\n" + "=" * 80)
    print("检查 settlement_management 应用的所有表")
    print("=" * 80)
    
    try:
        app_config = apps.get_app_config('settlement_management')
        models_list = app_config.get_models()
        
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_type = 'BASE TABLE'
            """)
            all_tables = {row[0] for row in cursor.fetchall()}
        
        print(f"\n找到 {len(models_list)} 个模型:")
        missing = []
        existing = []
        
        for model in models_list:
            table_name = model._meta.db_table
            if table_name in all_tables:
                existing.append(table_name)
                print(f"  ✓ {model.__name__} -> {table_name}")
            else:
                missing.append((model, table_name))
                print(f"  ✗ {model.__name__} -> {table_name} (缺失)")
        
        print(f"\n总结: {len(existing)} 个表存在, {len(missing)} 个表缺失")
        
        if missing:
            print("\n开始创建缺失的表...")
            for model, table_name in missing:
                try:
                    with connection.schema_editor() as schema_editor:
                        schema_editor.create_model(model)
                    print(f"  ✓ 创建表: {table_name}")
                except Exception as e:
                    error_msg = str(e)
                    if 'already exists' in error_msg.lower():
                        print(f"  - 表已存在: {table_name}")
                    else:
                        print(f"  ✗ 创建表失败: {table_name} - {error_msg}")
        
        return len(missing) == 0
        
    except Exception as e:
        print(f"✗ 检查失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    # 先修复 PaymentRecord 表
    success = fix_missing_table()
    
    # 然后检查所有 settlement_management 的表
    check_all_settlement_tables()
    
    print("\n" + "=" * 80)
    if success:
        print("修复完成！")
    else:
        print("修复过程中遇到问题，请检查上面的错误信息")
    print("=" * 80)





