#!/usr/bin/env python
"""应用沟通清单问题管理迁移脚本（0026和0027）"""
import os
import sys
import django

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.config.settings')
django.setup()

from django.core.management import call_command
from django.db import connection

def check_migration_status(migration_name):
    """检查迁移状态"""
    cursor = connection.cursor()
    cursor.execute("""
        SELECT COUNT(*) FROM django_migrations 
        WHERE app='customer_success' AND name=%s
    """, [migration_name])
    result = cursor.fetchone()
    return result[0] > 0 if result else False

def check_table_exists(table_name):
    """检查表是否存在"""
    cursor = connection.cursor()
    db_backend = connection.vendor
    
    if db_backend == 'postgresql':
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_name = %s
            )
        """, [table_name])
        result = cursor.fetchone()
        return result[0] if result else False
    elif db_backend == 'sqlite':
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name=?
        """, [table_name])
        return cursor.fetchone() is not None
    else:  # MySQL
        cursor.execute("""
            SELECT COUNT(*) FROM information_schema.tables 
            WHERE table_schema = DATABASE() AND table_name = %s
        """, [table_name])
        result = cursor.fetchone()
        return result[0] > 0 if result else False

def check_questions_count():
    """检查问题数量"""
    try:
        from backend.apps.customer_management.models import CommunicationChecklistQuestion
        count = CommunicationChecklistQuestion.objects.count()
        return count
    except Exception:
        return 0

if __name__ == '__main__':
    print("=" * 60)
    print("沟通清单问题管理迁移检查（0026和0027）")
    print("=" * 60)
    
    # 检查0026迁移状态
    migration_0026_applied = check_migration_status('0026_add_communication_checklist_questions')
    print(f"\n0026迁移状态: {'已应用' if migration_0026_applied else '未应用'}")
    
    # 检查0027迁移状态
    migration_0027_applied = check_migration_status('0027_seed_communication_checklist_questions')
    print(f"0027迁移状态: {'已应用' if migration_0027_applied else '未应用'}")
    
    # 检查表是否存在
    question_table_exists = check_table_exists('communication_checklist_question')
    answer_table_exists = check_table_exists('communication_checklist_answer')
    print(f"\n问题表状态: {'已存在' if question_table_exists else '不存在'}")
    print(f"答案表状态: {'已存在' if answer_table_exists else '不存在'}")
    
    # 检查问题数量
    questions_count = check_questions_count()
    print(f"问题数量: {questions_count}")
    
    print("\n" + "=" * 60)
    
    # 如果都已应用，直接退出
    if migration_0026_applied and migration_0027_applied and question_table_exists and answer_table_exists:
        print("✓ 迁移已完成，表已创建")
        if questions_count >= 25:
            print(f"✓ 问题数据已初始化（{questions_count}个问题）")
        else:
            print(f"⚠ 问题数量不足（期望25个，实际{questions_count}个）")
        sys.exit(0)
    
    # 尝试应用迁移
    if not migration_0026_applied or not question_table_exists:
        print("\n正在应用0026迁移（创建表结构）...")
        try:
            call_command('migrate', 'customer_success', '0026_add_communication_checklist_questions', verbosity=2)
            print("✓ 0026迁移应用成功")
            
            # 再次检查
            migration_0026_applied = check_migration_status('0026_add_communication_checklist_questions')
            question_table_exists = check_table_exists('communication_checklist_question')
            answer_table_exists = check_table_exists('communication_checklist_answer')
            
            if migration_0026_applied and question_table_exists and answer_table_exists:
                print("✓ 验证成功：表已创建")
            else:
                print("⚠ 警告：迁移可能未完全应用")
        except Exception as e:
            print(f"✗ 0026迁移失败: {str(e)}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
    
    # 应用0027迁移（初始化数据）
    if not migration_0027_applied:
        print("\n正在应用0027迁移（初始化问题数据）...")
        try:
            call_command('migrate', 'customer_success', '0027_seed_communication_checklist_questions', verbosity=2)
            print("✓ 0027迁移应用成功")
            
            # 检查问题数量
            questions_count = check_questions_count()
            if questions_count >= 25:
                print(f"✓ 问题数据已初始化（{questions_count}个问题）")
            else:
                print(f"⚠ 问题数量不足（期望25个，实际{questions_count}个）")
        except Exception as e:
            print(f"✗ 0027迁移失败: {str(e)}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
    
    print("\n" + "=" * 60)
    print("✓ 迁移完成！")
    print("=" * 60)
    
    # 最终验证
    migration_0026_applied = check_migration_status('0026_add_communication_checklist_questions')
    migration_0027_applied = check_migration_status('0027_seed_communication_checklist_questions')
    question_table_exists = check_table_exists('communication_checklist_question')
    answer_table_exists = check_table_exists('communication_checklist_answer')
    questions_count = check_questions_count()
    
    print(f"\n最终状态：")
    print(f"  - 0026迁移: {'✓' if migration_0026_applied else '✗'}")
    print(f"  - 0027迁移: {'✓' if migration_0027_applied else '✗'}")
    print(f"  - 问题表: {'✓' if question_table_exists else '✗'}")
    print(f"  - 答案表: {'✓' if answer_table_exists else '✗'}")
    print(f"  - 问题数量: {questions_count}")

