/**
 * 左侧导航栏交互功能
 * 维海科技信息化管理平台
 * 版本: 3.0
 */

(function() {
    'use strict';

    /**
     * 初始化导航栏交互功能
     */
    function initSidebar() {
        // 处理有子菜单的一级菜单项点击
        // 只选择有子菜单的项（通过检查是否有menu-arrow标记）
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
                        // 可选：展开当前项时，收起其他项（取消注释启用）
                        // document.querySelectorAll('.sidenav-item.expanded').forEach(function(otherItem) {
                        //     if (otherItem !== item) {
                        //         otherItem.classList.remove('expanded');
                        //     }
                        // });
                        item.classList.add('expanded');
                    }
                }
                // 如果没有子菜单，允许默认的链接跳转行为
            });
        });

        // 处理子菜单项点击（允许正常跳转）
        document.querySelectorAll('.sidenav-sub-link').forEach(function(link) {
            link.addEventListener('click', function(e) {
                // 允许默认的链接跳转行为
                // 如果需要在这里添加额外逻辑，可以添加
            });
        });

        // 初始化：展开包含激活项的子菜单
        document.querySelectorAll('.sidenav-item').forEach(function(item) {
            const activeSubLink = item.querySelector('.sidenav-sub-link[data-active="true"]');
            if (activeSubLink) {
                item.classList.add('expanded');
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

