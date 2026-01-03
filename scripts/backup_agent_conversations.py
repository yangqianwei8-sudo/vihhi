#!/usr/bin/env python
"""
Agent对话数据备份脚本
定期备份Agent对话和消息数据到本地JSON文件
"""
import os
import sys
import json
import django
from datetime import datetime
from pathlib import Path

# 设置Django环境
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.config.settings')
django.setup()

from backend.apps.workflow_engine.models import AgentConversation, AgentMessage
from django.contrib.auth import get_user_model

User = get_user_model()

# 备份目录
BACKUP_DIR = Path(__file__).resolve().parent.parent / 'backups' / 'agent_conversations'
BACKUP_DIR.mkdir(parents=True, exist_ok=True)


def backup_agent_conversations():
    """备份所有Agent对话数据"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = BACKUP_DIR / f'agent_conversations_{timestamp}.json'
    
    print(f"开始备份Agent对话数据...")
    print(f"备份文件: {backup_file}")
    
    try:
        # 获取所有对话
        conversations = AgentConversation.objects.select_related('user').prefetch_related('messages').all()
        
        backup_data = {
            'backup_time': datetime.now().isoformat(),
            'total_conversations': conversations.count(),
            'conversations': []
        }
        
        for conv in conversations:
            # 获取对话的所有消息
            messages = conv.messages.all().order_by('sequence', 'created_time')
            
            conversation_data = {
                'id': conv.id,
                'title': conv.title,
                'description': conv.description,
                'user_id': conv.user.id,
                'user_username': conv.user.username,
                'metadata': conv.metadata,
                'is_active': conv.is_active,
                'is_archived': conv.is_archived,
                'created_time': conv.created_time.isoformat() if conv.created_time else None,
                'updated_time': conv.updated_time.isoformat() if conv.updated_time else None,
                'last_message_time': conv.last_message_time.isoformat() if conv.last_message_time else None,
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
            
            backup_data['conversations'].append(conversation_data)
        
        # 保存到JSON文件
        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump(backup_data, f, ensure_ascii=False, indent=2)
        
        file_size = backup_file.stat().st_size / 1024  # KB
        print(f"✅ 备份完成!")
        print(f"   对话数量: {backup_data['total_conversations']}")
        print(f"   文件大小: {file_size:.2f} KB")
        print(f"   备份文件: {backup_file}")
        
        # 清理旧备份（保留最近30天的备份）
        cleanup_old_backups()
        
        return backup_file
        
    except Exception as e:
        print(f"❌ 备份失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def cleanup_old_backups(days=30):
    """清理30天前的备份文件"""
    from datetime import timedelta
    cutoff_date = datetime.now() - timedelta(days=days)
    
    deleted_count = 0
    for backup_file in BACKUP_DIR.glob('agent_conversations_*.json'):
        try:
            file_time = datetime.fromtimestamp(backup_file.stat().st_mtime)
            if file_time < cutoff_date:
                backup_file.unlink()
                deleted_count += 1
        except Exception as e:
            print(f"警告: 删除旧备份文件失败 {backup_file}: {e}")
    
    if deleted_count > 0:
        print(f"清理了 {deleted_count} 个旧备份文件（30天前）")


if __name__ == '__main__':
    backup_agent_conversations()

