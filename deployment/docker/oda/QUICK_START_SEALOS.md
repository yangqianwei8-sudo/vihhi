# Sealos 快速部署指南

## 🚀 5 分钟快速开始

### 步骤1：准备 Git 仓库

```bash
# 检查当前状态
cd /home/devbox/project/vihhi/weihai_tech_production_system
git status

# 如果使用 Git LFS（推荐，因为 DEB 包有 55MB）
git lfs install
git lfs track "deployment/docker/oda/*.deb"
git add .gitattributes

# 提交所有更改（包括 Dockerfile 和 DEB 包）
git add deployment/docker/Dockerfile.backend
git add deployment/docker/oda/ODAFileConverter_QT6_lnxX64_8.3dll_26.10.deb
git add .gitignore
git commit -m "配置 ODA File Converter DEB 包安装"
git push
```

**或者不使用 Git LFS**（如果仓库允许大文件）：
```bash
# 临时移除 .gitignore 中的排除规则
# 编辑 .gitignore，注释掉 deployment/docker/oda/*.deb 这一行
git add deployment/docker/oda/ODAFileConverter_QT6_lnxX64_8.3dll_26.10.deb
git commit -m "添加 ODA File Converter DEB 包"
git push
```

### 步骤2：在 Sealos 控制台配置

1. **登录 Sealos 控制台**
2. **创建/编辑应用**
   - 选择"从代码构建"
   - 连接您的 Git 仓库
3. **配置构建参数**
   ```
   Dockerfile 路径：deployment/docker/Dockerfile.backend
   构建上下文：/ (项目根目录)
   ```
4. **点击"构建"或"部署"**

### 步骤3：验证安装

构建完成后，在 Sealos 容器终端执行：

```bash
DWGConvert --version
# 或
ODAFileConverter --version
```

## ✅ 完成！

如果看到版本信息，说明安装成功！

## 📚 更多信息

- 详细指南：`SEALOS_BUILD_GUIDE.md`
- 故障排查：`SEALOS_BUILD_GUIDE.md` 中的故障排查部分

