# 构建并部署新镜像（永久消灭旧版 Vue SPA）

## 问题确认
- ✅ 代码已修改完成（views.py, settings.py, urls.py）
- ❌ Pod 重启后改动丢失（文件在镜像层，不在挂载卷）
- ✅ 必须构建新镜像才能永久生效

## 构建步骤（在本地有 Docker 的机器执行）

### 1. 准备环境
```bash
# 确保本地有 Docker Desktop 或 Docker Engine
docker --version

# 确保已登录 Docker Hub（或你的镜像仓库）
docker login
```

### 2. 获取代码
```bash
# 方式1：从 Git 仓库克隆
git clone <your-repo-url>
cd vihhi/weihai_tech_production_system

# 方式2：从 DevBox 打包下载
# 在 DevBox 执行：
# tar -czf code.tar.gz vihhi/weihai_tech_production_system/
# 然后下载到本地解压
```

### 3. 构建镜像（使用版本 tag，不要 latest）
```bash
cd vihhi/weihai_tech_production_system

# 设置版本 tag（日期+序号）
export TAG=20260113-01

# 构建镜像
docker build -t yqwlhl/backend:$TAG -f deployment/docker/Dockerfile.backend .

# 验证镜像
docker images | grep yqwlhl/backend
```

### 4. 推送镜像
```bash
docker push yqwlhl/backend:$TAG
```

### 5. 更新 K8s Deployment
```bash
# 更新镜像
kubectl set image -n ns-dqyh88ke deploy/backend backend=yqwlhl/backend:20260113-01

# 等待 rollout 完成
kubectl rollout status -n ns-dqyh88ke deploy/backend

# 查看新 Pod
kubectl get pods -n ns-dqyh88ke -l app=backend
```

### 6. 验证（旧版 Vue SPA 必须消失）
```bash
# 应该返回 302 重定向到 /admin/login/
curl -I https://hrozezgtxwhk.sealosbja.site/login/

# 应该找不到 chunk-vendors 或 app.db
curl -L https://hrozezgtxwhk.sealosbja.site/login/ | grep -i "chunk-vendors\|app\.db" || echo "✅ 未找到 Vue SPA 痕迹"
```

## 关键文件修改摘要

### backend/core/views.py
- `login_view`: 不再返回 `frontend/dist/index.html`，改为重定向到 `/admin/login/`
- `home`: 未登录时重定向到 `/admin/login/`

### backend/config/settings.py
- `LOGIN_URL`: 从 `/login/` 改为 `/admin/login/`

### backend/config/urls.py
- 注释掉前端静态资源服务（js/css/img）

## 注意事项
1. **永远不要使用 latest tag**：使用日期+序号版本号
2. **构建前确认代码已提交**：确保本地代码包含所有修改
3. **验证后再删除旧镜像**：保留旧版本以便回滚
