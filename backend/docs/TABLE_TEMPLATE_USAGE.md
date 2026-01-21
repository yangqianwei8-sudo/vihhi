# 列表表格共享模板使用指南

## 概述

`list_table.html` 是一个可复用的列表页面表格模板，基于现有的 `tables.css` 样式设计，提供了统一的表格展示功能。

## 文件位置

- 模板文件：`templates/shared/list_table.html`
- 样式文件：`static/css/components/tables.css`
- 操作列模板：`templates/shared/_partials/table_actions.html`

## 基本使用

### 1. 在模板中引入

```django
{% include 'shared/list_table.html' with 
    columns=columns 
    data=page_obj 
    empty_message='暂无数据' 
%}
```

### 2. 在视图中定义列

```python
def your_list_view(request):
    # ... 获取数据 ...
    
    columns = [
        {
            'name': '客户名称',
            'field': 'name',
            'width': '200',
            'sortable': True,
            'format': 'link',
            'url_name': 'customer_detail',
            'class': 'column-name'
        },
        {
            'name': '统一信用代码',
            'field': 'unified_credit_code',
            'width': '150',
            'format': 'code',
            'class': 'column-code',
            'small': True,
            'text_muted': True
        },
        {
            'name': '客户等级',
            'field': 'client_level',
            'width': '100',
            'format': 'badge',
            'class': 'column-level'
        },
        {
            'name': '创建时间',
            'field': 'created_at',
            'width': '150',
            'sortable': True,
            'format': 'datetime',
            'class': 'column-created'
        },
    ]
    
    context = {
        'columns': columns,
        'page_obj': page_obj,
        # ... 其他上下文 ...
    }
    return render(request, 'your_template.html', context)
```

## 参数说明

### 必需参数

- `columns`: 列定义列表（见下方列定义说明）
- `data`: 数据列表（分页对象或普通列表）

### 可选参数

- `table_id`: 表格的唯一ID（默认：'dataTable'）
- `show_checkbox`: 是否显示复选框列（默认：False）
- `checkbox_name`: 复选框的name属性（默认：'item_ids'）
- `show_actions`: 是否显示操作列（默认：False）
- `action_template`: 操作列的自定义模板路径（可选）
- `empty_message`: 空数据提示信息（默认：'暂无数据'）
- `empty_colspan`: 空数据行的colspan（自动计算）
- `show_pagination`: 是否显示分页（默认：False）
- `pagination_params`: 分页URL参数（字典格式）
- `table_class`: 额外的表格CSS类
- `column_settings_btn`: 是否显示列设置按钮（默认：False）

## 列定义说明

每个列定义是一个字典，支持以下属性：

### 基础属性

- `name`: 列标题（必需）
- `field`: 数据字段名（可选，用于自动获取数据）
- `width`: 列宽度（可选，如 '200', '150'）
- `class`: CSS类名（可选，如 'column-name'）
- `style`: 内联样式（可选，如 'display: none;'）
- `sortable`: 是否可排序（默认：False）

### 格式化属性

- `format`: 数据格式化方式，支持：
  - `'date'`: 日期格式（Y-m-d）
  - `'datetime'`: 日期时间格式（Y-m-d H:i）
  - `'badge'`: 徽章样式（蓝色）
  - `'badge-info'`: 信息徽章（青色）
  - `'badge-success'`: 成功徽章（绿色）
  - `'badge-secondary'`: 次要徽章（灰色）
  - `'link'`: 链接格式（需要配合 `url_name`）
  - `'code'`: 代码样式
  - `'currency'`: 货币格式（¥前缀）
  - `'truncate'`: 截断文本（10个词）
  - `'boolean'`: 布尔值（是/否徽章）

### 链接格式

当 `format='link'` 时，需要提供：
- `url_name`: URL名称（用于 `{% url %}` 标签）

### 自定义模板

- `template`: 自定义模板路径（可选，用于完全自定义列内容）

### 样式属性

- `small`: 是否使用小字体（添加 `small` 类）
- `text_muted`: 是否使用灰色文本（添加 `text-muted` 类）

## 使用示例

### 示例1：基础表格

```django
{% include 'shared/list_table.html' with 
    columns=columns 
    data=page_obj 
    empty_message='暂无数据' 
%}
```

### 示例2：带复选框和操作列

```django
{% include 'shared/list_table.html' with 
    table_id='customerTable'
    columns=columns 
    data=page_obj 
    show_checkbox=True
    checkbox_name='client_ids'
    show_actions=True
    action_template='shared/_partials/table_actions.html'
    empty_message='暂无客户数据'
    show_pagination=True
    pagination_params=request.GET.dict
%}
```

### 示例3：带列设置按钮

```django
{% include 'shared/list_table.html' with 
    columns=columns 
    data=page_obj 
    show_actions=True
    column_settings_btn=True
%}
```

### 示例4：自定义操作列

创建 `templates/your_app/table_actions.html`：

```django
<div class="btn-group btn-group-sm">
    <a href="{% url 'customer_detail' item.id %}" class="btn btn-sm">查看</a>
    {% if can_edit %}
    <a href="{% url 'customer_edit' item.id %}" class="btn btn-sm">编辑</a>
    {% endif %}
    {% if can_delete %}
    <button type="button" class="btn btn-sm" onclick="deleteItem({{ item.id }})">删除</button>
    {% endif %}
</div>
```

然后在模板中：

```django
{% include 'shared/list_table.html' with 
    columns=columns 
    data=page_obj 
    show_actions=True
    action_template='your_app/table_actions.html'
%}
```

## 样式说明

模板使用了以下CSS类（定义在 `tables.css` 中）：

- `.list-page-table-container`: 表格容器
- `.list-page-table-wrapper`: 表格包装器
- `.list-page-table`: 表格主体
- `.column-checkbox`: 复选框列
- `.column-actions`: 操作列
- `.sortable`: 可排序列
- `.sort-icon`: 排序图标

## 注意事项

1. 确保在页面中引入了 `tables.css` 样式文件
2. 如果使用复选框，需要添加全选/取消全选的JavaScript代码
3. 如果使用分页，确保 `data` 是分页对象（有 `has_other_pages`、`paginator` 等属性）
4. 自定义模板中的 `item` 变量代表当前数据项
5. 使用 `getattr` 过滤器获取对象属性（如果Django版本不支持，需要在视图中预处理数据）

## JavaScript 示例

### 全选/取消全选

```javascript
document.getElementById('selectAll')?.addEventListener('change', function() {
    const checkboxes = document.querySelectorAll('.row-checkbox');
    checkboxes.forEach(cb => {
        cb.checked = this.checked;
        const row = cb.closest('tr');
        if (row) {
            if (this.checked) {
                row.classList.add('selected');
            } else {
                row.classList.remove('selected');
            }
        }
    });
});
```

### 获取选中的项目

```javascript
function getSelectedItems() {
    const checkboxes = document.querySelectorAll('.row-checkbox:checked');
    return Array.from(checkboxes).map(cb => cb.value);
}
```

## 字段定义功能

模板支持字段定义功能，允许用户自定义显示哪些列以及列的顺序。

### 使用方法

1. **在视图中定义字段列表**：

```python
def your_list_view(request):
    # 定义所有可用字段
    all_fields = [
        {'column': 'column-checkbox', 'label': '复选框', 'required': True},
        {'column': 'column-name', 'label': '客户名称', 'required': True},
        {'column': 'column-code', 'label': '统一信用代码', 'required': False},
        {'column': 'column-level', 'label': '客户等级', 'required': False},
        {'column': 'column-created', 'label': '创建时间', 'required': False},
        {'column': 'column-actions', 'label': '操作', 'required': True},
    ]
    
    # 转换为JSON字符串
    import json
    all_fields_json = json.dumps(all_fields)
    
    context = {
        'all_fields_json': all_fields_json,
        'columns': columns,
        'page_obj': page_obj,
        # ...
    }
    return render(request, 'your_template.html', context)
```

2. **在模板中引入字段定义功能**：

```django
{% include 'shared/list_table.html' with 
    columns=columns 
    data=page_obj 
    show_actions=True
    column_settings_btn=True
%}

{% include 'shared/_partials/column_settings_modal.html' with 
    modal_id='fieldsSettingsModal'
    storage_key='customer_list_columns'
%}

{% include 'shared/_partials/column_settings_js.html' with 
    all_fields_json=all_fields_json
    storage_key='customer_list_columns'
    modal_id='fieldsSettingsModal'
%}
```

### 字段定义参数

- `all_fields_json`: 所有可用字段的JSON字符串（必需）
- `storage_key`: localStorage存储键名（默认：'table_columns'）
- `required_columns`: 必选列列表（默认：['column-checkbox', 'column-actions']）
- `modal_id`: 模态框ID（默认：'fieldsSettingsModal'）

### 字段对象格式

```javascript
{
    'column': 'column-name',  // CSS类名，必须与列定义中的class一致
    'label': '列名',          // 显示名称
    'required': false         // 是否为必选列
}
```

### 功能特性

- ✅ 显示/隐藏列
- ✅ 拖拽排序
- ✅ 保存到localStorage
- ✅ 重置为默认设置
- ✅ 必选列保护（不能隐藏）

### 注意事项

1. 字段定义中的 `column` 值必须与列定义中的 `class` 值一致
2. 必选列（如复选框、操作列）不能隐藏
3. 设置会保存到浏览器的localStorage中
4. 不同页面应使用不同的 `storage_key` 以避免冲突
