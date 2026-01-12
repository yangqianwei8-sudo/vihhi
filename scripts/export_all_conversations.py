#!/usr/bin/env python
"""
导出所有Agent对话数据（不限制日期）
用于查看数据库中所有会话记录
"""
import os
import sys
import json
import django
from datetime import datetime
from pathlib import Path
from django.utils import timezone

# 设置Django环境
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.config.settings')
django.setup()

from backend.apps.workflow_engine.models import AgentConversation, AgentMessage
from django.contrib.auth import get_user_model
from django.db import connection

User = get_user_model()

# 输出目录
OUTPUT_DIR = Path(__file__).resolve().parent.parent / 'exports' / 'agent_conversations'
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def export_all_conversations():
    """导出所有会话数据"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    print("=" * 60)
    print("导出所有Agent对话数据")
    print("=" * 60)
    
    # 显示数据库连接信息
    db_info = connection.settings_dict
    print(f"\n数据库连接信息:")
    print(f"  引擎: {db_info.get('ENGINE', '未知')}")
    print(f"  数据库: {db_info.get('NAME', '未知')}")
    print(f"  主机: {db_info.get('HOST', '未知')}")
    print(f"  端口: {db_info.get('PORT', '未知')}")
    
    try:
        # 获取所有对话
        conversations = AgentConversation.objects.select_related('user').prefetch_related('messages').all().order_by('-created_time')
        total_count = conversations.count()
        
        print(f"\n找到 {total_count} 个会话")
        
        if total_count == 0:
            print("\n⚠️  数据库中没有会话记录")
            print("   这可能是因为：")
            print("   1. 确实还没有创建任何会话")
            print("   2. 连接的不是同一个数据库")
            print("   3. 数据库连接配置有问题")
            return None
        
        # 按日期统计
        from collections import defaultdict
        date_stats = defaultdict(int)
        
        all_conversations_data = {
            'export_time': datetime.now().isoformat(),
            'database_info': {
                'engine': db_info.get('ENGINE', ''),
                'name': db_info.get('NAME', ''),
                'host': db_info.get('HOST', ''),
                'port': db_info.get('PORT', ''),
            },
            'total_conversations': total_count,
            'conversations': []
        }
        
        for conv in conversations:
            # 统计日期
            conv_date = conv.created_time.date() if conv.created_time else None
            if conv_date:
                date_stats[conv_date.isoformat()] += 1
            
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
        
        # 添加日期统计
        all_conversations_data['date_statistics'] = dict(sorted(date_stats.items(), reverse=True))
        
        # 保存到JSON文件
        output_file = OUTPUT_DIR / f'all_conversations_{timestamp}.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_conversations_data, f, ensure_ascii=False, indent=2)
        
        file_size = output_file.stat().st_size / 1024  # KB
        
        print("\n" + "=" * 60)
        print("✅ 导出完成!")
        print("=" * 60)
        print(f"  总会话数: {total_count}")
        print(f"  文件大小: {file_size:.2f} KB")
        print(f"  输出文件: {output_file}")
        
        if date_stats:
            print(f"\n按日期统计:")
            for date, count in sorted(date_stats.items(), reverse=True)[:10]:
                print(f"  {date}: {count} 个会话")
        
        print("=" * 60)
        
        return output_file
        
    except Exception as e:
        print(f"\n❌ 导出失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def export_summary_table():
    """导出汇总表格（CSV格式）"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    conversations = AgentConversation.objects.select_related('user').prefetch_related('messages').all().order_by('-created_time')
    
    if conversations.count() == 0:
        print("\n⚠️  没有数据可导出")
        return None
    
    # 生成CSV
    csv_file = OUTPUT_DIR / f'all_conversations_summary_{timestamp}.csv'
    
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
    json_file = export_all_conversations()
    
    if json_file:
        # 导出CSV汇总表
        csv_file = export_summary_table()
        print(f"\n📁 所有文件已保存到: {OUTPUT_DIR}")

