# 🔧 故障排查指南

## ✅ 当前状态检查

### 服务器状态
- ✅ Django服务器：运行中（8001端口）
- ✅ PostgreSQL数据库：连接成功
- ✅ HTTP响应：302（正常，重定向到登录页）

### 数据库配置
- ✅ 使用PostgreSQL数据库
- ✅ 连接地址：dbconn.sealosbja.site:38013
- ✅ 数据库版本：PostgreSQL 14.17

## 🔍 如果 http://localhost:8001/ 打不开

### 1. 检查服务器是否运行

```bash
# 检查进程
ps aux | grep "runserver.*8001"

# 检查端口
netstat -tlnp | grep :8001
```

### 2. 测试连接

```bash
# 测试HTTP连接
curl http://localhost:8001/

# 应该返回302（重定向到登录页）
```

### 3. 浏览器问题排查

**清除浏览器缓存**：
- 按 `Ctrl+Shift+Delete`
- 清除缓存和Cookie
- 或使用无痕模式（`Ctrl+Shift+N`）

**检查地址栏**：
- 确保是 `http://localhost:8001/`（不是https）
- 确保端口是8001（不是8000或8080）

**强制刷新**：
- 按 `Ctrl+F5` 强制刷新页面

### 4. 检查数据库连接

```bash
cd /home/devbox/project/vihhi/weihai_tech_production_system
source venv/bin/activate
python manage.py check --database default
```

### 5. 查看服务器日志

如果服务器在前台运行，查看终端输出。

如果服务器在后台运行：
```bash
# 查看Django日志
tail -f /tmp/django_server.log
```

### 6. 重启服务器

```bash
# 停止服务器
pkill -f "runserver.*8001"

# 重新启动
cd /home/devbox/project/vihhi/weihai_tech_production_system
source venv/bin/activate
python manage.py runserver 0.0.0.0:8001
```

## 🌐 访问地址

### 正确的访问地址

- **首页**: http://localhost:8001/
- **登录页**: http://localhost:8001/login/
- **交付管理**: http://localhost:8001/delivery/

### 错误的访问地址

- ❌ https://localhost:8001/ （Django开发服务器不支持HTTPS）
- ❌ http://localhost:8000/ （端口不对）
- ❌ http://localhost:8080/ （这是Vue前端，不是实际系统）

## 🔑 登录信息

如果需要创建用户：

```bash
cd /home/devbox/project/vihhi/weihai_tech_production_system
source venv/bin/activate
python manage.py createsuperuser
```

## 📋 常见错误

### 1. ERR_CONNECTION_REFUSED
- **原因**: 服务器没有运行
- **解决**: 启动服务器

### 2. ERR_SSL_PROTOCOL_ERROR
- **原因**: 使用HTTPS访问HTTP服务器
- **解决**: 使用 `http://` 而不是 `https://`

### 3. 页面空白或404
- **原因**: 浏览器缓存或路由问题
- **解决**: 清除缓存，使用无痕模式

### 4. 数据库连接错误
- **原因**: PostgreSQL连接失败
- **解决**: 检查数据库配置和网络连接

## 🎯 快速验证

运行以下命令验证系统状态：

```bash
# 1. 检查服务器
curl -I http://localhost:8001/

# 2. 检查数据库
python manage.py check --database default

# 3. 检查迁移
python manage.py showmigrations
```

## 📞 如果仍然无法访问

1. **检查防火墙**：确保8001端口没有被阻止
2. **检查网络**：确保localhost解析正常
3. **查看错误日志**：检查Django输出或日志文件
4. **尝试其他浏览器**：排除浏览器问题

---

**当前状态**：服务器和数据库都正常，如果打不开，很可能是浏览器缓存或访问地址问题。

