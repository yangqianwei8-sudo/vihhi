# list_page_base.html 筛选面板集成说明

## 概述

`list_page_base.html` 现在支持使用新的筛选面板模板（`_filter_panel.html`）。只需在视图中提供 `filter_config` 配置，模板会自动使用新的筛选面板。

## 使用方法

### 1. 在视图中配置筛选

```python
# views.py
from django.urls import reverse

def my_list_view(request):
    # 配置筛选面板
    filter_config = {
        'id': 'myListFilter',
        'method': 'form',  # 表单提交模式
        'form_action': request.path,
        'auto_submit': False,  # 列表页建议关闭自动提交
        'collapsible': True,
        'default_collapsed': False,
        'show_filter_tags': True,  # 显示筛选标签
        'enable_presets': True,  # 启用预设功能
        'enable_history': True,  # 启用历史功能
        'filters': [
            {
                'key': 'status',
                'label': '状态',
                'type': 'select',
                'options': [
                    {'value': 'all', 'label': '全部'},
                    {'value': 'active', 'label': '启用'},
                    {'value': 'inactive', 'label': '禁用'}
                ],
                'default': request.GET.get('status', 'all')
            },
            {
                'key': 'keyword',
                'label': '关键词',
                'type': 'text',
                'placeholder': '请输入关键词...',
                'default': request.GET.get('keyword', '')
            },
            {
                'key': 'date_range',
                'label': '日期范围',
                'type': 'date_range',
                'quick_select': [
                    {'value': 'today', 'label': '今天'},
                    {'value': 'this_week', 'label': '本周'},
                    {'value': 'this_month', 'label': '本月'}
                ],
                'default': {
                    'start': request.GET.get('date_range_start', ''),
                    'end': request.GET.get('date_range_end', '')
                }
            }
        ]
    }
    
    # 获取筛选参数并处理数据
    status = request.GET.get('status', 'all')
    keyword = request.GET.get('keyword', '')
    date_range_start = request.GET.get('date_range_start', '')
    date_range_end = request.GET.get('date_range_end', '')
    
    # 构建查询
    queryset = MyModel.objects.all()
    
    if status != 'all':
        queryset = queryset.filter(status=status)
    
    if keyword:
        queryset = queryset.filter(
            Q(name__icontains=keyword) |
            Q(description__icontains=keyword)
        )
    
    if date_range_start:
        queryset = queryset.filter(created_at__gte=date_range_start)
    
    if date_range_end:
        queryset = queryset.filter(created_at__lte=date_range_end)
    
    # 分页
    per_page = 10
    paginator = Paginator(queryset, per_page)
    page_obj = paginator.get_page(request.GET.get('page', 1))
    
    context = {
        'page_title': '我的列表',
        'filter_config': filter_config,
        'page_obj': page_obj,
        # ... 其他上下文
    }
    return render(request, 'my_app/list.html', context)
```

### 2. 在模板中使用

```django
{# list.html #}
{% extends "shared/list_page_base.html" %}

{# 筛选配置已在视图中提供，模板会自动使用新的筛选面板 #}
{# 如果需要自定义筛选区域，可以覆盖 list_page_filters 块 #}

{% block list_page_table_headers %}
<th>ID</th>
<th>名称</th>
<th>状态</th>
<th>创建时间</th>
{% endblock %}

{% block list_page_table_row_content %}
<td>{{ item.id }}</td>
<td>{{ item.name }}</td>
<td>{{ item.get_status_display }}</td>
<td>{{ item.created_at|date:"Y-m-d H:i" }}</td>
{% endblock %}
```

### 3. 自定义筛选区域（可选）

如果需要完全自定义筛选区域，可以覆盖 `list_page_filters` 块：

```django
{% block list_page_filters %}
    {# 使用自定义的筛选区域 #}
    <div class="custom-filters">
        <!-- 自定义筛选内容 -->
    </div>
{% endblock %}
```

## 配置选项说明

### 基本配置

- `id`: 筛选面板ID（必须，在页面中唯一）
- `method`: 提交方式，`'form'`（表单提交）或 `'ajax'`（AJAX提交），默认 `'form'`
- `form_action`: 表单提交URL（method='form'时使用），默认当前页面URL
- `auto_submit`: 是否自动提交，默认 `False`（列表页建议关闭）
- `collapsible`: 是否可折叠，默认 `True`
- `default_collapsed`: 默认是否折叠，默认 `False`

### 高级功能

- `show_filter_tags`: 显示筛选条件标签，默认 `False`
- `enable_presets`: 启用筛选预设功能，默认 `False`
- `enable_history`: 启用筛选历史功能，默认 `False`
- `max_history`: 最大历史记录数，默认 `10`
- `enable_field_settings`: 启用筛选字段设置功能，默认 `False`
- `max_enabled_fields`: 最多可启用的字段数，默认 `10`
- `default_enabled_fields`: 默认启用的字段key列表
- `required_fields`: 必填字段列表（不可隐藏）

### 筛选字段类型

支持以下筛选类型：
- `select`: 下拉选择框
- `multiselect`: 多选下拉框
- `text`: 文本输入框
- `date`: 日期选择器
- `date_range`: 日期范围选择器
- `time`: 时间选择器
- `datetime`: 日期时间选择器
- `number`: 数字输入框
- `number_range`: 数字范围输入框
- `checkbox`: 复选框组
- `radio`: 单选按钮组

详细配置说明请参考 `_filter_panel_usage.md` 文档。

## 与旧筛选方式的对比

### 旧方式（已弃用）

```django
{% block list_page_filter_fields %}
<div class="filter-row" data-filter-key="status">
    <label class="filter-label">状态:</label>
    <div class="filter-control">
        <select name="status" class="form-control form-control-sm">
            <option value="all">全部</option>
            <option value="active">启用</option>
            <option value="inactive">禁用</option>
        </select>
    </div>
</div>
{% endblock %}
```

### 新方式（推荐）

```python
# 在视图中配置
filter_config = {
    'id': 'myFilter',
    'filters': [
        {
            'key': 'status',
            'label': '状态',
            'type': 'select',
            'options': [
                {'value': 'all', 'label': '全部'},
                {'value': 'active', 'label': '启用'},
                {'value': 'inactive', 'label': '禁用'}
            ],
            'default': request.GET.get('status', 'all')
        }
    ]
}
```

## 优势

1. **配置化**：所有筛选配置在视图中完成，模板更简洁
2. **功能丰富**：支持日期快捷选择、筛选预设、筛选历史等高级功能
3. **易于维护**：统一的配置方式，便于维护和扩展
4. **用户体验好**：支持筛选标签、字段清除、URL同步等功能
5. **向后兼容**：不提供 `filter_config` 时不会影响现有功能

## 注意事项

1. 列表页建议设置 `auto_submit: False`，让用户手动点击筛选按钮提交
2. 确保筛选字段的 `key` 与后端参数名称一致
3. 日期范围字段会生成 `{key}_start` 和 `{key}_end` 两个参数
4. 多选字段会生成数组参数，后端需要使用 `request.GET.getlist()` 获取

