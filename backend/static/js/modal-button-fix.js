/**
 * 模态框按钮交互修复脚本
 * 
 * 修复模态框按钮无法点击的问题
 * 确保所有按钮都可以正常交互
 */

(function() {
    'use strict';

    // 防重复执行：如果已经执行过，直接返回
    if (window._ModalButtonFixInitialized) {
        return;
    }
    
    // 立即标记为已初始化
    window._ModalButtonFixInitialized = true;

    // 静默模式：默认不输出日志（可通过设置 window.MODAL_BUTTON_FIX_DEBUG=true 开启）
    const DEBUG_MODE = window.MODAL_BUTTON_FIX_DEBUG === true;
    
    function log(...args) {
        if (DEBUG_MODE) {
            console.log(...args);
        }
    }

    /**
     * 修复模态框按钮的交互性
     */
    function fixModalButtons() {
        // 查找所有模态框
        const modals = document.querySelectorAll('.modal.show');
        
        modals.forEach(modal => {
            // 确保模态框内容可以交互
            const dialog = modal.querySelector('.modal-dialog');
            const content = modal.querySelector('.modal-content');
            const header = modal.querySelector('.modal-header');
            const body = modal.querySelector('.modal-body');
            const footer = modal.querySelector('.modal-footer');
            
            // 设置 pointer-events
            if (dialog) {
                dialog.style.setProperty('pointer-events', 'auto', 'important');
            }
            if (content) {
                content.style.setProperty('pointer-events', 'auto', 'important');
            }
            if (header) {
                header.style.setProperty('pointer-events', 'auto', 'important');
            }
            if (body) {
                body.style.setProperty('pointer-events', 'auto', 'important');
            }
            if (footer) {
                footer.style.setProperty('pointer-events', 'auto', 'important');
            }
            
            // 确保所有按钮都可以点击
            const buttons = modal.querySelectorAll('button, a, input[type="button"], input[type="submit"]');
            buttons.forEach(button => {
                button.style.setProperty('pointer-events', 'auto', 'important');
                button.style.setProperty('cursor', 'pointer', 'important');
            });
        });
    }

    /**
     * 监听模态框显示事件
     */
    function setupModalListeners() {
        // 监听所有模态框的显示事件
        document.addEventListener('show.bs.modal', function(e) {
            // 模态框即将显示
        }, true);

        document.addEventListener('shown.bs.modal', function(e) {
            // 模态框已显示，修复按钮
            setTimeout(fixModalButtons, 100);
        }, true);

        // 使用 MutationObserver 监听模态框的显示
        const observer = new MutationObserver(function(mutations) {
            mutations.forEach(function(mutation) {
                mutation.addedNodes.forEach(function(node) {
                    if (node.nodeType === 1) {
                        // 检查是否是模态框
                        if (node.classList && node.classList.contains('modal')) {
                            if (node.classList.contains('show')) {
                                setTimeout(fixModalButtons, 100);
                            }
                        }
                        // 检查子元素中是否有模态框
                        const modals = node.querySelectorAll && node.querySelectorAll('.modal.show');
                        if (modals && modals.length > 0) {
                            setTimeout(fixModalButtons, 100);
                        }
                    }
                });
                
                // 检查 class 变化
                if (mutation.type === 'attributes' && mutation.attributeName === 'class') {
                    const target = mutation.target;
                    if (target.classList && target.classList.contains('modal') && target.classList.contains('show')) {
                        setTimeout(fixModalButtons, 100);
                    }
                }
            });
        });

        observer.observe(document.body, {
            childList: true,
            subtree: true,
            attributes: true,
            attributeFilter: ['class']
        });
    }

    /**
     * 初始化
     */
    function init() {
        // 立即修复已显示的模态框
        fixModalButtons();
        
        // 设置监听器
        setupModalListeners();
        
        log('✅ 模态框按钮交互修复脚本已加载');
    }

    // DOM 加载完成后初始化
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    // 导出到全局
    window.ModalButtonFix = {
        fix: fixModalButtons
    };
})();

