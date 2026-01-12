/**
 * 骨架屏加载器
 * 生成加载状态的占位UI
 * 维海科技信息化管理平台
 */
class SkeletonLoader {
    /**
     * 创建卡片骨架屏
     * @returns {string} HTML字符串
     */
    static createCardSkeleton() {
        return `
            <div class="skeleton-card">
                <div class="skeleton-header">
                    <div class="skeleton-line skeleton-title"></div>
                    <div class="skeleton-line skeleton-subtitle"></div>
                </div>
                <div class="skeleton-body">
                    <div class="skeleton-line"></div>
                    <div class="skeleton-line"></div>
                    <div class="skeleton-line skeleton-short"></div>
                </div>
            </div>
        `;
    }
    
    /**
     * 创建统计卡片骨架屏
     * @param {number} count - 数量
     * @returns {string} HTML字符串
     */
    static createStatsSkeleton(count = 4) {
        return Array(count).fill(0).map(() => `
            <div class="skeleton-stat-card">
                <div class="skeleton-circle"></div>
                <div class="skeleton-line"></div>
                <div class="skeleton-line skeleton-short"></div>
            </div>
        `).join('');
    }
    
    /**
     * 创建看板骨架屏
     * @returns {string} HTML字符串
     */
    static createKanbanSkeleton() {
        return `
            <div class="kanban">
                <div class="kanban-column">
                    <h4>待处理</h4>
                    ${Array(3).fill(0).map(() => `
                        <div class="skeleton-card" style="margin-bottom: 12px;">
                            <div class="skeleton-line"></div>
                            <div class="skeleton-line skeleton-short"></div>
                        </div>
                    `).join('')}
                </div>
                <div class="kanban-column">
                    <h4>进行中</h4>
                    ${Array(2).fill(0).map(() => `
                        <div class="skeleton-card" style="margin-bottom: 12px;">
                            <div class="skeleton-line"></div>
                            <div class="skeleton-line skeleton-short"></div>
                        </div>
                    `).join('')}
                </div>
                <div class="kanban-column">
                    <h4>已完成</h4>
                    ${Array(2).fill(0).map(() => `
                        <div class="skeleton-card" style="margin-bottom: 12px;">
                            <div class="skeleton-line"></div>
                            <div class="skeleton-line skeleton-short"></div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }
    
    /**
     * 显示骨架屏
     * @param {HTMLElement} container - 容器元素
     * @param {string} type - 骨架屏类型（card, stats, kanban）
     */
    static show(container, type = 'card') {
        if (!container) return;
        
        let html = '';
        switch (type) {
            case 'card':
                html = this.createCardSkeleton();
                break;
            case 'stats':
                html = this.createStatsSkeleton();
                break;
            case 'kanban':
                html = this.createKanbanSkeleton();
                break;
            default:
                html = this.createCardSkeleton();
        }
        
        container.innerHTML = html;
        container.classList.add('skeleton-loading');
    }
    
    /**
     * 隐藏骨架屏
     * @param {HTMLElement} container - 容器元素
     */
    static hide(container) {
        if (!container) return;
        container.classList.remove('skeleton-loading');
    }
}

// 兼容CommonJS和ES6模块
if (typeof module !== 'undefined' && module.exports) {
    module.exports = SkeletonLoader;
}


