# 计划模块可选增强：InboxAPI 计划待审 与 Plan.related_project_fk

本文档为**可选**方案评估，不要求在本轮实现；仅供后续迭代参考。

---

## 一、InboxAPI 计划侧补齐（待审与 ApprovalInstance 一致）

### 现状

- **页面**：`plan_approval_list` 展示的“待审批”来自两类数据：
  1. **ApprovalInstance**（工作流）：`content_type=Plan`，`status in ['pending','in_progress']`，`workflow__code in [plan_start_approval, plan_cancel_approval]`，再按 `Plan.company_id` 做公司隔离。
  2. **PlanDecision**（兼容）：`decided_at__isnull=True`，同样按 `plan__company_id` 做公司隔离。
- **API**：`GET /api/plan/inbox/`（InboxAPI）中，Plan 部分当前为 `Plan.objects.none()`，即**始终返回 0 条**；Goal 部分按 `status='pending_approval'` + `apply_company_scope` 返回。因此 Plan 待审在 API 与页面不一致。

### 目标

- 不改 UI，只补 API：使 InboxAPI 的 `plans` 与页面“计划审批列表”的待审口径一致，即**由 ApprovalInstance（+ 可选 PlanDecision）驱动**，并做公司隔离。

### 最小改动方案

1. **数据来源**（与 `plan_approval_list` 对齐）：
   - 查 `ApprovalInstance`：`content_type=ContentType.objects.get_for_model(Plan)`，`status__in=['pending','in_progress']`，`workflow__code__in=[PlanApprovalService.PLAN_START_WORKFLOW_CODE, PlanApprovalService.PLAN_CANCEL_WORKFLOW_CODE]`。
   - 公司隔离：非 superuser 时，用 `request.user` 的 `profile.company_id`（或 `department.company_id`）得到 `company_id`，再 `plan_ids = Plan.objects.filter(Q(company_id=company_id)|Q(company__isnull=True)).values_list('id', flat=True)`，`ApprovalInstance` 过滤 `object_id__in=plan_ids`。
   - （可选）若需与页面完全一致，可再合并 PlanDecision 中 `decided_at__isnull=True` 且 `plan_id__in=plan_ids` 的 plan_id，去重后与 ApprovalInstance 的 object_id 合并。
2. **InboxAPI.get 中 Plan 分支**：
   - 当 `can_approve_plan` 时，不再使用 `Plan.objects.none()`。
   - 按上一步得到待审的 `plan_id` 列表（来自 ApprovalInstance，可选合并 PlanDecision）。
   - `plans_qs = Plan.objects.filter(id__in=plan_ids)`，再 `apply_company_scope(plans_qs, user)`（二次保险），按 `created_time` 排序，用现有 `PlanInboxItemSerializer` 序列化返回。
3. **依赖**：`plan_management.services.plan_approval.PlanApprovalService` 的 workflow code 常量；`ContentType`、`ApprovalInstance`；现有 `apply_company_scope`。

### 页面一致性说明

- 页面“计划审批列表”以 ApprovalInstance + PlanDecision 合并展示；API 若只从 ApprovalInstance 取 plan_id，已与“工作流待审”一致；若再合并 PlanDecision，则与页面完全一致（含历史未迁移决策）。建议先只做 ApprovalInstance，再按需加 PlanDecision 合并。

---

## 二、Plan.related_project_fk 项目锚点结构化预留

### 现状

- `Plan` 仅有 `related_project`（CharField，来自商机等），无对 `production_management.Project` 的外键。
- 若后续需要按“项目”做统计、权限或看板，需要结构化关联。

### 方案：增加 related_project_fk（FK Project，null=True）

- **模型**：在 `Plan` 上增加字段，例如  
  `related_project_fk = models.ForeignKey('production_management.Project', on_delete=models.SET_NULL, null=True, blank=True, related_name='related_plans', verbose_name='关联项目')`。
- **迁移**：新增迁移即可，默认 `null=True`，对已有数据无破坏；历史数据不 backfill 也合法。

### 历史数据与最小同步策略

- **原则**：仅在**能唯一确定**对应 `Project` 时写入 `related_project_fk`，否则保持 `null`。
- **可选数据源**：
  1. **商机/业务机会**：若 Plan 创建时绑定了某 BusinessOpportunity，且该商机已关联唯一 Project（或已转项目），则可从该 Project 写入 `related_project_fk`。
  2. **related_project 字符串**：若当前 `related_project` 存的是项目编号或名称，且能**唯一**解析到一条 `Project`（例如按编号 `Project.objects.filter(project_number=...)` 且 `count()==1`），则可回填；若多选或无法唯一确定，则不写。
- **同步时机**：创建/更新 Plan 时在业务逻辑中“能唯一确定则 set，否则不 set”；历史数据可用一次性 management command 按上述规则 backfill，且只做“唯一匹配”的写入，避免一对多歧义。

### 风险与影响

- **迁移**：仅新增可空 FK，对现有表与查询影响最小。
- **历史数据**：不 backfill 则 `related_project_fk` 全为 null，与现有一致；backfill 仅建议在“唯一可解析”的场景下写入，避免错误关联。
- **兼容**：保留 `related_project` 字符字段，便于展示或未结构化时的兼容；后续可逐步用 `related_project_fk` 替代展示与统计。

---

以上为评估结论与最小实现/同步策略，具体实现以实际迭代为准。
