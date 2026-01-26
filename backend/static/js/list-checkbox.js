/**
 * 列表页面复选框功能
 * 提供全选/取消全选、批量操作等功能
 */
(function() {
    'use strict';

    // 初始化复选框功能
    function initCheckboxFeature() {
        console.log('[复选框] 开始初始化...');
        
        const selectAllCheckbox = document.getElementById('selectAll');
        const rowCheckboxes = document.querySelectorAll('.row-checkbox');
        
        console.log('[复选框] 全选复选框:', selectAllCheckbox);
        console.log('[复选框] 行复选框数量:', rowCheckboxes.length);
        
        // 如果没有全选复选框，不初始化（说明页面没有复选框功能）
        if (!selectAllCheckbox) {
            console.warn('[复选框] 未找到全选复选框，跳过初始化');
            return;
        }

        // 检查复选框是否被禁用
        if (selectAllCheckbox.disabled) {
            console.warn('[复选框] 全选复选框被禁用');
        }

        // 检查复选框的样式
        const selectAllStyles = window.getComputedStyle(selectAllCheckbox);
        console.log('[复选框] 全选复选框样式:', {
            pointerEvents: selectAllStyles.pointerEvents,
            cursor: selectAllStyles.cursor,
            opacity: selectAllStyles.opacity,
            display: selectAllStyles.display,
            visibility: selectAllStyles.visibility,
            zIndex: selectAllStyles.zIndex
        });

        // 如果有行复选框，绑定事件
        if (rowCheckboxes.length > 0) {
            console.log('[复选框] 找到', rowCheckboxes.length, '个行复选框，开始绑定事件');
            
            // 全选/取消全选
            selectAllCheckbox.addEventListener('change', function(e) {
                console.log('[复选框] 全选复选框被点击，状态:', this.checked);
                rowCheckboxes.forEach(function(checkbox) {
                    checkbox.checked = this.checked;
                }, this);
                updateSelectedCount();
            });

            // 单个复选框变化
            rowCheckboxes.forEach(function(checkbox, index) {
                // 检查每个复选框的样式
                const checkboxStyles = window.getComputedStyle(checkbox);
                if (checkboxStyles.pointerEvents === 'none') {
                    console.warn('[复选框] 行复选框', index, 'pointer-events为none');
                }
                
                checkbox.addEventListener('change', function(e) {
                    console.log('[复选框] 行复选框', index, '被点击，状态:', this.checked);
                    updateSelectAllState();
                    updateSelectedCount();
                });
                
                // 添加点击事件监听（作为备用）
                checkbox.addEventListener('click', function(e) {
                    console.log('[复选框] 行复选框', index, '被点击（click事件）');
                });
            });

            // 初始化选中数量
            updateSelectedCount();
            console.log('[复选框] 初始化完成');
        } else {
            console.warn('[复选框] 未找到行复选框');
            // 即使没有行复选框，也要确保全选复选框可以点击（虽然不会有任何效果）
            selectAllCheckbox.addEventListener('change', function() {
                console.log('[复选框] 全选复选框被点击（无行复选框）');
            });
        }
    }

    // 更新全选状态
    function updateSelectAllState() {
        const selectAllCheckbox = document.getElementById('selectAll');
        const rowCheckboxes = document.querySelectorAll('.row-checkbox');
        
        if (!selectAllCheckbox || rowCheckboxes.length === 0) {
            return;
        }

        const allChecked = rowCheckboxes.length > 0 && Array.from(rowCheckboxes).every(function(cb) {
            return cb.checked;
        });
        const someChecked = Array.from(rowCheckboxes).some(function(cb) {
            return cb.checked;
        });
        
        selectAllCheckbox.checked = allChecked;
        selectAllCheckbox.indeterminate = someChecked && !allChecked;
    }

    // 更新选中数量
    function updateSelectedCount() {
        const checked = document.querySelectorAll('.row-checkbox:checked');
        const count = checked.length;
        
        console.log('[复选框] 当前选中数量:', count);
        
        // 触发自定义事件，供其他功能使用
        const event = new CustomEvent('checkboxSelectionChanged', {
            detail: { count: count, selectedIds: getSelectedIds() }
        });
        document.dispatchEvent(event);
    }

    // 获取选中的ID列表
    function getSelectedIds() {
        const checked = document.querySelectorAll('.row-checkbox:checked');
        return Array.from(checked).map(function(cb) {
            return cb.value;
        });
    }

    // 清除所有选择
    function clearSelection() {
        const selectAllCheckbox = document.getElementById('selectAll');
        const rowCheckboxes = document.querySelectorAll('.row-checkbox');
        
        if (selectAllCheckbox) {
            selectAllCheckbox.checked = false;
            selectAllCheckbox.indeterminate = false;
        }
        
        rowCheckboxes.forEach(function(checkbox) {
            checkbox.checked = false;
        });
        
        updateSelectedCount();
    }

    // 导出全局函数
    window.getSelectedIds = getSelectedIds;
    window.clearSelection = clearSelection;
    window.updateSelectedCount = updateSelectedCount;
    window.updateSelectAllState = updateSelectAllState;

    // DOM加载完成后初始化（使用多种方式确保执行）
    function tryInit() {
        try {
            initCheckboxFeature();
        } catch (e) {
            console.error('[复选框] 初始化失败:', e);
            console.error(e.stack);
        }
    }

    // 立即尝试初始化（如果DOM已准备好）
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', tryInit);
    } else {
        // DOM已准备好，立即初始化
        tryInit();
    }

    // 延迟初始化（防止某些情况下DOM还没完全渲染）
    setTimeout(tryInit, 100);
    setTimeout(tryInit, 500);
    setTimeout(tryInit, 1000);
})();
