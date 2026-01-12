/**
 * 首页配置文件
 * 统一管理配置项
 * 维海科技信息化管理平台
 */
const DashboardConfig = {
    // API配置
    api: {
        baseURL: '/api/admin/dashboard',
        timeout: 10000,
        retry: {
            maxRetries: 3,
            delay: 1000,
            backoffMultiplier: 2
        },
        cache: {
            ttl: 30000, // 30秒
            enabled: true
        }
    },
    
    // UI配置
    ui: {
        refreshInterval: 300000, // 5分钟
        animationDuration: 300,
        skeletonCount: 4,
        itemsPerPage: 20,
        autoRefresh: true
    },
    
    // 功能开关
    features: {
        autoRefresh: true,
        offlineMode: false,
        notifications: true,
        analytics: false,
        performanceMonitoring: true
    },
    
    // 主题配置
    theme: {
        primaryColor: 'var(--vh-primary)',
        cardRadius: 'var(--radius-lg)',
        spacing: 'var(--spacing-lg)'
    }
};

// 兼容CommonJS和ES6模块
if (typeof module !== 'undefined' && module.exports) {
    module.exports = DashboardConfig;
}


