/**
 * 筛选字段设置功能模块
 * 提供可复用的筛选字段设置功能，包括：
 * - 筛选字段的启用/禁用
 * - 筛选字段的拖拽排序
 * - 筛选字段设置的保存和重置
 * 
 * 使用方法：
 * 1. 在HTML中包含模态框模板（filter_fields_settings_modal.html）
 * 2. 引入此JS文件
 * 3. 调用 FilterFieldsSettings.init(options) 初始化
 * 
 * 配置选项：
 * - storageKey: localStorage存储键名（默认：'filter_fields_settings'）
 * - containerId: 筛选条件容器ID（默认：'basicFilters'）
 * - modalId: 模态框ID（默认：'filterFieldsSettingsModal'）
 * - maxEnabledFields: 最多启用的字段数（默认：10）
 * - defaultEnabledFields: 默认启用的字段key数组
 */

(function(window) {
    'use strict';

    // 默认配置
    const DEFAULT_CONFIG = {
        storageKey: 'filter_fields_settings',
        containerId: 'basicFilters',
        modalId: 'filterFieldsSettingsModal',
        listId: 'filterFieldsList',
        settingsBtnId: 'settingsFilterFieldsBtn',
        saveBtnId: 'saveFilterFieldsSettings',
        resetBtnId: 'resetFilterFieldsSettings',
        maxEnabledFields: 10,
        defaultEnabledFields: [],
        requiredFields: [] // 必填字段（不可取消）
    };

    // 筛选字段设置类
    class FilterFieldsSettings {
        constructor(config = {}) {
            // 验证和清理配置参数
            this.config = this.validateConfig({ ...DEFAULT_CONFIG, ...config });
            this.filterFields = [];
            this.draggedRow = null;
            this.eventListeners = []; // 用于跟踪事件监听器，便于清理
            this.isApplyingSettings = false; // 标志：是否正在应用设置，防止循环更新
            this.modalInstance = null; // Bootstrap Modal 实例引用
            
            // 绑定方法上下文
            this.handleDragStart = this.handleDragStart.bind(this);
            this.handleDragOver = this.handleDragOver.bind(this);
            this.handleDrop = this.handleDrop.bind(this);
            this.handleDragEnd = this.handleDragEnd.bind(this);
        }

        /**
         * 验证ID格式（只允许字母、数字、连字符、下划线）
         */
        isValidId(id) {
            if (typeof id !== 'string' || id.length === 0 || id.length > 100) {
                return false;
            }
            // 只允许字母、数字、连字符、下划线
            return /^[a-zA-Z0-9_-]+$/.test(id);
        }

        /**
         * 验证和清理ID字符串
         */
        sanitizeId(id) {
            if (typeof id !== 'string') {
                return '';
            }
            // 只保留字母、数字、连字符、下划线
            return id.replace(/[^a-zA-Z0-9_-]/g, '');
        }

        /**
         * 验证配置参数
         */
        validateConfig(config) {
            // 验证字符串参数，防止XSS
            const stringFields = ['storageKey', 'containerId', 'modalId', 'listId', 
                                 'settingsBtnId', 'saveBtnId', 'resetBtnId'];
            stringFields.forEach(field => {
                if (config[field] && typeof config[field] !== 'string') {
                    config[field] = DEFAULT_CONFIG[field];
                }
                // ID类型的字段需要更严格的验证
                if (config[field] && typeof config[field] === 'string') {
                    if (field.endsWith('Id') || field === 'containerId') {
                        // ID类型字段：验证格式并清理
                        if (!this.isValidId(config[field])) {
                            const sanitized = this.sanitizeId(config[field]);
                            config[field] = sanitized || DEFAULT_CONFIG[field];
                        }
                    } else {
                        // 其他字符串字段：移除潜在的恶意字符
                        config[field] = config[field].replace(/[<>\"']/g, '');
                    }
                }
            });

            // 验证数字参数
            if (config.maxEnabledFields && (typeof config.maxEnabledFields !== 'number' || config.maxEnabledFields < 1)) {
                config.maxEnabledFields = DEFAULT_CONFIG.maxEnabledFields;
            }

            // 验证数组参数
            if (config.defaultEnabledFields && !Array.isArray(config.defaultEnabledFields)) {
                config.defaultEnabledFields = DEFAULT_CONFIG.defaultEnabledFields;
            }

            return config;
        }

        /**
         * 初始化筛选字段设置功能
         */
        init() {
            // 【修复1】确保模态框在 body 的直接子元素中（Bootstrap 5 要求）
            this.ensureModalInBody();
            
            // 初始化筛选字段列表
            this.initFilterFieldsList();
            
            // 设置事件监听器
            this.setupEventListeners();
            
            // 应用已保存的设置
            this.applySettings();
            
            // 确保设置按钮位置固定在右上角
            this.fixSettingsButtonPosition();
            
            // 启动DOM变化监听
            this.startMutationObserver();
        }
        
        /**
         * 确保模态框在 body 的直接子元素中
         * Bootstrap 5 要求模态框必须是 body 的直接子元素
         */
        ensureModalInBody() {
            const modalElement = document.getElementById(this.config.modalId);
            if (!modalElement) {
                return;
            }
            
            // 检查模态框是否在 body 的直接子元素中
            if (modalElement.parentElement !== document.body) {
                // 【修复】保存模态框的显示状态（是否已打开）
                const wasShown = modalElement.classList.contains('show');
                
                // 移动到 body
                document.body.appendChild(modalElement);
                
                // 【修复】确保模态框在移动后处于正确的隐藏状态
                // 如果模态框原本没有打开，确保它现在是隐藏的
                if (!wasShown) {
                    // 移除 show 类（如果有）
                    modalElement.classList.remove('show');
                    // 确保 aria-hidden="true"
                    modalElement.setAttribute('aria-hidden', 'true');
                    // 移除内联 display 样式，让 CSS 控制（Bootstrap 默认隐藏）
                    modalElement.style.removeProperty('display');
                    // 确保没有 backdrop
                    const backdrop = document.querySelector('.modal-backdrop');
                    if (backdrop && backdrop.parentElement === document.body) {
                        backdrop.remove();
                    }
                    // 移除 body 的 modal-open 类
                    document.body.classList.remove('modal-open');
                    // 移除 body 的 padding-right（Bootstrap 添加的）
                    document.body.style.removeProperty('padding-right');
                }
            } else {
                // 【修复】即使模态框已经在 body 下，也要确保它处于正确的隐藏状态（如果未打开）
                if (!modalElement.classList.contains('show')) {
                    modalElement.setAttribute('aria-hidden', 'true');
                    modalElement.style.removeProperty('display');
                }
            }
        }
        
        /**
         * 启动MutationObserver监听DOM变化（可选功能）
         */
        startMutationObserver() {
            if (typeof MutationObserver === 'undefined') return;
            
            const container = document.getElementById(this.config.containerId);
            if (!container) return;
            
            let debounceTimer = null;
            this.mutationObserver = new MutationObserver(() => {
                if (this.isApplyingSettings) return;
                clearTimeout(debounceTimer);
                debounceTimer = setTimeout(() => {
                    if (!this.isApplyingSettings) {
                        this.initFilterFieldsList();
                        this.applySettings();
                    }
                }, 300);
            });
            
            this.mutationObserver.observe(container, {
                childList: true,
                subtree: true,
                attributes: true,
                attributeFilter: ['data-filter-key', 'class']
            });
        }
        
        /**
         * 固定设置按钮位置在筛选容器右上角
         */
        fixSettingsButtonPosition() {
            const settingsBtn = document.getElementById(this.config.settingsBtnId);
            const container = document.getElementById(this.config.containerId);
            
            if (settingsBtn && container) {
                // 确保容器有相对定位
                const filterContainer = container.closest('.list-page-filters');
                if (filterContainer) {
                    // 强制设置position: relative
                    filterContainer.style.setProperty('position', 'relative', 'important');
                }
                
                // 强制设置按钮的绝对定位和位置
                settingsBtn.style.setProperty('position', 'absolute', 'important');
                settingsBtn.style.setProperty('top', '8px', 'important');
                settingsBtn.style.setProperty('right', '8px', 'important');
                settingsBtn.style.setProperty('z-index', '101', 'important'); // 高于操作栏的z-index:100
                settingsBtn.style.setProperty('margin', '0', 'important');
                settingsBtn.style.setProperty('padding', '4px 8px', 'important');
                settingsBtn.style.setProperty('pointer-events', 'auto', 'important'); // 确保可点击
                settingsBtn.style.setProperty('cursor', 'pointer', 'important');
                
                // 显示按钮（移除初始隐藏状态）
                settingsBtn.style.setProperty('opacity', '1', 'important');
                settingsBtn.style.setProperty('visibility', 'visible', 'important');
            }
        }

        /**
         * 从HTML中自动发现所有筛选字段
         * 支持两种格式：
         * 1. .filter-row[data-filter-key] - 新格式
         * 2. .list-page-filter-item 包含 select/input[name] - 旧格式
         */
        initializeFilterFields() {
            const container = document.getElementById(this.config.containerId);
            if (!container) {
                return [];
            }

            const fields = [];
            const processedKeys = new Set(); // 防止重复

            // 方式1: 查找新格式的筛选字段 (.filter-row[data-filter-key])
            const filterRows = container.querySelectorAll('.filter-row[data-filter-key]');
            filterRows.forEach(row => {
                const rawKey = row.getAttribute('data-filter-key');
                if (rawKey && !processedKeys.has(rawKey)) {
                    const safeKey = this.sanitizeId(String(rawKey).trim());
                    if (!safeKey) {
                        return;
                    }
                    processedKeys.add(safeKey);

                    // 从label中提取字段名称
                    const labelElement = row.querySelector('.filter-label');
                    let label = safeKey;
                    if (labelElement) {
                        label = labelElement.textContent.replace(/[:：]/g, '').trim();
                    }

                    const enabled = this.config.defaultEnabledFields && this.config.defaultEnabledFields.length > 0
                        ? this.config.defaultEnabledFields.includes(safeKey)
                        : true;

                    fields.push({
                        key: safeKey,
                        label: label || safeKey,
                        enabled: enabled
                    });
                }
            });

            // 方式2: 查找旧格式的筛选字段 (.list-page-filter-item)
            const filterItems = container.querySelectorAll('.list-page-filter-item');
            filterItems.forEach(item => {
                // 尝试从 select 或 input 元素获取 name 属性
                const selectElement = item.querySelector('select[name], input[name]');
                if (selectElement) {
                    const rawKey = selectElement.getAttribute('name');
                    if (rawKey && !processedKeys.has(rawKey)) {
                        const safeKey = this.sanitizeId(String(rawKey).trim());
                        if (!safeKey) {
                            return;
                        }
                        processedKeys.add(safeKey);

                        // 从 label 元素中提取字段名称
                        const labelElement = item.querySelector('label');
                        let label = safeKey;
                        if (labelElement) {
                            label = labelElement.textContent.replace(/[:：]/g, '').trim();
                        }

                        const enabled = this.config.defaultEnabledFields && this.config.defaultEnabledFields.length > 0
                            ? this.config.defaultEnabledFields.includes(safeKey)
                            : true;

                        fields.push({
                            key: safeKey,
                            label: label || safeKey,
                            enabled: enabled
                        });
                    }
                }
            });

            return fields;
        }

        /**
         * 初始化筛选字段列表
         */
        initFilterFieldsList() {
            const fields = this.initializeFilterFields();
            
            if (fields.length === 0) {
                // 即使没有字段，也要初始化空数组，避免后续错误
                this.filterFields = [];
                return;
            }

            // 从localStorage加载已保存的设置
            const saved = localStorage.getItem(this.config.storageKey);
            let savedFields = [];

            if (saved) {
                try {
                    // 验证JSON数据，防止注入攻击
                    const parsed = JSON.parse(saved);
                    // 验证解析后的数据结构
                    if (Array.isArray(parsed)) {
                        // 验证每个字段的结构，并清理key确保安全
                        savedFields = parsed.filter(item => {
                            if (!item || typeof item !== 'object' || typeof item.key !== 'string') {
                                return false;
                            }
                            // 验证和清理key
                            const safeKey = this.sanitizeId(item.key.trim());
                            if (!safeKey || safeKey.length === 0 || safeKey.length >= 100) {
                                return false;
                            }
                            // 如果key被清理过，更新为清理后的值
                            if (safeKey !== item.key) {
                                item.key = safeKey;
                            }
                            return true;
                        });
                    }
                } catch (e) {
                    // 如果解析失败，清除损坏的数据
                    try {
                        localStorage.removeItem(this.config.storageKey);
                    } catch (clearError) {
                    }
                }
            }

            // 合并保存的设置和当前字段
            // 如果没有保存的设置，使用字段的默认启用状态（由initializeFilterFields决定）
            if (savedFields.length === 0) {
                // 没有保存的设置，使用字段的默认启用状态
                // initializeFilterFields已经根据defaultEnabledFields设置了enabled状态
                this.filterFields = fields.map(field => {
                    const isRequired = this.config.requiredFields && this.config.requiredFields.includes(field.key);
                    // 必填字段必须启用
                    return {
                        ...field,
                        enabled: isRequired ? true : field.enabled, // 必填字段强制启用，其他字段使用默认值
                        required: isRequired
                    };
                });
            } else {
                // 有保存的设置，使用保存的设置
                this.filterFields = fields.map(field => {
                    const saved = savedFields.find(sf => sf.key === field.key);
                    const isRequired = this.config.requiredFields && this.config.requiredFields.includes(field.key);
                    if (saved) {
                        // 如果是必填字段，强制启用
                        return { 
                            ...field, 
                            ...saved, 
                            enabled: isRequired ? true : saved.enabled,
                            required: isRequired
                        };
                    }
                    // 如果没有保存的设置，使用字段的默认启用状态
                    return { 
                        ...field, 
                        enabled: isRequired ? true : field.enabled, // 必填字段强制启用，其他字段使用默认值
                        required: isRequired 
                    };
                });

                // 添加新字段（如果HTML中有新字段但保存的设置中没有）
                const existingKeys = new Set(this.filterFields.map(f => f.key));
                fields.forEach(field => {
                    if (!existingKeys.has(field.key)) {
                        const isRequired = this.config.requiredFields && this.config.requiredFields.includes(field.key);
                        // 新字段使用默认启用状态（由initializeFilterFields决定）
                        this.filterFields.push({ 
                            ...field, 
                            enabled: isRequired ? true : field.enabled, // 必填字段强制启用，其他字段使用默认值
                            required: isRequired
                        });
                    }
                });
            }
            
            // 对字段进行排序：必填字段在前，按配置顺序
            this.sortFilterFields();
        }

        /**
         * 对筛选字段进行排序：必填字段在前，按配置顺序
         */
        sortFilterFields() {
            if (!this.config.requiredFields || this.config.requiredFields.length === 0) {
                return;
            }
            
            // 分离必填字段和其他字段
            const requiredFields = [];
            const otherFields = [];
            
            this.filterFields.forEach(field => {
                const index = this.config.requiredFields.indexOf(field.key);
                if (index >= 0) {
                    requiredFields.push({ field, index });
                } else {
                    otherFields.push(field);
                }
            });
            
            // 按配置顺序排序必填字段
            requiredFields.sort((a, b) => a.index - b.index);
            
            // 重新组合：必填字段在前，其他字段在后
            this.filterFields = [
                ...requiredFields.map(item => item.field),
                ...otherFields
            ];
        }

        /**
         * 渲染筛选字段列表到模态框
         */
        renderFilterFieldsList() {
            const tbody = document.getElementById(this.config.listId);
            if (!tbody) {
                return;
            }

            tbody.textContent = '';

            this.filterFields.forEach((field) => {
                if (!field || !field.key) {
                    return;
                }

                // field.key已经在initializeFilterFields中验证和清理过，这里再次验证确保安全
                const safeKey = String(field.key || '').trim();
                if (!safeKey || safeKey.length === 0 || safeKey.length > 100 || !this.isValidId(safeKey)) {
                    return;
                }

                const row = document.createElement('tr');
                row.dataset.fieldKey = safeKey; // 使用已验证的key
                row.draggable = true;
                row.style.cursor = 'move';
                row.classList.add('filter-field-row');

                // 安全地构建HTML，确保所有用户输入都经过转义
                const fieldKey = this.escapeHtml(safeKey);
                const fieldLabel = this.escapeHtml(field.label || safeKey || '');
                const checkedAttr = field.enabled ? 'checked' : '';
                const isRequired = field.required || (this.config.requiredFields && this.config.requiredFields.includes(safeKey));
                const disabledAttr = isRequired ? 'disabled' : '';
                const requiredText = isRequired ? '<span class="text-danger ms-1">*</span>' : '';
                
                // 使用清理后的safeKey构建ID属性
                const checkboxId = `filter-field-${safeKey}`;
                row.innerHTML = `
                    <td>
                        <div class="form-check">
                            <input class="form-check-input filter-field-checkbox" type="checkbox" 
                                   id="${this.escapeHtml(checkboxId)}" 
                                   ${checkedAttr}
                                   ${disabledAttr}
                                   data-required="${isRequired ? 'true' : 'false'}">
                        </div>
                    </td>
                    <td>
                        <label class="form-check-label" for="${this.escapeHtml(checkboxId)}" style="cursor: ${isRequired ? 'not-allowed' : 'pointer'};">
                            ${fieldLabel}${requiredText}
                        </label>
                    </td>
                    <td>
                        <i class="bi bi-grip-vertical text-muted" style="font-size: 1.2em; cursor: ${isRequired ? 'not-allowed' : 'move'};"></i>
                    </td>
                `;
                
                // 如果是必填字段，禁用拖动
                if (isRequired) {
                    row.draggable = false;
                    row.style.cursor = 'default';
                }

                // 绑定拖动事件（记录以便后续清理）
                row.addEventListener('dragstart', this.handleDragStart);
                this.eventListeners.push({ element: row, event: 'dragstart', handler: this.handleDragStart });
                row.addEventListener('dragover', this.handleDragOver);
                this.eventListeners.push({ element: row, event: 'dragover', handler: this.handleDragOver });
                row.addEventListener('drop', this.handleDrop);
                this.eventListeners.push({ element: row, event: 'drop', handler: this.handleDrop });
                row.addEventListener('dragend', this.handleDragEnd);
                this.eventListeners.push({ element: row, event: 'dragend', handler: this.handleDragEnd });

                // 绑定复选框变化事件（记录以便后续清理）
                const checkbox = row.querySelector('.filter-field-checkbox');
                if (checkbox) {
                    const changeHandler = (e) => {
                        this.updateFieldEnabled(field.key, e.target.checked);
                    };
                    checkbox.addEventListener('change', changeHandler);
                    this.eventListeners.push({ element: checkbox, event: 'change', handler: changeHandler });
                }

                tbody.appendChild(row);
            });
            
            // 更新计数和空状态
            this.updateSelectedCount();
            this.updateMaxFieldsCount();
            
            // 检查是否有字段
            const emptyState = document.getElementById('filterFieldsEmpty');
            if (emptyState && tbody) {
                // 如果字段列表为空，或者表格中没有可见的行，显示空状态
                const visibleRows = tbody.querySelectorAll('tr.filter-field-row:not(.filtered-out)');
                if (this.filterFields.length === 0 || visibleRows.length === 0) {
                    emptyState.classList.remove('d-none');
                    // 如果是因为搜索导致没有可见行，显示不同的提示
                    if (this.filterFields.length > 0 && visibleRows.length === 0) {
                        const searchInput = document.getElementById('filterFieldsSearchInput');
                        if (searchInput && searchInput.value.trim()) {
                            emptyState.querySelector('p').textContent = `未找到包含"${searchInput.value.trim()}"的字段`;
                        }
                    } else if (this.filterFields.length === 0) {
                        emptyState.querySelector('p').textContent = '暂无筛选字段，请确保页面中包含带有 data-filter-key 属性的筛选行';
                    }
                } else {
                    emptyState.classList.add('d-none');
                }
            }
        }

        /**
         * 更新字段启用状态
         */
        updateFieldEnabled(fieldKey, enabled) {
            const field = this.filterFields.find(f => f.key === fieldKey);
            if (!field) {
                return;
            }

            // 检查是否为必填字段
            const isRequired = field.required || (this.config.requiredFields && this.config.requiredFields.includes(fieldKey));
            if (isRequired && !enabled) {
                alert('此字段为必填字段，不能取消！');
                // 使用清理后的key构建安全的ID选择器
                const safeKey = this.sanitizeId(String(fieldKey || ''));
                if (safeKey) {
                    const checkbox = document.getElementById(`filter-field-${safeKey}`);
                    if (checkbox) {
                        checkbox.checked = true;
                    }
                }
                return;
            }

            // 检查是否超过最大启用数量
            const enabledCount = this.filterFields.filter(f => f.enabled).length;
            if (enabled && enabledCount >= this.config.maxEnabledFields) {
                alert(`最多只能启用${this.config.maxEnabledFields}个筛选字段！`);
                // 使用清理后的key构建安全的ID选择器
                const safeKey = this.sanitizeId(String(fieldKey || ''));
                if (safeKey) {
                    const checkbox = document.getElementById(`filter-field-${safeKey}`);
                    if (checkbox) {
                        checkbox.checked = false;
                    }
                }
                return;
            }

            field.enabled = enabled;
            this.saveSettings();
            this.applySettings();
            this.updateSelectedCount();
        }

        /**
         * 全选所有字段
         */
        selectAllFields() {
            const enabledCount = this.filterFields.filter(f => f.enabled).length;
            const maxFields = this.config.maxEnabledFields || 10;
            
            // 如果已选数量已达到最大值，提示用户
            if (enabledCount >= maxFields) {
                const availableSlots = maxFields - enabledCount;
                if (availableSlots <= 0) {
                    alert(`最多只能启用 ${maxFields} 个筛选字段！`);
                    return;
                }
            }
            
            // 计算可以启用的字段数量
            let remainingSlots = maxFields - enabledCount;
            
            this.filterFields.forEach(field => {
                const isRequired = field.required || (this.config.requiredFields && this.config.requiredFields.includes(field.key));
                
                // 如果字段未启用且还有剩余位置
                if (!field.enabled && remainingSlots > 0 && !isRequired) {
                    field.enabled = true;
                    remainingSlots--;
                }
            });
            
            this.renderFilterFieldsList();
            this.saveSettings();
            this.applySettings();
            this.updateSelectedCount();
        }

        /**
         * 反选所有字段（必填字段不受影响）
         */
        invertFieldsSelection() {
            this.filterFields.forEach(field => {
                const isRequired = field.required || (this.config.requiredFields && this.config.requiredFields.includes(field.key));
                
                // 必填字段不能取消
                if (!isRequired) {
                    field.enabled = !field.enabled;
                }
            });
            
            // 检查是否超过最大数量
            const enabledCount = this.filterFields.filter(f => f.enabled).length;
            const maxFields = this.config.maxEnabledFields || 10;
            
            if (enabledCount > maxFields) {
                // 如果超过最大值，需要取消一些字段
                let toDisable = enabledCount - maxFields;
                this.filterFields.forEach(field => {
                    const isRequired = field.required || (this.config.requiredFields && this.config.requiredFields.includes(field.key));
                    if (field.enabled && !isRequired && toDisable > 0) {
                        field.enabled = false;
                        toDisable--;
                    }
                });
                alert(`最多只能启用 ${maxFields} 个筛选字段，已自动取消部分选择！`);
            }
            
            this.renderFilterFieldsList();
            this.saveSettings();
            this.applySettings();
            this.updateSelectedCount();
        }

        /**
         * 根据搜索关键词过滤字段列表
         */
        filterFieldsList(searchTerm) {
            const tbody = document.getElementById(this.config.listId);
            if (!tbody) {
                return;
            }
            
            const rows = tbody.querySelectorAll('tr.filter-field-row');
            let visibleCount = 0;
            
            rows.forEach(row => {
                const fieldKey = row.dataset.fieldKey || '';
                const labelElement = row.querySelector('label');
                const fieldLabel = labelElement ? labelElement.textContent.trim() : '';
                
                // 搜索字段名和标签
                const searchText = (fieldKey + ' ' + fieldLabel).toLowerCase();
                const matches = !searchTerm || searchText.includes(searchTerm);
                
                if (matches) {
                    row.classList.remove('filtered-out');
                    visibleCount++;
                } else {
                    row.classList.add('filtered-out');
                }
            });
            
            // 显示/隐藏空状态
            const emptyState = document.getElementById('filterFieldsEmpty');
            if (emptyState) {
                if (visibleCount === 0 && searchTerm) {
                    emptyState.classList.remove('d-none');
                    emptyState.querySelector('p').textContent = `未找到包含"${searchTerm}"的字段`;
                } else {
                    emptyState.classList.add('d-none');
                }
            }
        }

        /**
         * 更新已选字段计数显示
         */
        updateSelectedCount() {
            const countElement = document.getElementById('selectedFieldsCount');
            const warningElement = document.getElementById('maxFieldsWarning');
            const maxCountElement = document.getElementById('maxFieldsCountDisplay');
            
            if (!countElement) {
                return;
            }
            
            const enabledCount = this.filterFields.filter(f => f.enabled).length;
            const maxFields = this.config.maxEnabledFields || 10;
            
            countElement.textContent = enabledCount;
            
            if (maxCountElement) {
                maxCountElement.textContent = maxFields;
            }
            
            // 更新警告提示
            if (warningElement) {
                if (enabledCount >= maxFields) {
                    warningElement.classList.remove('d-none');
                } else {
                    warningElement.classList.add('d-none');
                }
            }
        }

        /**
         * 更新最大字段数显示
         */
        updateMaxFieldsCount() {
            const maxFieldsCountElement = document.getElementById('maxFieldsCount');
            if (maxFieldsCountElement) {
                const maxFields = this.config.maxEnabledFields || 10;
                maxFieldsCountElement.textContent = maxFields;
            }
        }

        /**
         * 应用筛选字段设置到页面
         * 注意：此方法会检测DOM中的新字段并自动添加到字段列表
         */
        applySettings() {
            // 防止重复调用导致的循环更新
            if (this.isApplyingSettings) {
                return;
            }
            
            this.isApplyingSettings = true;
            
            let container = null;
            
            try {
                container = document.getElementById(this.config.containerId);
                if (!container) {
                    return;
                }
                
                // 临时断开 MutationObserver，避免触发循环更新
                if (this.mutationObserver) {
                    this.mutationObserver.disconnect();
                }

                // 获取所有筛选行（支持两种格式）
                const filterRows = Array.from(container.querySelectorAll('.filter-row[data-filter-key]'));
                const filterItems = Array.from(container.querySelectorAll('.list-page-filter-item'));
                
                // 创建映射
                const rowsMap = {};
                const currentKeys = new Set();
                
                // 处理新格式的筛选字段
                filterRows.forEach(row => {
                    try {
                        const key = row.getAttribute('data-filter-key');
                        if (key && typeof key === 'string' && key.length > 0 && key.length < 100 && this.isValidId(key)) {
                            rowsMap[key] = row;
                            currentKeys.add(key);
                            
                            // 检测新字段
                            const existingField = this.filterFields.find(f => f.key === key);
                            if (!existingField) {
                                const labelElement = row.querySelector('.filter-label');
                                let label = key;
                                if (labelElement) {
                                    label = labelElement.textContent.replace(/[:：]/g, '').trim();
                                }
                                
                                const isRequired = this.config.requiredFields && this.config.requiredFields.includes(key);
                                const defaultEnabled = this.config.defaultEnabledFields && this.config.defaultEnabledFields.length > 0
                                    ? this.config.defaultEnabledFields.includes(key)
                                    : true;
                                this.filterFields.push({
                                    key: key,
                                    label: label,
                                    enabled: defaultEnabled,
                                    required: isRequired
                                });
                                this.sortFilterFields();
                            }
                        }
                    } catch (e) {
                    }
                });
                
                // 处理旧格式的筛选字段
                filterItems.forEach(item => {
                    try {
                        const selectElement = item.querySelector('select[name], input[name]');
                        if (selectElement) {
                            const key = selectElement.getAttribute('name');
                            if (key && typeof key === 'string' && key.length > 0 && key.length < 100 && this.isValidId(key) && !currentKeys.has(key)) {
                                // 为旧格式创建包装元素，以便统一处理
                                rowsMap[key] = item;
                                currentKeys.add(key);
                                
                                // 检测新字段
                                const existingField = this.filterFields.find(f => f.key === key);
                                if (!existingField) {
                                    const labelElement = item.querySelector('label');
                                    let label = key;
                                    if (labelElement) {
                                        label = labelElement.textContent.replace(/[:：]/g, '').trim();
                                    }
                                    
                                    const isRequired = this.config.requiredFields && this.config.requiredFields.includes(key);
                                    const defaultEnabled = this.config.defaultEnabledFields && this.config.defaultEnabledFields.length > 0
                                        ? this.config.defaultEnabledFields.includes(key)
                                        : true;
                                    this.filterFields.push({
                                        key: key,
                                        label: label,
                                        enabled: defaultEnabled,
                                        required: isRequired
                                    });
                                    this.sortFilterFields();
                                }
                            }
                        }
                    } catch (e) {
                    }
                });

                // 移除已不存在的字段（DOM中已删除的字段）
                this.filterFields = this.filterFields.filter(field => {
                    const exists = currentKeys.has(field.key);
                    return exists;
                });

            // 先移除所有元素（只移除新格式的，旧格式的通过显示/隐藏控制）
            filterRows.forEach(row => {
                if (row.parentNode === container) {
                    container.removeChild(row);
                }
            });

            // 按用户设置的顺序重新排列（必填字段在前）
            const orderedRows = [];
            const processedKeys = new Set();

            // 1. 先添加必填字段（按配置顺序）
            if (this.config.requiredFields && this.config.requiredFields.length > 0) {
                this.config.requiredFields.forEach(key => {
                    const field = this.filterFields.find(f => f.key === key);
                    if (field && field.enabled && rowsMap[key]) {
                        orderedRows.push({ row: rowsMap[key], key: key });
                        processedKeys.add(key);
                    }
                });
            }

            // 2. 添加其他启用的字段（按用户设置顺序）
            this.filterFields.forEach(field => {
                if (field.enabled && rowsMap[field.key] && !processedKeys.has(field.key)) {
                    orderedRows.push({ row: rowsMap[field.key], key: field.key });
                    processedKeys.add(field.key);
                }
            });

            // 3. 添加未在顺序中的字段（可能是新添加的字段，但未在用户设置中）
            Object.keys(rowsMap).forEach(key => {
                if (!processedKeys.has(key)) {
                    const field = this.filterFields.find(f => f.key === key);
                    if (!field || !field.enabled) {
                        // 如果字段未启用，也添加到列表末尾（但隐藏）
                        orderedRows.push({ row: rowsMap[key], key: key });
                    }
                }
            });

                // 3. 按顺序重新添加到容器，并根据启用状态显示/隐藏
                orderedRows.forEach(({ row, key }) => {
                    try {
                        const field = this.filterFields.find(f => f.key === key);
                        // 判断是新格式还是旧格式
                        const isNewFormat = row.classList.contains('filter-row');
                        const isOldFormat = row.classList.contains('list-page-filter-item');
                        
                        if (field && field.enabled) {
                            if (isNewFormat) {
                                row.style.display = 'flex';
                                // 新格式需要重新添加到容器
                                if (row.parentNode !== container) {
                                    container.appendChild(row);
                                }
                            } else if (isOldFormat) {
                                row.style.display = '';
                                // 旧格式已经在容器中，只需要显示/隐藏
                            }
                        } else {
                            if (isNewFormat) {
                                row.style.display = 'none';
                                // 新格式如果未启用，不添加到容器
                            } else if (isOldFormat) {
                                row.style.display = 'none';
                                // 旧格式隐藏即可
                            }
                        }
                    } catch (e) {
                    }
                });
            } catch (e) {
            } finally {
                // 重新连接 MutationObserver
                if (this.mutationObserver && container) {
                    this.mutationObserver.observe(container, {
                        childList: true,
                        subtree: true,
                        attributes: true,
                        attributeFilter: ['data-filter-key', 'class']
                    });
                }
                // 重置标志
                this.isApplyingSettings = false;
            }
        }

        /**
         * 保存设置到localStorage
         */
        saveSettings() {
            try {
                // 验证数据，确保只保存有效数据
                const validFields = this.filterFields.filter(field => {
                    return field && 
                           typeof field === 'object' &&
                           typeof field.key === 'string' &&
                           field.key.length > 0 &&
                           field.key.length < 100 &&
                           typeof field.enabled === 'boolean';
                });
                
                // 限制保存的数据大小，防止localStorage溢出
                const dataStr = JSON.stringify(validFields);
                if (dataStr.length > 100000) { // 限制100KB
                    throw new Error('数据过大，无法保存');
                }
                
                localStorage.setItem(this.config.storageKey, dataStr);
            } catch (e) {
                // alert不解析HTML，直接显示错误信息即可（不需要转义）
                const errorMsg = String(e.message || '未知错误');
                alert('保存失败：' + errorMsg);
            }
        }

        /**
         * 重置设置
         */
        resetSettings() {
            if (confirm('确定要重置所有筛选字段设置吗？')) {
                localStorage.removeItem(this.config.storageKey);
                this.initFilterFieldsList();
                this.renderFilterFieldsList();
                this.applySettings();
            }
        }

        /**
         * 打开设置模态框
         */
        openSettingsModal() {
            // 先检查模态框是否存在
            const modalElement = document.getElementById(this.config.modalId);
            if (!modalElement) {
                const errorMsg = `设置筛选字段模态框未找到，ID: ${this.config.modalId}`;
                alert(errorMsg + '\n\n请检查页面是否正确加载了模态框模板。');
                return;
            }
            
            // 检查模态框是否已经在显示
            if (modalElement.classList.contains('show')) {
                return;
            }
            
            // 先重新初始化字段列表（确保获取最新的筛选字段）
            try {
                this.initFilterFieldsList();
            } catch (e) {
                alert('初始化筛选字段列表失败：' + (e.message || '未知错误'));
                return;
            }
            
            // 如果字段列表为空，显示提示
            if (this.filterFields.length === 0) {
                const emptyState = document.getElementById('filterFieldsEmpty');
                if (emptyState) {
                    emptyState.classList.remove('d-none');
                    const container = document.getElementById(this.config.containerId);
                    let hint = '未找到筛选字段。';
                    if (!container) {
                        hint += `\n容器 "${this.config.containerId}" 不存在。`;
                    } else {
                        const newFormatCount = container.querySelectorAll('.filter-row[data-filter-key]').length;
                        const oldFormatCount = container.querySelectorAll('.list-page-filter-item').length;
                        hint += `\n找到新格式字段: ${newFormatCount} 个，旧格式字段: ${oldFormatCount} 个。`;
                    }
                    emptyState.querySelector('p').textContent = hint;
                }
            }
            
            // 渲染筛选字段列表
            try {
                this.renderFilterFieldsList();
            } catch (e) {
                alert('渲染筛选字段列表失败：' + (e.message || '未知错误'));
                return;
            }
            
            // 打开模态框
            this.ensureModalInBody();
            this.rebindCloseButtons();
            
            if (typeof bootstrap !== 'undefined' && bootstrap.Modal) {
                let modal = bootstrap.Modal.getInstance(modalElement) || new bootstrap.Modal(modalElement);
                this.modalInstance = modal;
                modal.show();
            } else {
                alert('Bootstrap 未加载，无法打开模态框');
            }
        }


        /**
         * 关闭模态框（不保存）
         */
        closeModal() {
            const modalElement = document.getElementById(this.config.modalId);
            if (!modalElement) return;
            
            // 移除焦点
            const activeElement = document.activeElement;
            if (activeElement && modalElement.contains(activeElement)) {
                activeElement.blur();
            }
            
            // 使用 Bootstrap Modal 关闭
            if (this.modalInstance) {
                try {
                    this.modalInstance.hide();
                } catch (e) {
                    this.forceCloseModal(modalElement);
                }
            } else if (typeof bootstrap !== 'undefined' && bootstrap.Modal) {
                const modal = bootstrap.Modal.getInstance(modalElement);
                if (modal) {
                    modal.hide();
                } else {
                    this.forceCloseModal(modalElement);
                }
            } else {
                this.forceCloseModal(modalElement);
            }
        }
        
        /**
         * 确保遮罩层被移除
         */
        ensureBackdropRemoved() {
            const backdrops = document.querySelectorAll('.modal-backdrop');
            if (backdrops.length > 0) {
                backdrops.forEach(backdrop => {
                    backdrop.remove();
                });
            }
            // 确保 body 的 modal-open 类被移除
            if (document.body.classList.contains('modal-open')) {
                document.body.classList.remove('modal-open');
                document.body.style.overflow = '';
                document.body.style.paddingRight = '';
            }
        }
        
        /**
         * 强制关闭模态框（降级方案）
         */
        forceCloseModal(modalElement) {
            if (!modalElement) {
                return;
            }
            
            // 先销毁 Bootstrap 实例，避免内部方法访问已销毁的元素
            // 必须在修改 DOM 之前销毁，否则 Bootstrap 内部代码可能会报错
            try {
                if (this.modalInstance) {
                    try {
                        // 检查实例是否仍然有效
                        if (this.modalInstance._element && this.modalInstance._element === modalElement) {
                            this.modalInstance.dispose();
                        }
                        this.modalInstance = null;
                    } catch (e) {
                    }
                }
                
                // 尝试销毁所有 Bootstrap 实例
                if (typeof bootstrap !== 'undefined' && bootstrap.Modal) {
                    const modalInstance = bootstrap.Modal.getInstance(modalElement);
                    if (modalInstance && modalInstance._element === modalElement) {
                        try {
                            modalInstance.dispose();
                        } catch (e) {
                        }
                    }
                }
            } catch (e) {
            }
            
            // 移除焦点
            try {
                const activeElement = document.activeElement;
                if (activeElement && modalElement.contains(activeElement)) {
                    activeElement.blur();
                }
            } catch (e) {
                // 忽略错误
            }
            
            // 移除 show 类
            modalElement.classList.remove('show');
            modalElement.classList.remove('fade'); // 移除 fade 类，避免动画干扰
            
            // 设置 aria 属性
            modalElement.setAttribute('aria-hidden', 'true');
            modalElement.removeAttribute('aria-modal');
            
            // 隐藏模态框
            modalElement.style.display = 'none';
            modalElement.style.visibility = 'hidden';
            modalElement.style.opacity = '0';
            
            // 移除 body 的 modal-open 类和样式
            document.body.classList.remove('modal-open');
            document.body.style.overflow = '';
            document.body.style.paddingRight = '';
            
            // 移除所有遮罩层
            this.ensureBackdropRemoved();
        }

        /**
         * 保存设置并关闭模态框
         */
        saveAndClose() {
            const tbody = document.getElementById(this.config.listId);
            if (!tbody || tbody.children.length === 0) {
                alert('没有可保存的筛选字段！');
                return;
            }

            // 从DOM中读取当前状态
            const rows = Array.from(tbody.children);
            const updatedFields = rows.map(row => {
                try {
                    const checkbox = row.querySelector('.filter-field-checkbox');
                    if (!checkbox) {
                        return null;
                    }
                    const fieldKey = row.dataset.fieldKey;
                    // 验证fieldKey，防止注入攻击
                    if (!fieldKey || typeof fieldKey !== 'string' || fieldKey.length > 100 || !this.isValidId(fieldKey)) {
                        return null;
                    }
                    const field = this.filterFields.find(f => f.key === fieldKey);
                    // 保存时不需要转义key和label，因为它们会通过JSON.stringify保存，使用时再转义
                    return {
                        key: fieldKey, // 保存原始key（已验证安全）
                        label: field ? (field.label || fieldKey) : fieldKey, // 保存原始label
                        enabled: Boolean(checkbox.checked) // 确保是布尔值
                    };
                } catch (e) {
                    return null;
                }
            }).filter(f => f !== null);

            if (updatedFields.length === 0) {
                alert('没有有效的筛选字段！');
                return;
            }

            // 检查是否超过最大启用数量
            const enabledCount = updatedFields.filter(f => f.enabled).length;
            if (enabledCount > this.config.maxEnabledFields) {
                alert(`最多只能启用${this.config.maxEnabledFields}个筛选字段！请取消一些字段的启用状态。`);
                return;
            }

            // 更新字段顺序
            this.filterFields = updatedFields;

            // 保存设置
            this.saveSettings();

            // 应用设置
            this.applySettings();

            // 关闭模态框（使用统一的关闭方法）
            this.closeModal();
        }

        /**
         * 【修复3】重新绑定所有关闭按钮的事件监听器
         * 在模态框打开时调用，确保所有关闭按钮都有事件监听器
         */
        rebindCloseButtons() {
            const modalElement = document.getElementById(this.config.modalId);
            if (!modalElement) {
                return;
            }
            
            // 1. 关闭按钮（右上角叉号）
            const closeBtn = modalElement.querySelector('.btn-close');
            if (closeBtn) {
                // 移除旧的事件监听器（通过克隆节点）
                const newCloseBtn = closeBtn.cloneNode(true);
                closeBtn.parentNode.replaceChild(newCloseBtn, closeBtn);
                
                // 确保按钮可以交互
                newCloseBtn.style.setProperty('pointer-events', 'auto', 'important');
                newCloseBtn.style.setProperty('cursor', 'pointer', 'important');
                
                const closeHandler = (e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    this.closeModal();
                };
                newCloseBtn.addEventListener('click', closeHandler, true); // 使用捕获阶段
                this.eventListeners.push({ element: newCloseBtn, event: 'click', handler: closeHandler });
            }
            
            // 2. 取消按钮（右下角）
            let cancelBtn = modalElement.querySelector('#cancelFilterFieldsSettings');
            if (!cancelBtn) {
                const cancelBtns = modalElement.querySelectorAll('[data-bs-dismiss="modal"]');
                cancelBtns.forEach(btn => {
                    if (!btn.classList.contains('btn-close') && 
                        btn.id !== this.config.saveBtnId && 
                        btn.id !== this.config.resetBtnId) {
                        cancelBtn = btn;
                    }
                });
            }
            
            if (cancelBtn) {
                // 移除旧的事件监听器（通过克隆节点）
                const newCancelBtn = cancelBtn.cloneNode(true);
                cancelBtn.parentNode.replaceChild(newCancelBtn, cancelBtn);
                
                // 确保按钮可以交互
                newCancelBtn.style.setProperty('pointer-events', 'auto', 'important');
                newCancelBtn.style.setProperty('cursor', 'pointer', 'important');
                
                // 移除可能存在的 data-bs-dismiss 属性，避免Bootstrap自动处理冲突
                newCancelBtn.removeAttribute('data-bs-dismiss');
                
                const cancelHandler = (e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    this.closeModal();
                };
                newCancelBtn.addEventListener('click', cancelHandler, true); // 使用捕获阶段
                this.eventListeners.push({ element: newCancelBtn, event: 'click', handler: cancelHandler });
            }
            
            // 3. 保存按钮
            const saveBtn = modalElement.querySelector('#' + this.config.saveBtnId);
            if (saveBtn) {
                // 确保按钮可以交互
                saveBtn.style.setProperty('pointer-events', 'auto', 'important');
                saveBtn.style.setProperty('cursor', 'pointer', 'important');
            }
            
            // 4. 重置按钮
            const resetBtn = modalElement.querySelector('#' + this.config.resetBtnId);
            if (resetBtn) {
                // 确保按钮可以交互
                resetBtn.style.setProperty('pointer-events', 'auto', 'important');
                resetBtn.style.setProperty('cursor', 'pointer', 'important');
            }
        }
        
        /**
         * 设置事件监听器
         */
        setupEventListeners() {
            // 开始设置事件监听器
            
            // 设置按钮 - 使用延迟查找，确保DOM已完全加载
            const setupSettingsBtn = () => {
                const settingsBtn = document.getElementById(this.config.settingsBtnId);
                if (settingsBtn) {
                    // 移除可能存在的旧事件监听器
                    const newBtn = settingsBtn.cloneNode(true);
                    settingsBtn.parentNode.replaceChild(newBtn, settingsBtn);
                    
                    const clickHandler = (e) => {
                        e.preventDefault();
                        e.stopPropagation();
                        // 设置筛选字段按钮被点击
                        this.openSettingsModal();
                    };
                    
                    newBtn.addEventListener('click', clickHandler);
                    this.eventListeners.push({ element: newBtn, event: 'click', handler: clickHandler });
                    
                    return true;
                }
                return false;
            };
            
            // 立即尝试绑定
            if (!setupSettingsBtn()) {
                // 如果按钮还未渲染，使用多重重试机制
                let retryCount = 0;
                const maxRetries = 20; // 增加重试次数
                const retryInterval = 100;
                
                const retryTimer = setInterval(() => {
                    retryCount++;
                    if (setupSettingsBtn()) {
                        clearInterval(retryTimer);
                        this.fixSettingsButtonPosition();
                    } else if (retryCount >= maxRetries) {
                        clearInterval(retryTimer);
                        // 尝试通过文本内容查找按钮
                        const allButtons = document.querySelectorAll('button, a');
                        for (let btn of allButtons) {
                            if (btn.textContent && (btn.textContent.includes('设置筛选字段') || btn.textContent.includes('⚙️'))) {
                                btn.id = this.config.settingsBtnId;
                                if (setupSettingsBtn()) {
                                    this.fixSettingsButtonPosition();
                                    break;
                                }
                            }
                        }
                    }
                }, retryInterval);
                
                // 同时监听DOMContentLoaded
                if (document.readyState === 'loading') {
                    document.addEventListener('DOMContentLoaded', () => {
                        if (!setupSettingsBtn()) {
                            setTimeout(() => {
                                setupSettingsBtn();
                                this.fixSettingsButtonPosition();
                            }, 200);
                        } else {
                            this.fixSettingsButtonPosition();
                        }
                    });
                }
            } else {
                // 如果立即绑定成功，确保位置固定
                this.fixSettingsButtonPosition();
            }

            // 保存按钮
            const saveBtn = document.getElementById(this.config.saveBtnId);
            if (saveBtn) {
                // 确保按钮可以交互
                saveBtn.style.setProperty('pointer-events', 'auto', 'important');
                saveBtn.style.setProperty('cursor', 'pointer', 'important');
                
                const saveHandler = (e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    this.saveAndClose();
                };
                saveBtn.addEventListener('click', saveHandler, true); // 使用捕获阶段
                this.eventListeners.push({ element: saveBtn, event: 'click', handler: saveHandler });
            }

            // 重置按钮
            const resetBtn = document.getElementById(this.config.resetBtnId);
            if (resetBtn) {
                // 确保按钮可以交互
                resetBtn.style.setProperty('pointer-events', 'auto', 'important');
                resetBtn.style.setProperty('cursor', 'pointer', 'important');
                
                const resetHandler = (e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    this.resetSettings();
                };
                resetBtn.addEventListener('click', resetHandler, true); // 使用捕获阶段
                this.eventListeners.push({ element: resetBtn, event: 'click', handler: resetHandler });
            }

            // 关闭按钮（右上角叉号）
            const modalElement = document.getElementById(this.config.modalId);
            if (modalElement) {
                // 查找关闭按钮
                const closeBtn = modalElement.querySelector('.btn-close');
                if (closeBtn) {
                    // 确保按钮可以交互
                    closeBtn.style.setProperty('pointer-events', 'auto', 'important');
                    closeBtn.style.setProperty('cursor', 'pointer', 'important');
                    
                    const closeHandler = (e) => {
                        e.preventDefault();
                        e.stopPropagation();
                        this.closeModal();
                    };
                    closeBtn.addEventListener('click', closeHandler, true); // 使用捕获阶段
                    this.eventListeners.push({ element: closeBtn, event: 'click', handler: closeHandler });
                }

                // 查找取消按钮（右下角）
                // 方法1: 通过ID查找（如果HTML中有ID）
                let cancelBtn = modalElement.querySelector('#cancelFilterFieldsSettings');
                
                // 方法2: 如果没有ID，查找所有 data-bs-dismiss="modal" 的按钮，排除关闭按钮
                if (!cancelBtn) {
                    const cancelBtns = modalElement.querySelectorAll('[data-bs-dismiss="modal"]');
                    cancelBtns.forEach(btn => {
                        // 排除关闭按钮（.btn-close）和保存、重置按钮
                        if (!btn.classList.contains('btn-close') && 
                            btn.id !== this.config.saveBtnId && 
                            btn.id !== this.config.resetBtnId) {
                            cancelBtn = btn;
                        }
                    });
                }
                
                // 为取消按钮添加事件监听器
                if (cancelBtn) {
                    // 确保按钮可以交互
                    cancelBtn.style.setProperty('pointer-events', 'auto', 'important');
                    cancelBtn.style.setProperty('cursor', 'pointer', 'important');
                    
                    // 移除可能存在的 data-bs-dismiss 属性，避免Bootstrap自动处理冲突
                    cancelBtn.removeAttribute('data-bs-dismiss');
                    const cancelHandler = (e) => {
                        e.preventDefault();
                        e.stopPropagation();
                        this.closeModal();
                    };
                    cancelBtn.addEventListener('click', cancelHandler, true); // 使用捕获阶段
                    this.eventListeners.push({ element: cancelBtn, event: 'click', handler: cancelHandler });
                }

                // 模态框显示时重新初始化和渲染
                const showHandler = () => {
                    // 重新初始化字段列表（确保获取最新的筛选字段）
                    this.initFilterFieldsList();
                    // 渲染字段列表
                    this.renderFilterFieldsList();
                    // 更新计数
                    this.updateSelectedCount();
                    this.updateMaxFieldsCount();
                };
                modalElement.addEventListener('show.bs.modal', showHandler);
                this.eventListeners.push({ element: modalElement, event: 'show.bs.modal', handler: showHandler });
            }

            // 全选按钮
            const selectAllBtn = document.getElementById('selectAllFilterFields');
            if (selectAllBtn) {
                const selectAllHandler = (e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    this.selectAllFields();
                };
                selectAllBtn.addEventListener('click', selectAllHandler);
                this.eventListeners.push({ element: selectAllBtn, event: 'click', handler: selectAllHandler });
            }

            // 反选按钮
            const invertBtn = document.getElementById('invertFilterFieldsSelection');
            if (invertBtn) {
                const invertHandler = (e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    this.invertFieldsSelection();
                };
                invertBtn.addEventListener('click', invertHandler);
                this.eventListeners.push({ element: invertBtn, event: 'click', handler: invertHandler });
            }

            // 搜索输入框
            const searchInput = document.getElementById('filterFieldsSearchInput');
            if (searchInput) {
                const searchHandler = (e) => {
                    const searchTerm = e.target.value.trim().toLowerCase();
                    this.filterFieldsList(searchTerm);
                };
                searchInput.addEventListener('input', searchHandler);
                this.eventListeners.push({ element: searchInput, event: 'input', handler: searchHandler });
            }
        }

        // ==================== 拖动相关方法 ====================

        handleDragStart(e) {
            const row = e.currentTarget;
            this.draggedRow = row;
            row.classList.add('dragging');
            e.dataTransfer.effectAllowed = 'move';
        }

        handleDragOver(e) {
            if (e.preventDefault) {
                e.preventDefault();
            }
            e.dataTransfer.dropEffect = 'move';

            const row = e.currentTarget;
            const rows = document.querySelectorAll(`#${this.config.listId} tr`);
            rows.forEach(r => {
                if (r !== this.draggedRow) {
                    r.classList.remove('drag-over');
                }
            });

            if (row !== this.draggedRow) {
                row.classList.add('drag-over');
            }

            return false;
        }

        handleDrop(e) {
            try {
                if (e.stopPropagation) {
                    e.stopPropagation();
                }

                const row = e.currentTarget;
                if (!this.draggedRow || this.draggedRow === row) {
                    return false;
                }

                const tbody = document.getElementById(this.config.listId);
                if (!tbody) {
                    return false;
                }

                const rows = Array.from(tbody.children);
                const draggedIndex = rows.indexOf(this.draggedRow);
                const targetIndex = rows.indexOf(row);

                if (draggedIndex === -1 || targetIndex === -1) {
                    return false;
                }

                if (draggedIndex < targetIndex) {
                    tbody.insertBefore(this.draggedRow, row.nextSibling);
                } else {
                    tbody.insertBefore(this.draggedRow, row);
                }

                // 更新字段顺序
                const newOrder = Array.from(tbody.children)
                    .map(r => r.dataset.fieldKey)
                    .filter(key => key && typeof key === 'string' && key.length > 0 && key.length < 100 && this.isValidId(key));
                const orderedFields = [];
                
                newOrder.forEach(key => {
                    const field = this.filterFields.find(f => f.key === key);
                    if (field) {
                        orderedFields.push(field);
                    }
                });

                // 添加未在列表中的字段
                this.filterFields.forEach(field => {
                    if (!orderedFields.find(f => f.key === field.key)) {
                        orderedFields.push(field);
                    }
                });

                this.filterFields = orderedFields;
            } catch (e) {
            } finally {
                // 清理拖拽样式
                try {
                    const rows = document.querySelectorAll(`#${this.config.listId} tr`);
                    rows.forEach(r => {
                        r.classList.remove('drag-over');
                    });
                } catch (e) {
                }
            }

            return false;
        }

        handleDragEnd(e) {
            const row = e.currentTarget;
            row.classList.remove('dragging');
            row.classList.remove('drag-over');
            this.draggedRow = null;

            const rows = document.querySelectorAll(`#${this.config.listId} tr`);
            rows.forEach(r => {
                r.classList.remove('drag-over');
            });
        }

        /**
         * HTML转义
         */
        /**
         * 转义HTML，防止XSS攻击
         */
        escapeHtml(text) {
            if (text == null || text === undefined) {
                return '';
            }
            // 确保是字符串
            const str = String(text);
            const div = document.createElement('div');
            div.textContent = str;
            return div.innerHTML;
        }

        /**
         * 清理资源，移除事件监听器
         */
        destroy() {
            // 清理所有事件监听器
            this.eventListeners.forEach(({ element, event, handler }) => {
                try {
                    element.removeEventListener(event, handler);
                } catch (e) {
                }
            });
            this.eventListeners = [];
            
            // 停止DOM变化监听
            if (this.mutationObserver) {
                try {
                    this.mutationObserver.disconnect();
                } catch (e) {
                }
                this.mutationObserver = null;
            }
            
            this.filterFields = [];
            this.draggedRow = null;
        }
    }

    // 导出到全局
    window.FilterFieldsSettings = FilterFieldsSettings;

    // 自动初始化（如果DOM已加载）
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            // 如果页面中已有配置，自动初始化
            if (window.filterFieldsSettingsConfig) {
                const instance = new FilterFieldsSettings(window.filterFieldsSettingsConfig);
                instance.init();
                window.filterFieldsSettingsInstance = instance;
            }
        });
    } else {
        // DOM已加载
        if (window.filterFieldsSettingsConfig) {
            const instance = new FilterFieldsSettings(window.filterFieldsSettingsConfig);
            instance.init();
            window.filterFieldsSettingsInstance = instance;
        }
    }

})(window);
