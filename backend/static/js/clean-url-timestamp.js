/**
 * 清理 URL 中的时间戳参数
 * 用于移除浏览器自动添加的 _t 参数，保持 URL 清洁
 */

(function() {
    'use strict';
    
    /**
     * 清理 URL 中的时间戳参数
     */
    function cleanUrlTimestamp() {
        // 检查 URL 中是否有 _t 参数
        const url = new URL(window.location.href);
        const hasTimestamp = url.searchParams.has('_t');
        
        if (hasTimestamp) {
            console.log('检测到 URL 中的时间戳参数 _t，正在清理...');
            
            // 移除 _t 参数
            url.searchParams.delete('_t');
            
            // 使用 replaceState 更新 URL，不刷新页面
            const cleanUrl = url.pathname + (url.search ? url.search : '') + (url.hash ? url.hash : '');
            window.history.replaceState(null, '', cleanUrl);
            
            console.log('URL 已清理，移除了时间戳参数');
        }
    }
    
    // 页面加载完成后清理
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', cleanUrlTimestamp);
    } else {
        // DOM 已加载，立即执行
        cleanUrlTimestamp();
    }
    
    // 监听 popstate 事件（浏览器前进/后退）
    window.addEventListener('popstate', function() {
        // 延迟执行，确保 URL 已更新
        setTimeout(cleanUrlTimestamp, 0);
    });
    
})();

