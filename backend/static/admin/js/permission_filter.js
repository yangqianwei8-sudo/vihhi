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
        // Django 4.2+ 的 filter_horizontal widget 已经有原生搜索框
        // 不再需要添加自定义搜索框，避免功能重复
        // 如果需要增强原生搜索框的功能，可以在这里添加

        // 自定义搜索框功能已移除，使用 Django 原生的搜索框
    });

})();

