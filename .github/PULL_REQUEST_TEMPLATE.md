## 变更说明
<!-- 简要说明本 PR 的目的与主要改动 -->

## 影响范围
<!-- 涉及模块、接口、页面等 -->

---

### 计划模块相关（若未改动计划模块可跳过）

**若本 PR 涉及 `plan_management`（计划管理）或相关页面/API/权限/工作流**，请勾选并确认已按 [计划模块安全回归清单](backend/apps/plan_management/docs/plan_security_regression.md) 执行：

- [ ] 已阅读 `plan_security_regression.md` 中「安全回归 10 条」
- [ ] 已确认无新增 `get_object_or_404(Plan, id=...)` / `get_object_or_404(StrategicGoal, id=...)` 裸取（Plan 用 `get_plan_or_404`，Goal 用 `get_goal_qs_for_user`）
- [ ] 已确认 Plan API（PlanViewSet）未绕过 `get_queryset` 的公司隔离与权限过滤
- [ ] （可选）已跑 `plan_management.tests.test_plan_visibility_p0_p1` 或相关回归

**未涉及计划模块**：本 PR 不修改 `backend/apps/plan_management` 及计划相关调用，上述勾选不适用。

---

## 测试
<!-- 如何验证本改动 -->

## 其他
<!-- 截图、依赖、迁移说明等 -->
