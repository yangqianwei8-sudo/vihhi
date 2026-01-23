# 计划审批迁移至审批引擎 - 迁移文档

## 概述

本次迁移将计划管理的计划审批功能从 `PlanDecision` 模型迁移至审批引擎（`workflow_engine`）进行集中管理。

## 迁移内容

### 1. 新增文件

#### 1.1 计划审批服务
- **文件**: `services/plan_approval.py`
- **功能**: 
  - `PlanApprovalService`: 计划审批服务类
  - `submit_start_approval()`: 提交计划启动审批
  - `submit_cancel_approval()`: 提交计划取消审批
  - `get_plan_approval_instance()`: 获取计划的审批实例
  - `check_approval_status()`: 检查审批状态
  - `handle_approval_result()`: 处理审批结果，更新计划状态

#### 1.2 信号处理器
- **文件**: `signals.py`
- **功能**: 监听审批实例状态变化，自动更新计划状态
- **注册**: 在 `apps.py` 的 `ready()` 方法中注册

#### 1.3 审批流程初始化命令
- **文件**: `management/commands/init_plan_approval_workflows.py`
- **功能**: 初始化计划审批流程模板
- **运行方式**: `python manage.py init_plan_approval_workflows`

### 2. 修改的文件

#### 2.1 `apps.py`
- 添加 `ready()` 方法，注册信号处理器

#### 2.2 `services/plan_decisions.py`
- `request_start()`: 优先使用审批引擎，如果审批流程未配置则回退到 PlanDecision
- `request_cancel()`: 优先使用审批引擎，如果审批流程未配置则回退到 PlanDecision
- 保持向后兼容性

#### 2.3 `views_pages.py`
- `plan_detail()`: 同时检查审批引擎和 PlanDecision 的待审批状态
- `plan_request_start()`: 使用审批引擎提交启动审批
- `plan_request_cancel()`: 使用审批引擎提交取消审批
- `plan_approval_list()`: 同时显示审批引擎和 PlanDecision 的审批列表
- `plan_edit()`: 检查审批引擎的待审批状态

## 审批流程配置

### 流程代码
- **计划启动审批**: `plan_start_approval`
- **计划取消审批**: `plan_cancel_approval`

### 审批节点
- 默认使用部门经理（`department_manager`）作为审批人
- 可在后台管理系统中手动配置审批节点，指定特定用户或角色

## 使用说明

### 1. 初始化审批流程

首次使用前，需要运行初始化命令创建审批流程模板：

```bash
python manage.py init_plan_approval_workflows
```

如果需要强制重新创建（会删除现有节点），使用：

```bash
python manage.py init_plan_approval_workflows --force
```

### 2. 提交审批

#### 方式一：通过页面提交（推荐）
- 在计划详情页面，点击"提交审批"按钮
- 系统会自动使用审批引擎创建审批实例

#### 方式二：通过 API 提交
```python
from backend.apps.plan_management.services.plan_approval import PlanApprovalService

# 提交启动审批
approval_instance = PlanApprovalService.submit_start_approval(
    plan=plan,
    applicant=user,
    comment="申请启动计划"
)

# 提交取消审批
approval_instance = PlanApprovalService.submit_cancel_approval(
    plan=plan,
    applicant=user,
    comment="申请取消计划"
)
```

### 3. 审批操作

审批操作通过审批引擎的统一界面进行：
- 访问审批列表页面：`/plan/plans/approval/`
- 或通过审批引擎的审批详情页面进行审批

### 4. 审批结果处理

审批结果通过信号处理器自动处理：
- **启动审批通过**: 计划状态从 `draft` 变为 `published`
- **取消审批通过**: 计划状态从 `in_progress` 变为 `cancelled`
- **审批驳回**: 计划状态保持不变，记录驳回日志

## 向后兼容性

为了保持向后兼容，系统同时支持：
1. **审批引擎**（新方式，推荐）
2. **PlanDecision**（旧方式，如果审批流程未配置则自动回退）

如果审批流程模板未配置或不可用，系统会自动回退到使用 `PlanDecision` 的方式。

## 数据迁移

### 现有 PlanDecision 数据
- 现有的 `PlanDecision` 数据不会被删除
- 系统会同时显示审批引擎和 PlanDecision 的审批请求
- 建议逐步将现有的 PlanDecision 审批完成，之后新提交的审批将使用审批引擎

### 审批历史
- 审批引擎的审批记录保存在 `ApprovalInstance` 和 `ApprovalRecord` 表中
- PlanDecision 的审批记录继续保存在 `PlanDecision` 表中
- 两种方式的审批历史都可以在系统中查看

## 注意事项

1. **审批流程配置**: 首次使用前必须运行初始化命令创建审批流程模板
2. **审批人配置**: 默认使用部门经理，如需指定特定用户或角色，请在后台管理系统中配置
3. **权限要求**: 审批操作需要 `plan_management.approve_plan` 权限
4. **公司数据隔离**: 审批列表会自动应用公司数据隔离，只显示同一公司的审批请求

## 辅助函数

### get_plan_approval_info()
获取计划的审批信息（包括审批引擎和 PlanDecision）：

```python
from backend.apps.plan_management.services.plan_approval import PlanApprovalService

approval_info = PlanApprovalService.get_plan_approval_info(plan)
# 返回：
# {
#     'has_pending_start': bool,
#     'has_pending_cancel': bool,
#     'start_approval_instance': ApprovalInstance | None,
#     'cancel_approval_instance': ApprovalInstance | None,
#     'pending_decisions': QuerySet,
# }
```

## 后续优化建议

1. **完全移除 PlanDecision**: 在所有审批流程配置完成后，可以考虑完全移除 PlanDecision 的支持
2. **审批流程自定义**: 允许用户根据不同计划类型配置不同的审批流程
3. **审批超时处理**: 配置审批超时后的自动处理机制
4. **审批通知优化**: 优化审批通知的内容和方式
5. **统一审批界面**: 在计划详情页面统一显示审批引擎和 PlanDecision 的审批信息

## 相关文件

- `services/plan_approval.py`: 计划审批服务
- `signals.py`: 审批状态变化信号处理器
- `management/commands/init_plan_approval_workflows.py`: 审批流程初始化命令
- `services/plan_decisions.py`: 计划决策服务（已集成审批引擎）
- `views_pages.py`: 页面视图（已更新支持审批引擎）

## 测试建议

1. 测试审批流程初始化命令
2. 测试提交启动审批
3. 测试提交取消审批
4. 测试审批通过后的状态变更
5. 测试审批驳回后的状态保持
6. 测试审批列表显示
7. 测试向后兼容性（审批流程未配置时的回退）

