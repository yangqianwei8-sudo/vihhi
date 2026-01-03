/**
 * 清理筛选条件展开/折叠功能的localStorage数据
 * 此脚本用于清理已删除功能的遗留数据
 * 在页面加载时自动执行
 */

(function() {
    'use strict';
    
    // 清理可能存在的筛选展开/折叠相关的localStorage数据
    const keysToRemove = [
        'filterCollapseState',
        'filterCollapseStatus',
        'customerListFilterCollapse',
        'filter_collapse_state',
        'filter_collapse_status',
        // 其他可能的键名
    ];
    
    // 清理所有匹配的localStorage键
    keysToRemove.forEach(key => {
        try {
            if (localStorage.getItem(key)) {
                localStorage.removeItem(key);
                console.log('已清理localStorage键:', key);
            }
        } catch (e) {
            console.warn('清理localStorage键失败:', key, e);
        }
    });
    
    // 清理所有包含 "collapse" 或 "toggle" 的localStorage键（如果键名包含这些词）
    try {
        const keys = Object.keys(localStorage);
        keys.forEach(key => {
            if (key.toLowerCase().includes('filter') && 
                (key.toLowerCase().includes('collapse') || key.toLowerCase().includes('toggle'))) {
                try {
                    localStorage.removeItem(key);
                    console.log('已清理localStorage键:', key);
                } catch (e) {
                    console.warn('清理localStorage键失败:', key, e);
                }
            }
        });
    } catch (e) {
        console.warn('遍历localStorage键失败:', e);
    }
    
    console.log('筛选条件展开/折叠功能数据清理完成');
})();

