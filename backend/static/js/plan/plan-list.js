/**
 * 计划列表页：筛选配置注入、删除确认、复选框全选/行选（P3 S1 C5 治理：从 plan_list.html 迁出）
 * 事件委托：data-action="plan-list-confirm-delete"
 * 配置：<script type="application/json" id="planListConfig">（含 listFiltersConfig 与 selectFieldNames 等）
 */
(function() {
  'use strict';

  (function injectListFiltersConfig() {
    var el = document.getElementById('planListConfig');
    if (!el || !el.textContent) return;
    try {
      var cfg = JSON.parse(el.textContent);
      if (cfg.selectFieldNames || cfg.dateStartFieldName || cfg.dateEndFieldName) {
        window.listFiltersConfig = {
          selectFieldNames: cfg.selectFieldNames || ['status', 'plan_type', 'plan_period', 'responsible_person', 'related_goal'],
          dateStartFieldName: cfg.dateStartFieldName || 'date_from',
          dateEndFieldName: cfg.dateEndFieldName || 'date_to'
        };
      }
    } catch (e) {}
  })();

  document.addEventListener('click', function(e) {
    var target = e.target && (e.target.closest ? e.target.closest('[data-action="plan-list-confirm-delete"]') : null);
    if (target) {
      e.preventDefault();
      var href = target.getAttribute('href');
      if (href && confirm('确定要删除此计划吗？')) {
        window.location.href = href;
      }
      return;
    }
  }, true);

  var observer = null;
  var initAttempts = 0;
  var MAX_INIT_ATTEMPTS = 10;

  function updateSelectAllState() {
    var selectAll = document.getElementById('selectAll');
    var rowCheckboxes = document.querySelectorAll('.row-checkbox');
    if (!selectAll || rowCheckboxes.length === 0) return;
    var allChecked = rowCheckboxes.length > 0 && Array.from(rowCheckboxes).every(function(cb) { return cb.checked; });
    var someChecked = Array.from(rowCheckboxes).some(function(cb) { return cb.checked; });
    selectAll.checked = allChecked;
    selectAll.indeterminate = someChecked && !allChecked;
  }

  function updateSelectedCount() {
    var checked = document.querySelectorAll('.row-checkbox:checked');
    var count = checked.length;
    var event = new CustomEvent('checkboxSelectionChanged', {
      detail: { count: count, selectedIds: Array.from(checked).map(function(cb) { return cb.value; }) }
    });
    document.dispatchEvent(event);
  }

  function bindSelectAllCheckbox(selectAll) {
    var newSelectAll = selectAll.cloneNode(true);
    selectAll.parentNode.replaceChild(newSelectAll, selectAll);
    var selectAllRef = newSelectAll;
    selectAllRef.addEventListener('change', function(e) {
      e.stopPropagation();
      var checked = this.checked;
      document.querySelectorAll('.row-checkbox').forEach(function(cb) { cb.checked = checked; });
      updateSelectedCount();
    });
    selectAllRef.addEventListener('click', function(e) {
      e.stopPropagation();
      setTimeout(function() {
        var checked = selectAllRef.checked;
        document.querySelectorAll('.row-checkbox').forEach(function(cb) { cb.checked = checked; });
        updateSelectedCount();
      }, 0);
    });
  }

  function bindRowCheckboxes(checkboxes) {
    checkboxes.forEach(function(cb) {
      if (cb.dataset.planListInitialized === 'true') return;
      cb.dataset.planListInitialized = 'true';
      cb.addEventListener('change', function(e) {
        e.stopPropagation();
        updateSelectAllState();
        updateSelectedCount();
      });
      cb.addEventListener('click', function(e) {
        e.stopPropagation();
        setTimeout(function() {
          updateSelectAllState();
          updateSelectedCount();
        }, 0);
      });
    });
  }

  function exportGlobalFunctions(selectAll) {
    window.getSelectedIds = function() {
      return Array.from(document.querySelectorAll('.row-checkbox:checked')).map(function(cb) { return cb.value; });
    };
    window.clearSelection = function() {
      if (selectAll) {
        selectAll.checked = false;
        selectAll.indeterminate = false;
      }
      document.querySelectorAll('.row-checkbox').forEach(function(cb) { cb.checked = false; });
      updateSelectedCount();
    };
    window.updateSelectedCount = updateSelectedCount;
    window.updateSelectAllState = updateSelectAllState;
  }

  function initPlanListCheckboxes() {
    var selectAll = document.getElementById('selectAll');
    var rowCheckboxes = document.querySelectorAll('.row-checkbox');
    if (!selectAll) {
      if (initAttempts < MAX_INIT_ATTEMPTS) { initAttempts++; return false; }
      return true;
    }
    if (selectAll.dataset.planListInitialized === 'true') {
      var uninitialized = Array.from(rowCheckboxes).filter(function(cb) { return cb.dataset.planListInitialized !== 'true'; });
      if (uninitialized.length > 0) bindRowCheckboxes(uninitialized);
      return true;
    }
    if (rowCheckboxes.length === 0) {
      selectAll.dataset.planListInitialized = 'true';
      bindSelectAllCheckbox(selectAll);
      exportGlobalFunctions(selectAll);
      return true;
    }
    selectAll.dataset.planListInitialized = 'true';
    bindSelectAllCheckbox(selectAll);
    bindRowCheckboxes(Array.from(rowCheckboxes));
    exportGlobalFunctions(selectAll);
    updateSelectAllState();
    updateSelectedCount();
    return true;
  }

  function tryInit() {
    try {
      var success = initPlanListCheckboxes();
      if (success) initAttempts = MAX_INIT_ATTEMPTS;
    } catch (e) {
      console.error('[计划列表] 复选框初始化失败:', e);
    }
  }

  function setupMutationObserver() {
    var tableBody = document.querySelector('.list-table tbody');
    if (!tableBody) return;
    if (observer) observer.disconnect();
    observer = new MutationObserver(function(mutations) {
      var shouldReinit = false;
      mutations.forEach(function(mutation) {
        if (mutation.addedNodes.length === 0) return;
        for (var i = 0; i < mutation.addedNodes.length; i++) {
          var node = mutation.addedNodes[i];
          if (node.nodeType === 1) {
            if (node.classList && node.classList.contains('row-checkbox')) shouldReinit = true;
            else if (node.querySelector && node.querySelector('.row-checkbox')) shouldReinit = true;
          }
        }
      });
      if (shouldReinit) setTimeout(tryInit, 100);
    });
    observer.observe(tableBody, { childList: true, subtree: true });
  }

  tryInit();
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() {
      tryInit();
      setupMutationObserver();
    });
  } else {
    setupMutationObserver();
  }
  setTimeout(tryInit, 100);
  setTimeout(tryInit, 500);
  setTimeout(function() {
    tryInit();
    setupMutationObserver();
  }, 1000);
})();
