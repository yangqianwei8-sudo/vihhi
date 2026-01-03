/**
 * 部门与人员过滤功能
 * 当选择部门时，自动过滤人员下拉列表为该部门的人员
 * 
 * 使用方法：
 * 1. 在表单中，部门字段的id或name应该包含'department'关键字
 * 2. 人员字段的id或name应该包含'person'或'user'关键字
 * 3. 调用 initDepartmentUserFilter() 初始化
 * 
 * 示例：
 * <select id="id_responsible_department" name="responsible_department">...</select>
 * <select id="id_responsible_person" name="responsible_person">...</select>
 * 
 * <script>
 *   initDepartmentUserFilter('id_responsible_department', 'id_responsible_person');
 * </script>
 */

(function() {
    'use strict';

    /**
     * 根据部门ID获取用户列表
     */
    function fetchUsersByDepartment(departmentId, callback) {
        if (!departmentId) {
            callback([]);
            return;
        }

        const url = `/api/system/users/?department=${departmentId}`;
        
        fetch(url)
            .then(response => {
                if (!response.ok) {
                    throw new Error('获取用户列表失败');
                }
                return response.json();
            })
            .then(data => {
                // 处理分页结果
                const users = data.results || data;
                callback(users);
            })
            .catch(error => {
                console.error('获取用户列表错误:', error);
                callback([]);
            });
    }

    /**
     * 更新人员下拉列表选项
     */
    function updateUserOptions(userSelect, users, currentValue) {
        // 保存当前选中的值
        const selectedValue = currentValue || userSelect.value;
        
        // 清空现有选项（保留第一个空选项）
        const firstOption = userSelect.options[0];
        userSelect.innerHTML = '';
        if (firstOption && firstOption.value === '') {
            userSelect.appendChild(firstOption.cloneNode(true));
        } else {
            // 如果没有空选项，添加一个
            const emptyOption = document.createElement('option');
            emptyOption.value = '';
            emptyOption.textContent = '-- 请选择 --';
            userSelect.appendChild(emptyOption);
        }

        // 添加用户选项
        users.forEach(user => {
            const option = document.createElement('option');
            option.value = user.id;
            
            // 显示用户全名或用户名
            let displayName = '';
            if (user.first_name || user.last_name) {
                displayName = (user.first_name || '') + ' ' + (user.last_name || '').trim();
            }
            if (!displayName || displayName.trim() === '') {
                displayName = user.username || '';
            }
            
            // 如果有部门信息，显示部门名称
            if (user.department_name) {
                displayName += ` (${user.department_name})`;
            }
            
            option.textContent = displayName;
            option.setAttribute('data-user-id', user.id);
            
            // 恢复之前选中的值
            if (selectedValue && String(option.value) === String(selectedValue)) {
                option.selected = true;
            }
            
            userSelect.appendChild(option);
        });

        // 如果没有匹配的用户，触发change事件
        if (users.length === 0 && selectedValue) {
            userSelect.value = '';
            userSelect.dispatchEvent(new Event('change', { bubbles: true }));
        }
    }

    /**
     * 初始化部门-人员过滤功能
     * @param {string|HTMLElement} departmentSelector - 部门选择器的选择器字符串或DOM元素
     * @param {string|HTMLElement} userSelector - 人员选择器的选择器字符串或DOM元素
     * @param {Object} options - 配置选项
     */
    function initDepartmentUserFilter(departmentSelector, userSelector, options = {}) {
        const departmentField = typeof departmentSelector === 'string' 
            ? document.querySelector(departmentSelector) 
            : departmentSelector;
        
        const userField = typeof userSelector === 'string'
            ? document.querySelector(userSelector)
            : userSelector;

        if (!departmentField || !userField) {
            console.warn('部门或人员选择器未找到');
            return;
        }

        // 保存初始用户列表（用于重置）
        const initialUserOptions = Array.from(userField.options).map(opt => ({
            value: opt.value,
            text: opt.textContent,
            selected: opt.selected
        }));

        // 监听部门选择变化
        departmentField.addEventListener('change', function() {
            const departmentId = this.value;
            const currentUserValue = userField.value;

            if (departmentId) {
                // 显示加载状态
                userField.disabled = true;
                const loadingText = options.loadingText || '加载中...';
                userField.innerHTML = `<option value="">${loadingText}</option>`;

                // 获取该部门的用户
                fetchUsersByDepartment(departmentId, function(users) {
                    updateUserOptions(userField, users, currentUserValue);
                    userField.disabled = false;

                    // 触发change事件，通知其他可能依赖的代码
                    userField.dispatchEvent(new Event('change', { bubbles: true }));
                });
            } else {
                // 如果没有选择部门，恢复初始选项
                userField.innerHTML = '';
                initialUserOptions.forEach(opt => {
                    const option = document.createElement('option');
                    option.value = opt.value;
                    option.textContent = opt.text;
                    option.selected = opt.selected;
                    userField.appendChild(option);
                });
                userField.dispatchEvent(new Event('change', { bubbles: true }));
            }
        });

        // 如果部门已有值，初始化时也加载用户
        if (departmentField.value) {
            departmentField.dispatchEvent(new Event('change'));
        }
    }

    /**
     * 自动查找并初始化所有部门-人员过滤
     * 查找所有包含'department'的字段，并查找对应的'person'或'user'字段
     */
    function autoInitDepartmentUserFilters() {
        // 查找所有部门字段
        const departmentFields = document.querySelectorAll('select[id*="department" i], select[name*="department" i]');
        
        departmentFields.forEach(departmentField => {
            const fieldId = departmentField.id || '';
            const fieldName = departmentField.name || '';
            
            // 尝试找到对应的人员字段
            // 常见的命名模式：responsible_department -> responsible_person
            let userFieldId = '';
            let userFieldName = '';
            
            if (fieldId.includes('responsible_department')) {
                userFieldId = fieldId.replace('responsible_department', 'responsible_person');
            } else if (fieldId.includes('department')) {
                userFieldId = fieldId.replace('department', 'person') || fieldId.replace('department', 'user');
            }
            
            if (fieldName.includes('responsible_department')) {
                userFieldName = fieldName.replace('responsible_department', 'responsible_person');
            } else if (fieldName.includes('department')) {
                userFieldName = fieldName.replace('department', 'person') || fieldName.replace('department', 'user');
            }
            
            // 尝试通过ID或name查找人员字段
            let userField = null;
            if (userFieldId) {
                userField = document.getElementById(userFieldId);
            }
            if (!userField && userFieldName) {
                userField = document.querySelector(`select[name="${userFieldName}"]`);
            }
            
            // 如果找到了人员字段，初始化过滤功能
            if (userField) {
                initDepartmentUserFilter(departmentField, userField);
            }
        });
    }

    // 导出函数到全局作用域
    window.initDepartmentUserFilter = initDepartmentUserFilter;
    window.autoInitDepartmentUserFilters = autoInitDepartmentUserFilters;

    // DOM加载完成后自动初始化
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', autoInitDepartmentUserFilters);
    } else {
        autoInitDepartmentUserFilters();
    }
})();

