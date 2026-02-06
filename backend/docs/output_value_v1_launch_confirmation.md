# 产值管理 V1 —— 最终确认，准备上线

**权威依据**：`docs/output_value_v1_execution.md`（冻结版）  
**接口文档**：`docs/output_value_v1_api.md`

---

## 一、已完成任务确认

### 1. API 接入与行为确认

- `GET /api/output/v1/opportunity/{id}/` 正常返回五字段（`dynamic_output`、`stage`、`milestone`、`milestone_weight`、`confidence`），计算逻辑与冻结文档一致。
- 未登录返回 **401**，商机不存在返回 **404**。

### 2. 接口文档与联调测试

- **文档**：`backend/docs/output_value_v1_api.md` 已完整，涵盖请求路径、认证、响应字段、类型说明、`confidence` 规则、200/404/401 说明与示例、与冻结文档对应关系、联调说明、上线前检查清单。
- **测试**：联调测试已完善（未登录 401、商机不存在 404、已登录且商机存在 200 及五字段校验）。

### 3. 上线前检查清单

- 商机 ID 存在时返回 200，字段齐全且数值合理。
- 商机不存在时返回 404 及 `detail`。
- 未登录时返回 401。
- 确认 `/api/output/` 路径在网关/负载均衡已放行。

### 4. 产值依据只来自计划管理（口径补丁验收）

- **验收项**：产值计算未直接依赖任何业务模块表/接口，仅依赖计划管理完成状态。  
- 验证方式：`calculator_v1` 中里程碑完成判定仅读取计划管理的「产值里程碑完成」记录（如 `PlanOutputMilestoneCompletion`）；无对 `OutputValueRecord` 或业务表完成度累计；可结合 `output_value_no_business_dependency_proof.md` 的 grep/引用证明做验收。

### 5. 门禁可执行验收（上线前必须通过）

- **验收项**：运行门禁验证命令，全部检查通过方可上线。  
- **可执行步骤**：在已迁移环境中执行：
  ```bash
  python manage.py verify_output_value_v1_gates
  ```
  **必须全绿通过**（所有项显示 `[PASS]`，退出码 0）。任一项 `[FAIL]` 或非 0 退出码视为门禁失效，不得上线。

---

## 二、完成标准确认

- [x] API 按冻结文档正确返回并计算产值。
- [x] 接口文档与测试用例已就绪，接口行为验证无误。
- [x] 上线前检查清单已准备好，部署后可逐项验证。

---

## 三、部署后验证建议

部署完成后，按 `docs/output_value_v1_api.md` 第 4 节「上线前检查清单」逐项执行验证，并可选执行：

```bash
python manage.py test backend.apps.output_value_management.tests.test_api_v1 --keepdb
```

（需测试库已完整迁移。）

---

**状态**：最终确认已完成，可进行上线。
