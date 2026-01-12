(function($) {
    'use strict';
    
    // 初始化所有分类过滤组件
    function initCategoryFilteredWidgets() {
        $('.category-filtered-widget').each(function() {
            initSingleWidget($(this));
        });
    }
    
    // 初始化单个组件
    function initSingleWidget($widget) {
        var widgetId = $widget.attr('id');
        var widgetName = widgetId.replace('category-filtered-', '');
        
        var $modelList = $widget.find('.model-list');
        var $hiddenInput = $widget.find('input[type="hidden"]');
        var $selectedList = $widget.find('.selected-list');
        
        // 从data属性获取映射数据
        var moduleModelMapping = $widget.data('module-mapping');
        var initialSelected = $widget.data('selected-models') || [];
        var categoryFieldId = $widget.data('category-field-id') || 'id_category';
        
        // 如果数据还没准备好，尝试从全局变量获取
        if (!moduleModelMapping || typeof moduleModelMapping !== 'object' || Object.keys(moduleModelMapping).length === 0) {
            if (typeof window.categoryFilteredData !== 'undefined' && window.categoryFilteredData[widgetId]) {
                var widgetData = window.categoryFilteredData[widgetId];
                moduleModelMapping = widgetData.moduleMapping || {};
                initialSelected = widgetData.selectedModels || [];
                categoryFieldId = widgetData.categoryFieldId || categoryFieldId;
                // 同时设置到data属性
                $widget.data('module-mapping', moduleModelMapping);
                $widget.data('selected-models', initialSelected);
                $widget.data('category-field-id', categoryFieldId);
            }
        }
        
        // 如果还是没有数据，等待
        if (!moduleModelMapping || typeof moduleModelMapping !== 'object' || Object.keys(moduleModelMapping).length === 0) {
            console.log('CategoryFilteredWidget: 数据未准备好，等待...', {
                widgetId: widgetId,
                hasDataAttr: $widget.data('module-mapping') !== undefined,
                hasGlobalData: typeof window.categoryFilteredData !== 'undefined' && window.categoryFilteredData[widgetId] !== undefined
            });
            return false;
        }
        
        // 当前选中的模型
        var currentSelected = initialSelected.slice();
        
        // 获取category字段（尝试多种可能的ID格式）
        var $categoryField = $('#' + categoryFieldId);
        if ($categoryField.length === 0) {
            // 尝试其他可能的ID格式
            $categoryField = $('select[name="category"]');
            if ($categoryField.length === 0) {
                $categoryField = $('input[name="category"]');
            }
        }
        
        if ($categoryField.length === 0) {
            console.warn('CategoryFilteredWidget: 未找到category字段', {
                widgetId: widgetId,
                categoryFieldId: categoryFieldId,
                allSelects: $('select').length,
                allInputs: $('input').length
            });
        }
        
        // 更新已选择列表显示
        function updateSelectedList() {
            $selectedList.empty();
            if (currentSelected.length === 0) {
                $selectedList.html('<span class="no-selection">暂无选择</span>');
            } else {
                currentSelected.forEach(function(modelCode) {
                    // 查找模型的信息（名称和URL）
                    var modelInfo = findModelInfo(modelCode);
                    var modelName = modelInfo.name;
                    var createUrl = modelInfo.url;
                    var $tag = $('<span class="selected-tag" style="display: inline-block; margin: 4px 8px 4px 0; padding: 4px 8px; background: #e3f2fd; border-radius: 4px;">' + 
                                modelName + 
                                (createUrl && createUrl !== '#' ? ' <a href="' + createUrl + '" target="_blank" style="margin-left: 5px; color: #1976d2; text-decoration: none; font-size: 12px;" title="打开创建表单">📝</a>' : '') +
                                '<span class="remove-btn" data-model="' + modelCode + '" style="margin-left: 8px; cursor: pointer; color: #f44336; font-weight: bold;">×</span></span>');
                    $selectedList.append($tag);
                });
            }
            // 更新隐藏字段
            $hiddenInput.val(currentSelected.join(','));
        }
        
        // 查找模型的信息（名称和URL）
        function findModelInfo(modelCode) {
            for (var module in moduleModelMapping) {
                var models = moduleModelMapping[module];
                for (var i = 0; i < models.length; i++) {
                    if (models[i][0] === modelCode) {
                        return {
                            name: models[i][1],
                            url: models[i][2] || null
                        };
                    }
                }
            }
            return { name: modelCode, url: null };
        }
        
        // 查找模型的中文名称（向后兼容）
        function findModelName(modelCode) {
            return findModelInfo(modelCode).name;
        }
        
        // 根据选中的分类更新业务对象列表
        function updateModelList() {
            var selectedCategory = $categoryField.val();
            
            $modelList.empty();
            
            if (!selectedCategory || selectedCategory === '') {
                $modelList.html('<p class="hint-text">请先在上方选择"流程分类"，然后在此处选择该分类下的业务对象类型</p>');
                return;
            }
            
            // 获取该分类下的业务对象
            var availableModels = moduleModelMapping[selectedCategory] || [];
            
            if (availableModels.length === 0) {
                $modelList.html('<p class="hint-text">所选分类暂无业务对象类型</p>');
                return;
            }
            
            // 显示模型列表
            availableModels.forEach(function(model) {
                var modelCode = model[0];
                var modelName = model[1];
                var createUrl = model[2] || '#'; // 获取create表单URL
                var isChecked = currentSelected.indexOf(modelCode) !== -1;
                
                // 创建包含链接的选项
                var $item = $('<div class="model-item" style="padding: 8px; border-bottom: 1px solid #eee;">' +
                            '<label style="display: flex; align-items: center; gap: 8px; cursor: pointer;">' +
                            '<input type="checkbox" class="model-checkbox" value="' + modelCode + '"' +
                            (isChecked ? ' checked' : '') + ' style="margin-right: 5px;">' +
                            '<span style="flex: 1;">' + modelName + '</span>' +
                            (createUrl !== '#' ? '<a href="' + createUrl + '" target="_blank" class="create-link" style="color: #1976d2; text-decoration: none; font-size: 12px; padding: 2px 8px; border: 1px solid #1976d2; border-radius: 3px; white-space: nowrap;" title="打开创建表单" onclick="event.stopPropagation();">📝 创建</a>' : '') +
                            '</label>' +
                            '</div>');
                $modelList.append($item);
            });
        }
        
        // 分类选择变化事件
        $categoryField.off('change.category-filtered').on('change.category-filtered', function() {
            updateModelList();
            updateSelectedList();
        });
        
        // 业务对象选择变化事件（使用事件委托）
        $modelList.off('change', '.model-checkbox').on('change', '.model-checkbox', function() {
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
        $selectedList.off('click', '.remove-btn').on('click', '.remove-btn', function(e) {
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
        
        // 初始化：如果有分类值，显示对应的列表
        if ($categoryField.length && $categoryField.val()) {
            updateModelList();
        } else {
            // 即使没有分类值，也显示提示
            $modelList.html('<p class="hint-text">请先在上方选择"流程分类"，然后在此处选择该分类下的业务对象类型</p>');
        }
        
        // 初始化已选择列表
        updateSelectedList();
        
        console.log('CategoryFilteredWidget: 初始化完成', {
            widgetId: widgetId,
            category: $categoryField.val(),
            mappingKeys: Object.keys(moduleModelMapping),
            selected: currentSelected
        });
        
        return true;
    }
    
    // 页面加载完成后初始化
    $(document).ready(function() {
        // 延迟一点执行，确保data属性已设置
        setTimeout(function() {
            initCategoryFilteredWidgets();
        }, 200);
        
        // 监听数据准备好事件
        $(document).on('widget-data-ready', '.category-filtered-widget', function() {
            initSingleWidget($(this));
        });
        
        // 在表单提交前，确保所有隐藏字段的值都是最新的
        $('form').on('submit', function(e) {
            $('.category-filtered-widget').each(function() {
                var $widget = $(this);
                var $hiddenInput = $widget.find('input[type="hidden"]');
                var $selectedList = $widget.find('.selected-list');
                var selectedModels = [];
                
                // 从已选择的标签中获取模型代码
                $selectedList.find('.selected-tag').each(function() {
                    var modelCode = $(this).find('.remove-btn').data('model');
                    if (modelCode) {
                        selectedModels.push(modelCode);
                    }
                });
                
                // 更新隐藏字段的值
                $hiddenInput.val(selectedModels.join(','));
                
                console.log('CategoryFilteredWidget: 表单提交前更新隐藏字段', {
                    widgetId: $widget.attr('id'),
                    value: $hiddenInput.val()
                });
            });
        });
    });
    
    // 如果使用Django Admin的inline表单，需要在添加新行后重新初始化
    $(document).on('formset:added', function() {
        setTimeout(function() {
            initCategoryFilteredWidgets();
        }, 200);
    });
    
})(django.jQuery || jQuery);


