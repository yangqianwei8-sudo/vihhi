/**
 * 共享 UI 行为层（P2 第11/12条）
 * 列表页基模相关：批量删除、筛选字段配置注入；事件驱动，禁止 setInterval 轮询。
 */
(function() {
  'use strict';

  function getCsrfToken() {
    var token = document.querySelector('[name=csrfmiddlewaretoken]') && document.querySelector('[name=csrfmiddlewaretoken]').value;
    if (token) return token;
    var meta = document.querySelector('meta[name=csrf-token]') || document.querySelector('meta[name="csrf-token"]');
    if (meta && meta.content) return meta.content;
    function getCookie(name) {
      var cookieValue = null;
      if (document.cookie && document.cookie !== '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
          var c = cookies[i].trim();
          if (c.substring(0, name.length + 1) === (name + '=')) {
            cookieValue = decodeURIComponent(c.substring(name.length + 1));
            break;
          }
        }
      }
      return cookieValue;
    }
    return getCookie('csrftoken') || '';
  }

  function showMessage(message, type) {
    type = type || 'info';
    if (typeof window.showNotification === 'function') {
      window.showNotification(message, type);
    } else if (type === 'success' && typeof window.showSuccess === 'function') {
      window.showSuccess(message);
    } else if (type === 'error' && typeof window.showError === 'function') {
      window.showError(message);
    } else {
      alert(message);
    }
  }

  function getListPageConfig() {
    var el = document.getElementById('listPageConfig');
    if (!el || !el.textContent) return null;
    try {
      return JSON.parse(el.textContent.trim());
    } catch (e) {
      return null;
    }
  }

  function getCreateFormConfig() {
    var el = document.getElementById('createFormConfig');
    if (!el || !el.textContent) return null;
    try {
      return JSON.parse(el.textContent.trim());
    } catch (e) {
      return null;
    }
  }

  function initCreateForm(config) {
    if (!config) return;
    var form = document.getElementById(config.formId || 'createForm');
    if (!form) return;
    if (form.dataset.createFormInitialized === 'true') return;
    form.dataset.createFormInitialized = 'true';

    var headerSubmitButton = document.getElementById(config.submitBtnId || 'headerSubmitButton');
    var draftButton = document.getElementById(config.draftBtnId || 'draftButton');
    var hiddenSubmitButton = document.getElementById(config.hiddenSubmitId || 'hiddenSubmitButton');
    var isDraftField = document.getElementById(config.isDraftFieldId || 'isDraftField');

    function handleDisabledFields() {
      var disabledFields = form.querySelectorAll('[disabled]');
      for (var i = 0; i < disabledFields.length; i++) {
        var field = disabledFields[i];
        if (!field.name) continue;
        var value = '';
        if (field.tagName === 'SELECT') {
          var selectedOption = field.options[field.selectedIndex];
          value = selectedOption ? selectedOption.value : '';
        } else {
          value = field.value || '';
        }
        if (value !== undefined && value !== null) {
          var existingHidden = form.querySelector('input[type="hidden"][name="' + field.name + '"]');
          if (existingHidden) {
            existingHidden.value = value;
          } else {
            var hiddenField = document.createElement('input');
            hiddenField.type = 'hidden';
            hiddenField.name = field.name;
            hiddenField.value = value;
            form.appendChild(hiddenField);
          }
        }
      }
    }

    function submitForm() {
      handleDisabledFields();
      if (hiddenSubmitButton) {
        hiddenSubmitButton.click();
      } else {
        form.submit();
      }
    }

    if (headerSubmitButton) {
      headerSubmitButton.addEventListener('click', function(e) {
        e.preventDefault();
        if (isDraftField) isDraftField.value = '1';
        submitForm();
      });
    }
    if (draftButton) {
      draftButton.addEventListener('click', function(e) {
        e.preventDefault();
        if (isDraftField) isDraftField.value = '1';
        submitForm();
      });
    }

    form.addEventListener('submit', function(e) {
      handleDisabledFields();
      if (config.validateRequired) {
        var requiredFields = form.querySelectorAll('[required]');
        var hasError = false;
        for (var j = 0; j < requiredFields.length; j++) {
          var rf = requiredFields[j];
          if (rf.hasAttribute('disabled')) continue;
          if (!rf.value || rf.value.trim() === '') {
            hasError = true;
            rf.classList.add('is-invalid');
          } else {
            rf.classList.remove('is-invalid');
          }
        }
        if (hasError) {
          e.preventDefault();
          var firstError = form.querySelector('.is-invalid');
          if (firstError) {
            firstError.focus();
            firstError.scrollIntoView({ behavior: 'smooth', block: 'center' });
          }
          return false;
        }
      }
      if (config.scrollRestore) {
        var scrollPosition = window.pageYOffset || document.documentElement.scrollTop || document.body.scrollTop;
        if (typeof sessionStorage !== 'undefined') {
          sessionStorage.setItem('formScrollPosition', scrollPosition);
          sessionStorage.setItem('formSubmitted', 'true');
        }
      }
    });

    if (config.scrollRestore && typeof sessionStorage !== 'undefined') {
      var formSubmitted = sessionStorage.getItem('formSubmitted');
      if (formSubmitted === 'true') {
        sessionStorage.removeItem('formSubmitted');
        setTimeout(function() {
          var selector = config.errorAlertSelector || '.alert-danger, .alert-warning, .alert-info';
          var errorAlert = document.querySelector(selector);
          if (errorAlert) {
            errorAlert.scrollIntoView({ behavior: 'smooth', block: 'center' });
          } else {
            var savedPosition = sessionStorage.getItem('formScrollPosition');
            if (savedPosition) {
              window.scrollTo(0, parseInt(savedPosition, 10));
              sessionStorage.removeItem('formScrollPosition');
            }
          }
        }, 200);
      }
    }
  }

  function updateBatchDeleteButton() {
    var btn = document.getElementById('batchDeleteBtn');
    if (!btn) return;
    var selectedIds = (typeof window.getSelectedIds === 'function') ? window.getSelectedIds() : [];
    var count = selectedIds.length;
    if (count > 0) {
      btn.style.display = 'inline-block';
      var icon = btn.querySelector('i');
      var iconHtml = icon ? icon.outerHTML : '<i class="bi bi-trash"></i>';
      btn.innerHTML = iconHtml + ' 批量删除 (' + count + ')';
    } else {
      btn.style.display = 'none';
      btn.innerHTML = '<i class="bi bi-trash"></i> 批量删除';
    }
  }

  function inferBatchDeleteUrl(config) {
    var url = (config && config.batchDeleteUrl) ? config.batchDeleteUrl.trim() : '';
    if (url) return url;
    var path = window.location.pathname || '';
    if (path.slice(-1) === '/') {
      url = path + 'batch-delete/';
    } else {
      url = path + '/batch-delete/';
    }
    return url;
  }

  function initBatchDelete(config) {
    var batchDeleteBtn = document.getElementById('batchDeleteBtn');
    if (!batchDeleteBtn) return;
    if (batchDeleteBtn.dataset.batchDeleteInitialized === 'true') return;
    batchDeleteBtn.dataset.batchDeleteInitialized = 'true';

    function onSelectionChange() {
      updateBatchDeleteButton();
    }

    document.addEventListener('checkboxSelectionChanged', onSelectionChange, true);
    document.addEventListener('change', function(e) {
      if (e.target && (e.target.classList && e.target.classList.contains('row-checkbox') || e.target.id === 'selectAll')) {
        setTimeout(onSelectionChange, 50);
      }
    }, true);
    document.addEventListener('click', function(e) {
      if (e.target && (e.target.classList && e.target.classList.contains('row-checkbox') || e.target.id === 'selectAll' || (e.target.closest && (e.target.closest('.row-checkbox') || e.target.closest('#selectAll')))) {
        setTimeout(onSelectionChange, 100);
      }
    }, true);

    updateBatchDeleteButton();

    batchDeleteBtn.addEventListener('click', function(e) {
      e.preventDefault();
      e.stopPropagation();
      if (this.disabled) return false;
      var selectedIds = (typeof window.getSelectedIds === 'function') ? window.getSelectedIds() : [];
      if (selectedIds.length === 0) {
        showMessage('请先选择要删除的项目', 'warning');
        return false;
      }
      var confirmMsg = (config && config.batchDeleteConfirmMessage) ? config.batchDeleteConfirmMessage.replace('{count}', selectedIds.length) : ('确定要删除选中的 ' + selectedIds.length + ' 个项目吗？此操作不可恢复！');
      if (!confirm(confirmMsg)) return false;

      var btn = this;
      var deleteUrl = inferBatchDeleteUrl(config);
      if (!deleteUrl || deleteUrl === '/batch-delete/') {
        showMessage('未配置批量删除URL。请在视图函数中设置 batch_delete_url 变量。', 'error');
        return false;
      }

      btn.disabled = true;
      btn.innerHTML = '<i class="bi bi-hourglass-split"></i> 删除中...';
      var csrfToken = getCsrfToken();
      if (!csrfToken) {
        showMessage('无法获取CSRF token，请刷新页面后重试', 'error');
        btn.disabled = false;
        btn.innerHTML = '<i class="bi bi-trash"></i> 批量删除';
        return false;
      }

      var formData = new FormData();
      formData.append('csrfmiddlewaretoken', csrfToken);
      formData.append('ids', selectedIds.join(','));

      if (typeof window.handleBatchDelete === 'function') {
        window.handleBatchDelete(selectedIds, {
          url: deleteUrl,
          csrfToken: csrfToken,
          onSuccess: function() {
            showMessage('批量删除成功', 'success');
            if (typeof window.clearSelection === 'function') window.clearSelection();
            setTimeout(function() { window.location.reload(); }, 500);
          },
          onError: function(err) {
            showMessage('批量删除失败：' + (err && err.message ? err.message : '未知错误'), 'error');
            btn.disabled = false;
            btn.innerHTML = '<i class="bi bi-trash"></i> 批量删除';
          }
        });
        return;
      }

      fetch(deleteUrl, {
        method: 'POST',
        headers: { 'X-CSRFToken': csrfToken, 'X-Requested-With': 'XMLHttpRequest' },
        body: formData,
        credentials: 'same-origin'
      })
      .then(function(res) {
        if (res.ok) return res.json().catch(function() { return { success: true }; });
        return res.json().then(function(data) { throw new Error(data.message || '删除失败'); }).catch(function() { throw new Error('删除失败，状态码：' + res.status); });
      })
      .then(function(data) {
        if (data.success !== false) {
          var n = (data.deleted_count != null) ? data.deleted_count : selectedIds.length;
          showMessage('成功删除 ' + n + ' 个项目', 'success');
          if (typeof window.clearSelection === 'function') window.clearSelection();
          setTimeout(function() { window.location.reload(); }, 500);
        } else {
          throw new Error(data.message || '删除失败');
        }
      })
      .catch(function(err) {
        showMessage('批量删除失败：' + (err && err.message ? err.message : '未知错误'), 'error');
        btn.disabled = false;
        btn.innerHTML = '<i class="bi bi-trash"></i> 批量删除';
      });
    });
  }

  function initListPage() {
    var config = getListPageConfig();
    if (!config) return;

    if (config.enableFilterFieldsSettings) {
      window.filterFieldsSettingsConfig = {
        containerId: config.filterFieldsContainerId || 'filterFieldsContainer',
        storageKey: 'list_page_filter_fields_' + (window.location.pathname || 'default').replace(/\//g, '_'),
        maxEnabledFields: config.filterFieldsMaxEnabled != null ? config.filterFieldsMaxEnabled : 10
      };
    }

    initBatchDelete(config);
  }

  window.updateBatchDeleteButton = updateBatchDeleteButton;

  function run() {
    try {
      initListPage();
    } catch (e) {
      console.error('[ui.js] list page init error:', e);
    }
    try {
      initCreateForm(getCreateFormConfig());
    } catch (e) {
      console.error('[ui.js] create form init error:', e);
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', run);
  } else {
    run();
  }
})();
