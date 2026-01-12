#!/usr/bin/env python
"""
会话记录同步验证脚本
用于验证多台电脑的会话记录是否同步
"""
import os
import sys
import django
from pathlib import Path
from datetime import datetime, timedelta
from django.db import connection
from django.utils import timezone

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.config.settings')
django.setup()

from backend.apps.workflow_engine.models import AgentConversation, AgentMessage

def get_sync_status():
    """获取同步状态信息"""
    db_info = connection.settings_dict
    
    print("=" * 70)
    print("会话记录同步状态检查")
    print("=" * 70)
    
    print(f"\n数据库连接信息:")
    print(f"  主机: {db_info.get('HOST', '未知')}")
    print(f"  端口: {db_info.get('PORT', '未知')}")
    print(f"  数据库: {db_info.get('NAME', '未知')}")
    
    # 获取统计数据
    total_conversations = AgentConversation.objects.count()
    total_messages = AgentMessage.objects.count()
    
    print(f"\n当前数据统计:")
    print(f"  总会话数: {total_conversations}")
    print(f"  总消息数: {total_messages}")
    
    if total_conversations == 0:
        print(f"\n⚠️  当前没有会话记录")
        print(f"  这是正常的，如果这是第一台检查的电脑")
        return
    
    # 按用户统计
    from django.db.models import Count
    user_stats = AgentConversation.objects.values('user__username').annotate(
        count=Count('id')
    ).order_by('-count')
    
    print(f"\n按用户统计:")
    for stat in user_stats[:10]:
        print(f"  {stat['user__username']}: {stat['count']} 个会话")
    
    # 按日期统计（最近7天）
    now = timezone.now()
    seven_days_ago = now - timedelta(days=7)
    
    from django.db.models import Count
    from django.db.models.functions import TruncDate
    
    date_stats = AgentConversation.objects.filter(
        created_time__gte=seven_days_ago
    ).annotate(
        date=TruncDate('created_time')
    ).values('date').annotate(
        count=Count('id')
    ).order_by('-date')
    
    print(f"\n最近7天按日期统计:")
    for stat in date_stats:
        print(f"  {stat['date']}: {stat['count']} 个会话")
    
    # 最新会话
    latest_conversations = AgentConversation.objects.select_related('user').order_by('-created_time')[:5]
    
    print(f"\n最新5个会话:")
    for conv in latest_conversations:
        msg_count = conv.messages.count()
        print(f"  ID: {conv.id}, 标题: {conv.title[:40]}, "
              f"用户: {conv.user.username}, "
              f"时间: {conv.created_time.strftime('%Y-%m-%d %H:%M:%S')}, "
              f"消息数: {msg_count}")
    
    # 生成唯一标识
    print(f"\n数据库唯一标识 (用于对比):")
    print(f"  主机+端口+数据库: {db_info.get('HOST')}:{db_info.get('PORT')}/{db_info.get('NAME')}")
    print(f"  总会话数: {total_conversations}")
    print(f"  总消息数: {total_messages}")
    
    if latest_conversations:
        latest_id = latest_conversations[0].id
        latest_time = latest_conversations[0].created_time
        print(f"  最新会话ID: {latest_id}")
        print(f"  最新会话时间: {latest_time.isoformat()}")
    
    print(f"\n验证步骤:")
    print(f"  1. 在每台电脑上运行此脚本")
    print(f"  2. 对比'数据库唯一标识'部分")
    print(f"  3. 如果'主机+端口+数据库'相同，说明连接的是同一个数据库")
    print(f"  4. 如果'总会话数'和'总消息数'相同，说明数据已同步")
    print(f"  5. 如果数字不同，可能是:")
    print(f"     - 连接了不同的数据库")
    print(f"     - 数据还未同步（需要等待几秒）")
    print(f"     - 有新的会话正在创建")

if __name__ == '__main__':
    get_sync_status()
    print("\n" + "=" * 70)

