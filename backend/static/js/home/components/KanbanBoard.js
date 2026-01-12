/**
 * 看板组件
 * 负责渲染和更新任务看板
 * 维海科技信息化管理平台
 */
class KanbanBoard {
    constructor(options = {}) {
        this.pendingContainer = options.pendingContainer || document.getElementById('task-pending-container');
        this.inProgressContainer = options.inProgressContainer || document.getElementById('task-in-progress-container');
        this.completedContainer = options.completedContainer || document.getElementById('task-completed-container');
        this.skeletonLoader = options.skeletonLoader || null;
        this.eventBus = options.eventBus || null;
    }
    
    /**
     * 渲染看板
     * @param {Array} todos - 待办事项数组
     */
    render(todos) {
        if (!todos || !Array.isArray(todos)) {
            this.showError('数据格式错误');
            return;
        }
        
        // 按优先级和状态分类任务
        const pendingTasks = todos.filter(t => 
            t.priority === 'high' || !t.status || t.status === 'pending'
        ).slice(0, 5);
        
        const inProgressTasks = todos.filter(t => 
            t.status === 'in_progress'
        ).slice(0, 5);
        
        const completedTasks = todos.filter(t => 
            t.status === 'completed'
        ).slice(0, 5);
        
        // 更新各个列
        this.updateColumn(this.pendingContainer, pendingTasks, '暂无待处理任务');
        this.updateColumn(this.inProgressContainer, inProgressTasks, '暂无进行中任务');
        this.updateColumn(this.completedContainer, completedTasks, '暂无已完成任务');
        
        // 发布更新事件
        if (this.eventBus) {
            this.eventBus.emit('dashboard:todos:updated', todos);
        }
    }
    
    /**
     * 更新看板列
     * @param {HTMLElement} container - 容器元素
     * @param {Array} tasks - 任务数组
     * @param {string} emptyMessage - 空状态消息
     */
    updateColumn(container, tasks, emptyMessage) {
        if (!container) return;
        
        // 隐藏骨架屏
        if (this.skeletonLoader) {
            this.skeletonLoader.hide(container);
        }
        
        if (tasks.length > 0) {
            container.innerHTML = tasks.map(task => this.renderTaskItem(task)).join('');
        } else {
            container.innerHTML = `<div class="text-muted text-center py-3">${emptyMessage}</div>`;
        }
    }
    
    /**
     * 渲染任务项
     * @param {Object} task - 任务对象
     * @returns {string} HTML字符串
     */
    renderTaskItem(task) {
        const priorityLabel = this.getPriorityLabel(task.priority);
        const priorityClass = `priority-${task.priority || 'medium'}`;
        
        return `
            <div class="work-item" data-task-id="${task.id || ''}">
                <div class="work-item-header">
                    <span class="work-item-title">${this.escapeHtml(task.title || '')}</span>
                    ${task.priority ? `<span class="work-item-priority ${priorityClass}">${priorityLabel}</span>` : ''}
                </div>
                ${task.description ? `<div class="work-item-description">${this.escapeHtml(task.description)}</div>` : ''}
                <div class="work-item-footer">
                    ${task.time ? `<span class="work-item-time">${this.escapeHtml(task.time)}</span>` : ''}
                    ${task.url ? `<a href="${this.escapeHtml(task.url)}" class="work-item-link">查看详情 →</a>` : ''}
                </div>
            </div>
        `;
    }
    
    /**
     * 获取优先级标签
     * @param {string} priority - 优先级
     * @returns {string} 标签文本
     */
    getPriorityLabel(priority) {
        const labels = {
            'high': '高',
            'medium': '中',
            'low': '低'
        };
        return labels[priority] || '中';
    }
    
    /**
     * HTML转义
     * @param {string} text - 文本
     * @returns {string} 转义后的文本
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    /**
     * 显示加载状态
     */
    showLoading() {
        if (this.skeletonLoader) {
            if (this.pendingContainer) {
                this.skeletonLoader.show(this.pendingContainer, 'kanban');
            }
        } else {
            const containers = [this.pendingContainer, this.inProgressContainer, this.completedContainer];
            containers.forEach(container => {
                if (container) {
                    container.innerHTML = '<div class="text-center text-muted">加载中...</div>';
                }
            });
        }
    }
    
    /**
     * 显示错误状态
     * @param {string} message - 错误消息
     */
    showError(message = '加载失败') {
        const containers = [this.pendingContainer, this.inProgressContainer, this.completedContainer];
        containers.forEach(container => {
            if (container) {
                container.innerHTML = `
                    <div class="text-center text-danger">
                        <i class="bi bi-exclamation-triangle"></i>
                        <div>${message}</div>
                    </div>
                `;
            }
        });
    }
}

// 兼容CommonJS和ES6模块
if (typeof module !== 'undefined' && module.exports) {
    module.exports = KanbanBoard;
}


