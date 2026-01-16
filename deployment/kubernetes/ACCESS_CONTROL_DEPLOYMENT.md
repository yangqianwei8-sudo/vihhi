# 访问控制三重锁部署指南

## 概述

本文档说明如何部署**三重锁访问控制**，确保 backend 服务只能通过公网域名 `hrozezgtxwhk.sealosbja.site` 访问，禁止所有内部访问路径。

---

## 三重锁说明

### 🔒 第一把锁：NetworkPolicy（集群层硬隔离）
- **目标**：只有 Ingress Controller 能访问 backend Service
- **文件**：`backend-networkpolicy.yaml`
- **效果**：拒绝集群内其他 Pod 直接访问 backend

### 🔒 第二把锁：HostGuardMiddleware（应用层防护）
- **目标**：严格验证请求的 Host 头
- **文件**：`backend/config/middleware.py`
- **效果**：拒绝所有非指定域名的请求（包括 Service IP、Pod IP、内部域名）

### 🔒 第三把锁：Django ALLOWED_HOSTS（Django 内置防护）
- **目标**：Django 框架层面的 Host 验证
- **文件**：`backend/config/settings.py`
- **效果**：Django 自动拒绝不在 ALLOWED_HOSTS 中的请求

---

## 部署步骤

### 步骤 1：确认 NetworkPolicy 支持

```bash
# 检查集群是否支持 NetworkPolicy
kubectl api-resources | grep networkpolicies

# 如果返回 networkpolicies，说明支持
# 如果不支持，跳过步骤 2，只使用应用层防护（第二、三把锁）
```

### 步骤 2：应用 NetworkPolicy（如果支持）

```bash
# 查看 Ingress Controller 所在的 namespace 和标签
kubectl get namespaces --show-labels | grep -i ingress
kubectl get pods -n <ingress-namespace> --show-labels | grep -i ingress

# 根据实际情况修改 backend-networkpolicy.yaml 中的 namespaceSelector
# 然后应用
kubectl apply -f deployment/kubernetes/backend-networkpolicy.yaml

# 验证
kubectl get networkpolicy -n ns-dqyh88ke
```

**注意**：如果 Sealos 平台不支持 NetworkPolicy，此步骤会失败，但不影响应用层防护。

### 步骤 3：更新代码并构建新镜像

```bash
# 1. 确认代码已更新（settings.py, middleware.py）
cd /home/devbox/project/vihhi/weihai_tech_production_system

# 2. 构建新镜像（使用版本 tag，不要 latest）
export TAG=$(date +%Y%m%d)-01
docker build -t yqwlhl/backend:$TAG -f deployment/docker/Dockerfile.backend .

# 3. 推送镜像
docker push yqwlhl/backend:$TAG
```

### 步骤 4：更新 Deployment

```bash
# 更新镜像
kubectl set image -n ns-dqyh88ke deploy/backend backend=yqwlhl/backend:$TAG

# 等待 rollout 完成
kubectl rollout status -n ns-dqyh88ke deploy/backend

# 查看新 Pod
kubectl get pods -n ns-dqyh88ke -l app=backend
```

### 步骤 5：验证访问控制

```bash
# ✅ 应该成功：通过公网域名访问
curl -I https://hrozezgtxwhk.sealosbja.site/admin/login/

# ❌ 应该失败：通过 Service IP 访问（如果 NetworkPolicy 生效）
# 获取 Service IP
SERVICE_IP=$(kubectl get svc -n ns-dqyh88ke -l app=backend -o jsonpath='{.items[0].spec.clusterIP}')
# 从集群内 Pod 测试（应该被拒绝）
kubectl run test-pod --image=curlimages/curl --rm -it --restart=Never -n ns-dqyh88ke -- \
  curl -v http://$SERVICE_IP:8000/admin/login/

# ❌ 应该失败：使用错误的 Host 头
curl -H "Host: backend-service.ns-dqyh88ke.svc.cluster.local" \
  https://hrozezgtxwhk.sealosbja.site/admin/login/
```

---

## 配置说明

### NetworkPolicy 配置调整

如果 NetworkPolicy 无法匹配 Ingress Controller，需要调整 `backend-networkpolicy.yaml`：

```yaml
# 方式1：通过 namespace 标签匹配
- from:
  - namespaceSelector:
      matchLabels:
        name: ingress-nginx  # 修改为实际的 namespace 标签

# 方式2：通过 Pod 标签匹配
- from:
  - namespaceSelector: {}
    podSelector:
      matchLabels:
        app.kubernetes.io/name: ingress-nginx  # 修改为实际的 Pod 标签
```

### 环境变量配置

确保在 Deployment 中设置正确的环境变量：

```yaml
env:
  - name: ALLOWED_HOSTS
    value: "hrozezgtxwhk.sealosbja.site"
  - name: CSRF_TRUSTED_ORIGINS
    value: "https://hrozezgtxwhk.sealosbja.site,http://hrozezgtxwhk.sealosbja.site"
```

---

## 故障排查

### 问题 1：NetworkPolicy 无法应用

**原因**：平台不支持 NetworkPolicy

**解决**：跳过 NetworkPolicy，依赖应用层防护（第二、三把锁）已经足够。

### 问题 2：公网访问被拒绝

**检查**：
1. 确认 `ALLOWED_HOSTS` 环境变量包含 `hrozezgtxwhk.sealosbja.site`
2. 查看 Pod 日志：`kubectl logs -n ns-dqyh88ke -l app=backend | grep HostGuardMiddleware`
3. 确认 Ingress 配置正确

### 问题 3：健康检查失败

**原因**：HostGuardMiddleware 可能阻止了健康检查

**解决**：健康检查路径（`/__health`, `/health`, `/healthz`）已自动放行，无需额外配置。

---

## 安全效果

部署完成后：

✅ **公网域名访问**：正常
- `https://hrozezgtxwhk.sealosbja.site/*`

❌ **内部访问被拒绝**：
- Service IP 直连
- Pod IP 直连
- 内部域名访问
- 错误的 Host 头

---

## 回滚方案

如果需要回滚：

```bash
# 1. 删除 NetworkPolicy
kubectl delete networkpolicy backend-only-from-ingress -n ns-dqyh88ke

# 2. 回滚到旧镜像
kubectl rollout undo -n ns-dqyh88ke deploy/backend

# 3. 如果需要，修改 settings.py 恢复旧的 ALLOWED_HOSTS
```

---

## 注意事项

1. **永远不要使用 latest tag**：使用日期+序号版本号
2. **NetworkPolicy 是可选的**：如果平台不支持，应用层防护已经足够
3. **健康检查路径已放行**：`/__health`, `/health`, `/healthz`, `/ready`, `/readiness`
4. **日志记录**：所有被拒绝的请求都会记录到日志中，便于安全审计
