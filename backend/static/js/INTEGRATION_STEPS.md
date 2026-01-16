# 服务信息表格模块集成步骤

## 前提条件

确保以下文件存在：
- ✅ `/backend/static/js/dynamic-table.js` - 动态表格模块
- ✅ 服务信息表格HTML结构（包含 `service-contents-container` 和 `add-service-content-btn`）

## 集成步骤

### 步骤1: 在模板中引入 dynamic-table.js

在 `contract_form.html` 的 `{% block extra_js %}` 或 `<script>` 标签开始处添加：

```html
{% block extra_js %}
<script src="{% static 'js/dynamic-table.js' %}"></script>
<script>
document.addEventListener('DOMContentLoaded', function() {
    // 步骤2的代码将放在这里
});
</script>
{% endblock %}
```

如果没有 `{% block extra_js %}`，可以在 `</form>` 标签之后、`{% endblock %}` 之前添加：

```html
</form>

<script src="{% static 'js/dynamic-table.js' %}"></script>
<script>
document.addEventListener('DOMContentLoaded', function() {
    // 步骤2的代码将放在这里
});
</script>

{% endblock %}
```

### 步骤2: 添加服务信息表格管理代码

在 `DOMContentLoaded` 事件处理器中，找到现有的 `function addServiceContent()` 函数位置，用以下代码替换：

**完整代码见：`contract-service-integration-complete.js`**

或者直接复制以下代码（包含Django模板语法，必须在HTML模板中使用）：

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
                const currentValue = serviceProfessionSelect.value;
                if (currentValue) {
                    const currentOption = serviceProfessionSelect.querySelector(`option[value="${currentValue}"]`);
                    if (currentOption && currentOption.style.display === 'none') {
                        serviceProfessionSelect.value = '';
                    }
                }
            }
            filterServiceProfessions();
            serviceTypeSelect.addEventListener('change', filterServiceProfessions);
        }
    },
    onRemove: (row, index) => {
        return true;
    },
    onUpdateNumbers: (rows) => {
        console.log(`当前共有 ${rows.length} 行服务信息`);
    }
});

// 初始化
if (serviceContentsTableManager.getRows().length === 0) {
    serviceContentsTableManager.addRow();
}

// 编辑模式数据初始化
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

window.serviceContentsTableManager = serviceContentsTableManager;
```

### 步骤3: 删除旧代码

删除以下旧代码：
- `function addServiceContent(serviceData = null) { ... }`
- `function updateServiceContentRowNumbers() { ... }`
- `addServiceContentBtn.addEventListener('click', ...)` 相关代码
- `let serviceContentIndex = 0;` 的旧定义（如果存在）

### 步骤4: 确保数据变量存在

确保模板中有以下JavaScript变量定义（通常在script标签开始处，DOMContentLoaded之前）：

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

## 测试清单

集成完成后，请测试以下功能：

- [ ] 点击"添加服务信息"按钮，能够添加新行
- [ ] 点击"删除"按钮，能够删除行（至少保留1行）
- [ ] 行号自动更新
- [ ] 选择服务类型后，服务专业选项正确过滤
- [ ] 成果清单可以多选
- [ ] 表单提交后，数据正确保存
- [ ] 编辑模式下，已有数据正确加载

## 故障排除

### 问题1: 添加按钮无反应
- 检查是否引入了 `dynamic-table.js`
- 检查浏览器控制台是否有JavaScript错误
- 检查 `add-service-content-btn` ID是否正确

### 问题2: 服务专业选项不显示
- 检查 `serviceProfessionsData` 变量是否正确定义
- 检查数据格式是否正确

### 问题3: Django模板语法错误
- 确保代码在HTML模板文件中，而不是外部JS文件
- 检查模板语法是否正确（注意 `{% %}` 和 `{{ }}` 的使用）

## 文件位置

- 模块文件: `/backend/static/js/dynamic-table.js`
- 完整集成代码: `/backend/static/js/contract-service-integration-complete.js`
- 使用文档: `/backend/static/js/dynamic-table.README.md`

