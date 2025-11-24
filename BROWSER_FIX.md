# 🌐 浏览器访问问题解决方案

## ❌ 问题现象

访问 `http://localhost:8000/` 时出现：
- 页面显示"网页无法访问"
- 控制台错误：`ERR_SSL_PROTOCOL_ERROR`
- 错误来源：`errsug7_new.js:1`（360浏览器错误提示脚本）

## 🔍 问题原因

这个错误通常由以下原因引起：

1. **360浏览器强制HTTPS**：360浏览器可能自动将HTTP请求升级为HTTPS
2. **浏览器扩展干扰**：某些安全扩展可能拦截HTTP请求
3. **端口不匹配**：根据Sealos配置，应该使用8001端口，而不是8000端口

## ✅ 解决方案

### 方案1：使用8001端口（推荐）

根据您的Sealos配置，服务器应该运行在**8001端口**：

**访问地址**：
- ✅ http://localhost:8001/
- ✅ http://127.0.0.1:8001/

### 方案2：更换浏览器

360浏览器可能对本地HTTP有特殊处理，建议使用：

- **Chrome浏览器**：http://localhost:8001/
- **Firefox浏览器**：http://localhost:8001/
- **Edge浏览器**：http://localhost:8001/

### 方案3：禁用360浏览器的HTTPS强制

1. 打开360浏览器设置
2. 找到"安全设置"或"高级设置"
3. 关闭"自动将HTTP升级为HTTPS"选项
4. 或者添加 `localhost` 到HTTP白名单

### 方案4：使用Sealos公网地址

如果本地访问有问题，可以使用Sealos提供的公网地址：

- **公网HTTPS地址**：https://tivpdkrxyioz.sealosbja.site/

这个地址由Sealos平台提供SSL证书，不会有SSL错误。

## 🔧 快速修复步骤

### 步骤1：确认服务器运行在8001端口

```bash
# 检查8001端口是否在监听
netstat -tlnp | grep :8001

# 测试连接
curl http://localhost:8001/
```

### 步骤2：停止8000端口，确保8001端口运行

```bash
# 停止8000端口
pkill -f "runserver.*8000"

# 确保8001端口运行
cd /home/devbox/project/vihhi/weihai_tech_production_system
source venv/bin/activate
python manage.py runserver 0.0.0.0:8001
```

### 步骤3：在浏览器中访问

1. **打开新标签页**
2. **输入地址**：`http://localhost:8001/`（注意是http，不是https）
3. **如果还是有问题**：
   - 清除浏览器缓存（Ctrl+Shift+Delete）
   - 使用无痕模式（Ctrl+Shift+N）
   - 或更换浏览器

## 📋 正确的访问地址

### 本地开发访问（HTTP）
- **首页**: http://localhost:8001/
- **登录页**: http://localhost:8001/login/
- **交付管理**: http://localhost:8001/delivery/
- **Django Admin**: http://localhost:8001/admin/

### Sealos公网访问（HTTPS）
- **首页**: https://tivpdkrxyioz.sealosbja.site/
- **交付管理**: https://tivpdkrxyioz.sealosbja.site/delivery/

## 🔍 验证服务器状态

### 检查服务器是否运行
```bash
# 检查8001端口进程
ps aux | grep "runserver.*8001"

# 检查端口监听
netstat -tlnp | grep :8001
# 或
ss -tlnp | grep :8001

# 测试HTTP连接
curl -v http://localhost:8001/
```

### 如果8001端口没有运行，启动它：
```bash
cd /home/devbox/project/vihhi/weihai_tech_production_system
source venv/bin/activate
python manage.py runserver 0.0.0.0:8001
```

## ⚠️ 重要提示

1. **使用正确的端口**：8001（不是8000）
2. **使用HTTP协议**：`http://`（不是https）
3. **浏览器兼容性**：如果360浏览器有问题，建议使用Chrome或Firefox
4. **公网访问**：如果本地访问有问题，使用Sealos公网地址

## 🎯 推荐操作

1. **停止8000端口服务器**（如果不需要）
2. **确保8001端口服务器运行**
3. **使用Chrome浏览器访问**：http://localhost:8001/
4. **或者使用Sealos公网地址**：https://tivpdkrxyioz.sealosbja.site/

---

**总结**：使用 `http://localhost:8001/` 访问，如果360浏览器有问题，建议使用Chrome浏览器或Sealos公网地址。

