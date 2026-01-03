// 所有功能模块数据
// 使用立即执行函数包裹，避免全局作用域冲突
(function() {
    'use strict';
    
    // 检查是否已经定义，避免重复声明
    if (typeof window.allModules !== 'undefined') {
        console.warn('allModules already defined, skipping redefinition');
        return;
    }
    
    const allModules = [
            // 总览工作台场景 - 核心功能入口
            {
                id: 'customer',
                title: '客户管理',
                icon: 'bi-people-fill',
                iconColor: '#4a9cff',
                description: '客户档案管理、跟进记录、客户分类、价值评估、客户关系维护',
                status: 'normal',
                progress: 85,
                stats: [
                    { value: '156', label: '客户总数' },
                    { value: '12', label: '新增本月' },
                    { value: '23', label: '待跟进' }
                ],
                actions: [
                    { label: '新增客户', type: 'primary', icon: 'bi-plus-circle' },
                    { label: '客户列表', type: 'secondary', icon: 'bi-list-ul' },
                    { label: '价值分析', type: 'secondary', icon: 'bi-graph-up' }
                ],
                scene: 'overview'
            },
            {
                id: 'contract',
                title: '合同管理',
                icon: 'bi-file-earmark-text-fill',
                iconColor: '#28a745',
                description: '合同起草、审批、签署、履约跟踪、变更管理、归档检索',
                status: 'warning',
                progress: 60,
                stats: [
                    { value: '342', label: '合同总数' },
                    { value: '5', label: '待审批' },
                    { value: '28', label: '执行中' }
                ],
                actions: [
                    { label: '起草合同', type: 'primary', icon: 'bi-pen' },
                    { label: '待我审批', type: 'secondary', icon: 'bi-clock' },
                    { label: '合同查询', type: 'secondary', icon: 'bi-search' }
                ],
                scene: 'overview'
            },
            {
                id: 'production',
                title: '生产管理',
                icon: 'bi-gear-fill',
                iconColor: '#ffc107',
                description: '生产计划制定、生产进度跟踪、质量控制、设备管理、物料管理',
                status: 'normal',
                progress: 75,
                stats: [
                    { value: '15', label: '生产计划' },
                    { value: '2', label: '待调度' },
                    { value: '98%', label: '完成率' }
                ],
                actions: [
                    { label: '生产计划', type: 'primary', icon: 'bi-calendar-plus' },
                    { label: '进度跟踪', type: 'secondary', icon: 'bi-speedometer2' },
                    { label: '质量检查', type: 'secondary', icon: 'bi-check-circle' }
                ],
                scene: 'overview'
            },
            {
                id: 'finance',
                title: '财务管理',
                icon: 'bi-cash-coin',
                iconColor: '#17a2b8',
                description: '预算编制、费用报销、会计核算、财务报表、税务管理、资金监控',
                status: 'normal',
                progress: 90,
                stats: [
                    { value: '¥2.5M', label: '本月收入' },
                    { value: '¥1.8M', label: '本月支出' },
                    { value: '15', label: '待审核' }
                ],
                actions: [
                    { label: '费用报销', type: 'primary', icon: 'bi-receipt' },
                    { label: '预算申请', type: 'secondary', icon: 'bi-wallet2' },
                    { label: '财务报表', type: 'secondary', icon: 'bi-file-earmark-text' }
                ],
                scene: 'overview'
            },
            {
                id: 'hr',
                title: '人事管理',
                icon: 'bi-person-badge-fill',
                iconColor: '#4a9cff',
                description: '招聘管理、入职办理、考勤管理、绩效考核、薪酬管理、员工发展',
                status: 'normal',
                progress: 80,
                stats: [
                    { value: '128', label: '员工总数' },
                    { value: '3', label: '待入职' },
                    { value: '5', label: '待审批' }
                ],
                actions: [
                    { label: '员工入职', type: 'primary', icon: 'bi-person-plus' },
                    { label: '考勤管理', type: 'secondary', icon: 'bi-clock-history' },
                    { label: '薪酬发放', type: 'secondary', icon: 'bi-cash-stack' }
                ],
                scene: 'overview'
            },
            {
                id: 'admin',
                title: '行政管理',
                icon: 'bi-building-fill',
                iconColor: '#9b59b6',
                description: '办公用品管理、车辆管理、会议管理、接待管理、固定资产管理',
                status: 'normal',
                progress: 70,
                stats: [
                    { value: '156', label: '资产项' },
                    { value: '8', label: '会议安排' },
                    { value: '23', label: '用品申领' }
                ],
                actions: [
                    { label: '会议安排', type: 'primary', icon: 'bi-calendar-plus' },
                    { label: '用品申领', type: 'secondary', icon: 'bi-cart-plus' },
                    { label: '车辆调度', type: 'secondary', icon: 'bi-truck' }
                ],
                scene: 'overview'
            },
            
            // 业务运营场景
            {
                id: 'customer_business',
                title: '客户管理',
                icon: 'bi-people-fill',
                iconColor: '#4a9cff',
                description: '客户档案管理、跟进记录、客户分类、价值评估、客户关系维护',
                status: 'normal',
                progress: 85,
                stats: [
                    { value: '156', label: '客户总数' },
                    { value: '45', label: '重点客户' },
                    { value: '23', label: '待跟进' }
                ],
                actions: [
                    { label: '客户档案', type: 'primary', icon: 'bi-person-vcard' },
                    { label: '跟进记录', type: 'secondary', icon: 'bi-chat-left-text' },
                    { label: '客户分析', type: 'secondary', icon: 'bi-graph-up' }
                ],
                scene: 'business'
            },
            {
                id: 'opportunity',
                title: '商机管理',
                icon: 'bi-lightning-charge-fill',
                iconColor: '#ffc107',
                description: '销售机会跟踪、商机阶段管理、转化率分析、销售预测、竞争分析',
                status: 'normal',
                progress: 65,
                stats: [
                    { value: '48', label: '进行中' },
                    { value: '¥8.5M', label: '预计金额' },
                    { value: '35%', label: '转化率' }
                ],
                actions: [
                    { label: '新建商机', type: 'primary', icon: 'bi-plus-circle' },
                    { label: '销售漏斗', type: 'secondary', icon: 'bi-funnel' },
                    { label: '预测分析', type: 'secondary', icon: 'bi-graph-up' }
                ],
                scene: 'business'
            },
            {
                id: 'contract_business',
                title: '合同管理',
                icon: 'bi-file-earmark-text-fill',
                iconColor: '#28a745',
                description: '合同起草、审批、签署、履约跟踪、变更管理、归档检索',
                status: 'warning',
                progress: 60,
                stats: [
                    { value: '342', label: '合同总数' },
                    { value: '5', label: '待审批' },
                    { value: '28', label: '执行中' }
                ],
                actions: [
                    { label: '起草合同', type: 'primary', icon: 'bi-pen' },
                    { label: '合同审批', type: 'secondary', icon: 'bi-clipboard-check' },
                    { label: '履约跟踪', type: 'secondary', icon: 'bi-eye' }
                ],
                scene: 'business'
            },
            {
                id: 'output',
                title: '产值管理',
                icon: 'bi-bar-chart-fill',
                iconColor: '#9b59b6',
                description: '产值数据统计、产值分析、产值报告生成、产值目标管理、绩效评估',
                status: 'normal',
                progress: 95,
                stats: [
                    { value: '¥25.6M', label: '本月产值' },
                    { value: '¥312M', label: '年度累计' },
                    { value: '108%', label: '完成率' }
                ],
                actions: [
                    { label: '产值录入', type: 'primary', icon: 'bi-plus-circle' },
                    { label: '分析报告', type: 'secondary', icon: 'bi-file-earmark-text' },
                    { label: '目标管理', type: 'secondary', icon: 'bi-bullseye' }
                ],
                scene: 'business'
            },
            {
                id: 'settlement',
                title: '项目结算',
                icon: 'bi-calculator-fill',
                iconColor: '#17a2b8',
                description: '项目成本核算、收入确认、结算审批、开票管理、收款跟踪',
                status: 'normal',
                progress: 70,
                stats: [
                    { value: '18', label: '待结算' },
                    { value: '¥6.8M', label: '结算中' },
                    { value: '7', label: '超期' }
                ],
                actions: [
                    { label: '发起结算', type: 'primary', icon: 'bi-play-circle' },
                    { label: '结算列表', type: 'secondary', icon: 'bi-list-ul' },
                    { label: '催办提醒', type: 'secondary', icon: 'bi-bell' }
                ],
                scene: 'business'
            },
            {
                id: 'payment',
                title: '回款管理',
                icon: 'bi-cash-stack',
                iconColor: '#28a745',
                description: '回款计划制定、回款跟踪、逾期预警、回款分析、催收管理',
                status: 'warning',
                progress: 55,
                stats: [
                    { value: '¥4.2M', label: '待回款' },
                    { value: '¥1.8M', label: '逾期' },
                    { value: '92%', label: '回款率' }
                ],
                actions: [
                    { label: '回款登记', type: 'primary', icon: 'bi-plus-circle' },
                    { label: '逾期催收', type: 'secondary', icon: 'bi-exclamation-triangle' },
                    { label: '回款分析', type: 'secondary', icon: 'bi-graph-up' }
                ],
                scene: 'business'
            },
            
            // 生产与资源场景
            {
                id: 'production_manage',
                title: '生产管理',
                icon: 'bi-gear-fill',
                iconColor: '#ffc107',
                description: '生产计划制定、生产进度跟踪、质量控制、设备管理、物料管理',
                status: 'normal',
                progress: 75,
                stats: [
                    { value: '15', label: '生产计划' },
                    { value: '2', label: '待调度' },
                    { value: '98%', label: '完成率' }
                ],
                actions: [
                    { label: '生产计划', type: 'primary', icon: 'bi-calendar-plus' },
                    { label: '进度跟踪', type: 'secondary', icon: 'bi-speedometer2' },
                    { label: '质量检查', type: 'secondary', icon: 'bi-check-circle' }
                ],
                scene: 'production'
            },
            {
                id: 'resource',
                title: '资源管理',
                icon: 'bi-boxes',
                iconColor: '#16a085',
                description: '资源调度、库存管理、采购管理、供应商管理、资源优化',
                status: 'normal',
                progress: 80,
                stats: [
                    { value: '1568', label: '资源项' },
                    { value: '23', label: '低库存' },
                    { value: '85%', label: '利用率' }
                ],
                actions: [
                    { label: '资源调度', type: 'primary', icon: 'bi-arrow-left-right' },
                    { label: '库存盘点', type: 'secondary', icon: 'bi-clipboard-check' },
                    { label: '采购申请', type: 'secondary', icon: 'bi-cart-plus' }
                ],
                scene: 'production'
            },
            {
                id: 'archive',
                title: '档案管理',
                icon: 'bi-archive-fill',
                iconColor: '#9b59b6',
                description: '档案分类、归档、借阅、销毁、数字化管理、安全存储',
                status: 'normal',
                progress: 85,
                stats: [
                    { value: '12,456', label: '档案卷数' },
                    { value: '8', label: '待归档' },
                    { value: '3', label: '借阅中' }
                ],
                actions: [
                    { label: '档案归档', type: 'primary', icon: 'bi-inbox' },
                    { label: '档案检索', type: 'secondary', icon: 'bi-search' },
                    { label: '借阅管理', type: 'secondary', icon: 'bi-book' }
                ],
                scene: 'production'
            },
            
            // 文档与档案场景
            {
                id: 'incoming',
                title: '收文管理',
                icon: 'bi-inbox-fill',
                iconColor: '#4a9cff',
                description: '来文登记、拟办意见、领导批示、传阅办理、归档管理',
                status: 'normal',
                progress: 75,
                stats: [
                    { value: '23', label: '今日收文' },
                    { value: '5', label: '待处理' },
                    { value: '156', label: '本月累计' }
                ],
                actions: [
                    { label: '收文登记', type: 'primary', icon: 'bi-plus-circle' },
                    { label: '待办收文', type: 'secondary', icon: 'bi-clock' },
                    { label: '查询统计', type: 'secondary', icon: 'bi-graph-up' }
                ],
                scene: 'documents'
            },
            {
                id: 'outgoing',
                title: '发文管理',
                icon: 'bi-send-fill',
                iconColor: '#dc3545',
                description: '对外公文的起草、核稿、审批、编号、用印、发送与归档',
                status: 'warning',
                progress: 65,
                stats: [
                    { value: '12', label: '起草中' },
                    { value: '3', label: '待审批' },
                    { value: '2', label: '待发送' }
                ],
                actions: [
                    { label: '新建发文', type: 'primary', icon: 'bi-pencil-square' },
                    { label: '待我审批', type: 'secondary', icon: 'bi-clipboard-check' },
                    { label: '发文记录', type: 'secondary', icon: 'bi-list-ul' }
                ],
                scene: 'documents'
            },
            
            // 综合管理场景
            {
                id: 'plan',
                title: '计划管理',
                icon: 'bi-calendar-range-fill',
                iconColor: '#28a745',
                description: '年度计划、月度计划、周计划制定、执行跟踪、完成分析',
                status: 'normal',
                progress: 70,
                stats: [
                    { value: '156', label: '进行中' },
                    { value: '12', label: '超期风险' },
                    { value: '89%', label: '完成率' }
                ],
                actions: [
                    { label: '制定计划', type: 'primary', icon: 'bi-plus-circle' },
                    { label: '计划跟踪', type: 'secondary', icon: 'bi-eye' },
                    { label: '完成情况', type: 'secondary', icon: 'bi-check2-circle' }
                ],
                scene: 'management'
            },
            {
                id: 'lawsuit',
                title: '诉讼管理',
                icon: 'bi-gavel',
                iconColor: '#9b59b6',
                description: '案件登记、诉讼进度跟踪、法律文书管理、律师管理、风险评估',
                status: 'danger',
                progress: 40,
                stats: [
                    { value: '3', label: '进行中' },
                    { value: '1', label: '紧急' },
                    { value: '12', label: '本年累计' }
                ],
                actions: [
                    { label: '案件登记', type: 'primary', icon: 'bi-plus-circle' },
                    { label: '进度跟踪', type: 'secondary', icon: 'bi-clock-history' },
                    { label: '律师沟通', type: 'secondary', icon: 'bi-chat-left-text' }
                ],
                scene: 'management'
            },
            {
                id: 'risk',
                title: '风险管理',
                icon: 'bi-exclamation-triangle-fill',
                iconColor: '#ffc107',
                description: '风险识别、风险评估、风险应对、风险监控、预警管理',
                status: 'warning',
                progress: 60,
                stats: [
                    { value: '8', label: '高风险' },
                    { value: '15', label: '中风险' },
                    { value: '3', label: '新风险' }
                ],
                actions: [
                    { label: '风险识别', type: 'primary', icon: 'bi-plus-circle' },
                    { label: '风险评估', type: 'secondary', icon: 'bi-clipboard-check' },
                    { label: '风险报告', type: 'secondary', icon: 'bi-file-earmark-text' }
                ],
                scene: 'management'
            },
            {
                id: 'finance_manage',
                title: '财务管理',
                icon: 'bi-cash-coin',
                iconColor: '#17a2b8',
                description: '预算编制、费用报销、会计核算、财务报表、税务管理、资金监控',
                status: 'normal',
                progress: 90,
                stats: [
                    { value: '¥2.5M', label: '本月收入' },
                    { value: '¥1.8M', label: '本月支出' },
                    { value: '15', label: '待审核' }
                ],
                actions: [
                    { label: '费用报销', type: 'primary', icon: 'bi-receipt' },
                    { label: '预算申请', type: 'secondary', icon: 'bi-wallet2' },
                    { label: '财务报表', type: 'secondary', icon: 'bi-file-earmark-text' }
                ],
                scene: 'management'
            },
            {
                id: 'hr_manage',
                title: '人事管理',
                icon: 'bi-person-badge-fill',
                iconColor: '#4a9cff',
                description: '招聘管理、入职办理、考勤管理、绩效考核、薪酬管理、员工发展',
                status: 'normal',
                progress: 80,
                stats: [
                    { value: '128', label: '员工总数' },
                    { value: '3', label: '待入职' },
                    { value: '5', label: '待审批' }
                ],
                actions: [
                    { label: '员工入职', type: 'primary', icon: 'bi-person-plus' },
                    { label: '考勤管理', type: 'secondary', icon: 'bi-clock-history' },
                    { label: '薪酬发放', type: 'secondary', icon: 'bi-cash-stack' }
                ],
                scene: 'management'
            },
            {
                id: 'admin_manage',
                title: '行政管理',
                icon: 'bi-building-fill',
                iconColor: '#9b59b6',
                description: '办公用品管理、车辆管理、会议管理、接待管理、固定资产管理',
                status: 'normal',
                progress: 70,
                stats: [
                    { value: '156', label: '资产项' },
                    { value: '8', label: '会议安排' },
                    { value: '23', label: '用品申领' }
                ],
                actions: [
                    { label: '会议安排', type: 'primary', icon: 'bi-calendar-plus' },
                    { label: '用品申领', type: 'secondary', icon: 'bi-cart-plus' },
                    { label: '车辆调度', type: 'secondary', icon: 'bi-truck' }
                ],
                scene: 'management'
            },
            
            // 系统管理场景
            {
                id: 'system',
                title: '系统管理',
                icon: 'bi-cpu-fill',
                iconColor: '#1a5f7a',
                description: '系统配置、用户管理、权限控制、数据字典、系统日志、备份恢复',
                status: 'normal',
                progress: 95,
                stats: [
                    { value: '128', label: '用户数' },
                    { value: '18', label: '角色数' },
                    { value: '98%', label: '正常率' }
                ],
                actions: [
                    { label: '用户管理', type: 'primary', icon: 'bi-people' },
                    { label: '权限配置', type: 'secondary', icon: 'bi-shield-check' },
                    { label: '系统日志', type: 'secondary', icon: 'bi-file-earmark-text' }
                ],
                scene: 'system'
            },
            {
                id: 'workflow',
                title: '流程引擎',
                icon: 'bi-diagram-2',
                iconColor: '#9b59b6',
                description: '流程设计、流程发布、流程监控、流程优化、流程统计分析',
                status: 'normal',
                progress: 85,
                stats: [
                    { value: '56', label: '流程数' },
                    { value: '235', label: '运行中' },
                    { value: '92%', label: '成功率' }
                ],
                actions: [
                    { label: '流程设计', type: 'primary', icon: 'bi-pencil-square' },
                    { label: '流程监控', type: 'secondary', icon: 'bi-eye' },
                    { label: '流程分析', type: 'secondary', icon: 'bi-graph-up' }
                ],
                scene: 'system'
            }
        ];
        
        // 初始化页面
        
        // 更新当前日期显示
        function updateCurrentDate() {
            const dateEl = document.getElementById('current-date');
            if (dateEl) {
                const now = new Date();
                const year = now.getFullYear();
                const month = String(now.getMonth() + 1).padStart(2, '0');
                const day = String(now.getDate()).padStart(2, '0');
                const weekdays = ['日', '一', '二', '三', '四', '五', '六'];
                const weekday = weekdays[now.getDay()];
                dateEl.textContent = year + '年' + month + '月' + day + '日，星期' + weekday;
            }
        }
        
        // 加载仪表盘统计数据
        async function loadDashboardStats() {
            try {
                const response = await fetch('/api/admin/dashboard/stats/');
                if (!response.ok) {
                    throw new Error('获取统计数据失败');
                }
                const data = await response.json();
                
                if (data.success) {
                    // 更新统计卡片
                    updateStatsCards(data);
                    // 更新最后刷新时间
                    updateLastRefreshTime();
                }
            } catch (error) {
                console.error('加载统计数据失败:', error);
                // 使用默认数据
                updateStatsCards({
                    pending_tasks: 5,
                    active_projects: 3,
                    pending_items: 2,
                    completed: 12
                });
            }
        }
        
        // 更新统计卡片
        function updateStatsCards(data) {
            const container = document.getElementById('stats-cards-container');
            if (!container) return;
            
            // 更新欢迎卡片中的计数
            const pendingApprovalsEl = document.getElementById('pending-approvals-count');
            const pendingTasksEl = document.getElementById('pending-tasks-count');
            if (pendingApprovalsEl) {
                pendingApprovalsEl.textContent = `${data.pending_tasks || 0}项`;
            }
            if (pendingTasksEl) {
                pendingTasksEl.textContent = `${data.pending_items || 0}个`;
            }
            
            const stats = [
                { 
                    label: '待审批任务', 
                    value: data.pending_tasks || 0, 
                    icon: 'bi-clock-history',
                    color: 'var(--warning)',
                    url: '/admin/workflow_engine/approvalinstance/?status__exact=pending'
                },
                { 
                    label: '进行中项目', 
                    value: data.active_projects || 0, 
                    icon: 'bi-folder2-open',
                    color: 'var(--info)',
                    url: '/production/'
                },
                { 
                    label: '待处理事项', 
                    value: data.pending_items || 0, 
                    icon: 'bi-inbox',
                    color: 'var(--danger)',
                    url: '/administrative/'
                },
                { 
                    label: '本月完成', 
                    value: data.completed || 0, 
                    icon: 'bi-check-circle',
                    color: 'var(--success)',
                    url: '/production/'
                }
            ];
            
            container.innerHTML = stats.map(stat => `
                <div class="info-item">
                    <a href="${stat.url}" style="text-decoration: none; color: inherit; display: block; height: 100%;">
                        <div class="d-flex justify-content-between align-items-start" style="height: 100%;">
                            <div style="flex: 1;">
                                <div class="info-value" style="color: ${stat.color}; font-size: 2rem; font-weight: 700; line-height: 1.2; margin-bottom: 0.5rem;">
                                    ${stat.value}
                                </div>
                                <div class="info-label" style="color: var(--gray-600); font-size: 0.875rem;">
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
        
        // 加载待办事项
        async function loadDashboardTodos() {
            try {
                const response = await fetch('/api/admin/dashboard/todos/');
                if (!response.ok) {
                    throw new Error('获取待办事项失败');
                }
                const data = await response.json();
                
                if (data.success && data.todos) {
                    // 更新任务看板
                    updateTaskKanban(data.todos);
                }
            } catch (error) {
                console.error('加载待办事项失败:', error);
            }
        }
        
        // 更新任务看板
        function updateTaskKanban(todos) {
            // 按优先级和状态分类任务
            const pendingTasks = todos.filter(t => t.priority === 'high' || !t.status || t.status === 'pending').slice(0, 5);
            const inProgressTasks = todos.filter(t => t.status === 'in_progress').slice(0, 5);
            const completedTasks = todos.filter(t => t.status === 'completed').slice(0, 5);
            
            // 更新待处理任务
            const pendingContainer = document.getElementById('task-pending-container');
            if (pendingContainer) {
                if (pendingTasks.length > 0) {
                    pendingContainer.innerHTML = pendingTasks.map(task => `
                        <div class="work-item" data-task-id="${task.id || ''}">
                            <div class="work-item-header">
                                <span class="work-item-title">${task.title}</span>
                                <span class="work-item-priority priority-${task.priority || 'medium'}">${getPriorityLabel(task.priority)}</span>
                            </div>
                            <div class="work-item-description">${task.description || ''}</div>
                            <div class="work-item-footer">
                                <span class="work-item-time">${task.time || ''}</span>
                                ${task.url ? `<a href="${task.url}" class="work-item-link">查看详情 →</a>` : ''}
                            </div>
                        </div>
                    `).join('');
                } else {
                    pendingContainer.innerHTML = '<div class="text-muted text-center py-3">暂无待处理任务</div>';
                }
            }
            
            // 更新进行中任务
            const inProgressContainer = document.getElementById('task-in-progress-container');
            if (inProgressContainer) {
                if (inProgressTasks.length > 0) {
                    inProgressContainer.innerHTML = inProgressTasks.map(task => `
                        <div class="work-item" data-task-id="${task.id || ''}">
                            <div class="work-item-header">
                                <span class="work-item-title">${task.title}</span>
                            </div>
                            <div class="work-item-description">${task.description || ''}</div>
                            <div class="work-item-footer">
                                <span class="work-item-time">${task.time || ''}</span>
                                ${task.url ? `<a href="${task.url}" class="work-item-link">查看详情 →</a>` : ''}
                            </div>
                        </div>
                    `).join('');
                } else {
                    inProgressContainer.innerHTML = '<div class="text-muted text-center py-3">暂无进行中任务</div>';
                }
            }
            
            // 更新已完成任务
            const completedContainer = document.getElementById('task-completed-container');
            if (completedContainer) {
                if (completedTasks.length > 0) {
                    completedContainer.innerHTML = completedTasks.map(task => `
                        <div class="work-item" data-task-id="${task.id || ''}">
                            <div class="work-item-header">
                                <span class="work-item-title">${task.title}</span>
                            </div>
                            <div class="work-item-description">${task.description || ''}</div>
                            <div class="work-item-footer">
                                <span class="work-item-time">${task.time || ''}</span>
                                ${task.url ? `<a href="${task.url}" class="work-item-link">查看详情 →</a>` : ''}
                            </div>
                        </div>
                    `).join('');
                } else {
                    completedContainer.innerHTML = '<div class="text-muted text-center py-3">暂无已完成任务</div>';
                }
            }
            
            // 更新待办计数
            updatePendingCount();
            
            // 更新任务状态分布图
            updateTaskStatusChart(todos);
        }
        
        // 更新任务状态分布图
        function updateTaskStatusChart(todos) {
            const chartContainer = document.getElementById('task-chart-container');
            const chartCanvas = document.getElementById('taskStatusChart');
            
            if (!chartContainer || !chartCanvas) {
                return;
            }
            
            // 等待Chart.js加载完成
            if (typeof Chart === 'undefined') {
                console.warn('Chart.js未加载，无法显示图表');
                return;
            }
            
            // 统计各状态任务数量
            const statusCounts = {
                'pending': todos.filter(t => t.priority === 'high' || !t.status || t.status === 'pending').length,
                'in_progress': todos.filter(t => t.status === 'in_progress').length,
                'completed': todos.filter(t => t.status === 'completed').length
            };
            
            // 如果有数据，显示图表容器
            if (Object.values(statusCounts).some(count => count > 0)) {
                chartContainer.style.display = 'block';
                
                // 等待Chart.js加载完成
                if (typeof Chart === 'undefined' || !Chart.getChart) {
                    console.warn('Chart.js未加载，无法显示图表');
                    return;
                }
                
                // 使用Chart.js绘制图表
                try {
                    // 强制清理：先销毁全局实例
                    if (window.taskStatusChartInstance) {
                        try {
                            window.taskStatusChartInstance.destroy();
                        } catch (e) {
                            // 忽略错误
                        }
                        window.taskStatusChartInstance = null;
                    }
                    
                    // 然后检查canvas是否已经被Chart.js使用
                    const existingChart = Chart.getChart(chartCanvas);
                    if (existingChart) {
                        try {
                            existingChart.destroy();
                        } catch (e) {
                            console.warn('销毁已存在的图表时出错:', e);
                        }
                    }
                    
                    // 确保canvas没有被其他Chart实例使用
                    // 如果Chart.getChart返回null，但canvas仍然被占用，尝试重置canvas
                    const ctx = chartCanvas.getContext('2d');
                    if (!ctx) {
                        console.error('无法获取canvas上下文');
                        return;
                    }
                    
                    // 创建新图表
                    window.taskStatusChartInstance = new Chart(ctx, {
                        type: 'doughnut',
                        data: {
                            labels: ['待处理', '进行中', '已完成'],
                            datasets: [{
                                data: [statusCounts.pending, statusCounts.in_progress, statusCounts.completed],
                                backgroundColor: [
                                    'rgba(220, 53, 69, 0.8)',
                                    'rgba(23, 162, 184, 0.8)',
                                    'rgba(40, 167, 69, 0.8)'
                                ],
                                borderColor: [
                                    'rgb(220, 53, 69)',
                                    'rgb(23, 162, 184)',
                                    'rgb(40, 167, 69)'
                                ],
                                borderWidth: 2
                            }]
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: false,
                            plugins: {
                                legend: {
                                    position: 'bottom',
                                    labels: {
                                        padding: 15,
                                        usePointStyle: true
                                    }
                                },
                                tooltip: {
                                    callbacks: {
                                        label: function(context) {
                                            const label = context.label || '';
                                            const value = context.parsed || 0;
                                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                            const percentage = total > 0 ? ((value / total) * 100).toFixed(1) : 0;
                                            return `${label}: ${value} (${percentage}%)`;
                                        }
                                    }
                                }
                            }
                        }
                    });
                } catch (error) {
                    console.error('初始化任务状态分布图失败:', error);
                    // 如果初始化失败，尝试清理canvas
                    try {
                        const existingChart = Chart.getChart(chartCanvas);
                        if (existingChart) {
                            existingChart.destroy();
                        }
                    } catch (e) {
                        // 忽略清理错误
                    }
                }
            } else {
                chartContainer.style.display = 'none';
            }
        }
        
        // 获取优先级标签
        function getPriorityLabel(priority) {
            const labels = {
                'high': '高',
                'medium': '中',
                'low': '低'
            };
            return labels[priority] || '中';
        }
        
        // 更新最后刷新时间
        function updateLastRefreshTime() {
            const timeEl = document.getElementById('lastRefreshTime');
            if (timeEl) {
                const now = new Date();
                const hours = String(now.getHours()).padStart(2, '0');
                const minutes = String(now.getMinutes()).padStart(2, '0');
                timeEl.textContent = `${hours}:${minutes} 更新`;
            }
        }
        
        // 加载本周工作计划
        async function loadWeeklyProjects() {
            try {
                // 从生产管理API获取本周项目
                const response = await fetch('/api/production/api/projects/?page_size=5&ordering=-created_time');
                if (!response.ok) {
                    return;
                }
                const data = await response.json();
                
                if (data.results && data.results.length > 0) {
                    updateProjectCards(data.results);
                } else {
                    // 显示空状态
                    const container = document.getElementById('project-cards-container');
                    if (container) {
                        container.innerHTML = '<div class="text-center py-4 text-muted">本周暂无工作计划</div>';
                    }
                }
            } catch (error) {
                console.error('加载本周工作计划失败:', error);
            }
        }
        
        // 更新项目卡片
        function updateProjectCards(projects) {
            const container = document.getElementById('project-cards-container');
            if (!container) return;
            
            container.innerHTML = projects.map(project => {
                const statusColors = {
                    'planning': '#17a2b8',
                    'in_progress': '#ffc107',
                    'completed': '#28a745',
                    'paused': '#6c757d',
                    'cancelled': '#dc3545'
                };
                const statusLabels = {
                    'planning': '计划中',
                    'in_progress': '进行中',
                    'completed': '已完成',
                    'paused': '已暂停',
                    'cancelled': '已取消'
                };
                const status = project.status || 'planning';
                const statusColor = statusColors[status] || '#6c757d';
                const statusLabel = statusLabels[status] || '未知';
                
                // 计算进度百分比
                const progress = project.progress || 0;
                
                // 格式化日期
                const formatDate = (dateStr) => {
                    if (!dateStr) return '';
                    try {
                        return new Date(dateStr).toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' });
                    } catch (e) {
                        return dateStr;
                    }
                };
                
                const startDate = formatDate(project.start_date);
                const endDate = formatDate(project.end_date);
                const dateRange = startDate && endDate ? `${startDate} - ${endDate}` : (startDate || endDate || '');
                
                return `
                    <div class="project-card" onclick="window.location.href='/production/projects/${project.id}/'" style="cursor: pointer;">
                        <div class="project-card-header">
                            <div class="project-card-title-group">
                                <h6 class="project-card-title">${project.name || project.project_number || '未命名项目'}</h6>
                                ${project.project_number && project.name ? `<p class="project-card-number">${project.project_number}</p>` : ''}
                            </div>
                            <span class="project-card-status" style="background-color: ${statusColor};">
                                ${statusLabel}
                            </span>
                        </div>
                        <div class="project-card-progress">
                            <div class="project-progress-bar">
                                <div class="project-progress-fill" style="width: ${progress}%; background-color: ${statusColor};"></div>
                            </div>
                            <div class="project-card-footer">
                                <span class="project-progress-text">进度: ${progress}%</span>
                                ${dateRange ? `<span class="project-date-range">${dateRange}</span>` : ''}
                            </div>
                        </div>
                    </div>
                `;
            }).join('');
        }
        
        // 加载流程审批消息
        async function loadApprovalMessages() {
            try {
                // 从待办事项API获取审批消息
                const response = await fetch('/api/admin/dashboard/todos/');
                if (!response.ok) {
                    return;
                }
                const data = await response.json();
                
                if (data.success && data.todos) {
                    // 筛选审批相关的待办事项
                    const approvalTodos = data.todos.filter(todo => 
                        todo.title && todo.title.includes('审批')
                    );
                    
                    updateApprovalMessages(approvalTodos);
                } else {
                    updateApprovalMessages([]);
                }
            } catch (error) {
                console.error('加载流程审批消息失败:', error);
                updateApprovalMessages([]);
            }
        }
        
        // 加载模块统计数据
        async function loadModuleStats() {
            try {
                // 并行获取各模块的统计数据
                const [statsData, customerData, projectData] = await Promise.all([
                    fetch('/api/admin/dashboard/stats/').then(r => r.ok ? r.json() : null).catch(() => null),
                    fetch('/api/customer/clients/?page_size=1').then(r => r.ok ? r.json() : null).catch(() => null),
                    fetch('/api/production/api/projects/?page_size=1').then(r => r.ok ? r.json() : null).catch(() => null)
                ]);
                
                // 更新模块统计数据
                updateModuleStatsData({
                    stats: statsData,
                    customers: customerData,
                    projects: projectData
                });
            } catch (error) {
                console.error('加载模块统计数据失败:', error);
            }
        }
        
        // 更新模块统计数据
        function updateModuleStatsData(data) {
            // 更新客户管理模块
            const customerModule = allModules.find(m => m.id === 'customer');
            if (customerModule && data.customers) {
                // 从API响应中获取count（REST Framework通常返回count字段）
                const customerCount = data.customers.count || (data.customers.results ? data.customers.results.length : 0);
                customerModule.stats = [
                    { value: customerCount.toString(), label: '客户总数' },
                    { value: '0', label: '新增本月' }, // 需要单独API或从dashboard_stats获取
                    { value: '0', label: '待跟进' } // 需要单独API
                ];
            }
            
            // 更新合同管理模块
            const contractModule = allModules.find(m => m.id === 'contract');
            if (contractModule && data.stats) {
                // 合同统计数据从dashboard_stats获取待审批任务数
                contractModule.stats = [
                    { value: '0', label: '合同总数' }, // 需要单独API
                    { value: data.stats.pending_tasks?.toString() || '0', label: '待审批' },
                    { value: '0', label: '执行中' } // 需要单独API
                ];
            }
            
            // 更新生产管理模块
            const productionModule = allModules.find(m => m.id === 'production');
            if (productionModule && data.projects) {
                const projectCount = data.projects.count || (data.projects.results ? data.projects.results.length : 0);
                const activeProjects = data.stats?.active_projects || 0;
                productionModule.stats = [
                    { value: projectCount.toString(), label: '生产计划' },
                    { value: '0', label: '待调度' }, // 需要单独API
                    { value: activeProjects > 0 ? `${Math.round((activeProjects / projectCount) * 100)}%` : '0%', label: '进行中' }
                ];
            }
            
            // 更新财务管理模块
            const financeModule = allModules.find(m => m.id === 'finance');
            if (financeModule && data.stats) {
                financeModule.stats = [
                    { value: '¥0', label: '本月收入' }, // 需要单独API
                    { value: '¥0', label: '本月支出' }, // 需要单独API
                    { value: data.stats.pending_items?.toString() || '0', label: '待审核' }
                ];
            }
            
            // 重新渲染模块（如果已渲染）
            const overviewContainer = document.getElementById('overview-modules');
            if (overviewContainer) {
                renderSceneModules('overview');
            }
        }
        
        // 更新流程审批消息
        function updateApprovalMessages(messages) {
            const container = document.getElementById('approval-messages-container');
            const emptyEl = document.getElementById('approval-empty');
            const viewAllEl = document.getElementById('approval-view-all');
            
            if (!container) return;
            
            if (messages.length === 0) {
                if (emptyEl) emptyEl.style.display = 'inline';
                if (viewAllEl) viewAllEl.style.display = 'none';
                container.innerHTML = '<div class="text-center py-3 text-muted">暂无待审批流程</div>';
            } else {
                if (emptyEl) emptyEl.style.display = 'none';
                if (viewAllEl) viewAllEl.style.display = 'inline';
                
                container.innerHTML = messages.slice(0, 5).map(msg => {
                    const priorityColors = {
                        'high': 'var(--danger)',
                        'medium': 'var(--warning)',
                        'low': 'var(--info)'
                    };
                    const priorityColor = priorityColors[msg.priority] || 'var(--gray-500)';
                    
                    return `
                        <div class="approval-message-item border-bottom pb-2 mb-2">
                            <div class="d-flex align-items-start">
                                <div class="me-2">
                                    <div style="width: 8px; height: 8px; border-radius: 50%; background-color: ${priorityColor}; margin-top: 6px;"></div>
                                </div>
                                <div class="flex-grow-1">
                                    <div class="d-flex justify-content-between align-items-start">
                                        <div>
                                            <h6 class="mb-1" style="font-size: 0.875rem;">${msg.title || '审批任务'}</h6>
                                            <p class="text-muted small mb-0">${msg.description || ''}</p>
                                        </div>
                                        ${msg.url ? `<a href="${msg.url}" class="btn btn-sm btn-outline-primary">处理</a>` : ''}
                                    </div>
                                    <small class="text-muted">${msg.time || ''}</small>
                                </div>
                            </div>
                        </div>
                    `;
                }).join('');
            }
        }
        
        // 设置刷新按钮
        function setupRefreshButton() {
            const refreshBtn = document.getElementById('refreshDataBtn');
            if (refreshBtn) {
                refreshBtn.addEventListener('click', async function() {
                    // 添加旋转动画
                    const icon = refreshBtn.querySelector('span');
                    if (icon) {
                        icon.style.transform = 'rotate(360deg)';
                        setTimeout(() => {
                            icon.style.transform = 'rotate(0deg)';
                        }, 500);
                    }
                    
                    // 重新加载数据
                    showToast('正在刷新数据...', 'info');
                    await Promise.all([
                        loadDashboardStats(),
                        loadDashboardTodos(),
                        loadWeeklyProjects(),
                        loadApprovalMessages(),
                        loadModuleStats()
                    ]);
                    showToast('数据已刷新', 'success');
                });
            }
        }
// 等待Chart.js加载完成的辅助函数
function waitForChartJS(callback, maxAttempts = 50) {
    let attempts = 0;
    const checkChart = setInterval(function() {
        attempts++;
        if (typeof Chart !== 'undefined' && Chart.getChart) {
            clearInterval(checkChart);
            callback();
        } else if (attempts >= maxAttempts) {
            clearInterval(checkChart);
            console.warn('Chart.js加载超时，跳过图表初始化');
        }
    }, 100);
}

// 清理所有图表实例的辅助函数
function cleanupAllCharts() {
    try {
        // 清理taskStatusChart
        const taskChartCanvas = document.getElementById('taskStatusChart');
        if (taskChartCanvas) {
            if (typeof Chart !== 'undefined' && Chart.getChart) {
                const existingChart = Chart.getChart(taskChartCanvas);
                if (existingChart) {
                    existingChart.destroy();
                }
            }
            // 清理全局实例
            if (window.taskStatusChartInstance) {
                try {
                    window.taskStatusChartInstance.destroy();
                } catch (e) {
                    // 忽略错误
                }
                window.taskStatusChartInstance = null;
            }
        }
        
        // 清理projectStatusChart
        const projectChartCanvas = document.getElementById('projectStatusChart');
        if (projectChartCanvas) {
            if (typeof Chart !== 'undefined' && Chart.getChart) {
                const existingChart = Chart.getChart(projectChartCanvas);
                if (existingChart) {
                    existingChart.destroy();
                }
            }
            if (window.projectStatusChartInstance) {
                try {
                    window.projectStatusChartInstance.destroy();
                } catch (e) {
                    // 忽略错误
                }
                window.projectStatusChartInstance = null;
            }
        }
    } catch (e) {
        console.warn('清理图表实例时出错:', e);
    }
}

document.addEventListener('DOMContentLoaded', function() {
            // 显示当前日期
            updateCurrentDate();
            
            // 立即清理可能存在的旧图表实例（防止冲突）
            cleanupAllCharts();
            
            // 等待Chart.js加载完成后再清理一次
            waitForChartJS(function() {
                cleanupAllCharts();
            });
            
            // 加载统计数据
            loadDashboardStats();
            
            // 加载待办事项（会在Chart.js加载后自动初始化图表）
            waitForChartJS(function() {
                loadDashboardTodos();
            });
            
            // 加载通知
            loadNotifications();
            
            // 等待Chart.js加载完成后再加载其他数据
            waitForChartJS(function() {
                // 加载本周工作计划
                loadWeeklyProjects();
                
                // 加载流程审批消息
                loadApprovalMessages();
                
                // 加载模块统计数据
                loadModuleStats();
            });
            
            // 渲染总览页模块
            renderSceneModules('overview');
            
            // 设置场景切换
            setupSceneNavigation();
            
            // 设置模块交互
            setupModuleInteractions();
            
            // 设置待办工作交互
            setupPendingWorkInteractions();
            
            // 设置按钮事件
            setupButtonEvents();
            
            // 设置搜索功能
            setupSearchFunction();
            
            // 初始化进度条动画
            initializeProgressBars();
            
            // 设置数据刷新按钮
            setupRefreshButton();
        });
        
        // 渲染场景模块
        function renderSceneModules(sceneId) {
            const container = document.getElementById(`${sceneId}-modules`);
            if (!container) {
                // 如果容器不存在，尝试创建
                const sceneContent = document.querySelector(`#scene-${sceneId}`);
                if (sceneContent) {
                    const modulesGrid = document.createElement('div');
                    modulesGrid.className = 'modules-grid';
                    modulesGrid.id = `${sceneId}-modules`;
                    sceneContent.appendChild(modulesGrid);
                } else {
                    return;
                }
            }
            
            const sceneModules = allModules.filter(m => m.scene === sceneId);
            
            if (sceneModules.length === 0) {
                container.innerHTML = `
                    <div class="col-12">
                        <div class="text-center py-5">
                            <i class="bi bi-inbox fs-1 text-muted"></i>
                            <h5 class="mt-3 text-muted">暂无数据</h5>
                            <p class="text-muted">该场景下暂无功能模块</p>
                        </div>
                    </div>
                `;
                return;
            }
            
            container.innerHTML = sceneModules.map(module => createModuleCard(module)).join('');
            
            // 重新绑定新模块的交互
            setTimeout(() => {
                setupModuleInteractions();
                initializeProgressBars();
            }, 100);
        }
        
        // 创建模块卡片HTML
        function createModuleCard(module) {
            const statusTexts = {
                'normal': '运行正常',
                'warning': '需要注意',
                'danger': '存在风险'
            };
            
            return `
                <div class="module-card" data-module="${module.id}">
                    <div class="module-header">
                        <div class="module-icon" style="background: linear-gradient(135deg, ${module.iconColor}, ${adjustColor(module.iconColor, -30)})">
                            <i class="bi ${module.icon}"></i>
                        </div>
                        <div class="module-title-wrapper">
                            <h5 class="module-title">${module.title}</h5>
                            <div class="module-subtitle">
                                <span class="module-status status-${module.status}">
                                    ${statusTexts[module.status]}
                                </span>
                            </div>
                        </div>
                    </div>
                    <p class="module-desc">${module.description}</p>
                    <div class="module-stats">
                        ${module.stats.map(stat => `
                            <div class="stat-item">
                                <span class="stat-value">${stat.value}</span>
                                <span class="stat-label">${stat.label}</span>
                            </div>
                        `).join('')}
                    </div>
                    <div class="module-actions">
                        ${module.actions.map(action => `
                            <a href="#" class="module-btn module-btn-${action.type}" data-action="${module.id}-${action.label}">
                                <i class="bi ${action.icon}"></i> ${action.label}
                            </a>
                        `).join('')}
                    </div>
                </div>
            `;
        }
        
        // 辅助函数：调整颜色亮度
        function adjustColor(color, amount) {
            let usePound = false;
            if (color[0] === "#") {
                color = color.slice(1);
                usePound = true;
            }
            
            const num = parseInt(color, 16);
            let r = (num >> 16) + amount;
            let g = ((num >> 8) & 0x00FF) + amount;
            let b = (num & 0x0000FF) + amount;
            
            r = r < 0 ? 0 : (r > 255 ? 255 : r);
            g = g < 0 ? 0 : (g > 255 ? 255 : g);
            b = b < 0 ? 0 : (b > 255 ? 255 : b);
            
            return (usePound ? "#" : "") + (b | (g << 8) | (r << 16)).toString(16).padStart(6, '0');
        }
        
        // 设置场景导航
        function setupSceneNavigation() {
            const navItems = document.querySelectorAll('.nav-item[data-scene]');
            const sceneContents = document.querySelectorAll('.scene-content');
            
            navItems.forEach(item => {
                item.addEventListener('click', function(e) {
                    e.preventDefault();
                    
                    // 更新激活状态
                    navItems.forEach(i => i.classList.remove('active'));
                    this.classList.add('active');
                    
                    // 显示对应的场景内容
                    const sceneId = this.getAttribute('data-scene');
                    sceneContents.forEach(content => {
                        content.style.display = 'none';
                        content.classList.remove('active');
                        if (content.id === `scene-${sceneId}`) {
                            content.style.display = 'flex';
                            content.classList.add('active');
                            document.title = `${this.querySelector('.text').textContent.trim()} - 维海科技信息化管理平台`;
                        }
                    });
                    
                    // 渲染该场景的模块
                    renderSceneModules(sceneId);
                    
                    // 保存当前场景到本地存储
                    localStorage.setItem('lastActiveScene', sceneId);
                });
            });
            
            // 恢复上次访问的场景
            const lastScene = localStorage.getItem('lastActiveScene') || 'overview';
            const lastSceneItem = document.querySelector(`.nav-item[data-scene="${lastScene}"]`);
            if (lastSceneItem && lastScene !== 'overview') {
                lastSceneItem.click();
            }
        }
        
        // 设置模块交互
        function setupModuleInteractions() {
            // 模块卡片点击
            document.querySelectorAll('.module-card').forEach(card => {
                card.addEventListener('click', function(e) {
                    if (e.target.closest('.module-btn')) return;
                    
                    const moduleId = this.getAttribute('data-module');
                    const module = allModules.find(m => m.id === moduleId);
                    if (module) {
                        showModuleDetail(module);
                    }
                });
            });
            
            // 模块按钮点击
            document.querySelectorAll('.module-btn').forEach(btn => {
                btn.addEventListener('click', function(e) {
                    e.preventDefault();
                    e.stopPropagation();
                    
                    const action = this.getAttribute('data-action');
                    const [moduleId, actionLabel] = action.split('-');
                    const module = allModules.find(m => m.id === moduleId);
                    
                    if (module) {
                        showActionToast(module.title, actionLabel);
                    }
                });
            });
            
            // 快捷操作点击
            document.querySelectorAll('[data-quick-action]').forEach(item => {
                item.addEventListener('click', function(e) {
                    e.preventDefault();
                    const action = this.getAttribute('data-quick-action');
                    handleQuickAction(action);
                });
            });
            
            // 常用功能点击
            document.querySelectorAll('[data-favorite]').forEach(item => {
                item.addEventListener('click', function(e) {
                    e.preventDefault();
                    const favorite = this.getAttribute('data-favorite');
                    handleFavorite(favorite);
                });
            });
        }
        
        // 显示模块详情
        function showModuleDetail(module) {
            // 创建模态框
            const modalHTML = `
                <div class="modal fade" id="moduleDetailModal" tabindex="-1">
                    <div class="modal-dialog modal-lg modal-dialog-centered">
                        <div class="modal-content">
                            <div class="modal-header">
                                <div class="d-flex align-items-center gap-3">
                                    <div class="module-icon" style="width: 3rem; height: 3rem; background: linear-gradient(135deg, ${module.iconColor}, ${adjustColor(module.iconColor, -30)})">
                                        <i class="bi ${module.icon}" style="font-size: 1.25rem;"></i>
                                    </div>
                                    <div>
                                        <h5 class="modal-title mb-0">${module.title}</h5>
                                        <div class="d-flex align-items-center gap-2 mt-1">
                                            <span class="badge bg-${module.status === 'normal' ? 'success' : module.status === 'warning' ? 'warning' : 'danger'}">
                                                ${module.status === 'normal' ? '运行正常' : module.status === 'warning' ? '需要注意' : '存在风险'}
                                            </span>
                                        </div>
                                    </div>
                                </div>
                                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                            </div>
                            <div class="modal-body">
                                <h6>功能描述</h6>
                                <p class="mb-4">${module.description}</p>
                                
                                <h6 class="mt-4">关键指标</h6>
                                <div class="row g-3 mb-4">
                                    ${module.stats.map(stat => `
                                        <div class="col-md-4">
                                            <div class="card border-0 bg-light">
                                                <div class="card-body text-center py-3">
                                                    <div class="h5 mb-1">${stat.value}</div>
                                                    <div class="text-muted small">${stat.label}</div>
                                                </div>
                                            </div>
                                        </div>
                                    `).join('')}
                                </div>
                                
                                <h6 class="mt-4">操作指南</h6>
                                <ul class="list-group list-group-flush">
                                    ${module.actions.map((action, index) => `
                                        <li class="list-group-item d-flex align-items-center">
                                            <span class="badge bg-primary me-3">${index + 1}</span>
                                            <div>
                                                <strong>${action.label}</strong>
                                                <div class="text-muted small mt-1">
                                                    ${getActionDescription(module.id, action.label)}
                                                </div>
                                            </div>
                                        </li>
                                    `).join('')}
                                </ul>
                            </div>
                            <div class="modal-footer">
                                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">关闭</button>
                                <button type="button" class="btn btn-primary" onclick="enterModule('${module.id}')">
                                    进入模块
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            `;
            
            // 移除现有的模态框
            const existingModal = document.getElementById('moduleDetailModal');
            if (existingModal) existingModal.remove();
            
            // 添加新的模态框
            document.body.insertAdjacentHTML('beforeend', modalHTML);
            
            // 显示模态框
            const modal = new bootstrap.Modal(document.getElementById('moduleDetailModal'));
            modal.show();
        }
        
        // 获取操作描述
        function getActionDescription(moduleId, actionLabel) {
            const descriptions = {
                'customer-新增客户': '填写客户基本信息，建立客户档案，分配客户经理',
                'customer-客户列表': '查看所有客户信息，支持筛选、搜索和导出',
                'customer-价值分析': '分析客户贡献度，评估客户价值等级',
                'contract-起草合同': '选择合同模板，填写合同内容，添加附件',
                'contract-待我审批': '查看需要审批的合同，支持批量审批',
                'contract-合同查询': '按条件查询合同，查看合同详情和历史记录',
                'finance-费用报销': '填写报销单，上传发票，提交审批',
                'finance-预算申请': '申请预算额度，填写预算明细，提交审批',
                'finance-财务报表': '生成财务报表，导出数据，分析财务指标',
                'hr-员工入职': '填写入职信息，上传证件，分配权限',
                'hr-考勤管理': '查看考勤记录，处理异常，生成考勤报表',
                'hr-薪酬发放': '计算薪酬，生成工资条，处理发放流程',
                'system-用户管理': '添加/编辑用户，分配角色，设置权限',
                'system-权限配置': '配置系统权限，设置角色，管理访问控制',
                'system-系统日志': '查看系统操作日志，分析系统运行状况',
                'workflow-流程设计': '设计工作流程，配置节点，设置审批规则',
                'workflow-流程监控': '监控流程运行状态，处理异常流程',
                'workflow-流程分析': '分析流程效率，优化流程设计'
            };
            
            return descriptions[`${moduleId}-${actionLabel}`] || '执行相关操作';
        }
        
        // 进入模块
        function enterModule(moduleId) {
            const module = allModules.find(m => m.id === moduleId);
            if (module) {
                // 模块路由映射
                const moduleRoutes = {
                    'contract': '/business/contracts/',
                    'contract_business': '/business/contracts/',
                    'customer': '/business/',
                    'customer_business': '/business/',
                    'production': '/production/',
                    'production_manage': '/production/',
                    'finance': '/financial/',
                    'finance_manage': '/financial/',
                    'hr': '/personnel/',
                    'hr_manage': '/personnel/',
                    'admin': '/administrative/',
                    'admin_manage': '/administrative/',
                    'opportunity': '/business/opportunities/',
                    'output': '/settlement/output-value/',
                    'settlement': '/settlement/project-settlement/',
                    'payment': '/settlement/payment-management/',
                    'resource': '/resource/',
                    'archive': '/archive/',
                    'incoming': '/delivery/incoming-document/',
                    'outgoing': '/delivery/outgoing-document/',
                    'plan': '/plan/',
                    'lawsuit': '/litigation/',
                    'risk': '/risk/',
                    'system': '/system-center/',
                    'workflow': '/workflow/'
                };
                
                // 查找对应的路由
                const route = moduleRoutes[moduleId];
                if (route) {
                    // 直接跳转到对应的功能模块页面
                    window.location.href = route;
                } else {
                    // 如果没有对应的路由，显示提示
                    showToast(`进入 ${module.title} 模块`, 'success');
                    setTimeout(() => {
                        alert(`即将跳转到 ${module.title} 模块的主页面`);
                    }, 500);
                }
            }
        }
        
        // 显示操作提示
        function showActionToast(moduleTitle, actionLabel) {
            showToast(`执行操作：${moduleTitle} - ${actionLabel}`, 'info');
        }
        
        // 显示Toast消息
        function showToast(message, type = 'info') {
            const toastHTML = `
                <div class="toast align-items-center text-white bg-${type === 'success' ? 'success' : type === 'error' ? 'danger' : 'primary'} border-0" role="alert">
                    <div class="d-flex">
                        <div class="toast-body">
                            <i class="bi ${type === 'success' ? 'bi-check-circle' : type === 'error' ? 'bi-exclamation-circle' : 'bi-info-circle'} me-2"></i>
                            ${message}
                        </div>
                        <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
                    </div>
                </div>
            `;
            
            const toastContainer = document.createElement('div');
            toastContainer.className = 'toast-container position-fixed bottom-0 end-0 p-3';
            toastContainer.innerHTML = toastHTML;
            document.body.appendChild(toastContainer);
            
            const toast = new bootstrap.Toast(toastContainer.querySelector('.toast'));
            toast.show();
            
            toastContainer.querySelector('.toast').addEventListener('hidden.bs.toast', () => {
                toastContainer.remove();
            });
        }
        
        // 处理快捷操作
        function handleQuickAction(action) {
            const actions = {
                'approval': { title: '快速审批', description: '处理待审批事项' },
                'meeting': { title: '安排会议', description: '创建新的会议安排' },
                'report': { title: '新建报告', description: '生成工作报告' },
                'workflow': { title: '流程设计', description: '设计工作流程' }
            };
            
            const actionInfo = actions[action];
            if (actionInfo) {
                showToast(`${actionInfo.title}: ${actionInfo.description}`, 'info');
            }
        }
        
        // 处理常用功能
        function handleFavorite(favorite) {
            // 直接跳转到对应的功能模块页面
            const favoriteRoutes = {
                'contract': '/business/contracts/',
                'project': '/production/',
                'finance': '/financial/',
                'hr': '/personnel/'
            };
            
            const route = favoriteRoutes[favorite];
            if (route) {
                window.location.href = route;
                return;
            }
            
            // 如果没有对应的路由，则显示模块详情（保留原有逻辑作为后备）
            const favorites = {
                'contract': '合同管理',
                'project': '项目管理',
                'finance': '财务管理',
                'hr': '人事管理'
            };
            
            const favoriteName = favorites[favorite];
            if (favoriteName) {
                // 找到对应的模块并显示详情
                const module = allModules.find(m => 
                    (favorite === 'contract' && m.title === '合同管理') ||
                    (favorite === 'project' && m.title === '项目管理') ||
                    (favorite === 'finance' && m.title === '财务管理') ||
                    (favorite === 'hr' && m.title === '人事管理')
                );
                
                if (module) {
                    showModuleDetail(module);
                }
            }
        }
        
        // 设置待办工作交互
        function setupPendingWorkInteractions() {
            document.querySelectorAll('.pending-works .btn').forEach((btn, index) => {
                btn.addEventListener('click', function() {
                    const workItems = document.querySelectorAll('.work-item');
                    const workTitle = workItems[index].querySelector('.work-title').textContent;
                    
                    showToast(`处理工作：${workTitle}`, 'info');
                    
                    // 模拟处理完成
                    if (this.textContent.includes('重新提交') || this.textContent.includes('立即审批')) {
                        const workItem = this.closest('.work-item');
                        workItem.style.opacity = '0.5';
                        setTimeout(() => {
                            workItem.remove();
                            updatePendingCount();
                            showToast('工作项已处理完成', 'success');
                        }, 300);
                    }
                });
            });
        }
        
        // 更新待处理计数
        function updatePendingCount() {
            const remaining = document.querySelectorAll('.work-item').length;
            
            // 更新欢迎区域的计数
            const countElements = document.querySelectorAll('.welcome-subtitle strong');
            countElements.forEach(el => {
                el.textContent = `${remaining}项`;
            });
            
            // 更新指标卡片
            const metricCard = document.querySelector('.metric-card:first-child .metric-value');
            if (metricCard) {
                metricCard.textContent = remaining;
            }
            
            // 更新通知徽章（使用待办事项数量）
            updateNotificationBadge(remaining);
        }
        
        // 设置按钮事件
        function setupButtonEvents() {
            // 欢迎卡片按钮事件已移除 - 仅作为展示元素
            // document.querySelectorAll('#quick-create, #quick-create-overview').forEach(btn => {
            //     btn.addEventListener('click', function() {
            //         showQuickCreateMenu();
            //     });
            // });
            
            // document.getElementById('refresh-data')?.addEventListener('click', function() {
            //     showToast('数据刷新成功', 'success');
            //     // 模拟数据刷新
            //     setTimeout(() => {
            //         initializeProgressBars();
            //     }, 500);
            // });
            
            // 新建工作按钮
            document.getElementById('quick-work')?.addEventListener('click', function() {
                showQuickCreateMenu();
            });
            
            // 帮助按钮
            document.getElementById('help-btn')?.addEventListener('click', function() {
                showHelpModal();
            });
            
            // 通知按钮
            document.getElementById('notification-btn')?.addEventListener('click', function() {
                showNotificationsModal();
            });
        }
        
        // 显示快速新建菜单
        function showQuickCreateMenu() {
            const menuHTML = `
                <div class="modal fade" id="quickCreateModal" tabindex="-1">
                    <div class="modal-dialog modal-dialog-centered">
                        <div class="modal-content">
                            <div class="modal-header">
                                <h5 class="modal-title">快速新建</h5>
                                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                            </div>
                            <div class="modal-body">
                                <div class="list-group list-group-flush">
                                    <a href="#" class="list-group-item list-group-item-action d-flex align-items-center" onclick="createItem('contract')">
                                        <div class="bg-primary bg-opacity-10 p-2 rounded me-3">
                                            <i class="bi bi-file-earmark-text text-primary"></i>
                                        </div>
                                        <div>
                                            <strong>新建合同</strong>
                                            <div class="text-muted small">创建销售/采购合同</div>
                                        </div>
                                    </a>
                                    <a href="#" class="list-group-item list-group-item-action d-flex align-items-center" onclick="createItem('customer')">
                                        <div class="bg-info bg-opacity-10 p-2 rounded me-3">
                                            <i class="bi bi-person-plus text-info"></i>
                                        </div>
                                        <div>
                                            <strong>新建客户</strong>
                                            <div class="text-muted small">添加新客户档案</div>
                                        </div>
                                    </a>
                                    <a href="#" class="list-group-item list-group-item-action d-flex align-items-center" onclick="createItem('project')">
                                        <div class="bg-success bg-opacity-10 p-2 rounded me-3">
                                            <i class="bi bi-kanban text-success"></i>
                                        </div>
                                        <div>
                                            <strong>新建项目</strong>
                                            <div class="text-muted small">创建新的项目计划</div>
                                        </div>
                                    </a>
                                    <a href="#" class="list-group-item list-group-item-action d-flex align-items-center" onclick="createItem('task')">
                                        <div class="bg-warning bg-opacity-10 p-2 rounded me-3">
                                            <i class="bi bi-list-task text-warning"></i>
                                        </div>
                                        <div>
                                            <strong>新建任务</strong>
                                            <div class="text-muted small">创建待办任务</div>
                                        </div>
                                    </a>
                                    <a href="#" class="list-group-item list-group-item-action d-flex align-items-center" onclick="createItem('report')">
                                        <div class="bg-danger bg-opacity-10 p-2 rounded me-3">
                                            <i class="bi bi-file-earmark-text text-danger"></i>
                                        </div>
                                        <div>
                                            <strong>新建报告</strong>
                                            <div class="text-muted small">生成工作报告</div>
                                        </div>
                                    </a>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            `;
            
            // 移除现有的模态框
            const existingModal = document.getElementById('quickCreateModal');
            if (existingModal) existingModal.remove();
            
            // 添加新的模态框
            document.body.insertAdjacentHTML('beforeend', menuHTML);
            
            // 显示模态框
            const modal = new bootstrap.Modal(document.getElementById('quickCreateModal'));
            modal.show();
        }
        
        // 创建项目
        function createItem(type) {
            const routes = {
                'contract': '/business/contracts/create/',
                'customer': '/business/customers/create/',
                'project': '/production/projects/create/',
                'task': '/workflow/',
                'report': '/archive/'
            };
            
            const route = routes[type];
            if (route) {
                window.location.href = route;
            } else {
                showToast(`创建功能开发中...`, 'info');
            }
        }
        
        // 显示帮助模态框
        function showHelpModal() {
            const helpHTML = `
                <div class="modal fade" id="helpModal" tabindex="-1">
                    <div class="modal-dialog modal-lg">
                        <div class="modal-content">
                            <div class="modal-header">
                                <h5 class="modal-title"><i class="bi bi-question-circle me-2"></i>帮助中心</h5>
                                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                            </div>
                            <div class="modal-body">
                                <div class="row">
                                    <div class="col-md-6">
                                        <h6>快速开始</h6>
                                        <ul class="list-unstyled">
                                            <li class="mb-2">
                                                <i class="bi bi-play-circle text-primary me-2"></i>
                                                <a href="#" class="text-decoration-none">平台使用指南</a>
                                            </li>
                                            <li class="mb-2">
                                                <i class="bi bi-film text-primary me-2"></i>
                                                <a href="#" class="text-decoration-none">视频教程</a>
                                            </li>
                                            <li class="mb-2">
                                                <i class="bi bi-card-checklist text-primary me-2"></i>
                                                <a href="#" class="text-decoration-none">常见问题解答</a>
                                            </li>
                                        </ul>
                                    </div>
                                    <div class="col-md-6">
                                        <h6>技术支持</h6>
                                        <ul class="list-unstyled">
                                            <li class="mb-2">
                                                <i class="bi bi-telephone text-success me-2"></i>
                                                技术支持热线：400-123-4567
                                            </li>
                                            <li class="mb-2">
                                                <i class="bi bi-envelope text-success me-2"></i>
                                                邮箱：support@company.com
                                            </li>
                                            <li class="mb-2">
                                                <i class="bi bi-clock text-success me-2"></i>
                                                服务时间：工作日 9:00-18:00
                                            </li>
                                        </ul>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            `;
            
            // 移除现有的模态框
            const existingModal = document.getElementById('helpModal');
            if (existingModal) existingModal.remove();
            
            // 添加新的模态框
            document.body.insertAdjacentHTML('beforeend', helpHTML);
            
            // 显示模态框
            const modal = new bootstrap.Modal(document.getElementById('helpModal'));
            modal.show();
        }
        
        // 加载通知
        async function loadNotifications() {
            try {
                // 从待办事项API获取通知数据
                const response = await fetch('/api/admin/dashboard/todos/');
                if (!response.ok) {
                    return;
                }
                const data = await response.json();
                
                if (data.success && data.todos) {
                    // 更新通知徽章数量
                    updateNotificationBadge(data.todos.length);
                }
            } catch (error) {
                console.error('加载通知失败:', error);
            }
        }
        
        // 更新通知徽章
        function updateNotificationBadge(count) {
            const badge = document.querySelector('#notification-btn .badge');
            if (badge) {
                if (count > 0) {
                    badge.textContent = count > 99 ? '99+' : count;
                    badge.style.display = 'inline-block';
                } else {
                    badge.style.display = 'none';
                }
            }
        }
        
        // 显示通知模态框
        async function showNotificationsModal() {
            // 加载最新通知
            let notifications = [];
            try {
                const response = await fetch('/api/admin/dashboard/todos/');
                if (response.ok) {
                    const data = await response.json();
                    if (data.success && data.todos) {
                        notifications = data.todos;
                    }
                }
            } catch (error) {
                console.error('加载通知失败:', error);
            }
            
            // 构建通知列表HTML
            let notificationsHTML = '';
            if (notifications.length > 0) {
                notificationsHTML = notifications.map(notif => {
                    const iconClass = notif.priority === 'high' ? 'bi-exclamation-circle text-danger' : 
                                     notif.priority === 'medium' ? 'bi-info-circle text-warning' : 
                                     'bi-check-circle text-success';
                    const bgClass = notif.priority === 'high' ? 'bg-danger bg-opacity-10' : 
                                   notif.priority === 'medium' ? 'bg-warning bg-opacity-10' : 
                                   'bg-success bg-opacity-10';
                    return `
                        <div class="notification-item border-bottom pb-3 mb-3">
                            <div class="d-flex align-items-start">
                                <div class="me-3">
                                    <div class="${bgClass} p-2 rounded">
                                        <i class="bi ${iconClass}"></i>
                                    </div>
                                </div>
                                <div class="flex-grow-1">
                                    <h6 class="mb-1">${notif.title || '通知'}</h6>
                                    <p class="mb-1 text-muted small">${notif.description || ''}</p>
                                    <span class="text-muted smaller">${notif.time || ''}</span>
                                </div>
                                ${notif.url ? `<div><a href="${notif.url}" class="btn btn-sm btn-outline-primary">查看</a></div>` : ''}
                            </div>
                        </div>
                    `;
                }).join('');
            } else {
                notificationsHTML = `
                    <div class="text-center py-5">
                        <i class="bi bi-bell-slash" style="font-size: 3rem; color: var(--gray-400);"></i>
                        <p class="text-muted mt-3">暂无通知</p>
                    </div>
                `;
            }
            
            const modalHTML = `
                <div class="modal fade" id="notificationsModal" tabindex="-1">
                    <div class="modal-dialog modal-dialog-centered modal-lg">
                        <div class="modal-content">
                            <div class="modal-header">
                                <h5 class="modal-title"><i class="bi bi-bell me-2"></i>通知中心</h5>
                                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                            </div>
                            <div class="modal-body" style="max-height: 500px; overflow-y: auto;">
                                ${notificationsHTML}
                            </div>
                            <div class="modal-footer">
                                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">关闭</button>
                                ${notifications.length > 0 ? '<button type="button" class="btn btn-primary" onclick="markAllAsRead()">全部已读</button>' : ''}
                            </div>
                        </div>
                    </div>
                </div>
            `;
            
            // 移除现有的模态框
            const existingModal = document.getElementById('notificationsModal');
            if (existingModal) existingModal.remove();
            
            // 添加新的模态框
            document.body.insertAdjacentHTML('beforeend', modalHTML);
            
            // 显示模态框
            const modal = new bootstrap.Modal(document.getElementById('notificationsModal'));
            modal.show();
        }
        
        // 标记全部已读
        function markAllAsRead() {
            // 更新通知徽章
            updateNotificationBadge(0);
            showToast('所有通知已标记为已读', 'success');
            
            // 关闭模态框
            const modal = bootstrap.Modal.getInstance(document.getElementById('notificationsModal'));
            if (modal) {
                modal.hide();
            }
            
            // 重新加载通知以更新显示
            loadNotifications();
        }
        
        // 设置搜索功能
        function setupSearchFunction() {
            const searchInput = document.getElementById('global-search');
            if (!searchInput) return;
            
            searchInput.addEventListener('keypress', function(e) {
                if (e.key === 'Enter' && this.value.trim()) {
                    performSearch(this.value.trim());
                }
            });
        }
        
        // 执行搜索
        async function performSearch(query) {
            if (!query || query.trim().length < 2) {
                showToast('请输入至少2个字符进行搜索', 'warning');
                return;
            }
            
            showToast('正在搜索...', 'info');
            
            try {
                // 并行搜索多个数据源
                const [modules, customers, contracts] = await Promise.all([
                    searchModules(query),
                    searchCustomers(query),
                    searchContracts(query)
                ]);
                
                // 合并结果
                const allResults = {
                    modules: modules,
                    customers: customers,
                    contracts: contracts,
                    total: modules.length + customers.length + contracts.length
                };
                
                if (allResults.total > 0) {
                    showSearchResults(allResults, query);
                } else {
                    showToast(`未找到与"${query}"相关的结果`, 'warning');
                }
            } catch (error) {
                console.error('搜索失败:', error);
                showToast('搜索失败，请稍后重试', 'error');
            }
        }
        
        // 搜索模块
        function searchModules(query) {
            return new Promise((resolve) => {
                const results = allModules.filter(module => 
                    module.title.toLowerCase().includes(query.toLowerCase()) ||
                    module.description.toLowerCase().includes(query.toLowerCase())
                ).map(module => ({
                    type: 'module',
                    title: module.title,
                    description: module.description,
                    icon: module.icon,
                    iconColor: module.iconColor,
                    url: getModuleUrl(module.id),
                    category: '功能模块'
                }));
                resolve(results);
            });
        }
        
        // 搜索客户
        async function searchCustomers(query) {
            try {
                const response = await fetch(`/api/customer/search-company/?keyword=${encodeURIComponent(query)}&num=5`);
                if (!response.ok) {
                    return [];
                }
                const data = await response.json();
                if (data.success && data.data && data.data.items) {
                    return data.data.items.map(item => ({
                        type: 'customer',
                        title: item.name,
                        description: `统一社会信用代码: ${item.credit_no || '未知'}`,
                        icon: 'bi-building',
                        iconColor: '#4a9cff',
                        url: `/business/customers/?search=${encodeURIComponent(item.name)}`,
                        category: '客户',
                        creditNo: item.credit_no
                    }));
                }
                return [];
            } catch (error) {
                console.error('搜索客户失败:', error);
                return [];
            }
        }
        
        // 搜索合同
        async function searchContracts(query) {
            try {
                // 合同管理API路径：/api/customer/contract_management/api/contracts/
                // 或者使用客户管理模块的合同搜索功能
                const response = await fetch(`/api/customer/clients/?search=${encodeURIComponent(query)}&page_size=5`);
                if (!response.ok) {
                    // 如果客户API失败，尝试直接搜索合同（如果API存在）
                    try {
                        const contractResponse = await fetch(`/business/contracts/?search=${encodeURIComponent(query)}`);
                        // 这里可能需要解析HTML或使用其他方式获取合同数据
                        return [];
                    } catch (e) {
                        return [];
                    }
                }
                const data = await response.json();
                // 客户API返回的是客户列表，不是合同列表
                // 合同搜索功能可能需要通过页面路由实现
                // 暂时返回空数组，等待合同搜索API完善
                return [];
            } catch (error) {
                console.error('搜索合同失败:', error);
                return [];
            }
        }
        
        // 获取模块URL
        function getModuleUrl(moduleId) {
            const moduleRoutes = {
                'contract': '/business/contracts/',
                'customer': '/business/',
                'production': '/production/',
                'finance': '/financial/',
                'hr': '/personnel/',
                'admin': '/administrative/',
                'opportunity': '/business/opportunities/',
                'output': '/settlement/output-value/',
                'settlement': '/settlement/project-settlement/',
                'payment': '/settlement/payment-management/',
                'resource': '/resource/',
                'archive': '/archive/',
                'incoming': '/delivery/incoming-document/',
                'outgoing': '/delivery/outgoing-document/',
                'plan': '/plan/',
                'lawsuit': '/litigation/',
                'risk': '/risk/',
                'system': '/system-center/',
                'workflow': '/workflow/'
            };
            return moduleRoutes[moduleId] || '#';
        }
        
        // 显示搜索结果
        function showSearchResults(results, query) {
            // 如果results是数组（旧格式），转换为新格式
            if (Array.isArray(results)) {
                results = {
                    modules: results,
                    customers: [],
                    contracts: [],
                    total: results.length
                };
            }
            
            let resultsHTML = `
                <div class="modal fade" id="searchResultsModal" tabindex="-1">
                    <div class="modal-dialog modal-xl">
                        <div class="modal-content">
                            <div class="modal-header">
                                <h5 class="modal-title"><i class="bi bi-search me-2"></i>搜索结果</h5>
                                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                            </div>
                            <div class="modal-body">
                                <p class="text-muted mb-3">
                                    <strong>${results.total || 0}</strong> 个与 "<strong>${query}</strong>" 相关的结果
                                </p>
                                <div class="search-results-container">
            `;
            
            // 按分类显示结果
            if (results.modules && results.modules.length > 0) {
                resultsHTML += `
                    <div class="search-category mb-4">
                        <h6 class="category-title mb-3">
                            <i class="bi bi-grid-3x3-gap me-2"></i>功能模块 (${results.modules.length})
                        </h6>
                        <div class="row g-3">
                            ${results.modules.map(item => {
                                const module = typeof item === 'object' && item.id ? item : allModules.find(m => m.id === item.id || m.title === item.title);
                                if (!module) return '';
                                return `
                                    <div class="col-md-6">
                                        <div class="card h-100 search-result-card" onclick="enterModule('${module.id}')" style="cursor: pointer;">
                                            <div class="card-body">
                                                <div class="d-flex align-items-start">
                                                    <div class="module-icon me-3" style="width: 40px; height: 40px; background: linear-gradient(135deg, ${module.iconColor}, ${adjustColor(module.iconColor, -30)}); display: flex; align-items: center; justify-content: center; border-radius: 8px;">
                                                        <i class="bi ${module.icon}" style="color: white; font-size: 1.2rem;"></i>
                                                    </div>
                                                    <div class="flex-grow-1">
                                                        <h6 class="card-title mb-1">${module.title}</h6>
                                                        <p class="text-muted small mb-2">${module.description}</p>
                                                        <span class="badge bg-light text-dark">功能模块</span>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                `;
                            }).filter(Boolean).join('')}
                        </div>
                    </div>
                `;
            }
            
            if (results.customers && results.customers.length > 0) {
                resultsHTML += `
                    <div class="search-category mb-4">
                        <h6 class="category-title mb-3">
                            <i class="bi bi-building me-2"></i>客户 (${results.customers.length})
                        </h6>
                        <div class="list-group">
                            ${results.customers.map(item => `
                                <a href="${item.url || '#'}" class="list-group-item list-group-item-action search-result-item">
                                    <div class="d-flex align-items-start">
                                        <div class="me-3">
                                            <i class="bi ${item.icon || 'bi-building'}" style="color: ${item.iconColor || '#4a9cff'}; font-size: 1.5rem;"></i>
                                        </div>
                                        <div class="flex-grow-1">
                                            <h6 class="mb-1">${item.title}</h6>
                                            <p class="text-muted small mb-0">${item.description || ''}</p>
                                        </div>
                                        <div>
                                            <span class="badge bg-light text-dark">${item.category || '客户'}</span>
                                        </div>
                                    </div>
                                </a>
                            `).join('')}
                        </div>
                    </div>
                `;
            }
            
            if (results.contracts && results.contracts.length > 0) {
                resultsHTML += `
                    <div class="search-category mb-4">
                        <h6 class="category-title mb-3">
                            <i class="bi bi-file-earmark-text me-2"></i>合同 (${results.contracts.length})
                        </h6>
                        <div class="list-group">
                            ${results.contracts.map(item => `
                                <a href="${item.url || '#'}" class="list-group-item list-group-item-action search-result-item">
                                    <div class="d-flex align-items-start">
                                        <div class="me-3">
                                            <i class="bi ${item.icon || 'bi-file-earmark-text'}" style="color: ${item.iconColor || '#28a745'}; font-size: 1.5rem;"></i>
                                        </div>
                                        <div class="flex-grow-1">
                                            <h6 class="mb-1">${item.title}</h6>
                                            <p class="text-muted small mb-0">${item.description || ''}</p>
                                        </div>
                                        <div>
                                            <span class="badge bg-light text-dark">${item.category || '合同'}</span>
                                        </div>
                                    </div>
                                </a>
                            `).join('')}
                        </div>
                    </div>
                `;
            }
            
            if ((!results.modules || results.modules.length === 0) && 
                (!results.customers || results.customers.length === 0) && 
                (!results.contracts || results.contracts.length === 0)) {
                resultsHTML += `
                    <div class="text-center py-5">
                        <i class="bi bi-search" style="font-size: 3rem; color: var(--gray-400);"></i>
                        <p class="text-muted mt-3">未找到相关结果</p>
                    </div>
                `;
            }
            
            resultsHTML += `
                                </div>
                            </div>
                            <div class="modal-footer">
                                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">关闭</button>
                            </div>
                        </div>
                    </div>
                </div>
            `;
            
            // 移除现有的模态框
            const existingModal = document.getElementById('searchResultsModal');
            if (existingModal) existingModal.remove();
            
            // 添加新的模态框
            document.body.insertAdjacentHTML('beforeend', resultsHTML);
            
            // 显示模态框
            const modal = new bootstrap.Modal(document.getElementById('searchResultsModal'));
            modal.show();
            
            // 清空搜索框
            const searchInput = document.getElementById('global-search');
            if (searchInput) {
                searchInput.value = '';
            }
        }
        
        // 初始化进度条动画
        function initializeProgressBars() {
            document.querySelectorAll('.progress-bar').forEach(bar => {
                const width = bar.style.width;
                bar.style.width = '0';
                setTimeout(() => {
                    bar.style.width = width;
                }, 100);
            });
        }
        
        // 添加键盘快捷键
        document.addEventListener('keydown', function(e) {
            // Ctrl/Cmd + K 聚焦搜索框
            if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
                e.preventDefault();
                const searchInput = document.getElementById('global-search');
                if (searchInput) {
                    searchInput.focus();
                    searchInput.select();
                }
            }
            
            // Esc 取消搜索
            if (e.key === 'Escape') {
                const searchInput = document.getElementById('global-search');
                if (searchInput && searchInput === document.activeElement) {
                    searchInput.value = '';
                    searchInput.blur();
                }
            }
            
            // F5 刷新
            if (e.key === 'F5') {
                e.preventDefault();
                // 触发刷新按钮点击
                const refreshBtn = document.getElementById('refreshDataBtn');
                if (refreshBtn) {
                    refreshBtn.click();
                } else {
                    // 如果没有刷新按钮，直接刷新数据
                    Promise.all([
                        loadDashboardStats(),
                        loadDashboardTodos(),
                        loadWeeklyProjects(),
                        loadApprovalMessages(),
                        loadModuleStats()
                    ]).then(() => {
                        showToast('数据已刷新', 'success');
                    });
                }
            }
        });
    
    // 将 allModules 暴露到全局作用域，供其他脚本使用
    window.allModules = allModules;
})();