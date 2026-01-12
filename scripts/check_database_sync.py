#!/usr/bin/env python
"""
检查数据库连接配置，确保所有电脑连接到同一个数据库
用于验证多台电脑的会话记录是否同步
"""
import os
import sys
import django
from pathlib import Path
from django.db import connection
from django.utils import timezone

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.config.settings')
django.setup()

from backend.apps.workflow_engine.models import AgentConversation, AgentMessage

def get_database_info():
    """获取当前数据库连接信息"""
    db_info = connection.settings_dict
    
    return {
        'host': db_info.get('HOST', '未知'),
        'port': db_info.get('PORT', '未知'),
        'name': db_info.get('NAME', '未知'),
        'user': db_info.get('USER', '未知'),
        'engine': db_info.get('ENGINE', '未知'),
    }

def check_database_connection():
    """检查数据库连接并显示信息"""
    print("=" * 70)
    print("数据库连接配置检查")
    print("=" * 70)
    
    db_info = get_database_info()
    
    print(f"\n当前数据库连接信息:")
    print(f"  主机 (Host): {db_info['host']}")
    print(f"  端口 (Port): {db_info['port']}")
    print(f"  数据库名 (Database): {db_info['name']}")
    print(f"  用户名 (User): {db_info['user']}")
    print(f"  引擎 (Engine): {db_info['engine']}")
    
    # 生成连接字符串（隐藏密码）
    connection_string = f"postgresql://{db_info['user']}:***@{db_info['host']}:{db_info['port']}/{db_info['name']}"
    print(f"\n连接字符串 (隐藏密码):")
    print(f"  {connection_string}")
    
    # 检查环境变量
    database_url = os.getenv('DATABASE_URL', '')
    if database_url:
        # 隐藏密码
        if '@' in database_url:
            parts = database_url.split('@')
            if '://' in parts[0]:
                protocol_user_pass = parts[0]
                if ':' in protocol_user_pass.split('://')[1]:
                    protocol = protocol_user_pass.split('://')[0]
                    user_pass = protocol_user_pass.split('://')[1]
                    user = user_pass.split(':')[0]
                    hidden_url = f"{protocol}://{user}:***@{parts[1]}"
                    print(f"\n环境变量 DATABASE_URL (隐藏密码):")
                    print(f"  {hidden_url}")
    else:
        print(f"\n环境变量 DATABASE_URL: 未设置 (使用默认配置)")
    
    # 测试连接
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        print(f"\n✅ 数据库连接成功")
        print(f"  PostgreSQL版本: {version.split(',')[0]}")
    except Exception as e:
        print(f"\n❌ 数据库连接失败: {e}")
        return False
    
    # 检查会话数据
    print(f"\n会话数据统计:")
    try:
        conv_count = AgentConversation.objects.count()
        msg_count = AgentMessage.objects.count()
        
        print(f"  会话记录数: {conv_count}")
        print(f"  消息记录数: {msg_count}")
        
        if conv_count > 0:
            latest_conv = AgentConversation.objects.order_by('-created_time').first()
            if latest_conv:
                print(f"  最新会话: ID={latest_conv.id}, 标题={latest_conv.title[:30]}, "
                      f"时间={latest_conv.created_time}")
    except Exception as e:
        print(f"  ⚠️  查询会话数据失败: {e}")
    
    return True

def generate_config_instructions():
    """生成配置说明"""
    db_info = get_database_info()
    
    print("\n" + "=" * 70)
    print("确保所有电脑同步的配置方法")
    print("=" * 70)
    
    print(f"\n方法1: 使用环境变量 (推荐)")
    print(f"  在所有电脑上设置相同的 DATABASE_URL 环境变量:")
    print(f"  ")
    print(f"  export DATABASE_URL='postgresql://{db_info['user']}:密码@{db_info['host']}:{db_info['port']}/{db_info['name']}'")
    print(f"  ")
    print(f"  或者在 ~/.bashrc 或 ~/.zshrc 中添加:")
    print(f"  echo \"export DATABASE_URL='postgresql://{db_info['user']}:密码@{db_info['host']}:{db_info['port']}/{db_info['name']}'\" >> ~/.bashrc")
    print(f"  source ~/.bashrc")
    
    print(f"\n方法2: 使用 .env 文件")
    print(f"  在项目根目录创建 .env 文件，添加:")
    print(f"  DATABASE_URL=postgresql://{db_info['user']}:密码@{db_info['host']}:{db_info['port']}/{db_info['name']}")
    
    print(f"\n方法3: 修改 settings.py (不推荐，仅用于开发)")
    print(f"  在 backend/config/settings.py 中修改 DEVELOPMENT_DATABASE_URL")
    
    print(f"\n验证方法:")
    print(f"  在每台电脑上运行此脚本:")
    print(f"  python scripts/check_database_sync.py")
    print(f"  ")
    print(f"  确保所有电脑显示的连接信息完全一致:")
    print(f"    - 主机 (Host) 必须相同")
    print(f"    - 端口 (Port) 必须相同")
    print(f"    - 数据库名 (Database) 必须相同")
    
    print(f"\n同步验证:")
    print(f"  1. 在电脑A上创建一个测试会话")
    print(f"  2. 在电脑B、C、D上运行检查脚本，应该能看到相同的会话记录数")
    print(f"  3. 如果记录数不一致，说明连接的不是同一个数据库")

if __name__ == '__main__':
    if check_database_connection():
        generate_config_instructions()
    
    print("\n" + "=" * 70)

