(function($) {
    'use strict';
    
    // 初始化所有两栏过滤组件
    function initTwoColumnFilters() {
        $('.two-column-filter-widget').each(function() {
            var $widget = $(this);
            var widgetId = $widget.attr('id');
            
            var $moduleCheckboxes = $widget.find('.module-checkbox');
            var $modelList = $widget.find('.model-list');
            var $hiddenInput = $widget.find('input[type="hidden"]');
            var $selectedList = $widget.find('.selected-list');
            
            // 从data属性获取映射数据
            var moduleModelMapping = $widget.data('module-mapping') || {};
            var initialSelected = $widget.data('selected-models') || [];
            
            // 当前选中的模型
            var currentSelected = initialSelected.slice();
            
            // 更新已选择列表显示
            function updateSelectedList() {
                $selectedList.empty();
                if (currentSelected.length === 0) {
                    $selectedList.html('<span class="no-selection">暂无选择</span>');
                } else {
                    currentSelected.forEach(function(modelCode) {
                        // 查找模型的中文名称
                        var modelName = findModelName(modelCode);
                        var $tag = $('<span class="selected-tag">' + modelName + 
                                    '<span class="remove-btn" data-model="' + modelCode + '">×</span></span>');
                        $selectedList.append($tag);
                    });
                }
                // 更新隐藏字段
                $hiddenInput.val(currentSelected.join(','));
            }
            
            // 查找模型的中文名称
            function findModelName(modelCode) {
                for (var module in moduleModelMapping) {
                    var models = moduleModelMapping[module];
                    for (var i = 0; i < models.length; i++) {
                        if (models[i][0] === modelCode) {
                            return models[i][1];
                        }
                    }
                }
                return modelCode;
            }
            
            // 根据选中的模块更新业务对象列表
            function updateModelList() {
                var selectedModules = [];
                $moduleCheckboxes.filter(':checked').each(function() {
                    selectedModules.push($(this).val());
                });
                
                $modelList.empty();
                
                if (selectedModules.length === 0) {
                    $modelList.html('<p class="hint-text">请先选择功能模块</p>');
                    return;
                }
                
                // 收集所有相关模型
                var availableModels = [];
                selectedModules.forEach(function(module) {
                    if (moduleModelMapping[module]) {
                        moduleModelMapping[module].forEach(function(model) {
                            // 避免重复
                            if (!availableModels.find(function(m) { return m[0] === model[0]; })) {
                                availableModels.push(model);
                            }
                        });
                    }
                });
                
                if (availableModels.length === 0) {
                    $modelList.html('<p class="hint-text">所选模块暂无业务对象</p>');
                    return;
                }
                
                // 显示模型列表
                availableModels.forEach(function(model) {
                    var modelCode = model[0];
                    var modelName = model[1];
                    var isChecked = currentSelected.indexOf(modelCode) !== -1;
                    var $item = $('<div class="model-item">' +
                                '<label>' +
                                '<input type="checkbox" class="model-checkbox" value="' + modelCode + '"' +
                                (isChecked ? ' checked' : '') + '>' +
                                modelName +
                                '</label>' +
                                '</div>');
                    $modelList.append($item);
                });
            }
            
            // 模块选择变化事件
            $moduleCheckboxes.on('change', function() {
                updateModelList();
            });
            
            // 业务对象选择变化事件（使用事件委托）
            $modelList.on('change', '.model-checkbox', function() {
                var modelCode = $(this).val();
                var isChecked = $(this).is(':checked');
                
                if (isChecked) {
                    if (currentSelected.indexOf(modelCode) === -1) {
                        currentSelected.push(modelCode);
                    }
                } else {
                    var index = currentSelected.indexOf(modelCode);
                    if (index !== -1) {
                        currentSelected.splice(index, 1);
                    }
                }
                updateSelectedList();
            });
            
            // 移除已选择的对象
            $selectedList.on('click', '.remove-btn', function(e) {
                e.stopPropagation();
                var modelCode = $(this).data('model');
                var index = currentSelected.indexOf(modelCode);
                if (index !== -1) {
                    currentSelected.splice(index, 1);
                }
                // 取消对应的checkbox
                $modelList.find('.model-checkbox[value="' + modelCode + '"]').prop('checked', false);
                updateSelectedList();
            });
            
            // 初始化：如果有已选择的对象，需要选中对应的模块
            if (currentSelected.length > 0) {
                // 找出包含已选择模型的模块
                currentSelected.forEach(function(modelCode) {
                    for (var module in moduleModelMapping) {
                        var models = moduleModelMapping[module];
                        if (models.find(function(m) { return m[0] === modelCode; })) {
                            $moduleCheckboxes.filter('[value="' + module + '"]').prop('checked', true);
                        }
                    }
                });
                updateModelList();
            }
            
            // 初始化已选择列表
            updateSelectedList();
        });
    }
    
    // 页面加载完成后初始化
    $(document).ready(function() {
        // 延迟一点执行，确保data属性已设置
        setTimeout(function() {
            initTwoColumnFilters();
        }, 100);
    });
    
    // 如果使用Django Admin的inline表单，需要在添加新行后重新初始化
    $(document).on('formset:added', function() {
        setTimeout(function() {
            initTwoColumnFilters();
        }, 100);
    });
    
})(django.jQuery || jQuery);
