# 动态表格管理模块使用文档

## 简介

`dynamic-table.js` 是一个通用的动态表格管理模块，用于在Django项目中统一处理表格行的添加、删除和行号更新功能。

## 功能特性

- ✅ 动态添加表格行
- ✅ 删除表格行（支持最少行数限制）
- ✅ 自动更新行号
- ✅ 支持自定义行模板
- ✅ 支持回调函数（添加/删除后执行）
- ✅ 支持数据获取和设置
- ✅ 自动绑定事件

## 引入方式

在HTML模板中引入：

```html
<script src="{% static 'js/dynamic-table.js' %}"></script>
```

## 基本使用

### 1. 简单示例

```javascript
document.addEventListener('DOMContentLoaded', function() {
    // 创建表格管理器
    const tableManager = new DynamicTableManager({
        containerId: 'parties-container',  // tbody的ID
        rowClass: 'party-row',              // 行的CSS类名
        addButtonId: 'add-party-btn',       // 添加按钮的ID
        removeButtonClass: 'remove-party-btn', // 删除按钮的CSS类名
        minRows: 2,                         // 最少保留2行
        rowTemplate: (index, data) => {
            // 行模板函数，返回HTML字符串
            return `
                <td style="text-align: center;">
                    <strong>0</strong>
                </td>
                <td>
                    <input type="text" 
                           name="parties[${index}][party_name]" 
                           class="form-control form-control-sm"
                           value="${data.party_name || ''}"
                           placeholder="请输入单位名称" required>
                </td>
                <td>
                    <button type="button" class="btn btn-sm btn-danger remove-party-btn">
                        <i class="bi bi-trash"></i> 删除
                    </button>
                </td>
            `;
        }
    });
});
```

### 2. 完整示例（带回调函数）

```javascript
document.addEventListener('DOMContentLoaded', function() {
    const tableManager = new DynamicTableManager({
        containerId: 'service-contents-container',
        rowClass: 'service-content-row',
        addButtonId: 'add-service-content-btn',
        removeButtonClass: 'remove-service-content-btn',
        minRows: 1,
        rowTemplate: (index, data) => {
            return `
                <td style="text-align: center;">
                    <strong>0</strong>
                </td>
                <td>
                    <select name="service_contents[${index}][service_type]" 
                            class="form-select form-select-sm" required>
                        <option value="">请选择</option>
                        <option value="1" ${data.service_type == 1 ? 'selected' : ''}>服务类型1</option>
                        <option value="2" ${data.service_type == 2 ? 'selected' : ''}>服务类型2</option>
                    </select>
                </td>
                <td>
                    <input type="text" 
                           name="service_contents[${index}][description]" 
                           class="form-control form-control-sm"
                           value="${data.description || ''}"
                           placeholder="请输入描述">
                </td>
                <td>
                    <button type="button" class="btn btn-sm btn-danger remove-service-content-btn">
                        <i class="bi bi-trash"></i>
                    </button>
                </td>
            `;
        },
        // 添加行后的回调
        onAdd: (row, index) => {
            console.log(`添加了第 ${index} 行`);
            // 可以在这里初始化下拉选项、绑定其他事件等
            const select = row.querySelector('select[name*="[service_type]"]');
            if (select && typeof initServiceTypeOptions === 'function') {
                initServiceTypeOptions(select);
            }
        },
        // 删除行前的回调（返回false可阻止删除）
        onRemove: (row, index) => {
            const confirmDelete = confirm('确定要删除这一行吗？');
            return confirmDelete; // 返回false会阻止删除
        },
        // 更新行号时的回调
        onUpdateNumbers: (rows) => {
            console.log(`当前共有 ${rows.length} 行`);
        }
    });
});
```

## API 参考

### 构造函数参数

| 参数 | 类型 | 必需 | 默认值 | 说明 |
|------|------|------|--------|------|
| `containerId` | string | ✅ | - | 表格容器ID（tbody元素） |
| `rowClass` | string | ❌ | `'dynamic-table-row'` | 行的CSS类名 |
| `addButtonId` | string | ❌ | - | 添加按钮ID |
| `removeButtonClass` | string | ❌ | `'remove-row-btn'` | 删除按钮CSS类名 |
| `minRows` | number | ❌ | `1` | 最少保留行数 |
| `rowTemplate` | Function | ✅ | - | 行模板函数 `(index, data) => string` |
| `onAdd` | Function | ❌ | `() => {}` | 添加行后的回调 `(row, index) => void` |
| `onRemove` | Function | ❌ | `() => true` | 删除行前的回调 `(row, index) => boolean` |
| `onUpdateNumbers` | Function | ❌ | `() => {}` | 更新行号时的回调 `(rows) => void` |
| `autoUpdateNumbers` | boolean | ❌ | `true` | 是否自动更新行号 |
| `numberCellSelector` | string | ❌ | `'td:first-child'` | 行号单元格选择器 |

### 实例方法

#### `addRow(data)`
添加新行

**参数：**
- `data` (Object, 可选): 行数据对象

**返回：** `HTMLElement|null` 新创建的行元素

**示例：**
```javascript
const row = tableManager.addRow({ party_name: '测试公司', party_type: 'party_a' });
```

#### `removeRow(row)`
删除指定行

**参数：**
- `row` (HTMLElement): 要删除的行元素

**返回：** `boolean` 是否成功删除

**示例：**
```javascript
const rows = tableManager.getRows();
if (rows.length > 0) {
    tableManager.removeRow(rows[0]);
}
```

#### `getRows()`
获取所有行

**返回：** `NodeList` 所有行元素

**示例：**
```javascript
const rows = tableManager.getRows();
console.log(`共有 ${rows.length} 行`);
```

#### `updateRowNumbers()`
手动更新行号

**示例：**
```javascript
tableManager.updateRowNumbers();
```

#### `getRowData(row)`
获取指定行的数据

**参数：**
- `row` (HTMLElement): 行元素

**返回：** `Object` 行数据对象

**示例：**
```javascript
const rows = tableManager.getRows();
const data = tableManager.getRowData(rows[0]);
console.log(data); // { party_name: 'xxx', party_type: 'party_a', ... }
```

#### `getAllRowData()`
获取所有行的数据

**返回：** `Array` 所有行的数据数组

**示例：**
```javascript
const allData = tableManager.getAllRowData();
console.log(allData); // [{ party_name: 'xxx', ... }, { ... }, ...]
```

#### `setRowData(row, data)`
设置指定行的数据

**参数：**
- `row` (HTMLElement): 行元素
- `data` (Object): 要设置的数据

**示例：**
```javascript
const row = tableManager.getRows()[0];
tableManager.setRowData(row, { party_name: '新公司名称', party_type: 'party_b' });
```

#### `clear()`
清空所有行

**示例：**
```javascript
tableManager.clear();
```

## 在合同表单中的使用示例

### 签约主体表格

```javascript
// 签约主体表格管理器
const partiesTableManager = new DynamicTableManager({
    containerId: 'parties-container',
    rowClass: 'party-row',
    addButtonId: 'add-party-btn',
    removeButtonClass: 'remove-party-btn',
    minRows: 2,
    rowTemplate: (index, data) => {
        const escapeHtml = (str) => (str || '').replace(/"/g, '&quot;').replace(/'/g, '&#39;');
        return `
            <td style="vertical-align: middle; text-align: center;">
                <strong>0</strong>
            </td>
            <td>
                <select name="parties[${index}][party_type]" class="form-select form-select-sm" required>
                    <option value="party_a" ${data.party_type === 'party_a' ? 'selected' : ''}>甲方</option>
                    <option value="party_b" ${data.party_type === 'party_b' ? 'selected' : ''}>乙方</option>
                    <option value="party_c" ${data.party_type === 'party_c' ? 'selected' : ''}>丙方</option>
                    <option value="other" ${data.party_type === 'other' ? 'selected' : ''}>其他</option>
                </select>
            </td>
            <td>
                <input type="text" name="parties[${index}][party_name]" 
                       class="form-control form-control-sm"
                       value="${escapeHtml(data.party_name || '')}" 
                       placeholder="请输入单位名称" required>
            </td>
            <td>
                <input type="text" name="parties[${index}][credit_code]" 
                       class="form-control form-control-sm"
                       value="${escapeHtml(data.credit_code || '')}" 
                       placeholder="请输入统一社会信用代码">
            </td>
            <td>
                <button type="button" class="btn btn-sm btn-danger remove-party-btn" title="删除">
                    <i class="bi bi-trash"></i>
                </button>
            </td>
        `;
    },
    onAdd: (row, index) => {
        // 添加行后可以执行一些初始化操作
        console.log(`添加了签约主体行 ${index}`);
    }
});

// 初始化时确保至少有两行
if (partiesTableManager.getRows().length === 0) {
    partiesTableManager.addRow({ party_type: 'party_a' });
    partiesTableManager.addRow({ party_type: 'party_b' });
}
```

### 服务信息表格

```javascript
// 服务信息表格管理器
const serviceContentsTableManager = new DynamicTableManager({
    containerId: 'service-contents-container',
    rowClass: 'service-content-row',
    addButtonId: 'add-service-content-btn',
    removeButtonClass: 'remove-service-content-btn',
    minRows: 1,
    rowTemplate: (index, data) => {
        // 使用服务类型选项（需要从后端传入）
        let serviceTypeOptions = '';
        if (typeof serviceTypeOptions !== 'undefined') {
            serviceTypeOptions.forEach(opt => {
                const selected = data.service_type == opt.value ? 'selected' : '';
                serviceTypeOptions += `<option value="${opt.value}" ${selected}>${opt.label}</option>`;
            });
        }
        
        return `
            <td style="text-align: center;">
                <strong>0</strong>
            </td>
            <td>
                <select name="service_contents[${index}][service_type]" 
                        class="form-select form-select-sm service-type-select" required>
                    <option value="">请选择</option>
                    ${serviceTypeOptions}
                </select>
            </td>
            <td>
                <input type="text" name="service_contents[${index}][description]" 
                       class="form-control form-control-sm"
                       value="${(data.description || '').replace(/"/g, '&quot;')}" 
                       placeholder="请输入描述">
            </td>
            <td>
                <button type="button" class="btn btn-sm btn-danger remove-service-content-btn">
                    <i class="bi bi-trash"></i>
                </button>
            </td>
        `;
    },
    onAdd: (row, index) => {
        // 初始化下拉选项
        const select = row.querySelector('.service-type-select');
        if (select && typeof initServiceTypeSelect === 'function') {
            initServiceTypeSelect(select);
        }
    }
});

// 初始化时确保至少有一行
if (serviceContentsTableManager.getRows().length === 0) {
    serviceContentsTableManager.addRow();
}
```

## 注意事项

1. **XSS防护**：在模板函数中使用用户输入的数据时，务必进行HTML转义，可以使用 `escapeHtml` 函数或类似方法。

2. **字段名格式**：建议使用 `name="prefix[${index}][field_name]"` 格式，这样后端可以方便地解析数据。

3. **索引管理**：模块会自动管理索引，无需手动维护。

4. **事件绑定**：删除按钮的事件会自动绑定，无需手动处理。

5. **最少行数**：设置 `minRows` 后，删除时会自动检查，防止删除过多行。

## 迁移现有代码

将现有的 `addPartyRow()` 等函数迁移到新模块：

**旧代码：**
```javascript
function addPartyRow(partyData = null) {
    const container = document.getElementById('parties-container');
    const index = partyIndex++;
    const row = document.createElement('tr');
    row.innerHTML = `...`;
    container.appendChild(row);
    // ... 绑定事件等
}
```

**新代码：**
```javascript
const partiesTableManager = new DynamicTableManager({
    containerId: 'parties-container',
    rowClass: 'party-row',
    addButtonId: 'add-party-btn',
    rowTemplate: (index, data) => `...`
});

// 添加行
partiesTableManager.addRow(partyData);
```

## 兼容性

- 支持所有现代浏览器（Chrome, Firefox, Safari, Edge）
- 不需要任何外部依赖
- 可以与jQuery等库共存

## 更新日志

### v1.0 (2024-12-19)
- 初始版本
- 支持基本的添加/删除功能
- 支持自定义模板和回调函数

