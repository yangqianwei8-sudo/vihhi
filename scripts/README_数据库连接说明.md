# Agent会话数据导出说明

## 重要说明

**所有会话记录都存储在云端数据库中，不是存储在本地电脑上。**

只要连接到同一个数据库，无论在哪台电脑上，都能看到所有会话记录。

## 数据库连接配置

### 查看当前数据库连接

运行以下命令查看当前连接的数据库：

```bash
cd /home/devbox/project/vihhi/weihai_tech_production_system
python scripts/export_all_conversations.py
```

### 连接到不同的数据库

如果需要连接到外地电脑使用的数据库，可以通过环境变量设置：

```bash
# 设置数据库连接
export DATABASE_URL="postgresql://用户名:密码@主机:端口/数据库名"

# 然后运行导出脚本
python scripts/export_recent_conversations.py
```

### 数据库连接格式

```
postgresql://用户名:密码@主机:端口/数据库名
```

示例：
```
postgresql://postgres:password123@dbconn.sealosbja.site:38013/postgres
```

## 导出脚本说明

### 1. 导出最近两天的会话

```bash
python scripts/export_recent_conversations.py
```

导出昨天和前天的所有会话数据。

### 2. 导出所有会话

```bash
python scripts/export_all_conversations.py
```

导出数据库中所有会话数据，不限制日期。

### 3. 导出文件位置

所有导出的文件保存在：
```
exports/agent_conversations/
```

- JSON文件：包含完整的会话和消息数据
- CSV文件：会话汇总表格

## 常见问题

### Q: 为什么查询不到会话记录？

A: 可能的原因：
1. 连接的不是同一个数据库实例
2. 确实还没有创建会话记录
3. 数据库连接配置错误

**解决方法：**
- 确认外地电脑使用的数据库连接信息
- 使用相同的 DATABASE_URL 环境变量
- 运行 `export_all_conversations.py` 查看所有会话

### Q: 如何确认连接的是正确的数据库？

A: 运行导出脚本时，会显示当前数据库连接信息：
- 数据库主机
- 数据库端口
- 数据库名称

对比这些信息，确认是否与外地电脑使用的数据库一致。

### Q: 会话记录会丢失吗？

A: 不会。会话记录存储在云端数据库中，只要数据库正常，数据就不会丢失。

