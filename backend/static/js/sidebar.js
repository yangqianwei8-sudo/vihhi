/**
 * 左侧导航栏交互功能
 * 维海科技信息化管理平台
 * 版本: 3.0
 */

(function() {
    'use strict';

    /**
     * 获取菜单项的唯一标识
     */
    function getMenuItemId(item) {
        const link = item.querySelector('.sidenav-link');
        if (link) {
            return link.getAttribute('href') || link.textContent.trim();
        }
        return null;
    }

    /**
     * 保存菜单项展开状态
     */
    function saveMenuItemState(itemId, isExpanded) {
        try {
            const key = 'sidebarMenuItem_' + itemId;
            localStorage.setItem(key, isExpanded ? 'expanded' : 'collapsed');
        } catch (e) {
            // localStorage可能不可用，忽略错误
            console.warn('无法保存菜单项状态:', e);
        }
    }

    /**
     * 恢复菜单项展开状态
     */
    function restoreMenuItemState(item) {
        const itemId = getMenuItemId(item);
        if (!itemId) return;

        try {
            const key = 'sidebarMenuItem_' + itemId;
            const savedState = localStorage.getItem(key);
            if (savedState === 'expanded') {
                item.classList.add('expanded');
            } else if (savedState === 'collapsed') {
                item.classList.remove('expanded');
            }
        } catch (e) {
            // localStorage可能不可用，忽略错误
        }
    }

    /**
     * 全部展开/折叠所有菜单项（排除首页菜单项和激活的菜单项）
     */
    function toggleAllMenuItems() {
        // 只选择有子菜单的菜单项，排除第一个菜单项（通常是首页）
        const allItems = Array.from(document.querySelectorAll('.sidenav-item.has-children'));
        if (allItems.length === 0) return;
        
        // 排除第一个菜单项（首页）和激活的菜单项（需要保持展开）
        const itemsToToggle = allItems.filter(function(item, index) {
            // 排除第一个菜单项
            if (index === 0) return false;
            // 排除激活的菜单项（需要保持展开状态）
            if (item.classList.contains('active')) return false;
            return true;
        });
        
        if (itemsToToggle.length === 0) return;
        
        // 检查这些菜单项的展开状态
        let allExpanded = true;
        let allCollapsed = true;
        
        itemsToToggle.forEach(function(item) {
            if (item.classList.contains('expanded')) {
                allCollapsed = false;
            } else {
                allExpanded = false;
            }
        });
        
        // 如果全部展开，则全部折叠；否则全部展开
        const shouldExpand = !allExpanded;
        
        itemsToToggle.forEach(function(item) {
            const itemId = getMenuItemId(item);
            const submenu = item.querySelector('.submenu');
            if (!submenu) return;
            
            if (shouldExpand) {
                item.classList.add('expanded');
                submenu.removeAttribute('style'); // 移除内联样式，让CSS规则生效
                if (itemId) saveMenuItemState(itemId, true);
            } else {
                item.classList.remove('expanded');
                submenu.removeAttribute('style'); // 移除内联样式，让CSS规则生效
                if (itemId) saveMenuItemState(itemId, false);
            }
        });
    }

    /**
     * 初始化导航栏交互功能
     */
    function initSidebar() {
        // 处理第一个菜单项（通常是首页）的特殊点击：全部展开/折叠
        // 适用于所有左侧栏的首页菜单项（如：商机管理首页、财务管理首页、档案管理首页等）
        const firstMenuItem = document.querySelector('.sidenav-item:first-child');
        if (firstMenuItem) {
            const firstLink = firstMenuItem.querySelector('.sidenav-link');
            if (firstLink) {
                firstLink.addEventListener('click', function(e) {
                    // 检查是否有子菜单
                    const item = this.closest('.sidenav-item');
                    const submenu = item ? item.querySelector('.submenu') : null;
                    const hasSubmenu = submenu && submenu.children.length > 0;
                    
                    // 如果没有子菜单，执行全部展开/折叠功能
                    if (!hasSubmenu) {
                        e.preventDefault();
                        e.stopPropagation();
                        toggleAllMenuItems();
                    }
                });
            }
        }

        // 处理有子菜单的一级菜单项点击
        // 使用事件委托，处理所有 .sidenav-item 内的链接点击
        // 优化：使用防抖处理，避免快速点击时的性能问题
        let clickTimeout = null;
        const workspaceNav = document.querySelector('.workspace-nav');
        if (workspaceNav) {
            workspaceNav.addEventListener('click', function(e) {
                // 检查点击的是否是一级菜单链接（不是二级菜单链接）
                const link = e.target.closest('.sidenav-link');
                if (!link) return; // 不是链接，不处理
                
                // 如果是二级菜单链接，不处理（允许正常跳转）
                if (link.classList.contains('sidenav-sub-link')) {
                    // 确保子菜单链接可以正常跳转，不阻止事件
                    return;
                }
                
                // 如果是第一个菜单项（首页），且没有子菜单，已经在上面处理了，这里跳过
                const item = link.closest('.sidenav-item');
                if (!item) return;
                
                const isFirstItem = item === item.parentElement.querySelector('.sidenav-item:first-child');
                const submenu = item.querySelector('.submenu');
                if (isFirstItem && !submenu) {
                    return; // 第一个菜单项且没有子菜单，已经在上面处理了
                }
                
                // 检查是否有子菜单
                if (!submenu) return; // 没有子菜单，允许默认跳转
                
                const hasSubmenu = submenu.children.length > 0;
                if (!hasSubmenu) return; // 子菜单为空，允许默认跳转
                
                // 有子菜单，阻止默认跳转并展开/折叠
                e.preventDefault();
                e.stopPropagation();
                
                // 防抖处理：避免快速连续点击
                if (clickTimeout) {
                    clearTimeout(clickTimeout);
                }
                
                clickTimeout = setTimeout(function() {
                    const isExpanded = item.classList.contains('expanded');
                    const itemId = getMenuItemId(item);
                    
                    // 添加过渡动画类
                    item.classList.add('transitioning');
                    
                    if (isExpanded) {
                        item.classList.remove('expanded');
                        // 移除内联样式，让 CSS 规则生效
                        submenu.removeAttribute('style');
                        if (itemId) saveMenuItemState(itemId, false);
                    } else {
                        item.classList.add('expanded');
                        // 移除内联样式，让 CSS 规则生效
                        submenu.removeAttribute('style');
                        if (itemId) saveMenuItemState(itemId, true);
                    }
                    
                    // 移除过渡动画类
                    setTimeout(function() {
                        item.classList.remove('transitioning');
                    }, 300);
                }, 50); // 50ms 防抖延迟
            });
        }

        // 处理子菜单项点击（允许正常跳转）
        // 优化：使用事件委托，避免为每个链接单独绑定事件
        const workspaceNavForSubLinks = document.querySelector('.workspace-nav');
        if (workspaceNavForSubLinks) {
            workspaceNavForSubLinks.addEventListener('click', function(e) {
                const subLink = e.target.closest('.sidenav-sub-link');
                if (subLink) {
                    // 添加点击反馈
                    subLink.style.transform = 'translateX(1px)';
                    setTimeout(function() {
                        subLink.style.transform = '';
                    }, 150);
                }
            });
        }

        // 初始化：展开包含激活项的子菜单，并恢复保存的状态
        // 优化：使用 requestAnimationFrame 提升性能
        const initMenuItems = function() {
            const items = document.querySelectorAll('.sidenav-item');
            if (items.length === 0) return;
            
            items.forEach(function(item, index) {
                // 使用 requestAnimationFrame 分批处理，避免阻塞主线程
                requestAnimationFrame(function() {
                    // 确保第一个菜单项（首页）始终显示
                    const isFirstItem = index === 0;
                    if (isFirstItem) {
                        item.style.display = 'flex';
                        item.style.visibility = 'visible';
                        item.style.opacity = '1';
                    }
                    
                    // 检查模板中是否已经设置了expanded类（通过menu_group.expanded）
                    const hasExpandedClass = item.classList.contains('expanded');
                    
                    // 检查是否有激活的二级菜单项
                    const activeSubLink = item.querySelector('.sidenav-sub-link[data-active="true"]');
                    
                    // 检查是否有激活的一级菜单项（有data-active属性）
                    const activeLink = item.querySelector('.sidenav-link[data-active="true"]');
                    const isActiveItem = item.classList.contains('active');
                    
                    // 检查子菜单
                    const submenu = item.querySelector('.submenu');
                    
                    if (submenu) {
                        // 移除可能存在的内联样式，让CSS规则生效
                        submenu.removeAttribute('style');
                    }
                    
                    // 优先级：激活项 > 模板设置的expanded类 > 保存的状态
                    if (activeSubLink || (isActiveItem && submenu)) {
                        // 如果有激活的子菜单项或激活的父菜单项有子菜单，优先展开
                        item.classList.add('expanded');
                        if (submenu) {
                            submenu.removeAttribute('style'); // 确保CSS规则生效
                        }
                    } else if (hasExpandedClass) {
                        // 如果模板中已经设置了expanded类，保持展开状态
                        // 不需要额外操作，CSS规则会自动处理
                        if (submenu) {
                            submenu.removeAttribute('style'); // 确保CSS规则生效
                        }
                    } else {
                        // 否则恢复保存的状态（仅当不是激活项时）
                        if (!isActiveItem && !activeLink) {
                            restoreMenuItemState(item);
                        }
                    }
                });
            });
        };
        
        initMenuItems();
    }

    /**
     * 切换导航栏折叠/展开状态
     */
    function toggleSidebarCollapse() {
        const workspaceNav = document.querySelector('.workspace-nav');
        if (workspaceNav) {
            workspaceNav.classList.toggle('collapsed');
            // 可选：保存折叠状态到 localStorage
            const isCollapsed = workspaceNav.classList.contains('collapsed');
            localStorage.setItem('sidebarCollapsed', isCollapsed ? 'true' : 'false');
        }
    }

    /**
     * 恢复导航栏折叠状态（从 localStorage）
     */
    function restoreSidebarState() {
        const workspaceNav = document.querySelector('.workspace-nav');
        if (workspaceNav) {
            const savedState = localStorage.getItem('sidebarCollapsed');
            if (savedState === 'true') {
                workspaceNav.classList.add('collapsed');
            }
        }
    }

    // 页面加载完成后初始化
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            initSidebar();
            restoreSidebarState();
        });
    } else {
        initSidebar();
        restoreSidebarState();
    }

    // 导出全局函数（如果需要外部调用）
    window.toggleSidebarCollapse = toggleSidebarCollapse;
})();

