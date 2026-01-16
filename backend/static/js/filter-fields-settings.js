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
        defaultEnabledFields: []
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
                    console.warn(`配置参数 ${field} 必须是字符串，使用默认值`);
                    config[field] = DEFAULT_CONFIG[field];
                }
                // ID类型的字段需要更严格的验证
                if (config[field] && typeof config[field] === 'string') {
                    if (field.endsWith('Id') || field === 'containerId') {
                        // ID类型字段：验证格式并清理
                        if (!this.isValidId(config[field])) {
                            console.warn(`配置参数 ${field} 格式无效，已清理：${config[field]}`);
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
                console.warn('maxEnabledFields 必须是大于0的数字，使用默认值');
                config.maxEnabledFields = DEFAULT_CONFIG.maxEnabledFields;
            }

            // 验证数组参数
            if (config.defaultEnabledFields && !Array.isArray(config.defaultEnabledFields)) {
                console.warn('defaultEnabledFields 必须是数组，使用默认值');
                config.defaultEnabledFields = DEFAULT_CONFIG.defaultEnabledFields;
            }

            return config;
        }

        /**
         * 初始化筛选字段设置功能
         */
        init() {
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
         * 启动MutationObserver监听DOM变化
         * 实时检测筛选字段的添加/删除
         */
        startMutationObserver() {
            // 检查浏览器是否支持MutationObserver
            if (typeof MutationObserver === 'undefined') {
                console.warn('浏览器不支持MutationObserver，将无法实时监听DOM变化');
                return;
            }
            
            const container = document.getElementById(this.config.containerId);
            if (!container) {
                console.warn('筛选容器未找到，无法启动DOM监听');
                return;
            }
            
            // 防抖处理，避免频繁触发
            let debounceTimer = null;
            const debounceDelay = 300; // 300ms防抖
            
            // 创建MutationObserver
            this.mutationObserver = new MutationObserver((mutations) => {
                // 检查是否有筛选字段相关的变化
                let shouldUpdate = false;
                
                mutations.forEach(mutation => {
                    // 检查是否有节点添加或删除
                    if (mutation.addedNodes.length > 0 || mutation.removedNodes.length > 0) {
                        mutation.addedNodes.forEach(node => {
                            if (node.nodeType === 1 && // Element节点
                                (node.classList.contains('filter-row') || 
                                 node.querySelector && node.querySelector('.filter-row'))) {
                                shouldUpdate = true;
                            }
                        });
                        
                        mutation.removedNodes.forEach(node => {
                            if (node.nodeType === 1 && // Element节点
                                (node.classList.contains('filter-row') || 
                                 node.querySelector && node.querySelector('.filter-row'))) {
                                shouldUpdate = true;
                            }
                        });
                    }
                    
                    // 检查属性变化（data-filter-key）
                    if (mutation.type === 'attributes' && 
                        mutation.attributeName === 'data-filter-key') {
                        shouldUpdate = true;
                    }
                });
                
                // 如果有相关变化，防抖后更新（但不在应用设置期间触发，避免循环）
                if (shouldUpdate && !this.isApplyingSettings) {
                    clearTimeout(debounceTimer);
                    debounceTimer = setTimeout(() => {
                        // 再次检查，防止在延迟期间已经开始应用设置
                        if (!this.isApplyingSettings) {
                            console.log('检测到筛选字段变化，自动同步字段列表');
                            // 重新初始化字段列表
                            this.initFilterFieldsList();
                            // 重新应用设置
                            this.applySettings();
                        }
                    }, debounceDelay);
                }
            });
            
            // 开始监听
            this.mutationObserver.observe(container, {
                childList: true,      // 监听子节点的添加/删除
                subtree: true,        // 监听所有后代节点
                attributes: true,     // 监听属性变化
                attributeFilter: ['data-filter-key', 'class']  // 只监听特定属性
            });
            
            console.log('已启动DOM变化监听，将自动检测筛选字段的变化');
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
                
                console.log('设置筛选字段按钮位置已固定到筛选容器右上角');
            } else {
                console.warn('设置筛选字段按钮或容器未找到，无法固定位置');
            }
        }

        /**
         * 从HTML中自动发现所有筛选字段
         */
        initializeFilterFields() {
            const container = document.getElementById(this.config.containerId);
            if (!container) {
                console.warn(`筛选条件容器 ${this.config.containerId} 未找到`);
                return [];
            }

            const filterRows = container.querySelectorAll('.filter-row[data-filter-key]');
            const fields = [];

            filterRows.forEach(row => {
                const rawKey = row.getAttribute('data-filter-key');
                if (rawKey) {
                    // 验证和清理key，确保只包含安全字符
                    const safeKey = this.sanitizeId(String(rawKey).trim());
                    if (!safeKey) {
                        console.warn('筛选字段key无效，已跳过:', rawKey);
                        return;
                    }
                    if (safeKey !== rawKey) {
                        console.warn('筛选字段key包含不安全字符，已清理:', rawKey, '->', safeKey);
                    }

                    // 从label中提取字段名称（移除冒号）
                    const labelElement = row.querySelector('.filter-label');
                    let label = safeKey; // 默认使用清理后的key

                    if (labelElement) {
                        label = labelElement.textContent.replace(/[:：]/g, '').trim();
                    }

                    // 检查是否在默认启用列表中（使用清理后的key）
                    const enabled = this.config.defaultEnabledFields.includes(safeKey);

                    fields.push({
                        key: safeKey, // 使用清理后的key
                        label: label,
                        enabled: enabled
                    });
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
                console.warn('未找到筛选字段，请确保HTML中包含 data-filter-key 属性的筛选行');
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
                    console.warn('解析保存的筛选字段设置失败:', e);
                    // 如果解析失败，清除损坏的数据
                    try {
                        localStorage.removeItem(this.config.storageKey);
                    } catch (clearError) {
                        console.error('清除损坏的localStorage数据失败:', clearError);
                    }
                }
            }

            // 合并保存的设置和当前字段
            // 如果没有保存的设置，默认所有字段都启用
            if (savedFields.length === 0) {
                // 没有保存的设置，默认所有字段都启用
                this.filterFields = fields.map(field => ({
                    ...field,
                    enabled: true  // 默认启用所有字段
                }));
            } else {
                // 有保存的设置，使用保存的设置
                this.filterFields = fields.map(field => {
                    const saved = savedFields.find(sf => sf.key === field.key);
                    return saved ? { ...field, ...saved } : field;
                });

                // 添加新字段（如果HTML中有新字段但保存的设置中没有）
                const existingKeys = new Set(this.filterFields.map(f => f.key));
                fields.forEach(field => {
                    if (!existingKeys.has(field.key)) {
                        // 新字段默认启用
                        this.filterFields.push({ ...field, enabled: true });
                    }
                });
            }
        }

        /**
         * 渲染筛选字段列表到模态框
         */
        renderFilterFieldsList() {
            const tbody = document.getElementById(this.config.listId);
            if (!tbody) {
                console.warn(`筛选字段列表容器 ${this.config.listId} 未找到`);
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
                    console.warn('无效的字段key，跳过:', field.key);
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
                
                // 使用清理后的safeKey构建ID属性
                const checkboxId = `filter-field-${safeKey}`;
                row.innerHTML = `
                    <td>
                        <div class="form-check">
                            <input class="form-check-input filter-field-checkbox" type="checkbox" 
                                   id="${this.escapeHtml(checkboxId)}" 
                                   ${checkedAttr}>
                        </div>
                    </td>
                    <td>
                        <label class="form-check-label" for="${this.escapeHtml(checkboxId)}" style="cursor: pointer;">
                            ${fieldLabel}
                        </label>
                    </td>
                    <td>
                        <i class="bi bi-grip-vertical text-muted" style="font-size: 1.2em; cursor: move;"></i>
                    </td>
                `;

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
        }

        /**
         * 更新字段启用状态
         */
        updateFieldEnabled(fieldKey, enabled) {
            const field = this.filterFields.find(f => f.key === fieldKey);
            if (!field) {
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
                    console.warn(`筛选条件容器 ${this.config.containerId} 未找到`);
                    return;
                }
                
                // 临时断开 MutationObserver，避免触发循环更新
                if (this.mutationObserver) {
                    this.mutationObserver.disconnect();
                }

                // 获取所有筛选行（重新从DOM抓取，支持动态添加的字段）
                const filterRows = Array.from(container.querySelectorAll('.filter-row[data-filter-key]'));
                
                // 创建映射
                const rowsMap = {};
                const currentKeys = new Set();
                filterRows.forEach(row => {
                    try {
                        const key = row.getAttribute('data-filter-key');
                        // 验证key格式，确保只包含安全字符
                        if (key && typeof key === 'string' && key.length > 0 && key.length < 100 && this.isValidId(key)) {
                            rowsMap[key] = row;
                            currentKeys.add(key);
                            
                            // 检测新字段：如果DOM中存在但字段列表中不存在，自动添加
                            const existingField = this.filterFields.find(f => f.key === key);
                            if (!existingField) {
                                // 从label中提取字段名称
                                const labelElement = row.querySelector('.filter-label');
                                let label = key; // 默认使用key
                                if (labelElement) {
                                    label = labelElement.textContent.replace(/[:：]/g, '').trim();
                                }
                                
                                // 自动添加新字段，默认启用
                                console.log('检测到新筛选字段，自动添加:', key, label);
                                this.filterFields.push({
                                    key: key,
                                    label: label,
                                    enabled: true  // 新字段默认启用
                                });
                            }
                        } else if (key && typeof key === 'string') {
                            console.warn('筛选行key格式无效，已忽略:', key);
                        }
                    } catch (e) {
                        console.warn('处理筛选行时出错:', e);
                    }
                });

                // 移除已不存在的字段（DOM中已删除的字段）
                this.filterFields = this.filterFields.filter(field => {
                    const exists = currentKeys.has(field.key);
                    if (!exists) {
                        console.log('筛选字段已从DOM中移除，从列表中删除:', field.key);
                    }
                    return exists;
                });

            // 先移除所有元素
            filterRows.forEach(row => {
                if (row.parentNode === container) {
                    container.removeChild(row);
                }
            });

            // 按用户设置的顺序重新排列
            const orderedRows = [];

            // 1. 先添加用户设置顺序中的字段（只添加启用的）
            this.filterFields.forEach(field => {
                if (field.enabled && rowsMap[field.key]) {
                    orderedRows.push({ row: rowsMap[field.key], key: field.key });
                }
            });

            // 2. 添加未在顺序中的字段（可能是新添加的字段，但未在用户设置中）
            Object.keys(rowsMap).forEach(key => {
                const field = this.filterFields.find(f => f.key === key);
                if (!field || !field.enabled) {
                    // 如果字段未启用，也添加到列表末尾（但隐藏）
                    orderedRows.push({ row: rowsMap[key], key: key });
                }
            });

                // 3. 按顺序重新添加到容器，并根据启用状态显示/隐藏
                orderedRows.forEach(({ row, key }) => {
                    try {
                        const field = this.filterFields.find(f => f.key === key);
                        if (field && field.enabled) {
                            row.style.display = 'flex';
                        } else {
                            row.style.display = 'none';
                        }
                        container.appendChild(row);
                    } catch (e) {
                        console.warn('添加筛选行时出错:', e);
                    }
                });
            } catch (e) {
                console.error('应用筛选字段设置失败:', e);
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
                console.error('保存筛选字段设置失败:', e);
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
            console.log('尝试打开设置筛选字段模态框，模态框ID:', this.config.modalId);
            
            // 先检查模态框是否存在
            const modalElement = document.getElementById(this.config.modalId);
            if (!modalElement) {
                console.error('模态框元素未找到，ID:', this.config.modalId);
                alert('设置筛选字段模态框未找到，请检查页面是否正确加载了模态框模板。\n模态框ID: ' + this.config.modalId);
                return;
            }
            
            console.log('模态框元素找到，准备渲染字段列表');
            
            // 渲染筛选字段列表
            try {
                this.renderFilterFieldsList();
                console.log('筛选字段列表渲染完成');
            } catch (e) {
                console.error('渲染筛选字段列表失败:', e);
                alert('渲染筛选字段列表失败：' + (e.message || '未知错误'));
                return;
            }
            
            // 打开模态框
            try {
                // 检查 bootstrap 是否可用
                if (typeof bootstrap !== 'undefined' && bootstrap.Modal) {
                    console.log('使用 Bootstrap 5 打开模态框');
                    const modal = new bootstrap.Modal(modalElement, {
                        backdrop: true  // 启用遮罩层
                    });
                    modal.show();
                } else if (typeof $ !== 'undefined' && $.fn.modal) {
                    console.log('使用 jQuery Bootstrap 打开模态框');
                    $(modalElement).modal({
                        backdrop: true  // 启用遮罩层
                    });
                    $(modalElement).modal('show');
                } else {
                    console.log('使用降级方案打开模态框');
                    // 降级方案：显示模态框
                    modalElement.style.display = 'block';
                    modalElement.classList.add('show');
                    modalElement.setAttribute('aria-hidden', 'false');
                    modalElement.setAttribute('aria-modal', 'true');
                    modalElement.setAttribute('role', 'dialog');
                    document.body.classList.add('modal-open');
                }
                console.log('模态框打开成功');
            } catch (e) {
                console.error('打开模态框失败:', e);
                alert('打开设置筛选字段模态框失败：' + (e.message || '未知错误'));
            }
        }

        /**
         * 关闭模态框（不保存）
         */
        closeModal() {
            const modalElement = document.getElementById(this.config.modalId);
            if (modalElement) {
                // 在关闭之前，先移除焦点，避免 aria-hidden 警告
                const activeElement = document.activeElement;
                if (activeElement && modalElement.contains(activeElement)) {
                    // 如果焦点在模态框内，将焦点移到 body
                    activeElement.blur();
                    document.body.focus();
                }
                
                // 检查 bootstrap 是否可用
                if (typeof bootstrap !== 'undefined' && bootstrap.Modal) {
                    const modal = bootstrap.Modal.getInstance(modalElement);
                    if (modal) {
                        modal.hide();
                    } else {
                        const newModal = new bootstrap.Modal(modalElement);
                        newModal.hide();
                    }
                } else if (typeof $ !== 'undefined' && $.fn.modal) {
                    // 兼容 jQuery Bootstrap
                    $(modalElement).modal('hide');
                } else {
                    // 降级方案：直接隐藏模态框
                    // 先移除焦点，再设置 aria-hidden
                    setTimeout(() => {
                        modalElement.style.display = 'none';
                        modalElement.classList.remove('show');
                        modalElement.setAttribute('aria-hidden', 'true');
                        document.body.classList.remove('modal-open');
                        const backdrop = document.getElementById('modalBackdrop');
                        if (backdrop) {
                            backdrop.remove();
                        }
                    }, 0);
                }
            }
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
                        console.warn('无效的字段key:', fieldKey);
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
                    console.warn('处理筛选字段行时出错:', e);
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

            // 关闭模态框
            const modalElement = document.getElementById(this.config.modalId);
            if (modalElement) {
                // 在关闭之前，先移除焦点，避免 aria-hidden 警告
                const activeElement = document.activeElement;
                if (activeElement && modalElement.contains(activeElement)) {
                    // 如果焦点在模态框内，将焦点移到 body
                    activeElement.blur();
                    document.body.focus();
                }
                
                // 检查 bootstrap 是否可用
                if (typeof bootstrap !== 'undefined' && bootstrap.Modal) {
                    const modal = bootstrap.Modal.getInstance(modalElement);
                    if (modal) {
                        modal.hide();
                    } else {
                        const newModal = new bootstrap.Modal(modalElement);
                        newModal.hide();
                    }
                } else if (typeof $ !== 'undefined' && $.fn.modal) {
                    // 兼容 jQuery Bootstrap
                    $(modalElement).modal('hide');
                } else {
                    // 降级方案：直接隐藏模态框
                    // 先移除焦点，再设置 aria-hidden
                    setTimeout(() => {
                        modalElement.style.display = 'none';
                        modalElement.classList.remove('show');
                        modalElement.setAttribute('aria-hidden', 'true');
                        document.body.classList.remove('modal-open');
                        const backdrop = document.getElementById('modalBackdrop');
                        if (backdrop) {
                            backdrop.remove();
                        }
                    }, 0);
                }
            }
        }

        /**
         * 设置事件监听器
         */
        setupEventListeners() {
            console.log('开始设置事件监听器，按钮ID:', this.config.settingsBtnId);
            
            // 设置按钮 - 使用延迟查找，确保DOM已完全加载
            const setupSettingsBtn = () => {
                const settingsBtn = document.getElementById(this.config.settingsBtnId);
                if (settingsBtn) {
                    console.log('找到设置按钮，准备绑定事件');
                    // 移除可能存在的旧事件监听器
                    const newBtn = settingsBtn.cloneNode(true);
                    settingsBtn.parentNode.replaceChild(newBtn, settingsBtn);
                    
                    const clickHandler = (e) => {
                        e.preventDefault();
                        e.stopPropagation();
                        console.log('设置筛选字段按钮被点击');
                        this.openSettingsModal();
                    };
                    
                    newBtn.addEventListener('click', clickHandler);
                    this.eventListeners.push({ element: newBtn, event: 'click', handler: clickHandler });
                    
                    console.log('设置按钮事件监听器绑定成功');
                    return true;
                } else {
                    console.warn('设置按钮未找到，ID:', this.config.settingsBtnId);
                }
                return false;
            };
            
            // 立即尝试绑定
            if (!setupSettingsBtn()) {
                console.log('按钮未找到，使用延迟绑定机制');
                // 如果按钮还未渲染，使用多重重试机制
                let retryCount = 0;
                const maxRetries = 20; // 增加重试次数
                const retryInterval = 100;
                
                const retryTimer = setInterval(() => {
                    retryCount++;
                    if (setupSettingsBtn()) {
                        clearInterval(retryTimer);
                        console.log('设置按钮绑定成功（重试' + retryCount + '次）');
                        this.fixSettingsButtonPosition();
                    } else if (retryCount >= maxRetries) {
                        clearInterval(retryTimer);
                        console.error('设置按钮绑定失败：按钮 ' + this.config.settingsBtnId + ' 未找到，已重试' + maxRetries + '次');
                        // 尝试通过文本内容查找按钮
                        const allButtons = document.querySelectorAll('button, a');
                        for (let btn of allButtons) {
                            if (btn.textContent && (btn.textContent.includes('设置筛选字段') || btn.textContent.includes('⚙️'))) {
                                console.log('通过文本内容找到按钮，尝试绑定事件');
                                btn.id = this.config.settingsBtnId;
                                if (setupSettingsBtn()) {
                                    console.log('通过文本内容找到的按钮绑定成功');
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
                console.log('设置按钮立即绑定成功');
                this.fixSettingsButtonPosition();
            }

            // 保存按钮
            const saveBtn = document.getElementById(this.config.saveBtnId);
            if (saveBtn) {
                const saveHandler = () => {
                    this.saveAndClose();
                };
                saveBtn.addEventListener('click', saveHandler);
                this.eventListeners.push({ element: saveBtn, event: 'click', handler: saveHandler });
            }

            // 重置按钮
            const resetBtn = document.getElementById(this.config.resetBtnId);
            if (resetBtn) {
                const resetHandler = () => {
                    this.resetSettings();
                };
                resetBtn.addEventListener('click', resetHandler);
                this.eventListeners.push({ element: resetBtn, event: 'click', handler: resetHandler });
            }

            // 关闭按钮（右上角叉号）
            const modalElement = document.getElementById(this.config.modalId);
            if (modalElement) {
                // 查找关闭按钮
                const closeBtn = modalElement.querySelector('.btn-close');
                if (closeBtn) {
                    const closeHandler = (e) => {
                        e.preventDefault();
                        this.closeModal();
                    };
                    closeBtn.addEventListener('click', closeHandler);
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
                    // 移除可能存在的 data-bs-dismiss 属性，避免Bootstrap自动处理冲突
                    cancelBtn.removeAttribute('data-bs-dismiss');
                    const cancelHandler = (e) => {
                        e.preventDefault();
                        e.stopPropagation();
                        this.closeModal();
                    };
                    cancelBtn.addEventListener('click', cancelHandler);
                    this.eventListeners.push({ element: cancelBtn, event: 'click', handler: cancelHandler });
                }

                // 模态框显示时重新渲染
                const showHandler = () => {
                    this.renderFilterFieldsList();
                };
                modalElement.addEventListener('show.bs.modal', showHandler);
                this.eventListeners.push({ element: modalElement, event: 'show.bs.modal', handler: showHandler });
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
                console.error('处理拖拽放置时出错:', e);
            } finally {
                // 清理拖拽样式
                try {
                    const rows = document.querySelectorAll(`#${this.config.listId} tr`);
                    rows.forEach(r => {
                        r.classList.remove('drag-over');
                    });
                } catch (e) {
                    console.warn('清理拖拽样式时出错:', e);
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
                    console.warn('移除事件监听器失败:', e);
                }
            });
            this.eventListeners = [];
            
            // 停止DOM变化监听
            if (this.mutationObserver) {
                try {
                    this.mutationObserver.disconnect();
                    console.log('已停止DOM变化监听');
                } catch (e) {
                    console.warn('停止MutationObserver失败:', e);
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

