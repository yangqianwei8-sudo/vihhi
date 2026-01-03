# Sealos 重新部署指南

## 🎯 重新部署步骤

### 步骤1：删除现有应用

1. 登录 Sealos 控制台
2. 进入"应用管理"或"工作负载"
3. 找到 `backend` 应用
4. 点击"删除"或"卸载"
5. 确认删除（注意：这会删除应用，但通常不会删除数据）

### 步骤2：创建新应用

#### 2.1 选择部署方式

- 点击"新建应用"或"+ 新建应用"
- 选择"镜像部署"或"从镜像部署"

#### 2.2 基础配置

```
应用名称：backend
命名空间：选择您的命名空间
镜像源：公共（Docker Hub）
镜像名称：yqwlhl/backend:latest
```

#### 2.3 资源配置

```
CPU：1-2 Core（推荐 2 Core，ODA File Converter 需要资源）
内存：2-4 GiB（推荐 4 GiB）
实例数：1
```

#### 2.4 网络配置

```
端口：8000
协议：HTTP
服务类型：ClusterIP 或 NodePort（根据需求）
```

#### 2.5 环境变量（重要）

必须配置的环境变量：

```bash
# 数据库连接（必须）
DATABASE_URL=postgresql://postgres:密码@dbconn.sealosbja.site:38013/postgres

# Django 设置
DEBUG=False
SECRET_KEY=您的密钥

# 其他必要的环境变量
ALLOWED_HOSTS=您的域名,sealos域名
```

#### 2.6 存储配置（可选）

如果需要持久化存储：

```
存储类型：PVC（Persistent Volume Claim）
挂载路径：/app/media（用于文件上传）
```

### 步骤3：启动应用

1. 检查所有配置
2. 点击"创建"或"部署"
3. 等待应用启动（约 1-2 分钟）

### 步骤4：验证部署

#### 4.1 检查应用状态

- 应用状态应该是 "Running"
- Pod 状态应该是 "Running"
- 检查日志是否有错误

#### 4.2 运行诊断脚本

进入容器终端，运行：

```bash
bash /app/deployment/docker/diagnose_parsing.sh
```

#### 4.3 测试功能

1. 访问应用 URL
2. 测试登录功能
3. 测试 CAD 文件上传和解析
4. 检查进度显示是否正常

## ⚠️ 注意事项

### 数据备份

在删除应用前，确保：

1. **数据库数据**：
   - 通常不会丢失（使用外部数据库）
   - 但建议备份重要数据

2. **上传的文件**：
   - 如果使用持久化存储，文件不会丢失
   - 如果使用临时存储，需要备份

3. **应用配置**：
   - 记录所有环境变量
   - 记录资源限制
   - 记录网络配置

### 常见问题

1. **应用无法启动**：
   - 检查镜像是否正确：`yqwlhl/backend:latest`
   - 检查环境变量是否正确
   - 查看容器日志

2. **数据库连接失败**：
   - 检查 `DATABASE_URL` 环境变量
   - 确认数据库服务可访问
   - 检查网络连接

3. **解析功能不工作**：
   - 运行诊断脚本检查
   - 检查 ODA File Converter 是否安装
   - 查看容器日志

## 📋 快速检查清单

- [ ] 已备份重要数据
- [ ] 已记录当前配置
- [ ] 已删除旧应用
- [ ] 已创建新应用
- [ ] 已配置环境变量
- [ ] 已配置资源限制
- [ ] 应用状态为 Running
- [ ] 诊断脚本运行正常
- [ ] 功能测试通过

## 🔗 相关链接

- Docker Hub 镜像：https://hub.docker.com/r/yqwlhl/backend
- GitHub Actions：https://github.com/yangqianwei8-sudo/vihhi/actions
- 诊断脚本：`/app/deployment/docker/diagnose_parsing.sh`

