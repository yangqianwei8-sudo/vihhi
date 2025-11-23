# GitHub自动同步说明

## 功能说明

自动同步脚本可以帮你实时或定时从GitHub拉取最新代码，支持三种模式：

1. **定时任务模式**：使用Cron每5分钟自动同步
2. **监控模式**：后台进程实时监控，每30秒检查一次
3. **手动模式**：需要时手动执行

## 快速开始

### 方式一：使用安装脚本（推荐）

```bash
cd /home/devbox/project/vihhi/weihai_tech_production_system
./setup_auto_sync.sh
```

然后根据提示选择同步方式。

### 方式二：手动使用

#### 1. 执行一次同步
```bash
./auto_sync.sh once
```

#### 2. 启动监控模式（每30秒检查）
```bash
./auto_sync.sh watch
```

#### 3. 自定义间隔（例如每60秒）
```bash
./auto_sync.sh interval 60
```

## 定时任务模式（Cron）

设置每5分钟自动同步：

```bash
# 编辑crontab
crontab -e

# 添加以下行
*/5 * * * * cd /home/devbox/project/vihhi/weihai_tech_production_system && ./auto_sync.sh once >> /tmp/git_auto_sync_cron.log 2>&1
```

查看定时任务：
```bash
crontab -l
```

查看日志：
```bash
tail -f /tmp/git_auto_sync_cron.log
```

## 监控模式

启动后台监控：
```bash
nohup ./auto_sync.sh watch > /tmp/git_auto_sync_watch.log 2>&1 &
```

查看日志：
```bash
tail -f /tmp/git_auto_sync.log
```

停止监控：
```bash
# 查找进程
ps aux | grep auto_sync.sh

# 停止进程
kill <PID>
```

## 日志文件

- 同步日志：`/tmp/git_auto_sync.log`
- Cron日志：`/tmp/git_auto_sync_cron.log`
- 监控日志：`/tmp/git_auto_sync_watch.log`

## 注意事项

1. **本地未提交的更改**：脚本会自动暂存（stash）本地更改，同步后尝试恢复
2. **冲突处理**：如果恢复时出现冲突，需要手动解决
3. **数据库迁移**：检测到迁移文件时会提示运行 `python manage.py migrate`
4. **权限**：确保脚本有执行权限：`chmod +x auto_sync.sh`

## 高级功能

### 使用GitHub Webhook（需要服务器配置）

如果你有服务器访问权限，可以设置GitHub Webhook实现真正的实时同步：

1. 在GitHub仓库设置中添加Webhook
2. 配置Webhook URL指向你的服务器
3. 服务器接收Webhook后触发同步脚本

### 集成到启动脚本

可以在 `start_services.sh` 中添加自动同步：

```bash
# 在启动服务前同步代码
cd "$PROJECT_DIR"
./auto_sync.sh once
```

## 故障排查

1. **同步失败**：查看日志文件 `/tmp/git_auto_sync.log`
2. **权限问题**：确保Git配置正确，SSH密钥已设置
3. **网络问题**：检查是否能访问GitHub

## 停止自动同步

### 停止Cron任务
```bash
crontab -e
# 删除相关行
```

### 停止监控进程
```bash
pkill -f "auto_sync.sh watch"
```

