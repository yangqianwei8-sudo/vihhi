/**
 * 列表页面复选框功能（按表格作用域，支持多表无 ID 冲突）
 * 提供全选/取消全选、批量操作等功能。
 * 依赖：表头用 class="js-select-all" data-table="表格ID"，行用 class="row-checkbox" data-table="表格ID"，表格用 data-table-id="表格ID"。
 */
(function() {
    'use strict';

    function getTableId(tableEl) {
        return tableEl && tableEl.getAttribute('data-table-id');
    }

    function getRowCheckboxesInTable(tableEl, tableId) {
        if (!tableEl || !tableId) return [];
        return Array.from(tableEl.querySelectorAll('.row-checkbox[data-table="' + tableId + '"]'));
    }

    function getSelectAllInTable(tableEl, tableId) {
        if (!tableEl || !tableId) return null;
        return tableEl.querySelector('.js-select-all[data-table="' + tableId + '"]');
    }

    // 初始化单个表格内的复选框功能
    function initTableCheckbox(tableEl) {
        const tableId = getTableId(tableEl);
        if (!tableId) return;

        const selectAllCheckbox = getSelectAllInTable(tableEl, tableId);
        const rowCheckboxes = getRowCheckboxesInTable(tableEl, tableId);

        if (!selectAllCheckbox) return;

        if (selectAllCheckbox.dataset.checkboxInitialized === 'true') {
            const uninitialized = rowCheckboxes.filter(function(cb) {
                return cb.dataset.checkboxInitialized !== 'true';
            });
            if (uninitialized.length > 0) bindRowCheckboxesInTable(uninitialized, tableEl, tableId);
            return;
        }

        selectAllCheckbox.dataset.checkboxInitialized = 'true';

        selectAllCheckbox.addEventListener('change', function() {
            const current = getRowCheckboxesInTable(tableEl, tableId);
            current.forEach(function(checkbox) {
                checkbox.checked = this.checked;
            }, this);
            updateSelectedCount();
        });

        if (rowCheckboxes.length > 0) {
            bindRowCheckboxesInTable(rowCheckboxes, tableEl, tableId);
            updateSelectedCount();
        } else {
            selectAllCheckbox.addEventListener('change', function() {
                const current = getRowCheckboxesInTable(tableEl, tableId);
                if (current.length > 0) {
                    current.forEach(function(checkbox) {
                        checkbox.checked = this.checked;
                    }, this);
                    updateSelectedCount();
                }
            });
        }
    }

    // 初始化所有带 data-table-id 的表格
    function initCheckboxFeature() {
        const tables = document.querySelectorAll('table[data-table-id]');
        tables.forEach(function(tableEl) {
            initTableCheckbox(tableEl);
        });
        // 兼容旧版：无 data-table-id 时按页内唯一 .js-select-all 初始化（仅一个表时等效）
        if (tables.length === 0) {
            const legacySelectAll = document.querySelector('.js-select-all');
            if (legacySelectAll) {
                const tableEl = legacySelectAll.closest('table');
                if (tableEl) {
                    tableEl.setAttribute('data-table-id', 'dataTable');
                    initTableCheckbox(tableEl);
                }
            }
        }
    }
    
    function bindRowCheckboxesInTable(checkboxes, tableEl, tableId) {
        checkboxes.forEach(function(checkbox) {
            if (checkbox.dataset.checkboxInitialized === 'true') return;
            checkbox.dataset.checkboxInitialized = 'true';

            checkbox.addEventListener('change', function() {
                updateSelectAllStateInTable(tableEl, tableId);
                updateSelectedCount();
            });
            checkbox.addEventListener('click', function() {
                setTimeout(function() {
                    updateSelectAllStateInTable(tableEl, tableId);
                    updateSelectedCount();
                }, 0);
            });
        });
    }

    function updateSelectAllStateInTable(tableEl, tableId) {
        const selectAllCheckbox = getSelectAllInTable(tableEl, tableId);
        const rowCheckboxes = getRowCheckboxesInTable(tableEl, tableId);
        if (!selectAllCheckbox || rowCheckboxes.length === 0) return;

        const allChecked = rowCheckboxes.every(function(cb) { return cb.checked; });
        const someChecked = rowCheckboxes.some(function(cb) { return cb.checked; });
        selectAllCheckbox.checked = allChecked;
        selectAllCheckbox.indeterminate = someChecked && !allChecked;
    }

    function updateSelectAllState() {
        document.querySelectorAll('table[data-table-id]').forEach(function(tableEl) {
            const tableId = getTableId(tableEl);
            if (tableId) updateSelectAllStateInTable(tableEl, tableId);
        });
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

    function clearSelection() {
        document.querySelectorAll('table[data-table-id]').forEach(function(tableEl) {
            const tableId = getTableId(tableEl);
            const selectAllCheckbox = getSelectAllInTable(tableEl, tableId);
            const rowCheckboxes = getRowCheckboxesInTable(tableEl, tableId);
            if (selectAllCheckbox) {
                selectAllCheckbox.checked = false;
                selectAllCheckbox.indeterminate = false;
            }
            rowCheckboxes.forEach(function(checkbox) {
                checkbox.checked = false;
            });
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
    
    function setupMutationObserver() {
        const tables = document.querySelectorAll('table[data-table-id]');
        if (tables.length === 0) return null;

        tables.forEach(function(tableEl) {
            const tbody = tableEl.querySelector('tbody');
            if (!tbody) return;

            const observer = new MutationObserver(function(mutations) {
                let shouldReinit = false;
                mutations.forEach(function(mutation) {
                    if (mutation.addedNodes.length === 0) return;
                    mutation.addedNodes.forEach(function(node) {
                        if (node.nodeType === 1) {
                            if (node.classList && node.classList.contains('row-checkbox')) shouldReinit = true;
                            else if (node.querySelector && node.querySelector('.row-checkbox')) shouldReinit = true;
                        }
                    });
                });
                if (shouldReinit) setTimeout(tryInit, 50);
            });
            observer.observe(tbody, { childList: true, subtree: true });
        });
        return null;
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
