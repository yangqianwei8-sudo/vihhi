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
        // 处理有子菜单的一级菜单项点击 - vh-sb__parent 结构
        document.querySelectorAll('.vh-sb__parent > .vh-sb__item--parent').forEach(function(link) {
            // 检查链接的 href 是否为 # 或空，如果是则临时修改为 javascript:void(0)
            const originalHref = link.getAttribute('href');
            if (originalHref === '#' || originalHref === '#!' || !originalHref) {
                link.setAttribute('href', 'javascript:void(0)');
            }
            
            link.addEventListener('click', function(e) {
                const parent = this.closest('.vh-sb__parent');
                const children = parent ? parent.querySelector('.vh-sb__children') : null;
                
                // 更精确的检查：如果点击发生在子菜单容器内，不处理父菜单的折叠逻辑
                // 这防止了点击子菜单项时触发父菜单折叠的问题
                if (children && (children.contains(e.target) || e.target.closest('.vh-sb__child'))) {
                    return; // 允许子菜单项正常跳转，不处理父菜单折叠
                }
                
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

    // 页面加载完成后初始化
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            initSidebar();
        });
    } else {
        initSidebar();
    }
})();

