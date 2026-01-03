# 静态表格共享模板使用指南

## 📋 概述

`_static_table.html` 是一个基于 `list_page_base.html` 表格样式的静态表格共享模板，提供了统一的表格展示组件，支持表格工具栏、批量操作栏和列设置功能。

## ✨ 功能特点

1. **统一的表格样式** - 与 `list_page_base.html` 保持一致的视觉效果
2. **表格工具栏** - 支持打印、列设置等功能
3. **批量操作栏** - 支持批量导出、批量删除等操作（引入 `batch_actions_bar.html`）
4. **列设置功能** - 支持显示/隐藏列、设置列宽度（需要引入列设置模态框）
5. **复选框支持** - 可选的行选择功能
6. **操作列** - 默认提供查看、编辑、删除操作
7. **响应式设计** - 适配不同屏幕尺寸
8. **可扩展的block结构** - 通过覆盖blocks自定义表格内容

## 🚀 基本使用方法

### 1. 最简单的使用方式

```django
{% include "shared/_static_table.html" with table_id="myTable" table_data=items %}
```

### 2. 自定义列头和行内容

```django
{% include "shared/_static_table.html" with table_id="myTable" table_data=items %}

{% block static_table_headers %}
    <th>ID</th>
    <th>名称</th>
    <th>状态</th>
    <th>创建时间</th>
{% endblock %}

{% block static_table_row_content %}
    <td>{{ item.id }}</td>
    <td>{{ item.name }}</td>
    <td>
        {% if item.status == 'active' %}
            <span class="badge bg-success">活跃</span>
        {% else %}
            <span class="badge bg-secondary">禁用</span>
        {% endif %}
    </td>
    <td>{{ item.created_at|date:"Y-m-d H:i" }}</td>
{% endblock %}
```

### 3. 启用复选框和批量操作

```django
{% include "shared/_static_table.html" with table_id="myTable" table_data=items show_checkbox=True show_batch_actions=True %}
```

### 4. 自定义操作列

```django
{% block static_table_actions_cell %}
<td>
    <div class="static-table-actions">
        <a href="{% url 'detail' item.id %}" class="action-view" title="查看">
            <i class="bi bi-eye"></i>
        </a>
        <span class="action-separator">|</span>
        <a href="{% url 'edit' item.id %}" class="action-edit" title="编辑">
            <i class="bi bi-pencil"></i>
        </a>
        {% if item.can_delete %}
        <span class="action-separator">|</span>
        <a href="{% url 'delete' item.id %}" class="action-delete" title="删除" onclick="return confirm('确定要删除吗？')">
            <i class="bi bi-trash"></i>
        </a>
        {% endif %}
    </div>
</td>
{% endblock %}
```

### 5. 启用扩展功能

```django
{% include "shared/_static_table.html" with table_id="myTable" table_data=items show_search=True show_stats=True show_export=True enable_sort=True enable_row_click=True %}

{% block static_table_headers %}
    <th class="sortable">ID</th>
    <th class="sortable">名称</th>
    <th>状态</th>
{% endblock %}
```

### 6. 完整的页面示例

```django
{% extends "shared/base.html" %}
{% load static %}

{% block title %}我的列表{% endblock %}

{% block content %}
<div class="container py-4">
    <h1>我的列表</h1>
    
    {% include "shared/_static_table.html" with table_id="myTable" table_data=items show_checkbox=True %}
    
    {% block static_table_headers %}
        <th>ID</th>
        <th>名称</th>
        <th>状态</th>
        <th>操作</th>
    {% endblock %}
    
    {% block static_table_row_content %}
        <td>{{ item.id }}</td>
        <td>{{ item.name }}</td>
        <td>{{ item.get_status_display }}</td>
    {% endblock %}
    
    {% block static_table_actions_cell %}
        <td>
            <a href="{% url 'detail' item.id %}" class="action-view">
                <i class="bi bi-eye"></i>
            </a>
            <span class="action-separator">|</span>
            <a href="{% url 'edit' item.id %}" class="action-edit">
                <i class="bi bi-pencil"></i>
            </a>
        </td>
    {% endblock %}
</div>
{% endblock %}

{% block modals %}
{{ block.super }}
{# 列设置模态框已在 base.html 中包含 #}
{% endblock %}
```

## 📝 可用的参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `table_id` | string | `'staticTable'` | 表格的ID（必需） |
| `table_data` | list | - | 表格数据列表（必需） |
| `table_class` | string | `''` | 表格额外的CSS类 |
| `show_checkbox` | boolean | `False` | 是否显示复选框列 |
| `show_actions` | boolean | `True` | 是否显示操作列 |
| `show_column_settings` | boolean | `True` | 是否显示列设置按钮 |
| `show_print` | boolean | `True` | 是否显示打印按钮 |
| `show_batch_actions` | boolean | `True` | 是否显示批量操作栏 |
| `show_search` | boolean | `False` | 是否显示搜索框 |
| `show_stats` | boolean | `False` | 是否显示统计信息 |
| `show_export` | boolean | `False` | 是否显示导出按钮 |
| `enable_sort` | boolean | `False` | 是否启用列排序（需要在表头添加 `class="sortable"`） |
| `enable_row_click` | boolean | `False` | 是否启用行点击高亮 |
| `empty_message` | string | `'暂无数据'` | 空数据提示消息 |
| `empty_colspan` | int | `2` | 空数据行的colspan |

## ⚡ 扩展功能说明

### 1. 搜索功能 (`show_search=True`)

启用后会在表格上方显示搜索框，支持实时过滤表格行。

**特性：**
- 实时搜索过滤
- 支持 `Ctrl+F` 快捷键聚焦搜索框
- 自动显示/隐藏清除按钮
- 配合统计信息显示过滤后的数量

**使用示例：**
```django
{% include "shared/_static_table.html" with table_id="myTable" table_data=items show_search=True %}
```

### 2. 统计信息 (`show_stats=True`)

在表格上方显示总记录数和当前显示的记录数。

**特性：**
- 实时更新（配合搜索功能）
- 显示格式：`共 X 条记录，显示 Y 条`

**使用示例：**
```django
{% include "shared/_static_table.html" with table_id="myTable" table_data=items show_stats=True %}
```

### 3. 导出功能 (`show_export=True`)

在表格工具栏显示导出按钮，可将当前显示的表格数据导出为CSV格式（Excel兼容）。

**特性：**
- 导出为CSV格式
- 只导出当前可见的行（配合搜索功能）
- 自动跳过复选框列和操作列
- 自动处理包含逗号的单元格值

**使用示例：**
```django
{% include "shared/_static_table.html" with table_id="myTable" table_data=items show_export=True %}
```

### 4. 列排序功能 (`enable_sort=True`)

启用后，点击带有 `class="sortable"` 的表头可以进行排序。

**特性：**
- 点击表头排序
- 支持数字和文本排序
- 显示排序指示器（↑↓）
- 可在表头添加 `class="sortable"` 来启用特定列的排序

**使用示例：**
```django
{% include "shared/_static_table.html" with table_id="myTable" table_data=items enable_sort=True %}

{% block static_table_headers %}
    <th class="sortable">ID</th>
    <th class="sortable">名称</th>
    <th>状态</th>  {# 此列不支持排序 #}
{% endblock %}
```

### 5. 行点击功能 (`enable_row_click=True`)

启用后，点击表格行可以高亮选中，并触发自定义事件。

**特性：**
- 点击行高亮选中（蓝色背景）
- 触发 `tableRowClick` 自定义事件
- 可通过JavaScript事件监听器处理行点击
- 点击链接、按钮或复选框时不会触发行点击

**使用示例：**
```django
{% include "shared/_static_table.html" with table_id="myTable" table_data=items enable_row_click=True %}

<script>
document.getElementById('myTable').addEventListener('tableRowClick', function(e) {
    console.log('点击了行:', e.detail.id);
    // 可以在这里处理行点击事件，比如跳转到详情页
    // window.location.href = '/detail/' + e.detail.id + '/';
});
</script>
```

### 6. 空状态优化

改进了空数据时的显示效果，使用更友好的界面。

**特性：**
- 显示图标（📭）和文字提示
- 更好的视觉层次

## 🎨 可覆盖的Blocks

### 表格结构相关

- `static_table_search` - 搜索框区域
- `static_table_stats` - 统计信息区域
- `static_table_toolbar` - 整个表格工具栏区域
- `static_table_toolbar_left` - 表格工具栏左侧内容
- `static_table_toolbar_right` - 表格工具栏右侧内容

### 表格内容相关

- `static_table_checkbox_header` - 复选框列头
- `static_table_headers` - 表格列头
- `static_table_actions_header` - 操作列头
- `static_table_checkbox_cell` - 复选框单元格
- `static_table_row_content` - 表格行内容
- `static_table_actions_cell` - 操作列单元格
- `static_table_empty_message` - 空数据提示消息
- `static_table_empty_colspan` - 空数据行的colspan

## 🔧 依赖项

### 必需的模板

1. **列设置模态框** - `shared/modals/column_settings_modal.html`
   - 通常在 `base.html` 中已包含
   - 如果页面没有继承 `base.html`，需要手动包含：
   ```django
   {% include "shared/modals/column_settings_modal.html" %}
   ```

2. **批量操作栏** - `shared/batch_actions_bar.html`
   - 已在 `_static_table.html` 中自动引入

### JavaScript依赖

1. **列设置功能** - 需要从 `list_page_base.html` 中复制相关JavaScript代码
   - `initColumnSettings()` 函数
   - 列设置的完整实现

2. **批量操作功能** - 需要从 `list_page_base.html` 中复制相关JavaScript代码
   - `initBatchActionsBar()` 函数
   - 批量操作的完整实现

### CSS依赖

- 表格样式已包含在 `_static_table.html` 中
- 依赖CSS变量（如 `--vh-surface`, `--vh-border` 等），通常在 `common.css` 中定义

## 📋 使用场景

### 适用场景

1. ✅ 列表页面（不使用 `list_page_base.html` 时）
2. ✅ 详情页中的关联数据表格
3. ✅ 仪表板中的数据展示表格
4. ✅ 表单中的只读数据表格
5. ✅ 任何需要统一表格样式的静态数据展示

### 不适用场景

1. ❌ 需要AJAX动态加载数据的表格（应使用 `_dynamic_table.html`）
2. ❌ 表单中的动态添加/删除行的表格（应使用 `_dynamic_form_table.html`）
3. ❌ 已经有 `list_page_base.html` 的列表页面（应直接使用其表格结构）

## 🔍 与 list_page_base.html 的区别

| 特性 | _static_table.html | list_page_base.html |
|------|-------------------|---------------------|
| 表格结构 | 独立的include模板 | 直接编码在模板中 |
| 动态功能 | 不支持 | 支持（筛选、分页等） |
| 使用方式 | include | extends |
| 适用范围 | 任何页面 | 列表页面 |
| 数据来源 | 传入的table_data | page_obj.object_list |

## 💡 最佳实践

1. **表格ID唯一性** - 确保每个页面中的表格ID是唯一的
2. **Block覆盖顺序** - 确保block覆盖在include之后
3. **模态框包含** - 如果使用列设置功能，确保包含列设置模态框
4. **JavaScript初始化** - 如果使用批量操作或列设置，需要相应的JavaScript支持
5. **响应式设计** - 在移动端会自动启用横向滚动

## 🔗 相关文档

- `list_page_base.html` - 列表页基础模板
- `_dynamic_table.html` - 动态表格模板
- `_dynamic_form_table.html` - 动态表单表格模板
- `batch_actions_bar.html` - 批量操作栏模板
- `modals/column_settings_modal.html` - 列设置模态框模板

---

**最后更新：** 2024年  
**维护者：** 开发团队

