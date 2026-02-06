/**
 * 收文列表：阶段/分类联动（P3 S1 治理：由模板 inline script 外移）
 */
(function () {
  function updateCategoryOptions() {
    var stageSelect = document.getElementById('stage_filter');
    var categorySelect = document.getElementById('category_filter');
    if (!stageSelect || !categorySelect) return;
    var selectedStage = stageSelect.value;
    var options = categorySelect.querySelectorAll('option[data-stage]');
    options.forEach(function (option) {
      if (selectedStage === 'all' || option.getAttribute('data-stage') === selectedStage) {
        option.classList.remove('d-none');
      } else {
        option.classList.add('d-none');
        if (option.selected) categorySelect.value = 'all';
      }
    });
  }

  function init() {
    var stageSelect = document.getElementById('stage_filter');
    if (stageSelect) {
      stageSelect.addEventListener('change', updateCategoryOptions);
    }
    updateCategoryOptions();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
