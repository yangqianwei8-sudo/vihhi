#!/usr/bin/env python
"""
全面检查Agent对话数据
检查所有可能的日期范围和条件
"""
import os
import sys
import django
from datetime import datetime, timedelta
from pathlib import Path
from django.utils import timezone
from django.db import connection

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.config.settings')
django.setup()

from backend.apps.workflow_engine.models import AgentConversation, AgentMessage

print("=" * 70)
print("全面检查Agent对话数据")
print("=" * 70)

# 显示数据库连接信息
db_info = connection.settings_dict
print(f"\n数据库连接信息:")
print(f"  主机: {db_info.get('HOST', '未知')}")
print(f"  端口: {db_info.get('PORT', '未知')}")
print(f"  数据库: {db_info.get('NAME', '未知')}")
print(f"  用户: {db_info.get('USER', '未知')}")

# 检查表是否存在
cursor = connection.cursor()
cursor.execute("""
    SELECT EXISTS (
        SELECT FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name = 'workflow_agent_conversation'
    )
""")
table_exists = cursor.fetchone()[0]

if not table_exists:
    print("\n❌ 表 workflow_agent_conversation 不存在！")
    sys.exit(1)

print("\n✅ 表 workflow_agent_conversation 存在")

# 检查记录数
cursor.execute("SELECT COUNT(*) FROM workflow_agent_conversation")
total_count = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM workflow_agent_message")
message_count = cursor.fetchone()[0]

print(f"\n数据统计:")
print(f"  会话记录数: {total_count}")
print(f"  消息记录数: {message_count}")

if total_count == 0:
    print("\n⚠️  数据库中没有会话记录")
    print("\n可能的原因:")
    print("  1. 确实还没有在这个系统中创建过会话")
    print("  2. 会话记录被清空或删除了")
    print("  3. 外地电脑使用的是不同的系统或应用")
    print("\n建议:")
    print("  - 确认外地电脑上使用的是同一个系统")
    print("  - 检查是否有其他数据库实例")
    print("  - 确认会话功能是否已启用")
else:
    # 查询所有会话的基本信息
    print(f"\n所有会话列表:")
    cursor.execute("""
        SELECT id, title, created_time, user_id, is_active, is_archived
        FROM workflow_agent_conversation
        ORDER BY created_time DESC
        LIMIT 20
    """)
    rows = cursor.fetchall()
    
    for row in rows:
        print(f"  ID: {row[0]}, 标题: {row[1][:40] if row[1] else '无'}, "
              f"创建时间: {row[2]}, 用户ID: {row[3]}, "
              f"活跃: {row[4]}, 归档: {row[5]}")
    
    # 按日期统计
    print(f"\n按日期统计（最近30天）:")
    cursor.execute("""
        SELECT DATE(created_time) as date, COUNT(*) as count
        FROM workflow_agent_conversation
        WHERE created_time >= NOW() - INTERVAL '30 days'
        GROUP BY DATE(created_time)
        ORDER BY date DESC
    """)
    date_stats = cursor.fetchall()
    
    if date_stats:
        for stat in date_stats:
            print(f"  {stat[0]}: {stat[1]} 个会话")
    else:
        print("  最近30天没有会话记录")
    
    # 查询昨天和前天的会话
    now = timezone.now()
    yesterday_start = (now - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    day_before_yesterday_start = (now - timedelta(days=2)).replace(hour=0, minute=0, second=0, microsecond=0)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    
    print(f"\n昨天和前天的会话:")
    print(f"  查询范围: {day_before_yesterday_start} 至 {today_start}")
    
    cursor.execute("""
        SELECT id, title, created_time, user_id
        FROM workflow_agent_conversation
        WHERE created_time >= %s AND created_time < %s
        ORDER BY created_time DESC
    """, [day_before_yesterday_start, today_start])
    
    recent_rows = cursor.fetchall()
    if recent_rows:
        print(f"  找到 {len(recent_rows)} 个会话:")
        for row in recent_rows:
            print(f"    ID: {row[0]}, 标题: {row[1][:40] if row[1] else '无'}, "
                  f"时间: {row[2]}, 用户ID: {row[3]}")
    else:
        print("  没有找到会话记录")

print("\n" + "=" * 70)

