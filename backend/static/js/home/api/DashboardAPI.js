/**
 * 仪表盘API封装
 * 支持请求合并、去重和缓存
 * 维海科技信息化管理平台
 */
class DashboardAPI {
    constructor(config = {}) {
        this.config = {
            baseURL: config.baseURL || '/api/admin/dashboard',
            timeout: config.timeout || 10000,
            cache: {
                ttl: config.cache?.ttl || 30000,
                enabled: config.cache?.enabled !== false
            },
            ...config
        };
        
        this.requestCache = new Map();
        this.pendingRequests = new Map();
        this.errorHandler = config.errorHandler || null;
    }
    
    /**
     * 获取CSRF Token
     * @returns {string} CSRF Token
     */
    getCSRFToken() {
        const cookie = document.cookie.match(/csrftoken=([^;]+)/);
        return cookie ? cookie[1] : '';
    }
    
    /**
     * 批量获取所有仪表盘数据（单次请求）
     * @param {Array<string>} include - 包含的数据类型 ['stats', 'todos', 'projects', 'approvals']
     * @returns {Promise<Object>} 所有数据
     */
    async fetchAll(include = ['stats', 'todos']) {
        const cacheKey = `dashboard_all_${include.join('_')}`;
        const cached = this.getCached(cacheKey);
        if (cached) {
            return cached;
        }
        
        // 检查是否有正在进行的请求
        if (this.pendingRequests.has(cacheKey)) {
            return this.pendingRequests.get(cacheKey);
        }
        
        const promise = fetch(`${this.config.baseURL}/all/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.getCSRFToken()
            },
            body: JSON.stringify({ include })
        })
        .then(async (res) => {
            if (!res.ok) {
                throw new Error(`HTTP ${res.status}: ${res.statusText}`);
            }
            return res.json();
        })
        .then(data => {
            if (data.success && data.data) {
                this.setCache(cacheKey, data.data);
            }
            this.pendingRequests.delete(cacheKey);
            return data.data || data;
        })
        .catch(err => {
            this.pendingRequests.delete(cacheKey);
            if (this.errorHandler) {
                this.errorHandler.handleError(err, 'fetchAll');
            }
            throw err;
        });
        
        this.pendingRequests.set(cacheKey, promise);
        return promise;
    }
    
    /**
     * 获取统计数据
     * @returns {Promise<Object>} 统计数据
     */
    async fetchStats() {
        return this.fetchWithDeduplication(`${this.config.baseURL}/stats/`);
    }
    
    /**
     * 获取待办事项
     * @returns {Promise<Object>} 待办事项数据
     */
    async fetchTodos() {
        return this.fetchWithDeduplication(`${this.config.baseURL}/todos/`);
    }
    
    /**
     * 请求去重：相同请求在短时间内只发送一次
     * @param {string} url - 请求URL
     * @param {Object} options - 请求选项
     * @returns {Promise} 请求结果
     */
    async fetchWithDeduplication(url, options = {}) {
        const key = `${url}_${JSON.stringify(options)}`;
        
        // 检查缓存
        const cached = this.getCached(key);
        if (cached) {
            return cached;
        }
        
        // 检查是否有相同请求正在进行
        if (this.pendingRequests.has(key)) {
            return this.pendingRequests.get(key);
        }
        
        const promise = fetch(url, {
            ...options,
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.getCSRFToken(),
                ...options.headers
            }
        })
        .then(async (res) => {
            if (!res.ok) {
                throw new Error(`HTTP ${res.status}: ${res.statusText}`);
            }
            return res.json();
        })
        .then(data => {
            if (this.config.cache.enabled) {
                this.setCache(key, data);
            }
            this.pendingRequests.delete(key);
            return data;
        })
        .catch(err => {
            this.pendingRequests.delete(key);
            if (this.errorHandler) {
                this.errorHandler.handleError(err, url);
            }
            throw err;
        });
        
        this.pendingRequests.set(key, promise);
        return promise;
    }
    
    /**
     * 获取缓存数据
     * @param {string} key - 缓存键
     * @returns {*} 缓存数据或null
     */
    getCached(key) {
        if (!this.config.cache.enabled) {
            return null;
        }
        
        const cached = this.requestCache.get(key);
        if (cached && Date.now() - cached.timestamp < this.config.cache.ttl) {
            return cached.data;
        }
        this.requestCache.delete(key);
        return null;
    }
    
    /**
     * 设置缓存
     * @param {string} key - 缓存键
     * @param {*} data - 缓存数据
     */
    setCache(key, data) {
        if (!this.config.cache.enabled) {
            return;
        }
        
        this.requestCache.set(key, {
            data,
            timestamp: Date.now()
        });
    }
    
    /**
     * 清除缓存
     * @param {string} key - 缓存键（可选，不传则清除所有）
     */
    clearCache(key = null) {
        if (key) {
            this.requestCache.delete(key);
        } else {
            this.requestCache.clear();
        }
    }
    
    /**
     * 智能刷新：只刷新过期的数据
     * @returns {Promise<Object>} 所有数据
     */
    async smartRefresh() {
        const allData = await this.fetchAll();
        const now = Date.now();
        
        // 检查哪些数据需要刷新
        const needsRefresh = [];
        const statsCache = this.requestCache.get('dashboard_all_stats_todos');
        if (!statsCache || now - statsCache.timestamp > 60000) {
            needsRefresh.push('stats');
        }
        
        if (needsRefresh.length > 0) {
            return this.fetchAll(needsRefresh);
        }
        
        return allData;
    }
}

// 兼容CommonJS和ES6模块
if (typeof module !== 'undefined' && module.exports) {
    module.exports = DashboardAPI;
}


