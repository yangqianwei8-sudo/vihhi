/**
 * 模态框辅助函数
 * 
 * 提供统一的模态框打开/关闭方法，自动使用ModalManager
 * 避免遮罩层问题，确保所有模态框正常工作
 * 
 * 使用方法：
 * openModal('modalId') - 打开模态框
 * closeModal('modalId') - 关闭模态框
 * toggleModal('modalId') - 切换模态框显示状态
 * getModalInstance('modalId') - 获取模态框实例
 */

(function() {
    'use strict';

    // 调试模式：设置为false可禁用详细日志（生产环境建议关闭）
    const DEBUG_MODE = window.MODAL_HELPERS_DEBUG !== false; // 默认开启，可通过设置window.MODAL_HELPERS_DEBUG=false关闭

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

    /**
     * 打开模态框
     * @param {string} modalId - 模态框ID
     * @param {object} options - 可选配置
     * @returns {boolean} 是否成功打开
     */
    function openModal(modalId, options) {
        if (!modalId) {
            error('[ModalHelpers] 模态框ID不能为空');
            return false;
        }

        const modalElement = document.getElementById(modalId);
        if (!modalElement) {
            error('[ModalHelpers] 未找到模态框:', modalId);
            return false;
        }

        try {
            // 优先使用ModalManager
            if (typeof window.ModalManager !== 'undefined') {
                window.ModalManager.show(modalId);
                
                // 如果有配置选项，应用它们
                if (options) {
                    const instance = window.ModalManager.getOrCreateInstance(modalId);
                    if (instance && options.onShown) {
                        modalElement.addEventListener('shown.bs.modal', function handler() {
                            options.onShown();
                            modalElement.removeEventListener('shown.bs.modal', handler);
                        }, { once: true });
                    }
                }
                
                return true;
            }
            
            // 降级到Bootstrap原生API
            if (typeof bootstrap !== 'undefined' && bootstrap.Modal) {
                const modal = bootstrap.Modal.getOrCreateInstance(modalElement);
                modal.show();
                
                if (options && options.onShown) {
                    modalElement.addEventListener('shown.bs.modal', function handler() {
                        options.onShown();
                        modalElement.removeEventListener('shown.bs.modal', handler);
                    }, { once: true });
                }
                
                return true;
            }
            
            console.warn('[ModalHelpers] Bootstrap未加载，无法打开模态框');
            return false;
        } catch (error) {
            console.error('[ModalHelpers] 打开模态框失败:', error);
            return false;
        }
    }

    /**
     * 关闭模态框
     * @param {string} modalId - 模态框ID
     * @returns {boolean} 是否成功关闭
     */
    function closeModal(modalId) {
        if (!modalId) {
            console.error('[ModalHelpers] 模态框ID不能为空');
            return false;
        }

        const modalElement = document.getElementById(modalId);
        if (!modalElement) {
            console.error('[ModalHelpers] 未找到模态框:', modalId);
            return false;
        }

        try {
            // 优先使用ModalManager
            if (typeof window.ModalManager !== 'undefined') {
                window.ModalManager.hide(modalId);
                return true;
            }
            
            // 降级到Bootstrap原生API
            if (typeof bootstrap !== 'undefined' && bootstrap.Modal) {
                const modal = bootstrap.Modal.getInstance(modalElement);
                if (modal) {
                    modal.hide();
                    return true;
                }
            }
            
            console.warn('[ModalHelpers] Bootstrap未加载，无法关闭模态框');
            return false;
        } catch (error) {
            console.error('[ModalHelpers] 关闭模态框失败:', error);
            return false;
        }
    }

    /**
     * 切换模态框显示状态
     * @param {string} modalId - 模态框ID
     * @returns {boolean} 是否成功切换
     */
    function toggleModal(modalId) {
        if (!modalId) {
            console.error('[ModalHelpers] 模态框ID不能为空');
            return false;
        }

        const modalElement = document.getElementById(modalId);
        if (!modalElement) {
            console.error('[ModalHelpers] 未找到模态框:', modalId);
            return false;
        }

        // 检查模态框是否可见
        const isVisible = modalElement.classList.contains('show');
        
        if (isVisible) {
            return closeModal(modalId);
        } else {
            return openModal(modalId);
        }
    }

    /**
     * 获取模态框实例
     * @param {string} modalId - 模态框ID
     * @returns {object|null} 模态框实例
     */
    function getModalInstance(modalId) {
        if (!modalId) {
            error('[ModalHelpers] 模态框ID不能为空');
            return null;
        }

        const modalElement = document.getElementById(modalId);
        if (!modalElement) {
            error('[ModalHelpers] 未找到模态框:', modalId);
            return null;
        }

        try {
            // 优先使用ModalManager
            if (typeof window.ModalManager !== 'undefined') {
                return window.ModalManager.getOrCreateInstance(modalId);
            }
            
            // 降级到Bootstrap原生API
            if (typeof bootstrap !== 'undefined' && bootstrap.Modal) {
                return bootstrap.Modal.getOrCreateInstance(modalElement);
            }
            
            return null;
        } catch (err) {
            error('[ModalHelpers] 获取模态框实例失败:', err);
            return null;
        }
    }

    /**
     * 检查模态框是否可见
     * @param {string} modalId - 模态框ID
     * @returns {boolean} 是否可见
     */
    function isModalVisible(modalId) {
        const modalElement = document.getElementById(modalId);
        if (!modalElement) {
            return false;
        }
        return modalElement.classList.contains('show');
    }

    /**
     * 等待模态框显示完成
     * @param {string} modalId - 模态框ID
     * @returns {Promise} Promise对象
     */
    function waitForModalShown(modalId) {
        return new Promise((resolve) => {
            const modalElement = document.getElementById(modalId);
            if (!modalElement) {
                resolve(false);
                return;
            }

            if (modalElement.classList.contains('show')) {
                resolve(true);
                return;
            }

            modalElement.addEventListener('shown.bs.modal', function handler() {
                modalElement.removeEventListener('shown.bs.modal', handler);
                resolve(true);
            }, { once: true });
        });
    }

    /**
     * 等待模态框隐藏完成
     * @param {string} modalId - 模态框ID
     * @returns {Promise} Promise对象
     */
    function waitForModalHidden(modalId) {
        return new Promise((resolve) => {
            const modalElement = document.getElementById(modalId);
            if (!modalElement) {
                resolve(false);
                return;
            }

            if (!modalElement.classList.contains('show')) {
                resolve(true);
                return;
            }

            modalElement.addEventListener('hidden.bs.modal', function handler() {
                modalElement.removeEventListener('hidden.bs.modal', handler);
                resolve(true);
            }, { once: true });
        });
    }

    // 导出到全局
    window.ModalHelpers = {
        open: openModal,
        close: closeModal,
        toggle: toggleModal,
        getInstance: getModalInstance,
        isVisible: isModalVisible,
        waitForShown: waitForModalShown,
        waitForHidden: waitForModalHidden
    };

    // 为了向后兼容，也导出简写形式
    window.openModal = openModal;
    window.closeModal = closeModal;
    window.toggleModal = toggleModal;
    window.getModalInstance = getModalInstance;

    log('[ModalHelpers] 模态框辅助函数已加载');
})();

