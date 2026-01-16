# P1 PlanDecision v2 稳态验收清单

## ⚠️ P1 规则：Plan.status 只允许在以下写入点发生改变

**不可推翻条款：**

1. **PlanDecision `decide(approve)`** - 裁决器修改状态
2. **`recalc_plan_status()` 系统完成** - 进度>=100自动完成

**其它入口一律视为违规（必须返回 410/409）**

---

## 核心设计原则

### 1. 4 态制状态机
- `draft`（草稿）
- `in_progress`（执行中）
- `completed`（已完成）
- `cancelled`（已取消）

**状态变更规则：**
- `draft` → `in_progress`：必须通过 `start-request` + `decide(approve=True)`
- `in_progress` → `cancelled`：必须通过 `cancel-request` + `decide(approve=True)`
- `in_progress` → `completed`：系统自动判定（`progress >= 100`）
- **禁止直接修改 `Plan.status`**：只能通过裁决接口修改

### 2. PlanDecision 模型约束

**字段：**
- `plan`：关联的计划
- `request_type`：请求类型（`start` / `cancel`）
- `decision`：决策结果（`approve` / `reject` / `null`）
- `requested_by`：请求人
- `decided_by`：决策人
- `requested_at`：请求时间
- `decided_at`：决策时间（`null` 表示 pending）
- `reason`：原因说明

**唯一约束：**
- 每个计划、每个请求类型，**只能有一个 pending 决策**（`decided_at__isnull=True`）
- 已裁决的决策（`decided_at` 非空）不影响唯一约束

### 3. API 端点

#### 3.1 发起请求
- `POST /api/plan/plans/{id}/start-request/`：发起启动请求
- `POST /api/plan/plans/{id}/cancel-request/`：发起取消请求
- **返回：** `201 Created`（创建了新的 pending decision）

#### 3.2 裁决决策
- `POST /api/plan/plan-decisions/{decision_id}/decide/`
- **Body：** `{"approve": true/false, "reason": "可选"}`
- **返回：** `200 OK`

#### 3.3 决策列表（只读）
- `GET /api/plan/plan-decisions/?plan={id}&pending=1`
- **过滤：** `pending=1` 等价于 `decided_at__isnull=True`
- **排序：** 默认按 `-requested_at`

### 4. 系统完成判定

**触发条件：**
- `plan.status == "in_progress"`
- `plan.progress >= 100`

**实现位置：**
- `backend/apps/plan_management/services/recalc_status.py::recalc_plan_status()`
- 通过裁决器处理：`adjudicate_plan_status(plan, decision=None, system_facts={'all_tasks_completed': True})`

**调用时机：**
- 进度更新时自动调用
- 任务完成时自动调用

### 5. 三层测试命令

#### 5.1 系统检查
```bash
python manage.py check
```

#### 5.2 单元测试
```bash
DJANGO_SETTINGS_MODULE=backend.config.settings_test \
python manage.py test backend.apps.plan_management.tests.test_plan_decision_v2 -v 2
```

#### 5.3 接口闭环测试
```bash
# 1. 登录
curl -c /tmp/c.txt -X POST 'http://127.0.0.1:8001/api/system/users/login/' \
  -H 'Content-Type: application/json' \
  -d '{"username":"admin","password":"admin123456"}'

# 2. 发起 start_request
curl -b /tmp/c.txt -X POST \
  http://127.0.0.1:8001/api/plan/plans/{PLAN_ID}/start-request/ \
  -H "Content-Type: application/json" \
  -H "X-CSRFToken: $(grep csrftoken /tmp/c.txt | awk '{print $7}')" \
  -d '{"reason":"start test"}'

# 3. 裁决 reject
curl -b /tmp/c.txt -X POST \
  http://127.0.0.1:8001/api/plan/plan-decisions/{DECISION_ID}/decide/ \
  -H "Content-Type: application/json" \
  -H "X-CSRFToken: $(grep csrftoken /tmp/c.txt | awk '{print $7}')" \
  -d '{"approve": false, "reason":"reject test"}'

# 4. 再发起 start_request（reject 后允许重新发起）
curl -b /tmp/c.txt -X POST \
  http://127.0.0.1:8001/api/plan/plans/{PLAN_ID}/start-request/ \
  -H "Content-Type: application/json" \
  -H "X-CSRFToken: $(grep csrftoken /tmp/c.txt | awk '{print $7}')" \
  -d '{"reason":"start after reject"}'

# 5. 裁决 approve
curl -b /tmp/c.txt -X POST \
  http://127.0.0.1:8001/api/plan/plan-decisions/{NEW_DECISION_ID}/decide/ \
  -H "Content-Type: application/json" \
  -H "X-CSRFToken: $(grep csrftoken /tmp/c.txt | awk '{print $7}')" \
  -d '{"approve": true, "reason":"approve start"}'

# 6. 查询 pending 列表
curl -b /tmp/c.txt \
  "http://127.0.0.1:8001/api/plan/plan-decisions/?plan={PLAN_ID}&pending=1" \
  -H "X-CSRFToken: $(grep csrftoken /tmp/c.txt | awk '{print $7}')"
```

### 6. 验收标准

- ✅ `start_request` 第一次：返回 `201 Created`，包含 `decision_id`
- ✅ 重复 `start_request`：返回 `400 Bad Request`，提示"已有 pending 请求"
- ✅ `reject`：返回 `200 OK`，`plan_status` 保持原状态（`draft`）
- ✅ `approve start`：返回 `200 OK`，`plan_status` 变为 `in_progress`
- ✅ `pending=1` 过滤：只返回 `decided_at` 为 `null` 的记录
- ✅ `progress >= 100`：系统自动将 `in_progress` → `completed`

### 7. 禁止事项

- ❌ **禁止直接修改 `Plan.status`**：必须通过裁决接口
- ❌ **禁止绕过唯一约束**：同一计划、同一请求类型不能有多个 pending 决策
- ❌ **禁止在 `in_progress` 状态下发起 `start_request`**
- ❌ **禁止在非 `in_progress` 状态下发起 `cancel_request`**

### 8. Legacy Endpoints (Deprecated, returns 410 Gone)

**P1 v2 已启用 PlanDecision 裁决机制，以下旧接口已退役，统一返回 `410 Gone`：**

> **证据文档：** 完整的 HTTP 410 响应证据已保存在 `docs/evidence/p1_legacy_410_proof.md`

#### 8.1 PlanViewSet 退役接口

- `POST /api/plan/plans/{id}/change-status/` - 手动状态变更
- `POST /api/plan/plans/{id}/submit-approval/` - 提交审批
- `POST /api/plan/plans/{id}/approve/` - 审批通过
- `POST /api/plan/plans/{id}/reject/` - 审批驳回
- `POST /api/plan/plans/{id}/cancel-approval/` - 取消审批

#### 8.2 StrategicGoalViewSet 退役接口

- `POST /api/plan/goals/{id}/submit-approval/` - 提交审批
- `POST /api/plan/goals/{id}/approve/` - 审批通过
- `POST /api/plan/goals/{id}/reject/` - 审批驳回
- `POST /api/plan/goals/{id}/cancel-approval/` - 取消审批

#### 8.3 响应格式

**HTTP 状态码：** `410 Gone`

**响应体：**
```json
{
    "success": false,
    "code": "LEGACY_ENDPOINT_GONE",
    "message": "P1 v2 已启用 PlanDecision 裁决机制，旧审批/手动状态变更接口已退役。请使用 /start-request/ /cancel-request/ 与 /plan-decisions/{id}/decide/。"
}
```

#### 8.4 迁移指南

**旧接口 → 新接口映射：**

| 旧接口 | 新接口 |
|--------|--------|
| `POST /plans/{id}/submit-approval/` | `POST /plans/{id}/start-request/` + `POST /plan-decisions/{id}/decide/` |
| `POST /plans/{id}/approve/` | `POST /plan-decisions/{id}/decide/` (approve=true) |
| `POST /plans/{id}/reject/` | `POST /plan-decisions/{id}/decide/` (approve=false) |
| `POST /plans/{id}/cancel-approval/` | `POST /plans/{id}/cancel-request/` + `POST /plan-decisions/{id}/decide/` |
| `POST /plans/{id}/change-status/` | 使用 `start-request` / `cancel-request` + `decide` |

---

**最后更新：** 2026-01-13  
**版本：** P1 v2

