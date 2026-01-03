/**
 * 合同表单 - 服务信息表格集成
 * 使用 dynamic-table.js 模块管理服务信息表格
 */

document.addEventListener('DOMContentLoaded', function() {
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

    // 检查容器是否存在
    const container = document.getElementById('service-contents-container');
    if (!container) {
        console.warn('service-contents-container 未找到，服务信息表格功能将不可用');
        return;
    }

    // 获取服务专业和成果清单数据（从后端传入的JavaScript变量）
    // 这些变量应该在模板中定义，例如：
    // const serviceProfessionsData = {{ service_professions_json|safe }};
    // const resultFileTypesData = {{ result_file_types_json|safe }};
    
    // 如果变量不存在，使用空数组
    const serviceProfessionsData = typeof serviceProfessionsData !== 'undefined' 
        ? serviceProfessionsData 
        : [];
    const resultFileTypesData = typeof resultFileTypesData !== 'undefined' 
        ? resultFileTypesData 
        : [];

    // 创建服务信息表格管理器
    const serviceContentsTableManager = new DynamicTableManager({
        containerId: 'service-contents-container',
        rowClass: 'service-content-row',
        addButtonId: 'add-service-content-btn',
        removeButtonClass: 'remove-service-content-btn',
        minRows: 1, // 至少保留1行
        rowTemplate: (index, data) => {
            const service = data || {};
            
            // 构建服务专业选项HTML
            let serviceProfessionOptions = '<option value="">-- 请选择服务专业 --</option>';
            if (Array.isArray(serviceProfessionsData)) {
                serviceProfessionsData.forEach(function(sp) {
                    const selected = service.service_profession == sp.id ? 'selected' : '';
                    serviceProfessionOptions += `<option value="${sp.id}" data-service-type="${sp.service_type_id || ''}" ${selected}>${escapeHtml(sp.name)}</option>`;
                });
            }
            
            // 构建成果清单选项HTML
            let resultListOptions = '';
            if (Array.isArray(resultFileTypesData)) {
                resultFileTypesData.forEach(function(rft) {
                    const selected = service.result_list && Array.isArray(service.result_list) && service.result_list.includes(String(rft.id))
                        ? 'selected' 
                        : '';
                    resultListOptions += `<option value="${rft.id}" ${selected}>${escapeHtml(rft.name)}</option>`;
                });
            }
            
            return `
                <td style="vertical-align: middle; text-align: center;">
                    <strong>0</strong>
                </td>
                <td>
                    <select name="service_contents[${index}][service_type]" 
                            class="form-select form-select-sm service-type-select" required>
                        <option value="">-- 请选择服务类型 --</option>
                        {% for st in service_types %}
                        <option value="{{ st.id }}" ${service.service_type == {{ st.id }} ? 'selected' : ''}>{{ st.name }}</option>
                        {% endfor %}
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
            // 添加行后，绑定服务类型变化事件，过滤服务专业
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
            // 可以在这里添加确认对话框
            return true; // 返回true允许删除
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
    if (typeof existingServiceContents !== 'undefined' && Array.isArray(existingServiceContents)) {
        existingServiceContents.forEach(function(content) {
            serviceContentsTableManager.addRow({
                service_type: content.service_type_id,
                service_profession: content.service_profession_id,
                result_list: content.result_list_ids || []
            });
        });
    }

    // 导出到全局作用域，以便在其他地方访问
    window.serviceContentsTableManager = serviceContentsTableManager;
});

