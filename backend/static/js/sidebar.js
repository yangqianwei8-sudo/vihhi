/**
 * 左侧导航栏交互功能
 * 维海科技信息化管理平台
 * 版本: 3.0
 */

(function() {
    'use strict';

    // ========== Admin 页面早退 ==========
    // 如果是 admin 页面，不初始化业务侧边栏，避免与 Django admin 混合
    if (window.location.pathname.startsWith('/admin/')) {
        return; // 关键：admin 页面不初始化业务菜单
    }
    // ========== Admin 页面早退结束 ==========

    /**
     * 初始化导航栏交互功能
     */
    function initSidebar() {
        // 处理有子菜单的一级菜单项点击 - 支持两种结构
        // 1. sidenav-item 结构（旧结构）
        document.querySelectorAll('.sidenav-item > .sidenav-link').forEach(function(link) {
            link.addEventListener('click', function(e) {
                const item = this.closest('.sidenav-item');
                const submenu = item.querySelector('.submenu');
                
                // 检查是否有子菜单：1) 存在submenu元素 2) submenu有子元素 3) 链接中有menu-arrow标记
                const hasSubmenu = submenu && submenu.children.length > 0;
                const hasArrow = this.querySelector('.menu-arrow') !== null;
                
                // 只有当确实有子菜单时才阻止默认跳转
                if (hasSubmenu && hasArrow) {
                    e.preventDefault();
                    e.stopPropagation();
                    
                    const isExpanded = item.classList.contains('expanded');
                    if (isExpanded) {
                        item.classList.remove('expanded');
                    } else {
                        item.classList.add('expanded');
                    }
                }
                // 如果没有子菜单，允许默认的链接跳转行为
            });
        });

        // 2. vh-sb__parent 结构（新结构）
        document.querySelectorAll('.vh-sb__parent > .vh-sb__item--parent').forEach(function(link) {
            // 检查链接的 href 是否为 # 或空，如果是则临时修改为 javascript:void(0)
            const originalHref = link.getAttribute('href');
            if (originalHref === '#' || originalHref === '#!' || !originalHref) {
                link.setAttribute('href', 'javascript:void(0)');
            }
            
            link.addEventListener('click', function(e) {
                const parent = this.closest('.vh-sb__parent');
                const children = parent.querySelector('.vh-sb__children');
                
                // 检查是否有子菜单
                const hasSubmenu = children && children.children.length > 0;
                
                // 只有当确实有子菜单时才阻止默认跳转
                if (hasSubmenu) {
                    e.preventDefault();
                    e.stopPropagation();
                    e.stopImmediatePropagation();
                    
                    const isOpen = parent.classList.contains('is-open');
                    if (isOpen) {
                        parent.classList.remove('is-open');
                    } else {
                        // 可选：展开当前项时，收起其他项（取消注释启用）
                        // document.querySelectorAll('.vh-sb__parent.is-open').forEach(function(otherParent) {
                        //     if (otherParent !== parent) {
                        //         otherParent.classList.remove('is-open');
                        //     }
                        // });
                        parent.classList.add('is-open');
                    }
                    
                    return false;
                }
                // 如果没有子菜单，允许默认的链接跳转行为
            }, true); // 使用捕获阶段，确保在其他事件处理器之前执行
        });

        // 处理子菜单项点击（允许正常跳转）
        document.querySelectorAll('.sidenav-sub-link').forEach(function(link) {
            link.addEventListener('click', function(e) {
                // 允许默认的链接跳转行为
            });
        });

        // 初始化：展开包含激活项的子菜单 - sidenav-item 结构
        document.querySelectorAll('.sidenav-item').forEach(function(item) {
            const activeSubLink = item.querySelector('.sidenav-sub-link[data-active="true"]');
            if (activeSubLink) {
                item.classList.add('expanded');
            }
        });

        // 初始化：展开包含激活项的子菜单 - vh-sb__parent 结构
        document.querySelectorAll('.vh-sb__parent').forEach(function(parent) {
            const activeChild = parent.querySelector('.vh-sb__child.is-active');
            // 检查是否有激活的子菜单项，或者后端传递了 expanded 属性
            const shouldExpand = activeChild || parent.hasAttribute('data-expanded') && parent.getAttribute('data-expanded') === 'true';
            if (shouldExpand) {
                parent.classList.add('is-open');
            }
        });
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

