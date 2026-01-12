# 国内镜像源配置说明

## 已配置的镜像源

### 1. Python pip 镜像源 ✅
已配置为使用清华大学镜像源：
- 配置文件：`~/.pip/pip.conf`
- 镜像地址：https://pypi.tuna.tsinghua.edu.cn/simple

### 2. npm 镜像源 ✅
已配置为使用淘宝镜像：
- 镜像地址：https://registry.npmmirror.com
- 配置命令：`npm config set registry https://registry.npmmirror.com`

### 3. Docker 镜像加速器 ⚠️
需要手动配置（需要 root 权限）：

#### 方法一：配置 daemon.json（推荐）
```bash
sudo mkdir -p /etc/docker
sudo tee /etc/docker/daemon.json <<-'EOF'
{
  "registry-mirrors": [
    "https://docker.mirrors.ustc.edu.cn",
    "https://hub-mirror.c.163.com",
    "https://mirror.baidubce.com"
  ]
}
EOF
sudo systemctl daemon-reload
sudo systemctl restart docker
```

#### 方法二：在 Dockerfile 中使用国内基础镜像
如果无法配置 daemon.json，可以在 Dockerfile 中使用国内镜像：
```dockerfile
# 使用阿里云镜像
FROM registry.cn-hangzhou.aliyuncs.com/acs/python:3.11-slim
```

### 4. Dockerfile 中的 pip 安装 ✅
已修改 Dockerfile.backend，在构建时自动使用清华镜像源。

## 验证配置

### 测试 pip 镜像源
```bash
pip config list
pip install --dry-run requests
```

### 测试 npm 镜像源
```bash
npm config get registry
npm install --dry-run axios
```

### 测试 Docker 镜像加速
```bash
docker info | grep -A 10 "Registry Mirrors"
```

## 其他可选镜像源

### pip 镜像源（备选）
- 阿里云：https://mirrors.aliyun.com/pypi/simple/
- 中科大：https://pypi.mirrors.ustc.edu.cn/simple/
- 腾讯云：https://mirrors.cloud.tencent.com/pypi/simple

### npm 镜像源（备选）
- 腾讯云：https://mirrors.cloud.tencent.com/npm/
- 华为云：https://repo.huaweicloud.com/repository/npm/

### Docker 镜像加速器（备选）
- 中科大：https://docker.mirrors.ustc.edu.cn
- 网易：https://hub-mirror.c.163.com
- 百度云：https://mirror.baidubce.com
- 阿里云：需要登录阿里云获取专属加速地址

## 注意事项

1. 如果遇到 SSL 证书问题，可以添加 `--trusted-host` 参数
2. 某些私有包可能不在镜像源中，需要临时切换回官方源
3. Docker 镜像加速器配置后需要重启 Docker 服务才能生效

