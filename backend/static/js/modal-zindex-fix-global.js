/**
 * Bootstrap 模态框 z-index 全局修复脚本
 * 
 * 适用于整个系统的所有模态框
 * 自动修复模态框被遮罩层覆盖的问题
 */

(function() {
    'use strict';

    // 防重复执行：如果已经执行过，直接返回
    if (window._ModalZIndexFixInitialized) {
        return;
    }
    
    // 立即标记为已初始化
    window._ModalZIndexFixInitialized = true;

    // 静默模式：默认不输出日志（可通过设置 window.MODAL_ZINDEX_FIX_DEBUG=true 开启）
    const DEBUG_MODE = window.MODAL_ZINDEX_FIX_DEBUG === true;
    
    function log(...args) {
        if (DEBUG_MODE) {
            console.log(...args);
        }
    }

    // 模态框 z-index 值（高于遮罩层）
    const MODAL_Z_INDEX = 10050;
    const BACKDROP_Z_INDEX = 10049;

    /**
     * 修复单个模态框的 z-index
     */
    function fixModalZIndex(modalElement) {
        if (!modalElement) return;

        // 监听模态框显示事件
        modalElement.addEventListener('show.bs.modal', function() {
            // 预先设置模态框的 z-index
            modalElement.style.setProperty('z-index', MODAL_Z_INDEX.toString(), 'important');
            modalElement.style.setProperty('position', 'fixed', 'important');
        }, { once: false });

        // 监听模态框已显示事件
        modalElement.addEventListener('shown.bs.modal', function() {
            // 查找遮罩层
            const backdrops = document.querySelectorAll('.modal-backdrop');
            const lastBackdrop = backdrops[backdrops.length - 1];
            
            if (lastBackdrop) {
                // 设置遮罩层的 z-index（低于模态框）
                lastBackdrop.style.setProperty('z-index', BACKDROP_Z_INDEX.toString(), 'important');
                lastBackdrop.style.setProperty('pointer-events', 'auto', 'important');
            }

            // 确保模态框的 z-index
            modalElement.style.setProperty('z-index', MODAL_Z_INDEX.toString(), 'important');
            modalElement.style.setProperty('position', 'fixed', 'important');
            
            // 确保模态框可以交互
            // 将容器的 pointer-events 设置为 none，子元素设置为 auto
            modalElement.style.setProperty('pointer-events', 'none', 'important');
            
            const dialog = modalElement.querySelector('.modal-dialog');
            if (dialog) {
                dialog.style.setProperty('pointer-events', 'auto', 'important');
            }
            
            const content = modalElement.querySelector('.modal-content');
            if (content) {
                content.style.setProperty('pointer-events', 'auto', 'important');
            }
        }, { once: false });
    }

    /**
     * 使用 MutationObserver 监听遮罩层的创建
     */
    function setupBackdropObserver() {
        const observer = new MutationObserver(function(mutations) {
            const modals = document.querySelectorAll('.modal.show');
            const backdrops = document.querySelectorAll('.modal-backdrop');
            
            if (modals.length > 0 && backdrops.length > 0) {
                const lastBackdrop = backdrops[backdrops.length - 1];
                const lastModal = modals[modals.length - 1];
                
                // 确保遮罩层在模态框下方
                lastBackdrop.style.setProperty('z-index', BACKDROP_Z_INDEX.toString(), 'important');
                lastModal.style.setProperty('z-index', MODAL_Z_INDEX.toString(), 'important');
            }
        });

        // 开始观察 body 的变化
        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
    }

    /**
     * 初始化所有模态框的修复
     */
    function initModalFixes() {
        // 修复现有的模态框
        const existingModals = document.querySelectorAll('.modal');
        existingModals.forEach(function(modalElement) {
            fixModalZIndex(modalElement);
        });

        // 监听动态添加的模态框
        const globalObserver = new MutationObserver(function(mutations) {
            const newModals = document.querySelectorAll('.modal');
            newModals.forEach(function(modalElement) {
                if (!modalElement.dataset.zindexFixed) {
                    modalElement.dataset.zindexFixed = 'true';
                    fixModalZIndex(modalElement);
                }
            });
        });

        globalObserver.observe(document.body, {
            childList: true,
            subtree: true
        });

        // 设置遮罩层观察器
        setupBackdropObserver();
    }

    // DOM 加载完成后初始化
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initModalFixes);
    } else {
        initModalFixes();
    }

    // 也监听页面可见性变化（处理单页应用）
    document.addEventListener('visibilitychange', function() {
        if (!document.hidden) {
            const modals = document.querySelectorAll('.modal');
            modals.forEach(function(modalElement) {
                if (!modalElement.dataset.zindexFixed) {
                    modalElement.dataset.zindexFixed = 'true';
                    fixModalZIndex(modalElement);
                }
            });
        }
    });

    log('✅ 模态框 z-index 全局修复脚本已加载');
})();

