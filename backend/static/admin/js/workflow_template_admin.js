/**
 * WorkflowTemplate Admin JavaScript
 * 用于增强适用模型和表单筛选条件的交互
 */

(function() {
    'use strict';
    
    // 获取 jQuery（Django Admin 使用 django.jQuery）
    var $;
    if (typeof django !== 'undefined' && typeof django.jQuery !== 'undefined') {
        $ = django.jQuery;
    } else if (typeof jQuery !== 'undefined') {
        $ = jQuery;
    } else {
        console.error('jQuery is not available');
        return;
    }
    
    // 模型对应的表单列表（从后端传递，这里作为备用）
    // 使用表单的主标题名称（用户在页面上看到的标题）
    var MODEL_FORM_MAP = {
        'plan': [
            ['plan', '创建计划'],
            ['strategicgoal', '创建战略目标'],
            ['plandecision', '计划决策'],
            ['planadjustment', '申请调整'],
            ['goaladjustment', '目标调整申请'],
        ],
        'businesscontract': [
            ['businesscontract', '创建合同'],
        ],
        'businessopportunity': [
            ['businessopportunity', '创建商机'],
        ],
        'project': [
            ['project', '创建项目'],
        ],
        'client': [
            ['client', '创建客户'],
        ],
        'strategicgoal': [
            ['strategicgoal', '创建战略目标'],
            ['goaladjustment', '目标调整申请'],
        ],
    };
    
    // 初始化
    function init() {
        // 调整字段布局
        adjustFieldLayout();
        
        // 绑定事件
        bindEvents();
        
        // 初始化筛选条件编辑器
        initFilterEditor();
    }
    
    // 调整字段布局，使适用模型和筛选条件并排显示
    function adjustFieldLayout() {
        var $applicableModelsField = $('#id_applicable_models').closest('.form-row, .field-applicable_models, div');
        var $filterConditionsField = $('#id_form_filter_conditions').closest('.form-row, .field-form_filter_conditions, div');
        
        if ($applicableModelsField.length && $filterConditionsField.length) {
            // 创建容器
            var $container = $('<div class="fieldset-scope"></div>');
            
            // 将字段移动到容器中
            $applicableModelsField.wrap('<div class="field-applicable_models"></div>');
            $filterConditionsField.wrap('<div class="field-form_filter_conditions"></div>');
            
            // 获取父容器
            var $parent = $applicableModelsField.parent();
            if ($parent.length) {
                $parent.addClass('fieldset-scope');
            }
        }
    }
    
    // 绑定事件
    function bindEvents() {
        // 监听适用模型选择变化
        $('#id_applicable_models').on('change', function() {
            updateFilterEditor();
        });
        
        // 监听筛选条件输入变化，实时验证JSON格式
        $('#id_form_filter_conditions').on('blur', function() {
            validateJSON($(this));
        });
    }
    
    // 初始化筛选条件编辑器
    function initFilterEditor() {
        var $select = $('#id_form_filter_conditions');
        if ($select.length) {
            // 更新下拉框内容
            updateFilterEditor();
        }
    }
    
    // 更新表单筛选条件下拉框
    function updateFilterEditor() {
        var selectedModels = $('#id_applicable_models').val() || [];
        var $select = $('#id_form_filter_conditions');
        
        if (!$select.length) {
            return;
        }
        
        if (selectedModels.length === 0) {
            // 清空选项，显示提示
            $select.empty();
            $select.append($('<option></option>').attr('value', '').text('请先选择适用模型'));
            $select.prop('disabled', true);
            return;
        }
        
        // 启用下拉框
        $select.prop('disabled', false);
        
        // 收集所有可用的表单选项
        var allForms = [];
        var seen = {};
        
        selectedModels.forEach(function(model) {
            if (MODEL_FORM_MAP[model]) {
                MODEL_FORM_MAP[model].forEach(function(form) {
                    if (!seen[form[0]]) {
                        seen[form[0]] = true;
                        allForms.push(form);
                    }
                });
            }
        });
        
        // 按名称排序
        allForms.sort(function(a, b) {
            return a[1].localeCompare(b[1]);
        });
        
        // 保存当前选中的值
        var currentValues = $select.val() || [];
        
        // 更新选项
        $select.empty();
        allForms.forEach(function(form) {
            var $option = $('<option></option>')
                .attr('value', form[0])
                .text(form[1]);
            if (currentValues.indexOf(form[0]) !== -1) {
                $option.prop('selected', true);
            }
            $select.append($option);
        });
        
        // 如果没有选项，显示提示
        if (allForms.length === 0) {
            $select.append($('<option></option>').attr('value', '').text('该模型下暂无可用表单'));
        }
    }
    
    // DOM加载完成后初始化
    $(document).ready(function() {
        init();
    });
    
    // 延迟初始化（确保Django admin的脚本执行完成）
    setTimeout(init, 100);
    setTimeout(init, 500);
    
})();
