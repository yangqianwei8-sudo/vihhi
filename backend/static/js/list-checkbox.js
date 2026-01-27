/**
 * 列表页面复选框功能
 * 提供全选/取消全选、批量操作等功能
 */
(function() {
    'use strict';

    // 初始化复选框功能
    function initCheckboxFeature() {
        const selectAllCheckbox = document.getElementById('selectAll');
        const rowCheckboxes = document.querySelectorAll('.row-checkbox');
        
        // 如果没有全选复选框，不初始化（说明页面没有复选框功能）
        if (!selectAllCheckbox) {
            return; // 静默返回，不输出警告
        }

        // 如果全选复选框已初始化，检查是否有新的行复选框需要绑定
        if (selectAllCheckbox.dataset.checkboxInitialized === 'true') {
            // 检查是否有未初始化的行复选框
            const uninitializedCheckboxes = Array.from(rowCheckboxes).filter(function(cb) {
                return cb.dataset.checkboxInitialized !== 'true';
            });
            
            if (uninitializedCheckboxes.length > 0) {
                bindRowCheckboxes(uninitializedCheckboxes);
            }
            return;
        }

        // 标记为已初始化
        selectAllCheckbox.dataset.checkboxInitialized = 'true';

        // 如果有行复选框，绑定事件
        if (rowCheckboxes.length > 0) {
            // 全选/取消全选
            selectAllCheckbox.addEventListener('change', function(e) {
                const currentRowCheckboxes = document.querySelectorAll('.row-checkbox');
                currentRowCheckboxes.forEach(function(checkbox) {
                    checkbox.checked = this.checked;
                }, this);
                updateSelectedCount();
            });

            // 绑定行复选框
            bindRowCheckboxes(Array.from(rowCheckboxes));

            // 初始化选中数量
            updateSelectedCount();
        } else {
            // 即使没有行复选框，也要绑定全选复选框事件（等待数据加载）
            selectAllCheckbox.addEventListener('change', function() {
                const currentRowCheckboxes = document.querySelectorAll('.row-checkbox');
                if (currentRowCheckboxes.length > 0) {
                    currentRowCheckboxes.forEach(function(checkbox) {
                        checkbox.checked = this.checked;
                    }, this);
                    updateSelectedCount();
                }
            });
        }
    }
    
    // 绑定行复选框事件（独立函数，便于重用）
    function bindRowCheckboxes(checkboxes) {
        checkboxes.forEach(function(checkbox, index) {
            // 如果已初始化，跳过
            if (checkbox.dataset.checkboxInitialized === 'true') {
                return;
            }
            
            // 标记为已初始化
            checkbox.dataset.checkboxInitialized = 'true';
            
            checkbox.addEventListener('change', function(e) {
                updateSelectAllState();
                updateSelectedCount();
            });
            
            // 添加点击事件监听（作为备用）
            checkbox.addEventListener('click', function(e) {
                setTimeout(function() {
                    updateSelectAllState();
                    updateSelectedCount();
                }, 0);
            });
        });
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
    
    // 使用 MutationObserver 监听 DOM 变化，当有新的行复选框添加时重新初始化
    function setupMutationObserver() {
        const tableBody = document.querySelector('.list-table tbody') || 
                         document.querySelector('table tbody') ||
                         document.querySelector('tbody');
        
        if (!tableBody) {
            return null;
        }
        
        const observer = new MutationObserver(function(mutations) {
            let shouldReinit = false;
            
            mutations.forEach(function(mutation) {
                // 检查是否有新节点添加
                if (mutation.addedNodes.length > 0) {
                    mutation.addedNodes.forEach(function(node) {
                        if (node.nodeType === 1) { // Element node
                            // 检查是否是行复选框或包含行复选框的元素
                            if (node.classList && node.classList.contains('row-checkbox')) {
                                shouldReinit = true;
                            } else if (node.querySelector && node.querySelector('.row-checkbox')) {
                                shouldReinit = true;
                            }
                        }
                    });
                }
            });
            
            if (shouldReinit) {
                setTimeout(tryInit, 50);
            }
        });
        
        observer.observe(tableBody, {
            childList: true,
            subtree: true
        });
        
        return observer;
    }

    // 立即尝试初始化（如果DOM已准备好）
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            tryInit();
            setupMutationObserver();
        });
    } else {
        // DOM已准备好，立即初始化
        tryInit();
        setupMutationObserver();
    }

    // 延迟初始化（防止某些情况下DOM还没完全渲染）
    setTimeout(function() {
        tryInit();
        setupMutationObserver();
    }, 100);
    setTimeout(function() {
        tryInit();
        setupMutationObserver();
    }, 500);
    setTimeout(function() {
        tryInit();
        setupMutationObserver();
    }, 1000);
})();
