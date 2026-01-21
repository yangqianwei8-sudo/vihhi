/**
 * 系统通知组件
 * 自动添加到顶部导航栏
 */
(function() {
    'use strict';
    
    // 等待DOM加载完成
    function initNotificationWidget() {
        // 查找导航栏
        const navbar = document.querySelector('.navbar') || document.querySelector('nav') || document.querySelector('.navbar-nav');
        if (!navbar) {
            // 如果找不到导航栏，延迟重试（最多重试10次）
            if (typeof initNotificationWidget.retryCount === 'undefined') {
                initNotificationWidget.retryCount = 0;
            }
            initNotificationWidget.retryCount++;
            if (initNotificationWidget.retryCount < 10) {
                setTimeout(initNotificationWidget, 500);
            } else {
                console.warn('通知组件：无法找到导航栏元素');
            }
            return;
        }
        
        // 创建通知图标HTML（只在顶部栏显示图标）
        const notificationIconHTML = `
            <div class="notification-icon-wrapper" id="notificationIcon">
                <span class="notification-icon">🔔</span>
                <span class="notification-badge" id="notificationBadge" style="display: none;">0</span>
            </div>
        `;
        
        // 创建模态框HTML（添加到body，不在顶部栏）
        const notificationModalHTML = `
            <div class="modal fade" id="notificationModal" tabindex="-1" aria-labelledby="notificationModalLabel" aria-hidden="true">
                <div class="modal-dialog modal-dialog-scrollable modal-lg">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title" id="notificationModalLabel">系统通知</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="关闭" id="closeNotificationModal"></button>
                        </div>
                        <div class="modal-body">
                            <div class="notification-list" id="notificationList">
                                <div class="notification-loading">加载中...</div>
                            </div>
                        </div>
                        <div class="modal-footer">
                            <a href="/administrative/announcements/" class="btn btn-link">查看全部通知</a>
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">关闭</button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // 创建图标容器
        const iconContainer = document.createElement('div');
        iconContainer.innerHTML = notificationIconHTML;
        const notificationIcon = iconContainer.firstElementChild;
        
        // 创建模态框容器（添加到body）
        const modalContainer = document.createElement('div');
        modalContainer.innerHTML = notificationModalHTML;
        const notificationModal = modalContainer.firstElementChild;
        
        // 将模态框添加到body
        document.body.appendChild(notificationModal);
        
        // 将图标添加到导航栏右侧
        if (navbar.classList.contains('navbar-nav')) {
            // 如果是nav元素，包装在li中
            const li = document.createElement('li');
            li.className = 'nav-item';
            li.appendChild(notificationIcon);
            navbar.appendChild(li);
        } else {
            // 如果是navbar容器，查找右侧区域
            const allNavs = navbar.querySelectorAll('.navbar-nav');
            let navRight = null;
            
            // 优先查找没有me-auto类的navbar-nav（右侧导航栏）
            for (let nav of allNavs) {
                if (!nav.classList.contains('me-auto')) {
                    navRight = nav;
                    break;
                }
            }
            
            // 如果没找到，使用最后一个navbar-nav
            if (!navRight && allNavs.length > 0) {
                navRight = allNavs[allNavs.length - 1];
            }
            
            // 如果还是没找到，尝试查找.nav-right
            if (!navRight) {
                navRight = navbar.querySelector('.nav-right');
            }
            
            if (navRight) {
                // 如果navRight是ul元素，需要将通知图标包装在li中
                if (navRight.tagName === 'UL') {
                    const li = document.createElement('li');
                    li.className = 'nav-item';
                    li.appendChild(notificationIcon);
                    navRight.appendChild(li);
                } else {
                    navRight.appendChild(notificationIcon);
                }
            } else {
                // 创建右侧容器
                const rightContainer = document.createElement('ul');
                rightContainer.className = 'navbar-nav ms-auto';
                rightContainer.style.display = 'flex';
                rightContainer.style.alignItems = 'center';
                // 将通知图标包装在li中
                const li = document.createElement('li');
                li.className = 'nav-item';
                li.appendChild(notificationIcon);
                rightContainer.appendChild(li);
                // 查找navbar-collapse容器
                const navbarCollapse = navbar.querySelector('.navbar-collapse') || navbar;
                navbarCollapse.appendChild(rightContainer);
            }
        }
        
        // 初始化通知功能
        // 延迟一下确保DOM完全渲染
        setTimeout(function() {
            initNotificationFunctionality();
        }, 100);
    }
    
    // 初始化通知功能
    function initNotificationFunctionality() {
        const iconWrapper = document.getElementById('notificationIcon');
        const modal = document.getElementById('notificationModal');
        const badge = document.getElementById('notificationBadge');
        const list = document.getElementById('notificationList');
        const closeBtn = document.getElementById('closeNotificationModal');
        
        console.log('初始化通知功能，查找元素:', {
            iconWrapper: !!iconWrapper,
            modal: !!modal,
            badge: !!badge,
            list: !!list,
            closeBtn: !!closeBtn
        });
        
        if (!iconWrapper || !modal || !badge || !list) {
            console.error('通知组件：无法找到必要的DOM元素', {
                iconWrapper: !!iconWrapper,
                modal: !!modal,
                badge: !!badge,
                list: !!list
            });
            return;
        }
        
        console.log('通知组件元素已找到，开始绑定事件');
        
        let notifications = [];
        
        // 使用Bootstrap Modal API
        let modalInstance = null;
        try {
            if (typeof bootstrap !== 'undefined' && bootstrap.Modal) {
                modalInstance = new bootstrap.Modal(modal);
            }
        } catch (e) {
            console.warn('Bootstrap Modal 不可用，将使用手动方式', e);
        }
        
        // 导出 lastToggleTime 到外部作用域，供点击外部关闭事件使用
        // （通过闭包，点击外部关闭事件可以访问这个变量）
        
        // 加载通知
        function loadNotifications() {
            fetch('/api/notifications/', {
                method: 'GET',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                },
                credentials: 'same-origin',
            })
            .then(response => response.json())
            .then(data => {
                notifications = data.notifications || [];
                updateBadge(data.unread_count || 0);
                renderNotifications();
            })
            .catch(error => {
                console.error('加载通知失败:', error);
                list.innerHTML = '<div class="notification-empty">加载失败，请刷新页面重试</div>';
            });
        }
        
        // 更新徽章
        function updateBadge(count) {
            if (count > 0) {
                badge.textContent = count > 99 ? '99+' : count;
                badge.style.display = 'inline-block';
            } else {
                badge.style.display = 'none';
            }
        }
        
        // 渲染通知列表
        function renderNotifications() {
            if (notifications.length === 0) {
                list.innerHTML = '<div class="notification-empty">暂无通知</div>';
                return;
            }
            
            const html = notifications.map(notif => {
                const unreadClass = notif.is_read ? '' : 'unread';
                const priorityClass = `priority-${notif.priority || 'normal'}`;
                const timeStr = formatTime(notif.created_time);
                
                return `
                    <div class="notification-item ${unreadClass} ${priorityClass}" 
                         data-id="${notif.id}" 
                         data-url="${notif.url || '#'}">
                        <div class="notification-icon-item">${notif.icon || '📢'}</div>
                        <div class="notification-content">
                            <div class="notification-title">${escapeHtml(notif.title)}</div>
                            <div class="notification-text">${escapeHtml(notif.content)}</div>
                            <div class="notification-time">${timeStr}</div>
                        </div>
                    </div>
                `;
            }).join('');
            
            list.innerHTML = html;
            
            // 绑定点击事件
            list.querySelectorAll('.notification-item').forEach(item => {
                item.addEventListener('click', function() {
                    const notifId = this.dataset.id;
                    const url = this.dataset.url;
                    
                    // 标记为已读
                    if (!notifications.find(n => n.id === notifId)?.is_read) {
                        markAsRead(notifId);
                    }
                    
                    // 跳转
                    if (url && url !== '#') {
                        window.location.href = url;
                    }
                });
            });
        }
        
        // 标记为已读
        function markAsRead(notificationId) {
            const formData = new FormData();
            formData.append('notification_id', notificationId);
            
            fetch('/api/notifications/mark-read/', {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                },
                credentials: 'same-origin',
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // 更新本地状态
                    const notif = notifications.find(n => n.id === notificationId);
                    if (notif) {
                        notif.is_read = true;
                    }
                    // 重新渲染
                    renderNotifications();
                    // 更新徽章
                    const unreadCount = notifications.filter(n => !n.is_read).length;
                    updateBadge(unreadCount);
                }
            })
            .catch(error => {
                console.error('标记已读失败:', error);
            });
        }
        
        // 格式化时间
        function formatTime(timeStr) {
            if (!timeStr) return '';
            
            const time = new Date(timeStr);
            const now = new Date();
            const diff = now - time;
            
            const minutes = Math.floor(diff / 60000);
            const hours = Math.floor(diff / 3600000);
            const days = Math.floor(diff / 86400000);
            
            if (minutes < 1) return '刚刚';
            if (minutes < 60) return `${minutes}分钟前`;
            if (hours < 24) return `${hours}小时前`;
            if (days < 7) return `${days}天前`;
            
            return time.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' });
        }
        
        // HTML转义
        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }
        
        // 打开模态框
        function openModal() {
            console.log('打开通知模态框');
            // 先加载通知
            loadNotifications();
            
            // 使用Bootstrap Modal API或手动方式打开
            if (modalInstance) {
                modalInstance.show();
            } else {
                // 手动方式
                modal.classList.add('show');
                modal.style.display = 'block';
                modal.setAttribute('aria-hidden', 'false');
                document.body.classList.add('modal-open');
                // 添加背景遮罩
                const backdrop = document.createElement('div');
                backdrop.className = 'modal-backdrop fade show';
                backdrop.id = 'notificationModalBackdrop';
                document.body.appendChild(backdrop);
            }
        }
        
        // 关闭模态框
        function closeModal() {
            console.log('关闭通知模态框');
            
            // 在关闭之前，先移除焦点，避免 aria-hidden 警告
            const activeElement = document.activeElement;
            if (activeElement && modal.contains(activeElement)) {
                // 如果焦点在模态框内，将焦点移到 body
                activeElement.blur();
                document.body.focus();
            }
            
            if (modalInstance) {
                modalInstance.hide();
            } else {
                // 手动方式：先移除焦点，再设置 aria-hidden
                setTimeout(() => {
                    modal.classList.remove('show');
                    modal.style.display = 'none';
                    modal.setAttribute('aria-hidden', 'true');
                    document.body.classList.remove('modal-open');
                    // 移除背景遮罩
                    const backdrop = document.getElementById('notificationModalBackdrop');
                    if (backdrop) {
                        backdrop.remove();
                    }
                }, 0);
            }
        }
        
        // 绑定图标点击事件
        iconWrapper.addEventListener('click', function(e) {
            console.log('通知图标被点击');
            e.stopPropagation();
            e.preventDefault();
            openModal();
        });
        
        // 绑定关闭按钮事件
        if (closeBtn) {
            closeBtn.addEventListener('click', function(e) {
                e.stopPropagation();
                closeModal();
            });
        }
        
        // 监听模态框关闭事件
        modal.addEventListener('hidden.bs.modal', function() {
            console.log('模态框已关闭');
        });
        
        // 页面加载时加载通知
        loadNotifications();
        
        // 定期刷新通知（每5分钟）
        setInterval(loadNotifications, 5 * 60 * 1000);
    }
    
    // 添加样式
    function addNotificationStyles() {
        if (document.getElementById('notification-widget-styles')) {
            return;
        }
        
        const style = document.createElement('style');
        style.id = 'notification-widget-styles';
        style.textContent = `
            .notification-icon-wrapper {
                position: relative;
                cursor: pointer;
                padding: 8px 12px;
                border-radius: 4px;
                transition: background-color 0.2s;
                pointer-events: auto !important;
                user-select: none;
                -webkit-user-select: none;
                -moz-user-select: none;
                -ms-user-select: none;
                touch-action: manipulation;
            }
            
            .notification-icon-wrapper:hover {
                background-color: rgba(255, 255, 255, 0.1);
            }
            
            .notification-icon-wrapper * {
                pointer-events: auto !important;
                cursor: pointer !important;
            }
            
            .notification-icon {
                font-size: 20px;
                display: inline-block;
                pointer-events: auto !important;
                cursor: pointer !important;
            }
            
            .notification-badge {
                position: absolute;
                top: 4px;
                right: 4px;
                background-color: #dc3545;
                color: white;
                border-radius: 10px;
                padding: 2px 6px;
                font-size: 11px;
                font-weight: bold;
                min-width: 18px;
                text-align: center;
                line-height: 1.4;
            }
            
            .notification-list {
                max-height: 60vh;
                overflow-y: auto;
                padding: 0;
            }
            
            .notification-item {
                padding: 12px 16px;
                border-bottom: 1px solid #f0f0f0;
                cursor: pointer;
                transition: background-color 0.2s;
                display: flex;
                align-items: flex-start;
                gap: 12px;
            }
            
            .notification-item:hover {
                background-color: #f8f9fa;
            }
            
            .notification-item.unread {
                background-color: #f0f7ff;
                border-left: 3px solid #0d6efd;
            }
            
            .notification-item.unread:hover {
                background-color: #e6f2ff;
            }
            
            .notification-icon-item {
                font-size: 24px;
                flex-shrink: 0;
            }
            
            .notification-content {
                flex: 1;
                min-width: 0;
            }
            
            .notification-title {
                font-weight: 600;
                color: #333;
                margin-bottom: 4px;
                font-size: 14px;
            }
            
            .notification-text {
                color: #666;
                font-size: 13px;
                line-height: 1.4;
                margin-bottom: 4px;
                overflow: hidden;
                text-overflow: ellipsis;
                display: -webkit-box;
                -webkit-line-clamp: 2;
                -webkit-box-orient: vertical;
            }
            
            .notification-time {
                color: #999;
                font-size: 12px;
            }
            
            .notification-empty {
                padding: 40px 20px;
                text-align: center;
                color: #999;
            }
            
            .notification-loading {
                padding: 40px 20px;
                text-align: center;
                color: #999;
            }
            
            .notification-footer {
                padding: 12px 16px;
                border-top: 1px solid #eee;
                text-align: center;
                background-color: #f8f9fa;
                border-radius: 0 0 8px 8px;
            }
            
            .notification-footer .btn-link {
                padding: 0;
                font-size: 13px;
                color: #0d6efd;
                text-decoration: none;
            }
            
            .notification-footer .btn-link:hover {
                text-decoration: underline;
            }
            
            .notification-item.priority-urgent {
                border-left-color: #dc3545;
            }
            
            .notification-item.priority-important {
                border-left-color: #ffc107;
            }
            
            .notification-item.priority-normal {
                border-left-color: #0d6efd;
            }
        `;
        
        document.head.appendChild(style);
    }
    
    // 初始化
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            addNotificationStyles();
            initNotificationWidget();
        });
    } else {
        addNotificationStyles();
        initNotificationWidget();
    }
})();



