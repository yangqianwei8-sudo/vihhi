#!/usr/bin/env python
"""
导出最近两天的Agent对话数据
拉取昨天和前天的所有会话表数据

使用方法:
1. 使用默认数据库连接:
   python scripts/export_recent_conversations.py

2. 指定数据库连接（通过环境变量）:
   export DATABASE_URL="postgresql://用户名:密码@主机:端口/数据库名"
   python scripts/export_recent_conversations.py
"""
import os
import sys
import json
import django
from datetime import datetime, timedelta
from pathlib import Path
from django.utils import timezone
from django.db.models import Q

# 设置Django环境
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.config.settings')
django.setup()

# 显示当前数据库连接信息
from django.db import connection

from backend.apps.workflow_engine.models import AgentConversation, AgentMessage
from django.contrib.auth import get_user_model

User = get_user_model()

# 输出目录
OUTPUT_DIR = Path(__file__).resolve().parent.parent / 'exports' / 'agent_conversations'
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def get_date_range():
    """获取昨天和前天的日期范围"""
    # 获取当前时间（使用Django时区）
    now = timezone.now()
    
    # 昨天：从昨天00:00:00到今天00:00:00
    yesterday_start = (now - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    yesterday_end = now.replace(hour=0, minute=0, second=0, microsecond=0)
    
    # 前天：从前天00:00:00到昨天00:00:00
    day_before_yesterday_start = (now - timedelta(days=2)).replace(hour=0, minute=0, second=0, microsecond=0)
    day_before_yesterday_end = yesterday_start
    
    return {
        'yesterday': {
            'start': yesterday_start,
            'end': yesterday_end,
            'label': '昨天'
        },
        'day_before_yesterday': {
            'start': day_before_yesterday_start,
            'end': day_before_yesterday_end,
            'label': '前天'
        }
    }


def export_conversations_by_date_range():
    """导出昨天和前天的所有会话数据"""
    date_ranges = get_date_range()
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # 显示数据库连接信息
    db_info = connection.settings_dict
    
    print("=" * 60)
    print("开始导出最近两天的Agent对话数据")
    print("=" * 60)
    print(f"\n当前数据库连接:")
    print(f"  主机: {db_info.get('HOST', '未知')}")
    print(f"  端口: {db_info.get('PORT', '未知')}")
    print(f"  数据库: {db_info.get('NAME', '未知')}")
    print(f"  用户: {db_info.get('USER', '未知')}")
    print(f"\n💡 提示: 如果这是错误的数据库，请设置 DATABASE_URL 环境变量")
    print(f"   例如: export DATABASE_URL='postgresql://user:pass@host:port/dbname'")
    
    all_conversations_data = {
        'export_time': datetime.now().isoformat(),
        'date_ranges': {},
        'conversations': []
    }
    
    # 查询条件：创建时间在昨天或前天
    yesterday_start = date_ranges['yesterday']['start']
    day_before_yesterday_start = date_ranges['day_before_yesterday']['start']
    today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    
    # 查询在这两天创建的会话
    conversations = AgentConversation.objects.select_related('user').prefetch_related('messages').filter(
        Q(created_time__gte=day_before_yesterday_start) & Q(created_time__lt=today_start)
    ).order_by('-created_time')
    
    print(f"\n查询时间范围:")
    print(f"  前天: {day_before_yesterday_start.strftime('%Y-%m-%d %H:%M:%S')} 至 {yesterday_start.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  昨天: {yesterday_start.strftime('%Y-%m-%d %H:%M:%S')} 至 {today_start.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"\n找到 {conversations.count()} 个会话")
    
    # 统计信息
    yesterday_count = 0
    day_before_yesterday_count = 0
    
    try:
        for conv in conversations:
            # 判断属于哪一天
            conv_date = conv.created_time.date()
            yesterday_date = (timezone.now() - timedelta(days=1)).date()
            day_before_yesterday_date = (timezone.now() - timedelta(days=2)).date()
            
            if conv_date == yesterday_date:
                day_label = '昨天'
                yesterday_count += 1
            elif conv_date == day_before_yesterday_date:
                day_label = '前天'
                day_before_yesterday_count += 1
            else:
                day_label = '其他'
            
            # 获取对话的所有消息
            messages = conv.messages.all().order_by('sequence', 'created_time')
            
            conversation_data = {
                'id': conv.id,
                'title': conv.title,
                'description': conv.description,
                'user_id': conv.user.id,
                'user_username': conv.user.username,
                'user_full_name': conv.user.get_full_name() if hasattr(conv.user, 'get_full_name') else '',
                'metadata': conv.metadata,
                'is_active': conv.is_active,
                'is_archived': conv.is_archived,
                'created_time': conv.created_time.isoformat() if conv.created_time else None,
                'created_date': conv.created_time.date().isoformat() if conv.created_time else None,
                'day_label': day_label,
                'updated_time': conv.updated_time.isoformat() if conv.updated_time else None,
                'last_message_time': conv.last_message_time.isoformat() if conv.last_message_time else None,
                'message_count': messages.count(),
                'messages': []
            }
            
            for msg in messages:
                message_data = {
                    'id': msg.id,
                    'role': msg.role,
                    'content': msg.content,
                    'metadata': msg.metadata,
                    'sequence': msg.sequence,
                    'created_time': msg.created_time.isoformat() if msg.created_time else None,
                }
                conversation_data['messages'].append(message_data)
            
            all_conversations_data['conversations'].append(conversation_data)
        
        # 添加统计信息
        all_conversations_data['date_ranges'] = {
            'yesterday': {
                'start': date_ranges['yesterday']['start'].isoformat(),
                'end': date_ranges['yesterday']['end'].isoformat(),
                'count': yesterday_count
            },
            'day_before_yesterday': {
                'start': date_ranges['day_before_yesterday']['start'].isoformat(),
                'end': date_ranges['day_before_yesterday']['end'].isoformat(),
                'count': day_before_yesterday_count
            }
        }
        all_conversations_data['total_conversations'] = len(all_conversations_data['conversations'])
        
        # 保存到JSON文件
        output_file = OUTPUT_DIR / f'conversations_yesterday_and_day_before_{timestamp}.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_conversations_data, f, ensure_ascii=False, indent=2)
        
        file_size = output_file.stat().st_size / 1024  # KB
        
        print("\n" + "=" * 60)
        print("✅ 导出完成!")
        print("=" * 60)
        print(f"  总会话数: {all_conversations_data['total_conversations']}")
        print(f"  昨天会话数: {yesterday_count}")
        print(f"  前天会话数: {day_before_yesterday_count}")
        print(f"  文件大小: {file_size:.2f} KB")
        print(f"  输出文件: {output_file}")
        print("=" * 60)
        
        return output_file
        
    except Exception as e:
        print(f"\n❌ 导出失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def export_summary_table():
    """导出汇总表格（CSV格式）"""
    date_ranges = get_date_range()
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # 查询会话
    yesterday_start = date_ranges['yesterday']['start']
    day_before_yesterday_start = date_ranges['day_before_yesterday']['start']
    today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    
    conversations = AgentConversation.objects.select_related('user').prefetch_related('messages').filter(
        Q(created_time__gte=day_before_yesterday_start) & Q(created_time__lt=today_start)
    ).order_by('-created_time')
    
    # 生成CSV
    csv_file = OUTPUT_DIR / f'conversations_summary_{timestamp}.csv'
    
    import csv
    with open(csv_file, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f)
        # 写入表头
        writer.writerow([
            '会话ID', '标题', '用户', '创建日期', '创建时间', 
            '消息数量', '是否活跃', '是否归档', '最后消息时间'
        ])
        
        # 写入数据
        for conv in conversations:
            writer.writerow([
                conv.id,
                conv.title,
                conv.user.username,
                conv.created_time.date().isoformat() if conv.created_time else '',
                conv.created_time.strftime('%Y-%m-%d %H:%M:%S') if conv.created_time else '',
                conv.messages.count(),
                '是' if conv.is_active else '否',
                '是' if conv.is_archived else '否',
                conv.last_message_time.strftime('%Y-%m-%d %H:%M:%S') if conv.last_message_time else ''
            ])
    
    print(f"\n✅ CSV汇总表已生成: {csv_file}")
    return csv_file


if __name__ == '__main__':
    # 导出完整JSON数据
    json_file = export_conversations_by_date_range()
    
    # 导出CSV汇总表
    csv_file = export_summary_table()
    
    print(f"\n📁 所有文件已保存到: {OUTPUT_DIR}")

