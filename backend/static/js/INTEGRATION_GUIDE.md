# 动态表格模块集成指南 - 服务信息表格

## 集成步骤

### 1. 在 contract_form.html 中引入模块

在 `{% block extra_js %}` 或 `<script>` 标签之前添加：

```html
{% block extra_js %}
<script src="{% static 'js/dynamic-table.js' %}"></script>
<script>
document.addEventListener('DOMContentLoaded', function() {
    // 服务信息表格集成代码（见下方）
});
</script>
{% endblock %}
```

### 2. 替换现有的 addServiceContent 函数

找到现有的 `function addServiceContent()` 和相关代码，替换为以下代码：

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

### 3. 删除旧的代码

删除以下旧代码：
- `function addServiceContent(serviceData = null) { ... }`
- `function updateServiceContentRowNumbers() { ... }`
- `addServiceContentBtn.addEventListener('click', ...)` 相关代码
- 旧的初始化代码

### 4. 确保数据变量存在

确保模板中有以下JavaScript变量定义（通常在script标签开始处）：

```javascript
// 服务专业数据
const serviceProfessionsData = [
    {% for sp in service_professions %}
    {
        id: {{ sp.id }},
        name: {{ sp.name|escapejs }},
        service_type_id: {{ sp.service_type_id|default:"null" }}
    }{% if not forloop.last %},{% endif %}
    {% endfor %}
];

// 成果清单数据
const resultFileTypesData = [
    {% for rft in result_file_types %}
    {
        id: {{ rft.id }},
        name: {{ rft.name|escapejs }}
    }{% if not forloop.last %},{% endif %}
    {% endfor %}
];
```

## 完整示例

查看 `contract-form-service-integration.js` 文件获取完整示例代码。

## 注意事项

1. **Django模板语法**：在模板中使用 `{% for %}` 等语法时，需要确保在 `<script>` 标签内，而不是外部JS文件中。

2. **数据格式**：确保 `serviceProfessionsData` 和 `resultFileTypesData` 的格式正确。

3. **向后兼容**：如果系统中有其他地方调用了 `addServiceContent()` 函数，需要更新为 `serviceContentsTableManager.addRow()`。

4. **测试**：集成后务必测试：
   - 添加行功能
   - 删除行功能
   - 服务类型过滤服务专业功能
   - 表单提交后数据是否正确

