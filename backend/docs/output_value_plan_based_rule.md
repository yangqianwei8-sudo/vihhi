# 产值只读计划完成状态 — 数据流与边界

## 1. 硬约束

- **产值计算唯一依据**：计划管理模块的「计划/里程碑完成状态」。
- **业务模块只允许**：产生“事实/证据事件”（FactEvent），用于计划管理判定里程碑是否可完成。
- **禁止**：任何业务模块字段/接口直接参与产值公式或权重计算。
- **禁止**：产值模块直接读取业务模块记录来判定完成度（只能读计划管理的完成状态）。

## 2. 数据流

```
业务模块（生产/结算/合同等）
    │
    │ 只写
    ▼
FactEvent（plan_management）
    type, ref_model, ref_id, occurred_at, payload, source_app
    │
    │ 计划管理评估（evaluate_milestone_completion / 管理命令批量）
    ▼
MilestoneEvidenceRule + FactEvent 满足
    │
    │ 写入
    ▼
PlanOutputMilestoneCompletion（plan_management）
    opportunity_id, milestone_code, completed_at, evidence_snapshot
    │
    │ 产值模块只读
    ▼
calculator_v1.is_milestone_completed(milestone_id, opportunity_id)
    → 仅查 PlanOutputMilestoneCompletion(opportunity_id, milestone.code).exists()
    │
    ▼
产值公式：base × service_weight × stage_weight × milestone_weight × event_modifier
```

## 3. 边界与职责

| 角色 | 允许 | 禁止 |
|------|------|------|
| 业务模块 | 写 FactEvent（证据） | 写产值、写计划完成状态、提供产值公式/权重字段或接口 |
| 计划管理 | 读 FactEvent + 规则，写 PlanOutputMilestoneCompletion | 写产值；直接改产值公式/权重 |
| 产值模块 | 读 opportunity/project 基础表、读 PlanOutputMilestoneCompletion、读 OutputValueStage/Milestone（权重配置） | 读 OutputValueRecord/业务表做完成度判定；读业务模块表 |

## 4. 相关模型与接口

- **计划管理**：`FactEvent`、`MilestoneEvidenceRule`、`PlanOutputMilestoneCompletion`；服务 `evaluate_milestone_completion`、`evaluate_recent_fact_events`；管理命令 `evaluate_output_milestone_completion`。
- **产值模块**：`calculator_v1.is_milestone_completed` 只查 `PlanOutputMilestoneCompletion`；`_get_completed_milestones_max_weight` 同上。
- **API**：`GET /api/output/v1/opportunity/<id>/` 仅通过 calculator_v1 使用上述完成状态，不读业务表。

## 5. 文档依据

- 冻结文档补丁：`docs/output_value_v1_execution.md` 第十一章「V1 口径补丁：产值依据只来自计划管理」。
- 验收项：`docs/output_value_v1_launch_confirmation.md` 第 4 节。

---

## 6. 门禁与审计

### 6.1 禁止直写

- **PlanOutputMilestoneCompletion**：仅允许由评估服务（`evaluate_milestone_completion` / `evaluate_output_milestone_completion` 命令）写入。禁止任何 view/form 直接 `create` 或 `update`；模型层 `save()` 会校验写入门禁，非评估上下文调用将抛出 `PermissionError`。
- **FactEvent**：模型层已阻断直写。必须通过唯一入口 `plan_management.services.fact_event.record_fact_event(...)` 写入；禁止业务/测试直接 `FactEvent.objects.create`、`bulk_create` 或 `update_or_create`，否则运行时抛 `PermissionError`。入口强制填写 `source_app`，并校验 `type` 在白名单（至少包含 `CONSULT_OPINION_SUBMITTED`）。

### 6.2 审计字段

- **PlanOutputMilestoneCompletion**：`created_by`（可空）、`created_via`（固定 `rule_engine`）、`rule_code`、`rule_snapshot`，用于追溯命中规则与写入途径。
- **FactEvent**：`created_at`（入库时间）、`idempotency_key`（可空，幂等写入），便于审计与去重。

### 6.3 可运行验证

- 运行手册：`backend/docs/output_value_v1_plan_based_runbook.md`（使用 `record_fact_event` 与评估命令，可复现完成记录及审计字段）。
