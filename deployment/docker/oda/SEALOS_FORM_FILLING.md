# Sealos 应用部署表单填写指南

## ⚠️ 重要：需要选择"从代码构建"

当前页面显示的是"镜像部署"方式，但我们需要"从代码构建"来使用 Dockerfile。

## 🔍 查找"从代码构建"选项

### 方法1：在创建应用时选择

1. **返回应用列表页面**
   - 点击左上角的返回按钮或导航到"应用管理"

2. **点击"+ 新建应用"**

3. **选择构建方式**
   - 查找"从代码构建"、"从 Git 构建"或"代码构建"选项
   - 不要选择"镜像部署"

### 方法2：使用 YAML 模式

如果 Sealos 支持 YAML 配置，可以：

1. **切换到"YAML 文件"标签页**
   - 在左侧导航中点击"YAML 文件"标签

2. **使用以下 YAML 配置**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend
  namespace: default
spec:
  replicas: 1
  selector:
    matchLabels:
      app: backend
  template:
    metadata:
      labels:
        app: backend
    spec:
      containers:
      - name: backend
        image: your-registry/backend:latest  # 需要先构建镜像
        ports:
        - containerPort: 8000
        resources:
          requests:
            cpu: "0.2"
            memory: "256Mi"
          limits:
            cpu: "2"
            memory: "4Gi"
```

**注意**：YAML 方式需要先构建镜像，所以还是推荐使用"从代码构建"。

## 📋 如果找到"从代码构建"选项，填写如下：

### 基础配置

```
应用名称：backend（或您自定义的名称）

代码源：选择您的 Git 仓库
分支：main

构建方式：Dockerfile
Dockerfile 路径：deployment/docker/Dockerfile.backend
构建上下文：/ (项目根目录)
```

### 资源配置

```
CPU：建议 1-2 Core（ODA File Converter 需要一定资源）
内存：建议 2-4 GiB（DEB 包安装需要内存）
```

### 网络配置

```
端口：8000（根据您的应用配置）
```

## 🔄 如果只有"镜像部署"选项

如果 Sealos 平台只提供"镜像部署"方式，您需要：

### 方案A：先构建镜像，再部署

1. **在 Sealos 的"镜像构建"或"构建服务"中**
   - 创建新的构建任务
   - 配置 Git 仓库
   - 设置 Dockerfile 路径：`deployment/docker/Dockerfile.backend`
   - 构建镜像

2. **构建完成后**
   - 在"镜像部署"中使用构建好的镜像
   - 填写镜像名称（如：`your-registry/backend:latest`）

### 方案B：使用外部 CI/CD

1. **使用 GitHub Actions 或其他 CI/CD**
   - 配置自动构建
   - 推送到镜像仓库

2. **在 Sealos 中使用构建好的镜像**

## 🎯 推荐操作步骤

### 步骤1：查找构建选项

在 Sealos 控制台中查找：
- "代码构建"
- "从 Git 构建"
- "构建服务"
- "镜像构建"

### 步骤2：配置构建

如果找到构建选项：

```
代码仓库：选择您的仓库
分支：main
Dockerfile 路径：deployment/docker/Dockerfile.backend
构建上下文：/ (项目根目录)
```

### 步骤3：配置部署

构建完成后，配置部署：

```
应用名称：backend
镜像：使用构建好的镜像
端口：8000
CPU：1-2 Core
内存：2-4 GiB
```

## 💡 提示

不同版本的 Sealos 界面可能不同：

- **新版本**：可能有"从代码构建"选项
- **旧版本**：可能需要先构建镜像，再部署

## 📞 如果找不到"从代码构建"

1. **查看 Sealos 文档**
   - 搜索"代码构建"或"Dockerfile 构建"

2. **联系 Sealos 技术支持**
   - 询问如何从 Git 仓库构建应用

3. **使用构建服务**
   - 查找"构建服务"或"镜像构建"功能
   - 先构建镜像，再部署

---

**关键点**：我们需要使用 Dockerfile 来构建包含 ODA File Converter 的镜像，而不是直接使用现成的镜像。

