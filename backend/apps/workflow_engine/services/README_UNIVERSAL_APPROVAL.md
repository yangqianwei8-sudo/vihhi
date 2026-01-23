# 通用审批流程服务使用指南

## 概述

`UniversalApprovalService` 提供了一个统一的审批流程接口，让各个业务模块可以方便地复用审批功能，无需重复编写审批逻辑。

## 核心特性

- ✅ **统一接口**：所有业务模块使用相同的审批接口
- ✅ **灵活配置**：支持多种审批人类型和审批模式
- ✅ **易于扩展**：子类可以重写验证逻辑
- ✅ **状态查询**：提供完整的审批状态查询接口
- ✅ **流程配置**：支持通过配置快速创建审批流程

## 快速开始

### 1. 创建业务审批服务类

```python
# apps/contract_management/services/contract_approval.py
from backend.apps.workflow_engine.services.universal_approval import UniversalApprovalService
from backend.apps.customer_management.models import BusinessContract

class ContractApprovalService(UniversalApprovalService):
    """合同审批服务"""
    
    # 必须设置：审批流程代码
    WORKFLOW_CODE = 'contract_approval'
    
    # 可选：关联的业务模型（用于类型提示）
    CONTENT_MODEL = BusinessContract
    
    def validate_before_submit(self, obj, applicant):
        """提交审批前的验证"""
        # 检查合同状态
        if obj.status != 'draft':
            raise ValueError('只有草稿状态的合同可以提交审批')
        
        # 检查必填字段
        if not obj.contract_amount:
            raise ValueError('合同金额不能为空')
        
        # 检查金额阈值
        if obj.contract_amount > 1000000:
            raise ValueError('金额超过100万需要特殊审批流程')
```

### 2. 提交审批

```python
from apps.contract_management.services.contract_approval import ContractApprovalService

# 在视图函数中使用
def submit_contract_approval(request, contract_id):
    contract = get_object_or_404(BusinessContract, id=contract_id)
    service = ContractApprovalService()
    
    try:
        instance = service.submit_approval(
            obj=contract,
            applicant=request.user,
            comment='申请审批合同'
        )
        
        if instance:
            messages.success(request, f'已提交审批，审批编号：{instance.instance_number}')
        else:
            messages.warning(request, '审批流程未配置，请联系管理员')
            
    except ValueError as e:
        messages.error(request, str(e))
    
    return redirect('contract_detail', contract_id=contract_id)
```

### 3. 审批操作

```python
def approve_contract(request, instance_id):
    service = ContractApprovalService()
    
    if service.approve(
        instance_id=instance_id,
        approver=request.user,
        comment='同意，合同条款符合要求'
    ):
        messages.success(request, '审批通过')
    else:
        messages.error(request, '审批失败')
    
    return redirect('contract_approval_list')
```

### 4. 查询审批状态

```python
def contract_detail(request, contract_id):
    contract = get_object_or_404(BusinessContract, id=contract_id)
    service = ContractApprovalService()
    
    # 获取审批状态
    approval_status = service.get_approval_status(contract)
    
    context = {
        'contract': contract,
        'approval_status': approval_status,
        'can_submit': approval_status['can_submit'],
        'can_approve': approval_status['can_approve'],
        'current_approvers': approval_status['approvers'],
    }
    
    return render(request, 'contract_detail.html', context)
```

## 高级用法

### 自定义审批流程配置

```python
from backend.apps.workflow_engine.services.universal_approval import UniversalApprovalService
from backend.apps.system_management.models import User, Role

# 创建审批流程
creator = User.objects.filter(is_superuser=True).first()

workflow = UniversalApprovalService.create_workflow_from_config(
    code='contract_approval',
    name='合同审批流程',
    description='合同审批流程：部门经理 -> 财务总监 -> 总经理',
    category='合同管理',
    creator=creator,
    allow_withdraw=True,
    allow_reject=True,
    allow_transfer=False,
    timeout_hours=24,
    nodes_config=[
        {
            'name': '部门经理审批',
            'node_type': 'approval',
            'sequence': 1,
            'approver_type': 'department_manager',  # 自动获取申请人部门经理
            'approval_mode': 'single',
            'timeout_hours': 24,
            'can_reject': True,
            'can_transfer': True,
        },
        {
            'name': '财务总监审批',
            'node_type': 'approval',
            'sequence': 2,
            'approver_type': 'role',
            'approval_mode': 'single',
            'approver_roles': [Role.objects.get(code='finance_director')],
            'timeout_hours': 48,
            'can_reject': True,
            'can_transfer': False,
        },
        {
            'name': '总经理审批',
            'node_type': 'approval',
            'sequence': 3,
            'approver_type': 'role',
            'approval_mode': 'single',
            'approver_roles': [Role.objects.get(code='general_manager')],
            'timeout_hours': 72,
            'can_reject': True,
            'can_transfer': False,
        },
    ]
)
```

### 审批人类型说明

| 类型 | 说明 | 示例 |
|------|------|------|
| `user` | 指定用户 | 固定审批人 |
| `role` | 指定角色 | 所有具有该角色的用户 |
| `department` | 指定部门 | 部门内所有用户 |
| `department_manager` | 部门经理 | 申请人所在部门的负责人 |
| `creator` | 创建人 | 申请人自己 |
| `creator_manager` | 创建人上级 | 申请人的上级 |
| `custom` | 自定义规则 | 需要自定义逻辑 |

### 审批模式说明

| 模式 | 说明 | 适用场景 |
|------|------|----------|
| `single` | 单人审批 | 标准审批流程 |
| `any` | 任意一人通过 | 多人中任意一人审批即可 |
| `all` | 全部通过 | 需要所有人同意 |
| `majority` | 多数通过 | 超过半数同意即可 |

### 获取待审批列表

```python
def my_pending_approvals(request):
    service = ContractApprovalService()
    
    # 获取当前用户的待审批列表
    pending_list = service.get_pending_approvals(request.user)
    
    context = {
        'pending_approvals': pending_list,
    }
    
    return render(request, 'my_pending_approvals.html', context)
```

### 获取我的申请列表

```python
def my_applications(request):
    service = ContractApprovalService()
    
    # 获取当前用户的申请列表
    applications = service.get_my_applications(request.user)
    
    context = {
        'applications': applications,
    }
    
    return render(request, 'my_applications.html', context)
```

## 完整示例：合同审批模块

### 1. 服务类定义

```python
# apps/contract_management/services/contract_approval.py
from backend.apps.workflow_engine.services.universal_approval import UniversalApprovalService
from backend.apps.customer_management.models import BusinessContract

class ContractApprovalService(UniversalApprovalService):
    WORKFLOW_CODE = 'contract_approval'
    CONTENT_MODEL = BusinessContract
    
    def validate_before_submit(self, obj, applicant):
        if obj.status != 'draft':
            raise ValueError('只有草稿状态的合同可以提交审批')
        if not obj.contract_amount:
            raise ValueError('合同金额不能为空')
```

### 2. 视图函数

```python
# apps/contract_management/views.py
from .services.contract_approval import ContractApprovalService

@login_required
def submit_contract_approval(request, contract_id):
    contract = get_object_or_404(BusinessContract, id=contract_id)
    service = ContractApprovalService()
    
    try:
        instance = service.submit_approval(
            obj=contract,
            applicant=request.user,
            comment=request.POST.get('comment', '')
        )
        
        if instance:
            messages.success(request, f'已提交审批，编号：{instance.instance_number}')
        else:
            messages.warning(request, '审批流程未配置')
    except ValueError as e:
        messages.error(request, str(e))
    
    return redirect('contract_detail', contract_id=contract_id)

@login_required
def approve_contract(request, instance_id):
    service = ContractApprovalService()
    action = request.POST.get('action')  # 'approve' or 'reject'
    comment = request.POST.get('comment', '')
    
    if action == 'approve':
        success = service.approve(instance_id, request.user, comment)
        message = '审批通过' if success else '审批失败'
    elif action == 'reject':
        success = service.reject(instance_id, request.user, comment)
        message = '已驳回' if success else '驳回失败'
    else:
        messages.error(request, '无效的操作')
        return redirect('contract_approval_list')
    
    if success:
        messages.success(request, message)
    else:
        messages.error(request, message)
    
    return redirect('contract_approval_list')
```

### 3. 模板使用

```html
<!-- contract_detail.html -->
{% if approval_status.has_pending %}
    <div class="alert alert-info">
        <p>审批中：{{ approval_status.current_node }}</p>
        <p>待审批人：{{ approval_status.approvers|join:", " }}</p>
    </div>
{% elif approval_status.can_submit %}
    <form method="post" action="{% url 'submit_contract_approval' contract.id %}">
        {% csrf_token %}
        <button type="submit" class="btn btn-primary">提交审批</button>
    </form>
{% endif %}
```

## 最佳实践

1. **每个业务模块创建一个服务类**：继承 `UniversalApprovalService`，设置 `WORKFLOW_CODE`
2. **实现验证逻辑**：重写 `validate_before_submit` 方法，确保数据完整性
3. **统一错误处理**：使用 try-except 捕获 `ValueError` 并显示给用户
4. **状态查询**：使用 `get_approval_status` 获取完整状态信息
5. **流程配置**：使用 `create_workflow_from_config` 快速创建审批流程

## 注意事项

- 审批流程模板必须在数据库中配置并启用（`status='active'`）
- 审批人类型为 `department_manager` 时，需要确保部门负责人已设置
- 审批实例编号会自动生成，格式：`{workflow_code}-{日期}-{序号}`
- 提交审批前会自动检查是否已有待审批实例，避免重复提交

## 扩展开发

如果需要更复杂的审批逻辑，可以：

1. **重写服务方法**：在子类中重写 `submit_approval`、`approve` 等方法
2. **自定义审批人**：实现 `custom` 类型的审批人逻辑
3. **添加回调**：在审批通过/驳回后执行自定义业务逻辑
4. **集成通知**：在审批状态变更时发送通知

