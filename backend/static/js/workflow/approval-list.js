/**
 * 审批列表页：批量审批、立即审批、撤回、导出占位、列设置（P3 S1 B1 治理：从 approval_list.html 迁出）
 * 事件委托：data-action="workflow-export-placeholder" | workflow-load-approval-modal | workflow-approval-withdraw
 */
(function() {
  'use strict';

  function loadApprovalModal(instanceId) {
    var modal = document.getElementById('approvalModal' + instanceId);
    if (modal) {
      // 可在此加载额外数据
    }
  }

  document.addEventListener('click', function(e) {
    var el = e.target && (e.target.closest ? e.target.closest('[data-action="workflow-export-placeholder"]') : null);
    if (el) {
      e.preventDefault();
      alert('导出功能开发中');
      return;
    }
    el = e.target && (e.target.closest ? e.target.closest('[data-action="workflow-load-approval-modal"]') : null);
    if (el && el.dataset && el.dataset.instanceId) {
      loadApprovalModal(el.dataset.instanceId);
    }
    el = e.target && (e.target.closest ? e.target.closest('[data-action="workflow-approval-withdraw"]') : null);
    if (el && el.dataset && el.dataset.withdrawUrl) {
      e.preventDefault();
      if (confirm('确定要撤回此审批吗？')) {
        window.location.href = el.dataset.withdrawUrl;
      }
    }
  }, true);

  document.addEventListener('DOMContentLoaded', function() {
    var batchApproveBtn = document.getElementById('batchApproveBtn');
    var batchRejectBtn = document.getElementById('batchRejectBtn');
    var batchApproveForm = document.getElementById('batchApproveForm');
    var selectAllCheckbox = document.getElementById('selectAll');
    var rowCheckboxes = document.querySelectorAll('.row-checkbox');
    var selectedCountSpan = document.getElementById('selectedCount');

    function updateBatchActions() {
      var checked = document.querySelectorAll('.row-checkbox:checked');
      if (checked.length > 0 && batchApproveForm) {
        batchApproveForm.style.display = 'block';
        if (selectedCountSpan) selectedCountSpan.textContent = checked.length;
      } else if (batchApproveForm) {
        batchApproveForm.style.display = 'none';
      }
    }

    if (selectAllCheckbox) {
      selectAllCheckbox.addEventListener('change', function() {
        for (var i = 0; i < rowCheckboxes.length; i++) rowCheckboxes[i].checked = this.checked;
        updateBatchActions();
      });
    }
    for (var i = 0; i < rowCheckboxes.length; i++) {
      rowCheckboxes[i].addEventListener('change', function() {
        updateBatchActions();
        if (selectAllCheckbox) {
          var allChecked = true;
          for (var j = 0; j < rowCheckboxes.length; j++) {
            if (!rowCheckboxes[j].checked) { allChecked = false; break; }
          }
          selectAllCheckbox.checked = allChecked;
        }
      });
    }

    function batchApprove(action) {
      var checked = document.querySelectorAll('.row-checkbox:checked');
      if (checked.length === 0) {
        alert('请至少选择一个审批实例');
        return;
      }
      if (!confirm('确定要' + (action === 'approve' ? '批量通过' : '批量驳回') + ' ' + checked.length + ' 个审批吗？')) return;
      var actionInput = document.getElementById('batchAction');
      if (actionInput) actionInput.value = action;
      var existingInputs = batchApproveForm.querySelectorAll('input[name="instance_ids"][type="hidden"]');
      for (var k = 0; k < existingInputs.length; k++) existingInputs[k].remove();
      for (var k = 0; k < checked.length; k++) {
        var hiddenInput = document.createElement('input');
        hiddenInput.type = 'hidden';
        hiddenInput.name = 'instance_ids';
        hiddenInput.value = checked[k].value;
        batchApproveForm.appendChild(hiddenInput);
      }
      batchApproveForm.submit();
    }

    if (batchApproveBtn && batchApproveForm) {
      batchApproveBtn.addEventListener('click', function() { batchApprove('approve'); });
    }
    if (batchRejectBtn && batchApproveForm) {
      batchRejectBtn.addEventListener('click', function() { batchApprove('reject'); });
    }

    /* 列设置：仅当存在对应 DOM 时初始化 */
    var STORAGE_KEY = 'approval_list_column_settings';
    var columnKeys = ['checkbox', 'instance_number', 'workflow_name', 'applicant', 'apply_time', 'status', 'current_node', 'content_object', 'actions'];

    function loadColumnSettings() {
      try {
        var saved = localStorage.getItem(STORAGE_KEY);
        if (saved) return JSON.parse(saved);
      } catch (err) {}
      return null;
    }
    function saveColumnSettings(settings) {
      try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(settings));
        return true;
      } catch (err) { return false; }
    }
    function applyColumnSettings() {
      var settings = loadColumnSettings();
      if (!settings) return;
      var table = document.querySelector('.list-table');
      if (!table) return;
      var headerRow = table.querySelector('thead tr');
      var rows = table.querySelectorAll('tbody tr');
      if (!headerRow) return;
      var headers = headerRow.querySelectorAll('th');
      for (var i = 0; i < headers.length && i < columnKeys.length; i++) {
        var visible = settings[columnKeys[i]] !== false;
        headers[i].style.display = visible ? '' : 'none';
      }
      for (var r = 0; r < rows.length; r++) {
        var cells = rows[r].querySelectorAll('td');
        for (var c = 0; c < cells.length && c < columnKeys.length; c++) {
          var vis = settings[columnKeys[c]] !== false;
          cells[c].style.display = vis ? '' : 'none';
        }
      }
    }
    function initColumnSettingsModal() {
      var modal = document.getElementById('fieldsSettingsModal');
      if (!modal) return;
      var settings = loadColumnSettings();
      var toggles = modal.querySelectorAll('.column-toggle');
      for (var t = 0; t < toggles.length; t++) {
        var col = toggles[t].dataset.column;
        toggles[t].checked = (settings && settings[col] !== false);
      }
    }

    var settingsBtn = document.getElementById('tableColumnSettingsBtn');
    var modalElement = document.getElementById('fieldsSettingsModal');
    if (settingsBtn && modalElement) {
      settingsBtn.addEventListener('click', function(ev) {
        ev.preventDefault();
        initColumnSettingsModal();
        if (typeof bootstrap !== 'undefined' && bootstrap.Modal) {
          var modal = new bootstrap.Modal(modalElement, { backdrop: true, keyboard: true });
          modal.show();
        }
      });
      modalElement.addEventListener('show.bs.modal', initColumnSettingsModal);

      var saveBtn = document.getElementById('saveColumnSettings');
      if (saveBtn) {
        saveBtn.addEventListener('click', function() {
          var settings = {};
          var toggles = document.querySelectorAll('#columnSettingsList .column-toggle');
          for (var i = 0; i < toggles.length; i++) {
            var col = toggles[i].dataset.column;
            settings[col] = toggles[i].checked;
          }
          if (saveColumnSettings(settings)) {
            applyColumnSettings();
            if (typeof bootstrap !== 'undefined' && bootstrap.Modal) {
              var inst = bootstrap.Modal.getInstance(modalElement);
              if (inst) inst.hide();
            }
            alert('列设置已保存');
          } else alert('保存失败，请重试');
        });
      }
      var resetBtn = document.getElementById('resetColumnSettings');
      if (resetBtn) {
        resetBtn.addEventListener('click', function() {
          if (confirm('确定要重置为默认设置吗？')) {
            localStorage.removeItem(STORAGE_KEY);
            var toggles = document.querySelectorAll('#columnSettingsList .column-toggle');
            for (var i = 0; i < toggles.length; i++) {
              if (!toggles[i].disabled) toggles[i].checked = true;
            }
            applyColumnSettings();
            alert('已重置为默认设置');
          }
        });
      }
      applyColumnSettings();
    }
  });
})();
