#!/usr/bin/env python
"""
直接使用 SQL 删除客户数据脚本

删除范围：
- 19 个客户
- 3 个客户联系人
- 25 条执行记录
- 4 条客户关系

注意：会先检查并处理外键约束
"""
import os
import sys
from dotenv import load_dotenv
import psycopg2
from urllib.parse import urlparse

# 加载环境变量
load_dotenv()

def get_db_connection():
    """获取数据库连接"""
    database_url = os.getenv('DATABASE_URL', '')
    if not database_url:
        print("❌ 未找到 DATABASE_URL 环境变量")
        sys.exit(1)
    
    # 解析数据库URL
    parsed = urlparse(database_url)
    
    try:
        conn = psycopg2.connect(
            host=parsed.hostname,
            port=parsed.port or 5432,
            user=parsed.username,
            password=parsed.password,
            database=parsed.path[1:] if parsed.path else 'postgres'
        )
        return conn
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        sys.exit(1)

def check_foreign_key_constraints(cursor):
    """检查外键约束"""
    print("=" * 70)
    print("检查外键约束")
    print("=" * 70)
    print()
    
    issues = []
    
    # 检查项目关联
    try:
        cursor.execute("""
            SELECT COUNT(*) 
            FROM production_management_project 
            WHERE client_id IS NOT NULL
        """)
        project_count = cursor.fetchone()[0]
        if project_count > 0:
            issues.append(('production_management_project', 'client_id', project_count))
            print(f"⚠️  发现 {project_count} 个项目关联了客户（PROTECT约束）")
    except Exception as e:
        # 忽略表不存在的错误
        pass
    
    # 检查合同关联
    try:
        cursor.execute("""
            SELECT COUNT(*) 
            FROM production_management_businesscontract 
            WHERE client_id IS NOT NULL
        """)
        contract_count = cursor.fetchone()[0]
        if contract_count > 0:
            issues.append(('production_management_businesscontract', 'client_id', contract_count))
            print(f"⚠️  发现 {contract_count} 个合同关联了客户（PROTECT约束）")
    except Exception as e:
        # 忽略表不存在的错误
        pass
    
    # 检查应收账款关联
    try:
        cursor.execute("""
            SELECT COUNT(*) 
            FROM financial_management_receivable 
            WHERE customer_id IS NOT NULL
        """)
        receivable_count = cursor.fetchone()[0]
        if receivable_count > 0:
            issues.append(('financial_management_receivable', 'customer_id', receivable_count))
            print(f"⚠️  发现 {receivable_count} 条应收账款关联了客户（PROTECT约束）")
    except Exception as e:
        # 忽略表不存在的错误
        pass
    
    # 检查交付记录关联（SET_NULL，不影响删除）
    try:
        cursor.execute("""
            SELECT COUNT(*) 
            FROM delivery_customer_deliveryrecord 
            WHERE client_id IS NOT NULL
        """)
        delivery_count = cursor.fetchone()[0]
        if delivery_count > 0:
            print(f"ℹ️  发现 {delivery_count} 条交付记录关联了客户（SET_NULL，删除后关联会丢失）")
    except Exception as e:
        pass
    
    # 检查诉讼案件关联（SET_NULL，不影响删除）
    try:
        cursor.execute("""
            SELECT COUNT(*) 
            FROM litigation_management_litigationcase 
            WHERE client_id IS NOT NULL
        """)
        litigation_count = cursor.fetchone()[0]
        if litigation_count > 0:
            print(f"ℹ️  发现 {litigation_count} 个诉讼案件关联了客户（SET_NULL，删除后关联会丢失）")
    except Exception as e:
        pass
    
    # 检查商机关联
    try:
        cursor.execute("""
            SELECT COUNT(*) 
            FROM business_opportunity 
            WHERE client_id IS NOT NULL
        """)
        opportunity_count = cursor.fetchone()[0]
        if opportunity_count > 0:
            issues.append(('business_opportunity', 'client_id', opportunity_count))
            print(f"⚠️  发现 {opportunity_count} 个商机关联了客户（需要解除关联）")
    except Exception as e:
        pass
    
    print()
    return issues

def remove_foreign_key_constraints(cursor, issues):
    """解除外键约束"""
    if not issues:
        print("✅ 没有需要解除的 PROTECT 约束")
        return True
    
    print("=" * 70)
    print("解除外键约束")
    print("=" * 70)
    print()
    
    for table_name, column_name, count in issues:
        print(f"处理 {table_name} ({count} 条记录)...")
        try:
            # 对于 business_opportunity，client_id 不允许 NULL，需要删除记录
            if table_name == 'business_opportunity':
                cursor.execute(f"""
                    DELETE FROM {table_name} 
                    WHERE {column_name} IS NOT NULL
                """)
                print(f"  ✅ 已删除 {count} 条商机记录（client_id 不允许 NULL）")
            else:
                cursor.execute(f"""
                    UPDATE {table_name} 
                    SET {column_name} = NULL 
                    WHERE {column_name} IS NOT NULL
                """)
                print(f"  ✅ 已解除 {count} 条记录的关联")
        except Exception as e:
            print(f"  ❌ 处理失败: {e}")
            return False
    
    print()
    return True

def get_data_counts(cursor):
    """获取当前数据量"""
    counts = {}
    
    try:
        cursor.execute("SELECT COUNT(*) FROM customer_client")
        counts['client'] = cursor.fetchone()[0]
    except:
        counts['client'] = 0
    
    try:
        cursor.execute("SELECT COUNT(*) FROM customer_contact")
        counts['contact'] = cursor.fetchone()[0]
    except:
        counts['contact'] = 0
    
    try:
        cursor.execute("SELECT COUNT(*) FROM customer_execution_record")
        counts['execution_record'] = cursor.fetchone()[0]
    except:
        counts['execution_record'] = 0
    
    try:
        cursor.execute("SELECT COUNT(*) FROM customer_relationship")
        counts['relationship'] = cursor.fetchone()[0]
    except:
        counts['relationship'] = 0
    
    return counts

def delete_customer_data(cursor):
    """删除客户数据"""
    print("=" * 70)
    print("删除客户数据")
    print("=" * 70)
    print()
    
    # 获取删除前的数据量
    before_counts = get_data_counts(cursor)
    print("删除前的数据量：")
    print(f"  客户: {before_counts['client']} 条")
    print(f"  客户联系人: {before_counts['contact']} 条")
    print(f"  执行记录: {before_counts['execution_record']} 条")
    print(f"  客户关系: {before_counts['relationship']} 条")
    print()
    
    # 删除顺序（先删除最底层的关联表，再删除主表）
    # 注意：需要按外键依赖顺序删除，避免外键约束问题
    
    deleted_counts = {}
    
    # 1. 先删除客户关系关联的联系人表
    try:
        cursor.execute("DELETE FROM customer_relationship_related_contacts")
        print(f"✅ 已删除客户关系关联的联系人记录")
    except Exception as e:
        # 表可能不存在，忽略
        pass
    
    # 2. 删除客户关系
    try:
        cursor.execute("DELETE FROM customer_relationship")
        deleted_counts['relationship'] = cursor.rowcount
        print(f"✅ 已删除 {deleted_counts['relationship']} 条客户关系记录")
    except Exception as e:
        print(f"⚠️  删除客户关系时出错: {e}")
    
    # 3. 删除执行记录
    try:
        cursor.execute("DELETE FROM customer_execution_record")
        deleted_counts['execution_record'] = cursor.rowcount
        print(f"✅ 已删除 {deleted_counts['execution_record']} 条执行记录")
    except Exception as e:
        print(f"⚠️  删除执行记录时出错: {e}")
    
    # 4. 删除客户联系人（会级联删除相关数据）
    try:
        cursor.execute("DELETE FROM customer_contact")
        deleted_counts['contact'] = cursor.rowcount
        print(f"✅ 已删除 {deleted_counts['contact']} 条客户联系人记录")
    except Exception as e:
        print(f"⚠️  删除客户联系人时出错: {e}")
    
    # 5. 最后删除客户（会级联删除所有剩余关联数据）
    try:
        cursor.execute("DELETE FROM customer_client")
        deleted_counts['client'] = cursor.rowcount
        print(f"✅ 已删除 {deleted_counts['client']} 条客户记录")
    except Exception as e:
        print(f"❌ 删除客户失败: {e}")
        return False
    
    # 获取删除后的数据量
    after_counts = get_data_counts(cursor)
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
    
    return True

def main():
    """主函数"""
    print("=" * 70)
    print("客户数据删除脚本（SQL版本）")
    print("=" * 70)
    print()
    print("⚠️  警告：此操作将删除所有客户数据及其关联数据！")
    print("   删除范围：")
    print("   - 19 个客户")
    print("   - 3 个客户联系人")
    print("   - 25 条执行记录")
    print("   - 4 条客户关系")
    print()
    
    # 确认
    confirm = input("确认删除？请输入 'YES' 继续: ")
    if confirm != 'YES':
        print("❌ 操作已取消")
        return
    
    print()
    
    conn = None
    try:
        # 连接数据库
        conn = get_db_connection()
        # 设置自动提交，避免事务问题
        conn.autocommit = True
        cursor = conn.cursor()
        
        # 步骤1: 检查外键约束
        issues = check_foreign_key_constraints(cursor)
        
        # 步骤2: 解除外键约束（如果有）
        if issues:
            if not remove_foreign_key_constraints(cursor, issues):
                print("❌ 解除外键约束失败，操作已取消")
                return
        
        # 步骤3: 删除客户数据
        if delete_customer_data(cursor):
            print()
            print("=" * 70)
            print("✅ 删除完成")
            print("=" * 70)
        else:
            print()
            print("=" * 70)
            print("❌ 删除失败")
            print("=" * 70)
        
    except Exception as e:
        print()
        print("=" * 70)
        print(f"❌ 操作失败: {e}")
        print("=" * 70)
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    main()

