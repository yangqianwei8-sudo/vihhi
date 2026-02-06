# 产值计算内核未直接依赖业务模块 — 证明

## 1. 结论

`backend/apps/output_value_management/services/calculator_v1.py` 未直接依赖任何业务模块表或接口；里程碑完成度仅依赖计划管理的 `PlanOutputMilestoneCompletion`。

## 2. 允许的依赖（非业务）

- `backend.apps.opportunity_management.models.BusinessOpportunity`（商机基础表，全系统共用）
- `backend.apps.output_value_management.models.OutputValueStage`、`OutputValueMilestone`（产值阶段/里程碑配置与权重，非业务记录）
- `backend.apps.plan_management.models.PlanOutputMilestoneCompletion`（计划管理维护的完成状态，产值只读）

## 3. Grep 证明：calculator_v1 未引用业务模块

在 `calculator_v1.py` 中禁止出现：

- 对 `OutputValueRecord` 的引用（完成度不得由产值记录表判定）
- 对 `production_management`、`settlement_management`、`contract_management`、`financial_management` 等业务模块的 model/服务导入（除全系统共用的 opportunity/project 外）

**命令与预期结果：**

```bash
# calculator_v1 中不应出现 OutputValueRecord
grep -n "OutputValueRecord" backend/apps/output_value_management/services/calculator_v1.py
# 预期：无匹配

# calculator_v1 中不应出现 production_management / settlement_management / contract_management / financial_management 等业务应用 model 或服务
grep -n "production_management\|settlement_management\|contract_management\|financial_management" backend/apps/output_value_management/services/calculator_v1.py
# 预期：无匹配（opportunity/project 通过 opportunity_management 与基础表使用，不在“业务模块直接参与公式”范围内）
```

**实际结果**：  
- `OutputValueRecord` 在 `calculator_v1.py` 中无引用。  
- 无对 `production_management`、`settlement_management`、`contract_management`、`financial_management` 的 import 或引用。

## 4. 完成度判定来源

- `is_milestone_completed(milestone_id, opportunity_id)`：仅执行  
  `PlanOutputMilestoneCompletion.objects.filter(opportunity_id=..., milestone_code=...).exists()`  
  及 `OutputValueMilestone.objects.get(pk=milestone_id)` 以取 `code`，不读 `OutputValueRecord` 或业务表。
- `_get_completed_milestones_max_weight(stage, opportunity)`：仅遍历当前 stage 的 milestones，对每个 milestone 仅查  
  `PlanOutputMilestoneCompletion.objects.filter(opportunity_id=..., milestone_code=m.code).exists()`，不读业务表。

## 5. 测试覆盖

- `test_calculator_v1.test_milestone_completion_only_from_plan_not_business`：仅有 FactEvent、无 PlanOutputMilestoneCompletion 时，里程碑未完成、产值不变。
- `test_api_v1.test_v1_only_fact_event_plan_not_completed_then_milestone_weight_unchanged`：仅有业务 FactEvent 但计划未完成时，V1 API 返回 milestone_weight=0、dynamic_output=0。
- `test_api_v1.test_v1_plan_milestone_completed_then_milestone_weight_and_output_change`：计划里程碑完成时，V1 API 返回 milestone_weight > 0、产值变化。

以上证明：产值计算未直接依赖任何业务模块表/接口，仅依赖计划管理完成状态。

---

## 6. 模型层门禁证据

**PlanOutputMilestoneCompletion**：仅评估服务可写，直写抛 `PermissionError`。

- 类/方法：`plan_management.models.PlanOutputMilestoneCompletion.save()` 内调用 `_get_completion_write_allowed()`，未允许则 `raise PermissionError(...)`。
- 允许写入：`allow_plan_completion_write()` / `reset_plan_completion_write(token)`，仅在 `plan_management.services.milestone_completion` 内调用。

**FactEvent**：仅 `record_fact_event` 可写，直写抛 `PermissionError`。

- 类/方法：`plan_management.models.FactEvent.save()` 内调用 `_get_fact_event_write_allowed()`，未允许则 `raise PermissionError(...)`；`FactEventQuerySet.bulk_create` 同样校验并阻断。
- 允许写入：`allow_fact_event_write()` / `reset_fact_event_write(token)`，仅在 `plan_management.services.fact_event.record_fact_event` 内调用。

**Grep 关键字（可执行证据）：**

```bash
# FactEvent 门禁：save() 与 bulk_create 阻断
grep -n "_get_fact_event_write_allowed\|allow_fact_event_write\|PermissionError" backend/apps/plan_management/models.py
# 应包含 FactEvent.save、FactEventQuerySet.bulk_create、allow_fact_event_write、reset_fact_event_write

# record_fact_event 内启用门禁
grep -n "allow_fact_event_write\|reset_fact_event_write" backend/apps/plan_management/services/fact_event.py
# 应包含 record_fact_event 内 try/finally 的 allow 与 reset
```

---

## 7. 可运行验证链路

在任意已迁移环境可按以下文档做端到端验证（不依赖测试库）：

- **运行手册**：`backend/docs/output_value_v1_plan_based_runbook.md`

手册步骤概要：创建/选择商机 → 运行 `seed_output_value_v1_plan_rules` → 插入 FactEvent（type=CONSULT_OPINION_SUBMITTED）→ 运行 `evaluate_output_milestone_completion --opportunity-id X --milestone-code consult_opinion_submitted` → 调用 API 或 calculator_v1 验证 milestone_weight=0.30、dynamic_output>0 → 删除 PlanOutputMilestoneCompletion 再验证产值回到 0。

---

## 8. 明确结论：FactEvent 与完成表对产值的影响

- **FactEvent 单独不改变产值**：业务侧仅写入 FactEvent 时，产值模块不读该表；只有计划管理根据规则评估后写入 `PlanOutputMilestoneCompletion`，产值才会变化。
- **只有 PlanOutputMilestoneCompletion 改变产值**：产值计算内核只根据 `PlanOutputMilestoneCompletion` 判定里程碑是否完成，从而决定 milestone_weight 与 dynamic_output。删除完成记录后产值立即回到 0，可验证“只认计划完成”的硬约束。
