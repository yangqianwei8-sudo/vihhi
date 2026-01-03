# 数据备份说明

本目录包含数据库和Agent对话数据的备份文件。

## 备份类型

### 1. Agent对话数据备份 (`agent_conversations/`)
- **格式**: JSON文件
- **文件名**: `agent_conversations_YYYYMMDD_HHMMSS.json`
- **内容**: 包含所有Agent对话会话和消息数据
- **自动备份**: 每天凌晨2:00（如果已设置定时任务）
- **保留时间**: 30天

### 2. 数据库完整备份 (`database_dumps/`)
- **格式**: SQL文件（压缩为.gz）
- **文件名**: `postgres_数据库名_YYYYMMDD_HHMMSS.sql.gz`
- **内容**: PostgreSQL数据库完整备份
- **自动备份**: 每天凌晨3:00（如果已设置定时任务）
- **保留时间**: 30天

## 使用方法

### 手动备份

#### Agent对话数据备份
```bash
cd /home/devbox/project/vihhi/weihai_tech_production_system
python scripts/backup_agent_conversations.py
```

#### 数据库完整备份
```bash
cd /home/devbox/project/vihhi/weihai_tech_production_system
bash scripts/backup_database.sh
```

### 恢复数据

#### 恢复Agent对话数据
```bash
# 列出所有备份
python scripts/restore_agent_conversations.py --list

# 预览恢复（不实际执行）
python scripts/restore_agent_conversations.py backups/agent_conversations/agent_conversations_20260102_020000.json

# 实际执行恢复
python scripts/restore_agent_conversations.py backups/agent_conversations/agent_conversations_20260102_020000.json --execute
```

#### 恢复数据库完整备份
```bash
# 解压备份文件
gunzip backups/database_dumps/postgres_postgres_20260102_030000.sql.gz

# 恢复数据库（需要数据库连接信息）
export PGPASSWORD="your_password"
psql -h dbconn.sealosbja.site -p 38013 -U postgres -d postgres < backups/database_dumps/postgres_postgres_20260102_030000.sql
```

## 设置自动备份

运行以下命令设置自动备份定时任务：

```bash
cd /home/devbox/project/vihhi/weihai_tech_production_system
bash scripts/setup_backup_cron.sh
```

这将设置：
- Agent对话数据备份：每天 02:00
- 数据库完整备份：每天 03:00

## 备份文件结构

```
backups/
├── README.md                          # 本文件
├── agent_conversations/              # Agent对话备份
│   ├── agent_conversations_20260102_020000.json
│   ├── agent_conversations_20260103_020000.json
│   └── backup.log                    # 备份日志
└── database_dumps/                    # 数据库完整备份
    ├── postgres_postgres_20260102_030000.sql.gz
    ├── postgres_postgres_20260103_030000.sql.gz
    └── backup.log                    # 备份日志
```

## 注意事项

1. **备份位置**: 备份文件存储在本地服务器，不会自动同步到其他位置
2. **存储空间**: 定期检查备份目录大小，确保有足够的磁盘空间
3. **安全性**: 备份文件包含敏感数据，请妥善保管
4. **测试恢复**: 定期测试备份文件的恢复功能，确保备份可用
5. **云端备份**: Sealos平台已有自动备份功能，建议同时使用

## 备份策略建议

1. **本地备份**（本脚本）: 快速恢复，保留最近30天
2. **云端备份**（Sealos）: 长期保留，灾难恢复
3. **定期验证**: 每月测试一次备份恢复功能

