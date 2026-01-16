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
            // 如果找不到导航栏，延迟重试
            setTimeout(initNotificationWidget, 500);
            return;
        }
        
        // 创建通知组件HTML
        const notificationHTML = `
            <div class="notification-dropdown-container">
                <div class="notification-icon-wrapper" id="notificationIcon">
                    <span class="notification-icon">🔔</span>
                    <span class="notification-badge" id="notificationBadge" style="display: none;">0</span>
                </div>
                <div class="notification-dropdown" id="notificationDropdown" style="display: none;">
                    <div class="notification-header">
                        <h6 class="mb-0">系统通知</h6>
                        <button type="button" class="btn-close btn-close-sm" id="closeNotificationDropdown"></button>
                    </div>
                    <div class="notification-list" id="notificationList">
                        <div class="notification-loading">加载中...</div>
                    </div>
                    <div class="notification-footer">
                        <a href="/administrative/announcement/list/" class="btn btn-sm btn-link">查看全部</a>
                    </div>
                </div>
            </div>
        `;
        
        // 创建容器
        const container = document.createElement('div');
        container.innerHTML = notificationHTML;
        const notificationWidget = container.firstElementChild;
        
        // 添加到导航栏右侧
        if (navbar.classList.contains('navbar-nav')) {
            // 如果是nav元素，直接添加
            navbar.appendChild(notificationWidget);
        } else {
            // 如果是navbar容器，查找右侧区域或创建
            const navRight = navbar.querySelector('.navbar-nav') || navbar.querySelector('.nav-right');
            if (navRight) {
                navRight.appendChild(notificationWidget);
            } else {
                // 创建右侧容器
                const rightContainer = document.createElement('div');
                rightContainer.className = 'navbar-nav ms-auto';
                rightContainer.style.display = 'flex';
                rightContainer.style.alignItems = 'center';
                rightContainer.appendChild(notificationWidget);
                navbar.appendChild(rightContainer);
            }
        }
        
        // 初始化通知功能
        initNotificationFunctionality();
    }
    
    // 初始化通知功能
    function initNotificationFunctionality() {
        const iconWrapper = document.getElementById('notificationIcon');
        const dropdown = document.getElementById('notificationDropdown');
        const badge = document.getElementById('notificationBadge');
        const list = document.getElementById('notificationList');
        const closeBtn = document.getElementById('closeNotificationDropdown');
        
        if (!iconWrapper || !dropdown || !badge || !list) {
            return;
        }
        
        let isOpen = false;
        let notifications = [];
        
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
        
        // 切换下拉菜单
        function toggleDropdown() {
            isOpen = !isOpen;
            dropdown.style.display = isOpen ? 'flex' : 'none';
            
            if (isOpen) {
                loadNotifications();
            }
        }
        
        // 关闭下拉菜单
        function closeDropdown() {
            isOpen = false;
            dropdown.style.display = 'none';
        }
        
        // 绑定事件
        iconWrapper.addEventListener('click', function(e) {
            e.stopPropagation();
            toggleDropdown();
        });
        
        if (closeBtn) {
            closeBtn.addEventListener('click', function(e) {
                e.stopPropagation();
                closeDropdown();
            });
        }
        
        // 点击外部关闭
        document.addEventListener('click', function(e) {
            if (isOpen && !dropdown.contains(e.target) && !iconWrapper.contains(e.target)) {
                closeDropdown();
            }
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
            .notification-dropdown-container {
                position: relative;
                margin-left: 15px;
            }
            
            .notification-icon-wrapper {
                position: relative;
                cursor: pointer;
                padding: 8px 12px;
                border-radius: 4px;
                transition: background-color 0.2s;
            }
            
            .notification-icon-wrapper:hover {
                background-color: rgba(255, 255, 255, 0.1);
            }
            
            .notification-icon {
                font-size: 20px;
                display: inline-block;
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
            
            .notification-dropdown {
                position: absolute;
                top: 100%;
                right: 0;
                width: 380px;
                max-height: 500px;
                background: white;
                border: 1px solid #ddd;
                border-radius: 8px;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
                z-index: 1050;
                margin-top: 8px;
                display: flex;
                flex-direction: column;
            }
            
            .notification-header {
                padding: 12px 16px;
                border-bottom: 1px solid #eee;
                display: flex;
                justify-content: space-between;
                align-items: center;
                background-color: #f8f9fa;
                border-radius: 8px 8px 0 0;
            }
            
            .notification-header h6 {
                font-weight: 600;
                color: #333;
                margin: 0;
            }
            
            .notification-list {
                max-height: 400px;
                overflow-y: auto;
                padding: 8px 0;
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

