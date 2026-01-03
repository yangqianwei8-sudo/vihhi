# 筛选面板使用指南 (Filter Panel Usage Guide)

## 概述

`_filter_panel.html` 是一个通用的筛选功能共享模板，提供了灵活的筛选条件配置和多种筛选类型支持。

## 功能特性

- ✅ 支持多种筛选类型（下拉选择、文本输入、日期范围、数字范围等）
- ✅ 支持筛选条件的组合和重置
- ✅ 支持自动提交和手动提交两种模式
- ✅ 支持AJAX筛选和表单提交筛选
- ✅ 可折叠的筛选面板
- ✅ 响应式设计，适配移动端
- ✅ 防抖处理，优化性能
- ✅ **URL参数同步**：自动从URL读取初始筛选值
- ✅ **单个字段清除**：每个筛选字段支持快速清除
- ✅ **与动态表格自动集成**：筛选条件变化自动更新表格数据
- ✅ **改进的数据收集**：正确处理复选框、数组等复杂数据类型
- ✅ **筛选字段设置**：支持自定义显示/隐藏筛选字段，支持拖拽排序（可选）
- ✅ **日期快捷选择**：支持"今天"、"昨天"、"本周"、"本月"等快捷日期选择
- ✅ **筛选条件标签**：显示已选择的筛选条件，支持快速清除
- ✅ **多选下拉框**：提供更友好的多选下拉框组件
- ✅ **字段依赖关系**：支持字段之间的显示/隐藏依赖关系
- ✅ **筛选预设模板**：保存/加载常用筛选组合，支持导入/导出
- ✅ **筛选历史记录**：自动记录最近使用的筛选条件，快速恢复
- ✅ **时间选择器**：支持time和datetime类型

## 基本使用

### 1. 在视图中配置筛选

```python
# views.py
def my_list_view(request):
    # 配置筛选面板
    filter_config = {
        'id': 'myFilterPanel',
        'method': 'form',  # 'ajax' 或 'form'
        'form_action': reverse('my_app:list'),  # 表单提交URL
        'auto_submit': True,  # 是否自动提交
        'debounce_ms': 300,  # 防抖延迟（毫秒）
        'collapsible': True,  # 是否可折叠
        'default_collapsed': False,  # 默认是否折叠
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
                'default': 'all',
                'required': False
            },
            {
                'key': 'keyword',
                'label': '关键词',
                'type': 'text',
                'placeholder': '请输入关键词...',
                'default': ''
            }
        ]
    }
    
    context = {
        'filter_config': filter_config,
        # ... 其他上下文数据
    }
    return render(request, 'my_app/list.html', context)
```

### 2. 在模板中引入

```django
{% include 'shared/_filter_panel.html' with filter_config=filter_config %}
```

### 3. 与动态表格集成

```python
# views.py
table_config = {
    'id': 'myTable',
    'filterable': True,
    'filter_config': {
        'id': 'tableFilter',
        'method': 'ajax',
        'submit_url': reverse('my_app:api_list'),
        'auto_submit': True,
        'filters': [
            # ... 筛选配置
        ]
    },
    # ... 其他表格配置
}
```

## 筛选类型详解

### 1. 下拉选择 (select)

```python
{
    'key': 'status',
    'label': '状态',
    'type': 'select',
    'options': [
        {'value': 'all', 'label': '全部'},
        {'value': 'active', 'label': '启用'},
        {'value': 'inactive', 'label': '禁用'}
    ],
    'default': 'all'
}
```

### 2. 文本输入 (text)

```python
{
    'key': 'keyword',
    'label': '关键词',
    'type': 'text',
    'placeholder': '请输入关键词...',
    'default': ''
}
```

### 3. 日期选择 (date)

```python
{
    'key': 'date',
    'label': '日期',
    'type': 'date',
    'default': ''  # YYYY-MM-DD 格式
}
```

### 4. 日期范围 (date_range)

```python
{
    'key': 'date_range',
    'label': '日期范围',
    'type': 'date_range',
    'start_key': 'start_date',  # 可选，默认为 {key}_start
    'end_key': 'end_date',  # 可选，默认为 {key}_end
    'default': {
        'start': '',
        'end': ''
    }
}
```

### 5. 数字输入 (number)

```python
{
    'key': 'price',
    'label': '价格',
    'type': 'number',
    'placeholder': '请输入价格',
    'min': 0,
    'max': 10000,
    'step': 0.01,
    'default': ''
}
```

### 6. 数字范围 (number_range)

```python
{
    'key': 'price_range',
    'label': '价格范围',
    'type': 'number_range',
    'start_key': 'min_price',  # 可选
    'end_key': 'max_price',  # 可选
    'min': 0,
    'max': 10000,
    'default': {
        'min': '',
        'max': ''
    }
}
```

### 7. 复选框组 (checkbox)

```python
{
    'key': 'tags',
    'label': '标签',
    'type': 'checkbox',
    'options': [
        {'value': 'tag1', 'label': '标签1'},
        {'value': 'tag2', 'label': '标签2'},
        {'value': 'tag3', 'label': '标签3'}
    ],
    'default': []  # 选中的值列表
}
```

### 8. 单选按钮组 (radio)

```python
{
    'key': 'type',
    'label': '类型',
    'type': 'radio',
    'options': [
        {'value': 'type1', 'label': '类型1'},
        {'value': 'type2', 'label': '类型2'}
    ],
    'default': 'type1'
}
```

### 9. 多选下拉框 (multiselect)

```python
{
    'key': 'tags',
    'label': '标签',
    'type': 'multiselect',
    'options': [
        {'value': 'tag1', 'label': '标签1'},
        {'value': 'tag2', 'label': '标签2'},
        {'value': 'tag3', 'label': '标签3'}
    ],
    'default': ['tag1', 'tag2']  # 默认选中的值列表
}
```

### 10. 带快捷选择的日期字段

```python
{
    'key': 'date',
    'label': '日期',
    'type': 'date',
    'quick_select': [
        {'value': 'today', 'label': '今天'},
        {'value': 'yesterday', 'label': '昨天'},
        {'value': 'this_week', 'label': '本周'},
        {'value': 'last_week', 'label': '上周'},
        {'value': 'this_month', 'label': '本月'},
        {'value': 'last_month', 'label': '上月'}
    ],
    'default': ''
}
```

### 11. 带快捷选择的日期范围字段

```python
{
    'key': 'date_range',
    'label': '日期范围',
    'type': 'date_range',
    'quick_select': [
        {'value': 'today', 'label': '今天'},
        {'value': 'this_week', 'label': '本周'},
        {'value': 'this_month', 'label': '本月'},
        {'value': 'this_year', 'label': '今年'}
    ],
    'default': {'start': '', 'end': ''}
}
```

### 12. 字段依赖关系

```python
{
    'key': 'category',
    'label': '分类',
    'type': 'select',
    'options': [
        {'value': 'all', 'label': '全部'},
        {'value': 'type1', 'label': '类型1'},
        {'value': 'type2', 'label': '类型2'}
    ]
},
{
    'key': 'subcategory',
    'label': '子分类',
    'type': 'select',
    'depends_on': 'category',  # 依赖于category字段
    'depends_value': 'type1,type2',  # 仅在category为type1或type2时显示
    'options': [...]
}
```

在模板中，也可以使用data属性：
```django
<div class="filter-field" 
     data-filter-key="subcategory"
     data-depends-on="category"
     data-depends-value="type1,type2">
    <!-- 字段内容 -->
</div>
```

### 13. 时间选择器 (time)

```python
{
    'key': 'time',
    'label': '时间',
    'type': 'time',
    'default': ''  # HH:MM 格式
}
```

### 14. 日期时间选择器 (datetime)

```python
{
    'key': 'datetime',
    'label': '日期时间',
    'type': 'datetime',
    'default': ''  # YYYY-MM-DDTHH:MM 格式
}
```

### 15. 启用筛选预设功能

```python
filter_config = {
    'id': 'myFilter',
    'enable_presets': True,  # 启用预设功能
    'filters': [...]
}
```

功能说明：
- **保存预设**：点击"预设"按钮，选择"保存当前筛选"，输入预设名称即可保存
- **应用预设**：在预设下拉菜单中选择已保存的预设即可应用
- **删除预设**：在预设列表中点击删除按钮
- **导入/导出预设**：支持JSON格式的导入导出，方便分享和备份

### 16. 启用筛选历史功能

```python
filter_config = {
    'id': 'myFilter',
    'enable_history': True,  # 启用历史功能
    'max_history': 10,  # 最大历史记录数（默认10）
    'filters': [...]
}
```

功能说明：
- **自动记录**：每次筛选提交时自动保存到历史记录
- **快速恢复**：在历史下拉菜单中选择历史记录即可恢复筛选条件
- **限制数量**：自动限制历史记录数量，防止占用过多存储空间
- **去重处理**：相同筛选条件不会重复记录

## JavaScript API

### 获取筛选数据

```javascript
// 获取当前筛选条件
const filterData = window.filterPanels['myFilterPanel'].getFilterData();
console.log(filterData);
// 输出: { status: 'active', keyword: 'test', ... }
```

### 手动提交筛选

```javascript
// 手动触发筛选提交
window.filterPanels['myFilterPanel'].submit();
```

### 重置筛选

```javascript
// 重置所有筛选条件
window.filterPanels['myFilterPanel'].reset();
```

### 设置筛选数据

```javascript
// 程序化设置筛选条件
window.filterPanels['myFilterPanel'].setFilterData({
    status: 'active',
    keyword: 'test',
    start_date: '2024-01-01',
    end_date: '2024-12-31'
});
```

### 更新URL参数

```javascript
// 将当前筛选条件同步到URL（不刷新页面）
window.filterPanels['myFilterPanel'].updateURL(true);  // true=replaceState, false=pushState
```

### 监听筛选事件

```javascript
// 监听筛选变化事件
if (!window.filterPanelEvents) {
    window.filterPanelEvents = {};
}

window.filterPanelEvents.onFilter = function(filterId, filterData) {
    console.log('筛选条件变化:', filterId, filterData);
    // 在这里处理筛选逻辑
    // 例如：更新表格数据
    if (window.dynamicTables && window.dynamicTables['myTable']) {
        window.dynamicTables['myTable'].loadData(filterData);
    }
};

// 监听数据更新事件（AJAX模式）
window.filterPanelEvents.onDataUpdate = function(filterId, data) {
    console.log('数据更新:', filterId, data);
    // 更新表格显示
};

// 监听错误事件
window.filterPanelEvents.onError = function(filterId, error) {
    console.error('筛选错误:', filterId, error);
    // 显示错误提示
};
```

## 与动态表格集成示例

```python
# views.py
def list_view(request):
    # 筛选配置
    filter_config = {
        'id': 'documentFilter',
        'method': 'ajax',
        'submit_url': reverse('api:document_list'),
        'auto_submit': True,
        'filters': [
            {
                'key': 'status',
                'label': '状态',
                'type': 'select',
                'options': [
                    {'value': 'all', 'label': '全部'},
                    {'value': 'draft', 'label': '草稿'},
                    {'value': 'published', 'label': '已发布'}
                ],
                'default': 'all'
            },
            {
                'key': 'date_range',
                'label': '创建日期',
                'type': 'date_range',
                'default': {'start': '', 'end': ''}
            }
        ]
    }
    
    # 表格配置
    table_config = {
        'id': 'documentTable',
        'filterable': True,
        'filter_config': filter_config,
        'ajax_url': reverse('api:document_list'),
        'columns': [
            {'key': 'id', 'label': 'ID', 'sortable': True},
            {'key': 'title', 'label': '标题', 'sortable': True},
            {'key': 'status', 'label': '状态', 'sortable': False},
            {'key': 'created_at', 'label': '创建时间', 'sortable': True}
        ],
        'pagination': True,
        'page_size': 10
    }
    
    context = {
        'table_config': table_config
    }
    return render(request, 'my_app/list.html', context)
```

```django
{# list.html #}
{% extends "shared/list_page_base.html" %}
{% load static %}

{% block list_page_content %}
    {% include 'shared/_dynamic_table.html' with table_config=table_config %}
{% endblock %}

{% block list_page_custom_js %}
<script>
// 连接筛选面板和动态表格
if (window.filterPanelEvents) {
    window.filterPanelEvents.onFilter = function(filterId, filterData) {
        if (filterId === 'documentFilter' && window.dynamicTables['documentTable']) {
            window.dynamicTables['documentTable'].loadData(filterData);
        }
    };
}
</script>
{% endblock %}
```

## 后端处理示例

### 表单提交模式

```python
# views.py
def list_view(request):
    # 获取筛选参数
    status = request.GET.get('status', 'all')
    keyword = request.GET.get('keyword', '')
    start_date = request.GET.get('date_range_start', '')
    end_date = request.GET.get('date_range_end', '')
    
    # 构建查询
    queryset = MyModel.objects.all()
    
    if status != 'all':
        queryset = queryset.filter(status=status)
    
    if keyword:
        queryset = queryset.filter(
            Q(title__icontains=keyword) |
            Q(description__icontains=keyword)
        )
    
    if start_date:
        queryset = queryset.filter(created_at__gte=start_date)
    
    if end_date:
        queryset = queryset.filter(created_at__lte=end_date)
    
    # 分页
    paginator = Paginator(queryset, 10)
    page_obj = paginator.get_page(request.GET.get('page', 1))
    
    context = {
        'page_obj': page_obj,
        # ...
    }
    return render(request, 'my_app/list.html', context)
```

### AJAX模式

```python
# views.py
from django.http import JsonResponse

def api_list_view(request):
    # 获取筛选参数（同上）
    status = request.GET.get('status', 'all')
    keyword = request.GET.get('keyword', '')
    # ...
    
    # 构建查询（同上）
    queryset = MyModel.objects.all()
    # ...
    
    # 分页
    page = int(request.GET.get('page', 1))
    page_size = int(request.GET.get('page_size', 10))
    paginator = Paginator(queryset, page_size)
    page_obj = paginator.get_page(page)
    
    # 返回JSON数据
    return JsonResponse({
        'results': [
            {
                'id': obj.id,
                'title': obj.title,
                'status': obj.status,
                'created_at': obj.created_at.strftime('%Y-%m-%d %H:%M:%S')
            }
            for obj in page_obj
        ],
        'count': paginator.count,
        'page': page,
        'page_size': page_size,
        'total_pages': paginator.num_pages
    })
```

## 样式自定义

筛选面板使用了Bootstrap样式，可以通过CSS覆盖来自定义样式：

```css
/* 自定义筛选面板样式 */
.filter-panel-container {
    border-radius: 0.5rem;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.filter-field {
    /* 自定义筛选字段样式 */
}

.filter-label {
    /* 自定义标签样式 */
}
```

## 新增功能说明

### URL参数同步

筛选面板会自动从URL参数中读取初始值。例如，如果URL是 `/list/?status=active&keyword=test`，筛选面板会自动设置相应的筛选条件。

### 单个字段清除

每个筛选字段都支持快速清除功能：
- 当字段有值时，会显示一个清除按钮（×）
- 点击清除按钮可以快速清空该字段的值
- 清除后会自动触发筛选（如果启用了自动提交）

### 与动态表格自动集成

当筛选面板与动态表格一起使用时，它们会自动连接：
- 筛选条件变化时，自动更新表格数据
- 搜索关键词与筛选条件会自动合并
- 无需手动编写连接代码

```python
# 只需要配置filter_config，系统会自动连接
table_config = {
    'id': 'myTable',
    'ajax_url': '/api/data/',
    'filterable': True,
    'filter_config': {
        'id': 'myFilter',
        'method': 'ajax',
        'filters': [...]
    }
}
```

## 筛选字段设置功能说明

### 启用方式

在 `filter_config` 中添加以下配置：

```python
filter_config = {
    'enable_field_settings': True,  # 启用筛选字段设置功能
    'max_enabled_fields': 10,  # 最多可启用的字段数（默认：10）
    'default_enabled_fields': ['field1', 'field2'],  # 默认启用的字段key列表（可选）
    'required_fields': ['field1'],  # 必填字段列表，这些字段不可隐藏（可选）
    # ... 其他配置
}
```

### 功能特性

- **显示/隐藏字段**：用户可以选择显示或隐藏筛选字段
- **拖拽排序**：支持拖拽调整筛选字段的显示顺序
- **必填字段保护**：必填字段（`required_fields`）不可隐藏
- **数量限制**：可设置最多启用的字段数（`max_enabled_fields`）
- **持久化存储**：设置保存在localStorage中，按筛选面板ID区分
- **搜索过滤**：在设置模态框中支持搜索字段名称

### 必填字段配置

可以通过两种方式设置必填字段：

1. **在filter_config中配置**（推荐）：
   ```python
   'required_fields': ['status', 'date']
   ```

2. **在单个筛选字段中配置**：
   ```python
   {
       'key': 'status',
       'required': True,  # 单个字段设为必填
       # ...
   }
   ```

两种方式都会被识别，必填字段在设置界面中不可取消勾选。

## 注意事项

1. **筛选ID唯一性**：确保每个筛选面板的 `id` 在页面中唯一
2. **默认值格式**：
   - 日期范围：`{'start': '', 'end': ''}`
   - 数字范围：`{'min': '', 'max': ''}`
   - 复选框：`[]`（数组）
3. **AJAX模式**：需要后端提供JSON格式的API接口
4. **表单模式**：会触发页面刷新，适合传统的表单提交场景
5. **防抖延迟**：建议设置为300-500毫秒，平衡用户体验和性能
6. **URL参数**：筛选面板会自动读取URL参数作为初始值，支持浏览器前进/后退
7. **清除按钮**：仅在文本、数字、日期、下拉选择字段上显示，复选框和单选按钮组不显示
8. **筛选字段设置**：需要引入 `filter-fields-settings.js` 文件（已自动引入），确保该文件已加载
9. **筛选预设和历史**：数据保存在localStorage中，按筛选面板ID区分，清除浏览器缓存会丢失数据

## 完整示例

查看 `templates/shared/dynamic_table_example.html` 获取完整的使用示例。

