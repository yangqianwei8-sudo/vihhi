/**
 * 修复布局结构 - 将 .two-col-main 移动到 .two-column-layout 内
 * 这是一个临时修复方案，用于解决 HTML 结构被破坏的问题
 */
(function() {
    'use strict';
    
    function fixLayoutStructure() {
        const layout = document.querySelector('.two-column-layout');
        const main = document.querySelector('.two-col-main');
        
        if (!layout || !main) {
            console.warn('布局修复：未找到 .two-column-layout 或 .two-col-main');
            return;
        }
        
        // 检查 .two-col-main 是否已经在 .two-column-layout 内
        if (layout.contains(main)) {
            console.log('布局修复：结构已正确，无需修复');
            return;
        }
        
        // 检查 .two-col-main 的父元素
        const mainParent = main.parentElement;
        if (mainParent === document.body) {
            console.log('布局修复：检测到 .two-col-main 在 body 下，开始修复...');
            
            // 将 .two-col-main 移动到 .two-column-layout 内
            layout.appendChild(main);
            
            console.log('布局修复：已将 .two-col-main 移动到 .two-column-layout 内');
            
            // 触发重新布局
            layout.offsetHeight; // 强制重排
            
            // 运行诊断脚本（如果存在）
            if (typeof layoutDiagnostic === 'function') {
                setTimeout(() => {
                    console.log('布局修复：运行诊断脚本...');
                    layoutDiagnostic();
                }, 100);
            }
        } else {
            console.warn('布局修复：.two-col-main 的父元素不是 body，无法自动修复');
            console.warn('  父元素:', mainParent.tagName, mainParent.className);
        }
    }
    
    // 在 DOM 加载完成后运行
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', fixLayoutStructure);
    } else {
        // DOM 已加载，立即运行
        fixLayoutStructure();
    }
    
    // 也监听动态内容加载
    if (typeof MutationObserver !== 'undefined') {
        const observer = new MutationObserver(function(mutations) {
            const layout = document.querySelector('.two-column-layout');
            const main = document.querySelector('.two-col-main');
            if (layout && main && !layout.contains(main)) {
                fixLayoutStructure();
            }
        });
        
        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
    }
})();
