/**
 * 项目创建/编辑页：步骤切换、自动生成编号、服务专业、草稿、提交（P3 S1 C2/C3 治理：create 从 project_create.html，edit 从 project_edit.html 迁出，复用本文件）
 * 事件委托：data-action="project-create-auto-generate-seq" | project-create-cancel | project-create-save-draft | project-create-submit
 * 配置：create 用 projectCreateConfig，edit 用 projectEditConfig（含 pageMode:"edit"）
 */
(function() {
  'use strict';

  var DRAFT_STORAGE_KEY = 'vihhi_project_create_draft';

  function getConfig() {
    var el = document.getElementById('projectEditConfig') || document.getElementById('projectCreateConfig');
    if (!el || !el.textContent) return {};
    try {
      return JSON.parse(el.textContent);
    } catch (e) {
      return {};
    }
  }

  document.addEventListener('click', function(e) {
    var target = e.target && (e.target.closest ? e.target.closest('[data-action="project-create-auto-generate-seq"]') : null);
    if (target) {
      e.preventDefault();
      if (typeof window.projectFormAutoGenerateSeq === 'function') window.projectFormAutoGenerateSeq();
      return;
    }
    target = e.target && (e.target.closest ? e.target.closest('[data-action="project-create-cancel"]') : null);
    if (target) {
      e.preventDefault();
      history.back();
      return;
    }
    target = e.target && (e.target.closest ? e.target.closest('[data-action="project-create-save-draft"]') : null);
    if (target) {
      e.preventDefault();
      if (typeof window.projectFormSaveDraft === 'function') window.projectFormSaveDraft();
      return;
    }
    target = e.target && (e.target.closest ? e.target.closest('[data-action="project-create-submit"]') : null);
    if (target) {
      e.preventDefault();
      if (typeof window.projectFormSubmit === 'function') window.projectFormSubmit();
      return;
    }
  }, true);

  document.addEventListener('DOMContentLoaded', function() {
    var cfg = getConfig();
    var professionOptions = cfg.serviceProfessionsMap || {};
    var preselectedProfessionIds = new Set(Array.isArray(cfg.selectedProfessionIds) ? cfg.selectedProfessionIds : []);

    /* ---------- 编辑页分支（C3：复用本文件，不新建第二 js） ---------- */
    if (cfg.pageMode === 'edit') {
      var projectFormEdit = document.getElementById('projectForm');
      var containerEdit = document.getElementById('professionOptions');
      function updateProfessionOptionsEdit(serviceTypeId) {
        if (!containerEdit) return;
        containerEdit.innerHTML = '';
        var options = professionOptions[String(serviceTypeId)] || [];
        options.forEach(function(profession) {
          var div = document.createElement('div');
          div.className = 'form-check form-check-inline';
          div.innerHTML = '<input class="form-check-input" type="checkbox" name="service_profession_ids[]" id="prof_' + profession.id + '" value="' + profession.id + '" data-required="true">' +
            '<label class="form-check-label" for="prof_' + profession.id + '">' + profession.name + '</label>';
          containerEdit.appendChild(div);
        });
        options.forEach(function(profession) {
          var checkbox = document.getElementById('prof_' + profession.id);
          if (checkbox && preselectedProfessionIds.has(profession.id)) checkbox.checked = true;
        });
      }
      document.querySelectorAll('input[name="service_type"]').forEach(function(radio) {
        radio.addEventListener('change', function() { updateProfessionOptionsEdit(this.value); });
      });
      var nameInputEdit = document.querySelector('input[name="name"]');
      if (nameInputEdit) {
        nameInputEdit.addEventListener('input', function() {
          var nameCount = document.getElementById('nameCount');
          if (nameCount) nameCount.textContent = this.value.length;
        });
        var nameCountEl = document.getElementById('nameCount');
        if (nameCountEl) nameCountEl.textContent = nameInputEdit.value.length;
      }
      window.projectFormSaveDraft = function() {
        document.getElementById('formAction').value = 'draft';
        if (projectFormEdit) projectFormEdit.submit();
      };
      window.projectFormSubmit = function() {
        var serviceType = document.querySelector('input[name="service_type"]:checked');
        var businessType = document.querySelector('select[name="business_type"]');
        var designStage = document.querySelector('select[name="design_stage"]');
        var selectedProfessions = document.querySelectorAll('input[name="service_profession_ids[]"]:checked');
        var isValid = true;
        if (!serviceType) { alert('请选择服务类型'); isValid = false; }
        if (!businessType || !businessType.value) { alert('请选择项目业态'); isValid = false; }
        if (!designStage || !designStage.value) { alert('请选择图纸阶段'); isValid = false; }
        if (!selectedProfessions.length) { alert('请选择至少一个服务专业'); isValid = false; }
        if (isValid) {
          document.querySelectorAll('[data-required="true"]').forEach(function(el) { el.setAttribute('required', 'required'); });
          document.getElementById('formAction').value = 'submit';
          if (projectFormEdit) projectFormEdit.submit();
        }
      };
      var activeServiceType = document.querySelector('input[name="service_type"]:checked');
      if (!activeServiceType) {
        var radios = document.querySelectorAll('input[name="service_type"]');
        if (radios.length) { radios[0].checked = true; activeServiceType = radios[0]; }
      }
      if (activeServiceType) updateProfessionOptionsEdit(activeServiceType.value);
      return;
    }

    /* ---------- 创建页逻辑 ---------- */
    var steps = Array.from(document.querySelectorAll('[data-step-content]'));
    var stepButtons = Array.from(document.querySelectorAll('.stepper__step'));
    var projectForm = document.getElementById('projectForm');
    var projectYearInput = document.getElementById('projectYear');
    var projectNumberSeq = document.getElementById('projectNumberSeq');
    var projectNumberHint = document.getElementById('projectNumberHint');
    var serviceTypeSelect = document.getElementById('serviceTypeSelect');
    var subsidiarySelect = document.getElementById('subsidiarySelect');
    var contractAmountInput = document.getElementById('contractAmountInput');
    var contractDateInput = document.getElementById('contractDateInput');
    var contractFileInput = document.getElementById('contractFileInput');
    var uploadProgress = document.getElementById('uploadProgress');
    var uploadProgressBar = document.getElementById('uploadProgressBar');
    var uploadProgressText = document.getElementById('uploadProgressText');
    var validationList = document.getElementById('validationList');
    var historyList = document.getElementById('historyList');
    var lastSavedLabel = document.getElementById('lastSaved');
    var nameInput = document.getElementById('projectNameInput');
    var aliasInput = document.getElementById('projectAliasInput');
    var currentStep = 0;
    var autoSaveTimer = null;

    function updateStep(newStep) {
      if (newStep < 0 || newStep >= steps.length) return;
      steps[currentStep].hidden = true;
      stepButtons[currentStep].classList.remove('stepper__step--active');
      currentStep = newStep;
      steps[currentStep].hidden = false;
      stepButtons[currentStep].classList.add('stepper__step--active');
      var prevBtn = document.getElementById('prevStepBtn');
      var nextBtn = document.getElementById('nextStepBtn');
      var submitBtn = document.getElementById('submitBtn');
      var stepProgress = document.getElementById('stepProgress');
      if (prevBtn) prevBtn.disabled = currentStep === 0;
      if (nextBtn) nextBtn.hidden = currentStep === steps.length - 1;
      if (submitBtn) submitBtn.hidden = currentStep !== steps.length - 1;
      if (stepProgress) stepProgress.style.width = ((currentStep + 1) / steps.length * 100) + '%';
    }

    stepButtons.forEach(function(btn) {
      btn.addEventListener('click', function() { updateStep(parseInt(btn.dataset.step, 10)); });
    });
    var nextBtn = document.getElementById('nextStepBtn');
    var prevBtn = document.getElementById('prevStepBtn');
    if (nextBtn) nextBtn.addEventListener('click', function() { updateStep(currentStep + 1); });
    if (prevBtn) prevBtn.addEventListener('click', function() { updateStep(currentStep - 1); });

    var toggleProjectSeq = document.getElementById('toggleProjectSeq');
    if (toggleProjectSeq) {
      toggleProjectSeq.addEventListener('click', function() {
        var isReadOnly = projectNumberSeq.hasAttribute('readonly');
        if (isReadOnly) {
          projectNumberSeq.removeAttribute('readonly');
          projectNumberSeq.focus();
          toggleProjectSeq.innerHTML = '<i class="bi bi-check"></i>';
        } else {
          projectNumberSeq.setAttribute('readonly', 'readonly');
          toggleProjectSeq.innerHTML = '<i class="bi bi-pencil-square"></i>';
          checkProjectNumber();
        }
      });
    }

    function buildProjectNumber() {
      var seq = (projectNumberSeq.value || '001').trim();
      while (seq.length < 3) seq = '0' + seq;
      return 'VIH-' + projectYearInput.value + '-' + seq;
    }

    window.projectFormAutoGenerateSeq = function() {
      var year = projectYearInput.value;
      var url = new URL('/api/project/api/projects/get_next_number/', window.location.origin);
      url.searchParams.set('year', year);
      fetch(url)
        .then(function(r) { return r.json(); })
        .then(function(data) {
          var seq = data.next_seq ? String(data.next_seq) : '001';
          while (seq.length < 3) seq = '0' + seq;
          projectNumberSeq.value = seq;
          projectNumberSeq.setAttribute('readonly', 'readonly');
          if (toggleProjectSeq) toggleProjectSeq.innerHTML = '<i class="bi bi-pencil-square"></i>';
          checkProjectNumber();
        })
        .catch(function() {
          projectNumberSeq.value = '001';
          if (projectNumberHint) {
            projectNumberHint.textContent = '获取编号失败，请稍后重试';
            projectNumberHint.className = 'form-text text-danger';
          }
          updateValidationState('project_number', false);
        });
    };

    function checkProjectNumber() {
      var number = buildProjectNumber();
      var regex = /^VIH-\d{4}-\d{3}$/;
      if (!regex.test(number)) {
        if (projectNumberHint) {
          projectNumberHint.textContent = '项目编号格式应为 VIH-YYYY-NNN';
          projectNumberHint.className = 'form-text text-danger';
        }
        updateValidationState('project_number', false);
        return;
      }
      var url = new URL('/api/project/api/projects/check_project_number/', window.location.origin);
      url.searchParams.set('project_number', number);
      fetch(url)
        .then(function(r) { return r.json(); })
        .then(function(data) {
          if (data.valid) {
            if (projectNumberHint) {
              projectNumberHint.textContent = '项目编号可用';
              projectNumberHint.className = 'form-text text-success';
            }
            updateValidationState('project_number', true);
          } else {
            if (projectNumberHint) {
              projectNumberHint.textContent = '项目编号已存在，请重新生成';
              projectNumberHint.className = 'form-text text-danger';
            }
            updateValidationState('project_number', false);
          }
        })
        .catch(function() {
          if (projectNumberHint) {
            projectNumberHint.textContent = '无法验证项目编号，请稍后再试';
            projectNumberHint.className = 'form-text text-warning';
          }
          updateValidationState('project_number', false);
        });
    }

    function updateProfessionOptions(serviceTypeId) {
      var container = document.getElementById('professionList');
      if (!container) return;
      var keyStr = String(serviceTypeId);
      var keyNum = Number.isFinite(parseInt(serviceTypeId, 10)) ? parseInt(serviceTypeId, 10) : null;
      var options = professionOptions[keyStr] || (keyNum !== null ? professionOptions[keyNum] : []) || [];
      var code = serviceTypeSelect && serviceTypeSelect.selectedOptions && serviceTypeSelect.selectedOptions[0] ? (serviceTypeSelect.selectedOptions[0].dataset && serviceTypeSelect.selectedOptions[0].dataset.code) || '' : '';
      var allowMap = {
        result_optimization: ['结构', '构造', '地库减面积', '地库加车位', '停车效率', '节能', '门窗栏杆', '幕墙', '总坪景观', '电气', '给排水', '暖通', '市政道路'],
        process_optimization: ['结构', '停车效率'],
        detailed_review: ['建筑', '结构', '电气', '给排水', '暖通'],
        process_consulting: ['建筑', '结构', '电气', '给排水', '暖通'],
        full_process_consulting: ['建筑', '结构', '电气', '给排水', '暖通']
      };
      var allowList = allowMap[code];
      if (Array.isArray(allowList) && allowList.length) options = options.filter(function(p) { return allowList.indexOf(p.name) !== -1; });
      container.innerHTML = '';
      options.forEach(function(prof) {
        var label = document.createElement('label');
        label.className = 'profession-item';
        label.title = prof.description || '专业服务';
        label.innerHTML = '<input type="checkbox" name="service_profession_ids[]" value="' + prof.id + '"><span>' + prof.name + '</span>';
        var input = label.querySelector('input');
        input.addEventListener('change', updateProfessionSummary);
        if (preselectedProfessionIds.has(prof.id)) input.checked = true;
        container.appendChild(label);
      });
      updateProfessionSummary();
    }

    function updateProfessionSummary() {
      var selected = document.querySelectorAll('input[name="service_profession_ids[]"]:checked');
      var el = document.getElementById('professionSummary');
      if (el) el.textContent = '已选择 ' + selected.length + ' 项专业';
      updateValidationState('service_professions', selected.length > 0);
    }

    var businessSelect = document.getElementById('businessTypeSelect');
    var businessOther = document.getElementById('businessTypeOther');
    if (businessSelect) {
      businessSelect.addEventListener('change', function() {
        var isOther = businessSelect.value === 'other';
        businessOther.hidden = !isOther;
        if (!isOther) businessOther.value = '';
        updateValidationState('business_type', !!businessSelect.value);
      });
      updateValidationState('business_type', !!businessSelect.value);
      if (businessSelect.value === 'other' && businessOther) businessOther.hidden = false;
    }

    window.projectFormSaveDraft = function() {
      document.getElementById('formAction').value = 'draft';
      localStorage.setItem(DRAFT_STORAGE_KEY, JSON.stringify(serializeForm()));
      updateHistory('手动保存草稿');
      if (lastSavedLabel) lastSavedLabel.textContent = '最后保存：' + new Date().toLocaleString();
      projectForm.submit();
    };

    window.projectFormSubmit = function() {
      if (!serviceTypeSelect || !serviceTypeSelect.value) {
        alert('请选择服务类型');
        updateValidationState('service_type', false);
        return;
      }
      if (document.querySelectorAll('input[name="service_profession_ids[]"]:checked').length === 0) {
        alert('请选择至少一个服务专业');
        updateValidationState('service_professions', false);
        return;
      }
      checkProjectNumber();
      document.getElementById('formAction').value = 'submit';
      localStorage.removeItem(DRAFT_STORAGE_KEY);
      projectForm.submit();
    };

    function updateValidationState(field, valid) {
      if (!validationList) return;
      var item = validationList.querySelector('[data-field="' + field + '"] span');
      if (!item) return;
      if (valid) {
        item.className = 'badge bg-success';
        item.textContent = '已完成';
      } else {
        item.className = 'badge bg-danger';
        item.textContent = '待填写';
      }
    }

    function updateHistory(action) {
      if (!historyList) return;
      var entry = document.createElement('div');
      entry.className = 'small text-muted';
      entry.textContent = new Date().toLocaleString() + ' · ' + action;
      historyList.insertBefore(entry, historyList.firstChild);
    }

    function serializeForm() {
      var formData = new FormData(projectForm);
      var data = {};
      formData.forEach(function(value, key) {
        if (data[key]) {
          if (!Array.isArray(data[key])) data[key] = [data[key]];
          data[key].push(value);
        } else {
          data[key] = value;
        }
      });
      data.project_number = buildProjectNumber();
      return data;
    }

    function populateForm(data) {
      Object.keys(data).forEach(function(key) {
        if (key === 'project_number') {
          var parts = data[key].split('-');
          if (parts.length === 3) {
            projectYearInput.value = parts[1];
            projectNumberSeq.value = parts[2];
          }
          return;
        }
        var value = data[key];
        if (Array.isArray(value)) {
          var inputs = projectForm.querySelectorAll('[name="' + key + '"]');
          inputs.forEach(function(input) {
            if (input.type === 'checkbox' || input.type === 'radio') input.checked = value.indexOf(input.value) !== -1;
          });
        } else {
          var input = projectForm.querySelector('[name="' + key + '"]');
          if (input) input.value = value;
        }
      });
    }

    function restoreDraft() {
      var raw = localStorage.getItem(DRAFT_STORAGE_KEY);
      if (!raw) return false;
      try {
        var data = JSON.parse(raw);
        populateForm(data);
        if (data['service_profession_ids[]']) {
          var values = Array.isArray(data['service_profession_ids[]']) ? data['service_profession_ids[]'] : [data['service_profession_ids[]']];
          preselectedProfessionIds = new Set(values.filter(Boolean).map(function(v) { return parseInt(v, 10); }).filter(function(n) { return Number.isFinite(n); }));
        }
        updateProfessionOptions(serviceTypeSelect ? serviceTypeSelect.value : '');
        updateHistory('已恢复草稿');
        if (lastSavedLabel) lastSavedLabel.textContent = '最后保存：' + new Date().toLocaleString();
        return true;
      } catch (e) {
        console.warn('无法恢复草稿', e);
        return false;
      }
    }

    function scheduleAutoSave() {
      clearTimeout(autoSaveTimer);
      autoSaveTimer = setTimeout(function() {
        localStorage.setItem(DRAFT_STORAGE_KEY, JSON.stringify(serializeForm()));
        updateHistory('自动保存草稿');
        if (lastSavedLabel) lastSavedLabel.textContent = '最后保存：' + new Date().toLocaleString();
      }, 1000);
    }

    function handleFormChange(e) {
      var name = e.target.name;
      if (name === 'service_type') {
        preselectedProfessionIds = new Set(Array.from(document.querySelectorAll('input[name="service_profession_ids[]"]:checked')).map(function(el) { return parseInt(el.value, 10); }));
        updateValidationState('service_type', true);
        updateProfessionOptions(e.target.value);
      }
      if (name === 'business_type') updateValidationState('business_type', !!businessSelect && businessSelect.value);
      if (name === 'service_profession_ids[]') updateProfessionSummary();
      if (name === 'subsidiary') {
        updateValidationState('subsidiary', !!subsidiarySelect && subsidiarySelect.value);
        window.projectFormAutoGenerateSeq();
      }
      if (name === 'project_number_seq') checkProjectNumber();
      scheduleAutoSave();
    }

    projectForm.addEventListener('input', handleFormChange, { capture: true });
    projectForm.addEventListener('change', handleFormChange, { capture: true });
    projectForm.addEventListener('submit', function() { localStorage.removeItem(DRAFT_STORAGE_KEY); });

    if (serviceTypeSelect) {
      updateProfessionOptions(serviceTypeSelect.value);
      serviceTypeSelect.addEventListener('change', function(e) { updateProfessionOptions(e.target.value); });
    }

    if (contractFileInput && uploadProgress && uploadProgressBar && uploadProgressText) {
      var resetUploadProgress = function() {
        uploadProgressBar.style.width = '0%';
        uploadProgressBar.setAttribute('aria-valuenow', 0);
        uploadProgressBar.textContent = '0%';
        uploadProgressText.textContent = '等待选择文件';
        uploadProgress.hidden = true;
      };
      resetUploadProgress();
      contractFileInput.addEventListener('change', function() {
        var file = contractFileInput.files && contractFileInput.files[0];
        if (!file) { resetUploadProgress(); return; }
        uploadProgress.hidden = false;
        uploadProgressBar.style.width = '0%';
        uploadProgressBar.setAttribute('aria-valuenow', 0);
        uploadProgressBar.textContent = '0%';
        uploadProgressText.textContent = file.name + ' · ' + (file.size / (1024 * 1024)).toFixed(2) + ' MB';
        var reader = new FileReader();
        reader.onloadstart = function() {
          uploadProgressBar.style.width = '0%';
          uploadProgressBar.textContent = '0%';
        };
        reader.onprogress = function(event) {
          if (event.lengthComputable) {
            var percent = Math.round((event.loaded / event.total) * 100);
            uploadProgressBar.style.width = percent + '%';
            uploadProgressBar.setAttribute('aria-valuenow', percent);
            uploadProgressBar.textContent = percent + '%';
          }
        };
        reader.onloadend = function() {
          uploadProgressBar.style.width = '100%';
          uploadProgressBar.setAttribute('aria-valuenow', 100);
          uploadProgressBar.textContent = '100%';
          uploadProgressText.textContent = file.name + ' 上传准备完成';
        };
        reader.onerror = function() { uploadProgressText.textContent = '读取文件失败，请重新选择'; };
        reader.readAsArrayBuffer(file);
      });
      projectForm.addEventListener('submit', function() {
        if (!uploadProgress.hidden) uploadProgressText.textContent = '正在上传，请稍候...';
      });
    }

    if (contractAmountInput) {
      contractAmountInput.dataset.raw = contractAmountInput.value.replace(/[^\d.]/g, '');
      contractAmountInput.addEventListener('input', function(e) {
        var cleaned = e.target.value.replace(/[^\d.]/g, '');
        e.target.dataset.raw = cleaned;
      });
      contractAmountInput.addEventListener('blur', function() {
        var amount = parseFloat(contractAmountInput.dataset.raw || '0', 10);
        contractAmountInput.value = amount ? amount.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : '';
      });
      contractAmountInput.addEventListener('focus', function() {
        contractAmountInput.value = contractAmountInput.dataset.raw || '';
      });
    }

    if (contractDateInput) {
      contractDateInput.addEventListener('change', function() { updateHistory('更新签约日期'); });
    }

    if (subsidiarySelect) updateValidationState('subsidiary', !!subsidiarySelect.value);
    if (serviceTypeSelect) updateValidationState('service_type', !!serviceTypeSelect.value);

    if (nameInput) {
      nameInput.addEventListener('input', function() {
        var text = nameInput.value.trim();
        var nameCount = document.getElementById('nameCount');
        if (nameCount) nameCount.textContent = text.length;
        updateValidationState('name', text.length > 0);
        if (aliasInput && !aliasInput.value) aliasInput.placeholder = text ? text.slice(0, 10) + ' 项目' : '如：天府商业综合体';
      });
      updateValidationState('name', !!nameInput.value.trim());
      var nameCount = document.getElementById('nameCount');
      if (nameCount) nameCount.textContent = nameInput.value.trim().length;
    }

    updateProfessionSummary();
    updateStep(0);
    var restored = restoreDraft();
    if (!projectNumberSeq.value) window.projectFormAutoGenerateSeq();
    if (serviceTypeSelect) updateProfessionOptions(serviceTypeSelect.value);
  });
})();
