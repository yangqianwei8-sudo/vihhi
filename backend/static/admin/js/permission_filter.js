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

    $(document).ready(function() {
        // 查找所有权限选择器
        $('.selector').each(function() {
            var $selector = $(this);
            var $available = $selector.find('.selector-available');
            var $chosen = $selector.find('.selector-chosen');
            
            // 如果找不到选择器，跳过
            if ($available.length === 0 || $chosen.length === 0) {
                return;
            }

            // 为可用权限列表添加搜索框
            var $availableSelect = $available.find('select');
            var $availableUl = $available.find('ul');
            
            if ($availableSelect.length > 0 && $availableUl.length === 0) {
                // 如果是 select 元素，转换为 ul/li 结构（如果需要）
                // 这里我们只添加搜索功能
                addSearchBox($available, 'available');
            } else if ($availableUl.length > 0) {
                // 如果已经是 ul 结构，添加搜索框
                addSearchBox($available, 'available');
            }

            // 为已选权限列表添加搜索框
            var $chosenSelect = $chosen.find('select');
            var $chosenUl = $chosen.find('ul');
            
            if ($chosenSelect.length > 0 && $chosenUl.length === 0) {
                addSearchBox($chosen, 'chosen');
            } else if ($chosenUl.length > 0) {
                addSearchBox($chosen, 'chosen');
            }
        });

        /**
         * 添加搜索框
         */
        function addSearchBox($container, type) {
            // 检查是否已经添加了搜索框
            if ($container.find('.permission-search-box').length > 0) {
                return;
            }

            var $searchBox = $('<input>', {
                type: 'text',
                class: 'permission-search-box',
                placeholder: '搜索权限代码或名称...',
                style: 'width: 100%; padding: 8px; margin-bottom: 10px; border: 1px solid #ddd; border-radius: 4px;'
            });

            // 插入搜索框
            var $select = $container.find('select');
            var $ul = $container.find('ul');
            
            if ($select.length > 0) {
                $searchBox.insertBefore($select);
            } else if ($ul.length > 0) {
                $searchBox.insertBefore($ul);
            } else {
                $searchBox.prependTo($container);
            }

            // 添加搜索功能
            $searchBox.on('input', function() {
                var searchTerm = $(this).val().toLowerCase();
                filterPermissions($container, searchTerm, type);
            });

            // 添加清除按钮
            var $clearBtn = $('<button>', {
                type: 'button',
                class: 'permission-clear-search',
                text: '清除',
                style: 'margin-left: 5px; padding: 6px 12px; border: 1px solid #ddd; border-radius: 4px; background-color: #f8f9fa; cursor: pointer; font-size: 12px;'
            });

            $clearBtn.on('click', function() {
                $searchBox.val('');
                filterPermissions($container, '', type);
            });

            $searchBox.after($clearBtn);
        }

        /**
         * 过滤权限
         */
        function filterPermissions($container, searchTerm, type) {
            var $select = $container.find('select');
            var $ul = $container.find('ul');
            var $options = $select.find('option');
            var $items = $ul.find('li');

            if ($select.length > 0 && $options.length > 0) {
                // 处理 select 元素
                $options.each(function() {
                    var $option = $(this);
                    var text = $option.text().toLowerCase();
                    var value = $option.val().toLowerCase();
                    
                    if (searchTerm === '' || text.indexOf(searchTerm) !== -1 || value.indexOf(searchTerm) !== -1) {
                        $option.show();
                    } else {
                        $option.hide();
                    }
                });
            } else if ($ul.length > 0 && $items.length > 0) {
                // 处理 ul/li 元素
                $items.each(function() {
                    var $item = $(this);
                    var text = $item.text().toLowerCase();
                    
                    if (searchTerm === '' || text.indexOf(searchTerm) !== -1) {
                        $item.show();
                        if (searchTerm !== '') {
                            $item.addClass('highlight');
                        } else {
                            $item.removeClass('highlight');
                        }
                    } else {
                        $item.hide();
                        $item.removeClass('highlight');
                    }
                });
            }
        }

        // 添加提示信息
        $('.selector').each(function() {
            var $selector = $(this);
            var $helpText = $selector.find('.selector-help-text');
            
            if ($helpText.length === 0) {
                var helpHtml = '<div class="selector-help-text">' +
                    '<strong>提示：</strong>在搜索框中输入权限代码或名称可以快速查找权限。' +
                    '例如：输入 "plan_management" 可以筛选所有计划管理权限。' +
                    '</div>';
                $selector.append(helpHtml);
            }
        });
    });

})();

