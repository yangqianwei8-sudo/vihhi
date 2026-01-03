# ODA File Converter 安装包目录

## 📦 安装步骤（Sealos平台）

### 1. 下载ODA File Converter

访问：https://www.opendesign.com/guestfiles
- 注册免费账号
- 下载Linux版本的ODA File Converter
- **推荐格式**：`ODAFileConverter_*.deb` (DEB包，适用于Ubuntu/Debian系统)
- **备选格式**：`ODAFileConverter_*.tar.gz` (压缩包)

### 2. 放置安装包

将下载的安装包放到此目录：
```bash
# 如果下载的是DEB包（推荐）
cp ODAFileConverter_*.deb deployment/docker/oda/

# 或者如果下载的是TAR.GZ压缩包
cp ODAFileConverter_*.tar.gz deployment/docker/oda/
```

### 3. 构建Docker镜像

```bash
docker build -f deployment/docker/Dockerfile.backend -t your-registry/backend:latest .
```

### 4. 部署到Sealos

镜像构建完成后，推送到镜像仓库并在Sealos上部署。

## ⚠️ 注意事项

1. **文件大小**：ODA File Converter安装包较大（约100-200MB），建议添加到`.gitignore`
2. **版本更新**：更新ODA File Converter时需要重新构建镜像
3. **可选安装**：如果没有安装包，Dockerfile会跳过安装，但DWG文件解析功能将不可用

## 📝 .gitignore 配置

如果不想将安装包提交到Git仓库，在`.gitignore`中添加：

```
deployment/docker/oda/*.deb
deployment/docker/oda/*.tar.gz
!deployment/docker/oda/.gitkeep
```

