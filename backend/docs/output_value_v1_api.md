# 产值管理 V1 API 接口文档

**权威依据**：`docs/output_value_v1_execution.md`（冻结版）  
**计算逻辑**：与冻结文档一致，不新增语义、不修改公式。

---

## 1. 查询当前动态产值

**文档对应**：冻结文档 八.1

### 请求

```http
GET /api/output/v1/opportunity/{id}/
```

| 项     | 说明 |
|--------|------|
| 方法   | GET |
| 路径   | `/api/output/v1/opportunity/<商机ID>/` |
| 认证   | 需登录（IsAuthenticated） |

### 响应

**200 OK**

| 字段             | 类型    | 说明 |
|------------------|---------|------|
| `dynamic_output` | number  | 当前动态产值（公式：商机金额 × 服务类型权重 × 1 × 里程碑权重 × 事件修正系数） |
| `stage`          | string  | 当前阶段名称 |
| `milestone`      | string \| null | 当前取到的已完成里程碑名称（无则为 null） |
| `milestone_weight` | number | 当前阶段内已完成里程碑的最大权重（0～1） |
| `confidence`     | string  | `low` \| `medium` \| `high`（见下） |

**confidence 规则（V1）**：
- `high`：milestone_weight ≥ 0.30
- `medium`：0 < milestone_weight < 0.30
- `low`：milestone_weight = 0

**404 Not Found**：商机不存在时返回 `{"detail": "商机不存在"}`。

**401 Unauthorized**：未登录或认证失效时由 DRF `IsAuthenticated` 返回 401。

### 示例

**请求**
```http
GET /api/output/v1/opportunity/123/
Authorization: Session 或 Token
```

**响应（200）**
```json
{
  "dynamic_output": 32000.0,
  "stage": "生产阶段",
  "milestone": "咨询意见提交",
  "milestone_weight": 0.3,
  "confidence": "high"
}
```

**响应（无已完成里程碑）**
```json
{
  "dynamic_output": 0.0,
  "stage": "生产阶段",
  "milestone": null,
  "milestone_weight": 0.0,
  "confidence": "low"
}
```

---

## 2. 与计算逻辑的一致性

- 动态产值由 `backend.apps.output_value_management.services.calculator_v1.calculate_dynamic_output(opportunity_id)` 计算。
- 公式、权重、confidence 阈值均按冻结文档实现，可追溯至 `output_value_v1_execution.md` 第一至八章。
- 本接口仅暴露计算结果，不修改任何业务数据（无副作用）。

---

## 3. 联调与上线

- **联调**：使用已登录会话或 Token 调用 `GET /api/output/v1/opportunity/<id>/`，核对返回的 `dynamic_output`、`milestone_weight`、`confidence` 与预期一致。
- **上线**：部署后确认该路径在网关/负载均衡中可访问，且认证中间件生效。

---

## 4. 上线前检查清单

| 检查项 | 说明 | 预期 |
|--------|------|------|
| 真实商机 ID | 用已存在的商机 ID 请求 | 200，返回 `dynamic_output`、`milestone_weight`、`confidence`、`stage`、`milestone` 五字段齐全，数值符合冻结文档计算逻辑 |
| 不存在的 ID | 用不存在的商机 ID 请求 | 404，响应体含 `detail`（如「商机不存在」） |
| 未登录 | 不带 Session/Token 请求 | 401 Unauthorized |
| 网关/负载均衡 | 若有统一网关或 LB | 确认 `/api/output/` 已放行且可访问 |

**自动化测试**：执行 `python manage.py test backend.apps.output_value_management.tests.test_api_v1 --keepdb`，确认 401、404、200 及响应结构用例通过。  
（前提：测试库已完整迁移，含 `production_management`、`output_value_management` 等；若迁移未完成，先执行 `python manage.py migrate` 再跑测试。）
