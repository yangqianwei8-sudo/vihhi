# 产值管理 V1 计算内核 —— 单元测试更新报告

**日期**：按实际完成日填写  
**依据**：`docs/output_value_v1_execution.md`、`backend.apps.output_value_management.tests.test_calculator_v1`

---

## 一、已完成任务

1. **单元测试补全**：已按要求补充 `calculate_dynamic_output` 和 `is_milestone_completed` 的用例。
2. **新增测试用例**：
   - 针对不同场景（如无商机、无里程碑等）验证 `calculate_dynamic_output` 和 `is_milestone_completed`。
   - 测试包括商机金额为 0、里程碑未完成、极端金额等边界情况。
3. **测试分层**：
   - `CalculatorV1MinimalTest`：不依赖 `Project/Record` 的纯逻辑。
   - `CalculatorV1WithDataTest`：依赖商机/阶段等数据的场景。
   - `CalculatorV1MilestoneCompletionTest`：里程碑完成度判定（含 `Project` 和 `OutputValueRecord`）。
   - `CalculatorV1FormulaWithCompletedMilestoneTest`：有已完成里程碑时的公式与 `confidence`。

---

## 二、运行说明

- 需先完成测试库迁移（`production_management_project` 等表）后执行。
- 执行命令：`python manage.py test backend.apps.output_value_management.tests.test_calculator_v1 --keepdb`

---

## 三、下一步

1. **代码集成与上线**：将计算内核与相关 API 或业务流程进行联调与上线准备。
2. **执行单元测试**：在测试库迁移完成后运行单元测试验证功能。
