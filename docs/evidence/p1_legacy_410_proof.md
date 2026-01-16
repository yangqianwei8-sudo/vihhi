# P1 Legacy Endpoints 退役 HTTP 410 证据

## 测试接口
POST /api/plan/plans/36/approve/

## 测试时间
2026-01-13

## 证据（原始响应）

```
HTTP/1.1 410 Gone
Date: Tue, 13 Jan 2026 03:34:05 GMT
Server: WSGIServer/0.2 CPython/3.11.11
Content-Type: application/json
Vary: Accept, Cookie, origin
Allow: POST, OPTIONS
X-Frame-Options: DENY
Content-Length: 228
X-Content-Type-Options: nosniff
Referrer-Policy: same-origin
Cross-Origin-Opener-Policy: same-origin

{
  "success": false,
  "code": "LEGACY_ENDPOINT_GONE",
  "message": "P1 v2 已启用 PlanDecision 裁决机制，旧审批/手动状态变更接口已退役。请使用 /start-request/ /cancel-request/ 与 /plan-decisions/{id}/decide/。"
}
```

## 验证结果
✅ 状态码：HTTP/1.1 410 Gone
✅ JSON body 包含：`"code": "LEGACY_ENDPOINT_GONE"`
✅ 消息明确说明接口已退役，并提供迁移路径

## 相关接口
以下 9 个接口均已退役，统一返回 410 Gone：

### PlanViewSet
- POST /api/plan/plans/{id}/change_status/
- POST /api/plan/plans/{id}/submit_approval/
- POST /api/plan/plans/{id}/approve/
- POST /api/plan/plans/{id}/reject/
- POST /api/plan/plans/{id}/cancel_approval/

### StrategicGoalViewSet
- POST /api/plan/strategic-goals/{id}/submit_approval/
- POST /api/plan/strategic-goals/{id}/approve/
- POST /api/plan/strategic-goals/{id}/reject/
- POST /api/plan/strategic-goals/{id}/cancel_approval/
