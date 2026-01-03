/**
 * Admin页面保护脚本
 * 确保Vue应用不会干扰Django Admin页面
 */

(function() {
    'use strict';
    
    // 检查当前路径是否为Admin页面
    const isAdminPath = window.location.pathname.startsWith('/admin/');
    
    if (isAdminPath) {
        // 如果是Admin页面，阻止Vue应用挂载
        console.log('[Admin Protection] Admin页面检测到，阻止Vue应用挂载');
        
        // 移除#app元素（如果存在）
        const appElement = document.getElementById('app');
        if (appElement) {
            console.log('[Admin Protection] 发现#app元素，移除它');
            appElement.remove();
        }
        
        // 阻止Vue应用挂载（如果Vue应用已经加载）
        if (window.Vue) {
            console.log('[Admin Protection] Vue已加载，阻止挂载');
            // 重写mount方法，阻止挂载
            const originalMount = window.Vue.mount;
            window.Vue.mount = function() {
                console.log('[Admin Protection] Vue mount被阻止');
                return null;
            };
        }
        
        // 监听DOM变化，确保#app元素不会被重新创建
        const observer = new MutationObserver(function(mutations) {
            mutations.forEach(function(mutation) {
                mutation.addedNodes.forEach(function(node) {
                    if (node.nodeType === 1) { // Element node
                        if (node.id === 'app' || node.querySelector && node.querySelector('#app')) {
                            console.log('[Admin Protection] 检测到#app元素被添加，移除它');
                            const appEl = node.id === 'app' ? node : node.querySelector('#app');
                            if (appEl) {
                                appEl.remove();
                            }
                        }
                    }
                });
            });
        });
        
        // 开始观察body的变化
        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
        
        // 阻止Vue Router拦截
        if (window.VueRouter) {
            console.log('[Admin Protection] Vue Router已加载，阻止路由拦截');
        }
    }
})();

