/**
 * 文件分类管理页：创建分类弹窗的 show/hidden 时重置表单与回填默认值（stage_code/showAll）
 * 依赖：页面内 #fileCategoryManageConfig（JSON）、#createCategoryModal、#createCategoryForm
 */
(function() {
  'use strict';

  function getConfig() {
    var el = document.getElementById('fileCategoryManageConfig');
    if (!el || !el.textContent) return null;
    try {
      return JSON.parse(el.textContent.trim());
    } catch (e) {
      return null;
    }
  }

  function run() {
    var modal = document.getElementById('createCategoryModal');
    var form = document.getElementById('createCategoryForm');
    if (!modal || !form) return;

    var config = getConfig();
    var showAll = config && config.showAll === true;
    var stageCode = (config && config.stageCode) ? config.stageCode : '';

    var modalName = document.getElementById('modal_name');
    var modalIsActive = document.getElementById('modal_is_active');

    modal.addEventListener('hidden.bs.modal', function() {
      form.reset();
      if (modalName) modalName.value = showAll ? '' : stageCode;
      if (modalIsActive) modalIsActive.checked = true;
    });

    modal.addEventListener('show.bs.modal', function() {
      if (!showAll && modalName) modalName.value = stageCode;
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', run);
  } else {
    run();
  }
})();
