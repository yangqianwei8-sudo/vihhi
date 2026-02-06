/**
 * 计划分解页：创建子计划表单提交校验
 */
(function() {
  'use strict';
  function run() {
    var form = document.querySelector('form[action*="plan_create"]');
    if (form) {
      form.addEventListener('submit', function(e) {
        if (!form.checkValidity()) {
          e.preventDefault();
          form.reportValidity();
          return false;
        }
      });
    }
  }
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', run);
  } else {
    run();
  }
})();
