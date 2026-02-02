# 计划模块安全回归清单

**适用场景**：任何涉及 `plan_management` 的代码改动（页面、API、权限、工作流、模型等）。  
**要求**：提 PR/MR 前必须勾选并确认本清单，合并前 Reviewer 可据此抽查。

---

## 安全回归 10 条（必跑）

- [ ] **1. 计划列表隔离**  
  计划列表仅展示本公司且符合权限（view_all 或 负责人/owner）的计划；未调用 `apply_company_scope` 的列表入口已改为使用 `get_plan_qs_for_user`（内含公司范围 + `_filter_plans_by_permission`）。

- [ ] **2. 计划详情可见性**  
  计划详情页：无 `plan_management.view` 或 计划不在当前用户可见范围内 时，应 404 或 redirect 到列表；取数必须使用 `get_plan_or_404(request, plan_id)`，禁止 `get_object_or_404(Plan, id=plan_id)`。

- [ ] **3. 计划编辑越权**  
  计划编辑：仅能编辑本公司且可见范围内的计划；取数必须使用 `get_plan_or_404`，禁止仅凭 `plan.manage` + `get_object_or_404(Plan, id=)`。

- [ ] **4. 计划删除越权**  
  计划删除：仅能删除本公司且可见范围内的计划；取数必须使用 `get_plan_or_404`，禁止仅凭 `plan.manage` + `get_object_or_404(Plan, id=)`。

- [ ] **5. 计划提交审批范围**  
  提交审批：仅能对本公司且可见范围内的计划发起审批；取数必须使用 `get_plan_or_404`，禁止仅凭 create/负责人 + `get_object_or_404(Plan, id=)`。

- [ ] **6. 决策通过/驳回范围**  
  决策通过/驳回：仅能对本公司且可见范围内的待审批 `PlanDecision` 操作；取数必须使用 `get_pending_decision_or_404(request, decision_id)`，禁止仅凭 `approve_plan` + `get_object_or_404(PlanDecision, id=)`。

- [ ] **7. 战略目标详情/编辑/删除可见性**  
  战略目标详情、编辑、删除：仅能操作列表可见范围内的目标（view_all / view_assigned / 负责人/参与人/公司级）；取数必须使用 `get_object_or_404(get_goal_qs_for_user(request), id=goal_id)`，禁止 `get_object_or_404(StrategicGoal, id=goal_id)`。

- [ ] **8. 创建下级目标父目标范围**  
  创建下级目标时，父目标必须位于当前用户可见目标范围内；取数使用 `get_object_or_404(get_goal_qs_for_user(request), id=parent_goal_id)`，禁止 `get_object_or_404(StrategicGoal, id=parent_goal_id)`。

- [ ] **9. Plan API 无绕过**  
  `PlanViewSet` 的 list / retrieve / update / destroy 及所有自定义 action 均通过 `get_queryset()` 获取数据；`get_queryset` 必须包含公司隔离（或 `apply_company_scope`）与 `_filter_plans_by_permission`，不得存在按裸 `Plan.objects.get(pk=...)` 或 `get_object_or_404(Plan, id=...)` 的入口。

- [ ] **10. 无遗漏裸取 Plan/StrategicGoal**  
  全项目（含本 app 及引用 plan_management 的其它 app）中，不得存在通过 `get_object_or_404(Plan, id=...)` 或 `get_object_or_404(StrategicGoal, id=...)` 直接按 id 取实体的入口；Plan 统一走 `get_plan_or_404` 或 `get_plan_qs_for_user`，StrategicGoal 统一走 `get_goal_qs_for_user` 再 `get_object_or_404(..., id=...)`。

---

## 检查方式建议

| 条目 | 建议检查方式 |
|------|--------------|
| 1 | 多公司环境下看计划列表是否只显示本公司；无 view_all 时是否只显示本人负责/owner。 |
| 2–5 | 用无权限或他公司 plan_id 直接访问详情/编辑/删除/提交审批 URL，应 404 或 redirect。 |
| 6 | 用他公司 decision_id 调用通过/驳回，应 404 或 403。 |
| 7–8 | 用无可见性的 goal_id/parent_goal_id 访问目标详情/编辑/删除或创建下级目标，应 404 或 403。 |
| 9 | 代码搜索：`PlanViewSet` 内无 `Plan.objects.get` / `get_object_or_404(Plan,`；所有单条取数均通过 `self.get_object()`。 |
| 10 | 全项目 grep：`get_object_or_404(Plan, id=`、`get_object_or_404(StrategicGoal, id=` 仅出现在文档或注释中，不出现在可执行代码路径。 |

---

## 相关文档

- 权限与数据隔离事实：`B0_PLAN_AUDIT_D.md`
- 状态与审批机制：`B0_PLAN_AUDIT_B_C.md`
- 自动化测试：`tests/test_plan_visibility_p0_p1.py`
