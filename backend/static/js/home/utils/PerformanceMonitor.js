/**
 * 性能监控工具
 * 追踪页面加载时间、API调用耗时等性能指标
 * 维海科技信息化管理平台
 */
class PerformanceMonitor {
    constructor() {
        this.metrics = {
            pageLoad: null,
            apiCalls: [],
            renderTime: []
        };
        this.init();
    }
    
    /**
     * 初始化性能监控
     */
    init() {
        // 页面加载时间
        window.addEventListener('load', () => {
            const perfData = performance.getEntriesByType('navigation')[0];
            if (perfData) {
                this.metrics.pageLoad = {
                    domContentLoaded: perfData.domContentLoadedEventEnd - perfData.domContentLoadedEventStart,
                    loadComplete: perfData.loadEventEnd - perfData.loadEventStart,
                    total: perfData.loadEventEnd - perfData.fetchStart
                };
                this.reportMetrics();
            }
        });
        
        // API调用监控
        this.interceptFetch();
    }
    
    /**
     * 拦截fetch请求
     */
    interceptFetch() {
        const originalFetch = window.fetch;
        const self = this;
        
        window.fetch = async function(...args) {
            const startTime = performance.now();
            const url = args[0];
            
            try {
                const response = await originalFetch(...args);
                const duration = performance.now() - startTime;
                
                self.metrics.apiCalls.push({
                    url,
                    duration,
                    status: response.status,
                    success: response.ok,
                    timestamp: new Date().toISOString()
                });
                
                // 慢请求警告
                if (duration > 2000) {
                    console.warn(`慢请求: ${url} 耗时 ${duration.toFixed(2)}ms`);
                }
                
                return response;
            } catch (error) {
                const duration = performance.now() - startTime;
                self.metrics.apiCalls.push({
                    url,
                    duration,
                    error: error.message,
                    success: false,
                    timestamp: new Date().toISOString()
                });
                throw error;
            }
        };
    }
    
    /**
     * 测量渲染性能
     * @param {string} componentName - 组件名称
     * @param {Function} renderFn - 渲染函数
     * @returns {*} 渲染结果
     */
    measureRender(componentName, renderFn) {
        const startTime = performance.now();
        const result = renderFn();
        const duration = performance.now() - startTime;
        
        this.metrics.renderTime.push({
            component: componentName,
            duration,
            timestamp: new Date().toISOString()
        });
        
        return result;
    }
    
    /**
     * 上报性能指标
     */
    reportMetrics() {
        // 发送到分析服务
        if (window.analytics && window.analytics.track) {
            window.analytics.track('Performance Metrics', {
                pageLoad: this.metrics.pageLoad,
                avgApiCallTime: this.getAverageApiCallTime(),
                slowestApiCall: this.getSlowestApiCall(),
                renderMetrics: this.metrics.renderTime
            });
        } else {
            // 简单的控制台输出
            console.log('Performance Metrics:', {
                pageLoad: this.metrics.pageLoad,
                avgApiCallTime: this.getAverageApiCallTime(),
                slowestApiCall: this.getSlowestApiCall(),
                totalApiCalls: this.metrics.apiCalls.length
            });
        }
    }
    
    /**
     * 获取平均API调用时间
     * @returns {number} 平均时间（毫秒）
     */
    getAverageApiCallTime() {
        if (this.metrics.apiCalls.length === 0) return 0;
        const total = this.metrics.apiCalls.reduce((sum, call) => sum + call.duration, 0);
        return total / this.metrics.apiCalls.length;
    }
    
    /**
     * 获取最慢的API调用
     * @returns {Object} API调用信息
     */
    getSlowestApiCall() {
        if (this.metrics.apiCalls.length === 0) {
            return { duration: 0, url: '' };
        }
        return this.metrics.apiCalls.reduce((slowest, call) => 
            call.duration > slowest.duration ? call : slowest
        , { duration: 0 });
    }
    
    /**
     * 获取性能报告
     * @returns {Object} 性能报告
     */
    getReport() {
        return {
            pageLoad: this.metrics.pageLoad,
            apiCalls: {
                total: this.metrics.apiCalls.length,
                average: this.getAverageApiCallTime(),
                slowest: this.getSlowestApiCall(),
                all: this.metrics.apiCalls
            },
            renderTime: {
                total: this.metrics.renderTime.length,
                average: this.metrics.renderTime.length > 0 
                    ? this.metrics.renderTime.reduce((sum, r) => sum + r.duration, 0) / this.metrics.renderTime.length 
                    : 0,
                all: this.metrics.renderTime
            }
        };
    }
}

// 自动初始化（如果启用性能监控）
if (typeof DashboardConfig !== 'undefined' && DashboardConfig.features.performanceMonitoring) {
    window.performanceMonitor = new PerformanceMonitor();
}

// 兼容CommonJS和ES6模块
if (typeof module !== 'undefined' && module.exports) {
    module.exports = PerformanceMonitor;
}


