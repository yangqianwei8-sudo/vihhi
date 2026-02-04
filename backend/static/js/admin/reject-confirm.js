/**
 * Admin 驳回确认页：提交前确认（P3 S1 D-01 治理：从 reject.html 迁出 onclick）
 * 事件：data-action="admin-reject-confirm"
 */
(function() {
  'use strict';
  document.addEventListener('DOMContentLoaded', function() {
    document.addEventListener('click', function(e) {
      var target = e.target && e.target.closest ? e.target.closest('[data-action="admin-reject-confirm"]') : null;
      if (!target) return;
      e.preventDefault();
      var form = document.getElementById('reject-form');
      if (!form) return;
      if (confirm('确定要驳回此审批吗？驳回后无法恢复。')) {
        form.submit();
      }
    });
  });
})();
