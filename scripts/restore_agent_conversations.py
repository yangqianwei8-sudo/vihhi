#!/usr/bin/env python
"""
Agent对话数据恢复脚本
从备份JSON文件恢复Agent对话和消息数据
"""
import os
import sys
import json
import django
from pathlib import Path
from datetime import datetime

# 设置Django环境
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.config.settings')
django.setup()

from backend.apps.workflow_engine.models import AgentConversation, AgentMessage
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.utils.dateparse import parse_datetime

User = get_user_model()

# 备份目录
BACKUP_DIR = Path(__file__).resolve().parent.parent / 'backups' / 'agent_conversations'


def list_backups():
    """列出所有可用的备份文件"""
    backups = sorted(BACKUP_DIR.glob('agent_conversations_*.json'), reverse=True)
    return backups


def restore_agent_conversations(backup_file_path, dry_run=False):
    """从备份文件恢复Agent对话数据"""
    backup_file = Path(backup_file_path)
    
    if not backup_file.exists():
        print(f"❌ 备份文件不存在: {backup_file}")
        return False
    
    print(f"开始恢复Agent对话数据...")
    print(f"备份文件: {backup_file}")
    print(f"模式: {'干运行（仅预览）' if dry_run else '实际恢复'}")
    
    try:
        # 读取备份文件
        with open(backup_file, 'r', encoding='utf-8') as f:
            backup_data = json.load(f)
        
        print(f"\n备份信息:")
        print(f"  备份时间: {backup_data.get('backup_time', '未知')}")
        print(f"  对话数量: {backup_data.get('total_conversations', 0)}")
        
        if dry_run:
            print(f"\n干运行模式 - 将恢复以下数据:")
            for conv_data in backup_data.get('conversations', [])[:5]:  # 只显示前5个
                print(f"  - {conv_data.get('title', '无标题')} (用户: {conv_data.get('user_username')}, 消息数: {len(conv_data.get('messages', []))})")
            if len(backup_data.get('conversations', [])) > 5:
                print(f"  ... 还有 {len(backup_data.get('conversations', [])) - 5} 个对话")
            print(f"\n要实际执行恢复，请使用: python {sys.argv[0]} {backup_file} --execute")
            return True
        
        # 实际恢复
        restored_count = 0
        error_count = 0
        
        for conv_data in backup_data.get('conversations', []):
            try:
                # 获取或创建用户
                user_id = conv_data.get('user_id')
                user_username = conv_data.get('user_username')
                try:
                    user = User.objects.get(id=user_id)
                except User.DoesNotExist:
                    print(f"⚠️  警告: 用户 {user_username} (ID: {user_id}) 不存在，跳过对话: {conv_data.get('title')}")
                    error_count += 1
                    continue
                
                # 检查对话是否已存在
                existing_conv = AgentConversation.objects.filter(id=conv_data.get('id')).first()
                if existing_conv:
                    print(f"⚠️  对话 ID {conv_data.get('id')} 已存在，跳过: {conv_data.get('title')}")
                    continue
                
                # 创建对话（不使用原始ID，让Django自动分配）
                conv = AgentConversation.objects.create(
                    title=conv_data.get('title', ''),
                    description=conv_data.get('description', ''),
                    user=user,
                    metadata=conv_data.get('metadata', {}),
                    is_active=conv_data.get('is_active', True),
                    is_archived=conv_data.get('is_archived', False),
                    created_time=parse_datetime(conv_data.get('created_time')) if conv_data.get('created_time') else timezone.now(),
                    last_message_time=parse_datetime(conv_data.get('last_message_time')) if conv_data.get('last_message_time') else None,
                )
                
                # 恢复消息
                for msg_data in conv_data.get('messages', []):
                    AgentMessage.objects.create(
                        conversation=conv,
                        role=msg_data.get('role', 'user'),
                        content=msg_data.get('content', ''),
                        metadata=msg_data.get('metadata', {}),
                        sequence=msg_data.get('sequence', 0),
                        created_time=parse_datetime(msg_data.get('created_time')) if msg_data.get('created_time') else timezone.now(),
                    )
                
                restored_count += 1
                
            except Exception as e:
                print(f"❌ 恢复对话失败 {conv_data.get('title', '未知')}: {e}")
                error_count += 1
                continue
        
        print(f"\n✅ 恢复完成!")
        print(f"   成功恢复: {restored_count} 个对话")
        if error_count > 0:
            print(f"   失败: {error_count} 个对话")
        
        return True
        
    except Exception as e:
        print(f"❌ 恢复失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("用法:")
        print(f"  列出备份: python {sys.argv[0]} --list")
        print(f"  预览恢复: python {sys.argv[0]} <备份文件路径>")
        print(f"  执行恢复: python {sys.argv[0]} <备份文件路径> --execute")
        print("\n可用备份:")
        backups = list_backups()
        for i, backup in enumerate(backups[:10], 1):
            size = backup.stat().st_size / 1024
            mtime = datetime.fromtimestamp(backup.stat().st_mtime)
            print(f"  {i}. {backup.name} ({size:.1f} KB, {mtime.strftime('%Y-%m-%d %H:%M:%S')})")
        sys.exit(1)
    
    if sys.argv[1] == '--list':
        backups = list_backups()
        print(f"找到 {len(backups)} 个备份文件:\n")
        for backup in backups:
            size = backup.stat().st_size / 1024
            mtime = datetime.fromtimestamp(backup.stat().st_mtime)
            print(f"  {backup.name} ({size:.1f} KB, {mtime.strftime('%Y-%m-%d %H:%M:%S')})")
    else:
        backup_file = sys.argv[1]
        dry_run = '--execute' not in sys.argv
        restore_agent_conversations(backup_file, dry_run=dry_run)

