# 行政管理审批服务改造说明

## 改造概述

根据系统最新的通用审批流程服务（`UniversalApprovalService`），已将行政管理模块的审批流程改造为使用统一的服务接口。

## 改造内容

### 1. 创建的服务类

#### LoanApprovalService（借款审批服务）
- **文件**: `services/loan_approval.py`
- **流程代码**: `loan_approval`
- **验证逻辑**:
  - 检查借款申请状态（必须是草稿或待审批状态）
  - 验证借款金额必须大于0
  - 验证借款日期和借款事由不能为空
  - 验证申请人必须属于某个部门

#### SealBorrowingApprovalService（印章借用审批服务）
- **文件**: `services/seal_borrowing_approval.py`
- **流程代码**: `seal_borrowing_approval`
- **验证逻辑**:
  - 检查印章借用状态（必须是待审批状态）
  - 验证必须选择印章
  - 验证借用事由和预计归还日期不能为空
  - 验证申请人必须属于某个部门

#### SealUsageApprovalService（用印申请审批服务）
- **文件**: `services/seal_usage_approval.py`
- **流程代码**: `seal_usage_approval`
- **验证逻辑**:
  - 检查用印申请状态（必须是待审批状态）
  - 验证必须选择印章
  - 验证用印事由不能为空
  - 验证申请人必须属于某个部门

### 2. 改造的视图函数

#### 借款申请创建视图 (`loan_create`)
- **位置**: `views_pages.py` 第7750-7786行
- **改造前**: 直接使用 `ApprovalEngine.start_approval`
- **改造后**: 使用 `LoanApprovalService.submit_approval`
- **改进**:
  - 统一的错误处理（区分验证错误和其他错误）
  - 更清晰的错误提示
  - 自动检查是否已有待审批实例

#### 印章借用申请视图 (`seal_borrowing_create`)
- **位置**: `views_pages.py` 第2656-2681行
- **改造前**: 直接使用 `ApprovalEngine.start_approval`
- **改造后**: 使用 `SealBorrowingApprovalService.submit_approval`
- **改进**: 同上

#### 用印申请视图 (`seal_usage_create`)
- **位置**: `views_pages.py` 第2884-2940行
- **改造前**: 直接使用 `ApprovalEngine.start_approval`
- **改造后**: 使用 `SealUsageApprovalService.submit_approval`
- **改进**: 
  - 同上
  - 保留了原有的行政主管抄送逻辑

## 使用方式

### 提交审批

```python
from backend.apps.administrative_management.services import LoanApprovalService

service = LoanApprovalService()
try:
    instance = service.submit_approval(
        obj=loan_application,
        applicant=request.user,
        comment='申请说明'
    )
    if instance:
        # 审批流程已启动
        pass
    else:
        # 审批流程未配置
        pass
except ValueError as e:
    # 验证失败
    pass
```

### 审批操作

```python
# 审批通过
service.approve(instance_id, approver=user, comment='同意')

# 审批驳回
service.reject(instance_id, approver=user, comment='不同意')

# 撤回审批
service.withdraw(instance_id, applicant=user)
```

### 查询审批状态

```python
status = service.get_approval_status(loan_application)
# 返回:
# {
#     'has_pending': bool,
#     'instance': ApprovalInstance | None,
#     'current_node': str | None,
#     'approvers': List[User],
#     'status': str,
#     'can_submit': bool,
#     'can_approve': bool,
# }
```

## 优势

1. **统一接口**: 所有审批流程使用相同的接口，代码更易维护
2. **自动验证**: 提交前自动进行数据验证，减少错误
3. **错误处理**: 统一的错误处理机制，用户体验更好
4. **易于扩展**: 可以轻松添加新的验证逻辑或业务规则
5. **状态查询**: 提供完整的审批状态查询接口

## 注意事项

1. 审批流程模板必须在数据库中配置并启用（`status='active'`）
2. 审批人类型为 `department_manager` 时，需要确保部门负责人已设置
3. 提交审批前会自动检查是否已有待审批实例，避免重复提交
4. 验证失败会抛出 `ValueError`，需要在视图中捕获并显示给用户

## 后续改进建议

1. 可以考虑在审批通过/驳回后添加业务状态更新逻辑
2. 可以添加审批通知功能
3. 可以添加审批历史查询功能
4. 可以考虑添加批量审批功能
