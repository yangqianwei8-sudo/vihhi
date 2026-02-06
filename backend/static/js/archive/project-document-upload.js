/**
 * 项目文档上传页：选择项目、文件校验、表单提交确认
 * 依赖：#projectDocumentUploadConfig（JSON）
 */
(function() {
  'use strict';

  function getConfig() {
    var el = document.getElementById('projectDocumentUploadConfig');
    if (!el || !el.textContent) return null;
    try {
      return JSON.parse(el.textContent.trim());
    } catch (e) {
      return null;
    }
  }

  function run() {
    var config = getConfig();
    if (!config) return;

    var projectSelectId = config.projectSelectId;
    var documentNameId = config.documentNameId;
    var fileInputId = config.fileInputId;
    var formCardSelector = config.formCardSelector || '.form-card';
    var uploadFormId = config.uploadFormId || 'uploadForm';

    function selectProject(projectId, projectName) {
      var projectSelect = document.getElementById(projectSelectId);
      if (projectSelect) {
        projectSelect.value = projectId;
        projectSelect.dispatchEvent(new Event('change'));
      }
      var card = document.querySelector(formCardSelector);
      if (card) {
        var alertDiv = document.createElement('div');
        alertDiv.className = 'alert alert-success alert-dismissible fade show';
        alertDiv.innerHTML = '<i class="bi bi-check-circle"></i> 已选择项目：' + (projectName || '') +
          '<button type="button" class="btn-close" data-bs-dismiss="alert"></button>';
        card.insertBefore(alertDiv, card.firstChild);
      }
      var form = document.querySelector('form');
      if (form) form.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }

    document.addEventListener('click', function(e) {
      var btn = e.target && e.target.closest ? e.target.closest('[data-action="select-project"]') : null;
      if (!btn) return;
      var id = btn.getAttribute('data-project-id');
      var name = (btn.getAttribute('data-project-name') || '').replace(/&quot;/g, '"');
      if (id) selectProject(id, name);
    });

    var fileInput = document.getElementById(fileInputId);
    if (fileInput) {
      fileInput.addEventListener('change', function(e) {
        var file = e.target.files[0];
        if (!file) return;
        var fileSize = (file.size / 1024 / 1024).toFixed(2);
        if (file.size > 100 * 1024 * 1024) {
          alert('文件大小 ' + fileSize + 'MB 超过100MB限制，请选择较小的文件');
          e.target.value = '';
          return;
        }
        var docNameInput = document.getElementById(documentNameId);
        if (docNameInput && !docNameInput.value) {
          docNameInput.value = file.name.replace(/\.[^/.]+$/, '');
        }
      });
    }

    var form = document.getElementById(uploadFormId);
    if (form) {
      form.addEventListener('submit', function(e) {
        var docName = document.getElementById(documentNameId) && document.getElementById(documentNameId).value;
        var fileInputEl = document.getElementById(fileInputId);
        var projectSelect = document.getElementById(projectSelectId);
        if (!(docName && docName.trim())) {
          e.preventDefault();
          alert('请填写文档名称');
          return false;
        }
        if (!fileInputEl || !fileInputEl.files || fileInputEl.files.length === 0) {
          e.preventDefault();
          alert('请选择要上传的文件');
          return false;
        }
        if (!projectSelect || !projectSelect.value) {
          e.preventDefault();
          alert('请选择所属项目');
          return false;
        }
        if (!confirm('确定要上传文档吗？')) {
          e.preventDefault();
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
