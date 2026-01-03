# Sealos平台部署 - ODA File Converter安装指南

## 🎯 重要说明

**在Sealos平台上，ODA File Converter必须安装在Docker容器镜像中，而不是您的本机！**

Sealos是基于Kubernetes的云原生平台，您的应用运行在容器中，所以所有依赖都需要打包到容器镜像里。

## 📦 安装方式

### 方式1：修改Dockerfile（推荐）

修改 `deployment/docker/Dockerfile.backend`，添加ODA File Converter的安装步骤：

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-dev \
    wget \
    tar \
    && rm -rf /var/lib/apt/lists/*

# 安装ODA File Converter
# 注意：需要先从ODA官网下载安装包，然后上传到代码仓库或使用wget下载
RUN mkdir -p /opt/ODAFileConverter && \
    # 方法1：如果安装包在代码仓库中
    # COPY deployment/docker/ODAFileConverter_*.tar.gz /tmp/ && \
    # tar -xzf /tmp/ODAFileConverter_*.tar.gz -C /opt/ODAFileConverter --strip-components=1 && \
    # 方法2：如果可以从ODA官网直接下载（需要注册账号）
    # wget -q --user=YOUR_USERNAME --password=YOUR_PASSWORD \
    #     https://www.opendesign.com/guestfiles/download/ODAFileConverter_*.tar.gz -O /tmp/oda.tar.gz && \
    # tar -xzf /tmp/oda.tar.gz -C /opt/ODAFileConverter --strip-components=1 && \
    chmod +x /opt/ODAFileConverter/bin/DWGConvert && \
    ln -s /opt/ODAFileConverter/bin/DWGConvert /usr/local/bin/DWGConvert && \
    rm -rf /tmp/*.tar.gz

# 复制依赖文件并安装
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目代码
COPY . .

# 收集静态文件
RUN python manage.py collectstatic --noinput

EXPOSE 8000

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "backend.config.wsgi:application"]
```

### 方式2：使用多阶段构建（更灵活）

```dockerfile
FROM python:3.11-slim as base

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-dev \
    wget \
    tar \
    && rm -rf /var/lib/apt/lists/*

# 安装ODA File Converter的构建阶段
FROM base as oda-installer
# 在这里下载和安装ODA File Converter
RUN mkdir -p /opt/ODAFileConverter
# ... 安装步骤 ...

# 最终镜像
FROM base
COPY --from=oda-installer /opt/ODAFileConverter /opt/ODAFileConverter
RUN ln -s /opt/ODAFileConverter/bin/DWGConvert /usr/local/bin/DWGConvert

# ... 其他步骤 ...
```

### 方式3：使用Init容器（Sealos/Kubernetes特有）

在Sealos的部署配置中，可以使用Init容器来安装ODA File Converter：

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend
spec:
  template:
    spec:
      initContainers:
      - name: install-oda
        image: busybox
        command:
        - sh
        - -c
        - |
          # 下载并安装ODA File Converter
          wget https://download.opendesign.com/guestfiles/ODAFileConverter_*.tar.gz
          tar -xzf ODAFileConverter_*.tar.gz -C /shared/oda
        volumeMounts:
        - name: oda-shared
          mountPath: /shared/oda
      containers:
      - name: backend
        image: your-backend-image
        volumeMounts:
        - name: oda-shared
          mountPath: /opt/ODAFileConverter
      volumes:
      - name: oda-shared
        emptyDir: {}
```

## 🚀 实际部署步骤

### 步骤1：准备ODA File Converter安装包

1. **下载安装包**
   - 访问：https://www.opendesign.com/guestfiles
   - 注册账号并下载Linux版本的ODA File Converter
   - 文件格式：`ODAFileConverter_*.tar.gz`

2. **上传到代码仓库**
   ```bash
   # 创建目录
   mkdir -p deployment/docker/oda
   
   # 复制安装包
   cp ODAFileConverter_*.tar.gz deployment/docker/oda/
   
   # 添加到.gitignore（如果文件太大）
   echo "deployment/docker/oda/*.tar.gz" >> .gitignore
   ```

### 步骤2：修改Dockerfile

修改 `deployment/docker/Dockerfile.backend`：

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-dev \
    wget \
    tar \
    && rm -rf /var/lib/apt/lists/*

# 安装ODA File Converter
COPY deployment/docker/oda/ODAFileConverter_*.tar.gz /tmp/oda.tar.gz
RUN mkdir -p /opt/ODAFileConverter && \
    tar -xzf /tmp/oda.tar.gz -C /opt/ODAFileConverter --strip-components=1 && \
    chmod +x /opt/ODAFileConverter/bin/DWGConvert && \
    ln -s /opt/ODAFileConverter/bin/DWGConvert /usr/local/bin/DWGConvert && \
    rm -f /tmp/oda.tar.gz

# 验证安装
RUN DWGConvert --version || echo "ODA File Converter安装失败"

# 复制依赖文件并安装
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目代码
COPY . .

# 收集静态文件
RUN python manage.py collectstatic --noinput

EXPOSE 8000

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "backend.config.wsgi:application"]
```

### 步骤3：构建和部署

```bash
# 构建镜像
docker build -f deployment/docker/Dockerfile.backend -t your-registry/backend:latest .

# 推送到镜像仓库
docker push your-registry/backend:latest

# 在Sealos上部署
# 通过Sealos控制台或使用sealos命令部署
```

## 🔧 Sealos平台特殊配置

### 在Sealos中配置环境变量

如果ODA File Converter安装在非标准位置，可以在Sealos的应用配置中添加环境变量：

```yaml
env:
  - name: ODA_FILE_CONVERTER_PATH
    value: "/opt/ODAFileConverter/bin/DWGConvert"
```

### 使用Sealos的存储卷

如果需要持久化ODA File Converter，可以使用Sealos的存储卷：

```yaml
volumes:
  - name: oda-converter
    mountPath: /opt/ODAFileConverter
    type: pvc
```

## ✅ 验证安装

部署后，在容器中验证：

```bash
# 进入容器
kubectl exec -it <pod-name> -- /bin/bash

# 检查ODA File Converter
DWGConvert --version

# 检查Python依赖
python -c "import ezdxf; print('ezdxf OK')"
python -c "from pdf2image import convert_from_path; print('pdf2image OK')"
```

## ⚠️ 注意事项

1. **镜像大小**：ODA File Converter会增加镜像大小（约100-200MB）
2. **构建时间**：首次构建可能需要更长时间
3. **许可证**：确保遵守ODA File Converter的使用许可
4. **版本更新**：更新ODA File Converter时需要重新构建镜像

## 📝 替代方案

如果不想在镜像中包含ODA File Converter，可以考虑：

1. **使用Sidecar容器**：在同一个Pod中运行ODA File Converter的Sidecar容器
2. **使用共享存储**：将ODA File Converter放在共享存储中，多个Pod共享
3. **使用服务网格**：通过服务网格调用外部的ODA File Converter服务

## 🔗 相关资源

- Sealos文档：https://sealos.io/docs
- ODA File Converter下载：https://www.opendesign.com/guestfiles
- Kubernetes Init容器：https://kubernetes.io/docs/concepts/workloads/pods/init-containers/

