/**
 * 现金流量表报表页：生成报表按钮（P3 S1 治理：由模板 inline script 外移）
 */
(function () {
  function generateReport() {
    var yearEl = document.querySelector('[name="period_year"]');
    var monthEl = document.querySelector('[name="period_month"]');
    var hiddenYear = document.getElementById('hidden_period_year');
    var hiddenMonth = document.getElementById('hidden_period_month');
    var form = document.getElementById('generateForm');
    if (!form || !hiddenYear || !hiddenMonth) return;
    if (yearEl) hiddenYear.value = yearEl.value;
    if (monthEl) hiddenMonth.value = monthEl.value;
    form.submit();
  }

  function init() {
    document.addEventListener('click', function (e) {
      var el = e.target && e.target.closest ? e.target.closest('[data-action="cash-flow-generate-report"]') : null;
      if (el) {
        e.preventDefault();
        generateReport();
      }
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
