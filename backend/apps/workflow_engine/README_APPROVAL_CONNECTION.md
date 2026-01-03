# 审批流程与审批实例连接说明

## 概述

审批流程模板（`WorkflowTemplate`）通过 `ApprovalEngine.start_approval()` 方法连接到具体的审批实例（`ApprovalInstance`）。审批实例通过 Django 的 ContentTypes 框架关联到具体的业务对象（如发文、合同等）。

## 连接机制

### 1. 数据模型关系

```
WorkflowTemplate (流程模板)
    ↓ (ForeignKey)
ApprovalInstance (审批实例)
    ↓ (GenericForeignKey via content_type + object_id)
ContentObject (业务对象，如 OutgoingDocument)
```

### 2. 核心字段

**ApprovalInstance 模型的关键字段：**
- `workflow`: ForeignKey 关联到 WorkflowTemplate
- `content_type`: ForeignKey 关联到 ContentType（业务对象类型）
- `object_id`: PositiveIntegerField（业务对象ID）
- `current_node`: ForeignKey 关联到 ApprovalNode（当前审批节点）

### 3. 连接方式

#### 方式一：通过流程代码（推荐）

```python
from backend.apps.workflow_engine.services import ApprovalEngine
from backend.apps.workflow_engine.models import WorkflowTemplate
from backend.apps.delivery_customer.models import OutgoingDocument

# 1. 获取流程模板（通过流程代码）
workflow = WorkflowTemplate.objects.get(code='document_approval', status='active')

# 2. 获取业务对象
document = OutgoingDocument.objects.get(id=123)

# 3. 启动审批流程
instance = ApprovalEngine.start_approval(
    workflow=workflow,
    content_object=document,  # 业务对象
    applicant=request.user,   # 申请人
    comment='请审批此发文'     # 申请说明
)

# 4. 审批实例已创建，关联关系已建立
# instance.workflow -> WorkflowTemplate
# instance.content_object -> OutgoingDocument实例
# instance.current_node -> 第一个审批节点
```

#### 方式二：通过流程名称

```python
workflow = WorkflowTemplate.objects.get(name='发文审批流程', status='active')
instance = ApprovalEngine.start_approval(
    workflow=workflow,
    content_object=document,
    applicant=request.user,
    comment='请审批此发文'
)
```

## 实际使用示例

### 示例1：发文提交时启动审批

```python
# 在发文提交视图中
@login_required
def outgoing_document_submit(request, document_id):
    document = OutgoingDocument.objects.get(id=document_id)
    
    # 检查是否已有审批实例
    from django.contrib.contenttypes.models import ContentType
    from backend.apps.workflow_engine.models import ApprovalInstance
    
    content_type = ContentType.objects.get_for_model(OutgoingDocument)
    existing_instance = ApprovalInstance.objects.filter(
        content_type=content_type,
        object_id=document.id,
        status__in=['pending', 'approved']
    ).first()
    
    if existing_instance:
        messages.warning(request, '该发文已有审批流程')
        return redirect('delivery_pages:outgoing_document_detail', document_id=document.id)
    
    # 获取流程模板
    try:
        workflow = WorkflowTemplate.objects.get(
            code='document_approval',  # 发文审批流程代码
            status='active'
        )
    except WorkflowTemplate.DoesNotExist:
        messages.error(request, '未找到启用的发文审批流程')
        return redirect('delivery_pages:outgoing_document_detail', document_id=document.id)
    
    # 启动审批流程
    from backend.apps.workflow_engine.services import ApprovalEngine
    
    try:
        instance = ApprovalEngine.start_approval(
            workflow=workflow,
            content_object=document,
            applicant=request.user,
            comment=f'提交发文审批：{document.title}'
        )
        
        # 更新业务对象状态
        document.status = 'reviewing'  # 审核中
        document.save()
        
        messages.success(request, f'审批流程已启动，实例编号：{instance.instance_number}')
        return redirect('workflow_engine:approval_detail', instance_id=instance.id)
        
    except Exception as e:
        logger.exception('启动审批流程失败')
        messages.error(request, f'启动审批流程失败：{str(e)}')
        return redirect('delivery_pages:outgoing_document_detail', document_id=document.id)
```

### 示例2：从业务对象获取审批实例

```python
# 获取业务对象的审批实例
from django.contrib.contenttypes.models import ContentType
from backend.apps.workflow_engine.models import ApprovalInstance

def get_approval_instance(content_object):
    """获取业务对象的审批实例"""
    content_type = ContentType.objects.get_for_model(content_object)
    return ApprovalInstance.objects.filter(
        content_type=content_type,
        object_id=content_object.id
    ).order_by('-created_time').first()

# 使用
document = OutgoingDocument.objects.get(id=123)
instance = get_approval_instance(document)

if instance:
    print(f"审批实例编号：{instance.instance_number}")
    print(f"审批状态：{instance.get_status_display()}")
    print(f"当前节点：{instance.current_node.name if instance.current_node else '无'}")
```

### 示例3：在业务对象模型中添加便捷方法

```python
# 在 OutgoingDocument 模型中添加
from django.contrib.contenttypes.fields import GenericRelation

class OutgoingDocument(models.Model):
    # ... 其他字段 ...
    
    # 添加通用关系（可选，用于反向查询）
    approval_instances = GenericRelation(
        'workflow_engine.ApprovalInstance',
        content_type_field='content_type',
        object_id_field='object_id',
        related_query_name='outgoing_document'
    )
    
    def get_current_approval_instance(self):
        """获取当前审批实例"""
        return self.approval_instances.filter(
            status__in=['pending', 'approved']
        ).order_by('-created_time').first()
    
    def start_approval_workflow(self, workflow_code='document_approval', applicant=None, comment=''):
        """启动审批流程"""
        from backend.apps.workflow_engine.models import WorkflowTemplate
        from backend.apps.workflow_engine.services import ApprovalEngine
        
        try:
            workflow = WorkflowTemplate.objects.get(code=workflow_code, status='active')
        except WorkflowTemplate.DoesNotExist:
            raise ValueError(f'未找到流程代码为 {workflow_code} 的启用流程')
        
        return ApprovalEngine.start_approval(
            workflow=workflow,
            content_object=self,
            applicant=applicant,
            comment=comment
        )

# 使用
document = OutgoingDocument.objects.get(id=123)
instance = document.start_approval_workflow(
    workflow_code='document_approval',
    applicant=request.user,
    comment='请审批此发文'
)
```

## 流程代码配置

### 流程代码的作用

流程代码（`WorkflowTemplate.code`）是连接业务对象和审批流程的关键：

1. **唯一标识**：每个流程模板有唯一的代码
2. **业务映射**：业务代码通过流程代码找到对应的审批流程
3. **自动关联**：启动审批时，通过代码自动关联流程模板

### 常见流程代码示例

- `document_approval` - 发文审批流程
- `contract_approval` - 合同审批流程
- `customer_approval` - 客户审批流程
- `project_approval` - 项目审批流程

## 审批实例的生命周期

1. **创建**：调用 `ApprovalEngine.start_approval()` 创建实例
2. **关联**：通过 `content_type` 和 `object_id` 关联业务对象
3. **流转**：通过 `current_node` 跟踪当前审批节点
4. **完成**：状态变为 `approved` 或 `rejected`
5. **同步**：通过 `_sync_content_object_status()` 同步业务对象状态

## 注意事项

1. **流程代码必须唯一**：确保每个业务类型有对应的流程代码
2. **流程状态**：只有 `status='active'` 的流程才能启动审批
3. **避免重复**：启动前检查是否已有审批实例
4. **异常处理**：启动审批可能失败（如找不到审批人），需要处理异常
5. **状态同步**：审批完成后需要同步更新业务对象状态

## 完整连接流程示例

### 步骤1：创建流程模板

在后台创建流程模板，设置流程代码（如 `document_approval`），配置节点。

### 步骤2：在业务代码中启动审批

```python
from backend.apps.workflow_engine.services import ApprovalEngine
from backend.apps.workflow_engine.models import WorkflowTemplate

# 获取流程模板
workflow = WorkflowTemplate.objects.get(code='document_approval', status='active')

# 启动审批
instance = ApprovalEngine.start_approval(
    workflow=workflow,
    content_object=document,  # 业务对象
    applicant=request.user,
    comment='请审批此发文'
)
```

### 步骤3：审批流程自动执行

- 系统自动创建审批记录（`ApprovalRecord`）
- 根据节点配置查找审批人
- 审批人审批后，自动流转到下一个节点
- 流程完成后，自动同步业务对象状态

### 步骤4：状态同步

审批完成后，系统会调用 `_sync_content_object_status()` 方法，自动更新业务对象的状态：

- `approved` -> 业务对象状态更新为 `approved`
- `rejected` -> 业务对象状态更新为 `rejected`

## 查询审批实例

### 从业务对象查询审批实例

```python
from django.contrib.contenttypes.models import ContentType
from backend.apps.workflow_engine.models import ApprovalInstance

content_type = ContentType.objects.get_for_model(OutgoingDocument)
instance = ApprovalInstance.objects.filter(
    content_type=content_type,
    object_id=document.id
).first()
```

### 从审批实例查询业务对象

```python
# 通过 content_object 属性（Django GenericForeignKey）
content_object = instance.content_object  # 返回 OutgoingDocument 实例

# 或者手动查询
content_object = instance.content_type.get_object_for_this_type(
    id=instance.object_id
)
```

## 相关文件

- `backend/apps/workflow_engine/models.py` - 数据模型定义
- `backend/apps/workflow_engine/services.py` - 审批引擎服务
- `backend/apps/workflow_engine/views_pages.py` - 视图函数
- `backend/apps/workflow_engine/examples/start_approval_example.py` - 示例代码

