# Docker 安装指南（Debian/Ubuntu）

## 🐳 安装 Docker

### 方法1：使用官方安装脚本（推荐）

```bash
# 下载并运行 Docker 官方安装脚本
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# 启动 Docker 服务
sudo systemctl start docker
sudo systemctl enable docker

# 验证安装
docker --version
```

### 方法2：使用 apt 包管理器

```bash
# 更新包索引
sudo apt-get update

# 安装必要的依赖
sudo apt-get install -y \
    ca-certificates \
    curl \
    gnupg \
    lsb-release

# 添加 Docker 官方 GPG 密钥
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/debian/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# 设置仓库
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# 安装 Docker Engine
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# 启动 Docker 服务
sudo systemctl start docker
sudo systemctl enable docker
```

### 方法3：使用系统包管理器（简单但可能版本较旧）

```bash
sudo apt-get update
sudo apt-get install -y docker.io
sudo systemctl start docker
sudo systemctl enable docker
```

## ✅ 验证安装

```bash
# 检查 Docker 版本
docker --version

# 运行测试容器
sudo docker run hello-world
```

## 👤 配置用户权限（可选）

为了避免每次使用 `sudo`，可以将用户添加到 docker 组：

```bash
# 将当前用户添加到 docker 组
sudo usermod -aG docker $USER

# 重新登录或执行以下命令使更改生效
newgrp docker

# 验证（应该不需要 sudo）
docker ps
```

## 🚀 开始构建

安装完成后，就可以构建镜像了：

```bash
cd /home/devbox/project/vihhi/weihai_tech_production_system
docker build -f deployment/docker/Dockerfile.backend -t backend:latest .
```

