# 筛选功能模块 - 快速集成指南

## 📦 模块文件

- `list-filters.js` - 核心筛选功能
- `filter-fields-settings.js` - 筛选字段设置功能（可选）
- `list-filters.README.md` - 详细文档
- `filter-fields-settings.README.md` - 设置功能文档

## 🚀 快速开始（3步集成）

### 步骤 1: 引入文件

```html
<!-- 引入CSS样式 -->
<link rel="stylesheet" href="{% static 'css/components/list-filters.css' %}">

<!-- 引入JavaScript文件 -->
<script src="{% static 'js/list-filters.js' %}"></script>
```

### 步骤 2: HTML结构

```html
<form method="get" id="filterForm">
    <div id="basicFilters">
        <!-- 筛选字段行 -->
        <div class="filter-row" data-filter-key="status">
            <label class="filter-label">状态:</label>
            <div class="filter-buttons">
                <button type="button" class="filter-btn active" 
                        data-filter="status" data-value="">全部</button>
                <button type="button" class="filter-btn" 
                        data-filter="status" data-value="active">启用</button>
                <input type="hidden" name="status" id="filter_status" value="">
            </div>
        </div>
    </div>
</form>
```

### 步骤 3: 完成！

模块会自动初始化，无需额外配置。

## 📋 完整示例

### 基础筛选（无设置功能）

```html
<!DOCTYPE html>
<html>
<head>
    <link rel="stylesheet" href="{% static 'css/components/list-filters.css' %}">
</head>
<body>
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
                    <input type="hidden" name="status" id="filter_status" value="">
                </div>
            </div>
        </div>
    </form>

    <script src="{% static 'js/list-filters.js' %}"></script>
</body>
</html>
```

### 带筛选字段设置功能

```html
<!-- 1. 引入文件 -->
<link rel="stylesheet" href="{% static 'css/components/list-filters.css' %}">
<script src="{% static 'js/filter-fields-settings.js' %}"></script>
<script src="{% static 'js/list-filters.js' %}"></script>

<!-- 2. 添加设置按钮 -->
<button type="button" id="settingsFilterFieldsBtn">⚙️ 设置筛选字段</button>

<!-- 3. 包含模态框模板 -->
{% include "your_app/includes/filter_fields_settings_modal.html" %}

<!-- 4. 配置 -->
<script>
window.listFiltersConfig = {
    enableFieldsSettings: true,
    fieldsSettingsStorageKey: 'your_module_filter_fields',
    defaultEnabledFields: ['status', 'type']
};
</script>
```

## 🎯 支持的筛选类型

### 1. 按钮筛选
```html
<button type="button" class="filter-btn" 
        data-filter="status" data-value="active">启用</button>
```

### 2. 下拉框筛选
```html
<select name="region" class="form-select">
    <option value="">请选择</option>
    <option value="北京">北京</option>
</select>
<input type="hidden" name="region" id="filter_region" value="">
```

### 3. 文本输入筛选
```html
<input type="text" id="filter_name" class="form-control" placeholder="请输入">
```

### 4. 日期范围筛选
```html
<button type="button" class="filter-btn" 
        data-filter="date_range" data-value="today">今天</button>
<button type="button" class="filter-btn" 
        data-filter="date_range" data-value="custom">自定义</button>
<div id="customDateRange" style="display: none;">
    <input type="date" name="start_date">
    <span>至</span>
    <input type="date" name="end_date">
</div>
```

## ⚙️ 配置选项

```javascript
window.listFiltersConfig = {
    formId: 'filterForm',              // 表单ID
    debounceDelay: 500,                // 防抖延迟（毫秒）
    autoSubmit: true,                  // 自动提交
    enableFieldsSettings: false,       // 启用字段设置
    fieldsSettingsStorageKey: 'filter_fields_settings',  // 存储键名
    maxEnabledFields: 10,              // 最多启用字段数
    defaultEnabledFields: []           // 默认启用字段
};
```

## 📚 详细文档

- 完整文档: `list-filters.README.md`
- 设置功能文档: `filter-fields-settings.README.md`

## ✅ 已应用模块

- ✅ 客户管理模块 (`customer_management`)

## 🔧 自定义配置示例

```javascript
// 自定义表单ID
window.listFiltersConfig = {
    formId: 'myFilterForm'
};

// 禁用自动提交，手动控制
window.listFiltersConfig = {
    autoSubmit: false
};
// 手动提交: window.listFiltersInstance.submit();

// 启用筛选字段设置
window.listFiltersConfig = {
    enableFieldsSettings: true,
    fieldsSettingsStorageKey: 'my_module_filters',
    defaultEnabledFields: ['field1', 'field2']
};
```

## 💡 注意事项

1. **必须的属性**：
   - 筛选按钮: `data-filter` 和 `data-value`
   - 筛选行: `data-filter-key`
   - 隐藏输入框: `id="filter_字段名"` 和 `name="字段名"`

2. **"全部"按钮**：
   - `data-value` 必须为空字符串 `""`
   - 必须添加 `active` 类（默认选中）

3. **自动初始化**：
   - 模块会在 DOM 加载完成后自动初始化
   - 如果需要在代码中访问实例: `window.listFiltersInstance`

## 🐛 常见问题

**Q: 筛选不生效？**
A: 检查表单ID是否为 `filterForm`，或配置 `formId` 选项。

**Q: 如何禁用自动提交？**
A: 设置 `autoSubmit: false`，然后手动调用 `window.listFiltersInstance.submit()`。

**Q: 如何添加筛选字段设置功能？**
A: 引入 `filter-fields-settings.js`，包含模态框模板，设置 `enableFieldsSettings: true`。

