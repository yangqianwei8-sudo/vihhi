# 列表筛选功能模块

这是一个可复用的列表页面筛选功能模块，可以在任何列表页面中使用。

## 功能特性

- ✅ 筛选按钮点击处理
- ✅ 日期范围筛选（今天、昨天、本周、上周、本月、上月、自定义）
- ✅ 下拉框筛选（自动同步隐藏字段）
- ✅ 文本输入防抖筛选（延迟提交，提升性能）
- ✅ 表单自动提交
- ✅ 按钮状态自动管理（"全部"按钮状态）
- ✅ **筛选字段设置功能（可选）** - 启用/禁用筛选字段、拖拽排序
- ✅ 完全独立，易于集成

## 使用方法

### 1. 引入文件

在HTML模板中引入：

```html
<!-- 引入CSS样式（如果还没有引入） -->
<link rel="stylesheet" href="{% static 'css/components/list-filters.css' %}">

<!-- 引入JavaScript文件 -->
<script src="{% static 'js/list-filters.js' %}"></script>

<!-- 如果需要使用筛选字段设置功能，还需要引入： -->
<script src="{% static 'js/filter-fields-settings.js' %}"></script>
```

### 2. HTML结构要求

筛选表单的基本结构：

```html
<form method="get" id="filterForm">
    <!-- 筛选条件容器 -->
    <div id="basicFilters">
        <!-- 筛选字段行 -->
        <div class="filter-row" data-filter-key="field_name">
            <label class="filter-label">字段名称:</label>
            <div class="filter-buttons">
                <!-- "全部"按钮 -->
                <button type="button" class="filter-btn active" 
                        data-filter="field_name" 
                        data-value="">
                    全部
                </button>
                <!-- 其他筛选选项 -->
                <button type="button" class="filter-btn" 
                        data-filter="field_name" 
                        data-value="value1">
                    选项1
                </button>
                <!-- 隐藏输入框（用于表单提交） -->
                <input type="hidden" name="field_name" id="filter_field_name" value="">
            </div>
        </div>
    </div>
</form>
```

### 3. 配置选项（可选）

如果需要自定义配置，在页面底部添加：

```html
<script>
window.listFiltersConfig = {
    formId: 'filterForm',        // 筛选表单ID
    debounceDelay: 500,          // 文本输入防抖延迟（毫秒）
    autoSubmit: true,            // 是否自动提交表单
    // 筛选字段设置功能（可选）
    enableFieldsSettings: true,  // 是否启用筛选字段设置功能
    fieldsSettingsStorageKey: 'customer_list_filter_fields',  // localStorage存储键名
    fieldsSettingsContainerId: 'basicFilters',  // 筛选条件容器ID
    fieldsSettingsModalId: 'filterFieldsSettingsModal',  // 模态框ID
    maxEnabledFields: 10,       // 最多启用的字段数
    defaultEnabledFields: ['client_level', 'relationship_stage', 'region']  // 默认启用的字段
};

// 如果DOM已加载，手动初始化
if (document.readyState !== 'loading' && window.ListFilters) {
    window.listFiltersInstance = new window.ListFilters(window.listFiltersConfig);
}
</script>
```

### 4. 启用筛选字段设置功能（可选）

如果需要使用筛选字段设置功能：

1. **引入必要的文件**：
```html
<!-- 引入筛选字段设置功能模块 -->
<script src="{% static 'js/filter-fields-settings.js' %}"></script>

<!-- 引入模态框模板 -->
{% include "customer_management/includes/filter_fields_settings_modal.html" %}
```

2. **添加设置按钮**：
```html
<button type="button" id="settingsFilterFieldsBtn" 
        data-bs-toggle="modal" 
        data-bs-target="#filterFieldsSettingsModal">
    ⚙️ 设置筛选字段
</button>
```

3. **在配置中启用**：
```javascript
window.listFiltersConfig = {
    enableFieldsSettings: true,  // 启用筛选字段设置功能
    defaultEnabledFields: ['field1', 'field2']  // 默认启用的字段
};
```

**注意**：`list-filters.js` 会检测 `window.FilterFieldsSettings` 是否存在。如果存在，则调用外部模块；如果不存在，会显示警告信息。

## 支持的筛选类型

### 1. 按钮筛选

使用 `data-filter` 和 `data-value` 属性：

```html
<button type="button" class="filter-btn" 
        data-filter="status" 
        data-value="active">
    启用
</button>
```

### 2. 下拉框筛选

支持的下拉框字段：
- `region` - 地区
- `department` - 部门
- `responsible_user` - 负责人

```html
<select name="region" class="form-select">
    <option value="">请选择地区</option>
    <option value="北京">北京</option>
    <option value="上海">上海</option>
</select>
<input type="hidden" name="region" id="filter_region" value="">
```

### 3. 文本输入筛选

支持的文本输入字段：
- `filter_industry` - 行业
- `filter_company_email` - 公司邮箱
- `filter_legal_representative` - 法定代表人

```html
<input type="text" 
       id="filter_industry" 
       class="form-control" 
       placeholder="请输入行业">
```

### 4. 日期范围筛选

```html
<!-- 日期范围按钮 -->
<button type="button" class="filter-btn" 
        data-filter="date_range" 
        data-value="today">
    今天
</button>

<!-- 自定义日期范围输入框 -->
<div id="customDateRange" style="display: none;">
    <input type="date" name="created_time_start">
    <span>至</span>
    <input type="date" name="created_time_end">
</div>
```

支持的日期范围值：
- `today` - 今天
- `yesterday` - 昨天
- `this_week` - 本周
- `last_week` - 上周
- `this_month` - 本月
- `last_month` - 上月
- `custom` - 自定义日期范围

## API方法

如果需要在代码中手动调用功能，可以使用实例方法：

```javascript
// 获取实例
const instance = window.listFiltersInstance;

// 手动提交表单
instance.submit();

// 重置筛选条件
instance.reset();
```

## 配置选项说明

| 选项 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `formId` | string | `'filterForm'` | 筛选表单的ID |
| `debounceDelay` | number | `500` | 文本输入防抖延迟（毫秒） |
| `autoSubmit` | boolean | `true` | 是否自动提交表单 |
| `enableFieldsSettings` | boolean | `false` | 是否启用筛选字段设置功能 |
| `fieldsSettingsStorageKey` | string | `'filter_fields_settings'` | localStorage存储键名 |
| `fieldsSettingsContainerId` | string | `'basicFilters'` | 筛选条件容器ID |
| `fieldsSettingsModalId` | string | `'filterFieldsSettingsModal'` | 模态框ID |
| `fieldsSettingsListId` | string | `'filterFieldsList'` | 筛选字段列表容器ID |
| `fieldsSettingsBtnId` | string | `'settingsFilterFieldsBtn'` | 设置按钮ID |
| `fieldsSettingsSaveBtnId` | string | `'saveFilterFieldsSettings'` | 保存按钮ID |
| `fieldsSettingsResetBtnId` | string | `'resetFilterFieldsSettings'` | 重置按钮ID |
| `maxEnabledFields` | number | `10` | 最多启用的筛选字段数量 |
| `defaultEnabledFields` | array | `[]` | 默认启用的字段key数组 |

## 完整示例

```html
<!DOCTYPE html>
<html>
<head>
    <link rel="stylesheet" href="{% static 'css/components/list-filters.css' %}">
</head>
<body>
    <!-- 筛选表单 -->
    <form method="get" id="filterForm">
        <div id="basicFilters">
            <!-- 状态筛选 -->
            <div class="filter-row" data-filter-key="status">
                <label class="filter-label">状态:</label>
                <div class="filter-buttons">
                    <button type="button" class="filter-btn active" 
                            data-filter="status" data-value="">全部</button>
                    <button type="button" class="filter-btn" 
                            data-filter="status" data-value="active">启用</button>
                    <button type="button" class="filter-btn" 
                            data-filter="status" data-value="inactive">禁用</button>
                    <input type="hidden" name="status" id="filter_status" value="">
                </div>
            </div>
            
            <!-- 日期范围筛选 -->
            <div class="filter-row" data-filter-key="date_range">
                <label class="filter-label">创建时间:</label>
                <div class="filter-buttons">
                    <button type="button" class="filter-btn active" 
                            data-filter="date_range" data-value="">全部</button>
                    <button type="button" class="filter-btn" 
                            data-filter="date_range" data-value="today">今天</button>
                    <button type="button" class="filter-btn" 
                            data-filter="date_range" data-value="this_month">本月</button>
                    <button type="button" class="filter-btn" 
                            data-filter="date_range" data-value="custom">自定义</button>
                    <div id="customDateRange" style="display: none;">
                        <input type="date" name="created_time_start">
                        <span>至</span>
                        <input type="date" name="created_time_end">
                    </div>
                    <input type="hidden" name="date_range" id="filter_date_range" value="">
                </div>
            </div>
        </div>
    </form>

    <!-- 引入JavaScript -->
    <script src="{% static 'js/list-filters.js' %}"></script>
    
    <!-- 可选：自定义配置 -->
    <script>
    window.listFiltersConfig = {
        formId: 'filterForm',
        debounceDelay: 500,
        autoSubmit: true
    };
    </script>
</body>
</html>
```

## 注意事项

1. **筛选按钮必须包含属性**：
   - `data-filter`: 筛选字段名称
   - `data-value`: 筛选值（空字符串表示"全部"）

2. **隐藏输入框命名规则**：
   - ID格式：`filter_字段名`
   - Name格式：与字段名相同

3. **"全部"按钮**：
   - `data-value` 必须为空字符串 `""`
   - 点击"全部"时会清空该字段的筛选条件

4. **自动提交**：
   - 默认情况下，筛选条件变化时会自动提交表单
   - 可以通过 `autoSubmit: false` 禁用自动提交，然后手动调用 `instance.submit()`

5. **防抖处理**：
   - 文本输入框使用防抖机制，避免频繁提交
   - 失去焦点时会立即提交

## 浏览器兼容性

- Chrome/Edge: ✅ 支持
- Firefox: ✅ 支持
- Safari: ✅ 支持
- IE11: ❌ 不支持（使用了ES6+语法）

## 更新日志

### v1.0.0 (2024)
- 初始版本
- 支持筛选按钮点击处理
- 支持日期范围筛选
- 支持下拉框筛选
- 支持文本输入防抖筛选
- 支持表单自动提交

