# Sealos 镜像部署方案（无代码构建选项）

## 🎯 当前情况

- ✅ 代码已推送到 Git 仓库
- ✅ Dockerfile 已配置完成
- ⚠️  Sealos 只有"镜像部署"选项，没有"从代码构建"

## 📋 解决方案：先构建镜像，再部署

由于 Sealos 不支持直接从代码构建，我们需要：

### 方案1：使用 GitHub Actions 自动构建（推荐）⭐

#### 步骤1：创建 GitHub Actions 工作流

在项目根目录创建 `.github/workflows/build-and-push.yml`：

```yaml
name: Build and Push Docker Image

on:
  push:
    branches: [ main ]
  workflow_dispatch:

jobs:
  build:
    runs-on: ubuntu-latest
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v3
      
    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v2
      
    - name: Login to Docker Hub (或您的镜像仓库)
      uses: docker/login-action@v2
      with:
        username: ${{ secrets.DOCKER_USERNAME }}
        password: ${{ secrets.DOCKER_PASSWORD }}
        
    - name: Build and push
      uses: docker/build-push-action@v4
      with:
        context: .
        file: ./deployment/docker/Dockerfile.backend
        push: true
        tags: |
          your-dockerhub-username/backend:latest
          your-dockerhub-username/backend:${{ github.sha }}
```

#### 步骤2：配置 GitHub Secrets

在 GitHub 仓库设置中添加：
- `DOCKER_USERNAME`: 您的 Docker Hub 用户名
- `DOCKER_PASSWORD`: 您的 Docker Hub 密码或访问令牌

#### 步骤3：触发构建

- 推送到 main 分支会自动触发
- 或手动在 Actions 页面触发

#### 步骤4：在 Sealos 中使用镜像

```
镜像源：公共（如果使用 Docker Hub）
镜像名：your-dockerhub-username/backend:latest
```

---

### 方案2：使用 Sealos DevBox 构建（如果可用）

#### 步骤1：在 Sealos DevBox 中构建

1. 进入 Sealos DevBox（您当前使用的开发环境）
2. 克隆代码仓库
3. 构建镜像：

```bash
cd /path/to/project
docker build -f deployment/docker/Dockerfile.backend -t your-registry/backend:latest .
```

4. 推送到镜像仓库：

```bash
# 登录到 Sealos 的镜像仓库
docker login hub.sealos.run

# 标记镜像
docker tag your-registry/backend:latest hub.sealos.run/your-namespace/backend:latest

# 推送镜像
docker push hub.sealos.run/your-namespace/backend:latest
```

#### 步骤2：在 Sealos 应用管理中部署

```
镜像源：私有
镜像仓库地址：hub.sealos.run
用户名：您的 Sealos 用户名
密码：您的 Sealos 密码
镜像名：your-namespace/backend:latest
```

---

### 方案3：本地构建后推送

#### 步骤1：在本地或服务器构建

```bash
# 克隆代码
git clone <your-repo-url>
cd weihai_tech_production_system

# 构建镜像
docker build -f deployment/docker/Dockerfile.backend -t backend:latest .

# 标记镜像（替换为您的镜像仓库）
docker tag backend:latest your-registry/backend:latest

# 登录镜像仓库
docker login your-registry.com

# 推送镜像
docker push your-registry/backend:latest
```

#### 步骤2：在 Sealos 中部署

使用推送的镜像名称部署。

---

## 📝 在 Sealos 中填写部署表单

### 基础配置

```
应用名称：backend

镜像源：公共（Docker Hub）或 私有（其他仓库）

镜像名：your-registry/backend:latest

如果是私有仓库：
  用户名：您的镜像仓库用户名
  密码：您的镜像仓库密码
  镜像仓库地址：registry.example.com（或留空使用默认）
```

### 部署模式

```
部署模式：固定实例（或弹性伸缩）

实例数：1

CPU：1-2 Core（ODA File Converter 需要一定资源）

内存：2-4 GiB（DEB 包安装需要内存）
```

### 网络配置

```
端口：8000（根据您的应用配置）
```

---

## ✅ 验证部署

部署完成后：

1. **进入应用详情页**
2. **打开终端**
3. **执行验证命令**：

```bash
DWGConvert --version
ODAFileConverter --version
```

---

## 🎯 推荐方案

**推荐使用方案1（GitHub Actions）**，因为：
- ✅ 自动化构建
- ✅ 代码更新自动触发
- ✅ 无需手动操作
- ✅ 构建日志清晰

---

## 📖 相关文档

- GitHub Actions 文档：https://docs.github.com/en/actions
- Docker Hub：https://hub.docker.com
- Sealos 镜像仓库：查看 Sealos 文档

