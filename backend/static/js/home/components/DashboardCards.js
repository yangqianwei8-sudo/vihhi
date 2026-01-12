/**
 * 统计卡片组件
 * 负责渲染和更新数据概览卡片
 * 维海科技信息化管理平台
 */
class DashboardCards {
    constructor(options = {}) {
        this.container = options.container || document.getElementById('stats-cards-container');
        this.skeletonLoader = options.skeletonLoader || null;
        this.eventBus = options.eventBus || null;
    }
    
    /**
     * 渲染统计卡片
     * @param {Object} data - 统计数据
     */
    render(data) {
        if (!this.container) return;
        
        // 隐藏骨架屏
        if (this.skeletonLoader) {
            this.skeletonLoader.hide(this.container);
        }
        
        // 更新欢迎卡片中的计数
        this.updateWelcomeCounts(data);
        
        // 更新快速统计卡片
        this.updateQuickStats(data);
        
        // 更新数据概览卡片
        this.updateStatsCards(data);
        
        // 发布更新事件
        if (this.eventBus) {
            this.eventBus.emit('dashboard:stats:updated', data);
        }
    }
    
    /**
     * 更新欢迎卡片中的计数
     * @param {Object} data - 统计数据
     */
    updateWelcomeCounts(data) {
        const pendingApprovalsEl = document.getElementById('pending-approvals-count');
        const pendingTasksEl = document.getElementById('pending-tasks-count');
        
        if (pendingApprovalsEl) {
            pendingApprovalsEl.textContent = `${data.pending_tasks || 0}项`;
        }
        if (pendingTasksEl) {
            pendingTasksEl.textContent = `${data.pending_items || 0}个`;
        }
    }
    
    /**
     * 更新快速统计卡片
     * @param {Object} data - 统计数据
     */
    updateQuickStats(data) {
        const quickApprovalCountEl = document.getElementById('quick-approval-count');
        const quickTaskCountEl = document.getElementById('quick-task-count');
        const quickProjectCountEl = document.getElementById('quick-project-count');
        const quickOverdueCountEl = document.getElementById('quick-overdue-count');
        
        if (quickApprovalCountEl) {
            quickApprovalCountEl.textContent = data.pending_tasks || 0;
        }
        if (quickTaskCountEl) {
            quickTaskCountEl.textContent = data.pending_items || 0;
        }
        if (quickProjectCountEl) {
            quickProjectCountEl.textContent = data.active_projects || 0;
        }
        if (quickOverdueCountEl) {
            quickOverdueCountEl.textContent = data.overdue_tasks || 0;
        }
    }
    
    /**
     * 更新数据概览卡片
     * @param {Object} data - 统计数据
     */
    updateStatsCards(data) {
        if (!this.container) return;
        
        const stats = [
            { 
                label: '待审批任务', 
                value: data.pending_tasks || 0, 
                icon: 'bi-clock-history',
                color: 'var(--vh-warning)',
                url: '/workflow/approvals/'
            },
            { 
                label: '进行中项目', 
                value: data.active_projects || 0, 
                icon: 'bi-folder2-open',
                color: 'var(--vh-info)',
                url: '/production/'
            },
            { 
                label: '待处理事项', 
                value: data.pending_items || 0, 
                icon: 'bi-inbox',
                color: 'var(--vh-error)',
                url: '/administrative/'
            },
            { 
                label: '本月完成', 
                value: data.completed || 0, 
                icon: 'bi-check-circle',
                color: 'var(--vh-success)',
                url: '/production/'
            }
        ];
        
        this.container.innerHTML = stats.map(stat => `
            <div class="info-item">
                <a href="${stat.url}" style="text-decoration: none; color: inherit; display: block; height: 100%;">
                    <div class="d-flex justify-content-between align-items-start" style="height: 100%;">
                        <div style="flex: 1;">
                            <div class="info-value" style="color: ${stat.color}; font-size: 2rem; font-weight: 700; line-height: 1.2; margin-bottom: 0.5rem;">
                                ${stat.value}
                            </div>
                            <div class="info-label" style="color: var(--vh-text-muted); font-size: 0.875rem;">
                                ${stat.label}
                            </div>
                        </div>
                        <div style="font-size: 2.5rem; color: ${stat.color}; opacity: 0.2; flex-shrink: 0; margin-left: 1rem;">
                            <i class="bi ${stat.icon}"></i>
                        </div>
                    </div>
                </a>
            </div>
        `).join('');
    }
    
    /**
     * 显示加载状态
     */
    showLoading() {
        if (!this.container) return;
        
        if (this.skeletonLoader) {
            this.skeletonLoader.show(this.container, 'stats');
        } else {
            this.container.innerHTML = '<div class="text-center text-muted">加载中...</div>';
        }
    }
    
    /**
     * 显示错误状态
     * @param {string} message - 错误消息
     */
    showError(message = '加载失败') {
        if (!this.container) return;
        
        this.container.innerHTML = `
            <div class="text-center text-danger">
                <i class="bi bi-exclamation-triangle"></i>
                <div>${message}</div>
            </div>
        `;
    }
}

// 兼容CommonJS和ES6模块
if (typeof module !== 'undefined' && module.exports) {
    module.exports = DashboardCards;
}


