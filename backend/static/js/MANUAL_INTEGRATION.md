# 服务信息表格模块 - 手动集成指南

## 📋 集成清单

在开始之前，请确认以下文件存在：
- ✅ `/backend/static/js/dynamic-table.js`
- ✅ `/backend/templates/customer_management/contract_form.html`

## 🔧 集成步骤

### 步骤1: 引入 dynamic-table.js 模块

**位置**: 在 `contract_form.html` 中找到 `<script>` 标签开始处（约第691行，`DOMContentLoaded` 之前）

**操作**: 添加以下代码：

```html
<script src="{% static 'js/dynamic-table.js' %}"></script>
```

**完整示例**:
```html
<script src="{% static 'js/dynamic-table.js' %}"></script>
<script>
document.addEventListener('DOMContentLoaded', function() {
    // ... 其他代码
```

---

### 步骤2: 找到并替换 addServiceContent 函数

**位置**: 约第1744行，查找 `function addServiceContent(serviceData = null) {`

**操作**: 
1. 找到整个 `addServiceContent` 函数（从 `function addServiceContent` 开始，到对应的 `}` 结束）
2. 删除整个函数
3. 在相同位置插入以下代码（从 `contract-service-integration-complete.js` 文件复制）：

```javascript
// ========== 服务信息表格管理（使用动态表格模块） ==========
let serviceContentIndex = 0;

// HTML转义辅助函数
function escapeHtml(str) {
    if (!str) return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;');
}

// 创建服务信息表格管理器
const serviceContentsTableManager = new DynamicTableManager({
    containerId: 'service-contents-container',
    rowClass: 'service-content-row',
    addButtonId: 'add-service-content-btn',
    removeButtonClass: 'remove-service-content-btn',
    minRows: 1,
    rowTemplate: (index, data) => {
        const service = data || {};
        
        // 构建服务专业选项HTML
        let serviceProfessionOptions = '<option value="">-- 请选择服务专业 --</option>';
        if (typeof serviceProfessionsData !== 'undefined' && Array.isArray(serviceProfessionsData)) {
            serviceProfessionsData.forEach(function(sp) {
                const selected = service.service_profession == sp.id ? 'selected' : '';
                serviceProfessionOptions += `<option value="${sp.id}" data-service-type="${sp.service_type_id || ''}" ${selected}>${escapeHtml(sp.name)}</option>`;
            });
        }
        
        // 构建成果清单选项HTML
        let resultListOptions = '';
        if (typeof resultFileTypesData !== 'undefined' && Array.isArray(resultFileTypesData)) {
            resultFileTypesData.forEach(function(rft) {
                const selected = service.result_list && Array.isArray(service.result_list) && service.result_list.includes(String(rft.id))
                    ? 'selected' 
                    : '';
                resultListOptions += `<option value="${rft.id}" ${selected}>${escapeHtml(rft.name)}</option>`;
            });
        }
        
        // 构建服务类型选项HTML（使用Django模板语法）
        let serviceTypeOptions = '<option value="">-- 请选择服务类型 --</option>';
        {% for st in service_types %}
        const selected{{ st.id }} = service.service_type == {{ st.id }} ? 'selected' : '';
        serviceTypeOptions += `<option value="{{ st.id }}" ${selected{{ st.id }}}>{{ st.name }}</option>`;
        {% endfor %}
        
        return `
            <td style="vertical-align: middle; text-align: center;">
                <strong>0</strong>
            </td>
            <td>
                <select name="service_contents[${index}][service_type]" 
                        class="form-select form-select-sm service-type-select" required>
                    ${serviceTypeOptions}
                </select>
            </td>
            <td>
                <select name="service_contents[${index}][service_profession]" 
                        class="form-select form-select-sm service-profession-select" required>
                    ${serviceProfessionOptions}
                </select>
            </td>
            <td>
                <select name="service_contents[${index}][result_list]" 
                        class="form-select form-select-sm" 
                        multiple 
                        style="min-height: 60px;">
                    ${resultListOptions}
                </select>
                <small class="form-text text-muted">可多选，按住Ctrl/Cmd键选择多个</small>
            </td>
            <td style="vertical-align: middle; text-align: center;">
                <button type="button" class="btn btn-sm btn-danger remove-service-content-btn" title="删除">
                    <i class="bi bi-trash"></i> 删除
                </button>
            </td>
        `;
    },
    onAdd: (row, index) => {
        // 绑定服务类型变化事件，过滤服务专业
        const serviceTypeSelect = row.querySelector('.service-type-select');
        const serviceProfessionSelect = row.querySelector('.service-profession-select');
        
        if (serviceTypeSelect && serviceProfessionSelect) {
            // 过滤服务专业的函数
            function filterServiceProfessions() {
                const selectedServiceType = serviceTypeSelect.value;
                const options = serviceProfessionSelect.querySelectorAll('option');
                options.forEach(function(opt) {
                    if (opt.value === '') {
                        opt.style.display = '';
                    } else {
                        const serviceType = opt.getAttribute('data-service-type');
                        opt.style.display = (serviceType === selectedServiceType) ? '' : 'none';
                    }
                });
                // 如果当前选择的服务专业不匹配，清空选择
                const currentValue = serviceProfessionSelect.value;
                if (currentValue) {
                    const currentOption = serviceProfessionSelect.querySelector(`option[value="${currentValue}"]`);
                    if (currentOption && currentOption.style.display === 'none') {
                        serviceProfessionSelect.value = '';
                    }
                }
            }
            
            // 初始执行一次
            filterServiceProfessions();
            
            // 监听服务类型变化
            serviceTypeSelect.addEventListener('change', filterServiceProfessions);
        }
        
        console.log(`添加了服务信息行 ${index}`);
    },
    onRemove: (row, index) => {
        return true; // 允许删除
    },
    onUpdateNumbers: (rows) => {
        console.log(`当前共有 ${rows.length} 行服务信息`);
    }
});

// 初始化：确保至少有一行服务内容
if (serviceContentsTableManager.getRows().length === 0) {
    serviceContentsTableManager.addRow();
}

// 如果是从后端加载的数据（编辑模式），初始化已有数据
{% if existing_service_contents %}
const existingServiceContents = [
    {% for sc in existing_service_contents %}
    {
        service_type: {{ sc.service_type_id|default:"null" }},
        service_profession: {{ sc.service_profession_id|default:"null" }},
        result_list: {{ sc.result_list_ids|default:"[]"|safe }}
    }{% if not forloop.last %},{% endif %}
    {% endfor %}
];

existingServiceContents.forEach(function(content) {
    serviceContentsTableManager.addRow(content);
});
{% endif %}

// 导出到全局作用域（可选）
window.serviceContentsTableManager = serviceContentsTableManager;
```

---

### 步骤3: 删除旧的事件监听器代码

**位置**: 约第2616-2629行，查找以下代码：

```javascript
const addServiceContentBtn = document.getElementById('add-service-content-btn');
if (addServiceContentBtn) {
    addServiceContentBtn.addEventListener('click', function(e) {
        e.preventDefault();
        e.stopPropagation();
        addServiceContent();
    });
}
```

**操作**: 删除这段代码（新模块会自动处理按钮事件）

---

### 步骤4: 删除 updateServiceContentRowNumbers 函数（如果存在）

**位置**: 查找 `function updateServiceContentRowNumbers()`

**操作**: 删除整个函数（新模块会自动更新行号）

---

## ✅ 验证步骤

集成完成后，请测试以下功能：

1. **添加行功能**
   - 点击"添加服务信息"按钮
   - 应该能成功添加新行
   - 行号应该自动更新

2. **删除行功能**
   - 点击某行的"删除"按钮
   - 应该能成功删除行
   - 至少保留1行（minRows限制）

3. **服务类型过滤**
   - 选择不同的服务类型
   - 服务专业选项应该根据服务类型过滤

4. **表单提交**
   - 填写服务信息
   - 提交表单
   - 检查后端是否正确接收数据

---

## 🐛 故障排除

### 问题1: 添加按钮无反应
**解决方案**:
- 检查浏览器控制台是否有JavaScript错误
- 确认 `dynamic-table.js` 已正确引入
- 确认 `add-service-content-btn` ID存在

### 问题2: 服务专业选项不显示
**解决方案**:
- 检查 `serviceProfessionsData` 变量是否正确定义
- 检查数据格式是否正确

### 问题3: Django模板语法错误
**解决方案**:
- 确保代码在HTML模板文件中（不是外部JS文件）
- 检查模板语法是否正确

---

## 📁 相关文件

- **模块文件**: `/backend/static/js/dynamic-table.js`
- **完整集成代码**: `/backend/static/js/contract-service-integration-complete.js`
- **使用文档**: `/backend/static/js/dynamic-table.README.md`

---

## 💡 提示

- 建议在修改前先备份 `contract_form.html` 文件
- 可以使用版本控制（git）来跟踪更改
- 如果遇到问题，可以查看浏览器控制台的错误信息

