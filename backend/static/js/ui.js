/**
 * 共享 UI 行为层（P2 第11/12条）
 * 列表页基模相关：批量删除、筛选字段配置注入；事件驱动，禁止 setInterval 轮询。
 * 两栏基模：Bootstrap CDN 回退加载（读 twoColumnLayoutConfig）。
 */
(function() {
  'use strict';

  function getTwoColumnLayoutConfig() {
    var el = document.getElementById('twoColumnLayoutConfig');
    if (!el || !el.textContent) return null;
    try {
      return JSON.parse(el.textContent.trim());
    } catch (e) {
      return null;
    }
  }

  function loadBootstrapResource(type, urls, index) {
    index = index || 0;
    if (index >= urls.length) return;
    var url = urls[index], el;
    if (type === 'css' || type === 'icons') {
      el = document.createElement('link');
      el.rel = 'stylesheet';
      el.href = url;
      el.onerror = function() {
        if (this.parentNode) this.parentNode.removeChild(this);
        loadBootstrapResource(type, urls, index + 1);
      };
      document.head.appendChild(el);
    } else if (type === 'js') {
      el = document.createElement('script');
      el.src = url;
      el.onerror = function() {
        if (this.parentNode) this.parentNode.removeChild(this);
        loadBootstrapResource(type, urls, index + 1);
      };
      (document.body || document.head).appendChild(el);
    }
  }

  function initTwoColumnLayoutBootstrap() {
    var config = getTwoColumnLayoutConfig();
    if (!config) return;
    var bootstrapCDNs = {
      css: config.css || [],
      icons: config.icons || [],
      js: config.js || []
    };
    loadBootstrapResource('css', bootstrapCDNs.css);
    loadBootstrapResource('icons', bootstrapCDNs.icons);
    loadBootstrapResource('js', bootstrapCDNs.js);
    window.loadBootstrapResource = function(type, urls, index) {
      loadBootstrapResource(type, urls, index);
    };
    window.bootstrapCDNs = bootstrapCDNs;
    if (!window.bootstrap) {
      setTimeout(function() {
        var loadResource = window.loadBootstrapResource;
        if (loadResource && bootstrapCDNs.js && bootstrapCDNs.js.length) {
          loadResource('js', bootstrapCDNs.js);
        }
      }, 2000);
    }
  }

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
      var t = e.target;
      var isRowCheckbox = t && (
        (t.classList && t.classList.contains('row-checkbox')) ||
        t.id === 'selectAll' ||
        (t.closest && (t.closest('.row-checkbox') || t.closest('#selectAll')))
      );
      if (isRowCheckbox) {
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

  function previewImage(imageUrl) {
    if (!imageUrl) return;
    var modal = document.createElement('div');
    modal.className = 'modal fade';
    modal.innerHTML =
      '<div class="modal-dialog modal-lg modal-dialog-centered">' +
        '<div class="modal-content">' +
          '<div class="modal-header"><h5 class="modal-title">图片预览</h5>' +
            '<button type="button" class="btn-close" data-bs-dismiss="modal"></button></div>' +
          '<div class="modal-body text-center">' +
            '<img src="' + imageUrl.replace(/"/g, '&quot;') + '" class="img-fluid" alt="预览图片">' +
          '</div>' +
          '<div class="modal-footer">' +
            '<a href="' + imageUrl.replace(/"/g, '&quot;') + '" download class="btn btn-light"><i class="fas fa-download"></i> 下载图片</a>' +
            '<button type="button" class="btn btn-light" data-bs-dismiss="modal">关闭</button>' +
          '</div>' +
        '</div>' +
      '</div>';
    document.body.appendChild(modal);
    if (typeof bootstrap !== 'undefined' && bootstrap.Modal) {
      var bsModal = new bootstrap.Modal(modal);
      bsModal.show();
      modal.addEventListener('hidden.bs.modal', function() {
        if (modal.parentNode) document.body.removeChild(modal);
      });
    }
  }

  function initDetailBase() {
    var form = document.getElementById('submitApprovalForm');
    var btn = document.getElementById('submitApprovalBtn');
    if (form && btn) {
      form.addEventListener('submit', function(e) {
        if (!confirm('确定要提交审批吗？提交后需要等待审批通过才能启动计划。')) {
          e.preventDefault();
          return false;
        }
        btn.disabled = true;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 提交中...';
      });
    }
    document.addEventListener('click', function(e) {
      var el = e.target && (e.target.closest ? e.target.closest('[data-action="confirm-before-navigate"]') : null);
      if (el && el.getAttribute && el.getAttribute('href')) {
        e.preventDefault();
        var msg = el.getAttribute('data-confirm-message') || '确定要继续吗？';
        if (confirm(msg)) {
          window.location.href = el.getAttribute('href');
        }
      }
      el = e.target && (e.target.closest ? e.target.closest('[data-action="confirm-before-submit"]') : null);
      if (el) {
        e.preventDefault();
        var msg = el.getAttribute('data-confirm-message') || '确定要继续吗？';
        if (confirm(msg)) {
          var form = el.closest('form');
          if (form) form.submit();
        }
      }
      el = e.target && (e.target.closest ? e.target.closest('[data-action="preview-image"]') : null);
      if (el && el.dataset && el.dataset.imageUrl) {
        e.preventDefault();
        previewImage(el.dataset.imageUrl);
      }
      el = e.target && (e.target.closest ? e.target.closest('[data-action="open-feedback-modal"]') : null);
      if (el) {
        e.preventDefault();
        try {
          var modal = document.getElementById('feedbackModal');
          if (!modal) return;
          if (typeof bootstrap !== 'undefined' && bootstrap.Modal) {
            var bsModal = new bootstrap.Modal(modal);
            bsModal.show();
          } else {
            setTimeout(function() {
              if (typeof bootstrap !== 'undefined' && bootstrap.Modal) {
                var bm = new bootstrap.Modal(modal);
                bm.show();
              }
            }, 500);
          }
        } catch (err) {
          console.warn('打开反馈弹窗时出错：', err);
        }
      }
    }, true);
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
      initTwoColumnLayoutBootstrap();
    } catch (e) {
      console.error('[ui.js] two-column bootstrap init error:', e);
    }
    try {
      initDetailBase();
    } catch (e) {
      console.error('[ui.js] detail base init error:', e);
    }
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

  document.addEventListener('change', function(e) {
    var el = e.target && e.target.closest ? e.target.closest('[data-action="submit-parent-form"]') : null;
    if (el && el.form) el.form.submit();
  }, true);

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', run);
  } else {
    run();
  }
})();
