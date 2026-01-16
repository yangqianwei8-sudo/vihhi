# Plan.status 写入点清单（P1 v2 收口）

## ⚠️ P1 规则：Plan.status 只允许在以下写入点发生改变

**不可推翻条款：**

1. **PlanDecision `decide(approve)`** - 裁决器修改状态
2. **`recalc_plan_status()` 系统完成** - 进度>=100自动完成

**其它入口一律视为违规（必须返回 410/409）**

---

## ✅ 允许的写入点（P1 v2 允许）

### 1. 裁决器修改（P1 核心）
- **位置：** `services/plan_decisions.py::decide()`
- **触发：** `approve start` → `draft` → `in_progress`
- **触发：** `approve cancel` → `in_progress` → `cancelled`
- **状态：** ✅ 符合 P1 规则

### 2. 系统完成判定（P1 核心）
- **位置：** `services/recalc_status.py::recalc_plan_status()`
- **触发：** `progress >= 100` → `in_progress` → `completed`
- **状态：** ✅ 符合 P1 规则

### 3. 进度/时间更新触发重算（间接调用 recalc）
- **位置：** `views.py::perform_update()`
- **调用链：** `recalc_plan_status()` → `adjudicate_plan_status()`
- **状态：** ✅ 符合 P1 规则（间接调用裁决器）

### 4. 进度更新触发重算（间接调用 recalc）
- **位置：** `views.py::update_progress()`
- **调用链：** `recalc_plan_status()` → `adjudicate_plan_status()`
- **状态：** ✅ 符合 P1 规则（间接调用裁决器）

### 5. 批量重算命令（管理命令）
- **位置：** `management/commands/recalc_plan_statuses.py`
- **调用链：** `recalc_plan_status()` → `adjudicate_plan_status()`
- **状态：** ✅ 符合 P1 规则（间接调用裁决器）

---

## ⚠️ 需要收口的写入点（旧逻辑，P1 应禁用）

### 6. 手动状态变更（旧接口，P1 应禁用）
- **位置：** `views.py::change_status()`
- **问题：** 允许直接修改状态，绕过裁决机制
- **建议：** P1 应禁用此接口，或改为调用裁决器

### 7. 审批通过（旧审批流，P1 应禁用）
- **位置：** `views.py::approve()`
- **问题：** 旧审批流，P1 应使用 PlanDecision 裁决
- **状态：** ⚠️ P1 应禁用或标记为废弃

### 8. 审批驳回（旧审批流，P1 应禁用）
- **位置：** `views.py::reject()`
- **问题：** 旧审批流，P1 应使用 PlanDecision 裁决
- **状态：** ⚠️ P1 应禁用或标记为废弃

### 9. 取消审批（旧审批流，P1 应禁用）
- **位置：** `views.py::cancel_approval()`
- **问题：** 旧审批流，P1 应使用 PlanDecision 裁决
- **状态：** ⚠️ P1 应禁用或标记为废弃

### 10. 提交审批（旧审批流，P1 应禁用）
- **位置：** `views.py::submit_approval()`
- **问题：** 旧审批流，P1 应使用 `start-request`
- **状态：** ⚠️ P1 应禁用或标记为废弃

### 11. 页面完成确认（旧逻辑，P1 应禁用）
- **位置：** `views_pages.py::plan_execution_track()`
- **问题：** 直接调用 `plan.transition_to('completed')`，绕过裁决机制
- **建议：** P1 应禁用，或改为调用 `recalc_plan_status()`（如果 progress>=100）

### 12. 模型方法 transition_to（旧逻辑，P1 应禁用）
- **位置：** `models.py::Plan.transition_to()`
- **问题：** 允许直接修改状态，绕过裁决机制
- **建议：** P1 应禁用，或改为调用裁决器

---

## ✅ 测试/工具写入点（允许）

### 13. 测试用例
- **位置：** `tests/test_plan_decision_v2.py`
- **状态：** ✅ 允许（测试用）

### 14. 创建测试数据
- **位置：** `management/commands/create_test_plans.py`
- **状态：** ✅ 允许（测试用）

---

## 收口建议

### 立即收口（P1 上线前）
1. **禁用 `change_status` 接口**：或改为调用裁决器
2. **禁用页面完成确认**：改为调用 `recalc_plan_status()`
3. **标记旧审批流接口为废弃**：`approve()`, `reject()`, `cancel_approval()`, `submit_approval()`

### 后续收口（P2 阶段）
1. **重构 `transition_to()` 方法**：改为调用裁决器
2. **统一状态变更入口**：所有状态变更都通过裁决器

---

**最后更新：** 2026-01-12  
**版本：** P1 v2

