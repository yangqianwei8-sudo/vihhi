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
            // 筛选字段设置相关属性
            this.filterFields = [];
            this.draggedRow = null;
            this.init();
        }

        /**
         * 初始化筛选功能
         */
        init() {
            // 等待DOM加载完成
            if (document.readyState === 'loading') {
                document.addEventListener('DOMContentLoaded', () => {
                    this.setupFilterButtons();
                    this.setupSelects();
                    this.setupTextInputs();
                    this.setupDateRange();
                    // 如果启用了筛选字段设置功能，初始化它
                    if (this.config.enableFieldsSettings) {
                        this.initFieldsSettings();
                    }
                });
            } else {
                this.setupFilterButtons();
                this.setupSelects();
                this.setupTextInputs();
                this.setupDateRange();
                // 如果启用了筛选字段设置功能，初始化它
                if (this.config.enableFieldsSettings) {
                    this.initFieldsSettings();
                }
            }
        }

        /**
         * 设置筛选按钮事件
         */
        setupFilterButtons() {
            document.querySelectorAll('.filter-btn').forEach(btn => {
                // 移除旧的事件监听器（如果存在）
                const newBtn = btn.cloneNode(true);
                btn.parentNode.replaceChild(newBtn, btn);
                
                newBtn.addEventListener('click', (e) => {
                    this.handleFilterButtonClick(e.currentTarget);
                });
            });
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
            const startInput = document.querySelector('input[name="created_time_start"]');
            const endInput = document.querySelector('input[name="created_time_end"]');
            
            let startDate, endDate;
            
            switch(range) {
                case 'today':
                    startDate = endDate = today.toISOString().split('T')[0];
                    break;
                case 'yesterday':
                    const yesterday = new Date(today);
                    yesterday.setDate(yesterday.getDate() - 1);
                    startDate = endDate = yesterday.toISOString().split('T')[0];
                    break;
                case 'this_week':
                    const weekStart = new Date(today);
                    weekStart.setDate(today.getDate() - today.getDay());
                    startDate = weekStart.toISOString().split('T')[0];
                    endDate = today.toISOString().split('T')[0];
                    break;
                case 'last_week':
                    const lastWeekStart = new Date(today);
                    lastWeekStart.setDate(today.getDate() - today.getDay() - 7);
                    const lastWeekEnd = new Date(today);
                    lastWeekEnd.setDate(today.getDate() - today.getDay() - 1);
                    startDate = lastWeekStart.toISOString().split('T')[0];
                    endDate = lastWeekEnd.toISOString().split('T')[0];
                    break;
                case 'this_month':
                    startDate = new Date(today.getFullYear(), today.getMonth(), 1).toISOString().split('T')[0];
                    endDate = today.toISOString().split('T')[0];
                    break;
                case 'last_month':
                    const lastMonth = new Date(today.getFullYear(), today.getMonth() - 1, 1);
                    const lastMonthEnd = new Date(today.getFullYear(), today.getMonth(), 0);
                    startDate = lastMonth.toISOString().split('T')[0];
                    endDate = lastMonthEnd.toISOString().split('T')[0];
                    break;
                default:
                    return;
            }
            
            if (startInput && startDate) {
                startInput.value = startDate;
            }
            if (endInput && endDate) {
                endInput.value = endDate;
            }
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
            // 通用下拉框处理（region, department, responsible_user等）
            document.querySelectorAll('select[name="region"], select[name="department"], select[name="responsible_user"]').forEach(select => {
                select.addEventListener('change', (e) => {
                    this.handleSelectChange(e.currentTarget);
                });
            });

            // 地区下拉框特殊处理
            const regionSelect = document.getElementById('regionSelect');
            if (regionSelect) {
                regionSelect.addEventListener('change', (e) => {
                    this.handleRegionSelectChange(e.currentTarget);
                });
            }

            // 部门下拉框特殊处理
            const departmentSelect = document.querySelector('select[name="department"]');
            if (departmentSelect) {
                departmentSelect.addEventListener('change', (e) => {
                    this.handleDepartmentSelectChange(e.currentTarget);
                });
            }

            // 负责人下拉框特殊处理
            const responsibleUserSelect = document.querySelector('select[name="responsible_user"]');
            if (responsibleUserSelect) {
                responsibleUserSelect.addEventListener('change', (e) => {
                    this.handleResponsibleUserSelectChange(e.currentTarget);
                });
            }
        }

        /**
         * 处理下拉框变化（通用）
         */
        handleSelectChange(select) {
            const group = select.closest('.filter-buttons');
            const allBtn = group ? group.querySelector('.filter-btn[data-value=""]') : null;
            
            if (allBtn && select.value === '') {
                // 选择"全部"时，激活"全部"按钮
                if (group) {
                    group.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
                }
                allBtn.classList.add('active');
            } else if (allBtn && select.value !== '') {
                // 选择具体值时，取消"全部"按钮的激活状态
                allBtn.classList.remove('active');
            }
            
            if (this.config.autoSubmit) {
                this.submitForm();
            }
        }

        /**
         * 处理地区下拉框变化
         */
        handleRegionSelectChange(select) {
            const hiddenInput = document.getElementById('filter_region');
            if (hiddenInput) {
                hiddenInput.value = select.value;
            }
            this.updateAllButtonState(select);
            if (this.config.autoSubmit) {
                this.submitForm();
            }
        }

        /**
         * 处理部门下拉框变化
         */
        handleDepartmentSelectChange(select) {
            const hiddenInput = document.getElementById('filter_department');
            if (hiddenInput) {
                hiddenInput.value = select.value;
            }
            this.updateAllButtonState(select);
            if (this.config.autoSubmit) {
                this.submitForm();
            }
        }

        /**
         * 处理负责人下拉框变化
         */
        handleResponsibleUserSelectChange(select) {
            const hiddenInput = document.getElementById('filter_responsible_user');
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
            // 支持的文本输入字段（可根据需要扩展）
            const textInputIds = ['filter_industry', 'filter_company_email', 'filter_legal_representative'];
            
            textInputIds.forEach(inputId => {
                const input = document.getElementById(inputId);
                if (input) {
                    // 输入事件（防抖）
                    input.addEventListener('input', (e) => {
                        this.handleTextInput(e.currentTarget);
                    });
                    
                    // 失去焦点时立即提交
                    input.addEventListener('blur', (e) => {
                        this.handleTextInputBlur(e.currentTarget);
                    });
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
            if (this.debounceTimers[inputId]) {
                clearTimeout(this.debounceTimers[inputId]);
            }
            
            this.debounceTimers[inputId] = setTimeout(() => {
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
            if (this.debounceTimers[inputId]) {
                clearTimeout(this.debounceTimers[inputId]);
            }
            
            // 立即提交表单
            if (this.config.autoSubmit) {
                this.submitForm();
            }
        }

        /**
         * 设置日期范围相关事件
         */
        setupDateRange() {
            // 自定义日期范围输入框变化时提交表单
            const startInput = document.querySelector('input[name="created_time_start"]');
            const endInput = document.querySelector('input[name="created_time_end"]');
            
            if (startInput) {
                startInput.addEventListener('change', () => {
                    if (this.config.autoSubmit) {
                        this.submitForm();
                    }
                });
            }
            
            if (endInput) {
                endInput.addEventListener('change', () => {
                    if (this.config.autoSubmit) {
                        this.submitForm();
                    }
                });
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
                // 提交表单
                if (this.config.autoSubmit) {
                    this.submitForm();
                }
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
    
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            // 只有在页面中存在筛选功能时才自动初始化
            if (shouldAutoInit()) {
                // 如果页面中已有配置，自动初始化
                if (window.listFiltersConfig) {
                    const instance = new ListFilters(window.listFiltersConfig);
                    window.listFiltersInstance = instance;
                } else {
                    // 使用默认配置初始化
                    const instance = new ListFilters();
                    window.listFiltersInstance = instance;
                }
            }
        });
    } else {
        // DOM已加载
        // 只有在页面中存在筛选功能时才自动初始化
        if (shouldAutoInit()) {
            if (window.listFiltersConfig) {
                const instance = new ListFilters(window.listFiltersConfig);
                window.listFiltersInstance = instance;
            } else {
                // 使用默认配置初始化
                const instance = new ListFilters();
                window.listFiltersInstance = instance;
            }
        }
    }

})(window);

