/**
 * 审批详情三栏页：审批表单提交校验（P3 S1 B3 治理：从 approval_detail_three_column.html 迁出）
 */
(function() {
  'use strict';

  document.addEventListener('DOMContentLoaded', function() {
    var approvalForm = document.getElementById('approvalForm');
    if (!approvalForm) return;
    approvalForm.addEventListener('submit', function(e) {
      var action = (e.submitter && e.submitter.value) || (e.target.querySelector && e.target.querySelector('button[type="submit"][name="action"]') && e.target.querySelector('button[type="submit"][name="action"]').value);
      if (action === 'approve' || action === 'reject') {
        var commentEl = document.getElementById('approval_comment');
        var comment = (commentEl && commentEl.value) ? commentEl.value.trim() : '';
        if (!comment) {
          e.preventDefault();
          alert('请输入审批意见');
          return false;
        }
        if (!confirm('确认' + (action === 'approve' ? '通过' : '驳回') + '此审批吗？')) {
          e.preventDefault();
          return false;
        }
      }
    });
  });
})();
