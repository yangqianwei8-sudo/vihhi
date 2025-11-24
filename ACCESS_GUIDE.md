# 🌐 访问指南

## 🔍 问题诊断

根据您的Sealos配置，服务器应该运行在 **8001端口**，而不是8000端口。

## ✅ 正确的访问方式

### 方式1：本地访问（开发用）

**使用 HTTP 协议**（不是 HTTPS）：
- ✅ http://localhost:8001/
- ✅ http://127.0.0.1:8001/

**重要**：不要使用 `https://`，Django开发服务器不支持HTTPS。

### 方式2：Sealos内网访问

根据您的配置：
- **内网地址**: http://my-devbox.ns-dqyh88ke:8001

### 方式3：Sealos公网访问

- **公网地址**: https://tivpdkrxyioz.sealosbja.site

**注意**：公网地址使用HTTPS，这是由Sealos平台提供的SSL证书。

## 🚀 启动服务器

### 启动8001端口的服务器

```bash
cd /home/devbox/project/vihhi/weihai_tech_production_system
source venv/bin/activate
python manage.py runserver 0.0.0.0:8001
```

### 后台运行（推荐）

```bash
cd /home/devbox/project/vihhi/weihai_tech_production_system
source venv/bin/activate
nohup python manage.py runserver 0.0.0.0:8001 > /tmp/django_server_8001.log 2>&1 &
```

## 🔧 常见问题解决

### 1. SSL协议错误

**错误**: `ERR_SSL_PROTOCOL_ERROR`

**原因**: 使用HTTPS访问了只支持HTTP的本地服务器

**解决**: 
- 本地访问使用：`http://localhost:8001/`（注意是http，不是https）
- 公网访问使用：`https://tivpdkrxyioz.sealosbja.site`（Sealos提供的HTTPS）

### 2. 端口不匹配

**问题**: 服务器运行在8000端口，但Sealos配置的是8001端口

**解决**: 
```bash
# 停止8000端口的服务器
pkill -f "runserver.*8000"

# 启动8001端口的服务器
python manage.py runserver 0.0.0.0:8001
```

### 3. 浏览器缓存问题

**解决**:
1. 清除浏览器缓存（Ctrl+Shift+Delete）
2. 使用无痕模式访问
3. 或者强制刷新（Ctrl+F5）

### 4. 连接被拒绝

**检查服务器是否运行**:
```bash
ps aux | grep "runserver.*8001"
netstat -tlnp | grep :8001
```

**重启服务器**:
```bash
pkill -f "runserver.*8001"
python manage.py runserver 0.0.0.0:8001
```

## 📋 访问地址列表

### 本地开发访问
- **首页**: http://localhost:8001/
- **登录页**: http://localhost:8001/login/
- **交付管理**: http://localhost:8001/delivery/
- **Django Admin**: http://localhost:8001/admin/

### API接口
- **交付记录**: http://localhost:8001/api/delivery/delivery/
- **交付文件**: http://localhost:8001/api/delivery/files/
- **交付统计**: http://localhost:8001/api/delivery/delivery/statistics/
- **交付预警**: http://localhost:8001/api/delivery/delivery/warnings/

### Sealos公网访问
- **首页**: https://tivpdkrxyioz.sealosbja.site/
- **交付管理**: https://tivpdkrxyioz.sealosbja.site/delivery/

## 🔍 验证服务器状态

### 检查服务器是否运行
```bash
# 检查进程
ps aux | grep "runserver.*8001"

# 检查端口
netstat -tlnp | grep :8001
# 或
ss -tlnp | grep :8001

# 测试连接
curl http://localhost:8001/
```

### 查看服务器日志
```bash
# 如果使用nohup后台运行
tail -f /tmp/django_server_8001.log

# 或者查看Django输出
# 如果在前台运行，日志会直接显示在终端
```

## ⚠️ 重要提示

1. **本地访问**: 使用 `http://`（不是https）
2. **公网访问**: 使用 `https://`（Sealos提供SSL）
3. **端口匹配**: 确保服务器运行在Sealos配置的端口（8001）
4. **防火墙**: 确保Sealos平台已正确配置端口映射

## 🎯 快速修复步骤

1. **确认端口**:
   ```bash
   netstat -tlnp | grep :8001
   ```

2. **启动/重启服务器**:
   ```bash
   pkill -f "runserver.*8001"
   cd /home/devbox/project/vihhi/weihai_tech_production_system
   source venv/bin/activate
   python manage.py runserver 0.0.0.0:8001
   ```

3. **测试访问**:
   ```bash
   curl http://localhost:8001/
   ```

4. **浏览器访问**:
   - 打开浏览器
   - 访问：http://localhost:8001/
   - 或访问：https://tivpdkrxyioz.sealosbja.site/

---

**总结**: 使用 `http://localhost:8001/` 访问本地服务器，或使用 `https://tivpdkrxyioz.sealosbja.site/` 访问公网地址。

