/**
 * 模态框 aria-hidden 修复脚本
 * 解决 Bootstrap 模态框在关闭时，如果内部元素仍有焦点，会触发 aria-hidden 警告的问题
 * 
 * 问题：当模态框被设置为 aria-hidden="true" 时，如果内部元素仍然有焦点，
 *       会违反 WAI-ARIA 规范，导致无障碍访问问题。
 * 
 * 解决方案：在模态框关闭之前，先移除内部元素的焦点，然后再设置 aria-hidden
 */

(function() {
    'use strict';

    /**
     * 移除模态框内部元素的焦点
     * @param {HTMLElement} modalElement - 模态框元素
     */
    function removeFocusFromModal(modalElement) {
        if (!modalElement) return;
        
        const activeElement = document.activeElement;
        
        // 如果当前焦点在模态框内部，移除焦点
        if (activeElement && modalElement.contains(activeElement)) {
            // 尝试将焦点移到 body
            if (activeElement.blur) {
                activeElement.blur();
            }
            
            // 确保焦点不在模态框内
            // 使用 setTimeout 确保 blur 操作完成
            setTimeout(() => {
                // 如果焦点仍在模态框内，强制移除
                if (modalElement.contains(document.activeElement)) {
                    document.body.focus();
                    // 如果 body 不能获得焦点，创建一个隐藏的可聚焦元素
                    if (document.activeElement === activeElement) {
                        const tempFocus = document.createElement('div');
                        tempFocus.setAttribute('tabindex', '-1');
                        tempFocus.style.position = 'absolute';
                        tempFocus.style.left = '-9999px';
                        document.body.appendChild(tempFocus);
                        tempFocus.focus();
                        setTimeout(() => {
                            document.body.removeChild(tempFocus);
                        }, 0);
                    }
                }
            }, 0);
        }
    }

    /**
     * 修复单个模态框的 aria-hidden 问题
     * @param {HTMLElement} modalElement - 模态框元素
     */
    function fixModalAriaHidden(modalElement) {
        if (!modalElement) return;

        // 监听 Bootstrap 模态框的隐藏事件
        modalElement.addEventListener('hide.bs.modal', function(event) {
            // 在模态框隐藏之前，先移除焦点
            removeFocusFromModal(modalElement);
        }, { capture: true });

        // 监听隐藏完成事件，确保 aria-hidden 设置正确
        modalElement.addEventListener('hidden.bs.modal', function(event) {
            // 再次确保焦点已移除
            removeFocusFromModal(modalElement);
            
            // 确保 aria-hidden 已正确设置
            if (modalElement.getAttribute('aria-hidden') !== 'true') {
                removeFocusFromModal(modalElement);
                setTimeout(() => {
                    modalElement.setAttribute('aria-hidden', 'true');
                }, 0);
            }
        }, { capture: true });

        // 监听手动设置 aria-hidden 的情况（通过 MutationObserver）
        const observer = new MutationObserver(function(mutations) {
            mutations.forEach(function(mutation) {
                if (mutation.type === 'attributes' && mutation.attributeName === 'aria-hidden') {
                    const newValue = modalElement.getAttribute('aria-hidden');
                    if (newValue === 'true') {
                        // 如果设置为 true，确保没有焦点在模态框内
                        removeFocusFromModal(modalElement);
                    }
                }
            });
        });

        observer.observe(modalElement, {
            attributes: true,
            attributeFilter: ['aria-hidden']
        });
    }

    /**
     * 修复所有现有的模态框
     */
    function fixAllModals() {
        // 查找所有模态框元素
        const modals = document.querySelectorAll('.modal[aria-hidden]');
        modals.forEach(function(modal) {
            fixModalAriaHidden(modal);
        });
    }

    /**
     * 修复新创建的模态框（通过 DOM 观察）
     */
    function observeNewModals() {
        const observer = new MutationObserver(function(mutations) {
            mutations.forEach(function(mutation) {
                mutation.addedNodes.forEach(function(node) {
                    if (node.nodeType === 1) { // Element node
                        // 检查是否是模态框
                        if (node.classList && node.classList.contains('modal')) {
                            fixModalAriaHidden(node);
                        }
                        // 检查子元素中是否有模态框
                        const modals = node.querySelectorAll && node.querySelectorAll('.modal[aria-hidden]');
                        if (modals) {
                            modals.forEach(function(modal) {
                                fixModalAriaHidden(modal);
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
    }

    // 页面加载完成后初始化
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            fixAllModals();
            observeNewModals();
        });
    } else {
        // DOM 已经加载完成
        fixAllModals();
        observeNewModals();
    }

    // 导出函数供其他脚本使用
    if (typeof window !== 'undefined') {
        window.fixModalAriaHidden = fixModalAriaHidden;
        window.removeFocusFromModal = removeFocusFromModal;
    }
})();
