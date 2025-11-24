# 🚀 Django服务器运行状态

## ✅ 服务器状态

**服务器已成功启动！**

### 运行中的服务器实例

1. **端口 8000** ✅
   - 状态：运行中
   - 访问地址：
     - 本地：http://localhost:8000
     - 局域网：http://0.0.0.0:8000
   - 进程ID：23491

2. **端口 8001** ✅
   - 状态：运行中（之前启动的实例）
   - 访问地址：
     - 本地：http://localhost:8001
     - 局域网：http://0.0.0.0:8001
   - 进程ID：9661

## 📋 访问地址

### 主要页面
- **首页**: http://localhost:8000/
- **登录页**: http://localhost:8000/login/
- **交付管理**: http://localhost:8000/delivery/
- **Django Admin**: http://localhost:8000/admin/

### API接口
- **交付管理API**: http://localhost:8000/api/delivery/delivery/
- **交付文件API**: http://localhost:8000/api/delivery/files/
- **交付统计API**: http://localhost:8000/api/delivery/delivery/statistics/
- **交付预警API**: http://localhost:8000/api/delivery/delivery/warnings/

## 🔧 服务器管理命令

### 查看服务器进程
```bash
ps aux | grep "manage.py runserver"
```

### 停止服务器
```bash
# 停止8000端口的服务器
pkill -f "runserver 0.0.0.0:8000"

# 停止8001端口的服务器
pkill -f "runserver 0.0.0.0:8001"

# 停止所有Django服务器
pkill -f "manage.py runserver"
```

### 重启服务器
```bash
cd /home/devbox/project/vihhi/weihai_tech_production_system
source venv/bin/activate
python manage.py runserver 0.0.0.0:8000
```

### 后台运行服务器（带日志）
```bash
cd /home/devbox/project/vihhi/weihai_tech_production_system
source venv/bin/activate
nohup python manage.py runserver 0.0.0.0:8000 > /tmp/django_server.log 2>&1 &
```

### 查看服务器日志
```bash
tail -f /tmp/django_server.log
```

## 📊 系统检查

- ✅ Django系统检查：通过（0个问题）
- ✅ 数据库连接：正常
- ✅ 交付管理模块：4个表已创建
- ✅ 静态文件：已配置
- ✅ 媒体文件：已配置

## 🔍 调试信息

### 检查端口占用
```bash
netstat -tlnp | grep :8000
# 或
ss -tlnp | grep :8000
```

### 查看Django配置
```bash
python manage.py check
python manage.py check --deploy
```

### 查看数据库连接
```bash
python manage.py dbshell
```

## ⚠️ 注意事项

1. **多个服务器实例**：当前有2个服务器在运行（8000和8001端口），建议只保留一个
2. **开发模式**：当前运行在DEBUG模式下，适合开发使用
3. **数据库**：使用PostgreSQL生产数据库，请谨慎操作
4. **静态文件**：开发模式下会自动服务静态文件

## 🎯 快速测试

### 测试首页
```bash
curl http://localhost:8000/
```

### 测试API
```bash
curl http://localhost:8000/api/delivery/delivery/
```

### 测试交付管理页面
```bash
curl http://localhost:8000/delivery/
```

---

**更新时间**: 2024-11-23  
**状态**: ✅ 服务器运行正常

