# Sealos 平台构建指南 - ODA File Converter

## 🎯 方案2：在 Sealos 平台直接构建

### 前置条件

✅ **已完成**：
- DEB 包已下载：`ODAFileConverter_QT6_lnxX64_8.3dll_26.10.deb`
- Dockerfile 已配置：`deployment/docker/Dockerfile.backend`
- 支持自动检测和安装 DEB 包

## 📋 部署步骤

### 步骤1：配置 Git 仓库

#### 选项A：将 DEB 包提交到 Git（如果文件大小允许）

如果您的 Git 仓库支持大文件（如使用 Git LFS），可以将 DEB 包提交：

```bash
# 检查文件大小
ls -lh deployment/docker/oda/ODAFileConverter_QT6_lnxX64_8.3dll_26.10.deb

# 如果使用 Git LFS（推荐用于大文件）
git lfs install
git lfs track "deployment/docker/oda/*.deb"
git add .gitattributes
git add deployment/docker/oda/ODAFileConverter_QT6_lnxX64_8.3dll_26.10.deb
git commit -m "添加 ODA File Converter DEB 包"
git push
```

#### 选项B：不提交 DEB 包（推荐，使用自动下载）

如果不想将大文件提交到 Git，可以配置 Dockerfile 从 ODA 官网自动下载：

1. **确保 DEB 包在构建时可用**（通过环境变量或构建参数）
2. **或修改 Dockerfile 支持从 URL 下载**

### 步骤2：在 Sealos 控制台配置构建

1. **登录 Sealos 控制台**
   - 访问您的 Sealos 平台
   - 进入应用管理页面

2. **创建新应用或编辑现有应用**
   - 选择"从代码构建"或"从 Dockerfile 构建"
   - 连接您的 Git 仓库

3. **配置构建参数**
   ```
   构建上下文：/ (项目根目录)
   Dockerfile 路径：deployment/docker/Dockerfile.backend
   构建命令：自动（Sealos 会使用 Dockerfile）
   ```

4. **设置环境变量**（如果需要）
   ```
   # 如果使用自动下载方式，可能需要设置：
   ODA_DOWNLOAD_URL=<下载链接>
   ODA_USERNAME=<您的ODA账号>
   ODA_PASSWORD=<您的ODA密码>
   ```

### 步骤3：触发构建

1. **手动触发**
   - 在 Sealos 控制台点击"构建"或"重新构建"
   - Sealos 会从 Git 仓库拉取代码并执行构建

2. **自动触发**（如果配置了 Webhook）
   - 推送到 Git 仓库后自动触发构建

### 步骤4：监控构建过程

在 Sealos 构建日志中，您应该能看到：

```
安装ODA File Converter (DEB包)...
✓ ODA File Converter (DEB) 安装成功
```

### 步骤5：验证部署

构建完成后，在 Sealos 容器中验证：

```bash
# 通过 Sealos 控制台的终端功能进入容器
# 或使用 kubectl（如果有权限）

# 检查 ODA File Converter
DWGConvert --version
# 或
ODAFileConverter --version

# 检查安装位置
ls -la /opt/ODAFileConverter/
ls -la /usr/local/bin/DWGConvert
```

## 🔧 高级配置

### 使用 Git LFS（推荐用于大文件）

如果 DEB 包超过 100MB，建议使用 Git LFS：

```bash
# 安装 Git LFS
git lfs install

# 跟踪 DEB 文件
git lfs track "deployment/docker/oda/*.deb"

# 提交配置
git add .gitattributes
git add deployment/docker/oda/ODAFileConverter_QT6_lnxX64_8.3dll_26.10.deb
git commit -m "添加 ODA File Converter (使用 Git LFS)"
git push
```

### 使用构建缓存优化

在 Sealos 构建配置中启用缓存，可以加速后续构建：

```yaml
# 在 Sealos 构建配置中
cache:
  enabled: true
  paths:
    - /var/lib/apt/lists
```

### 使用多阶段构建优化镜像大小

如果需要优化镜像大小，可以考虑多阶段构建（已在 Dockerfile 中实现）。

## ⚠️ 注意事项

1. **文件大小限制**
   - 如果 Git 仓库有文件大小限制，使用 Git LFS
   - 或使用自动下载方式

2. **构建时间**
   - 首次构建可能需要 5-10 分钟
   - 后续构建会使用缓存，速度更快

3. **网络访问**
   - 确保 Sealos 构建环境可以访问 Git 仓库
   - 如果使用自动下载，确保可以访问 ODA 官网

4. **权限问题**
   - 确保 Sealos 有权限访问您的 Git 仓库
   - 如果使用私有仓库，配置访问令牌

## 🐛 故障排查

### 问题1：构建失败 - 找不到 DEB 包

**解决方案**：
- 检查 DEB 包是否在 Git 仓库中
- 检查 Dockerfile 中的 COPY 路径是否正确
- 查看构建日志确认文件是否存在

### 问题2：构建失败 - 权限错误

**解决方案**：
- 检查 Dockerfile 中的文件权限设置
- 确保使用正确的用户权限

### 问题3：运行时找不到 DWGConvert 命令

**解决方案**：
- 检查符号链接是否正确创建
- 验证 `/usr/local/bin/DWGConvert` 是否存在
- 检查 PATH 环境变量

## 📝 检查清单

在 Sealos 上部署前，确认：

- [ ] DEB 包已提交到 Git 仓库（或配置了自动下载）
- [ ] Dockerfile 路径正确：`deployment/docker/Dockerfile.backend`
- [ ] Sealos 已连接到 Git 仓库
- [ ] 构建配置已设置
- [ ] 构建日志显示 ODA File Converter 安装成功
- [ ] 部署后验证 `DWGConvert --version` 可以执行

## 🎉 完成！

构建成功后，您的应用就可以在 Sealos 平台上使用 ODA File Converter 进行 DWG 文件转换了！

