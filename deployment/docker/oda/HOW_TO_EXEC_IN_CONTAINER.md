# 如何在 Sealos 容器中执行命令

## 🎯 方法1：通过 Sealos 控制台终端（最简单）

### 步骤：

1. **登录 Sealos 控制台**
   - 访问您的 Sealos 平台
   - 使用账号登录

2. **进入应用详情页**
   - 找到您的应用（backend）
   - 点击应用名称进入详情页

3. **打开终端/控制台**
   - 在应用详情页找到"终端"、"Console"或"执行命令"按钮
   - 点击打开 Web 终端

4. **执行验证命令**
   ```bash
   # 检查 DWGConvert 命令
   DWGConvert --version
   
   # 或检查 ODAFileConverter 命令
   ODAFileConverter --version
   
   # 检查安装位置
   ls -la /opt/ODAFileConverter/
   ls -la /usr/local/bin/DWGConvert
   ```

### 界面位置（不同 Sealos 版本可能略有不同）：
- 通常在应用详情页的顶部或侧边栏
- 可能显示为："终端"、"控制台"、"Console"、"执行命令"、"Shell"等

---

## 🔧 方法2：通过 kubectl（需要集群访问权限）

### 前提条件：
- 已安装 kubectl
- 已配置 Sealos 集群的 kubeconfig
- 有访问权限

### 步骤：

1. **获取 Pod 名称**
   ```bash
   kubectl get pods -n <namespace>
   # 或
   kubectl get pods
   ```
   
   输出示例：
   ```
   NAME                      READY   STATUS    RESTARTS   AGE
   backend-xxxxxxxxxx-xxxxx   1/1     Running   0          5m
   ```

2. **进入容器**
   ```bash
   kubectl exec -it <pod-name> -n <namespace> -- /bin/bash
   # 或如果默认命名空间
   kubectl exec -it <pod-name> -- /bin/bash
   ```
   
   示例：
   ```bash
   kubectl exec -it backend-xxxxxxxxxx-xxxxx -- /bin/bash
   ```

3. **执行验证命令**
   ```bash
   # 检查版本
   DWGConvert --version
   ODAFileConverter --version
   
   # 检查文件
   ls -la /opt/ODAFileConverter/
   which DWGConvert
   ```

4. **退出容器**
   ```bash
   exit
   ```

---

## 🚀 方法3：使用 kubectl exec 直接执行命令（无需进入容器）

### 步骤：

```bash
# 直接执行命令（不需要进入容器）
kubectl exec <pod-name> -- DWGConvert --version

# 或
kubectl exec <pod-name> -- ODAFileConverter --version

# 检查文件
kubectl exec <pod-name> -- ls -la /opt/ODAFileConverter/
kubectl exec <pod-name> -- ls -la /usr/local/bin/DWGConvert
```

**优点**：快速，不需要交互式终端

---

## 📋 方法4：通过 Sealos CLI（如果支持）

### 步骤：

```bash
# 如果 Sealos 提供了 CLI 工具
sealos exec <app-name> -- DWGConvert --version

# 或进入容器
sealos shell <app-name>
```

---

## 🔍 验证命令清单

在容器中执行以下命令来验证安装：

```bash
# 1. 检查命令是否存在
which DWGConvert
which ODAFileConverter

# 2. 检查版本
DWGConvert --version
ODAFileConverter --version

# 3. 检查安装目录
ls -la /opt/ODAFileConverter/
ls -la /opt/ODAFileConverter/ODAFileConverter

# 4. 检查符号链接
ls -la /usr/local/bin/DWGConvert
ls -la /usr/local/bin/ODAFileConverter

# 5. 测试转换功能（可选，需要测试文件）
# DWGConvert input.dwg output.dxf
```

---

## ✅ 成功标志

如果看到以下输出，说明安装成功：

```bash
$ DWGConvert --version
ODAFileConverter version 26.10.0.0
# 或类似的版本信息

$ which DWGConvert
/usr/local/bin/DWGConvert

$ ls -la /opt/ODAFileConverter/ODAFileConverter
-rwxr-xr-x 1 root root 529640 ... /opt/ODAFileConverter/ODAFileConverter
```

---

## ❌ 如果命令未找到

如果 `DWGConvert: command not found`，检查：

1. **构建是否成功**
   - 查看 Sealos 构建日志
   - 确认看到 "✓ ODA File Converter (DEB) 安装成功"

2. **检查安装位置**
   ```bash
   # 在容器中执行
   ls -la /opt/ODAFileConverter/
   ls -la /usr/local/bin/
   ```

3. **检查 PATH 环境变量**
   ```bash
   echo $PATH
   # 应该包含 /usr/local/bin
   ```

4. **手动测试可执行文件**
   ```bash
   /opt/ODAFileConverter/ODAFileConverter --version
   /usr/local/bin/DWGConvert --version
   ```

---

## 💡 提示

- **方法1（Sealos 控制台终端）**是最简单的方式，推荐使用
- 如果 Sealos 控制台没有终端功能，使用 **方法2（kubectl）**
- **方法3（kubectl exec）**适合快速检查，不需要交互式终端

---

## 📞 需要帮助？

如果无法访问容器或遇到问题：

1. 检查 Sealos 控制台的帮助文档
2. 联系 Sealos 技术支持
3. 查看构建日志确认安装是否成功

