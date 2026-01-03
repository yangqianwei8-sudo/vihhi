# ODA File Converter DEB 包安装步骤

## ✅ 您已完成：下载 DEB 包
文件：`ODAFileConverter_QT6_InxX64_8.3dll_26.10.deb`

## 📋 下一步操作

### 步骤1：将 DEB 包复制到项目目录

您需要将 Windows 下载文件夹中的 DEB 包复制到 Linux 项目目录。

**方法1：使用 SCP（推荐）**
```bash
# 在 Linux 终端执行（替换为您的实际路径）
scp /mnt/c/Users/Administrator/下载/ODAFileConverter_QT6_InxX64_8.3dll_26.10.deb \
    /home/devbox/project/vihhi/weihai_tech_production_system/deployment/docker/oda/
```

**方法2：使用共享文件夹**
如果您的 Windows 和 Linux 之间有共享文件夹，直接复制即可。

**方法3：在 Linux 中重新下载**
```bash
# 如果可以直接访问下载链接，在 Linux 中下载
cd /home/devbox/project/vihhi/weihai_tech_production_system/deployment/docker/oda/
wget <下载链接> -O ODAFileConverter_QT6_InxX64_8.3dll_26.10.deb
```

### 步骤2：验证文件已复制

```bash
ls -lh /home/devbox/project/vihhi/weihai_tech_production_system/deployment/docker/oda/
# 应该能看到 ODAFileConverter_QT6_InxX64_8.3dll_26.10.deb 文件
```

### 步骤3：构建 Docker 镜像

#### 选项A：在本地构建（需要安装 Docker）

**如果系统未安装 Docker，可以安装：**

```bash
# Debian/Ubuntu 系统安装 Docker
sudo apt-get update
sudo apt-get install -y docker.io
sudo systemctl start docker
sudo systemctl enable docker
# 将当前用户添加到 docker 组（可选，避免每次使用 sudo）
sudo usermod -aG docker $USER
# 重新登录或执行：newgrp docker
```

**然后构建镜像：**
```bash
cd /home/devbox/project/vihhi/weihai_tech_production_system
docker build -f deployment/docker/Dockerfile.backend -t backend:latest .
```

#### 选项B：在 Sealos 平台上直接构建（推荐）⭐

**详细指南请查看**：`SEALOS_BUILD_GUIDE.md`

**快速步骤**：
1. 将代码推送到 Git 仓库
   - 如果使用 Git LFS：`git lfs track "deployment/docker/oda/*.deb"` 然后提交
   - 或直接提交（如果仓库允许大文件）
2. 在 Sealos 控制台配置构建：
   - Dockerfile 路径：`deployment/docker/Dockerfile.backend`
   - 构建上下文：项目根目录
3. 触发构建，Sealos 会自动构建并部署

**注意**：DEB 包（55MB）已添加到 `.gitignore`，如需提交请使用 Git LFS 或移除忽略规则。

**注意**：构建过程可能需要几分钟时间，Dockerfile 会自动：
1. 检测 DEB 包
2. 提取并安装 ODA File Converter
3. 创建 `DWGConvert` 和 `ODAFileConverter` 命令的符号链接

### 步骤4：验证安装

```bash
# 运行容器并测试
docker run --rm backend:latest DWGConvert --version

# 或者测试 ODAFileConverter 命令
docker run --rm backend:latest ODAFileConverter --version
```

### 步骤5：部署到 Sealos

构建成功后，将镜像推送到镜像仓库，然后在 Sealos 平台上部署。

## 🎯 完成！

构建成功后，ODA File Converter 就已经集成到 Docker 镜像中了，可以部署到 Sealos 平台使用。

