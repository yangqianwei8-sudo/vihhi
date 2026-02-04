/**
 * 交付列表页：筛选、全选、刷新、搜索回车提交（P3 S1 D-01 治理：从 delivery_list.html 迁出）
 * 事件委托：data-action="delivery-list-reload"
 */
(function() {
  'use strict';

  document.addEventListener('DOMContentLoaded', function() {
    var filterForm = document.getElementById('filterForm');
    var searchForm = document.getElementById('searchForm');
    var searchInput = document.getElementById('searchInput');

    // 刷新按钮：data-action="delivery-list-reload"
    document.addEventListener('click', function(e) {
      var target = e.target && e.target.closest ? e.target.closest('[data-action="delivery-list-reload"]') : null;
      if (target) {
        e.preventDefault();
        location.reload();
        return;
      }
    });

    // 搜索框回车提交
    if (searchInput && searchForm) {
      searchInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter') {
          e.preventDefault();
          searchForm.submit();
        }
      });
    }

    // 筛选按钮点击
    document.querySelectorAll('.filter-btn').forEach(function(btn) {
      btn.addEventListener('click', function() {
        var filterKey = this.getAttribute('data-filter');
        var filterValue = this.getAttribute('data-value');
        var hiddenInput = document.getElementById('filter_' + filterKey);

        if (hiddenInput) {
          hiddenInput.value = filterValue;
        }

        var filterRow = this.closest('.filter-row');
        if (filterRow) {
          filterRow.querySelectorAll('.filter-btn').forEach(function(b) {
            b.classList.remove('active');
          });
        }
        this.classList.add('active');

        if (filterForm) {
          filterForm.submit();
        }
      });
    });

    // 下拉框变化时提交表单
    var projectSelect = document.getElementById('projectSelect');
    if (projectSelect) {
      projectSelect.addEventListener('change', function() {
        var filterProject = document.getElementById('filter_project_id');
        if (filterProject) {
          filterProject.value = this.value;
        }
        if (filterForm) filterForm.submit();
      });
    }

    var clientSelect = document.getElementById('clientSelect');
    if (clientSelect) {
      clientSelect.addEventListener('change', function() {
        var filterClient = document.getElementById('filter_client_id');
        if (filterClient) {
          filterClient.value = this.value;
        }
        if (filterForm) filterForm.submit();
      });
    }

    // 筛选栏折叠/展开
    var toggleFilterBtn = document.getElementById('toggleFilterCollapse');
    var basicFilters = document.getElementById('basicFilters');
    var filterCollapseText = document.getElementById('filterCollapseText');
    var filterCollapseIcon = document.getElementById('filterCollapseIcon');

    if (toggleFilterBtn && basicFilters) {
      toggleFilterBtn.addEventListener('click', function() {
        if (basicFilters.style.display === 'none') {
          basicFilters.style.display = 'block';
          if (filterCollapseText) filterCollapseText.textContent = '收起';
          if (filterCollapseIcon) filterCollapseIcon.textContent = '▲';
        } else {
          basicFilters.style.display = 'none';
          if (filterCollapseText) filterCollapseText.textContent = '展开';
          if (filterCollapseIcon) filterCollapseIcon.textContent = '▼';
        }
      });
    }

    // 全选/取消全选
    var selectAll = document.getElementById('selectAll');
    var rowCheckboxes = document.querySelectorAll('.row-checkbox');

    function updateSelectedCount() {
      var selectedCount = document.querySelectorAll('.row-checkbox:checked').length;
      var countElement = document.getElementById('selectedCount');
      var clearSelectionBtn = document.getElementById('clearSelection');
      var batchBtns = document.querySelectorAll('#batchExportBtn, #batchDeleteBtn');

      if (countElement) {
        countElement.textContent = selectedCount;
      }

      if (clearSelectionBtn) {
        clearSelectionBtn.style.display = selectedCount > 0 ? 'block' : 'none';
      }

      batchBtns.forEach(function(btn) {
        btn.disabled = selectedCount === 0;
      });
    }

    function updateSelectAllState() {
      var allChecked = rowCheckboxes.length > 0 && Array.prototype.every.call(rowCheckboxes, function(cb) {
        return cb.checked;
      });
      if (selectAll) {
        selectAll.checked = allChecked;
      }
    }

    if (selectAll) {
      selectAll.addEventListener('change', function() {
        rowCheckboxes.forEach(function(checkbox) {
          checkbox.checked = this.checked;
        }, this);
        updateSelectedCount();
      });
    }

    rowCheckboxes.forEach(function(checkbox) {
      checkbox.addEventListener('change', function() {
        updateSelectedCount();
        updateSelectAllState();
      });
    });

    var clearSelectionBtn = document.getElementById('clearSelection');
    if (clearSelectionBtn) {
      clearSelectionBtn.addEventListener('click', function() {
        rowCheckboxes.forEach(function(checkbox) {
          checkbox.checked = false;
        });
        if (selectAll) {
          selectAll.checked = false;
        }
        updateSelectedCount();
      });
    }
  });
})();
