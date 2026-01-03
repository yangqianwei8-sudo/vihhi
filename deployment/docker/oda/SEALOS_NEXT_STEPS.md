# Sealos 配置下一步操作

## ✅ 已完成

- [x] DEB 包已推送到 Git 仓库
- [x] Dockerfile 已配置支持 DEB 包安装
- [x] 代码已推送到远程仓库

## 📋 在 Sealos 控制台的操作步骤

### 步骤1：登录 Sealos 控制台

1. 访问您的 Sealos 平台地址
2. 登录您的账号

### 步骤2：创建/编辑应用

#### 如果是新应用：

1. 点击"创建应用"或"新建应用"
2. 选择"从代码构建"或"从 Git 仓库构建"

#### 如果是现有应用：

1. 找到您的应用
2. 点击"编辑"或"设置"
3. 进入"构建配置"或"代码构建"页面

### 步骤3：配置 Git 仓库连接

1. **选择代码源**
   - 选择您的 Git 提供商（GitHub/GitLab/Gitee 等）
   - 授权 Sealos 访问您的仓库

2. **选择仓库和分支**
   - 仓库：选择包含代码的仓库
   - 分支：选择 `main` 或 `master` 分支

### 步骤4：配置构建参数

**关键配置项**：

```
构建方式：Dockerfile
Dockerfile 路径：deployment/docker/Dockerfile.backend
构建上下文：/ (项目根目录，或留空使用默认值)
```

**其他可选配置**：

```
镜像名称：backend（或您自定义的名称）
镜像标签：latest（或版本号）
构建命令：留空（使用 Dockerfile 默认构建）
```

### 步骤5：触发构建

1. 点击"构建"或"开始构建"按钮
2. 等待构建完成（首次构建可能需要 5-10 分钟）

### 步骤6：监控构建过程

在构建日志中，您应该看到：

```
安装ODA File Converter (DEB包)...
✓ ODA File Converter (DEB) 安装成功
```

**如果看到这个日志，说明安装成功！**

### 步骤7：验证安装

构建完成后，部署应用，然后在容器中验证：

**方法1：通过 Sealos 控制台终端**

1. 进入应用详情页
2. 点击"终端"或"Console"
3. 执行以下命令：

```bash
# 检查 DWGConvert 命令
DWGConvert --version

# 或检查 ODAFileConverter 命令
ODAFileConverter --version

# 检查安装位置
ls -la /opt/ODAFileConverter/
ls -la /usr/local/bin/DWGConvert
```

**方法2：通过 kubectl（如果有权限）**

```bash
# 获取 Pod 名称
kubectl get pods

# 进入容器
kubectl exec -it <pod-name> -- /bin/bash

# 验证
DWGConvert --version
```

## ⚠️ 注意事项

### 关于大文件（54.41 MB）

虽然文件已成功推送，但 GitHub 建议使用 Git LFS。**当前可以正常使用**，但如果您将来需要：

- 频繁更新 DEB 包
- 添加更多大文件
- 优化仓库性能

可以考虑迁移到 Git LFS：

```bash
# 安装 Git LFS
git lfs install

# 迁移现有文件
git lfs migrate import --include="deployment/docker/oda/*.deb" --everything

# 强制推送（会重写历史）
git push --force
```

**注意**：迁移 Git LFS 会重写 Git 历史，需要团队协作时谨慎操作。

### 构建失败排查

如果构建失败，检查：

1. **Dockerfile 路径是否正确**
   - 应该是：`deployment/docker/Dockerfile.backend`

2. **构建上下文是否正确**
   - 应该是项目根目录

3. **DEB 包是否在仓库中**
   - 检查 Git 仓库中是否有 `deployment/docker/oda/ODAFileConverter_QT6_lnxX64_8.3dll_26.10.deb`

4. **查看构建日志**
   - 在 Sealos 构建日志中查看具体错误信息

## 🎯 成功标志

构建成功后，您应该能够：

- ✅ 在容器中执行 `DWGConvert --version` 看到版本信息
- ✅ 在容器中执行 `ODAFileConverter --version` 看到版本信息
- ✅ 应用可以正常使用 DWG 文件转换功能

## 📞 需要帮助？

如果遇到问题：

1. 查看构建日志中的错误信息
2. 参考 `SEALOS_BUILD_GUIDE.md` 中的故障排查部分
3. 检查 Sealos 文档或联系 Sealos 技术支持

---

**祝您部署顺利！** 🚀

