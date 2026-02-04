/**
 * 计划表单页：表单提交验证、计划列表 Formset 增删折叠、结束时间自动计算、周计划错误模态框（P3 S1 C1 治理：从 plan_form.html 迁出）
 * 事件委托：data-action="plan-form-add-item" | plan-form-toggle-item | plan-form-remove-item
 * 配置：<script type="application/json" id="planFormConfig">
 */
(function() {
  'use strict';

  function getConfig() {
    var el = document.getElementById('planFormConfig');
    if (!el || !el.textContent) return {};
    try {
      return JSON.parse(el.textContent);
    } catch (e) {
      return {};
    }
  }

  function calculateEndDateByPeriod(startDateObj, planPeriod) {
    var endDate = new Date(startDateObj);
    switch (planPeriod) {
      case 'yearly':
        endDate.setFullYear(endDate.getFullYear() + 1);
        endDate.setDate(endDate.getDate() - 1);
        break;
      case 'quarterly':
        endDate.setMonth(endDate.getMonth() + 3);
        endDate.setDate(endDate.getDate() - 1);
        break;
      case 'monthly':
        endDate.setMonth(endDate.getMonth() + 1);
        endDate.setDate(endDate.getDate() - 1);
        break;
      case 'weekly':
        endDate.setDate(endDate.getDate() + 6);
        break;
      case 'daily':
        endDate.setDate(endDate.getDate() + 1);
        break;
      default:
        return startDateObj;
    }
    return endDate;
  }

  function formatDateString(dateObj) {
    var year = dateObj.getFullYear();
    var month = String(dateObj.getMonth() + 1).padStart(2, '0');
    var day = String(dateObj.getDate()).padStart(2, '0');
    return year + '-' + month + '-' + day;
  }

  function calculateEndTime(startInput, endInput, planPeriod) {
    var startDate = startInput.value.trim();
    if (!startDate || !planPeriod) return;
    var startDateObj = new Date(startDate);
    if (isNaN(startDateObj.getTime())) return;
    var endDate = calculateEndDateByPeriod(startDateObj, planPeriod);
    endInput.value = formatDateString(endDate);
  }

  document.addEventListener('click', function(e) {
    var target = e.target && (e.target.closest ? e.target.closest('[data-action="plan-form-add-item"]') : null);
    if (target) {
      e.preventDefault();
      var container = document.getElementById('planItemsContainer');
      var cfg = getConfig();
      if (container && typeof window.planFormAddItem === 'function') {
        window.planFormAddItem();
      }
      return;
    }
    target = e.target && (e.target.closest ? e.target.closest('[data-action="plan-form-toggle-item"]') : null);
    if (target) {
      e.preventDefault();
      if (typeof window.planFormToggleItem === 'function') {
        window.planFormToggleItem(target);
      }
      return;
    }
    target = e.target && (e.target.closest ? e.target.closest('[data-action="plan-form-remove-item"]') : null);
    if (target) {
      e.preventDefault();
      if (typeof window.planFormRemoveItem === 'function') {
        window.planFormRemoveItem(target);
      }
      return;
    }
  }, true);

  document.addEventListener('DOMContentLoaded', function() {
    var cfg = getConfig();
    var form = document.getElementById('createForm');
    if (form) {
      form.addEventListener('submit', function(e) {
        var formsetCards = document.querySelectorAll('#planItemsContainer .plan-item-card');
        var errors = [];
        var hasValidPlan = false;
        var visibleIndex = 0;
        formsetCards.forEach(function(card) {
          var deleteCheckbox = card.querySelector('input[type="checkbox"][name*="DELETE"]');
          if (deleteCheckbox && deleteCheckbox.checked) return;
          var name = card.querySelector('input[name*="name"]');
          var relatedGoal = card.querySelector('select[name*="related_goal"]');
          var content = card.querySelector('textarea[name*="content"]');
          var planObjective = card.querySelector('input[name*="plan_objective"]');
          var startTime = card.querySelector('input[name*="start_time"]');
          var endTime = card.querySelector('input[name*="end_time"]');
          var hasData = (name && name.value.trim()) ||
            (relatedGoal && relatedGoal.value) ||
            (content && content.value.trim()) ||
            (planObjective && planObjective.value.trim()) ||
            (startTime && startTime.value) ||
            (endTime && endTime.value);
          if (hasData) {
            hasValidPlan = true;
            var rowNum = visibleIndex + 1;
            if (!name || !name.value.trim()) errors.push('第 ' + rowNum + ' 行：计划名称不能为空');
            if (!relatedGoal || !relatedGoal.value) errors.push('第 ' + rowNum + ' 行：关联战略目标不能为空');
            if (!content || !content.value.trim()) errors.push('第 ' + rowNum + ' 行：计划内容不能为空');
            if (!planObjective || !planObjective.value.trim()) errors.push('第 ' + rowNum + ' 行：计划目标不能为空');
            if (!startTime || !startTime.value) errors.push('第 ' + rowNum + ' 行：开始时间不能为空');
            if (!endTime || !endTime.value) errors.push('第 ' + rowNum + ' 行：结束时间不能为空');
            if (startTime && startTime.value && endTime && endTime.value) {
              var startDate = new Date(startTime.value);
              var endDate = new Date(endTime.value);
              if (isNaN(startDate.getTime()) || isNaN(endDate.getTime())) {
                errors.push('第 ' + rowNum + ' 行：日期格式无效');
              } else if (endDate <= startDate) {
                errors.push('第 ' + rowNum + ' 行：结束时间必须晚于开始时间');
              }
            }
            visibleIndex++;
          }
        });
        if (!hasValidPlan && formsetCards.length > 0) errors.push('请至少填写一个完整的计划信息');
        if (errors.length > 0) {
          e.preventDefault();
          alert('❌ 表单验证失败\n\n' + errors.join('\n') + '\n\n请填写完整后重新提交。');
          return false;
        }
      });
    }

    if (cfg.showWeeklyPlanError) {
      var modalEl = document.getElementById('weeklyPlanErrorModal');
      if (modalEl && typeof bootstrap !== 'undefined' && bootstrap.Modal) {
        var modal = new bootstrap.Modal(modalEl);
        modal.show();
      }
    }

    var container = document.getElementById('planItemsContainer');
    var totalFormCount = (cfg.totalFormCount | 0) || 0;
    var formPrefix = cfg.formPrefix || 'planitems';
    var getParentPlanOptionsUrl = cfg.getParentPlanOptionsUrl || '';

    if (!container || totalFormCount === 0) return;

    var planItemFormCount = totalFormCount;

    function updatePlanItemFormIndexes() {
      var cards = container.querySelectorAll('.plan-item-card');
      var visibleIndex = 0;
      cards.forEach(function(card) {
        var deleteCheckbox = card.querySelector('input[type="checkbox"][name*="DELETE"]');
        if (deleteCheckbox && deleteCheckbox.checked) return;
        card.dataset.formIndex = visibleIndex;
        var title = card.querySelector('h5');
        if (title) title.textContent = '计划 ' + (visibleIndex + 1);
        card.querySelectorAll('input, select, textarea').forEach(function(field) {
          if (field.name && field.name.indexOf(formPrefix) !== -1) {
            var nameParts = field.name.split('-');
            if (nameParts.length >= 3 && nameParts[0] === formPrefix) {
              var fieldName = nameParts.slice(2).join('-');
              field.name = formPrefix + '-' + visibleIndex + '-' + fieldName;
              if (field.id) {
                var idParts = field.id.split('-');
                if (idParts.length >= 3 && idParts[0] === 'id' && idParts[1] === formPrefix) {
                  field.id = 'id_' + formPrefix + '-' + visibleIndex + '-' + fieldName;
                }
              }
            }
          }
        });
        visibleIndex++;
      });
      var totalFormsInput = document.querySelector('input[name="' + formPrefix + '-TOTAL_FORMS"]');
      if (totalFormsInput) totalFormsInput.value = visibleIndex;
    }

    function initExpandCollapseState() {
      var cards = container.querySelectorAll('.plan-item-card');
      cards.forEach(function(card, index) {
        var deleteCheckbox = card.querySelector('input[type="checkbox"][name*="DELETE"]');
        if (deleteCheckbox && deleteCheckbox.checked) return;
        var toggleBtn = card.querySelector('.toggle-expand-btn');
        var details = card.querySelector('.plan-item-details');
        if (toggleBtn && details) {
          if (index === 0) {
            details.classList.add('plan-item-details--expanded');
            toggleBtn.dataset.expanded = 'true';
            var icon = toggleBtn.querySelector('i');
            if (icon) {
              icon.classList.remove('bi-chevron-down');
              icon.classList.add('bi-chevron-up');
            }
          } else {
            details.classList.remove('plan-item-details--expanded');
            toggleBtn.dataset.expanded = 'false';
            var icon2 = toggleBtn.querySelector('i');
            if (icon2) {
              icon2.classList.remove('bi-chevron-up');
              icon2.classList.add('bi-chevron-down');
            }
          }
        }
      });
    }

    window.planFormToggleItem = function(btn) {
      var card = btn.closest('.plan-item-card');
      if (!card) return;
      var details = card.querySelector('.plan-item-details');
      var icon = btn.querySelector('i');
      var isExpanded = btn.dataset.expanded === 'true';
      if (isExpanded) {
        details.classList.remove('plan-item-details--expanded');
        btn.dataset.expanded = 'false';
        if (icon) {
          icon.classList.remove('bi-chevron-up');
          icon.classList.add('bi-chevron-down');
        }
      } else {
        details.classList.add('plan-item-details--expanded');
        btn.dataset.expanded = 'true';
        if (icon) {
          icon.classList.remove('bi-chevron-down');
          icon.classList.add('bi-chevron-up');
        }
      }
    };

    window.planFormRemoveItem = function(btn) {
      var card = btn.closest('.plan-item-card');
      if (!card) return;
      var deleteCheckbox = card.querySelector('input[type="checkbox"][name*="DELETE"]');
      if (deleteCheckbox) {
        deleteCheckbox.checked = true;
        card.style.display = 'none';
        card.style.opacity = '0.5';
      } else {
        card.remove();
      }
      updatePlanItemFormIndexes();
      initExpandCollapseState();
    };

    window.planFormAddItem = function() {
      var levelSelect = document.getElementById('id_level');
      var levelOptions = '<option value="">---------</option>';
      if (levelSelect) {
        levelSelect.querySelectorAll('option').forEach(function(option) {
          levelOptions += '<option value="' + option.value + '"' + (option.selected ? ' selected' : '') + '>' + option.text + '</option>';
        });
      }
      var planPeriodSelect = document.getElementById('id_plan_period');
      var planPeriodOptions = '<option value="">---------</option>';
      if (planPeriodSelect) {
        planPeriodSelect.querySelectorAll('option').forEach(function(option) {
          planPeriodOptions += '<option value="' + option.value + '"' + (option.selected ? ' selected' : '') + '>' + option.text + '</option>';
        });
      }
      var parentPlanSelect = document.getElementById('id_parent_plan');
      var parentPlanOptions = '<option value="">-------</option>';
      if (parentPlanSelect) {
        parentPlanSelect.querySelectorAll('option').forEach(function(option) {
          parentPlanOptions += '<option value="' + option.value + '"' + (option.selected ? ' selected' : '') + '>' + option.text + '</option>';
        });
      }
      var existingGoalSelect = container.querySelector('select[name*="related_goal"]');
      var goalOptions = '<option value="">---------</option>';
      if (existingGoalSelect) {
        existingGoalSelect.querySelectorAll('option').forEach(function(option) {
          goalOptions += '<option value="' + option.value + '">' + option.text + '</option>';
        });
      }
      var existingParticipantsSelect = container.querySelector('select[name*="participants"]');
      var participantsOptions = '';
      if (existingParticipantsSelect) {
        existingParticipantsSelect.querySelectorAll('option').forEach(function(option) {
          var displayText = option.text;
          if (displayText.indexOf(' - ') !== -1) {
            displayText = displayText.split(' - ')[1] || displayText.split(' - ')[0];
          }
          participantsOptions += '<option value="' + option.value + '">' + displayText + '</option>';
        });
      }

      var newCard = document.createElement('div');
      newCard.className = 'plan-item-card mb-4 p-3 border rounded';
      newCard.dataset.formIndex = planItemFormCount;
      newCard.innerHTML =
        '<div class="d-flex justify-content-between align-items-center mb-3 plan-item-header">' +
          '<div class="d-flex align-items-center gap-2">' +
            '<button type="button" class="btn btn-sm btn-link p-0 toggle-expand-btn" data-action="plan-form-toggle-item" title="展开/折叠" data-expanded="false">' +
              '<i class="bi bi-chevron-down"></i>' +
            '</button>' +
            '<h5 class="mb-0">计划 ' + (planItemFormCount + 1) + '</h5>' +
          '</div>' +
          '<button type="button" class="btn btn-sm btn-dark" data-action="plan-form-remove-item" title="删除">' +
            '<i class="fas fa-trash"></i> 删除' +
          '</button>' +
        '</div>' +
        '<div class="plan-item-details">' +
        '<div class="row mb-3 form-row-5">' +
          '<div class="col-5-fields form-field-wrapper"><label class="form-label">计划级别 <span class="text-danger">*</span></label>' +
          '<select name="level" class="form-select" id="id_level" required>' + levelOptions + '</select>' +
          '<div class="form-text text-muted small">从基本信息区域继承</div></div>' +
          '<div class="col-5-fields form-field-wrapper"><label class="form-label">计划周期 <span class="text-danger">*</span></label>' +
          '<select name="plan_period" class="form-select" id="id_plan_period" required">' + planPeriodOptions + '</select>' +
          '<div class="form-text text-muted small">从基本信息区域继承，所有计划项共享</div></div>' +
          '<div class="col-5-fields form-field-wrapper"><label class="form-label">开始时间 <span class="text-danger">*</span></label>' +
          '<input type="date" name="' + formPrefix + '-' + planItemFormCount + '-start_time" class="form-control" id="id_' + formPrefix + '-' + planItemFormCount + '-start_time"></div>' +
          '<div class="col-5-fields form-field-wrapper"><label class="form-label">结束时间（系统自动计算） <span class="text-danger">*</span></label>' +
          '<input type="date" name="' + formPrefix + '-' + planItemFormCount + '-end_time" class="form-control plan-form-end-time-readonly" id="id_' + formPrefix + '-' + planItemFormCount + '-end_time" readonly>' +
          '<div class="form-text text-muted small">根据开始时间和计划周期自动计算</div></div>' +
          '<div class="col-5-fields form-field-wrapper"><label class="form-label">父计划</label>' +
          '<select name="parent_plan" class="form-select" id="id_parent_plan">' + parentPlanOptions + '</select>' +
          '<div class="form-text text-muted small">从基本信息区域继承，用于计划分解</div></div>' +
        '</div>' +
        '<div class="row mb-3 form-row-5">' +
          '<div class="col-5-fields form-field-wrapper"><label class="form-label">计划名称 <span class="text-danger">*</span></label>' +
          '<input type="text" name="' + formPrefix + '-' + planItemFormCount + '-name" class="form-control" placeholder="请输入计划名称" maxlength="200" id="id_' + formPrefix + '-' + planItemFormCount + '-name"></div>' +
          '<div class="col-5-fields form-field-wrapper"><label class="form-label">计划目标 <span class="text-danger">*</span></label>' +
          '<input type="text" name="' + formPrefix + '-' + planItemFormCount + '-plan_objective" class="form-control" placeholder="请输入计划目标" maxlength="1000" id="id_' + formPrefix + '-' + planItemFormCount + '-plan_objective"></div>' +
          '<div class="col-5-fields form-field-wrapper"><label class="form-label">关联战略目标 <span class="text-danger">*</span></label>' +
          '<select name="' + formPrefix + '-' + planItemFormCount + '-related_goal" class="form-select" id="id_' + formPrefix + '-' + planItemFormCount + '-related_goal">' + goalOptions + '</select>' +
          '<div class="form-text text-muted small">仅显示您负责的个人目标（状态为已发布或进行中）</div></div>' +
          '<div class="col-5-fields form-field-wrapper"><label class="form-label">关联项目</label>' +
          '<input type="text" name="' + formPrefix + '-' + planItemFormCount + '-related_project" class="form-control" placeholder="请输入关联项目" maxlength="200" id="id_' + formPrefix + '-' + planItemFormCount + '-related_project"></div>' +
          '<div class="col-5-fields form-field-wrapper"></div>' +
        '</div>' +
        '<div class="row mb-3"><div class="col-12 form-field-wrapper"><label class="form-label">计划内容 <span class="text-danger">*</span></label>' +
        '<textarea name="' + formPrefix + '-' + planItemFormCount + '-content" class="form-control" rows="2" placeholder="请输入计划内容" maxlength="5000" id="id_' + formPrefix + '-' + planItemFormCount + '-content"></textarea></div></div>' +
        '<div class="row mb-3"><div class="col-12 form-field-wrapper"><label class="form-label">验收标准 <span class="text-danger">*</span></label>' +
        '<textarea name="' + formPrefix + '-' + planItemFormCount + '-acceptance_criteria" class="form-control" rows="2" placeholder="请输入验收标准" maxlength="1000" required id="id_' + formPrefix + '-' + planItemFormCount + '-acceptance_criteria"></textarea></div></div>' +
        '<div class="row mb-3"><div class="col-12 form-field-wrapper"><label class="form-label">协作计划</label>' +
        '<textarea name="' + formPrefix + '-' + planItemFormCount + '-collaboration_plan" class="form-control" rows="2" placeholder="请输入协作计划" maxlength="2000" id="id_' + formPrefix + '-' + planItemFormCount + '-collaboration_plan"></textarea></div></div>' +
        '<div class="row mb-3"><div class="col-12 form-field-wrapper"><label class="form-label">协作人员</label>' +
        '<select name="' + formPrefix + '-' + planItemFormCount + '-participants" class="form-select" multiple size="3" id="id_' + formPrefix + '-' + planItemFormCount + '-participants">' + participantsOptions + '</select></div></div>' +
        '<div class="d-none"><input type="checkbox" name="' + formPrefix + '-' + planItemFormCount + '-DELETE" id="id_' + formPrefix + '-' + planItemFormCount + '-DELETE"></div>' +
        '</div>';

      container.appendChild(newCard);
      planItemFormCount++;
      updatePlanItemFormIndexes();

      setTimeout(function() {
        var newStartTimeInput = newCard.querySelector('input[name*="start_time"]');
        var newEndTimeInput = newCard.querySelector('input[name*="end_time"]');
        var planPeriodSel = document.getElementById('id_plan_period');
        if (newStartTimeInput && newEndTimeInput) {
          function calcEnd() {
            if (planPeriodSel && planPeriodSel.value) {
              calculateEndTime(newStartTimeInput, newEndTimeInput, planPeriodSel.value);
            }
          }
          newStartTimeInput.addEventListener('change', calcEnd);
          newStartTimeInput.addEventListener('input', calcEnd);
          if (newStartTimeInput.value.trim() && planPeriodSel && planPeriodSel.value) calcEnd();
        }
      }, 100);
    };

    function initEndTimeCalculationForExistingItems() {
      var planPeriodSelect = document.getElementById('id_plan_period');
      if (!planPeriodSelect) return;

      if (!planPeriodSelect.dataset.endTimeCalculated) {
        planPeriodSelect.dataset.endTimeCalculated = 'true';
        planPeriodSelect.addEventListener('change', function() {
          var selectedPeriod = planPeriodSelect.value;
          var parentPlanSelect = document.getElementById('id_parent_plan');
          var parentPlanHelpText = parentPlanSelect ? parentPlanSelect.parentElement.querySelector('.form-text') : null;
          if (parentPlanSelect && getParentPlanOptionsUrl) {
            parentPlanSelect.innerHTML = '<option value="">加载中...</option>';
            parentPlanSelect.disabled = true;
            var planIdMatch = window.location.pathname.match(/\/plans\/(\d+)\/edit\//);
            var planIdParam = planIdMatch ? planIdMatch[1] : '';
            var sep = (getParentPlanOptionsUrl && getParentPlanOptionsUrl.indexOf('?') !== -1) ? '&' : '?';
            var url = getParentPlanOptionsUrl + sep + 'plan_period=' + encodeURIComponent(selectedPeriod);
            if (planIdParam) url += '&plan_id=' + encodeURIComponent(planIdParam);
            fetch(url, { method: 'GET', headers: { 'X-Requested-With': 'XMLHttpRequest' }, credentials: 'same-origin' })
              .then(function(r) { return r.json(); })
              .then(function(data) {
                parentPlanSelect.innerHTML = '';
                if (data.options && data.options.length > 0) {
                  data.options.forEach(function(opt) {
                    var o = document.createElement('option');
                    o.value = opt.value;
                    o.textContent = opt.text;
                    parentPlanSelect.appendChild(o);
                  });
                } else {
                  var o = document.createElement('option');
                  o.value = '';
                  o.textContent = '-------';
                  parentPlanSelect.appendChild(o);
                }
                parentPlanSelect.disabled = false;
                if (parentPlanHelpText && data.help_text) parentPlanHelpText.textContent = data.help_text;
                parentPlanSelect.value = '';
              })
              .catch(function(err) {
                console.error('加载父计划选项失败:', err);
                parentPlanSelect.innerHTML = '<option value="">加载失败，请刷新页面</option>';
                parentPlanSelect.disabled = false;
              });
          }
          var allCards = container.querySelectorAll('.plan-item-card');
          allCards.forEach(function(card) {
            var deleteCheckbox = card.querySelector('input[type="checkbox"][name*="DELETE"]');
            if (deleteCheckbox && deleteCheckbox.checked) return;
            var startInput = card.querySelector('input[name*="start_time"]');
            var endInput = card.querySelector('input[name*="end_time"]');
            if (startInput && endInput && startInput.value.trim()) {
              calculateEndTime(startInput, endInput, planPeriodSelect.value);
            }
          });
        });
      }

      var planItemCards = container.querySelectorAll('.plan-item-card');
      planItemCards.forEach(function(card) {
        var deleteCheckbox = card.querySelector('input[type="checkbox"][name*="DELETE"]');
        if (deleteCheckbox && deleteCheckbox.checked) return;
        var startTimeInput = card.querySelector('input[name*="start_time"]');
        var endTimeInput = card.querySelector('input[name*="end_time"]');
        if (startTimeInput && endTimeInput && !startTimeInput.dataset.endTimeCalculated) {
          function calcForItem() {
            if (planPeriodSelect && planPeriodSelect.value) {
              calculateEndTime(startTimeInput, endTimeInput, planPeriodSelect.value);
            }
          }
          startTimeInput.dataset.endTimeCalculated = 'true';
          startTimeInput.addEventListener('change', calcForItem);
          startTimeInput.addEventListener('input', calcForItem);
          if (startTimeInput.value.trim() && planPeriodSelect && planPeriodSelect.value) calcForItem();
        }
      });
    }

    updatePlanItemFormIndexes();
    initEndTimeCalculationForExistingItems();
    initExpandCollapseState();
  });
})();
