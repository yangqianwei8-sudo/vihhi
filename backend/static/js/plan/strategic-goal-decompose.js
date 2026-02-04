/**
 * 战略目标分解页：分解方式/指标类型切换、目标值输入动态更新、创建下级目标表单提交（P3 S1 治理：从 strategic_goal_decompose.html 迁出）
 * 配置：<script type="application/json" id="strategicGoalDecomposeConfig">
 */
(function() {
  'use strict';

  function getConfig() {
    var el = document.getElementById('strategicGoalDecomposeConfig');
    if (!el || !el.textContent) return {};
    try {
      return JSON.parse(el.textContent);
    } catch (e) {
      return {};
    }
  }

  function escapeHtml(s) {
    if (s == null) return '';
    var div = document.createElement('div');
    div.textContent = s;
    return div.innerHTML;
  }

  document.addEventListener('DOMContentLoaded', function() {
    var cfg = getConfig();
    var parentIndicatorType = cfg.parentIndicatorType || '';
    var parentIndicatorName = cfg.parentIndicatorName || '';
    var parentIndicatorUnit = cfg.parentIndicatorUnit || '';
    var parentValueChoices = cfg.parentValueChoices || [];
    var createChildGoalUrl = cfg.createChildGoalUrl || '';

    var decomposeMethodSelect = document.getElementById('decomposeMethodSelect');
    var goalTypeSelect = document.getElementById('goalTypeSelect');
    var indicatorTypeSelect = document.getElementById('indicatorTypeSelect');
    var indicatorNameInput = document.getElementById('indicatorNameInput');
    var indicatorUnitInput = document.getElementById('indicatorUnitInput');
    var valueChoicesDiv = document.getElementById('valueChoicesDiv');
    var valueChoicesInput = document.getElementById('valueChoicesInput');
    var targetValueContainer = document.getElementById('targetValueContainer');
    var departmentSelectDiv = document.getElementById('departmentSelectDiv');
    var userSelectDiv = document.getElementById('userSelectDiv');
    var departmentSelect = document.getElementById('departmentSelect');
    var userSelect = document.getElementById('userSelect');

    function updateTargetValueInput(indicatorType, valueChoices) {
      valueChoices = valueChoices || [];
      if (!targetValueContainer) return;

      var indicatorName = indicatorNameInput ? indicatorNameInput.value : parentIndicatorName;
      var indicatorUnit = indicatorUnitInput ? indicatorUnitInput.value : parentIndicatorUnit;

      var html = '';
      var hint = '';

      if (indicatorType === 'boolean') {
        html = '<select name="target_value" class="form-control" id="targetValueInput" required>' +
               '<option value="0">未完成</option>' +
               '<option value="1">已完成</option>' +
               '</select>';
        hint = '继承指标：' + escapeHtml(indicatorName) + '（布尔型：完成/未完成）';
      } else if (indicatorType === 'text') {
        html = '<input type="text" name="target_value" class="form-control" id="targetValueInput" required placeholder="请输入文本内容">';
        hint = '继承指标：' + escapeHtml(indicatorName) + '（文本型）';
      } else if (indicatorType === 'choice') {
        var options = '<option value="">请选择</option>';
        if (valueChoices.length > 0) {
          valueChoices.forEach(function(choice) {
            options += '<option value="' + escapeHtml(choice.value) + '">' + escapeHtml(choice.label) + '</option>';
          });
        }
        html = '<select name="target_value" class="form-control" id="targetValueInput" required>' + options + '</select>';
        hint = '继承指标：' + escapeHtml(indicatorName) + '（选择型）';
      } else if (indicatorType === 'percentage') {
        html = '<div class="target-value-row">' +
               '<input type="number" name="target_value" class="form-control target-value-input-flex" id="targetValueInput" step="0.01" min="0" max="100" required placeholder="0.00">' +
               '<span class="target-value-unit">%</span>' +
               '</div>';
        hint = '继承指标：' + escapeHtml(indicatorName) + '（百分比型：0-100%）';
      } else {
        var unitDisplay = indicatorUnit
          ? '<span id="indicatorUnitDisplay" class="target-value-unit">' + escapeHtml(indicatorUnit) + '</span>'
          : '';
        html = '<div class="target-value-row">' +
               '<input type="number" name="target_value" class="form-control target-value-input-flex" id="targetValueInput" step="0.01" required placeholder="0.00">' +
               unitDisplay +
               '</div>';
        hint = '继承指标：' + escapeHtml(indicatorName) + (indicatorUnit ? ' (' + escapeHtml(indicatorUnit) + ')' : '') + '（数值型）';
      }

      targetValueContainer.innerHTML = html + '<div class="form-hint" id="targetValueHint">' + hint + '</div>';
    }

    function showEl(el) {
      if (el) el.classList.add('show');
    }
    function hideEl(el) {
      if (el) el.classList.remove('show');
    }

    if (indicatorTypeSelect) {
      indicatorTypeSelect.addEventListener('change', function() {
        var selectedType = this.value;
        if (selectedType === 'choice') {
          showEl(valueChoicesDiv);
          if (valueChoicesInput) valueChoicesInput.required = true;
        } else {
          hideEl(valueChoicesDiv);
          if (valueChoicesInput) valueChoicesInput.required = false;
        }

        if (selectedType) {
          var choices = [];
          if (selectedType === 'choice' && valueChoicesInput && valueChoicesInput.value) {
            try {
              choices = JSON.parse(valueChoicesInput.value);
            } catch (e) {
              choices = parentValueChoices;
            }
          } else if (selectedType === parentIndicatorType) {
            choices = parentValueChoices;
          }
          updateTargetValueInput(selectedType, choices);
        }
      });
    }

    if (indicatorNameInput) {
      indicatorNameInput.addEventListener('input', function() {
        if (indicatorTypeSelect && indicatorTypeSelect.value) {
          var choices = [];
          if (indicatorTypeSelect.value === 'choice' && valueChoicesInput && valueChoicesInput.value) {
            try {
              choices = JSON.parse(valueChoicesInput.value);
            } catch (e) {
              choices = parentValueChoices;
            }
          } else if (indicatorTypeSelect.value === parentIndicatorType) {
            choices = parentValueChoices;
          }
          updateTargetValueInput(indicatorTypeSelect.value, choices);
        }
      });
    }

    if (indicatorUnitInput) {
      indicatorUnitInput.addEventListener('input', function() {
        if (indicatorTypeSelect && indicatorTypeSelect.value === 'numeric') {
          updateTargetValueInput('numeric', []);
        }
      });
    }

    if (valueChoicesInput) {
      valueChoicesInput.addEventListener('input', function() {
        if (indicatorTypeSelect && indicatorTypeSelect.value === 'choice') {
          var choices = [];
          if (this.value) {
            try {
              choices = JSON.parse(this.value);
            } catch (e) {
              return;
            }
          }
          updateTargetValueInput('choice', choices);
        }
      });
    }

    if (decomposeMethodSelect) {
      decomposeMethodSelect.addEventListener('change', function() {
        if (this.value === 'department') {
          showEl(departmentSelectDiv);
          showEl(userSelectDiv);
          if (departmentSelect) departmentSelect.required = true;
          if (userSelect) userSelect.required = true;
        } else if (this.value === 'personal') {
          hideEl(departmentSelectDiv);
          showEl(userSelectDiv);
          if (departmentSelect) departmentSelect.required = false;
          if (userSelect) userSelect.required = true;
        } else {
          hideEl(departmentSelectDiv);
          hideEl(userSelectDiv);
          if (departmentSelect) departmentSelect.required = false;
          if (userSelect) userSelect.required = false;
        }
      });
    }

    var form = document.getElementById('createChildGoalForm');
    if (form) {
      form.addEventListener('submit', function(e) {
        e.preventDefault();

        if (!form.checkValidity()) {
          form.reportValidity();
          return;
        }

        if (!decomposeMethodSelect || !decomposeMethodSelect.value) {
          alert('请选择分解方式');
          if (decomposeMethodSelect) decomposeMethodSelect.focus();
          return;
        }

        if (!goalTypeSelect || !goalTypeSelect.value) {
          alert('请选择目标类型');
          if (goalTypeSelect) goalTypeSelect.focus();
          return;
        }

        if (!indicatorTypeSelect || !indicatorTypeSelect.value) {
          alert('请选择指标类型');
          if (indicatorTypeSelect) indicatorTypeSelect.focus();
          return;
        }

        if (indicatorTypeSelect.value === 'choice') {
          if (!valueChoicesInput || !valueChoicesInput.value) {
            alert('选择型指标需要填写选择项');
            if (valueChoicesInput) valueChoicesInput.focus();
            return;
          }
          try {
            var choices = JSON.parse(valueChoicesInput.value);
            if (!Array.isArray(choices) || choices.length === 0) {
              alert('选择项必须是包含至少一个选项的JSON数组');
              valueChoicesInput.focus();
              return;
            }
          } catch (err) {
            alert('选择项格式错误，请输入有效的JSON格式');
            valueChoicesInput.focus();
            return;
          }
        }

        if (!userSelect || !userSelect.value) {
          alert('请选择负责人');
          if (userSelect) userSelect.focus();
          return;
        }

        if (decomposeMethodSelect.value === 'department' && (!departmentSelect || !departmentSelect.value)) {
          alert('请选择部门');
          if (departmentSelect) departmentSelect.focus();
          return;
        }

        var formData = new FormData(form);
        formData.set('decompose_method', decomposeMethodSelect.value);
        if (decomposeMethodSelect.value === 'personal') {
          formData.delete('department_id');
        }

        fetch(createChildGoalUrl, {
          method: 'POST',
          body: formData,
          headers: {
            'X-CSRFToken': formData.get('csrfmiddlewaretoken')
          },
          credentials: 'same-origin'
        })
        .then(function(response) {
          var contentType = response.headers.get('Content-Type') || '';
          if (contentType.indexOf('application/json') === -1) {
            return response.text().then(function(text) {
              console.error('非JSON响应:', text.substring(0, 200));
              throw new Error('服务器返回了非JSON响应，可能是权限问题或服务器错误');
            });
          }
          if (!response.ok) {
            return response.json().then(function(data) {
              throw new Error(data.message || '请求失败');
            }).catch(function(err) {
              if (err.message) throw err;
              throw new Error('请求失败，状态码: ' + response.status);
            });
          }
          return response.json();
        })
        .then(function(data) {
          if (data.success) {
            window.location.reload();
          } else {
            alert('创建失败：' + (data.message || '未知错误'));
          }
        })
        .catch(function(error) {
          console.error('Error:', error);
          alert('创建失败：' + error.message);
        });
      });
    }

    if (indicatorTypeSelect && indicatorTypeSelect.value === 'choice' && valueChoicesInput && parentValueChoices && parentValueChoices.length > 0) {
      if (!valueChoicesInput.value) {
        valueChoicesInput.value = JSON.stringify(parentValueChoices);
      }
    }
  });
})();
