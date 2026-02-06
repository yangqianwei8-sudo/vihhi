/**
 * 资产负债表页：生成报表按钮委托（读查询表单年月 → 填 hidden → 提交 generateForm）
 * 依赖：页面内 #queryForm（name="period_year" / period_month）、#generateForm、hidden_period_year、hidden_period_month
 */
(function() {
  'use strict';

  document.addEventListener('click', function(e) {
    var btn = e.target && e.target.closest ? e.target.closest('[data-action="balance-sheet-generate"]') : null;
    if (!btn) return;
    var queryForm = document.getElementById('queryForm');
    var form = document.getElementById('generateForm');
    var hiddenYear = document.getElementById('hidden_period_year');
    var hiddenMonth = document.getElementById('hidden_period_month');
    if (!queryForm || !form || !hiddenYear || !hiddenMonth) return;
    var yearEl = queryForm.querySelector('[name="period_year"]');
    var monthEl = queryForm.querySelector('[name="period_month"]');
    if (yearEl) hiddenYear.value = yearEl.value;
    if (monthEl) hiddenMonth.value = monthEl.value;
    form.submit();
  });
})();
