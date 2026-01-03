/**
 * Bootstrap 模态框快速修复脚本
 * 
 * 解决三个核心问题：
 * 1. DOM结构错误：将模态框移动到body下
 * 2. CSS覆盖冲突：移除workspace CSS的!important覆盖
 * 3. z-index异常：重置为正确的值
 * 
 * 注意：此脚本已被 modal-manager.js 替代，保留仅为兼容性
 */

(function() {
    'use strict';

    // 防重复执行：在脚本最开始就检查，避免任何执行
    if (window._ModalQuickFixInitialized) {
        return;
    }
    
    // 立即标记为已初始化，防止并发执行
    window._ModalQuickFixInitialized = true;

    // 完全静默模式：默认不输出任何日志（可通过设置 window.MODAL_QUICK_FIX_DEBUG=true 开启详细日志）
    const DEBUG_MODE = window.MODAL_QUICK_FIX_DEBUG === true;
    
    function log(...args) {
        // 默认不输出任何日志，除非明确开启调试模式
        if (DEBUG_MODE) {
            console.log(...args);
        }
    }

    /**
     * 将模态框移动到body下
     */
    function moveModalsToBody() {
        const modals = document.querySelectorAll('.modal');
        let movedCount = 0;

        modals.forEach(function(modal) {
            // 检查模态框是否已经在body下
            let parent = modal.parentElement;
            let isInBody = false;
            
            while (parent) {
                if (parent === document.body) {
                    isInBody = true;
                    break;
                }
                parent = parent.parentElement;
            }

            // 如果不在body下，移动到body下
            if (!isInBody) {
                log('移动模态框到body:', modal.id || modal.className);
                document.body.appendChild(modal);
                movedCount++;
            }
        });

        if (movedCount > 0) {
            log(`✅ 已移动 ${movedCount} 个模态框到body下`);
        } else {
            log('✓ 所有模态框已在body下');
        }
    }

    /**
     * 修复CSS覆盖冲突
     */
    function fixCSSOverrides() {
        const modals = document.querySelectorAll('.modal');
        
        modals.forEach(function(modal) {
            // 移除可能被workspace CSS覆盖的样式
            // 重置为Bootstrap默认值，但使用更高的z-index
            modal.style.setProperty('z-index', '1055', 'important');
            modal.style.setProperty('position', 'fixed', 'important');
            
            // 确保不继承父容器的transform等属性
            modal.style.setProperty('transform', 'none', 'important');
            modal.style.setProperty('opacity', '1', 'important');
        });

        // 修复遮罩层
        const backdrops = document.querySelectorAll('.modal-backdrop');
        backdrops.forEach(function(backdrop) {
            backdrop.style.setProperty('z-index', '1050', 'important');
        });

        log('✅ 已修复CSS覆盖冲突');
    }

    /**
     * 修复z-index异常
     */
    function fixZIndex() {
        const modals = document.querySelectorAll('.modal');
        const backdrops = document.querySelectorAll('.modal-backdrop');

        // 设置正确的z-index值
        modals.forEach(function(modal) {
            modal.style.setProperty('z-index', '1055', 'important');
        });

        backdrops.forEach(function(backdrop) {
            backdrop.style.setProperty('z-index', '1050', 'important');
        });

        log('✅ 已修复z-index值');
    }

    /**
     * 监听新创建的模态框
     */
    let observerInstance = null;
    function setupObserver() {
        // 如果已经设置了观察器，不再重复设置
        if (observerInstance) {
            return;
        }

        observerInstance = new MutationObserver(function(mutations) {
            let hasNewModal = false;
            
            // 检查新添加的模态框
            mutations.forEach(function(mutation) {
                mutation.addedNodes.forEach(function(node) {
                    if (node.nodeType === 1) { // Element node
                        // 检查是否是模态框
                        if (node.classList && node.classList.contains('modal')) {
                            hasNewModal = true;
                        }
                        // 检查子元素中是否有模态框
                        const modals = node.querySelectorAll && node.querySelectorAll('.modal');
                        if (modals && modals.length > 0) {
                            hasNewModal = true;
                        }
                    }
                });
            });

            // 只在检测到新模态框时才执行修复
            if (hasNewModal) {
                log('检测到新模态框，应用修复...');
                moveModalsToBody();
                fixCSSOverrides();
                fixZIndex();
            }
        });

        observerInstance.observe(document.body, {
            childList: true,
            subtree: true
        });

        log('✅ 已设置观察器，监听新模态框');
    }

    /**
     * 执行所有修复
     */
    let isInitialized = false;
    function applyAllFixes() {
        // 防止重复执行
        if (isInitialized) {
            return;
        }
        
        moveModalsToBody();
        fixCSSOverrides();
        fixZIndex();
        setupObserver();
        
        isInitialized = true;
        log('🎉 快速修复完成！');
    }

    // DOM加载完成后执行
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', applyAllFixes, { once: true });
    } else {
        applyAllFixes();
    }

    // 也监听页面可见性变化（处理单页应用）- 但只执行必要的修复
    let visibilityHandlerAdded = false;
    if (!visibilityHandlerAdded) {
        document.addEventListener('visibilitychange', function() {
            if (!document.hidden && !isInitialized) {
                // 只在未初始化时执行
                applyAllFixes();
            }
        }, { once: true });
        visibilityHandlerAdded = true;
    }

    // 导出到全局
    window.ModalQuickFix = {
        apply: applyAllFixes,
        moveModalsToBody: moveModalsToBody,
        fixCSSOverrides: fixCSSOverrides,
        fixZIndex: fixZIndex
    };
})();

