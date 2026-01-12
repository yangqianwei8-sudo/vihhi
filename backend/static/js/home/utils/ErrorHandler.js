/**
 * 错误处理器
 * 统一处理错误，支持重试机制和错误分类
 * 维海科技信息化管理平台
 */
class ErrorHandler {
    constructor() {
        this.retryConfig = {
            maxRetries: 3,
            retryDelay: 1000,
            backoffMultiplier: 2
        };
    }
    
    /**
     * 带重试的请求
     * @param {string} url - 请求URL
     * @param {Object} options - 请求选项
     * @param {number} retries - 剩余重试次数
     * @returns {Promise} 请求结果
     */
    async fetchWithRetry(url, options = {}, retries = this.retryConfig.maxRetries) {
        try {
            const response = await fetch(url, options);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            return await response.json();
        } catch (error) {
            if (retries > 0) {
                const delay = this.retryConfig.retryDelay * 
                    Math.pow(this.retryConfig.backoffMultiplier, 
                    this.retryConfig.maxRetries - retries);
                
                console.warn(`请求失败，${delay}ms后重试... (剩余${retries}次)`, url);
                
                await this.sleep(delay);
                return this.fetchWithRetry(url, options, retries - 1);
            }
            
            // 所有重试都失败
            this.handleError(error, url);
            throw error;
        }
    }
    
    /**
     * 错误分类处理
     * @param {Error} error - 错误对象
     * @param {string} context - 错误上下文
     */
    handleError(error, context) {
        const errorType = this.classifyError(error);
        
        switch (errorType) {
            case 'network':
                this.showNetworkError();
                break;
            case 'timeout':
                this.showTimeoutError();
                break;
            case 'server':
                this.showServerError();
                break;
            case 'auth':
                this.handleAuthError();
                break;
            default:
                this.showGenericError(error);
        }
        
        // 上报错误
        this.reportError(error, context);
    }
    
    /**
     * 分类错误类型
     * @param {Error} error - 错误对象
     * @returns {string} 错误类型
     */
    classifyError(error) {
        if (error.message.includes('Failed to fetch') || 
            error.message.includes('NetworkError')) {
            return 'network';
        }
        if (error.message.includes('timeout')) {
            return 'timeout';
        }
        if (error.status >= 500) {
            return 'server';
        }
        if (error.status === 401 || error.status === 403) {
            return 'auth';
        }
        return 'unknown';
    }
    
    /**
     * 显示网络错误
     */
    showNetworkError() {
        this.showToast('网络连接失败，请检查网络设置', 'error', {
            action: '重试',
            onAction: () => window.location.reload()
        });
    }
    
    /**
     * 显示超时错误
     */
    showTimeoutError() {
        this.showToast('请求超时，请稍后重试', 'error');
    }
    
    /**
     * 显示服务器错误
     */
    showServerError() {
        this.showToast('服务器错误，请稍后重试', 'error');
    }
    
    /**
     * 处理认证错误
     */
    handleAuthError() {
        this.showToast('登录已过期，请重新登录', 'error', {
            action: '登录',
            onAction: () => window.location.href = '/login/'
        });
    }
    
    /**
     * 显示通用错误
     * @param {Error} error - 错误对象
     */
    showGenericError(error) {
        this.showToast(error.message || '发生未知错误', 'error');
    }
    
    /**
     * 显示Toast提示
     * @param {string} message - 提示消息
     * @param {string} type - 提示类型
     * @param {Object} options - 选项
     */
    showToast(message, type = 'info', options = {}) {
        // 创建Toast元素
        const toast = document.createElement('div');
        toast.className = `home-toast home-toast--${type}`;
        toast.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 12px 20px;
            background: ${type === 'error' ? '#E23D3D' : '#2563EB'};
            color: white;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            z-index: 10000;
            animation: toastSlideIn 0.3s ease;
        `;
        toast.textContent = message;
        
        // 添加操作按钮
        if (options.action && options.onAction) {
            const actionBtn = document.createElement('button');
            actionBtn.textContent = options.action;
            actionBtn.style.cssText = `
                margin-left: 12px;
                padding: 4px 12px;
                background: rgba(255,255,255,0.2);
                border: 1px solid rgba(255,255,255,0.3);
                color: white;
                border-radius: 4px;
                cursor: pointer;
            `;
            actionBtn.onclick = options.onAction;
            toast.appendChild(actionBtn);
        }
        
        document.body.appendChild(toast);
        
        // 3秒后自动移除
        setTimeout(() => {
            toast.style.animation = 'toastSlideOut 0.3s ease';
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }
    
    /**
     * 延迟函数
     * @param {number} ms - 毫秒数
     * @returns {Promise}
     */
    sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
    
    /**
     * 上报错误
     * @param {Error} error - 错误对象
     * @param {string} context - 错误上下文
     */
    reportError(error, context) {
        // 发送到错误监控服务
        if (window.errorReporter) {
            window.errorReporter.report({
                error: error.message,
                context,
                timestamp: new Date().toISOString(),
                userAgent: navigator.userAgent
            });
        } else {
            // 简单的控制台日志
            console.error('Error reported:', {
                error: error.message,
                context,
                timestamp: new Date().toISOString()
            });
        }
    }
}

// 添加Toast动画样式
if (typeof document !== 'undefined') {
    const style = document.createElement('style');
    style.textContent = `
        @keyframes toastSlideIn {
            from {
                transform: translateX(100%);
                opacity: 0;
            }
            to {
                transform: translateX(0);
                opacity: 1;
            }
        }
        @keyframes toastSlideOut {
            from {
                transform: translateX(0);
                opacity: 1;
            }
            to {
                transform: translateX(100%);
                opacity: 0;
            }
        }
    `;
    document.head.appendChild(style);
}

// 兼容CommonJS和ES6模块
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ErrorHandler;
}


