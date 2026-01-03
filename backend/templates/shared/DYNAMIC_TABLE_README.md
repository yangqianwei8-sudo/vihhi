# 动态表格模板使用说明

## 概述

动态表格模板 (`_dynamic_table.html`) 是一个通用的、可配置的表格组件，支持动态列配置、数据加载、排序、筛选、分页等功能。

## 功能特性

- ✅ 动态列配置
- ✅ 静态数据渲染
- ✅ AJAX动态数据加载
- ✅ 列排序（点击表头）
- ✅ 搜索功能
- ✅ 筛选功能（可扩展）
- ✅ 行选择（复选框）
- ✅ 批量操作
- ✅ 自定义操作列
- ✅ 自定义列渲染
- ✅ 响应式设计

## 使用方法

### 1. 在视图中准备配置和数据

```python
from django.shortcuts import render

def my_list_view(request):
    # 表格配置
    table_config = {
        'id': 'myTable',  # 表格唯一ID
        'columns': [
            {
                'key': 'id',
                'label': 'ID',
                'sortable': True,
                'width': '80px'
            },
            {
                'key': 'name',
                'label': '名称',
                'sortable': True,
                'width': '200px'
            },
            {
                'key': 'status',
                'label': '状态',
                'sortable': False,
                'render': 'render_status'  # 自定义渲染函数
            },
            {
                'key': 'created_time',
                'label': '创建时间',
                'sortable': True,
                'render': 'render_date'
            }
        ],
        'actions': [
            {
                'label': '查看',
                'class': 'action-view',
                'url': '/detail/{id}/',
                'icon': 'bi-eye'
            },
            {
                'label': '编辑',
                'class': 'action-edit',
                'url': '/edit/{id}/',
                'icon': 'bi-pencil'
            },
            {
                'label': '删除',
                'class': 'action-delete',
                'url': '/delete/{id}/',
                'icon': 'bi-trash'
            }
        ],
        'selectable': True,      # 是否支持行选择
        'searchable': True,      # 是否支持搜索
        'filterable': False,     # 是否支持筛选
        'pagination': True,      # 是否启用分页
        'page_size': 10          # 每页显示数量
    }
    
    # 静态数据（如果使用静态数据）
    table_data = [
        {
            'id': 1,
            'name': '项目A',
            'status': 'active',
            'created_time': '2024-01-01'
        },
        {
            'id': 2,
            'name': '项目B',
            'status': 'inactive',
            'created_time': '2024-01-02'
        }
    ]
    
    # 如果使用AJAX加载，则不需要table_data，只需设置ajax_url
    # table_config['ajax_url'] = '/api/my-data/'
    
    return render(request, 'my_template.html', {
        'table_config': table_config,
        'table_data': table_data  # 可选
    })
```

### 2. 在模板中引入

```django
{% extends 'base.html' %}
{% load static %}

{% block content %}
<div class="container py-4">
    <h2>我的列表</h2>
    
    {% include 'shared/_dynamic_table.html' with table_config=table_config table_data=table_data %}
</div>

<!-- 自定义渲染函数 -->
<script>
window.dynamicTableRenderers = {
    render_status: function(row, key) {
        const status = row[key];
        const statusMap = {
            'active': '<span class="badge bg-success">启用</span>',
            'inactive': '<span class="badge bg-secondary">停用</span>',
            'pending': '<span class="badge bg-warning">待审核</span>'
        };
        return statusMap[status] || status;
    },
    
    render_date: function(row, key) {
        const date = row[key];
        if (!date) return '—';
        return new Date(date).toLocaleDateString('zh-CN');
    }
};
</script>
{% endblock %}
```

## 配置选项

### table_config 字典

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `id` | string | 是 | 表格唯一ID |
| `columns` | list | 是 | 列配置列表 |
| `actions` | list | 否 | 操作按钮配置列表 |
| `selectable` | bool | 否 | 是否支持行选择，默认False |
| `searchable` | bool | 否 | 是否支持搜索，默认False |
| `filterable` | bool | 否 | 是否支持筛选，默认False |
| `pagination` | bool | 否 | 是否启用分页，默认False |
| `page_size` | int | 否 | 每页显示数量，默认10 |
| `ajax_url` | string | 否 | AJAX数据源URL（如果使用AJAX加载） |

### column 配置

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `key` | string | 是 | 数据字段键名 |
| `label` | string | 是 | 列标题 |
| `sortable` | bool | 否 | 是否可排序，默认False |
| `width` | string | 否 | 列宽度，如'100px'或'15%' |
| `render` | string | 否 | 自定义渲染函数名 |

### action 配置

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `label` | string | 是 | 按钮文本 |
| `class` | string | 是 | CSS类名 |
| `url` | string | 是 | 链接URL，可用{id}占位符 |
| `icon` | string | 否 | Bootstrap图标类名，如'bi-eye' |

## AJAX数据加载

如果使用AJAX加载数据，需要：

1. 在配置中设置 `ajax_url`
2. 后端API返回JSON格式数据：

```python
from django.http import JsonResponse
from django.core.paginator import Paginator

def api_my_data(request):
    queryset = MyModel.objects.all()
    
    # 分页
    paginator = Paginator(queryset, 10)
    page = request.GET.get('page', 1)
    page_obj = paginator.get_page(page)
    
    # 搜索
    search = request.GET.get('search', '')
    if search:
        queryset = queryset.filter(name__icontains=search)
    
    # 排序
    sort = request.GET.get('sort')
    order = request.GET.get('order', 'asc')
    if sort:
        if order == 'desc':
            sort = '-' + sort
        queryset = queryset.order_by(sort)
    
    # 构建响应数据
    data = {
        'results': [
            {
                'id': obj.id,
                'name': obj.name,
                'status': obj.status,
                'created_time': obj.created_time.isoformat()
            }
            for obj in page_obj
        ],
        'count': paginator.count,
        'page': page_obj.number,
        'pages': paginator.num_pages
    }
    
    return JsonResponse(data)
```

## 事件处理

可以通过 `window.dynamicTableEvents` 对象监听表格事件：

```javascript
window.dynamicTableEvents = {
    // 排序事件
    onSort: function(tableId, key, direction) {
        console.log('排序:', tableId, key, direction);
        // 重新加载数据
        if (window.dynamicTables && window.dynamicTables[tableId]) {
            window.dynamicTables[tableId].loadData({ 
                sort: key, 
                order: direction 
            });
        }
    },
    
    // 搜索事件
    onSearch: function(tableId, keyword) {
        console.log('搜索:', tableId, keyword);
        // 重新加载数据
        if (window.dynamicTables && window.dynamicTables[tableId]) {
            window.dynamicTables[tableId].loadData({ search: keyword });
        }
    },
    
    // 选择变化事件
    onSelectionChange: function(tableId, selectedIds) {
        console.log('选择变化:', tableId, selectedIds);
    }
};
```

## API方法

表格实例通过 `window.dynamicTables[tableId]` 访问，提供以下方法：

```javascript
// 获取表格实例
const table = window.dynamicTables['myTable'];

// 加载数据
table.loadData({ page: 1, search: '关键词' });

// 获取选中的行ID
const selectedIds = table.getSelectedRows();

// 清除选择
table.clearSelection();
```

## 自定义渲染函数

在 `window.dynamicTableRenderers` 对象中定义自定义渲染函数：

```javascript
window.dynamicTableRenderers = {
    render_status: function(row, key) {
        // row: 整行数据对象
        // key: 当前字段键名
        const status = row[key];
        return `<span class="badge bg-${status === 'active' ? 'success' : 'secondary'}">${status}</span>`;
    },
    
    render_custom: function(row, key) {
        // 自定义渲染逻辑
        return '自定义内容';
    }
};
```

## 批量操作

如果启用了行选择（`selectable: True`），可以添加批量操作按钮：

```django
{% block dynamic_table_batch_actions %}
<button type="button" class="btn btn-sm btn-primary" onclick="batchDelete()">
    批量删除
</button>
<button type="button" class="btn btn-sm btn-success" onclick="batchExport()">
    批量导出
</button>
{% endblock %}
```

```javascript
function batchDelete() {
    const table = window.dynamicTables['myTable'];
    const selectedIds = table.getSelectedRows();
    
    if (selectedIds.length === 0) {
        alert('请先选择要删除的数据');
        return;
    }
    
    if (confirm(`确定要删除选中的 ${selectedIds.length} 项吗？`)) {
        // 执行删除操作
        fetch('/api/batch-delete/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            },
            body: JSON.stringify({ ids: selectedIds })
        })
        .then(response => response.json())
        .then(data => {
            alert('删除成功');
            // 重新加载表格
            table.loadData();
        });
    }
}
```

## 样式定制

表格使用Bootstrap 5样式，可以通过CSS覆盖默认样式：

```css
/* 自定义表格样式 */
#myTable {
    /* 自定义样式 */
}

/* 自定义操作按钮样式 */
#myTable .action-view {
    color: #0d6efd;
}

#myTable .action-edit {
    color: #198754;
}

#myTable .action-delete {
    color: #dc3545;
}
```

## 注意事项

1. **表格ID必须唯一**：每个页面上的表格ID不能重复
2. **数据格式**：如果使用AJAX加载，后端必须返回符合格式的JSON数据
3. **CSRF Token**：如果使用AJAX POST请求，需要包含CSRF token
4. **模板标签**：确保已加载 `customer_tags` 模板标签库（用于 `get_item` 过滤器）

## 完整示例

参考 `dynamic_table_example.html` 文件查看完整的使用示例。

