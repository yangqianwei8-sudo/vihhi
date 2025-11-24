# 🚀 前端服务器启动指南

## 📋 项目架构

这个项目采用**前后端分离**架构：
- **后端（Django）**: 运行在 8001 端口，提供 API 接口
- **前端（Vue.js）**: 运行在 8080 端口，提供用户界面

## ✅ 启动步骤

### 1. 启动后端服务器（Django）

```bash
cd /home/devbox/project/vihhi/weihai_tech_production_system
source venv/bin/activate
python manage.py runserver 0.0.0.0:8001
```

**访问地址**: http://localhost:8001/

### 2. 启动前端服务器（Vue.js）

```bash
cd /home/devbox/project/vihhi/weihai_tech_production_system/frontend
npm run dev
```

**访问地址**: http://localhost:8080/

## 🌐 访问地址

### 开发环境

- **前端界面**: http://localhost:8080/ （Vue.js开发服务器）
- **后端API**: http://localhost:8001/ （Django开发服务器）
- **Django Admin**: http://localhost:8001/admin/

### Sealos公网访问

- **前端界面**: https://tivpdkrxyioz.sealosbja.site/ （如果配置了前端部署）
- **后端API**: https://tivpdkrxyioz.sealosbja.site/api/

## 🔧 前端项目信息

- **框架**: Vue.js 3.3.0
- **UI库**: Element Plus 2.3.0
- **状态管理**: Vuex 4.1.0
- **路由**: Vue Router 4.2.0
- **HTTP客户端**: Axios 1.4.0
- **图表库**: ECharts 5.4.0

## 📝 常用命令

### 前端开发

```bash
# 启动开发服务器
cd frontend
npm run dev

# 构建生产版本
npm run build

# 代码检查
npm run lint
```

### 后端开发

```bash
# 启动开发服务器
cd /home/devbox/project/vihhi/weihai_tech_production_system
source venv/bin/activate
python manage.py runserver 0.0.0.0:8001

# 运行数据库迁移
python manage.py migrate

# 创建超级用户
python manage.py createsuperuser
```

## 🔍 检查服务状态

### 检查后端（8001端口）

```bash
# 检查进程
ps aux | grep "runserver.*8001"

# 检查端口
netstat -tlnp | grep :8001

# 测试连接
curl http://localhost:8001/
```

### 检查前端（8080端口）

```bash
# 检查进程
ps aux | grep "vue-cli-service\|npm.*dev"

# 检查端口
netstat -tlnp | grep :8080

# 测试连接
curl http://localhost:8080/
```

## ⚠️ 注意事项

1. **两个服务器都需要运行**：
   - 前端服务器（8080）提供用户界面
   - 后端服务器（8001）提供API接口

2. **CORS配置**：
   - Django后端已配置CORS，允许来自8080端口的请求

3. **开发模式**：
   - 前端使用Vue CLI开发服务器（热重载）
   - 后端使用Django开发服务器（自动重载）

4. **生产环境**：
   - 前端需要构建：`npm run build`
   - 构建后的文件会放在 `frontend/dist/` 目录
   - Django需要配置静态文件服务

## 🎯 快速启动脚本

创建 `start_dev.sh`：

```bash
#!/bin/bash

# 启动后端
cd /home/devbox/project/vihhi/weihai_tech_production_system
source venv/bin/activate
python manage.py runserver 0.0.0.0:8001 > /tmp/django_server.log 2>&1 &

# 启动前端
cd frontend
npm run dev > /tmp/vue_server.log 2>&1 &

echo "✅ 后端服务器: http://localhost:8001/"
echo "✅ 前端服务器: http://localhost:8080/"
echo "📋 查看日志: tail -f /tmp/django_server.log /tmp/vue_server.log"
```

---

**总结**: 访问 **http://localhost:8080/** 使用前端界面，后端API在 **http://localhost:8001/** 运行。

