# 计划管理体检 B + C（代码事实）

## B. 核心实体关系图（文字版 ER）

### 1. Plan → related_goal(FK) → StrategicGoal

- **Plan.related_goal**：`ForeignKey(StrategicGoal, on_delete=PROTECT, null=True, blank=True, related_name='related_plans')`  
  证据：`plan_management/models.py` L757–765。

### 2. PlanDecision → plan(FK) / decided_by / decided_at

- **plan**：`ForeignKey(Plan, on_delete=CASCADE, related_name='decisions')`  
  证据：`plan_management/models.py` L1732–1737。
- **requested_by**：`ForeignKey(User, on_delete=SET_NULL, null=True, related_name='requested_plan_decisions')`  
  证据：L1755–1760。
- **decided_by**：`ForeignKey(User, on_delete=SET_NULL, null=True, blank=True, related_name='decided_plan_decisions')`  
  证据：L1766–1772。
- **decided_at**：`DateTimeField(null=True, blank=True)`，pending 判定为 `decided_at is None`。  
  证据：L1773–1776。

### 3. ApprovalNotification → 关联对象是谁

- **无 FK 到 plan/goal/decision/ApprovalInstance**。  
  证据：`plan_management/models.py` L1814–1871。
- **关联方式**：`object_type`（CharField，choices：plan/goal/todo/summary/notification）+ `object_id`（CharField，max_length=50）。
- **语义**：  
  - 审批相关：`object_type='plan'|'goal'` 时，`object_id` 可为业务对象主键字符串，或 workflow 约定格式 `approval_{instance.id}:{business_object_id}`。  
  证据：`workflow_engine/services.py` L461–464、L615–616 使用 `approval_object_id = f"approval_{instance.id}:{instance.object_id}"` 写入 ApprovalNotification。
- **user**：`ForeignKey(User, on_delete=CASCADE, related_name='approval_notifications')`，表示接收人。

### 4. TodoTask → 关联对象是谁

- **无 ContentType/GenericForeignKey**。  
  证据：`plan_management/models.py` L1889–1930。
- **关联方式**：`related_object_type`（CharField，choices：goal/plan/todo）+ `related_object_id`（CharField，max_length=50, null=True, blank=True）。
- **user**：`ForeignKey(User, on_delete=CASCADE, related_name='todo_tasks')`，负责人。  
  **completed_by**：`SET_NULL`；**cancelled_by**：`SET_NULL`。

### 5. Attachment → 当前已挂载哪些对象

- **模型**：`ContentType` + `object_id`（PositiveIntegerField）+ `GenericForeignKey('content_type','object_id')`。  
  证据：`plan_management/models.py` L1411–1418（Attachment 定义）。
- **代码挂载点（ContentType 实际使用）**：
  - **Plan**：`ContentType.objects.get_for_model(Plan)`，用于 filter/create。  
    证据：`views_pages.py` 多处（如 L2334、L3229、L3282、L3389、L3459、L4004、L5706、L5773、L6334、L6445 等）；`plan_approval.py` L55、L111、L160、L276 等。
  - **StrategicGoal**：`ContentType.objects.get_for_model(StrategicGoal)`。  
    证据：`views_pages.py` L4802、L4826；`views.py` L340、L443 等。
  - **PlanAdjustment**：`ContentType.objects.get_for_model(PlanAdjustment)`。  
    证据：`views_pages.py` L7313、L7399。

### 6. 关系字段与 on_delete 汇总

| 实体 | 关系字段 | 目标 | on_delete |
|------|----------|------|-----------|
| Plan | related_goal | StrategicGoal | PROTECT |
| PlanDecision | plan | Plan | CASCADE |
| PlanDecision | requested_by | User | SET_NULL |
| PlanDecision | decided_by | User | SET_NULL |
| ApprovalNotification | user | User | CASCADE |
| ApprovalNotification | object_type / object_id | 无 FK，字符串关联 plan/goal/approval 等 | — |
| TodoTask | user | User | CASCADE |
| TodoTask | completed_by | User | SET_NULL |
| TodoTask | cancelled_by | User | SET_NULL |
| TodoTask | related_object_type / related_object_id | 无 FK，字符串关联 goal/plan/todo | — |
| Attachment | content_type | ContentType | CASCADE |
| Attachment | object_id | 泛型 | — |
| Attachment | uploaded_by | User | SET_NULL |

---

## C. 状态机与审批机制核查

### 1. Plan.status 枚举值与流转入口

- **枚举**：`STATUS_CHOICES` = draft, published, in_progress, completed, cancelled, paused, delayed。  
  证据：`plan_management/models.py` L498–506。
- **合法流转**（`get_valid_transitions`）：  
  draft→[published,cancelled]；published→[in_progress,cancelled,paused,delayed]；in_progress→[completed,cancelled,paused,delayed]；completed/cancelled→[]；paused/delayed→[in_progress,cancelled]。  
  证据：`plan_management/models.py` L1122–1131。

### 2. 哪些 view/action 会改变 Plan.status（文件路径+函数名）

| 文件 | 函数/位置 | 行为 | 证据（关键逻辑） |
|------|-----------|------|------------------|
| plan_management/views_pages.py | plan_submit_approval | cancelled→draft（仅当重新提交时） | L6354–6360：`plan.status = 'draft'` + `plan.save(update_fields=['status'])` |
| plan_management/views_pages.py | （计划创建/分解等） | 新建时默认 status（见 Plan.save） | L656–664：日/周计划 published，其他 draft |
| plan_management/views.py | StrategicGoalViewSet 内 submit_approval/approve/reject/cancel | 不写 Plan | 仅 Goal；Plan 在下方 |
| plan_management/views.py | PlanViewSet 内 start-request 等 action | 通过裁决器写 status | L1146、L1320、L1433、L1535：`plan.status = result.new_status` + `plan.save(update_fields=['status'])`，result 来自 adjudicator |
| plan_management/services/recalc_status.py | — | 按规则写 status | L51、L64：`plan.status = result.new_status` |
| plan_management/services/plan_decisions.py | decide / 取消通过 | 写 status | L236：`plan.status = "cancelled"`；L288：`plan.status = result.new_status` |
| plan_management/services/plan_approval.py | — | 仅判断/取消时写 | L237：`plan.status = 'cancelled'` |
| plan_management/signals.py | — | 不直接改 status，仅触发逻辑 | L226 判断 `plan.status == 'published'` |
| plan_management/views_pages.py | plan_progress_update / plan_complete 等 | 可能经服务层改 status | 需经 adjudicate/recalc 或 transition_to，非直接赋值（未在本次 grep 中出现直接 `plan.status=`） |

### 3. 是否存在绕过状态机直接改 status 的路径（如 DRF partial_update）

- **DRF 侧**：有防护。  
  - `PlanSerializer`：`read_only_fields` 含 `status`（L65）；`validate()` 中若 `initial_data` 含 `status` 则抛出 ValidationError。  
  证据：`plan_management/serializers.py` L82–91（注释“P1: 禁止在 update/partial_update 中直接修改 status”）。
- **结论**：通过 PlanViewSet 的 update/partial_update 无法直接改 status，会被序列化器拒绝。

### 4. Fix-1（status 只读）是否仍对 Plan 生效

- **生效**。  
  - 序列化器：`read_only_fields = (..., 'status', ...)` 且 `validate()` 中显式禁止 `status`。  
  证据：`plan_management/serializers.py` L65、L82–91。  
  - 状态变更仅通过裁决/服务层写入（views.py 中 `plan.status = result.new_status` 的 result 来自 adjudicator）。

### 5. 提交审批链路（页面 & API）

#### 5.1 views_pages.plan_submit_approval 做了什么

- **不创建 PlanDecision**。使用 `PlanStartApprovalService`（plan_approval_v2），走通用审批引擎。  
  证据：`views_pages.py` L6392–6399：`PlanStartApprovalService().submit_approval(obj=plan, applicant=request.user, comment=...)`，无 `request_start()` 或 `PlanDecision.objects.create`。
- **会创建 workflow_engine.ApprovalInstance**。  
  证据：`PlanStartApprovalService` 继承 `UniversalApprovalService`，提交后由工作流创建 ApprovalInstance（见 plan_approval_v2.py L14–38）。
- **会写 ApprovalNotification**。  
  证据：工作流在“提交审批”时通知审批人，`workflow_engine/services.py` L449–475 调用 `safe_approval_notification(...)`，创建 ApprovalNotification（object_type 来自 content_type.model，object_id 为 `approval_{instance.id}:{instance.object_id}`）。

#### 5.2 views_pages.plan_approval_list 查询的是什么

- **双数据源**：  
  1）**ApprovalInstance**（workflow）：`content_type=plan_content_type, status__in=['pending','in_progress'], workflow__code__in=[PLAN_START_WORKFLOW_CODE, PLAN_CANCEL_WORKFLOW_CODE]`，再按公司、搜索、类型、日期等过滤；  
  2）**PlanDecision**（向后兼容）：`decided_at__isnull=True`，再同样公司/筛选。  
  证据：`views_pages.py` L3998–4024（ApprovalInstance）、L4033–4060（PlanDecision），L4122–4152 两套分页与统计同时传给模板。

#### 5.3 api/plan/inbox/（InboxAPI）为什么 plans_qs = Plan.objects.none()

- **原因**：注释写明“P1: 不认 pending_approval 状态，改为空查询或 draft”。  
  证据：`views_inbox.py` L43–44：`# P1: 不认 pending_approval 状态，改为空查询或 draft`、`plans_qs = Plan.objects.none()`。
- **结论**：刻意禁用“待我审批”中的 Plan 列表（Plan 已不走 pending_approval，走工作流）；非未实现，无 TODO。Goal 仍按 `status='pending_approval'` 查询。

#### 5.4 计划审批任务现在从哪里看

- **页面**：`plan/plans/approval/` → `plan_approval_list`，展示 **ApprovalInstance（工作流）** + **PlanDecision（待办）** 两列表（含筛选、分页、统计）。  
  证据：同上 5.2；路由在 `urls_pages.py` L26。

### 6. 通知/待办生成机制

#### 6.1 ApprovalNotification 在哪些地方创建（.create 调用点）

- **唯一写入入口**：`plan_management/compat.py` 的 `safe_approval_notification()` → `_ApprovalNotification.objects.create(*args, **kwargs)`。  
  证据：`compat.py` L51–56。
- **调用方**（均通过 safe_approval_notification）：  
  - `plan_management/notifications.py`：多处（notify_approvers、notify_submitter、目标/计划发布与接收、周计划提醒/逾期、待办、进度通知、每日通知等）；  
  - `workflow_engine/services.py`：提交审批时通知审批人（L467）、审批结果通知提交人（L619）；  
  - `plan_management/services/todo_generator.py`、`work_summary_service.py`、`tasks.py`；  
  - 若干 management commands（send_daily_notifications、send_weekly_plan_reminder、generate_monthly_personal_plan_todos、check_weekly_plan_overdue、check_todo_overdue、daily_todo_reminder 等）。  
  证据：grep `safe_approval_notification` 得 45 处；直接 `ApprovalNotification.objects.create` 仅 `send_test_notification.py` L78 与 compat 内。

#### 6.2 TodoTask 在哪些动作触发创建/完成/取消

- **创建**：  
  - `plan_management/services/todo_service.py`：`create_todo_task()` 内 `TodoTask.objects.create(...)`。  
  证据：L1843–1888。  
  - 调用 `create_todo_task` 的只有：`todo_generator.py`（日/周/月计划分解、目标创建与进度、计划创建与进度等）、`generate_monthly_personal_plan_todos` 命令。  
  证据：grep `create_todo_task` 得 13 处。
- **完成**：  
  - 页面：`views_pages.todo_task_complete` → `todo_service.mark_todo_completed()`，更新 status、completed_at、completed_by、completion_note/evidence、verification_* 等。  
  证据：`views_pages.py` L7607–7661；`todo_service.py` L1892–1945。  
  - 自动闭环：`todo_service.mark_todo_completed` 在其他业务逻辑中调用（如计划/目标完成时）。  
  证据：`todo_service.py` 内多处（如 L54、L181、L478 等判断 plan/goal 状态后调用）。
- **取消**：  
  - 页面：`views_pages.todo_task_cancel` → `todo_service.mark_todo_cancelled()`。  
  证据：`views_pages.py` L7667–7700。

#### 6.3 “通知列表”的唯一事实来源（单一口径）

- **计划/目标审批与待办类通知**：唯一数据源为 **plan_management.ApprovalNotification**，查询口径为 **当前用户**：`ApprovalNotification.objects.filter(user=request.user).order_by("-created_at")`。  
  证据：`plan_management/views_notifications.py` 中 `NotificationListAPI.get_queryset()`（L19–28）；可选过滤 `is_read`。  
- **接口**：`GET /api/plan/notifications/`（NotificationListAPI）。  
  证据：`plan_management/urls.py` L29。  
- **说明**：全局 `api/notifications/`（core.api_views.notification_list）聚合的是公告、项目团队、诉讼等，**不包含** plan_management.ApprovalNotification。  
  证据：`backend/core/api_views.py` L36–156 仅 Announcement、ProjectTeamNotification、LitigationNotificationConfirmation，无 ApprovalNotification。

---

## 总结：是否仍存在“两套审批机制不同步”的风险点（5 条以内）

1. **P1 – 页面提交 vs API 提交不同源**：  
   - 页面提交审批：`plan_submit_approval` 只走 **PlanStartApprovalService → 工作流 ApprovalInstance**，**不创建 PlanDecision**。  
   - API 提交（PlanViewSet start-request）：走 `request_start()`，**优先工作流**，若成功则仍会**补一条 PlanDecision**（标记用）；若工作流未配置则**仅创建 PlanDecision**。  
   - 因此：同一计划“待审批”可能只存在于 ApprovalInstance，或同时存在一条“占位” PlanDecision，列表页需合并两套数据（已做）；若前端/移动端只调 API 且环境未配工作流，会只出现 PlanDecision，与页面审批入口不一致。

2. **P1 – 审批列表双数据源合并**：  
   - `plan_approval_list` 同时查 ApprovalInstance 与 PlanDecision，分页与统计是两套分别算再合并，**未按时间统一排序**，可能出现“两页、两套统计”的体验；若业务上以工作流为准，PlanDecision 仅兼容，则需在文案/产品上明确“从哪里审批”。

3. **P0 – InboxAPI 计划侧恒为空**：  
   - `api/plan/inbox/` 的 plans 始终 `Plan.objects.none()`，前端若依赖该接口展示“待我审批的计划”会永远为空；实际待办在 **plan/plans/approval/** 页面（ApprovalInstance + PlanDecision）。需在接口文档或前端约定“计划待审批不通过 inbox，走审批列表页”。

4. **P2 – 通知列表口径不统一**：  
   - 计划/目标/待办类通知唯一来源是 `GET /api/plan/notifications/`（ApprovalNotification）；全局 `GET /api/notifications/` 不包含上述内容。若产品上有“一个通知中心”预期，需要前端聚合或后端统一入口，否则存在“两个通知列表”口径。

5. **P2 – ApprovalNotification.object_id 双格式**：  
   - 工作流创建时为 `approval_{instance.id}:{instance.object_id}`；notifications 模块内部分为 `str(obj.id)`。序列化器/详情跳转若只解析一种格式，另一种可能链错或无法跳转；建议统一约定并在一处解析（如 serializers_notifications 的 get_detail_url 已按 event/object_type 处理，需确认覆盖两种 object_id 格式）。

以上均为代码事实与证据归纳，未做理想设计建议。
