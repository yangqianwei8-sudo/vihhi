#!/usr/bin/env python
"""
安全删除客户数据脚本

删除范围：
- 19 个客户
- 3 个客户联系人
- 25 条执行记录
- 4 条客户关系

注意：会先检查并处理外键约束
"""
import os
import sys
import django

# 设置Django环境
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(script_dir))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.config.settings')

try:
    django.setup()
except Exception as e:
    print(f"❌ Django 设置失败: {e}")
    sys.exit(1)

from django.db import connection, transaction
from django.contrib.contenttypes.models import ContentType

def check_foreign_key_constraints():
    """检查外键约束"""
    print("=" * 70)
    print("检查外键约束")
    print("=" * 70)
    print()
    
    cursor = connection.cursor()
    issues = []
    
    # 检查项目关联
    cursor.execute("""
        SELECT COUNT(*) 
        FROM production_management_project 
        WHERE client_id IS NOT NULL
    """)
    project_count = cursor.fetchone()[0]
    if project_count > 0:
        issues.append(('production_management_project', project_count, 'PROTECT'))
        print(f"⚠️  发现 {project_count} 个项目关联了客户（PROTECT约束）")
    
    # 检查合同关联
    cursor.execute("""
        SELECT COUNT(*) 
        FROM production_management_businesscontract 
        WHERE client_id IS NOT NULL
    """)
    contract_count = cursor.fetchone()[0]
    if contract_count > 0:
        issues.append(('production_management_businesscontract', contract_count, 'PROTECT'))
        print(f"⚠️  发现 {contract_count} 个合同关联了客户（PROTECT约束）")
    
    # 检查应收账款关联
    cursor.execute("""
        SELECT COUNT(*) 
        FROM financial_management_receivable 
        WHERE customer_id IS NOT NULL
    """)
    receivable_count = cursor.fetchone()[0]
    if receivable_count > 0:
        issues.append(('financial_management_receivable', receivable_count, 'PROTECT'))
        print(f"⚠️  发现 {receivable_count} 条应收账款关联了客户（PROTECT约束）")
    
    # 检查交付记录关联（SET_NULL，不影响删除）
    cursor.execute("""
        SELECT COUNT(*) 
        FROM delivery_customer_deliveryrecord 
        WHERE client_id IS NOT NULL
    """)
    delivery_count = cursor.fetchone()[0]
    if delivery_count > 0:
        print(f"ℹ️  发现 {delivery_count} 条交付记录关联了客户（SET_NULL，删除后关联会丢失）")
    
    # 检查诉讼案件关联（SET_NULL，不影响删除）
    cursor.execute("""
        SELECT COUNT(*) 
        FROM litigation_management_litigationcase 
        WHERE client_id IS NOT NULL
    """)
    litigation_count = cursor.fetchone()[0]
    if litigation_count > 0:
        print(f"ℹ️  发现 {litigation_count} 个诉讼案件关联了客户（SET_NULL，删除后关联会丢失）")
    
    print()
    return issues

def remove_foreign_key_constraints(issues):
    """解除外键约束"""
    if not issues:
        print("✅ 没有需要解除的 PROTECT 约束")
        return True
    
    print("=" * 70)
    print("解除外键约束")
    print("=" * 70)
    print()
    
    cursor = connection.cursor()
    
    for table_name, count, constraint_type in issues:
        print(f"处理 {table_name} ({count} 条记录)...")
        
        if table_name == 'production_management_project':
            cursor.execute("""
                UPDATE production_management_project 
                SET client_id = NULL 
                WHERE client_id IS NOT NULL
            """)
        elif table_name == 'production_management_businesscontract':
            cursor.execute("""
                UPDATE production_management_businesscontract 
                SET client_id = NULL 
                WHERE client_id IS NOT NULL
            """)
        elif table_name == 'financial_management_receivable':
            cursor.execute("""
                UPDATE financial_management_receivable 
                SET customer_id = NULL 
                WHERE customer_id IS NOT NULL
            """)
        
        print(f"  ✅ 已解除 {count} 条记录的关联")
    
    connection.commit()
    print()
    return True

def get_data_counts():
    """获取当前数据量"""
    cursor = connection.cursor()
    
    counts = {}
    
    cursor.execute("SELECT COUNT(*) FROM customer_client")
    counts['client'] = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM customer_contact")
    counts['contact'] = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM customer_execution_record")
    counts['execution_record'] = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM customer_relationship")
    counts['relationship'] = cursor.fetchone()[0]
    
    return counts

def delete_customer_data():
    """删除客户数据"""
    print("=" * 70)
    print("删除客户数据")
    print("=" * 70)
    print()
    
    # 获取删除前的数据量
    before_counts = get_data_counts()
    print("删除前的数据量：")
    print(f"  客户: {before_counts['client']} 条")
    print(f"  客户联系人: {before_counts['contact']} 条")
    print(f"  执行记录: {before_counts['execution_record']} 条")
    print(f"  客户关系: {before_counts['relationship']} 条")
    print()
    
    from backend.apps.customer_management.models import Client
    
    # 删除所有客户（会级联删除关联数据）
    with transaction.atomic():
        deleted_count = Client.objects.all().delete()[0]
        print(f"✅ 已删除 {deleted_count} 条客户记录（包括所有关联数据）")
    
    # 获取删除后的数据量
    after_counts = get_data_counts()
    print()
    print("删除后的数据量：")
    print(f"  客户: {after_counts['client']} 条")
    print(f"  客户联系人: {after_counts['contact']} 条")
    print(f"  执行记录: {after_counts['execution_record']} 条")
    print(f"  客户关系: {after_counts['relationship']} 条")
    print()
    
    # 计算实际删除的数据量
    print("实际删除的数据量：")
    print(f"  客户: {before_counts['client'] - after_counts['client']} 条")
    print(f"  客户联系人: {before_counts['contact'] - after_counts['contact']} 条")
    print(f"  执行记录: {before_counts['execution_record'] - after_counts['execution_record']} 条")
    print(f"  客户关系: {before_counts['relationship'] - after_counts['relationship']} 条")

def main():
    """主函数"""
    print("=" * 70)
    print("客户数据删除脚本")
    print("=" * 70)
    print()
    print("⚠️  警告：此操作将删除所有客户数据及其关联数据！")
    print()
    
    # 确认
    confirm = input("确认删除？请输入 'YES' 继续: ")
    if confirm != 'YES':
        print("❌ 操作已取消")
        return
    
    print()
    
    try:
        # 步骤1: 检查外键约束
        issues = check_foreign_key_constraints()
        
        # 步骤2: 解除外键约束（如果有）
        if issues:
            remove_foreign_key_constraints(issues)
        
        # 步骤3: 删除客户数据
        delete_customer_data()
        
        print()
        print("=" * 70)
        print("✅ 删除完成")
        print("=" * 70)
        
    except Exception as e:
        print()
        print("=" * 70)
        print(f"❌ 删除失败: {e}")
        print("=" * 70)
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()

