/**
 * 两栏布局滚动条修复脚本
 * 确保当使用 two-column-layout 时，body 的滚动条被禁用
 * 解决双重滚动条问题
 */

(function() {
    'use strict';

    /**
     * 修复两栏布局的滚动条问题
     */
    function fixTwoColumnLayoutScroll() {
        // 查找所有 two-column-layout 元素
        const layouts = document.querySelectorAll('.two-column-layout');
        
        if (layouts.length > 0) {
            // 如果页面使用了 two-column-layout，禁用 body 滚动条
            document.body.style.overflowY = 'hidden';
            document.body.style.height = '100%';
            
            // 添加类名作为备用方案（用于不支持 :has() 的浏览器）
            if (!document.body.classList.contains('two-column-layout-active')) {
                document.body.classList.add('two-column-layout-active');
            }
        } else {
            // 如果没有使用 two-column-layout，恢复 body 滚动条
            document.body.style.overflowY = '';
            document.body.style.height = '';
            document.body.classList.remove('two-column-layout-active');
        }
    }

    /**
     * 观察 DOM 变化，动态修复
     */
    function observeLayoutChanges() {
        const observer = new MutationObserver(function(mutations) {
            let shouldFix = false;
            
            mutations.forEach(function(mutation) {
                // 检查是否有 two-column-layout 被添加或移除
                mutation.addedNodes.forEach(function(node) {
                    if (node.nodeType === 1) {
                        if (node.classList && node.classList.contains('two-column-layout')) {
                            shouldFix = true;
                        }
                        if (node.querySelectorAll && node.querySelectorAll('.two-column-layout').length > 0) {
                            shouldFix = true;
                        }
                    }
                });
                
                mutation.removedNodes.forEach(function(node) {
                    if (node.nodeType === 1) {
                        if (node.classList && node.classList.contains('two-column-layout')) {
                            shouldFix = true;
                        }
                    }
                });
            });
            
            if (shouldFix) {
                fixTwoColumnLayoutScroll();
            }
        });

        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
    }

    // 初始化
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            fixTwoColumnLayoutScroll();
            observeLayoutChanges();
        });
    } else {
        fixTwoColumnLayoutScroll();
        observeLayoutChanges();
    }

    // 导出函数供其他脚本使用
    if (typeof window !== 'undefined') {
        window.fixTwoColumnLayoutScroll = fixTwoColumnLayoutScroll;
    }
})();
