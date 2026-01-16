# 构建新镜像步骤（Windows PowerShell）

## 0. 先止血：恢复可用镜像（已完成）
```powershell
kubectl set image -n ns-dqyh88ke deploy/backend backend=yqwlhl/backend:latest
kubectl rollout status -n ns-dqyh88ke deploy/backend
```

## 1. 准备代码（选择一种方式）

### 方式 A：从 Git 克隆（如果有仓库）
```powershell
cd C:\Users\admin
git clone <你的仓库地址> weihai_tech_production_system
cd .\weihai_tech_production_system
dir deployment\docker\Dockerfile.backend
```

### 方式 B：从 DevBox 下载（如果只有 DevBox 有代码）
1. 在 DevBox 已打包：`/tmp/weihai_tech_production_system.tar.gz`
2. 下载到 Windows：`C:\Users\admin\weihai_tech_production_system.tar.gz`
3. 解压：
```powershell
cd C:\Users\admin
# 使用 7-Zip 或 WinRAR 解压 tar.gz
# 或使用 WSL：
wsl tar -xzf weihai_tech_production_system.tar.gz
cd weihai_tech_production_system
dir deployment\docker\Dockerfile.backend
```

## 2. 构建镜像
```powershell
# 进入项目根目录
cd C:\Users\admin\weihai_tech_production_system

# 设置版本 tag
$env:TAG="20260113-01"

# 构建镜像
docker build -t yqwlhl/backend:$env:TAG -f deployment/docker/Dockerfile.backend .

# 验证镜像
docker images | Select-String "yqwlhl/backend"
```

## 3. 推送镜像
```powershell
# 确保已登录 Docker Hub
docker login

# 推送镜像
docker push yqwlhl/backend:$env:TAG
```

## 4. 更新 Deployment
```powershell
# 更新镜像
kubectl set image -n ns-dqyh88ke deploy/backend backend=yqwlhl/backend:20260113-01

# 等待 rollout 完成
kubectl rollout status -n ns-dqyh88ke deploy/backend

# 查看新 Pod
kubectl get pods -n ns-dqyh88ke -l app=backend
```

## 5. 验证（旧版 Vue SPA 必须消失）
```powershell
# 应该返回 302 重定向到 /admin/login/
curl.exe -I https://hrozezgtxwhk.sealosbja.site/login/

# 应该找不到 chunk-vendors
curl.exe -L https://hrozezgtxwhk.sealosbja.site/login/ | findstr /i "chunk-vendors app.db"
# 预期：无输出（找不到）
```

## 关键文件修改摘要
- ✅ `backend/core/views.py` - login_view 重定向到 /admin/login/
- ✅ `backend/config/settings.py` - LOGIN_URL = '/admin/login/'
- ✅ `backend/config/urls.py` - 前端静态资源服务已注释

## 注意事项
1. **不要使用 latest tag**：使用日期版本号（20260113-01）
2. **构建前确认代码已提交**：确保包含所有修改
3. **验证后再删除旧镜像**：保留旧版本以便回滚
