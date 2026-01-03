/**
 * 动态表格管理模块
 * 维海科技信息化管理平台
 * 版本: 1.0
 * 
 * 功能：
 * - 动态添加表格行
 * - 删除表格行
 * - 自动更新行号
 * - 支持数据验证（最少行数等）
 * - 支持自定义回调函数
 * 
 * 使用示例：
 * const tableManager = new DynamicTableManager({
 *     containerId: 'parties-container',
 *     rowClass: 'party-row',
 *     addButtonId: 'add-party-btn',
 *     removeButtonClass: 'remove-party-btn',
 *     minRows: 2,
 *     rowTemplate: (index, data) => `...`,
 *     onAdd: (row, index) => { ... },
 *     onRemove: (row, index) => { ... },
 *     onUpdateNumbers: (rows) => { ... }
 * });
 */

class DynamicTableManager {
    /**
     * 构造函数
     * @param {Object} options 配置选项
     * @param {string} options.containerId - 表格容器ID（tbody元素）
     * @param {string} options.rowClass - 行CSS类名
     * @param {string} [options.addButtonId] - 添加按钮ID
     * @param {string} [options.removeButtonClass] - 删除按钮CSS类名
     * @param {number} [options.minRows=1] - 最少保留行数
     * @param {Function} options.rowTemplate - 行模板函数 (index, data) => string
     * @param {Function} [options.onAdd] - 添加行后的回调 (row, index) => void
     * @param {Function} [options.onRemove] - 删除行前的回调 (row, index) => boolean，返回false可阻止删除
     * @param {Function} [options.onUpdateNumbers] - 更新行号时的回调 (rows) => void
     * @param {boolean} [options.autoUpdateNumbers=true] - 是否自动更新行号
     * @param {string} [options.numberCellSelector] - 行号单元格选择器（默认第一个td）
     */
    constructor(options) {
        // 必需参数验证
        if (!options.containerId) {
            throw new Error('containerId 是必需参数');
        }
        if (!options.rowTemplate || typeof options.rowTemplate !== 'function') {
            throw new Error('rowTemplate 必须是函数');
        }

        // 保存配置
        this.containerId = options.containerId;
        this.rowClass = options.rowClass || 'dynamic-table-row';
        this.addButtonId = options.addButtonId;
        this.removeButtonClass = options.removeButtonClass || 'remove-row-btn';
        this.minRows = options.minRows || 1;
        this.rowTemplate = options.rowTemplate;
        this.onAdd = options.onAdd || (() => {});
        this.onRemove = options.onRemove || (() => true);
        this.onUpdateNumbers = options.onUpdateNumbers || (() => {});
        this.autoUpdateNumbers = options.autoUpdateNumbers !== false;
        this.numberCellSelector = options.numberCellSelector || 'td:first-child';

        // 初始化索引计数器
        this.indexCounter = 0;

        // 初始化
        this.init();
    }

    /**
     * 初始化
     */
    init() {
        // 获取容器
        this.container = document.getElementById(this.containerId);
        if (!this.container) {
            console.warn(`容器 ${this.containerId} 未找到，动态表格功能可能无法正常工作`);
            return;
        }

        // 绑定添加按钮事件
        if (this.addButtonId) {
            const addButton = document.getElementById(this.addButtonId);
            if (addButton) {
                addButton.addEventListener('click', (e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    this.addRow();
                });
            } else {
                console.warn(`添加按钮 ${this.addButtonId} 未找到`);
            }
        }

        // 为现有行绑定删除按钮事件
        this.bindRemoveButtons();

        // 初始化索引计数器（基于现有行数）
        this.updateIndexCounter();

        // 更新行号
        if (this.autoUpdateNumbers) {
            this.updateRowNumbers();
        }
    }

    /**
     * 添加新行
     * @param {Object} [data={}] - 行数据
     * @returns {HTMLElement|null} 新创建的行元素
     */
    addRow(data = {}) {
        if (!this.container) {
            console.error(`容器 ${this.containerId} 未找到，无法添加行`);
            return null;
        }

        const index = this.indexCounter++;
        const row = document.createElement('tr');
        row.className = this.rowClass;
        row.setAttribute('data-row-index', index);

        // 使用模板生成行内容
        try {
            row.innerHTML = this.rowTemplate(index, data);
        } catch (error) {
            console.error('生成行模板失败:', error);
            return null;
        }

        // 添加到容器
        this.container.appendChild(row);

        // 绑定删除按钮事件
        this.bindRemoveButton(row);

        // 更新行号
        if (this.autoUpdateNumbers) {
            this.updateRowNumbers();
        }

        // 执行添加回调
        this.onAdd(row, index);

        return row;
    }

    /**
     * 删除行
     * @param {HTMLElement} row - 要删除的行元素
     * @returns {boolean} 是否成功删除
     */
    removeRow(row) {
        if (!row) {
            return false;
        }

        // 检查最少行数限制
        const currentRows = this.getRows();
        if (currentRows.length <= this.minRows) {
            alert(`至少需要保留 ${this.minRows} 行`);
            return false;
        }

        // 执行删除前回调
        const index = parseInt(row.getAttribute('data-row-index') || '0');
        if (this.onRemove(row, index) === false) {
            return false; // 回调返回false，阻止删除
        }

        // 删除行
        row.remove();

        // 更新行号
        if (this.autoUpdateNumbers) {
            this.updateRowNumbers();
        }

        return true;
    }

    /**
     * 获取所有行
     * @returns {NodeList} 所有行元素
     */
    getRows() {
        if (!this.container) {
            return [];
        }
        return this.container.querySelectorAll(`tr.${this.rowClass}`);
    }

    /**
     * 更新行号
     */
    updateRowNumbers() {
        if (!this.container) {
            return;
        }

        const rows = this.getRows();
        rows.forEach((row, idx) => {
            const numberCell = row.querySelector(this.numberCellSelector);
            if (numberCell) {
                const strong = numberCell.querySelector('strong');
                if (strong) {
                    strong.textContent = idx + 1;
                } else {
                    numberCell.textContent = idx + 1;
                }
            }
        });

        // 执行更新回调
        this.onUpdateNumbers(rows);
    }

    /**
     * 更新索引计数器
     */
    updateIndexCounter() {
        const rows = this.getRows();
        if (rows.length > 0) {
            // 找到最大的索引
            let maxIndex = -1;
            rows.forEach(row => {
                const index = parseInt(row.getAttribute('data-row-index') || '0');
                if (index > maxIndex) {
                    maxIndex = index;
                }
            });
            this.indexCounter = maxIndex + 1;
        } else {
            this.indexCounter = 0;
        }
    }

    /**
     * 为所有行绑定删除按钮事件
     */
    bindRemoveButtons() {
        if (!this.container) {
            return;
        }

        const rows = this.getRows();
        rows.forEach(row => {
            this.bindRemoveButton(row);
        });
    }

    /**
     * 为单行绑定删除按钮事件
     * @param {HTMLElement} row - 行元素
     */
    bindRemoveButton(row) {
        if (!row) {
            return;
        }

        const removeBtn = row.querySelector(`.${this.removeButtonClass}`);
        if (removeBtn) {
            // 移除旧的事件监听器（如果存在）
            const newBtn = removeBtn.cloneNode(true);
            removeBtn.parentNode.replaceChild(newBtn, removeBtn);

            // 绑定新的事件
            newBtn.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                this.removeRow(row);
            });
        }
    }

    /**
     * 清空所有行
     */
    clear() {
        if (!this.container) {
            return;
        }

        const rows = this.getRows();
        rows.forEach(row => row.remove());
        this.indexCounter = 0;
    }

    /**
     * 获取行数据
     * @param {HTMLElement} row - 行元素
     * @returns {Object} 行数据对象
     */
    getRowData(row) {
        if (!row) {
            return {};
        }

        const data = {};
        const inputs = row.querySelectorAll('input, select, textarea');
        inputs.forEach(input => {
            const name = input.getAttribute('name');
            if (name) {
                // 解析 name="parties[0][party_type]" 格式
                const match = name.match(/\[(\d+)\]\[(\w+)\]/);
                if (match) {
                    const field = match[2];
                    if (input.type === 'checkbox' || input.type === 'radio') {
                        data[field] = input.checked ? input.value : '';
                    } else {
                        data[field] = input.value;
                    }
                } else {
                    // 普通字段名
                    data[name] = input.value;
                }
            }
        });

        return data;
    }

    /**
     * 获取所有行数据
     * @returns {Array} 所有行的数据数组
     */
    getAllRowData() {
        const rows = this.getRows();
        return Array.from(rows).map(row => this.getRowData(row));
    }

    /**
     * 设置行数据
     * @param {HTMLElement} row - 行元素
     * @param {Object} data - 要设置的数据
     */
    setRowData(row, data) {
        if (!row || !data) {
            return;
        }

        Object.keys(data).forEach(field => {
            const input = row.querySelector(`[name*="[${field}]"]`);
            if (input) {
                if (input.type === 'checkbox' || input.type === 'radio') {
                    input.checked = input.value === String(data[field]);
                } else {
                    input.value = data[field] || '';
                }
            }
        });
    }
}

// 导出到全局作用域（如果使用模块系统，可以改为 export）
if (typeof module !== 'undefined' && module.exports) {
    module.exports = DynamicTableManager;
}

