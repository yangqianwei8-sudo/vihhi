/**
 * 统一模态框管理工具
 * 
 * 一次性解决所有模态框遮罩层问题：
 * 1. 统一管理模态框实例，避免重复创建
 * 2. 自动清理多余的backdrop，防止叠加
 * 3. 确保z-index正确，防止遮罩层覆盖模态框
 * 4. 确保DOM结构正确（模态框在body下）
 * 5. 防止重复绑定事件监听器
 * 
 * 使用方法：
 * ModalManager.show('modalId') - 显示模态框
 * ModalManager.hide('modalId') - 隐藏模态框
 * ModalManager.getOrCreateInstance('modalId') - 获取或创建实例
 */

(function() {
    'use strict';

    // 调试模式：默认关闭，生产环境不输出日志
    // 开发环境可通过设置 window.MODAL_MANAGER_DEBUG = true 来开启调试日志
    const DEBUG_MODE = window.MODAL_MANAGER_DEBUG === true;

    // 日志输出函数
    function log(...args) {
        if (DEBUG_MODE) {
            console.log(...args);
        }
    }

    function error(...args) {
        console.error(...args); // 错误始终输出
    }

    function warn(...args) {
        if (DEBUG_MODE) {
            console.warn(...args);
        }
    }

    // Bootstrap 标准 z-index 值
    const MODAL_Z_INDEX = 1055;
    const BACKDROP_Z_INDEX = 1050;

    // 存储所有模态框实例
    const modalInstances = new Map();
    
    // 存储已绑定事件的模态框ID
    const boundModals = new Set();

    /**
     * 确保模态框在body下
     */
    function ensureModalInBody(modalElement) {
        if (!modalElement) return false;
        
        let parent = modalElement.parentElement;
        let isInBody = false;
        
        while (parent && parent !== document.body) {
            parent = parent.parentElement;
        }
        
        if (parent === document.body) {
            isInBody = true;
        }
        
        if (!isInBody) {
            log('[ModalManager] 移动模态框到body:', modalElement.id || '未命名');
            document.body.appendChild(modalElement);
            return true;
        }
        
        return false;
    }

    /**
     * 清理多余的backdrop
     * 注意：只在确认有多余backdrop时才清理，避免删除正在使用的backdrop
     */
    function cleanupBackdrops() {
        const backdrops = document.querySelectorAll('.modal-backdrop');
        const visibleModals = document.querySelectorAll('.modal.show');
        
        // 如果可见的模态框数量少于backdrop数量，清理多余的
        // 但要确保至少保留一个backdrop（如果至少有一个可见模态框）
        if (backdrops.length > visibleModals.length && visibleModals.length > 0) {
            log(`[ModalManager] 检测到 ${backdrops.length} 个backdrop，但只有 ${visibleModals.length} 个可见模态框，清理多余的...`);
            
            // 保留最后一个，删除其他的
            const toRemove = backdrops.length - visibleModals.length;
            for (let i = 0; i < toRemove; i++) {
                const backdrop = backdrops[i];
                if (backdrop && backdrop.parentNode) {
                    backdrop.parentNode.removeChild(backdrop);
                    log('[ModalManager] 已删除多余的backdrop');
                }
            }
        }
        
        // 确保所有backdrop的z-index正确
        const remainingBackdrops = document.querySelectorAll('.modal-backdrop');
        remainingBackdrops.forEach((backdrop) => {
            backdrop.style.setProperty('z-index', BACKDROP_Z_INDEX.toString(), 'important');
        });
    }

    /**
     * 确保模态框的z-index正确
     */
    function ensureModalZIndex(modalElement) {
        if (!modalElement) return;
        
        modalElement.style.setProperty('z-index', MODAL_Z_INDEX.toString(), 'important');
        modalElement.style.setProperty('position', 'fixed', 'important');
        
        // 确保模态框可以交互
        modalElement.style.setProperty('pointer-events', 'none', 'important');
        
        const dialog = modalElement.querySelector('.modal-dialog');
        if (dialog) {
            dialog.style.setProperty('pointer-events', 'auto', 'important');
        }
    }

    /**
     * 绑定模态框事件（只绑定一次）
     */
    function bindModalEvents(modalElement) {
        if (!modalElement || boundModals.has(modalElement.id)) {
            return;
        }
        
        boundModals.add(modalElement.id);
        
        // 监听显示事件
        // 注意：此时Bootstrap还未创建backdrop，所以不清理
        modalElement.addEventListener('show.bs.modal', function() {
            ensureModalInBody(modalElement);
            ensureModalZIndex(modalElement);
            // 不在这里清理backdrop，因为Bootstrap还没有创建
        }, { once: false });
        
        // 监听已显示事件
        // 此时Bootstrap已经创建了backdrop，可以安全地设置z-index和清理多余的
        modalElement.addEventListener('shown.bs.modal', function() {
            ensureModalZIndex(modalElement);
            
            // 延迟清理，确保Bootstrap已经完成backdrop的创建
            setTimeout(() => {
                cleanupBackdrops();
                
                // 确保backdrop的z-index正确
                const backdrops = document.querySelectorAll('.modal-backdrop');
                backdrops.forEach(backdrop => {
                    backdrop.style.setProperty('z-index', BACKDROP_Z_INDEX.toString(), 'important');
                });
            }, 50);
        }, { once: false });
        
        // 监听隐藏事件
        modalElement.addEventListener('hide.bs.modal', function() {
            cleanupBackdrops();
        }, { once: false });
        
        // 监听已隐藏事件
        modalElement.addEventListener('hidden.bs.modal', function() {
            cleanupBackdrops();
            
            // 如果所有模态框都隐藏了，清理所有backdrop
            const visibleModals = document.querySelectorAll('.modal.show');
            if (visibleModals.length === 0) {
                const backdrops = document.querySelectorAll('.modal-backdrop');
                backdrops.forEach(backdrop => {
                    if (backdrop.parentNode) {
                        backdrop.parentNode.removeChild(backdrop);
                    }
                });
                document.body.classList.remove('modal-open');
            }
        }, { once: false });
        
        log('[ModalManager] 已为模态框绑定事件:', modalElement.id);
    }

    /**
     * 获取或创建模态框实例
     */
    function getOrCreateInstance(modalId) {
        if (!modalId) {
            error('[ModalManager] 模态框ID不能为空');
            return null;
        }
        
        const modalElement = document.getElementById(modalId);
        if (!modalElement) {
            error('[ModalManager] 未找到模态框:', modalId);
            return null;
        }
        
        // 确保模态框在body下
        ensureModalInBody(modalElement);
        
        // 确保z-index正确
        ensureModalZIndex(modalElement);
        
        // 绑定事件（只绑定一次）
        bindModalEvents(modalElement);
        
        // 如果已有实例，直接返回
        if (modalInstances.has(modalId)) {
            return modalInstances.get(modalId);
        }
        
        // 创建新实例
        if (typeof bootstrap !== 'undefined' && bootstrap.Modal) {
            const instance = bootstrap.Modal.getOrCreateInstance(modalElement);
            modalInstances.set(modalId, instance);
            log('[ModalManager] 创建模态框实例:', modalId);
            return instance;
        } else {
            warn('[ModalManager] Bootstrap未加载，无法创建模态框实例');
            return null;
        }
    }

    /**
     * 显示模态框
     */
    function show(modalId) {
        const instance = getOrCreateInstance(modalId);
        if (instance) {
            // 显示模态框（Bootstrap会自动创建backdrop）
            instance.show();
            
            // 延迟确保z-index和backdrop正确（Bootstrap在show后异步创建backdrop）
            setTimeout(() => {
                ensureModalZIndex(document.getElementById(modalId));
                
                // 确保backdrop存在且z-index正确
                const backdrops = document.querySelectorAll('.modal-backdrop');
                backdrops.forEach(backdrop => {
                    backdrop.style.setProperty('z-index', BACKDROP_Z_INDEX.toString(), 'important');
                });
                
                // 清理多余的backdrop（如果有）
                cleanupBackdrops();
            }, 100);
        } else {
            error('[ModalManager] 无法显示模态框:', modalId);
        }
    }

    /**
     * 隐藏模态框
     */
    function hide(modalId) {
        const instance = getOrCreateInstance(modalId);
        if (instance) {
            instance.hide();
            cleanupBackdrops();
        } else {
            error('[ModalManager] 无法隐藏模态框:', modalId);
        }
    }

    /**
     * 初始化所有模态框
     */
    function initAllModals() {
        const modals = document.querySelectorAll('.modal');
        log(`[ModalManager] 初始化 ${modals.length} 个模态框`);
        
        modals.forEach(modal => {
            if (modal.id) {
                ensureModalInBody(modal);
                ensureModalZIndex(modal);
                bindModalEvents(modal);
            }
        });
    }

    /**
     * 监听新添加的模态框
     */
    function setupObserver() {
        const observer = new MutationObserver(function(mutations) {
            mutations.forEach(function(mutation) {
                mutation.addedNodes.forEach(function(node) {
                    if (node.nodeType === 1) { // Element node
                        // 检查是否是模态框
                        if (node.classList && node.classList.contains('modal')) {
                            log('[ModalManager] 检测到新模态框，自动初始化');
                            if (node.id) {
                                ensureModalInBody(node);
                                ensureModalZIndex(node);
                                bindModalEvents(node);
                            }
                        }
                        // 检查子元素中是否有模态框
                        const modals = node.querySelectorAll && node.querySelectorAll('.modal');
                        if (modals && modals.length > 0) {
                            modals.forEach(modal => {
                                if (modal.id) {
                                    ensureModalInBody(modal);
                                    ensureModalZIndex(modal);
                                    bindModalEvents(modal);
                                }
                            });
                        }
                    }
                });
            });
        });

        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
        
        log('[ModalManager] 已设置观察器，监听新模态框');
    }

    /**
     * 监听backdrop的变化
     */
    function setupBackdropObserver() {
        const backdropObserver = new MutationObserver(function(mutations) {
            // 检查是否有backdrop被添加
            let backdropAdded = false;
            mutations.forEach(mutation => {
                mutation.addedNodes.forEach(node => {
                    if (node.nodeType === 1 && node.classList && node.classList.contains('modal-backdrop')) {
                        backdropAdded = true;
                    }
                });
            });
            
            if (backdropAdded) {
                // 延迟处理，确保Bootstrap完成操作
                setTimeout(() => {
                    // 确保backdrop的z-index正确
                    const backdrops = document.querySelectorAll('.modal-backdrop');
                    backdrops.forEach(backdrop => {
                        backdrop.style.setProperty('z-index', BACKDROP_Z_INDEX.toString(), 'important');
                    });
                    
                    // 清理多余的backdrop
                    cleanupBackdrops();
                    
                    // 确保所有可见模态框的z-index正确
                    const visibleModals = document.querySelectorAll('.modal.show');
                    visibleModals.forEach(modal => {
                        ensureModalZIndex(modal);
                    });
                }, 50);
            } else {
                // 如果没有添加backdrop，只清理多余的
                cleanupBackdrops();
            }
        });

        backdropObserver.observe(document.body, {
            childList: true,
            subtree: false
        });
        
        log('[ModalManager] 已设置backdrop观察器');
    }

    /**
     * 初始化
     */
    function init() {
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', function() {
                initAllModals();
                setupObserver();
                setupBackdropObserver();
            });
        } else {
            initAllModals();
            setupObserver();
            setupBackdropObserver();
        }
        
        log('[ModalManager] 模态框管理器已初始化');
    }

    // 立即初始化
    init();

    // 导出到全局
    window.ModalManager = {
        show: show,
        hide: hide,
        getOrCreateInstance: getOrCreateInstance,
        init: init,
        cleanupBackdrops: cleanupBackdrops,
        ensureModalZIndex: ensureModalZIndex
    };

})();

