/**
 * 事件总线
 * 用于组件间解耦通信
 * 维海科技信息化管理平台
 */
class EventBus {
    constructor() {
        this.events = {};
    }
    
    /**
     * 订阅事件
     * @param {string} event - 事件名称
     * @param {Function} callback - 回调函数
     */
    on(event, callback) {
        if (!this.events[event]) {
            this.events[event] = [];
        }
        this.events[event].push(callback);
    }
    
    /**
     * 取消订阅
     * @param {string} event - 事件名称
     * @param {Function} callback - 回调函数
     */
    off(event, callback) {
        if (this.events[event]) {
            this.events[event] = this.events[event].filter(cb => cb !== callback);
        }
    }
    
    /**
     * 发布事件
     * @param {string} event - 事件名称
     * @param {*} data - 事件数据
     */
    emit(event, data) {
        if (this.events[event]) {
            this.events[event].forEach(callback => {
                try {
                    callback(data);
                } catch (error) {
                    console.error(`EventBus: Error in callback for event "${event}":`, error);
                }
            });
        }
    }
    
    /**
     * 一次性订阅
     * @param {string} event - 事件名称
     * @param {Function} callback - 回调函数
     */
    once(event, callback) {
        const wrapper = (data) => {
            callback(data);
            this.off(event, wrapper);
        };
        this.on(event, wrapper);
    }
    
    /**
     * 清除所有事件监听器
     */
    clear() {
        this.events = {};
    }
}

// 导出单例
if (typeof window !== 'undefined') {
    window.EventBus = window.EventBus || new EventBus();
}

// 兼容CommonJS和ES6模块
if (typeof module !== 'undefined' && module.exports) {
    module.exports = EventBus;
}


