/**
 * 列表筛选功能模块
 * 提供可复用的列表页面筛选功能，包括：
 * - 筛选按钮点击处理
 * - 日期范围筛选
 * - 下拉框筛选
 * - 文本输入防抖筛选
 * - 表单自动提交
 * - 筛选字段设置功能（可选）
 * 
 * 使用方法：
 * 1. 在HTML中引入此JS文件
 * 2. 确保筛选表单ID为 'filterForm'（可通过配置修改）
 * 3. 筛选按钮需要包含 data-filter 和 data-value 属性
 * 4. 如需使用筛选字段设置功能，在HTML中包含模态框模板
 * 
 * 配置选项：
 * - formId: 筛选表单ID（默认：'filterForm'）
 * - debounceDelay: 文本输入防抖延迟（默认：500ms）
 * - autoSubmit: 是否自动提交表单（默认：true）
 * - enableFieldsSettings: 是否启用筛选字段设置功能（默认：false）
 * - fieldsSettingsStorageKey: localStorage存储键名（默认：'filter_fields_settings'）
 * - fieldsSettingsContainerId: 筛选条件容器ID（默认：'basicFilters'）
 * - fieldsSettingsModalId: 模态框ID（默认：'filterFieldsSettingsModal'）
 * - maxEnabledFields: 最多启用的字段数（默认：10）
 * - defaultEnabledFields: 默认启用的字段key数组
 */

(function(window) {
    'use strict';

    // 默认配置
    const DEFAULT_CONFIG = {
        formId: 'filterForm',
        debounceDelay: 500,
        autoSubmit: true,
        // 文本输入字段ID列表（可配置）
        textInputIds: ['filter_industry', 'filter_company_email', 'filter_legal_representative'],
        // 下拉框字段名列表（可配置）
        selectFieldNames: ['region', 'department', 'responsible_user'],
        // 日期范围字段名
        dateStartFieldName: 'created_time_start',
        dateEndFieldName: 'created_time_end',
        // 筛选字段设置功能配置（可选）
        enableFieldsSettings: false,
        fieldsSettingsStorageKey: 'filter_fields_settings',
        fieldsSettingsContainerId: 'basicFilters',
        fieldsSettingsModalId: 'filterFieldsSettingsModal',
        fieldsSettingsListId: 'filterFieldsList',
        fieldsSettingsBtnId: 'settingsFilterFieldsBtn',
        fieldsSettingsSaveBtnId: 'saveFilterFieldsSettings',
        fieldsSettingsResetBtnId: 'resetFilterFieldsSettings',
        maxEnabledFields: 10,
        defaultEnabledFields: []
    };

    // 列表筛选类
    class ListFilters {
        constructor(config = {}) {
            this.config = { ...DEFAULT_CONFIG, ...config };
            this.debounceTimers = {};
            // 事件监听器引用（用于清理）
            this.eventListeners = new Map();
            // 筛选字段设置相关属性
            this.filterFields = [];
            this.draggedRow = null;
            this.init();
        }

        /**
         * 初始化筛选功能
         */
        init() {
            const initAll = () => {
                this.setupFilterButtons();
                this.setupSelects();
                this.setupTextInputs();
                this.setupDateRange();
                this.setupResetButton();
                // 如果启用了筛选字段设置功能，初始化它
                if (this.config.enableFieldsSettings) {
                    this.initFieldsSettings();
                }
            };

            // 等待DOM加载完成
            if (document.readyState === 'loading') {
                document.addEventListener('DOMContentLoaded', initAll);
            } else {
                initAll();
            }
        }

        /**
         * 设置筛选按钮事件
         */
        setupFilterButtons() {
            document.querySelectorAll('.filter-btn').forEach(btn => {
                // 使用 data 属性标记已处理，避免重复绑定
                if (btn.hasAttribute('data-list-filters-bound')) {
                    return;
                }
                btn.setAttribute('data-list-filters-bound', 'true');
                
                const handler = (e) => {
                    this.handleFilterButtonClick(e.currentTarget);
                };
                
                btn.addEventListener('click', handler);
                // 保存监听器引用以便后续清理
                this._storeEventListener(btn, 'click', handler);
            });
        }

        /**
         * 存储事件监听器引用（用于清理）
         */
        _storeEventListener(element, event, handler) {
            const key = `${element}_${event}`;
            if (!this.eventListeners.has(key)) {
                this.eventListeners.set(key, { element, event, handler });
            }
        }

        /**
         * 处理筛选按钮点击
         */
        handleFilterButtonClick(btn) {
            const filterName = btn.dataset.filter;
            const filterValue = btn.dataset.value;
            
            if (!filterName) {
                console.warn('筛选按钮缺少 data-filter 属性');
                return;
            }

            const hiddenInput = document.getElementById('filter_' + filterName);
            const group = btn.closest('.filter-buttons');
            
            // 移除同组其他按钮的active状态
            if (group) {
                group.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
            }
            
            // 设置当前按钮为active
            btn.classList.add('active');
            
            // 更新隐藏输入框的值
            if (hiddenInput) {
                hiddenInput.value = filterValue || '';
            }

            // 特殊处理：自定义日期范围
            if (filterName === 'date_range') {
                this.handleDateRangeFilter(filterValue);
            }
            
            // 特殊处理：下拉框筛选（地区、部门、负责人等）
            if (['region', 'department', 'responsible_user'].includes(filterName)) {
                this.handleSelectFilter(filterName, filterValue, group);
            }
            
            // 自动提交表单
            if (this.config.autoSubmit) {
                this.submitForm();
            }
        }

        /**
         * 处理日期范围筛选
         */
        handleDateRangeFilter(range) {
            const customDateRange = document.getElementById('customDateRange');
            
            if (range === 'custom') {
                // 显示自定义日期范围输入框
                if (customDateRange) {
                    customDateRange.style.display = 'flex';
                }
            } else {
                // 隐藏自定义日期范围输入框
                if (customDateRange) {
                    customDateRange.style.display = 'none';
                }
                
                // 自动应用日期范围
                if (range) {
                    this.applyDateRange(range);
                }
            }
        }

        /**
         * 应用日期范围
         */
        applyDateRange(range) {
            const today = new Date();
            const startInput = document.querySelector(`input[name="${this.config.dateStartFieldName}"]`);
            const endInput = document.querySelector(`input[name="${this.config.dateEndFieldName}"]`);
            
            const dateRange = this._calculateDateRange(range, today);
            if (!dateRange) {
                return;
            }
            
            const { startDate, endDate } = dateRange;
            
            if (startInput && startDate) {
                startInput.value = startDate;
            }
            if (endInput && endDate) {
                endInput.value = endDate;
            }
        }

        /**
         * 计算日期范围（工具方法）
         */
        _calculateDateRange(range, today) {
            const formatDate = (date) => date.toISOString().split('T')[0];
            
            let startDate, endDate;
            
            switch(range) {
                case 'today':
                    startDate = endDate = formatDate(today);
                    break;
                case 'yesterday':
                    const yesterday = new Date(today);
                    yesterday.setDate(yesterday.getDate() - 1);
                    startDate = endDate = formatDate(yesterday);
                    break;
                case 'this_week':
                    const weekStart = new Date(today);
                    weekStart.setDate(today.getDate() - today.getDay());
                    startDate = formatDate(weekStart);
                    endDate = formatDate(today);
                    break;
                case 'last_week':
                    const lastWeekStart = new Date(today);
                    lastWeekStart.setDate(today.getDate() - today.getDay() - 7);
                    const lastWeekEnd = new Date(today);
                    lastWeekEnd.setDate(today.getDate() - today.getDay() - 1);
                    startDate = formatDate(lastWeekStart);
                    endDate = formatDate(lastWeekEnd);
                    break;
                case 'this_month':
                    startDate = formatDate(new Date(today.getFullYear(), today.getMonth(), 1));
                    endDate = formatDate(today);
                    break;
                case 'last_month':
                    const lastMonth = new Date(today.getFullYear(), today.getMonth() - 1, 1);
                    const lastMonthEnd = new Date(today.getFullYear(), today.getMonth(), 0);
                    startDate = formatDate(lastMonth);
                    endDate = formatDate(lastMonthEnd);
                    break;
                default:
                    return null;
            }
            
            return { startDate, endDate };
        }

        /**
         * 处理下拉框筛选
         */
        handleSelectFilter(filterName, filterValue, group) {
            if (filterValue === '') {
                // 选择"全部"时，清空下拉框
                const select = group ? group.querySelector('select') : null;
                if (select) {
                    select.value = '';
                }
            }
        }

        /**
         * 设置下拉框事件
         */
        setupSelects() {
            // 通用下拉框处理（通过 name 属性）
            const selectors = this.config.selectFieldNames.map(name => `select[name="${name}"]`).join(', ');
            document.querySelectorAll(selectors).forEach(select => {
                // 避免重复绑定
                if (select.hasAttribute('data-list-filters-bound')) {
                    return;
                }
                select.setAttribute('data-list-filters-bound', 'true');
                
                const handler = (e) => {
                    this.handleSelectChange(e.currentTarget);
                };
                select.addEventListener('change', handler);
                this._storeEventListener(select, 'change', handler);
            });

            // 特殊处理：通过 ID 查找的下拉框（如 regionSelect）
            const specialSelects = [
                { id: 'regionSelect', fieldName: 'region' },
                // 可以扩展更多特殊处理的下拉框
            ];

            specialSelects.forEach(({ id, fieldName }) => {
                const select = document.getElementById(id);
                if (select && !select.hasAttribute('data-list-filters-bound')) {
                    select.setAttribute('data-list-filters-bound', 'true');
                    const handler = (e) => {
                        this.handleSelectFieldChange(e.currentTarget, fieldName);
                    };
                    select.addEventListener('change', handler);
                    this._storeEventListener(select, 'change', handler);
                }
            });
        }

        /**
         * 处理下拉框变化（通用）
         */
        handleSelectChange(select) {
            // 从 select 的 name 属性获取字段名
            const fieldName = select.name;
            if (fieldName) {
                this.handleSelectFieldChange(select, fieldName);
            } else {
                // 如果没有 name 属性，只更新按钮状态
                this.updateAllButtonState(select);
                if (this.config.autoSubmit) {
                    this.submitForm();
                }
            }
        }

        /**
         * 处理指定字段的下拉框变化（统一处理方法）
         */
        handleSelectFieldChange(select, fieldName) {
            const hiddenInput = document.getElementById(`filter_${fieldName}`);
            if (hiddenInput) {
                hiddenInput.value = select.value;
            }
            this.updateAllButtonState(select);
            if (this.config.autoSubmit) {
                this.submitForm();
            }
        }

        /**
         * 更新"全部"按钮状态
         */
        updateAllButtonState(select) {
            const group = select.closest('.filter-buttons');
            const allBtn = group ? group.querySelector('.filter-btn[data-value=""]') : null;
            
            if (allBtn) {
                if (select.value === '') {
                    // 选择"全部"时，激活"全部"按钮
                    if (group) {
                        group.querySelectorAll('.filter-btn').forEach(btn => {
                            if (btn !== allBtn) btn.classList.remove('active');
                        });
                    }
                    allBtn.classList.add('active');
                } else {
                    // 选择具体值时，取消"全部"按钮的激活状态
                    allBtn.classList.remove('active');
                }
            }
        }

        /**
         * 设置文本输入框事件（防抖）
         */
        setupTextInputs() {
            this.config.textInputIds.forEach(inputId => {
                const input = document.getElementById(inputId);
                if (input && !input.hasAttribute('data-list-filters-bound')) {
                    input.setAttribute('data-list-filters-bound', 'true');
                    
                    // 输入事件（防抖）
                    const inputHandler = (e) => {
                        this.handleTextInput(e.currentTarget);
                    };
                    input.addEventListener('input', inputHandler);
                    this._storeEventListener(input, 'input', inputHandler);
                    
                    // 失去焦点时立即提交
                    const blurHandler = (e) => {
                        this.handleTextInputBlur(e.currentTarget);
                    };
                    input.addEventListener('blur', blurHandler);
                    this._storeEventListener(input, 'blur', blurHandler);
                }
            });
        }

        /**
         * 处理文本输入（防抖）
         */
        handleTextInput(input) {
            const inputId = input.id;
            
            // 更新"全部"按钮状态
            const group = input.closest('.filter-buttons');
            const allBtn = group ? group.querySelector('.filter-btn[data-value=""]') : null;
            
            if (allBtn) {
                if (input.value.trim() === '') {
                    // 输入为空时，激活"全部"按钮
                    if (group) {
                        group.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
                    }
                    allBtn.classList.add('active');
                } else {
                    // 有输入时，取消"全部"按钮的激活状态
                    allBtn.classList.remove('active');
                }
            }
            
            // 防抖：延迟提交表单
            this._clearDebounceTimer(inputId);
            
            this.debounceTimers[inputId] = setTimeout(() => {
                delete this.debounceTimers[inputId];
                if (this.config.autoSubmit) {
                    this.submitForm();
                }
            }, this.config.debounceDelay);
        }

        /**
         * 处理文本输入失去焦点
         */
        handleTextInputBlur(input) {
            const inputId = input.id;
            
            // 清除防抖定时器
            this._clearDebounceTimer(inputId);
            
            // 立即提交表单
            if (this.config.autoSubmit) {
                this.submitForm();
            }
        }

        /**
         * 清除防抖定时器（工具方法）
         */
        _clearDebounceTimer(inputId) {
            if (this.debounceTimers[inputId]) {
                clearTimeout(this.debounceTimers[inputId]);
                delete this.debounceTimers[inputId];
            }
        }

        /**
         * 清理所有防抖定时器
         */
        _clearAllDebounceTimers() {
            Object.keys(this.debounceTimers).forEach(inputId => {
                this._clearDebounceTimer(inputId);
            });
        }

        /**
         * 设置日期范围相关事件
         */
        setupDateRange() {
            // 自定义日期范围输入框变化时提交表单
            const startInput = document.querySelector(`input[name="${this.config.dateStartFieldName}"]`);
            const endInput = document.querySelector(`input[name="${this.config.dateEndFieldName}"]`);
            
            const changeHandler = () => {
                if (this.config.autoSubmit) {
                    this.submitForm();
                }
            };
            
            if (startInput && !startInput.hasAttribute('data-list-filters-bound')) {
                startInput.setAttribute('data-list-filters-bound', 'true');
                startInput.addEventListener('change', changeHandler);
                this._storeEventListener(startInput, 'change', changeHandler);
            }
            
            if (endInput && !endInput.hasAttribute('data-list-filters-bound')) {
                endInput.setAttribute('data-list-filters-bound', 'true');
                endInput.addEventListener('change', changeHandler);
                this._storeEventListener(endInput, 'change', changeHandler);
            }
        }

        /**
         * 提交表单
         */
        submitForm() {
            const form = document.getElementById(this.config.formId);
            if (form) {
                form.submit();
            } else {
                console.warn(`筛选表单 ${this.config.formId} 未找到`);
            }
        }

        /**
         * 设置重置按钮事件
         */
        setupResetButton() {
            const form = document.getElementById(this.config.formId);
            if (form) {
                // 查找表单内的重置按钮
                const resetBtn = form.querySelector('button[type="reset"]');
                if (resetBtn && !resetBtn.hasAttribute('data-list-filters-handled')) {
                    resetBtn.setAttribute('data-list-filters-handled', 'true');
                    resetBtn.addEventListener('click', (e) => {
                        e.preventDefault();
                        this.reset();
                    });
                }
                
                // 也查找通过 form 属性关联的重置按钮（在表单外部）
                const externalResetBtn = document.querySelector(`button[type="reset"][form="${this.config.formId}"]`);
                if (externalResetBtn && !externalResetBtn.hasAttribute('data-list-filters-handled')) {
                    externalResetBtn.setAttribute('data-list-filters-handled', 'true');
                    externalResetBtn.addEventListener('click', (e) => {
                        e.preventDefault();
                        this.reset();
                    });
                }
            }
        }


        /**
         * 手动提交表单（供外部调用）
         */
        submit() {
            this.submitForm();
        }

        /**
         * 重置筛选条件（供外部调用）
         */
        reset() {
            const form = document.getElementById(this.config.formId);
            if (form) {
                // 清除所有防抖定时器
                this._clearAllDebounceTimers();
                
                form.reset();
                
                // 重置所有筛选按钮状态
                document.querySelectorAll('.filter-btn').forEach(btn => {
                    btn.classList.remove('active');
                    if (btn.dataset.value === '') {
                        btn.classList.add('active');
                    }
                });
                
                // 重置隐藏输入框
                form.querySelectorAll('input[type="hidden"]').forEach(input => {
                    if (input.id && input.id.startsWith('filter_')) {
                        input.value = '';
                    }
                });
                
                // 重置下拉框
                form.querySelectorAll('select').forEach(select => {
                    select.value = '';
                });
                
                // 隐藏自定义日期范围输入框
                const customDateRange = document.getElementById('customDateRange');
                if (customDateRange) {
                    customDateRange.style.display = 'none';
                }
                
                // 提交表单
                if (this.config.autoSubmit) {
                    this.submitForm();
                }
            }
        }

        /**
         * 销毁实例，清理所有事件监听器和定时器
         */
        destroy() {
            // 清理所有防抖定时器
            this._clearAllDebounceTimers();
            
            // 清理所有事件监听器
            this.eventListeners.forEach(({ element, event, handler }) => {
                element.removeEventListener(event, handler);
            });
            this.eventListeners.clear();
            
            // 清理筛选字段设置实例
            if (this.fieldsSettingsInstance && typeof this.fieldsSettingsInstance.destroy === 'function') {
                this.fieldsSettingsInstance.destroy();
            }
        }

        // ==================== 筛选字段设置功能（可选） ====================

        /**
         * 初始化筛选字段设置功能
         * 如果 filter-fields-settings.js 已加载，使用它；否则使用内置的简化版本
         */
        initFieldsSettings() {
            // 使用独立的 filter-fields-settings.js 模块
            // 添加延迟检查，确保 filter-fields-settings.js 已完全加载
            const tryInit = () => {
                try {
                    if (window.FilterFieldsSettings && typeof window.FilterFieldsSettings === 'function') {
                        // 验证配置参数
                        const fieldsSettingsConfig = {
                            storageKey: String(this.config.fieldsSettingsStorageKey || 'filter_fields_settings'),
                            containerId: String(this.config.fieldsSettingsContainerId || 'basicFilters'),
                            modalId: String(this.config.fieldsSettingsModalId || 'filterFieldsSettingsModal'),
                            listId: String(this.config.fieldsSettingsListId || 'filterFieldsList'),
                            settingsBtnId: String(this.config.fieldsSettingsBtnId || 'settingsFilterFieldsBtn'),
                            saveBtnId: String(this.config.fieldsSettingsSaveBtnId || 'saveFilterFieldsSettings'),
                            resetBtnId: String(this.config.fieldsSettingsResetBtnId || 'resetFilterFieldsSettings'),
                            maxEnabledFields: Number(this.config.maxEnabledFields) || 10,
                            defaultEnabledFields: Array.isArray(this.config.defaultEnabledFields) ? 
                                                 this.config.defaultEnabledFields : []
                        };
                        
                        // 验证数字范围
                        if (fieldsSettingsConfig.maxEnabledFields < 1 || fieldsSettingsConfig.maxEnabledFields > 50) {
                            fieldsSettingsConfig.maxEnabledFields = 10;
                        }
                        
                        this.fieldsSettingsInstance = new window.FilterFieldsSettings(fieldsSettingsConfig);
                        this.fieldsSettingsInstance.init();
                        return true;
                    }
                } catch (e) {
                    console.error('初始化筛选字段设置功能失败:', e);
                }
                return false;
            };
            
            // 立即尝试初始化
            if (!tryInit()) {
                // 如果 FilterFieldsSettings 还未加载，等待一段时间后重试
                let retryCount = 0;
                const maxRetries = 10; // 最多重试10次
                const retryInterval = 100; // 每次间隔100ms
                
                const retryTimer = setInterval(() => {
                    retryCount++;
                    if (tryInit()) {
                        clearInterval(retryTimer);
                    } else if (retryCount >= maxRetries) {
                        clearInterval(retryTimer);
                        console.warn('筛选字段设置功能需要先引入 filter-fields-settings.js 文件，已重试' + maxRetries + '次');
                    }
                }, retryInterval);
            }
        }
    }

    // 导出到全局
    window.ListFilters = ListFilters;

    // 自动初始化（如果DOM已加载）
    // 只有在页面中存在筛选表单或筛选容器时才初始化
    const shouldAutoInit = () => {
        // 检查是否存在筛选表单
        const filterForm = document.getElementById('filterForm');
        // 检查是否存在筛选容器
        const filterContainer = document.getElementById('basicFilters') || document.querySelector('.list-page-filters');
        // 检查是否有筛选按钮
        const filterButtons = document.querySelectorAll('.filter-btn');
        
        // 如果存在筛选表单、筛选容器或筛选按钮，则应该初始化
        return filterForm || filterContainer || filterButtons.length > 0;
    };
    
    const autoInit = () => {
        // 只有在页面中存在筛选功能时才自动初始化
        if (shouldAutoInit()) {
            const config = window.listFiltersConfig || {};
            const instance = new ListFilters(config);
            window.listFiltersInstance = instance;
        }
    };
    
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', autoInit);
    } else {
        // DOM已加载，立即初始化
        autoInit();
    }

})(window);

