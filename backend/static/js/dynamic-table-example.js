/**
 * 动态表格模块使用示例
 * 展示如何在合同表单中使用 dynamic-table.js
 */

document.addEventListener('DOMContentLoaded', function() {
    // ========== 1. 签约主体表格 ==========
    
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

    // 创建签约主体表格管理器
    const partiesTableManager = new DynamicTableManager({
        containerId: 'parties-container',
        rowClass: 'party-row',
        addButtonId: 'add-party-btn',
        removeButtonClass: 'remove-party-btn',
        minRows: 2, // 至少保留2行（甲方和乙方）
        rowTemplate: (index, data) => {
            const party = data || {};
            return `
                <td style="vertical-align: middle; text-align: center;">
                    <strong>0</strong>
                </td>
                <td>
                    <select name="parties[${index}][party_type]" class="form-select form-select-sm" required>
                        <option value="party_a" ${party.party_type === 'party_a' ? 'selected' : ''}>甲方</option>
                        <option value="party_b" ${party.party_type === 'party_b' ? 'selected' : ''}>乙方</option>
                        <option value="party_c" ${party.party_type === 'party_c' ? 'selected' : ''}>丙方</option>
                        <option value="other" ${party.party_type === 'other' ? 'selected' : ''}>其他</option>
                    </select>
                </td>
                <td>
                    <input type="text" name="parties[${index}][party_name]" 
                           class="form-control form-control-sm"
                           value="${escapeHtml(party.party_name || '')}" 
                           placeholder="请输入单位名称" required>
                </td>
                <td>
                    <input type="text" name="parties[${index}][credit_code]" 
                           class="form-control form-control-sm"
                           value="${escapeHtml(party.credit_code || '')}" 
                           placeholder="请输入统一社会信用代码">
                </td>
                <td>
                    <input type="text" name="parties[${index}][legal_representative]" 
                           class="form-control form-control-sm"
                           value="${escapeHtml(party.legal_representative || '')}" 
                           placeholder="请输入法定代表人">
                </td>
                <td>
                    <input type="text" name="parties[${index}][project_manager]" 
                           class="form-control form-control-sm"
                           value="${escapeHtml(party.project_manager || '')}" 
                           placeholder="请输入项目负责人">
                </td>
                <td>
                    <input type="text" name="parties[${index}][contact_phone]" 
                           class="form-control form-control-sm"
                           value="${escapeHtml(party.contact_phone || '')}" 
                           placeholder="请输入联系电话">
                </td>
                <td>
                    <input type="email" name="parties[${index}][contact_email]" 
                           class="form-control form-control-sm"
                           value="${escapeHtml(party.contact_email || '')}" 
                           placeholder="请输入联系邮箱">
                </td>
                <td>
                    <input type="text" name="parties[${index}][address]" 
                           class="form-control form-control-sm"
                           value="${escapeHtml(party.address || '')}" 
                           placeholder="请输入办公地址">
                </td>
                <td style="vertical-align: middle; text-align: center;">
                    <button type="button" class="btn btn-sm btn-danger remove-party-btn" 
                            data-index="${index}" title="删除">
                        <i class="bi bi-trash"></i>
                    </button>
                </td>
            `;
        },
        onAdd: (row, index) => {
            console.log(`添加了签约主体行 ${index}`);
            // 可以在这里执行其他初始化操作
        },
        onRemove: (row, index) => {
            // 可以在这里添加确认对话框
            return true; // 返回true允许删除，false阻止删除
        }
    });

    // 初始化：确保至少有两行（甲方和乙方）
    if (partiesTableManager.getRows().length === 0) {
        partiesTableManager.addRow({ party_type: 'party_a' });
        partiesTableManager.addRow({ party_type: 'party_b' });
    }

    // ========== 2. 服务信息表格 ==========
    
    // 服务信息表格管理器
    const serviceContentsTableManager = new DynamicTableManager({
        containerId: 'service-contents-container',
        rowClass: 'service-content-row',
        addButtonId: 'add-service-content-btn',
        removeButtonClass: 'remove-service-content-btn',
        minRows: 1,
        rowTemplate: (index, data) => {
            const content = data || {};
            
            // 生成服务类型选项（需要从后端传入 serviceTypeOptions）
            let serviceTypeOptionsHtml = '<option value="">请选择</option>';
            if (typeof serviceTypeOptions !== 'undefined' && Array.isArray(serviceTypeOptions)) {
                serviceTypeOptions.forEach(opt => {
                    const selected = content.service_type == opt.value ? 'selected' : '';
                    serviceTypeOptionsHtml += `<option value="${opt.value}" ${selected}>${escapeHtml(opt.label)}</option>`;
                });
            }
            
            // 生成设计阶段选项（需要从后端传入 designStageOptions）
            let designStageOptionsHtml = '<option value="">请选择</option>';
            if (typeof designStageOptions !== 'undefined' && Array.isArray(designStageOptions)) {
                designStageOptions.forEach(opt => {
                    const selected = content.design_stage == opt.value ? 'selected' : '';
                    designStageOptionsHtml += `<option value="${opt.value}" ${selected}>${escapeHtml(opt.label)}</option>`;
                });
            }
            
            return `
                <td style="vertical-align: middle; text-align: center;">
                    <strong>0</strong>
                </td>
                <td>
                    <select name="service_contents[${index}][service_type]" 
                            class="form-select form-select-sm service-type-select" required>
                        ${serviceTypeOptionsHtml}
                    </select>
                </td>
                <td>
                    <select name="service_contents[${index}][design_stage]" 
                            class="form-select form-select-sm design-stage-select">
                        ${designStageOptionsHtml}
                    </select>
                </td>
                <td>
                    <textarea name="service_contents[${index}][description]" 
                              class="form-control form-control-sm" 
                              rows="2"
                              placeholder="请输入服务描述">${escapeHtml(content.description || '')}</textarea>
                </td>
                <td style="vertical-align: middle; text-align: center;">
                    <button type="button" class="btn btn-sm btn-danger remove-service-content-btn" 
                            title="删除">
                        <i class="bi bi-trash"></i>
                    </button>
                </td>
            `;
        },
        onAdd: (row, index) => {
            // 添加行后，可以初始化下拉选项或绑定其他事件
            console.log(`添加了服务信息行 ${index}`);
            
            // 如果服务类型改变，可以动态更新其他字段
            const serviceTypeSelect = row.querySelector('.service-type-select');
            if (serviceTypeSelect) {
                serviceTypeSelect.addEventListener('change', function() {
                    // 根据服务类型更新其他选项
                    console.log('服务类型已更改:', this.value);
                });
            }
        }
    });

    // 初始化：确保至少有一行
    if (serviceContentsTableManager.getRows().length === 0) {
        serviceContentsTableManager.addRow();
    }

    // ========== 3. 回款信息表格 ==========
    
    // 回款信息表格管理器
    const paymentInfoTableManager = new DynamicTableManager({
        containerId: 'payment-info-container',
        rowClass: 'payment-info-row',
        addButtonId: 'add-payment-info-btn',
        removeButtonClass: 'remove-payment-info-btn',
        minRows: 1,
        rowTemplate: (index, data) => {
            const payment = data || {};
            return `
                <td style="text-align: center;">
                    <strong>0</strong>
                </td>
                <td>
                    <input type="text" name="payment_info[${index}][payment_name]" 
                           class="form-control form-control-sm"
                           value="${escapeHtml(payment.payment_name || '')}" 
                           placeholder="回款名称" required>
                </td>
                <td>
                    <input type="number" name="payment_info[${index}][amount]" 
                           class="form-control form-control-sm payment-amount"
                           value="${payment.amount || ''}" 
                           step="0.01"
                           placeholder="0.00" required>
                </td>
                <td>
                    <input type="date" name="payment_info[${index}][payment_date]" 
                           class="form-control form-control-sm"
                           value="${payment.payment_date || ''}">
                </td>
                <td>
                    <button type="button" class="btn btn-sm btn-danger remove-payment-info-btn">
                        <i class="bi bi-trash"></i>
                    </button>
                </td>
            `;
        },
        onAdd: (row, index) => {
            // 绑定金额输入事件，可以自动计算总额
            const amountInput = row.querySelector('.payment-amount');
            if (amountInput) {
                amountInput.addEventListener('input', function() {
                    calculateTotalPayment(); // 自定义函数
                });
            }
        },
        onUpdateNumbers: (rows) => {
            // 更新行号时，重新计算总额
            if (typeof calculateTotalPayment === 'function') {
                calculateTotalPayment();
            }
        }
    });

    // 初始化：确保至少有一行
    if (paymentInfoTableManager.getRows().length === 0) {
        paymentInfoTableManager.addRow();
    }

    // ========== 4. 使用示例：获取所有数据 ==========
    
    // 在表单提交前，可以获取所有行的数据
    const contractForm = document.getElementById('contract-form');
    if (contractForm) {
        contractForm.addEventListener('submit', function(e) {
            // 获取所有签约主体数据
            const partiesData = partiesTableManager.getAllRowData();
            console.log('签约主体数据:', partiesData);
            
            // 获取所有服务信息数据
            const serviceContentsData = serviceContentsTableManager.getAllRowData();
            console.log('服务信息数据:', serviceContentsData);
            
            // 获取所有回款信息数据
            const paymentInfoData = paymentInfoTableManager.getAllRowData();
            console.log('回款信息数据:', paymentInfoData);
            
            // 可以在这里进行数据验证
            // 如果验证失败，可以调用 e.preventDefault() 阻止提交
        });
    }

    // ========== 5. 使用示例：从后端数据初始化 ==========
    
    // 如果是从后端加载的数据（编辑模式），可以这样初始化
    if (typeof existingParties !== 'undefined' && Array.isArray(existingParties)) {
        existingParties.forEach(party => {
            partiesTableManager.addRow(party);
        });
    }

    if (typeof existingServiceContents !== 'undefined' && Array.isArray(existingServiceContents)) {
        existingServiceContents.forEach(content => {
            serviceContentsTableManager.addRow(content);
        });
    }

    // ========== 6. 导出到全局作用域（可选） ==========
    // 如果需要在其他地方访问这些管理器
    window.partiesTableManager = partiesTableManager;
    window.serviceContentsTableManager = serviceContentsTableManager;
    window.paymentInfoTableManager = paymentInfoTableManager;
});

