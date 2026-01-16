# 快速构建指南

## ✅ 代码路径确认

**正确的项目根目录：**
```bash
/home/devbox/project/vihhi/weihai_tech_production_system
```

**验证文件存在：**
```bash
cd /home/devbox/project/vihhi/weihai_tech_production_system
ls deployment/docker/Dockerfile.backend
ls backend/core/views.py
```

## 📦 打包文件已准备

- **位置**: `/tmp/weihai_tech_production_system.tar.gz` (820M)
- **HTTP 下载**: `http://10.107.254.178:8009/weihai_tech_production_system.tar.gz`

## 🖥️ Windows 本机操作

### 1. 下载源码
在 Windows 浏览器或 PowerShell：
```
http://10.107.254.178:8009/weihai_tech_production_system.tar.gz
```

### 2. 解压
```powershell
cd C:\Users\admin
mkdir weihai_tech_production_system -Force
wsl tar -xzf Downloads/weihai_tech_production_system.tar.gz -C weihai_tech_production_system
cd weihai_tech_production_system
dir deployment\docker\Dockerfile.backend
```

### 3. 构建镜像
```powershell
$env:TAG="20260113-02"
docker build -t yqwlhl/backend:$env:TAG -f deployment\docker\Dockerfile.backend .
docker push yqwlhl/backend:$env:TAG
```

### 4. 更新 Deployment
```powershell
kubectl set image -n ns-dqyh88ke deploy/backend backend=yqwlhl/backend:20260113-02
kubectl rollout status -n ns-dqyh88ke deploy/backend
```

### 5. 验证
```powershell
curl.exe -I https://hrozezgtxwhk.sealosbja.site/login/
# 应该返回 302 Location: /admin/login/
```

## ✅ 代码修改确认

- ✅ `backend/core/views.py` - login_view 重定向到 /admin/login/
- ✅ `backend/config/settings.py` - LOGIN_URL = '/admin/login/'
- ✅ `backend/config/urls.py` - 前端静态资源服务已注释
