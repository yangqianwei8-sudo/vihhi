# 在 Sealos 上创建应用 - 完整步骤

## 🎯 当前状态

- ✅ 代码已推送到 Git 仓库
- ✅ Dockerfile 已配置完成
- ⏳ **需要：在 Sealos 上创建应用**

## 📋 创建应用步骤

### 步骤1：点击"新建应用"按钮

在 Sealos Cloud 的"应用管理"页面，点击右下角的 **"+ 新建应用"** 按钮。

### 步骤2：选择应用类型

选择 **"从代码构建"** 或 **"从 Git 仓库构建"** 选项。

### 步骤3：配置 Git 仓库

1. **选择代码源**
   - 选择您的 Git 提供商（GitHub/GitLab/Gitee 等）
   - 如果是第一次，需要授权 Sealos 访问您的仓库

2. **选择仓库**
   - 选择包含您代码的仓库
   - 选择分支：`main` 或 `master`

### 步骤4：配置构建参数

**关键配置**：

```
应用名称：backend（或您自定义的名称）

构建方式：Dockerfile

Dockerfile 路径：deployment/docker/Dockerfile.backend

构建上下文：/ (项目根目录，或留空使用默认值)
```

**其他配置**：

```
镜像名称：backend（或自定义）
镜像标签：latest
端口：8000（根据您的应用配置）
```

### 步骤5：配置资源（可选）

```
CPU：根据需求设置（如 1-2 Core）
内存：根据需求设置（如 2-4 GiB）
```

### 步骤6：启动构建

1. 检查所有配置
2. 点击"创建"或"开始构建"按钮
3. 等待构建完成（首次构建可能需要 5-10 分钟）

### 步骤7：监控构建过程

在构建日志中，您应该看到：

```
安装ODA File Converter (DEB包)...
✓ ODA File Converter (DEB) 安装成功
```

## ✅ 构建成功后的验证

构建完成后，应用会自动部署。然后：

1. **进入应用详情页**
   - 在应用列表中点击您的应用名称

2. **打开终端**
   - 在应用详情页找到"终端"或"Console"按钮
   - 点击打开容器终端

3. **执行验证命令**
   ```bash
   DWGConvert --version
   ODAFileConverter --version
   ```

## 📸 界面位置参考

### 创建应用时的关键字段：

```
┌─────────────────────────────────┐
│ 应用名称: backend               │
│                                 │
│ 代码源: [选择 Git 仓库]         │
│ 分支: main                      │
│                                 │
│ 构建方式: Dockerfile            │
│ Dockerfile路径:                 │
│   deployment/docker/            │
│   Dockerfile.backend            │
│                                 │
│ 构建上下文: /                   │
└─────────────────────────────────┘
```

## ⚠️ 注意事项

1. **Dockerfile 路径必须正确**
   - 确保路径是：`deployment/docker/Dockerfile.backend`
   - 不要包含项目根目录名称

2. **构建上下文**
   - 通常是项目根目录 `/`
   - 或留空使用默认值

3. **首次构建时间**
   - 可能需要 5-10 分钟
   - 因为需要下载基础镜像和安装 DEB 包

## 🐛 常见问题

### 问题1：构建失败 - 找不到 Dockerfile

**解决**：检查 Dockerfile 路径是否正确，应该是 `deployment/docker/Dockerfile.backend`

### 问题2：构建失败 - 找不到 DEB 包

**解决**：
- 确认 DEB 包已推送到 Git 仓库
- 检查文件路径：`deployment/docker/oda/ODAFileConverter_QT6_lnxX64_8.3dll_26.10.deb`

### 问题3：构建超时

**解决**：
- 增加构建超时时间
- 检查网络连接
- 查看构建日志中的具体错误

## 🎉 完成！

创建应用并构建成功后，您就可以在应用容器的终端中验证 ODA File Converter 的安装了！

---

**提示**：如果 Sealos 界面与描述略有不同，请参考 Sealos 的官方文档或联系技术支持。

