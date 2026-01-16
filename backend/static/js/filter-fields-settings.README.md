# 筛选字段设置功能模块

这是一个可复用的筛选字段设置功能模块，可以在任何列表页面中使用。

## 功能特性

- ✅ 自动发现页面中的筛选字段
- ✅ 支持启用/禁用筛选字段
- ✅ 支持拖拽排序筛选字段
- ✅ 设置保存到localStorage
- ✅ 最多支持10个启用的筛选字段（可配置）
- ✅ 完全独立，易于集成

## 使用方法

### 1. 引入必要的文件

在HTML模板中引入：

```html
<!-- 引入CSS样式（如果还没有引入） -->
<link rel="stylesheet" href="{% static 'css/components/list-filters.css' %}">

<!-- 引入JavaScript文件 -->
<script src="{% static 'js/filter-fields-settings.js' %}"></script>

<!-- 引入模态框模板 -->
{% include "customer_management/includes/filter_fields_settings_modal.html" %}
```

### 2. 在筛选条件区域添加设置按钮

在筛选条件标题旁边添加设置按钮：

```html
<div class="list-page-filters">
    <div class="d-flex justify-content-between align-items-center mb-2">
        <h6 class="mb-0 small fw-semibold">筛选条件</h6>
        <div class="d-flex gap-2">
            <button type="button" class="btn btn-link btn-sm p-0 text-decoration-none" 
                    id="settingsFilterFieldsBtn" 
                    data-bs-toggle="modal" 
                    data-bs-target="#filterFieldsSettingsModal">
                ⚙️ 设置筛选字段
            </button>
        </div>
    </div>
    <div id="basicFilters">
        <!-- 筛选条件行，每个行需要添加 data-filter-key 属性 -->
        <div class="filter-row" data-filter-key="field1">
            <label class="filter-label">字段1:</label>
            <div class="filter-buttons">
                <!-- 筛选内容 -->
            </div>
        </div>
        <!-- 更多筛选字段... -->
    </div>
</div>
```

### 3. 初始化功能

在页面底部添加初始化代码：

```html
<script>
// 配置选项
window.filterFieldsSettingsConfig = {
    storageKey: 'my_page_filter_fields',  // localStorage存储键名
    containerId: 'basicFilters',            // 筛选条件容器ID
    modalId: 'filterFieldsSettingsModal',   // 模态框ID
    listId: 'filterFieldsList',            // 列表容器ID
    settingsBtnId: 'settingsFilterFieldsBtn', // 设置按钮ID
    saveBtnId: 'saveFilterFieldsSettings',   // 保存按钮ID
    resetBtnId: 'resetFilterFieldsSettings', // 重置按钮ID
    maxEnabledFields: 10,                   // 最多启用的字段数
    defaultEnabledFields: ['field1', 'field2'] // 默认启用的字段key数组
};

// 如果DOM已加载，手动初始化
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() {
        if (window.FilterFieldsSettings) {
            const instance = new window.FilterFieldsSettings(window.filterFieldsSettingsConfig);
            instance.init();
            window.filterFieldsSettingsInstance = instance;
        }
    });
} else {
    if (window.FilterFieldsSettings) {
        const instance = new window.FilterFieldsSettings(window.filterFieldsSettingsConfig);
        instance.init();
        window.filterFieldsSettingsInstance = instance;
    }
}
</script>
```

## 配置选项说明

| 选项 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `storageKey` | string | `'filter_fields_settings'` | localStorage存储键名，不同页面应使用不同的键名 |
| `containerId` | string | `'basicFilters'` | 筛选条件容器的ID |
| `modalId` | string | `'filterFieldsSettingsModal'` | 模态框的ID |
| `listId` | string | `'filterFieldsList'` | 筛选字段列表容器的ID |
| `settingsBtnId` | string | `'settingsFilterFieldsBtn'` | 设置按钮的ID |
| `saveBtnId` | string | `'saveFilterFieldsSettings'` | 保存按钮的ID |
| `resetBtnId` | string | `'resetFilterFieldsSettings'` | 重置按钮的ID |
| `maxEnabledFields` | number | `10` | 最多启用的筛选字段数量 |
| `defaultEnabledFields` | array | `[]` | 默认启用的字段key数组 |

## HTML结构要求

筛选字段的HTML结构必须符合以下要求：

```html
<div id="basicFilters">
    <!-- 每个筛选字段行必须包含 data-filter-key 属性 -->
    <div class="filter-row" data-filter-key="field_key">
        <!-- label 元素用于自动提取字段名称 -->
        <label class="filter-label">字段名称:</label>
        <div class="filter-buttons">
            <!-- 筛选内容 -->
        </div>
    </div>
</div>
```

## API方法

如果需要在代码中手动调用功能，可以使用实例方法：

```javascript
// 获取实例
const instance = window.filterFieldsSettingsInstance;

// 打开设置模态框
instance.openSettingsModal();

// 保存设置
instance.saveSettings();

// 应用设置
instance.applySettings();

// 重置设置
instance.resetSettings();
```

## 注意事项

1. **筛选字段必须包含 `data-filter-key` 属性**：模块通过此属性识别筛选字段
2. **字段名称自动提取**：从 `.filter-label` 元素中提取字段名称（自动移除冒号）
3. **localStorage存储**：每个页面应使用不同的 `storageKey`，避免冲突
4. **Bootstrap依赖**：模态框功能依赖Bootstrap 5
5. **CSS样式**：确保已引入 `list-filters.css` 样式文件

## 示例：客户列表页面

参考 `customer_list.html` 中的实现：

```html
<!-- 1. 引入文件 -->
<script src="{% static 'js/filter-fields-settings.js' %}"></script>
{% include "customer_management/includes/filter_fields_settings_modal.html" %}

<!-- 2. 添加设置按钮 -->
<button type="button" id="settingsFilterFieldsBtn" 
        data-bs-toggle="modal" 
        data-bs-target="#filterFieldsSettingsModal">
    ⚙️ 设置筛选字段
</button>

<!-- 3. 筛选条件容器 -->
<div id="basicFilters">
    <div class="filter-row" data-filter-key="client_level">
        <label class="filter-label">客户分类:</label>
        <!-- ... -->
    </div>
</div>

<!-- 4. 初始化 -->
<script>
window.filterFieldsSettingsConfig = {
    storageKey: 'customer_list_filter_fields',
    defaultEnabledFields: ['client_level', 'relationship_stage', 'region']
};
</script>
```

## 浏览器兼容性

- Chrome/Edge: ✅ 支持
- Firefox: ✅ 支持
- Safari: ✅ 支持
- IE11: ❌ 不支持（使用了ES6+语法）

## 更新日志

### v1.0.0 (2024)
- 初始版本
- 支持筛选字段的启用/禁用
- 支持拖拽排序
- 支持设置保存和重置

