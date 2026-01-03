#!/usr/bin/env python
"""
直接使用 SQL 删除生产管理所有项目数据脚本

删除范围：
- 所有项目（production_management_project）
- 所有项目相关的关联数据（会自动级联删除）

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
    
    # 检查客户关联（PROTECT约束）
    try:
        cursor.execute("""
            SELECT COUNT(*) 
            FROM production_management_project 
            WHERE client_id IS NOT NULL
        """)
        client_count = cursor.fetchone()[0]
        if client_count > 0:
            issues.append(('production_management_project', 'client_id', client_count))
            print(f"⚠️  发现 {client_count} 个项目关联了客户（PROTECT约束，需要解除）")
    except Exception as e:
        pass
    
    # 检查用户关联（PROTECT约束）
    try:
        cursor.execute("""
            SELECT COUNT(*) 
            FROM production_management_project 
            WHERE created_by_id IS NOT NULL 
               OR project_manager_id IS NOT NULL 
               OR business_manager_id IS NOT NULL
        """)
        user_count = cursor.fetchone()[0]
        if user_count > 0:
            print(f"ℹ️  发现 {user_count} 个项目关联了用户（PROTECT约束，需要解除）")
            issues.append(('production_management_project', 'user_fields', user_count))
    except Exception as e:
        pass
    
    # 检查其他模块关联到项目的表（SET_NULL，仅提示）
    set_null_tables = [
        ('delivery_customer_deliveryrecord', 'project_id', '交付记录'),
        ('financial_management_receivable', 'project_id', '应收账款'),
        ('financial_management_payable', 'project_id', '应付账款'),
        ('financial_management_fundflow', 'project_id', '资金流水'),
        ('litigation_management_litigationcase', 'project_id', '诉讼案件'),
        ('customer_contact_tracking', 'related_project_id', '客户联系跟踪'),
        ('customer_contact_cooperation', 'project_id', '客户合作记录'),
        ('customer_authorizationletter', 'project_id', '授权委托书'),
    ]
    
    for table_name, column_name, desc in set_null_tables:
        try:
            cursor.execute(f"""
                SELECT COUNT(*) 
                FROM {table_name} 
                WHERE {column_name} IS NOT NULL
            """)
            count = cursor.fetchone()[0]
            if count > 0:
                print(f"ℹ️  发现 {count} 条{desc}关联了项目（SET_NULL，删除后关联会丢失）")
        except Exception as e:
            # 表可能不存在，忽略
            pass
    
    # 检查客户项目管理关联（CASCADE，会级联删除）
    try:
        cursor.execute("""
            SELECT COUNT(*) 
            FROM customer_client_project 
            WHERE project_id IS NOT NULL
        """)
        client_project_count = cursor.fetchone()[0]
        if client_project_count > 0:
            print(f"ℹ️  发现 {client_project_count} 条客户项目关联（CASCADE，会级联删除）")
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
            if column_name == 'user_fields':
                # 解除所有用户字段的关联
                cursor.execute(f"""
                    UPDATE {table_name} 
                    SET created_by_id = NULL,
                        project_manager_id = NULL,
                        business_manager_id = NULL
                    WHERE created_by_id IS NOT NULL 
                       OR project_manager_id IS NOT NULL 
                       OR business_manager_id IS NOT NULL
                """)
                print(f"  ✅ 已解除用户字段关联")
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
    
    # 统计项目相关表的数据量
    tables = [
        ('production_management_project', 'project'),
        ('production_management_flow_log', 'flow_log'),
        ('production_management_team', 'team'),
        ('production_management_team_log', 'team_log'),
        ('production_management_team_notification', 'team_notification'),
        ('production_management_task', 'task'),
        ('production_management_design_reply', 'design_reply'),
        ('production_management_meeting_record', 'meeting_record'),
        ('production_management_meeting_decision', 'meeting_decision'),
        ('production_management_milestone', 'milestone'),
        ('production_management_drawing_submission', 'drawing_submission'),
        ('production_management_drawing_file', 'drawing_file'),
        ('production_management_drawing_review', 'drawing_review'),
        ('production_management_start_notice', 'start_notice'),
        ('production_management_document', 'document'),
        ('production_management_archive', 'archive'),
        ('business_contract', 'business_contract'),
        ('business_payment_plan', 'payment_plan'),
    ]
    
    for table_name, key in tables:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            counts[key] = cursor.fetchone()[0]
        except Exception as e:
            counts[key] = 0
    
    # 统计其他模块关联项目的数量
    other_tables = [
        ('customer_client_project', 'client_project'),
        ('production_quality_opinion', 'opinion'),
        ('production_quality_productionreport', 'production_report'),
        ('production_quality_projectstartup', 'project_startup'),
    ]
    
    for table_name, key in other_tables:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            counts[key] = cursor.fetchone()[0]
        except Exception as e:
            counts[key] = 0
    
    return counts

def delete_project_data(cursor):
    """删除项目数据"""
    print("=" * 70)
    print("删除项目数据")
    print("=" * 70)
    print()
    
    # 获取删除前的数据量
    before_counts = get_data_counts(cursor)
    print("删除前的数据量：")
    print(f"  项目: {before_counts.get('project', 0)} 条")
    print(f"  项目流程日志: {before_counts.get('flow_log', 0)} 条")
    print(f"  项目团队: {before_counts.get('team', 0)} 条")
    print(f"  项目任务: {before_counts.get('task', 0)} 条")
    print(f"  项目里程碑: {before_counts.get('milestone', 0)} 条")
    print(f"  项目文档: {before_counts.get('document', 0)} 条")
    print(f"  商务合同: {before_counts.get('business_contract', 0)} 条")
    print(f"  项目意见: {before_counts.get('opinion', 0)} 条")
    print(f"  生产报告: {before_counts.get('production_report', 0)} 条")
    print()
    
    deleted_counts = {}
    
    # 注意：由于外键级联删除，删除项目会自动删除所有关联数据
    # 但为了明确显示删除过程，我们按顺序删除
    
    # 1. 删除项目相关的关联数据（这些会被级联删除，但先删除可以避免约束问题）
    # 先删除最底层的关联表
    
    # 删除图纸文件（通过提交关联）
    try:
        cursor.execute("""
            DELETE FROM production_management_drawing_file 
            WHERE submission_id IN (
                SELECT id FROM production_management_drawing_submission
            )
        """)
        deleted_counts['drawing_file'] = cursor.rowcount
        if deleted_counts['drawing_file'] > 0:
            print(f"✅ 已删除 {deleted_counts['drawing_file']} 条图纸文件记录")
    except Exception as e:
        print(f"⚠️  删除图纸文件时出错: {e}")
    
    # 删除图纸预审记录
    try:
        cursor.execute("""
            DELETE FROM production_management_drawing_review 
            WHERE submission_id IN (
                SELECT id FROM production_management_drawing_submission
            )
        """)
        deleted_counts['drawing_review'] = cursor.rowcount
        if deleted_counts['drawing_review'] > 0:
            print(f"✅ 已删除 {deleted_counts['drawing_review']} 条图纸预审记录")
    except Exception as e:
        print(f"⚠️  删除图纸预审记录时出错: {e}")
    
    # 删除图纸提交
    try:
        cursor.execute("DELETE FROM production_management_drawing_submission")
        deleted_counts['drawing_submission'] = cursor.rowcount
        if deleted_counts['drawing_submission'] > 0:
            print(f"✅ 已删除 {deleted_counts['drawing_submission']} 条图纸提交记录")
    except Exception as e:
        print(f"⚠️  删除图纸提交时出错: {e}")
    
    # 删除会议决定（通过会议记录关联）
    try:
        cursor.execute("""
            DELETE FROM production_management_meeting_decision 
            WHERE meeting_id IN (
                SELECT id FROM production_management_meeting_record
            )
        """)
        deleted_counts['meeting_decision'] = cursor.rowcount
        if deleted_counts['meeting_decision'] > 0:
            print(f"✅ 已删除 {deleted_counts['meeting_decision']} 条会议决定记录")
    except Exception as e:
        print(f"⚠️  删除会议决定时出错: {e}")
    
    # 删除会议记录
    try:
        cursor.execute("DELETE FROM production_management_meeting_record")
        deleted_counts['meeting_record'] = cursor.rowcount
        if deleted_counts['meeting_record'] > 0:
            print(f"✅ 已删除 {deleted_counts['meeting_record']} 条会议记录")
    except Exception as e:
        print(f"⚠️  删除会议记录时出错: {e}")
    
    # 删除其他级联关联的数据（这些删除项目时会自动删除，但先删除可以更快）
    cascade_tables = [
        ('production_management_flow_log', '项目流程日志'),
        ('production_management_team', '项目团队'),
        ('production_management_team_log', '项目团队变更日志'),
        ('production_management_team_notification', '项目团队通知'),
        ('production_management_task', '项目任务'),
        ('production_management_design_reply', '设计方回复'),
        ('production_management_milestone', '项目里程碑'),
        ('production_management_start_notice', '开工通知'),
        ('production_management_document', '项目文档'),
        ('production_management_archive', '项目归档'),
        ('business_payment_plan', '回款计划'),
        ('business_contract', '商务合同'),
    ]
    
    for table_name, desc in cascade_tables:
        try:
            cursor.execute(f"DELETE FROM {table_name}")
            count = cursor.rowcount
            if count > 0:
                deleted_counts[table_name] = count
                print(f"✅ 已删除 {count} 条{desc}记录")
        except Exception as e:
            print(f"⚠️  删除{desc}时出错: {e}")
    
    # 2. 删除项目（这会级联删除剩余的所有关联数据）
    try:
        cursor.execute("DELETE FROM production_management_project")
        deleted_counts['project'] = cursor.rowcount
        print(f"✅ 已删除 {deleted_counts['project']} 条项目记录")
    except Exception as e:
        print(f"❌ 删除项目失败: {e}")
        return False
    
    # 获取删除后的数据量
    after_counts = get_data_counts(cursor)
    print()
    print("删除后的数据量：")
    print(f"  项目: {after_counts.get('project', 0)} 条")
    print(f"  项目流程日志: {after_counts.get('flow_log', 0)} 条")
    print(f"  项目团队: {after_counts.get('team', 0)} 条")
    print(f"  项目任务: {after_counts.get('task', 0)} 条")
    print(f"  项目里程碑: {after_counts.get('milestone', 0)} 条")
    print(f"  项目文档: {after_counts.get('document', 0)} 条")
    print(f"  商务合同: {after_counts.get('business_contract', 0)} 条")
    print()
    
    # 计算实际删除的数据量
    print("实际删除的数据量：")
    print(f"  项目: {before_counts.get('project', 0) - after_counts.get('project', 0)} 条")
    print(f"  项目流程日志: {before_counts.get('flow_log', 0) - after_counts.get('flow_log', 0)} 条")
    print(f"  项目团队: {before_counts.get('team', 0) - after_counts.get('team', 0)} 条")
    print(f"  项目任务: {before_counts.get('task', 0) - after_counts.get('task', 0)} 条")
    print(f"  项目里程碑: {before_counts.get('milestone', 0) - after_counts.get('milestone', 0)} 条")
    print(f"  项目文档: {before_counts.get('document', 0) - after_counts.get('document', 0)} 条")
    print(f"  商务合同: {before_counts.get('business_contract', 0) - after_counts.get('business_contract', 0)} 条")
    
    return True

def main():
    """主函数"""
    import sys
    
    # 检查是否通过命令行参数跳过确认
    skip_confirm = '--yes' in sys.argv or '-y' in sys.argv
    
    print("=" * 70)
    print("生产管理项目数据删除脚本（SQL版本）")
    print("=" * 70)
    print()
    print("⚠️  警告：此操作将删除所有项目数据及其关联数据！")
    print("   删除范围：")
    print("   - 所有项目")
    print("   - 所有项目相关的关联数据（流程日志、团队、任务、文档等）")
    print("   - 所有商务合同和回款计划")
    print()
    
    # 确认
    if skip_confirm:
        print("⚠️  使用 --yes 参数，跳过确认，直接执行删除...")
        print()
    else:
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
            if not skip_confirm:
                confirm_constraints = input("发现需要解除的约束，是否继续？(y/n): ")
                if confirm_constraints.lower() != 'y':
                    print("❌ 操作已取消")
                    return
            else:
                print("⚠️  自动解除外键约束...")
            
            if not remove_foreign_key_constraints(cursor, issues):
                print("❌ 解除外键约束失败，操作已取消")
                return
        
        # 步骤3: 删除项目数据
        if delete_project_data(cursor):
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

