/**
 * 首页主入口文件
 * 使用模块化架构，整合各个组件
 * 维海科技信息化管理平台
 */

// 加载核心模块（使用全局变量方式，兼容非模块化环境）
(function() {
    'use strict';
    
    // #region agent log
    fetch('http://localhost:7242/ingest/8da7066a-e0c2-4e09-9af7-37ab2ebaf22c',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'home/home.js:8',message:'home/home.js开始执行（修复后版本）',data:{timestamp:Date.now()},timestamp:Date.now(),sessionId:'debug-session',runId:'post-fix',hypothesisId:'B'})}).catch(()=>{});
    // #endregion
    
    // 等待所有依赖加载完成
    function waitForDependencies(callback, maxWait = 5000) {
        const startTime = Date.now();
        const checkInterval = 100;
        
        function check() {
            if (typeof EventBus !== 'undefined' && 
                typeof StateManager !== 'undefined' &&
                typeof ErrorHandler !== 'undefined' &&
                typeof DashboardAPI !== 'undefined' &&
                typeof DashboardCards !== 'undefined' &&
                typeof KanbanBoard !== 'undefined' &&
                typeof SkeletonLoader !== 'undefined' &&
                typeof DashboardConfig !== 'undefined') {
                callback();
            } else if (Date.now() - startTime < maxWait) {
                setTimeout(check, checkInterval);
            } else {
                console.error('部分模块加载超时，使用默认实现');
                // 使用默认实现继续
                if (typeof EventBus === 'undefined') {
                    window.EventBus = new EventBus();
                }
                callback();
            }
        }
        check();
    }
    
    waitForDependencies(function() {
        // 初始化事件总线和状态管理器
        const eventBus = window.EventBus || new EventBus();
        const state = new StateManager({
            stats: null,
            todos: [],
            loading: false,
            error: null
        });
        
        // 初始化错误处理器
        const errorHandler = new ErrorHandler();
        
        // 初始化API客户端
        const api = new DashboardAPI({
            baseURL: '/api/admin/dashboard',
            errorHandler: errorHandler,
            cache: {
                ttl: 30000,
                enabled: true
            }
        });
        
        // 初始化组件
        const dashboardCards = new DashboardCards({
            container: document.getElementById('stats-cards-container'),
            skeletonLoader: SkeletonLoader,
            eventBus: eventBus
        });
        
        const kanbanBoard = new KanbanBoard({
            pendingContainer: document.getElementById('task-pending-container'),
            inProgressContainer: document.getElementById('task-in-progress-container'),
            completedContainer: document.getElementById('task-completed-container'),
            skeletonLoader: SkeletonLoader,
            eventBus: eventBus
        });
        
        // 主应用类
        // #region agent log
        fetch('http://localhost:7242/ingest/8da7066a-e0c2-4e09-9af7-37ab2ebaf22c',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'home/home.js:79',message:'准备定义HomeApp类',data:{},timestamp:Date.now(),sessionId:'debug-session',runId:'post-fix',hypothesisId:'B'})}).catch(()=>{});
        // #endregion
        class HomeApp {
            constructor() {
                this.api = api;
                this.eventBus = eventBus;
                this.state = state;
                this.dashboardCards = dashboardCards;
                this.kanbanBoard = kanbanBoard;
                this.refreshInterval = null;
                
                this.init();
            }
            
            /**
             * 初始化应用
             */
            async init() {
                try {
                    // 显示加载状态
                    this.setLoading(true);
                    this.dashboardCards.showLoading();
                    this.kanbanBoard.showLoading();
                    
                    // 加载初始数据
                    await this.loadInitialData();
                    
                    // 更新日期显示
                    this.updateDateDisplay();
                    
                    // 绑定事件
                    this.bindEvents();
                    
                    // 启动自动刷新
                    if (typeof DashboardConfig !== 'undefined' && DashboardConfig.ui.autoRefresh) {
                        this.startAutoRefresh();
                    }
                    
                    // 设置加载完成
                    this.setLoading(false);
                    
                } catch (error) {
                    console.error('HomeApp初始化失败:', error);
                    this.setLoading(false);
                    this.showErrorState();
                }
            }
            
            /**
             * 加载初始数据
             */
            async loadInitialData() {
                try {
                    // 使用统一API获取所有数据
                    const allData = await this.api.fetchAll(['stats', 'todos']);
                    
                    // 更新统计卡片
                    if (allData.stats && allData.stats.success) {
                        this.dashboardCards.render(allData.stats);
                        this.state.setState({ stats: allData.stats });
                    }
                    
                    // 更新看板
                    if (allData.todos && allData.todos.success && allData.todos.todos) {
                        this.kanbanBoard.render(allData.todos.todos);
                        this.state.setState({ todos: allData.todos.todos });
                    }
                    
                    // 更新最后刷新时间
                    this.updateLastRefreshTime();
                    
                } catch (error) {
                    console.error('加载数据失败:', error);
                    // 使用默认数据
                    this.dashboardCards.render({
                        pending_tasks: 0,
                        active_projects: 0,
                        pending_items: 0,
                        completed: 0
                    });
                }
            }
            
            /**
             * 刷新数据
             */
            async refreshData() {
                try {
                    // 清除缓存
                    this.api.clearCache();
                    
                    // 重新加载数据
                    await this.loadInitialData();
                    
                    // 显示成功提示
                    this.showToast('数据已刷新', 'success');
                    
                } catch (error) {
                    console.error('刷新数据失败:', error);
                    this.showToast('数据刷新失败', 'error');
                }
            }
            
            /**
             * 更新日期显示
             */
            updateDateDisplay() {
                // 更新欢迎卡片中的日期（如果存在）
                const dateEl = document.getElementById('current-date');
                // 更新顶部栏中的日期
                const dateElHeader = document.getElementById('current-date-header');
                
                const now = new Date();
                const options = { 
                    year: 'numeric', 
                    month: 'long', 
                    day: 'numeric',
                    weekday: 'long'
                };
                const dateText = now.toLocaleDateString('zh-CN', options);
                
                if (dateEl) {
                    dateEl.textContent = dateText;
                }
                if (dateElHeader) {
                    dateElHeader.textContent = dateText;
                }
                
                // 更新时间问候语
                const timeBadgeEl = document.getElementById('welcome-time-badge');
                const timeBadgeElHeader = document.getElementById('welcome-time-badge-header');
                
                const hour = new Date().getHours();
                let greeting = '你好';
                if (hour >= 5 && hour < 12) {
                    greeting = '早上好';
                } else if (hour >= 12 && hour < 14) {
                    greeting = '中午好';
                } else if (hour >= 14 && hour < 18) {
                    greeting = '下午好';
                } else if (hour >= 18 && hour < 22) {
                    greeting = '晚上好';
                } else {
                    greeting = '夜深了';
                }
                
                if (timeBadgeEl) {
                    timeBadgeEl.textContent = greeting;
                }
                if (timeBadgeElHeader) {
                    timeBadgeElHeader.textContent = greeting;
                }
            }
            
            /**
             * 更新最后刷新时间
             */
            updateLastRefreshTime() {
                // #region agent log
                fetch('http://localhost:7242/ingest/8da7066a-e0c2-4e09-9af7-37ab2ebaf22c',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'home/home.js:234',message:'updateLastRefreshTime方法执行',data:{},timestamp:Date.now(),sessionId:'debug-session',runId:'post-fix',hypothesisId:'B'})}).catch(()=>{});
                // #endregion
                const refreshTimeEl = document.getElementById('lastRefreshTime');
                if (refreshTimeEl) {
                    const now = new Date();
                    refreshTimeEl.textContent = `刚刚更新 (${now.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })})`;
                }
            }
            
            /**
             * 设置加载状态
             */
            setLoading(loading) {
                this.state.setState({ loading });
            }
            
            /**
             * 启动自动刷新
             */
            startAutoRefresh() {
                const interval = (typeof DashboardConfig !== 'undefined' && DashboardConfig.ui.refreshInterval) 
                    ? DashboardConfig.ui.refreshInterval 
                    : 300000; // 5分钟
                
                if (this.refreshInterval) {
                    clearInterval(this.refreshInterval);
                }
                
                this.refreshInterval = setInterval(() => {
                    this.refreshData();
                }, interval);
            }
            
            /**
             * 停止自动刷新
             */
            stopAutoRefresh() {
                if (this.refreshInterval) {
                    clearInterval(this.refreshInterval);
                    this.refreshInterval = null;
                }
            }
            
            /**
             * 绑定事件
             */
            bindEvents() {
                // 刷新按钮
                const refreshBtn = document.getElementById('refresh-data');
                const refreshDataBtn = document.getElementById('refreshDataBtn');
                
                if (refreshBtn) {
                    refreshBtn.addEventListener('click', () => this.refreshData());
                }
                if (refreshDataBtn) {
                    refreshDataBtn.addEventListener('click', () => this.refreshData());
                }
                
                // 快速创建按钮
                const quickCreateBtn = document.getElementById('quick-create-overview');
                if (quickCreateBtn) {
                    quickCreateBtn.addEventListener('click', () => {
                        this.showToast('快速创建功能开发中', 'info');
                    });
                }
                
                // 监听状态变化
                this.state.subscribe((newState, prevState) => {
                    if (newState.loading !== prevState.loading) {
                        // 可以在这里更新UI加载状态
                    }
                });
            }
            
            /**
             * 显示Toast提示
             */
            showToast(message, type = 'info') {
                if (errorHandler && errorHandler.showToast) {
                    errorHandler.showToast(message, type);
                } else {
                    console.log(`[${type}] ${message}`);
                }
            }
            
            /**
             * 显示错误状态
             */
            showErrorState() {
                const main = document.querySelector('.workspace-main');
                if (!main) return;
                
                main.innerHTML = `
                    <div class="home-empty-state">
                        <div class="home-empty-state__icon">⚠️</div>
                        <div class="home-empty-state__title">加载失败</div>
                        <div class="home-empty-state__description">
                            无法加载工作台数据，请检查网络连接或刷新页面重试。
                        </div>
                        <button class="btn btn-primary mt-3" onclick="location.reload()">
                            刷新页面
                        </button>
                    </div>
                `;
            }
        }
        
        // #region agent log
        fetch('http://localhost:7242/ingest/8da7066a-e0c2-4e09-9af7-37ab2ebaf22c',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'home/home.js:345',message:'HomeApp类定义完成',data:{},timestamp:Date.now(),sessionId:'debug-session',runId:'post-fix',hypothesisId:'B'})}).catch(()=>{});
        // #endregion
        
        // 等待DOM加载完成后初始化
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => {
                window.homeApp = new HomeApp();
            });
        } else {
            window.homeApp = new HomeApp();
        }
    });
    
})();
