# 列表页操作列统一实现使用指南

## 概述

`list_page_base.html` 现在提供了统一的操作列实现，无需在每个子模板中重复编写查看、编辑、删除按钮的代码。

## 功能特性

- ✅ **统一实现**：所有列表页使用相同的操作列代码
- ✅ **权限控制**：支持 `can_view`、`can_edit`、`can_delete` 权限控制
- ✅ **灵活配置**：通过视图函数传递 URL 名称即可配置
- ✅ **向后兼容**：子模板仍可完全覆盖 `list_page_table_actions_cell` 块
- ✅ **自定义消息**：支持自定义删除确认消息

## 使用方法

### 方式1：在视图函数中传递 URL 名称（推荐）

在视图函数中传递以下变量：

```python
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.core.paginator import Paginator

@login_required
def customer_list(request):
    # ... 获取数据 ...
    queryset = Customer.objects.all()
    paginator = Paginator(queryset, 10)
    page_obj = paginator.get_page(request.GET.get('page', 1))
    
    return render(request, 'customer_management/customer_list.html', {
        'page_obj': page_obj,
        
        # 权限控制
        'can_create': request.user.has_perm('customer_management.add_customer'),
        'can_edit': request.user.has_perm('customer_management.change_customer'),
        'can_delete': request.user.has_perm('customer_management.delete_customer'),
        'can_view': True,  # 默认True，可省略
        
        # 操作列URL配置（必需）
        'detail_url_name': 'business_pages:customer_detail',  # 查看详情URL名称
        'edit_url_name': 'business_pages:customer_edit',     # 编辑URL名称
        'delete_url_name': 'business_pages:customer_delete', # 删除URL名称
    })
```

### 方式2：在子模板中覆盖删除确认消息

如果需要自定义删除确认消息，可以在子模板中覆盖 `delete_confirm_message` 块：

```django
{% block delete_confirm_message %}确定要删除此客户吗？此操作不可恢复。{% endblock %}
```

### 方式3：完全自定义操作列（向后兼容）

如果某个页面需要特殊逻辑（如条件判断、额外的操作按钮等），仍可在子模板中完全覆盖：

```django
{% block list_page_table_actions_cell %}
<td>
    <div class="list-page-table-actions">
        {# 自定义操作列逻辑 #}
        {% if item.approval_instance_id %}
            <a href="{% url 'workflow_engine:approval_detail' item.approval_instance_id %}" 
               class="action-view">
                <i class="bi bi-eye"></i>
            </a>
        {% else %}
            <a href="{% url 'delivery_pages:outgoing_document_detail' item.id %}" 
               class="action-view">
                <i class="bi bi-eye"></i>
            </a>
        {% endif %}
        {# ... 其他自定义逻辑 ... #}
    </div>
</td>
{% endblock %}
```

## 配置参数说明

### 必需参数

- `detail_url_name`: 查看详情页面的 URL 名称（格式：`'app_name:view_name'`）
- `edit_url_name`: 编辑页面的 URL 名称
- `delete_url_name`: 删除操作的 URL 名称

### 可选参数

- `can_view`: 是否显示查看按钮（默认 `True`，设置为 `False` 可隐藏）
- `can_edit`: 是否显示编辑按钮（默认使用 `can_create` 的值）
- `can_delete`: 是否显示删除按钮（默认 `False`，需要显式设置为 `True`）

### 可覆盖的块

- `action_view_title`: 查看按钮的 title 属性（默认："查看详情"）
- `action_edit_title`: 编辑按钮的 title 属性（默认："编辑"）
- `action_delete_title`: 删除按钮的 title 属性（默认："删除"）
- `delete_confirm_message`: 删除确认对话框的消息（默认："确定要删除此记录吗？此操作不可恢复。"）

## 示例

### 示例1：基本使用

```python
# views.py
def opportunity_list(request):
    queryset = Opportunity.objects.all()
    paginator = Paginator(queryset, 10)
    page_obj = paginator.get_page(request.GET.get('page', 1))
    
    return render(request, 'customer_management/opportunity_list.html', {
        'page_obj': page_obj,
        'can_create': True,
        'can_delete': True,
        'detail_url_name': 'business_pages:opportunity_detail',
        'edit_url_name': 'business_pages:opportunity_edit',
        'delete_url_name': 'business_pages:opportunity_delete',
    })
```

### 示例2：自定义删除确认消息

```django
{# opportunity_list.html #}
{% block delete_confirm_message %}确定要删除此商机吗？此操作不可恢复。{% endblock %}
```

### 示例3：隐藏查看按钮

```python
# views.py
return render(request, 'xxx_list.html', {
    'page_obj': page_obj,
    'can_view': False,  # 隐藏查看按钮
    'can_create': True,
    'can_delete': True,
    'edit_url_name': 'app:edit',
    'delete_url_name': 'app:delete',
})
```

### 示例4：只显示查看和删除按钮

```python
# views.py
return render(request, 'xxx_list.html', {
    'page_obj': page_obj,
    'can_view': True,
    'can_edit': False,  # 隐藏编辑按钮
    'can_delete': True,
    'detail_url_name': 'app:detail',
    'delete_url_name': 'app:delete',
})
```

## 迁移指南

### 从子模板迁移到统一实现

**之前（子模板中）：**
```django
{% block list_page_table_actions_cell %}
<td>
    <div class="list-page-table-actions">
        <a href="{% url 'business_pages:customer_detail' item.id %}" 
           class="action-view" title="查看">
            <i class="bi bi-eye"></i>
        </a>
        {% if can_create %}
        <span class="action-separator">|</span>
        <a href="{% url 'business_pages:customer_edit' item.id %}" 
           class="action-edit" title="编辑">
            <i class="bi bi-pencil"></i>
        </a>
        {% endif %}
        {% if can_delete %}
        <span class="action-separator">|</span>
        <a href="{% url 'business_pages:customer_delete' item.id %}" 
           class="action-delete" title="删除"
           onclick="return confirm('确定要删除此客户吗？此操作不可恢复。');">
            <i class="bi bi-trash"></i>
        </a>
        {% endif %}
    </div>
</td>
{% endblock %}
```

**之后（视图函数中）：**
```python
# views.py
return render(request, 'customer_management/customer_list.html', {
    'page_obj': page_obj,
    'can_create': request.user.has_perm('customer_management.add_customer'),
    'can_delete': request.user.has_perm('customer_management.delete_customer'),
    'detail_url_name': 'business_pages:customer_detail',
    'edit_url_name': 'business_pages:customer_edit',
    'delete_url_name': 'business_pages:customer_delete',
})
```

```django
{# customer_list.html - 只需覆盖确认消息（可选） #}
{% block delete_confirm_message %}确定要删除此客户吗？此操作不可恢复。{% endblock %}
```

**或者完全删除 `list_page_table_actions_cell` 块，使用默认实现。**

## 注意事项

1. **URL 名称必须存在**：确保传递的 URL 名称在 `urls.py` 中已定义
2. **权限检查**：建议在视图函数中进行权限检查，而不是仅依赖模板变量
3. **特殊需求**：对于有特殊逻辑的页面（如条件判断），仍可在子模板中覆盖
4. **向后兼容**：现有的子模板覆盖不会受到影响，可以逐步迁移

## 优势

- ✅ **减少代码重复**：30+ 个子模板无需重复编写操作列代码
- ✅ **统一行为**：所有列表页的操作列行为一致
- ✅ **易于维护**：修改一处即可影响所有页面
- ✅ **灵活配置**：支持权限控制、自定义消息等
- ✅ **向后兼容**：不影响现有子模板

