# 计划管理体检 D（权限与数据隔离）— 代码事实

## 一、各页面权限检查 + queryset 过滤逻辑（证据路径与关键条件）

### 1. plan_list

| 项目 | 事实 | 证据 |
|------|------|------|
| 权限检查 | 必须拥有 `plan_management.view`，否则 redirect admin:index | `views_pages.py` L2219–2223：`if not _permission_granted('plan_management.view', permission_set): ... return redirect('admin:index')` |
| queryset | `Plan.objects.select_related(...).prefetch_related('participants')` 后经 **`_filter_plans_by_permission(plans, request.user, permission_set)`** 过滤 | L2238–2247 |
| 公司/部门隔离 | **无**。未调用 `apply_company_scope` | 全文无 apply_company_scope |

### 2. plan_detail

| 项目 | 事实 | 证据 |
|------|------|------|
| 权限检查 | 先检查 `plan_management.view`；再对 **同一 plan_id** 做一次“可见性”过滤 | L3126–3132：view 不通过则 redirect list；L3134–3148：`plan = get_object_or_404(Plan, id=plan_id)`，再用 `_filter_plans_by_permission(Plan.objects.filter(id=plan_id), ...)`，若 `not filtered_plans.exists()` 则 redirect list |
| queryset | 先 `get_object_or_404(Plan, id=plan_id)`，再用 **`_filter_plans_by_permission`** 判断当前用户是否在该 plan 的可见范围内 | L3144–3148 |
| 公司/部门隔离 | **无**。仅依赖 _filter_plans_by_permission（view_all 或 responsible_person\|owner） | 无 apply_company_scope |

### 3. plan_create

| 项目 | 事实 | 证据 |
|------|------|------|
| 权限检查 | 仅检查 `plan_management.plan.create`，否则 redirect list | L2683–2686 |
| queryset | 无列表 queryset（创建页）；创建时由表单/API 写库，未在此处做公司 scope | — |

### 4. plan_edit

| 项目 | 事实 | 证据 |
|------|------|------|
| 权限检查 | **不检查 view**；只检查“是否可编辑”：`plan.status in ['draft','cancelled']`、无待审批、且（`plan.responsible_person == request.user` 或 `plan_management.plan.manage`） | L3449–3484：`get_object_or_404(Plan, id=plan_id)`，然后 `can_edit = ... (responsible_person == request.user or _permission_granted('plan_management.plan.manage', ...))` |
| queryset | **未用 _filter_plans_by_permission 或 apply_company_scope**。直接 `get_object_or_404(Plan, id=plan_id)` | L3450 |
| 风险 | 拥有 `plan.manage` 的用户可通过 **任意 plan_id** 编辑（含他公司/非本人负责的计划），存在越权与串数据风险 | — |

### 5. plan_delete

| 项目 | 事实 | 证据 |
|------|------|------|
| 权限检查 | 仅检查 `plan_management.plan.manage`，否则 redirect list | L5673–5678 |
| queryset | **未过滤**。直接 `get_object_or_404(Plan, id=plan_id)`，不按公司、不按 view | L5680 |
| 风险 | 拥有 `plan.manage` 的用户可对 **任意 plan_id** 执行删除（跨公司/跨人），存在越权与串数据风险 | — |

### 6. plan_submit_approval

| 项目 | 事实 | 证据 |
|------|------|------|
| 权限检查 | `plan_management.plan.create` 或 `plan.responsible_person == request.user` | L6315–6321：`plan = get_object_or_404(Plan, id=plan_id)`，`can_submit = _permission_granted('plan_management.plan.create', ...) or plan.responsible_person == request.user` |
| queryset | **未用 _filter_plans_by_permission 或 apply_company_scope**。直接按 plan_id 取 Plan | L6316 |
| 风险 | 拥有 create 且知晓 plan_id 的用户可对任意计划提交审批（含他公司），依赖“不知道 id”的隐蔽性；若与 list/detail 的 view 不一致，存在口径不统一 | — |

### 7. plan_approval_list

| 项目 | 事实 | 证据 |
|------|------|------|
| 权限检查 | 仅用 `can_approve` 控制按钮/展示，**未用权限挡入口**（有 approve_plan 或 superuser 则 can_approve=True） | L3988–3989 |
| queryset | **有公司隔离**。先查 ApprovalInstance（plan_content_type, pending/in_progress, 指定 workflow code），再按 **company_id** 过滤：`plan_ids = Plan.objects.filter(Q(company_id=company_id) \| Q(company__isnull=True)).values_list('id')`，`pending_approval_instances = ... .filter(object_id__in=plan_ids)`；PlanDecision 同样按 `plan__company_id` / `plan__company__isnull` 过滤 | L4014–4060、L4056–4059 |
| 公司来源 | `request.user.profile.company_id` 或 `profile.department.company_id` | L4017–4023、4045–4051 |

### 8. decision_approve / decision_reject

| 项目 | 事实 | 证据 |
|------|------|------|
| 权限检查 | `plan_management.approve_plan` 或 `request.user.is_superuser` | L6478–6484（approve）、L6508–6515（reject） |
| queryset | **未按公司或可见性过滤**。`get_object_or_404(PlanDecision, id=decision_id, decided_at__isnull=True)`，未限制 decision 所属 plan 是否在当前用户公司/可见范围内 | L6477–6479、6509–6510 |
| 风险 | 拥有 approve_plan 的用户若知晓 **decision_id**，可对任意公司的 PlanDecision 进行通过/驳回，存在越权与审批泄露风险 | — |

### 9. todo_task_list / todo_task_complete / todo_task_cancel

| 项目 | 事实 | 证据 |
|------|------|------|
| 权限检查 | list：仅用权限控制“是否显示管理/筛选”等，**列表数据不按权限过滤**，只按 **user** 过滤；complete/cancel：先取 todo，再校验 `todo.user_id == request.user.id` | L7468–7475（list 入口）、L7475：`TodoTask.objects.filter(user=request.user)`；L7615–7618（complete）：`todo.user_id != request.user.id` 则 redirect；L7670–7674（cancel）：同上 |
| queryset | list：**仅 `TodoTask.objects.filter(user=request.user)`**；complete/cancel：`get_object_or_404(TodoTask, id=todo_id)` + 严格校验 `todo.user_id == request.user.id` | L7475、L7615、L7670 |
| 结论 | 无跨用户串数据；无公司/部门字段参与过滤 | — |

### 10. StrategicGoal 列表 / 详情 / 编辑 / 删除 / 审批相关

| 视图 | 权限检查 | queryset / 可见性 | 证据 |
|------|----------|-------------------|------|
| strategic_goal_list | 必须 `plan_management.manage_goal` | 有过滤：**view_all** 则全部；**view_assigned** 则 `responsible_person \| owner \| participants \| level='company'`；否则仅 `level='company' \| responsible_person \| owner \| participants` | L2472–2517 |
| strategic_goal_detail | 必须 `plan_management.manage_goal` | **无**：直接 `get_object_or_404(StrategicGoal, id=goal_id)`，**未**用与 list 相同的 view_all/view_assigned 过滤 | L4718–4732 |
| strategic_goal_edit | 必须 `plan_management.manage_goal`；且 goal.status=='draft' | **无**：直接 `get_object_or_404(StrategicGoal, id=goal_id)`，未按 list 可见性过滤 | L4958–4966 |
| strategic_goal_delete | 必须 `plan_management.manage_goal` | **无**：直接 `get_object_or_404(StrategicGoal, id=goal_id)`，未按 list 可见性过滤 | L5607–5616 |
| goal_adjustment_* | manage_goal 或负责人等（见具体视图） | 按 goal_id 取 Goal/Adjustment，未做公司或“目标列表可见性”一致过滤 | 如 L6813 等 |

**StrategicGoal 模型**：无 `company` / `org_department` 字段（见 `backfill_goal_org` 命令说明：“StrategicGoal 模型无 company/org_department 字段”）。因此目标侧 **无组织/部门隔离**，仅有 view_all / view_assigned / level+负责人的过滤，且仅 **列表** 使用该过滤。

---

## 二、是否存在“只检查 has_perm，但不 filter queryset”的串数据风险？

**存在，且有多处。**

| 位置 | 事实 | 风险 |
|------|------|------|
| plan_edit | 只检查 `plan.manage` 或负责人；取数用 `get_object_or_404(Plan, id=plan_id)`，**无** _filter_plans_by_permission、**无** apply_company_scope | 有 manage 即可编辑任意 plan_id（含他公司） |
| plan_delete | 只检查 `plan.manage`；取数同上 | 有 manage 即可删除任意 plan_id（含他公司） |
| plan_submit_approval | 只检查 create 或负责人；取数同上 | 有 create 且知 plan_id 可对任意计划提交审批 |
| decision_approve / decision_reject | 只检查 approve_plan 或 superuser；取数 `get_object_or_404(PlanDecision, id=decision_id)`，**未**限制 plan 所属公司/可见性 | 有 approve_plan 且知 decision_id 可裁决任意公司决策 |
| strategic_goal_detail | 只检查 manage_goal；取数 `get_object_or_404(StrategicGoal, id=goal_id)`，**未**用与 list 一致的 view_all/view_assigned 过滤 | 有 manage_goal 即可查看任意 goal_id（含他人个人目标） |
| strategic_goal_edit / strategic_goal_delete | 同上 | 有 manage_goal 即可编辑/删除任意 goal_id |

**对比：** plan_list / plan_detail 在列表与详情上 **有** queryset 过滤（_filter_plans_by_permission），因此“列表可见”与“详情可见”一致；plan_edit、plan_delete、decision_approve/reject、goal 的 detail/edit/delete 则 **仅 has_perm，无与列表一致的 queryset 过滤**，存在串数据/越权风险。

---

## 三、view_all / view_assigned / view_own（或实际权限名）分别影响哪些查询？

### Plan

- **实际权限名**：`plan_management.plan.view_all`、无单独 “view_assigned” 命名；无 view_all 时按“本人”过滤。
- **影响**：仅 **plan_list** 与 **plan_detail** 使用 **`_filter_plans_by_permission`**（`views_pages.py` L569–604）：
  - **view_all**：`'plan_management.plan.view_all' in permission_set` → 返回全部 plans，不再过滤。
  - **无 view_all**：`plans.filter(Q(responsible_person=user) | Q(owner=user)).distinct()`（即仅本人负责或本人为 owner）。
- **superuser**：直接返回全部，不检查 view_all。
- **结论**：view_all / 本人 只影响 **列表与详情** 的可见范围；**编辑、删除、提交审批、决策裁决** 均不依赖 view_all，只依赖 manage / create / approve_plan 等，且不跟 list 的 queryset 一致。

### StrategicGoal

- **实际权限名**：`plan_management.goal.view_all`、`plan_management.goal.view_assigned`、`plan_management.manage_goal`。
- **影响**：仅 **strategic_goal_list** 使用（L2496–2517）：
  - **view_all**：不额外 filter，全部目标。
  - **view_assigned**：`responsible_person | owner | participants | level='company'`。
  - **仅 manage_goal**：`level='company' | responsible_person | owner | participants`。
- **详情/编辑/删除**：不根据 view_all / view_assigned 再过滤，仅 manage_goal + id，故与列表可见性不一致。

---

## 四、组织/部门隔离是否存在？当前隔离口径是什么？

| 范围 | 是否存在 | 口径 | 证据 |
|------|----------|------|------|
| Plan 列表/详情（页面） | **否** | 仅 **权限 + 负责人/owner**（_filter_plans_by_permission），无 company | plan_list、plan_detail 未调用 apply_company_scope |
| Plan 分析页（完成情况等） | **是** | 先 **apply_company_scope(plans, request.user)**，再 _filter_plans_by_permission | L6037–6041 |
| 审批列表（页面） | **是** | 按 **request.user.profile.company_id**（或 department.company_id）过滤 ApprovalInstance / PlanDecision 的 plan 范围 | L4014–4060 |
| Plan API（views.py） | **是** | 使用 **apply_company_scope** + _filter_plans_by_permission（如 list） | views.py L801；views_inbox 使用 apply_company_scope |
| StrategicGoal | **否** | 模型无 company/org_department；仅 view_all / view_assigned / level+负责人，无组织隔离 | backfill_goal_org 说明；strategic_goal_list 无 apply_company_scope |
| TodoTask | **否** | 仅 **user=request.user**（本人待办），无公司/部门字段 | TodoTask.objects.filter(user=request.user) |

**结论**：  
- **存在** 组织隔离的只有：计划 **分析页**、**审批列表**、**Plan 相关 API**（及 Inbox 等），且依赖 `user.profile.company_id`（或 department.company_id）与 Plan 的 **company_id**。  
- **不存在** 组织隔离的：plan_list / plan_detail / plan_edit / plan_delete / plan_submit_approval、StrategicGoal 全链路、TodoTask（仅按 user）。  
- 当前“隔离”口径：**能做的页面/API** = 公司维度（company_id）；**未做的** = 仅 user 或权限（view_all / 负责人/owner）。

---

## 五、审批列表（workflow + legacy）是否会出现“审批人能看到不该看的计划详情”？

**会，存在两种方向的问题：**

1. **审批人能看到他公司以外/本不该看到的计划详情**  
   - 审批列表已按 **company_id** 过滤，审批人只能看到“本公司的待审批”。  
   - 但 **plan_detail** 不按公司过滤，只按 ** _filter_plans_by_permission**（view_all 或 responsible_person|owner）。  
   - 若审批人拥有 **plan_management.plan.view_all**，则可在列表外直接访问任意 plan_id 的详情（含他公司），即“审批列表”限制不住“详情页”的越权。  
   - 若审批人仅有 **approve_plan**、无 view_all，则从审批列表点进“计划详情”时，若该计划不是其 responsible/owner，会被 _filter_plans_by_permission 挡掉（redirect list），即 **看不到详情**，属于体验问题（该看的审批项点进去反而看不到）。

2. **决策裁决不按公司/可见性过滤**  
   - **decision_approve / decision_reject** 仅校验 approve_plan，不校验 decision 所属 plan 是否在当前用户公司或可见范围内。  
   - 因此拥有 approve_plan 且知晓 **decision_id** 的用户，可对任意公司的 PlanDecision 进行通过/驳回，属于 **审批泄露/越权**。

---

## 六、风险分级

| 级别 | 项 | 说明 |
|------|----|------|
| **P0** | plan_edit / plan_delete 仅 has_perm(manage)、无 queryset 过滤 | 有 plan.manage 即可按 plan_id 编辑/删除任意计划（含他公司），存在越权与串数据。 |
| **P0** | decision_approve / decision_reject 仅 has_perm(approve_plan)、无 decision/plan 范围过滤 | 有 approve_plan 且知 decision_id 即可裁决任意公司决策，存在审批泄露与越权。 |
| **P0** | plan_list / plan_detail 无公司隔离 | 若多租户按公司隔离为必选，则 view_all 用户可见全公司计划，属串数据；且与“审批列表/API”按公司隔离口径不一致。 |
| **P1** | strategic_goal 列表有 view_all/view_assigned，详情/编辑/删除仅 manage_goal + id | 有 manage_goal 即可查看/编辑/删除任意 goal_id（含他人个人目标），与列表可见性不一致，绑定业务对象后可见性必冲突。 |
| **P1** | plan_submit_approval 仅 create 或负责人、无 list 可见性/公司一致过滤 | 有 create 且知 plan_id 可对任意计划提交审批，与 list/detail 可见范围不一致，绑定业务对象后易冲突。 |
| **P1** | 审批人无 view_all 时，从审批列表点进计划详情可能被 redirect list | 体验问题：该审批的项打不开详情，需依赖工作流审批页或其它入口。 |
| **P2** | StrategicGoal 无 company/org_department，无法做组织级隔离 | 后续若要做“按公司/部门隔离目标”，需模型与全链路改造，属维护性/扩展性。 |
| **P2** | TodoTask 仅 user 维度，无公司/部门 | 若未来需“管理员看全公司待办”等，需扩展字段与过滤逻辑，属体验/维护性。 |

以上均为代码事实与证据归纳。
