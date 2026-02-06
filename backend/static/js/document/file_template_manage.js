/**
 * 文件模板管理：弹窗分类选项联动与重置（P3 S1 治理：由模板 inline script 外移）
 */
(function () {
  function getConfig() {
    var el = document.getElementById('fileTemplateManageConfig');
    if (!el || !el.textContent) return {};
    try {
      return JSON.parse(el.textContent);
    } catch (e) {
      return {};
    }
  }

  function updateCategoryOptions(stageCode) {
    var categorySelect = document.getElementById('modal_category');
    if (!categorySelect) return;
    var options = categorySelect.querySelectorAll('option[data-stage]');
    options.forEach(function (option) {
      if (stageCode && option.getAttribute('data-stage') === stageCode) {
        option.classList.remove('d-none');
      } else {
        option.classList.add('d-none');
      }
    });
    categorySelect.value = '';
  }

  function init() {
    var config = getConfig();
    var modal = document.getElementById('createTemplateModal');
    var form = document.getElementById('createTemplateForm');
    if (!modal || !form) return;

    modal.addEventListener('hidden.bs.modal', function () {
      form.reset();
      if (!config.showAll) {
        var stageSelect = document.getElementById('modal_stage');
        if (stageSelect) {
          stageSelect.value = config.stageCode || '';
          updateCategoryOptions(config.stageCode || '');
        }
      }
      var activeCb = document.getElementById('modal_is_active');
      if (activeCb) activeCb.checked = true;
    });

    modal.addEventListener('show.bs.modal', function () {
      if (!config.showAll) {
        var stageSelect = document.getElementById('modal_stage');
        if (stageSelect) {
          stageSelect.value = config.stageCode || '';
          updateCategoryOptions(config.stageCode || '');
        }
      }
    });

    var stageSelect = document.getElementById('modal_stage');
    if (stageSelect) {
      stageSelect.addEventListener('change', function () {
        updateCategoryOptions(this.value);
      });
    }
  }

  window.updateCategoryOptions = updateCategoryOptions;
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
