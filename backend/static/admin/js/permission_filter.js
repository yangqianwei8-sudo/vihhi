/**
 * 权限过滤器 JavaScript
 * 用于增强 Django Admin 权限选择器的功能
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

    // 强制设置选择器宽度，确保不被Django admin默认行为覆盖
    function enforceSelectorWidth() {
        // 查找所有权限选择器（使用原生DOM，避免jQuery可能的问题）
        var selectors = document.querySelectorAll('.selector-available, .selector-chosen');
        
        if (selectors.length > 0) {
            // 使用内联样式强制设置宽度（优先级最高）
            selectors.forEach(function(selector) {
                selector.style.setProperty('flex', '0 0 700px', 'important');
                selector.style.setProperty('min-width', '700px', 'important');
                selector.style.setProperty('width', '700px', 'important');
                selector.style.setProperty('max-width', '700px', 'important');
            });
        }
    }

    // 模块代码到中文名称的映射
    var MODULE_NAME_MAP = {
        'production_management': '生产管理',
        'settlement_management': '结算管理',
        'settlement_center': '回款管理',
        'production_quality': '生产质量',
        'customer_management': '客户管理',
        'opportunity_management': '商机管理',
        'contract_management': '合同管理',
        'personnel_management': '人事管理',
        'risk_management': '风险管理',
        'system_management': '系统管理',
        'permission_management': '权限管理',
        'resource_standard': '资源标准',
        'task_collaboration': '任务协作',
        'delivery_customer': '交付客户',
        'archive_management': '档案管理',
        'plan_management': '计划管理',
        'litigation_management': '诉讼管理',
        'financial_management': '财务管理',
        'administrative_management': '行政管理',
        'workflow_engine': '审批引擎'
    };
    
    // 从权限代码中提取模块名
    function getModuleFromCode(code) {
        if (!code) return null;
        var parts = code.split('.');
        if (parts.length >= 2) {
            var moduleCode = parts[0];
            return MODULE_NAME_MAP[moduleCode] || moduleCode;
        }
        return null;
    }
    
    // 添加模块筛选功能
    function addModuleFilter() {
        // 检查是否已经添加过筛选器
        if ($('#module-filter-select').length > 0) {
            console.log('[Permission Filter] 筛选器已存在，跳过');
            return;
        }
        
        // 查找权限选择器容器（尝试多种选择器）
        var $selector = $('.selector');
        var $fieldset = null;
        var $container = null;
        
        if ($selector.length === 0) {
            // 尝试查找包含filter_horizontal的容器
            $selector = $('fieldset:has(.selector), .form-row:has(.selector), .field-custom_permissions');
        }
        
        // 如果还是找不到，尝试通过select元素找到容器
        if ($selector.length === 0) {
            var $select = $('select[id*="custom_permissions"]').first();
            if ($select.length > 0) {
                $container = $select.closest('fieldset, .form-row, .selector, div');
                $fieldset = $select.closest('fieldset');
                console.log('[Permission Filter] 通过select找到容器:', $container ? $container.length : 0, 'fieldset:', $fieldset ? $fieldset.length : 0);
            }
        }
        
        if ($selector.length === 0 && (!$container || $container.length === 0)) {
            console.log('[Permission Filter] 未找到选择器容器');
            console.log('[Permission Filter] 页面中的select元素:', $('select').length);
            console.log('[Permission Filter] 包含custom_permissions的select:', $('select[id*="custom_permissions"]').length);
            return;
        }
        
        console.log('[Permission Filter] 找到选择器容器，开始添加筛选功能');
        
        // 获取所有权限项，提取模块信息
        var modules = new Set();
        var moduleDataMap = {}; // 模块名 -> {items: [], codes: []}
        
        // 从select元素的option中提取模块信息（更可靠）
        // Django admin的filter_horizontal使用select元素，id格式为 id_custom_permissions_from 和 id_custom_permissions_to
        var $availableSelect = $('#id_custom_permissions_from, select.selector-available');
        var $chosenSelect = $('#id_custom_permissions_to, select.selector-chosen');
        
        console.log('[Permission Filter] 找到可用权限select:', $availableSelect.length, '找到已选权限select:', $chosenSelect.length);
        
        $availableSelect.add($chosenSelect).each(function() {
            var $select = $(this);
            $select.find('option').each(function() {
                var $option = $(this);
                var value = $option.val();
                var text = $option.text().trim();
                
                if (value && value !== '') {
                    // 从权限代码中提取模块
                    var moduleName = getModuleFromCode(value);
                    if (moduleName) {
                        modules.add(moduleName);
                        if (!moduleDataMap[moduleName]) {
                            moduleDataMap[moduleName] = {codes: [], items: []};
                        }
                        if (moduleDataMap[moduleName].codes.indexOf(value) === -1) {
                            moduleDataMap[moduleName].codes.push(value);
                        }
                    }
                }
            });
        });
        
        // 也从li元素中提取（用于已选中的权限）
        $selector.find('.selector-available li, .selector-chosen li').each(function() {
            var $li = $(this);
            var $option = $li.find('option');
            if ($option.length === 0) {
                // 如果没有option，尝试从li的data属性或文本中提取
                var text = $li.text().trim();
                var code = $li.find('code').text().trim();
                if (code) {
                    var moduleName = getModuleFromCode(code);
                    if (moduleName) {
                        modules.add(moduleName);
                        if (!moduleDataMap[moduleName]) {
                            moduleDataMap[moduleName] = {codes: [], items: []};
                        }
                        if (moduleDataMap[moduleName].codes.indexOf(code) === -1) {
                            moduleDataMap[moduleName].codes.push(code);
                        }
                        moduleDataMap[moduleName].items.push($li);
                    }
                }
            }
        });
        
        // 如果还是没有模块，尝试从所有select中提取
        if (modules.size === 0) {
            console.log('[Permission Filter] 未找到模块，尝试从所有select元素提取');
            $('select[id*="custom_permissions"]').each(function() {
                var $select = $(this);
                $select.find('option').each(function() {
                    var value = $(this).val();
                    if (value && value !== '') {
                        var moduleName = getModuleFromCode(value);
                        if (moduleName) {
                            modules.add(moduleName);
                            if (!moduleDataMap[moduleName]) {
                                moduleDataMap[moduleName] = {codes: [], items: []};
                            }
                            if (moduleDataMap[moduleName].codes.indexOf(value) === -1) {
                                moduleDataMap[moduleName].codes.push(value);
                            }
                        }
                    }
                });
            });
        }
        
        // 如果还是没有模块，返回
        if (modules.size === 0) {
            console.log('[Permission Filter] 仍然未找到模块，无法添加筛选功能');
            return;
        }
        
        console.log('[Permission Filter] 找到', modules.size, '个模块:', Array.from(modules));
        
        // 创建筛选器HTML
        var moduleList = Array.from(modules).sort();
        var filterHtml = '<div class="module-filter-container" style="margin-bottom: 15px; padding: 10px; background: #f8f9fa; border-radius: 4px; border: 1px solid #dee2e6;">' +
            '<label for="module-filter-select" style="font-weight: bold; margin-right: 10px; color: #495057;">按模块筛选：</label>' +
            '<select id="module-filter-select" style="padding: 6px 12px; border: 1px solid #ced4da; border-radius: 4px; font-size: 14px; min-width: 200px; background: white; cursor: pointer;">' +
            '<option value="">全部模块</option>';
        
        moduleList.forEach(function(module) {
            filterHtml += '<option value="' + module + '">' + module + '</option>';
        });
        
        filterHtml += '</select>' +
            '<span id="module-filter-count" style="margin-left: 15px; color: #6c757d; font-size: 13px;"></span>' +
            '</div>';
        
        // 在selector容器的最前面插入筛选器，如果找不到selector，则在业务权限字段集前面插入
        var inserted = false;
        var $target = null;
        
        // 优先使用找到的selector
        if ($selector.length > 0) {
            $target = $selector.first();
        } else if ($fieldset && $fieldset.length > 0) {
            $target = $fieldset.first();
        } else if ($container && $container.length > 0) {
            $target = $container.first();
        } else {
            // 最后尝试查找包含custom_permissions的fieldset
            $target = $('fieldset:has(select[id*="custom_permissions"])').first();
        }
        
        if ($target && $target.length > 0) {
            $target.prepend(filterHtml);
            inserted = true;
            console.log('[Permission Filter] 筛选器已添加到目标容器:', $target[0].tagName, $target[0].className);
        } else {
            // 最后尝试直接在select元素前插入
            var $select = $('select[id*="custom_permissions"]').first();
            if ($select.length > 0) {
                $select.before(filterHtml);
                inserted = true;
                console.log('[Permission Filter] 筛选器已添加到select前');
            }
        }
        
        if (inserted) {
            console.log('[Permission Filter] 筛选器已成功添加');
        } else {
            console.error('[Permission Filter] 无法找到合适的插入位置');
        }
        
        // 绑定筛选事件
        $('#module-filter-select').on('change', function() {
            var selectedModule = $(this).val();
            filterByModule(selectedModule, moduleDataMap);
        });
        
        // 初始化显示
        filterByModule('', moduleDataMap);
    }
    
    // 按模块筛选权限项
    function filterByModule(selectedModule, moduleDataMap) {
        var $availableSelect = $('#id_custom_permissions_from, select.selector-available, select[id*="custom_permissions_from"]');
        var totalCount = 0;
        var visibleCount = 0;
        
        // 筛选可用权限列表（select元素中的option）
        if ($availableSelect.length > 0) {
            $availableSelect.find('option').each(function() {
                var $option = $(this);
                var value = $option.val();
                
                // 跳过空值和默认选项
                if (!value || value === '') {
                    return;
                }
                
                totalCount++;
                var shouldShow = true;
                
                if (selectedModule) {
                    shouldShow = false;
                    var moduleName = getModuleFromCode(value);
                    if (moduleName === selectedModule) {
                        shouldShow = true;
                        visibleCount++;
                    }
                } else {
                    visibleCount++;
                }
                
                // 对于select元素，隐藏option在不同浏览器中表现不一致
                // 我们使用一个变通方法：通过过滤select的选项
                if (shouldShow) {
                    $option.show();
                } else {
                    $option.hide();
                }
            });
        }
        
        // 也处理ul中的li元素（某些版本的Django admin使用这种方式）
        $('.selector-available ul li, ul.selector-chooser li').each(function() {
            var $li = $(this);
            var code = $li.find('code').text().trim();
            
            if (!code) {
                // 尝试从关联的option获取
                var $option = $li.closest('select').find('option[value="' + $li.data('value') + '"]');
                if ($option.length > 0) {
                    code = $option.val();
                }
            }
            
            if (code) {
                if (totalCount === 0) totalCount = 1; // 避免重复计数
                var shouldShow = true;
                
                if (selectedModule) {
                    shouldShow = false;
                    var moduleName = getModuleFromCode(code);
                    if (moduleName === selectedModule) {
                        shouldShow = true;
                        if (visibleCount < totalCount) visibleCount++;
                    }
                } else {
                    if (visibleCount < totalCount) visibleCount++;
                }
                
                if (shouldShow) {
                    $li.show();
                } else {
                    $li.hide();
                }
            }
        });
        
        // 更新计数显示
        if (selectedModule) {
            $('#module-filter-count').text('显示 ' + visibleCount + ' / ' + totalCount + ' 个权限项');
        } else {
            $('#module-filter-count').text('共 ' + totalCount + ' 个权限项');
        }
        
        // 触发select的change事件，确保Django admin的搜索功能正常工作
        if ($availableSelect.length > 0) {
            $availableSelect.trigger('change');
        }
    }

    // 初始化函数
    function init() {
        console.log('[Permission Filter] 开始初始化...');
        console.log('[Permission Filter] jQuery可用:', typeof $ !== 'undefined');
        console.log('[Permission Filter] 查找.selector:', $('.selector').length);
        console.log('[Permission Filter] 查找custom_permissions select:', $('select[id*="custom_permissions"]').length);
        
        // 立即执行一次
        enforceSelectorWidth();
        
        // 延迟执行，确保在Django admin的脚本之后执行
        setTimeout(enforceSelectorWidth, 100);
        setTimeout(enforceSelectorWidth, 500);
        setTimeout(enforceSelectorWidth, 1000);
        
        // 添加模块筛选功能（多次尝试，确保DOM加载完成）
        setTimeout(addModuleFilter, 100);
        setTimeout(addModuleFilter, 300);
        setTimeout(addModuleFilter, 500);
        setTimeout(addModuleFilter, 1000);
        setTimeout(addModuleFilter, 2000);
    }

    $(document).ready(function() {
        console.log('[Permission Filter] DOM ready');
        init();
        
        // 使用MutationObserver监听DOM变化，确保动态添加的元素也能应用样式
        if (typeof MutationObserver !== 'undefined') {
            var observer = new MutationObserver(function(mutations) {
                enforceSelectorWidth();
                // 如果选择器存在但筛选器不存在，添加筛选器
                if (($('.selector').length > 0 || $('select[id*="custom_permissions"]').length > 0) && 
                    $('.module-filter-container').length === 0 && 
                    $('#module-filter-select').length === 0) {
                    console.log('[Permission Filter] MutationObserver检测到选择器，尝试添加筛选器');
                    setTimeout(addModuleFilter, 100);
                }
            });
            
            // 观察body的变化
            if (document.body) {
                observer.observe(document.body, {
                    childList: true,
                    subtree: true
                });
            }
        }
        
        // Django 4.2+ 的 filter_horizontal widget 已经有原生搜索框
        // 不再需要添加自定义搜索框，避免功能重复
        // 如果需要增强原生搜索框的功能，可以在这里添加

        // 自定义搜索框功能已移除，使用 Django 原生的搜索框
    });
    
    // 也监听window.load事件，确保所有资源加载完成
    $(window).on('load', function() {
        console.log('[Permission Filter] Window loaded');
        setTimeout(addModuleFilter, 500);
    });

})();

