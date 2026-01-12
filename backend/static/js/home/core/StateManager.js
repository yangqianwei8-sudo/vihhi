/**
 * 状态管理器
 * 管理应用状态，支持状态订阅和通知
 * 维海科技信息化管理平台
 */
class StateManager {
    constructor(initialState = {}) {
        this.state = { ...initialState };
        this.listeners = [];
    }
    
    /**
     * 获取当前状态
     * @returns {Object} 状态副本
     */
    getState() {
        return { ...this.state };
    }
    
    /**
     * 设置状态
     * @param {Object} updates - 要更新的状态
     */
    setState(updates) {
        const prevState = { ...this.state };
        this.state = { ...this.state, ...updates };
        this.notifyListeners(prevState, this.state);
    }
    
    /**
     * 订阅状态变化
     * @param {Function} listener - 监听函数
     * @returns {Function} 取消订阅函数
     */
    subscribe(listener) {
        this.listeners.push(listener);
        return () => {
            this.listeners = this.listeners.filter(l => l !== listener);
        };
    }
    
    /**
     * 通知所有监听器
     * @param {Object} prevState - 之前的状态
     * @param {Object} nextState - 新的状态
     */
    notifyListeners(prevState, nextState) {
        this.listeners.forEach(listener => {
            try {
                listener(nextState, prevState);
            } catch (error) {
                console.error('StateManager: Error in listener:', error);
            }
        });
    }
    
    /**
     * 重置状态
     * @param {Object} newState - 新状态
     */
    reset(newState = {}) {
        const prevState = { ...this.state };
        this.state = { ...newState };
        this.notifyListeners(prevState, this.state);
    }
}

// 兼容CommonJS和ES6模块
if (typeof module !== 'undefined' && module.exports) {
    module.exports = StateManager;
}


