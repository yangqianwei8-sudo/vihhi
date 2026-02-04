/**
 * 合同详情页：状态流转弹窗、签章弹窗（P3 D-01 #7 #8 治理：从 contract_detail 迁出）
 * 事件委托：data-action="contract-detail-status-transition" | contract-detail-sign-modal，data-code / data-label
 */
(function() {
  'use strict';

  function showStatusTransitionModal(statusCode, statusLabel) {
    var input = document.getElementById('target_status_input');
    var display = document.getElementById('target_status_display');
    var modalEl = document.getElementById('statusTransitionModal');
    if (input) input.value = statusCode;
    if (display) display.value = statusLabel;
    if (modalEl && typeof bootstrap !== 'undefined') {
      var modal = new bootstrap.Modal(modalEl);
      modal.show();
    }
  }

  function showSignModal(statusCode, statusLabel) {
    var input = document.getElementById('sign_target_status_input');
    var display = document.getElementById('sign_target_status_display');
    var modalEl = document.getElementById('signModal');
    if (input) input.value = statusCode;
    if (display) display.value = statusLabel;
    if (modalEl && typeof bootstrap !== 'undefined') {
      var modal = new bootstrap.Modal(modalEl);
      modal.show();
    }
  }

  document.addEventListener('submit', function(e) {
    var form = e.target && e.target.closest && e.target.closest('form[data-action="contract-detail-delete-confirm"]');
    if (form) {
      var msg = form.getAttribute('data-message') || '确定要删除吗？';
      if (!confirm(msg)) {
        e.preventDefault();
      }
    }
  }, true);

  document.addEventListener('click', function(e) {
    var target = e.target && (e.target.closest ? e.target.closest('[data-action="contract-detail-status-transition"]') : null);
    if (target) {
      e.preventDefault();
      var code = target.getAttribute('data-code');
      var label = target.getAttribute('data-label') || '';
      if (code) showStatusTransitionModal(code, label);
      return;
    }
    target = e.target && (e.target.closest ? e.target.closest('[data-action="contract-detail-sign-modal"]') : null);
    if (target) {
      e.preventDefault();
      var code = target.getAttribute('data-code');
      var label = target.getAttribute('data-label') || '';
      if (code) showSignModal(code, label);
      return;
    }
  });
})();
