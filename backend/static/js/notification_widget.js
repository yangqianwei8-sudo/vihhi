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
            // 如果是navbar容器，查找右侧区域（最后一个navbar-nav，或者没有me-auto类的）
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
                // 如果navRight是ul元素，需要将通知组件包装在li中
                if (navRight.tagName === 'UL') {
                    const li = document.createElement('li');
                    li.className = 'nav-item';
                    li.appendChild(notificationWidget);
                    navRight.appendChild(li);
                } else {
                    navRight.appendChild(notificationWidget);
                }
            } else {
                // 创建右侧容器
                const rightContainer = document.createElement('ul');
                rightContainer.className = 'navbar-nav ms-auto';
                rightContainer.style.display = 'flex';
                rightContainer.style.alignItems = 'center';
                // 将通知组件包装在li中
                const li = document.createElement('li');
                li.className = 'nav-item';
                li.appendChild(notificationWidget);
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
        const dropdown = document.getElementById('notificationDropdown');
        const badge = document.getElementById('notificationBadge');
        const list = document.getElementById('notificationList');
        const closeBtn = document.getElementById('closeNotificationDropdown');
        
        console.log('初始化通知功能，查找元素:', {
            iconWrapper: !!iconWrapper,
            dropdown: !!dropdown,
            badge: !!badge,
            list: !!list,
            closeBtn: !!closeBtn
        });
        
        if (!iconWrapper || !dropdown || !badge || !list) {
            console.error('通知组件：无法找到必要的DOM元素', {
                iconWrapper: !!iconWrapper,
                dropdown: !!dropdown,
                badge: !!badge,
                list: !!list
            });
            return;
        }
        
        console.log('通知组件元素已找到，开始绑定事件');
        
        let isOpen = false;
        let notifications = [];
        let lastToggleTime = 0; // 防抖：记录上次切换时间
        const TOGGLE_DEBOUNCE_MS = 100; // 防抖时间：100毫秒内只允许切换一次
        
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
            const now = Date.now();
            // 防抖：如果距离上次切换时间太短，忽略此次调用
            if (now - lastToggleTime < TOGGLE_DEBOUNCE_MS) {
                return;
            }
            lastToggleTime = now;
            
            console.log('toggleDropdown 被调用，当前状态:', isOpen);
            isOpen = !isOpen;
            console.log('切换后状态:', isOpen);
            console.log('dropdown 元素:', dropdown);
            if (dropdown) {
                if (isOpen) {
                    dropdown.style.display = 'flex';
                    dropdown.classList.add('show');
                } else {
                    dropdown.style.display = 'none';
                    dropdown.classList.remove('show');
                }
                console.log('下拉菜单显示状态:', dropdown.style.display, 'class:', dropdown.className);
            } else {
                console.error('dropdown 元素不存在！');
            }
            
            if (isOpen) {
                loadNotifications();
            }
        }
        
        // 关闭下拉菜单
        function closeDropdown() {
            isOpen = false;
            if (dropdown) {
                dropdown.style.display = 'none';
                dropdown.classList.remove('show');
            }
        }
        
        // 绑定事件 - 使用多种方式确保事件能触发
        function handleIconClick(e) {
            console.log('通知图标点击事件触发', e);
            // 不要阻止默认行为，只阻止冒泡到document
            e.stopPropagation();
            // 不调用 preventDefault，避免阻止正常的点击行为
            console.log('通知图标被点击，准备切换下拉菜单');
            try {
                toggleDropdown();
            } catch (error) {
                console.error('调用toggleDropdown时出错:', error);
            }
        }
        
        // 只使用 click 事件，避免多个事件重复触发
        iconWrapper.addEventListener('click', function(e) {
            e.stopPropagation(); // 阻止事件冒泡到document，防止立即关闭
            e.preventDefault(); // 阻止默认行为
            handleIconClick(e);
        }, false);
        
        if (closeBtn) {
            closeBtn.addEventListener('click', function(e) {
                e.stopPropagation();
                closeDropdown();
            });
        }
        
        // 点击外部关闭 - 使用延迟确保不会立即关闭刚打开的菜单
        document.addEventListener('click', function(e) {
            // 如果点击的是通知图标或下拉菜单内的元素，不关闭
            if (iconWrapper.contains(e.target) || (dropdown && dropdown.contains(e.target))) {
                return;
            }
            // 如果菜单是打开的，关闭它
            if (isOpen) {
                // 延迟关闭，避免与打开事件冲突
                setTimeout(function() {
                    if (isOpen && !iconWrapper.contains(e.target) && (!dropdown || !dropdown.contains(e.target))) {
                        closeDropdown();
                    }
                }, 10);
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
                z-index: 1051;
            }
            
            .notification-icon-wrapper {
                position: relative;
                cursor: pointer;
                padding: 8px 12px;
                border-radius: 4px;
                transition: background-color 0.2s;
                z-index: 1052;
                pointer-events: auto !important;
                user-select: none;
                -webkit-user-select: none;
                -moz-user-select: none;
                -ms-user-select: none;
            }
            
            .notification-icon-wrapper:hover {
                background-color: rgba(255, 255, 255, 0.1);
            }
            
            /* 移除子元素的 pointer-events: none，允许事件冒泡 */
            .notification-icon-wrapper * {
                pointer-events: auto;
                cursor: pointer;
            }
            
            .notification-icon {
                font-size: 20px;
                display: inline-block;
                pointer-events: auto;
                cursor: pointer;
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
                z-index: 1053 !important;
                margin-top: 8px;
                display: none;
                flex-direction: column;
            }
            
            .notification-dropdown.show {
                display: flex !important;
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



