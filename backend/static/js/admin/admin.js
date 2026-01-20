/**
 * Admin 后台管理系统 - 主JavaScript文件
 */

(function() {
    'use strict';
    
    // ========== URL清理：清除admin/#中的空hash ==========
    /**
     * 清理URL中的空hash（如 admin/# 变为 admin/）
     */
    function cleanAdminHash() {
        // 检查是否是admin路径
        if (window.location.pathname.startsWith('/admin/')) {
            // 如果hash为空或只有#，清除它
            if (window.location.hash === '' || window.location.hash === '#') {
                // 使用replace而不是assign，避免在历史记录中留下记录
                const cleanUrl = window.location.pathname + window.location.search;
                if (window.location.href !== cleanUrl) {
                    window.history.replaceState(null, '', cleanUrl);
                }
            }
        }
    }
    
    // 立即执行一次清理
    cleanAdminHash();
    
    // 监听hashchange事件，如果hash变为空，立即清理
    window.addEventListener('hashchange', function() {
        cleanAdminHash();
    });
    
    // ========== Vue应用保护 ==========
    // 确保Vue应用不会干扰Django Admin页面
    
    // 检查当前路径是否为Admin页面（排除登录页面）
    const isAdminPath = window.location.pathname.startsWith('/admin/') && 
                       !window.location.pathname.includes('/admin/login') &&
                       !window.location.pathname.includes('/admin/logout');
    
    if (isAdminPath) {
        // 如果是Admin页面，立即阻止Vue应用挂载
        
        // 阻止Vue应用的JS文件加载
        const originalCreateElement = document.createElement;
        document.createElement = function(tagName) {
            const element = originalCreateElement.call(document, tagName);
            if (tagName.toLowerCase() === 'script' && element.setAttribute) {
                const originalSetAttribute = element.setAttribute;
                element.setAttribute = function(name, value) {
                    // 阻止加载Vue应用的JS文件
                    if (name === 'src' && value && (
                        value.includes('app.js') || 
                        value.includes('chunk-vendors') ||
                        value.includes('/js/app.') ||
                        value.includes('/static/js/app.')
                    )) {
                        return; // 不设置src属性，阻止加载
                    }
                    return originalSetAttribute.call(this, name, value);
                };
            }
            return element;
        };
        
        // 移除已加载的Vue应用JS文件
        function removeVueScripts() {
            const scripts = document.querySelectorAll('script[src]');
            scripts.forEach(function(script) {
                const src = script.getAttribute('src') || '';
                if (src.includes('app.js') || 
                    src.includes('chunk-vendors') ||
                    src.includes('/js/app.') ||
                    src.includes('/static/js/app.')) {
                    script.remove();
                }
            });
        }
        
        // 移除#app元素（如果存在）
        const removeAppElement = function() {
            const appElement = document.getElementById('app');
            if (appElement) {
                appElement.remove();
            }
        };
        
        // 立即执行
        removeAppElement();
        removeVueScripts();
        
        // 监听DOM变化，确保#app元素和Vue JS文件不会被添加
        if (typeof MutationObserver !== 'undefined') {
            const observer = new MutationObserver(function(mutations) {
                mutations.forEach(function(mutation) {
                    mutation.addedNodes.forEach(function(node) {
                        if (node.nodeType === 1) { // Element node
                            // 检查是否是script标签
                            if (node.tagName === 'SCRIPT' && node.src) {
                                const src = node.src || node.getAttribute('src') || '';
                                if (src.includes('app.js') || 
                                    src.includes('chunk-vendors') ||
                                    src.includes('/js/app.') ||
                                    src.includes('/static/js/app.')) {
                                    node.remove();
                                }
                            }
                            // 检查是否是#app元素
                            if (node.id === 'app') {
                                node.remove();
                            } else if (node.querySelector && node.querySelector('#app')) {
                                const appEl = node.querySelector('#app');
                                if (appEl) {
                                    appEl.remove();
                                }
                            }
                        }
                    });
                });
            });
            
            // 开始观察document的变化
            observer.observe(document.documentElement, {
                childList: true,
                subtree: true
            });
        }
        
        // 阻止Vue应用挂载（如果Vue应用已经加载）
        if (window.Vue && window.Vue.mount) {
            try {
                const originalMount = window.Vue.mount;
                window.Vue.mount = function() {
                    return null;
                };
            } catch (e) {
                // 静默处理错误
            }
        }
        
        // 监听Vue应用加载（使用try-catch避免属性已定义的错误）
        try {
            // 先检查Vue属性是否已存在且可配置
            const vueDescriptor = Object.getOwnPropertyDescriptor(window, 'Vue');
            if (vueDescriptor && !vueDescriptor.configurable) {
                // 如果Vue属性不可配置，直接覆盖mount方法
                if (window.Vue && window.Vue.mount) {
                    window.Vue.mount = function() {
                        return null;
                    };
                }
            } else {
                // 如果Vue属性不存在或可配置，使用defineProperty
                Object.defineProperty(window, 'Vue', {
                    set: function(value) {
                        if (value && value.mount) {
                            try {
                                const originalMount = value.mount;
                                value.mount = function() {
                                    return null;
                                };
                            } catch (e) {
                                // 静默处理错误
                            }
                        }
                        window._Vue = value;
                    },
                    get: function() {
                        return window._Vue;
                    },
                    configurable: true,
                    enumerable: true
                });
            }
        } catch (e) {
            // 备用方案：直接覆盖window.Vue
            const originalVue = window.Vue;
            window.Vue = function() {
                return {};
            };
            if (originalVue) {
                window.Vue.mount = function() {
                    return null;
                };
            }
        }
        
        // 定期检查并移除
        setInterval(function() {
            removeAppElement();
            removeVueScripts();
        }, 1000);
        
        
        // 监听内容区域的变化
        if (typeof MutationObserver !== 'undefined') {
            const contentObserver = new MutationObserver(function(mutations) {
                mutations.forEach(function(mutation) {
                    if (mutation.removedNodes.length > 0) {
                        mutation.removedNodes.forEach(function(node) {
                            if (node.nodeType === 1) {
                                const id = node.id || '';
                                const className = node.className || '';
                                if (id.includes('content') || className.includes('changelist') || className.includes('results')) {
                                    // 内容区域被移除，静默处理
                                }
                            }
                        });
                    }
                });
            });
            
            const contentMain = document.getElementById('content-main');
            const content = document.getElementById('content');
            if (contentMain) {
                contentObserver.observe(contentMain, {
                    childList: true,
                    subtree: true
                });
            }
            if (content) {
                contentObserver.observe(content, {
                    childList: true,
                    subtree: true
                });
            }
        }
    }
    
    // ========== 原有功能 ==========

    // ========== 工具函数 ==========
    
    /**
     * 查找侧边栏元素
     */
    function findSidebarElement() {
        // 检查是否是客户管理首页
        const isCustomerManagementPage = document.getElementById('customer-management-app-index') || 
                                         document.querySelector('.customer-management-layout');
        
        // 如果是客户管理首页，查找客户管理的侧边栏
        if (isCustomerManagementPage) {
            const customerSidebar = document.querySelector('.customer-sidebar');
            if (customerSidebar) {
                return customerSidebar;
            }
        }
        
        // 查找Django Admin的侧边栏（dashboard-sidebar）
        let sidebar = document.querySelector('.dashboard-sidebar');
        if (sidebar) {
            return sidebar;
        }
        
        // 否则查找默认的侧边栏
        sidebar = document.getElementById('nav-sidebar');
        if (!sidebar) {
            sidebar = document.querySelector('#nav-sidebar');
        }
        if (!sidebar) {
            sidebar = document.querySelector('div[class*="sidebar"]:not(.customer-sidebar)');
        }
        if (!sidebar) {
            sidebar = document.querySelector('#content-related');
        }
        if (!sidebar) {
            const elements = document.querySelectorAll('div');
            for (let el of elements) {
                if (el.textContent && el.textContent.includes('系统管理后台')) {
                    sidebar = el.closest('div[style*="position"], div[style*="fixed"]') || el;
                    break;
                }
            }
        }
        return sidebar;
    }

    /**
     * 动态插入强制样式
     */
    function injectForceStyle() {
        const styleId = 'force-nav-sidebar-left';
        if (document.getElementById(styleId)) return;
        
        const style = document.createElement('style');
        style.id = styleId;
        style.innerHTML = `
            html, html body, body {
                margin-left: 0 !important;
                padding-left: 0 !important;
            }
            #container {
                margin-left: 0 !important;
                padding-left: 0 !important;
            }
            #nav-sidebar,
            div#nav-sidebar,
            [id="nav-sidebar"] {
                position: fixed !important;
                left: 0 !important;
                width: 130px !important;
                margin-left: 0 !important;
                padding-left: 0 !important;
                margin: 0 !important;
                padding: 0 !important;
                transform: translateX(0) !important;
                box-sizing: border-box !important;
            }
            #content {
                margin-left: 130px !important;
            }
        `;
        document.head.appendChild(style);
    }

    // ========== 强制左侧导航栏对齐 ==========
    
    /**
     * 强制左侧导航栏贴边对齐
     */
    /**
     * 强制左侧导航栏贴边 - 功能已禁用
     */
    function forceSidebarLeftAlign() {
        // 功能已禁用，不再执行任何操作
        return false;
    }

    // ========== 一级菜单切换 ==========
    
    /**
     * 根据菜单路径生成URL
     * 优先从后端配置中获取，如果没有则使用默认映射
     */
    function getMenuUrl(menuPath) {
        // 清理菜单路径：去除首尾空格和换行符
        if (menuPath) {
            menuPath = menuPath.trim().replace(/\s+/g, ' ');
        }
        
        // 尝试从后端配置中获取（如果后端有提供）
        if (window.ADMIN_MENU_URL_MAPPING && window.ADMIN_MENU_URL_MAPPING[menuPath]) {
            return window.ADMIN_MENU_URL_MAPPING[menuPath];
        }
        
        // 备用：菜单路径到URL的映射（与后端保持一致）
        const menuUrlMap = {
            '首页': '/admin/',
            '客户管理': '/admin/customer_management/',
            '合同管理': '/admin/production_management/businesscontract/',
            '商机管理': '/admin/customer_success/',
            '生产管理': '/admin/production_management/',
            '结算管理': '/admin/settlement_center/',
            '收文管理': '/admin/delivery_customer/incomingdocument/',
            '发文管理': '/admin/delivery_customer/outgoingdocument/',
            '档案管理': '/admin/archive_management/',
            '财务管理': '/admin/financial_management/',
            '人事管理': '/admin/personnel_management/',
            '行政管理': '/admin/administrative_management/',
            '计划管理': '/admin/plan_management/',
            '诉讼管理': '/admin/litigation_management/',
            '风险管理': '/admin/risk_management/',
            '资源管理': '/admin/resource_standard/',
            '报表管理': '/admin/report_management/',
            '系统设置': '/admin/system_management/',
            '权限设置': '/admin/permission_management/',
            '流程设置': '/admin/workflow_engine/',
            'API管理': '/admin/api_management/',
            '团队管理': '/admin/auth/',
        };
        
        // 精确匹配
        if (menuUrlMap[menuPath]) {
            return menuUrlMap[menuPath];
        }
        
        // 模糊匹配：如果包含菜单名称
        for (const key in menuUrlMap) {
            if (menuPath && menuPath.indexOf(key) !== -1) {
                return menuUrlMap[key];
            }
        }
        
        return '#';
    }
    
    /**
     * 初始化一级菜单
     */
    function initPrimaryMenu() {
        // ========== Admin 页面早退 ==========
        // 如果是 admin 页面，不初始化业务菜单，避免与 Django admin 混合
        // 注意：admin.js 本身是 admin 专用脚本，但 initPrimaryMenu 不应该在 admin 页面初始化业务菜单
        // 这里检查是否在 admin 路径，如果是则跳过业务菜单初始化
        if (window.location.pathname.startsWith('/admin/')) {
            // admin 页面只初始化 admin 自己的菜单，不初始化业务菜单
            return;
        }
        // ========== Admin 页面早退结束 ==========
        
        // 直接查找所有包含菜单文本的链接元素
        const allLinks = document.querySelectorAll('a');
        const menuLabels = ['首页', '客户管理', '合同管理', '商机管理', '生产管理', '结算管理', '收文管理', '发文管理', '档案管理', '财务管理', '人事管理', '行政管理', '计划管理', '诉讼管理', '风险管理', '资源管理', '报表管理', '系统设置', '权限设置', '流程设置', 'API管理', '团队管理'];
        
        const menuItems = Array.from(allLinks).filter(function(link) {
            const text = (link.textContent || link.innerText || '').trim();
            // 精确匹配或包含匹配
            return menuLabels.some(function(label) {
                return text === label || text.indexOf(label) !== -1;
            });
        });
        
        menuItems.forEach(function(item) {
            // 如果菜单项没有 href 属性，尝试生成一个
            if (!item.getAttribute('href') || item.getAttribute('href') === '#') {
                // 尝试从 data-menu 属性获取菜单路径
                let menuPath = item.getAttribute('data-menu');
                if (!menuPath) {
                    // 如果没有data-menu，尝试从文本内容获取
                    const textContent = item.textContent || item.innerText || '';
                    menuPath = textContent.trim().replace(/\s+/g, ' ');
                }
                const url = getMenuUrl(menuPath);
                if (url && url !== '#') {
                    item.setAttribute('href', url);
                }
            }
            
            item.addEventListener('click', function(e) {
                e.preventDefault(); // 始终阻止默认行为，使用JavaScript控制跳转
                
                const itemText = (this.textContent || this.innerText || '').trim();
                
                // 检查是否是链接元素且有有效的 href
                let href = this.getAttribute('href');
                const originalHref = href;
                
                // 如果 href 是 "#" 或空,尝试生成URL
                if (!href || href === '#') {
                    const menuPath = this.getAttribute('data-menu') || itemText;
                    href = getMenuUrl(menuPath);
                    if (href && href !== '#') {
                        this.setAttribute('href', href);
                    }
                }
                
                // 如果有有效的 href 且不是 "#" 或空,进行跳转
                if (href && href !== '#' && href !== '') {
                    // 移除所有激活状态
                    menuItems.forEach(function(mi) {
                        mi.classList.remove('active');
                    });
                    
                    // 添加当前激活状态
                    this.classList.add('active');
                    
                    // 强制使用window.location.href跳转，确保跳转成功
                    window.location.href = href;
                    return false;
                } else {
                    // 如果没有有效链接,阻止默认行为但不跳转
                    // 移除所有激活状态
                    menuItems.forEach(function(mi) {
                        mi.classList.remove('active');
                    });
                    
                    // 添加当前激活状态
                    this.classList.add('active');
                }
            });
        });
    }

    // ========== 全屏切换 ==========
    
    /**
     * 初始化全屏切换
     */
    function initFullscreenToggle() {
        const fullscreenBtn = document.getElementById('toggle-fullscreen');
        if (!fullscreenBtn) return;
        
        fullscreenBtn.addEventListener('click', function(e) {
            e.preventDefault();
            
            if (!document.fullscreenElement) {
                document.documentElement.requestFullscreen().catch(function(err) {
                    console.error('无法进入全屏模式:', err);
                });
            } else {
                document.exitFullscreen();
            }
        });
    }

    // ========== 更新用户名 ==========
    
    /**
     * 更新顶部用户名显示
     */
    function updateTopUserName() {
        const userNameElement = document.getElementById('admin-user-name');
        if (!userNameElement) return;
        
        // 这里可以从后端获取用户名
        // 暂时使用默认值
        const userName = userNameElement.textContent.trim() || '管理员';
        userNameElement.querySelector('span').textContent = userName;
    }

    // ========== 添加用户信息到侧边栏 ==========
    
    /**
     * 在侧边栏添加用户信息 - 功能已禁用
     */
    function addUserInfoToSidebar() {
        // 功能已禁用，不再添加用户信息到侧边栏
        return;
    }

    // ========== 等待侧边栏元素出现 ==========
    
    /**
     * 等待侧边栏元素出现
     */
    function waitForSidebar(callback, maxAttempts) {
        maxAttempts = maxAttempts || 50;
        let attempts = 0;
        
        const checkInterval = setInterval(function() {
            attempts++;
            const sidebar = findSidebarElement();
            if (sidebar) {
                clearInterval(checkInterval);
                // 调试日志已移除
                if (callback) callback();
            } else if (attempts >= maxAttempts) {
                clearInterval(checkInterval);
                // 降低日志级别，避免控制台噪音（侧边栏可能不存在于某些页面）
                // console.warn('等待侧边栏元素超时，已尝试 ' + maxAttempts + ' 次');
            }
        }, 100);
    }

    // ========== 修复Django菜单筛选功能 ==========
    
    /**
     * 修复Django内置的菜单筛选功能，使其能够覆盖CSS的!important规则
     */
    function fixMenuFilter() {
        // 等待Django的nav_sidebar.js加载完成
        if (typeof window.initSidebarQuickFilter === 'undefined') {
            // 如果Django的筛选功能还没加载，延迟重试
            setTimeout(fixMenuFilter, 100);
            return;
        }
        
        // 保存原始的initSidebarQuickFilter函数
        const originalInit = window.initSidebarQuickFilter;
        
        // 重写筛选功能
        window.initSidebarQuickFilter = function() {
            const options = [];
            const navSidebar = document.getElementById('nav-sidebar');
            if (!navSidebar) {
                return;
            }
            
            // 查找所有菜单项（包括主菜单和子菜单）
            navSidebar.querySelectorAll('th[scope=row] a, #nav-sidebar a').forEach((container) => {
                const text = container.textContent.trim() || container.innerText.trim();
                if (text) {
                    options.push({
                        title: text,
                        node: container,
                        module: container.closest('.module')
                    });
                }
            });
            
            function checkValue(event) {
                let filterValue = event.target.value;
                if (filterValue) {
                    filterValue = filterValue.toLowerCase().trim();
                }
                if (event.key === 'Escape') {
                    filterValue = '';
                    event.target.value = '';
                }
                
                let matches = false;
                const matchedModules = new Set();
                
                // 遍历所有菜单项
                for (const o of options) {
                    const row = o.node.closest('tr') || o.node.closest('.module') || o.node.parentElement;
                    const module = o.module || o.node.closest('.module');
                    
                    if (filterValue) {
                        // 检查是否匹配
                        if (o.title.toLowerCase().indexOf(filterValue) !== -1) {
                            matches = true;
                            // 显示匹配的菜单项
                            if (row) {
                                row.style.setProperty('display', '', 'important');
                            }
                            // 展开包含匹配项的模块
                            if (module) {
                                module.style.setProperty('display', '', 'important');
                                module.classList.add('expanded');
                                updateToggleIcon(module, true);
                                matchedModules.add(module);
                            }
                        } else {
                            // 隐藏不匹配的菜单项（但保留模块容器）
                            if (row && !row.closest('th[scope=row]')) {
                                row.style.setProperty('display', 'none', 'important');
                            }
                        }
                    } else {
                        // 清空搜索时，恢复默认显示
                        if (row) {
                            row.style.removeProperty('display');
                        }
                        // 恢复模块状态
                        if (module) {
                            module.style.removeProperty('display');
                            // 根据保存的状态恢复展开/折叠
                            const header = module.querySelector('th[scope=row]');
                            if (header) {
                                const menuLabel = header.textContent.trim() || header.querySelector('a')?.textContent.trim() || '';
                                if (menuLabel) {
                                    const savedState = localStorage.getItem('admin_menu_' + menuLabel);
                                    if (savedState !== 'expanded') {
                                        module.classList.remove('expanded');
                                        updateToggleIcon(module, false);
                                    }
                                }
                            }
                        }
                    }
                }
                
                // 隐藏没有匹配项的模块
                if (filterValue) {
                    navSidebar.querySelectorAll('.module').forEach(function(module) {
                        if (!matchedModules.has(module)) {
                            const hasMatch = Array.from(module.querySelectorAll('a')).some(function(link) {
                                const text = (link.textContent || link.innerText || '').toLowerCase();
                                return text.indexOf(filterValue) !== -1;
                            });
                            if (!hasMatch) {
                                module.style.setProperty('display', 'none', 'important');
                            }
                        }
                    });
                }
                
                // 处理无结果状态
                if (!filterValue || matches) {
                    event.target.classList.remove('no-results');
                } else {
                    event.target.classList.add('no-results');
                }
                
                sessionStorage.setItem('django.admin.navSidebarFilterValue', filterValue);
            }
            
            const nav = document.getElementById('nav-filter');
            if (nav) {
                // 添加占位符提示
                if (!nav.getAttribute('placeholder')) {
                    nav.setAttribute('placeholder', '搜索菜单...');
                }
                
                nav.addEventListener('change', checkValue, false);
                nav.addEventListener('input', checkValue, false);
                nav.addEventListener('keyup', checkValue, false);
                
                // 添加清除按钮功能（双击清除）
                nav.addEventListener('dblclick', function() {
                    this.value = '';
                    checkValue({target: this, key: ''});
                    this.focus();
                });
                
                const storedValue = sessionStorage.getItem('django.admin.navSidebarFilterValue');
                if (storedValue) {
                    nav.value = storedValue;
                    checkValue({target: nav, key: ''});
                }
            }
        };
        
        // 调用修复后的函数
        window.initSidebarQuickFilter();
    }
    
    // ========== 菜单展开/折叠功能 ==========
    
    /**
     * 创建折叠/展开图标
     */
    function createToggleIcon() {
        const icon = document.createElement('span');
        icon.className = 'menu-toggle-icon';
        icon.innerHTML = '▶';
        icon.style.cssText = 'margin-left: auto; font-size: 10px; color: #9CA3AF; transition: transform 0.3s ease; cursor: pointer; user-select: none;';
        return icon;
    }
    
    /**
     * 初始化菜单展开/折叠功能
     * 只允许点击标题文字展开，禁止hover自动展开
     */
    function initMenuToggle() {
        const menuItems = document.querySelectorAll('.sidebar-menu-item.has-children, .module');
        
        menuItems.forEach(function(item) {
            // 查找菜单头部（可能是th[scope=row]或.menu-item-header）
            const header = item.querySelector('th[scope=row]') || item.querySelector('.menu-item-header') || item.querySelector('caption');
            if (!header) return;
            
            const link = header.querySelector('a');
            if (!link) return;
            
            // 检查是否有子菜单
            const hasSubmenu = item.querySelector('ul') || item.querySelector('tbody tr:not(:first-child)');
            if (!hasSubmenu) return;
            
            // 强制设置：只有expanded类才显示子菜单，禁止hover展开
            item.classList.remove('expanded');
            
            // 阻止所有hover事件导致的展开（包括Django默认行为）
            item.addEventListener('mouseenter', function(e) {
                // 阻止任何hover导致的展开
                e.stopPropagation();
                // 确保不会因为hover而展开
                if (!item.classList.contains('expanded')) {
                    // 强制隐藏子菜单
                    const submenu = item.querySelector('ul');
                    if (submenu) {
                        submenu.style.display = 'none';
                        submenu.style.maxHeight = '0';
                        submenu.style.opacity = '0';
                    }
                }
            }, true);
            
            // 添加折叠/展开图标（如果不存在）
            let toggleIcon = header.querySelector('.menu-toggle-icon');
            if (!toggleIcon) {
                toggleIcon = createToggleIcon();
                // 将图标插入到链接内部
                if (link) {
                    link.appendChild(toggleIcon);
                } else {
                    header.appendChild(toggleIcon);
                }
            }
            
            // 为标题链接添加点击事件 - 点击标题文字才展开
            link.addEventListener('click', function(e) {
                // 如果点击的是图标，不处理（由图标的事件处理）
                if (e.target.closest('.menu-toggle-icon')) {
                    return;
                }
                
                // 点击标题文字：切换展开状态，并阻止默认跳转
                e.preventDefault();
                e.stopPropagation();
                
                toggleMenu(item, header);
            });
            
            // 为图标单独添加点击事件
            if (toggleIcon) {
                toggleIcon.addEventListener('click', function(e) {
                    e.preventDefault();
                    e.stopPropagation();
                    toggleMenu(item, header);
                });
            }
            
            // 恢复保存的状态
            const menuLabel = header.textContent.trim() || link.textContent.trim() || '';
            if (menuLabel) {
                const savedState = localStorage.getItem('admin_menu_' + menuLabel);
                if (savedState === 'expanded') {
                    item.classList.add('expanded');
                    updateToggleIcon(item, true);
                } else {
                    item.classList.remove('expanded');
                    updateToggleIcon(item, false);
                }
            } else {
                item.classList.remove('expanded');
                updateToggleIcon(item, false);
            }
        });
        
        // 高亮当前页面对应的菜单项
        highlightActiveMenu();
    }
    
    /**
     * 切换菜单展开/折叠状态
     */
    function toggleMenu(item, header) {
        const isExpanded = item.classList.contains('expanded');
        
        if (isExpanded) {
            item.classList.remove('expanded');
        } else {
            item.classList.add('expanded');
        }
        
        updateToggleIcon(item, !isExpanded);
        
        // 保存状态到localStorage
        const menuLabel = header.textContent.trim() || header.querySelector('a')?.textContent.trim() || '';
        if (menuLabel) {
            localStorage.setItem('admin_menu_' + menuLabel, !isExpanded ? 'expanded' : 'collapsed');
        }
    }
    
    /**
     * 更新折叠/展开图标状态
     */
    function updateToggleIcon(item, isExpanded) {
        const icon = item.querySelector('.menu-toggle-icon');
        if (icon) {
            if (isExpanded) {
                icon.style.transform = 'rotate(90deg)';
                icon.style.color = '#17a2b8';
            } else {
                icon.style.transform = 'rotate(0deg)';
                icon.style.color = '#9CA3AF';
            }
        }
    }
    
    /**
     * 高亮当前页面对应的菜单项，并隐藏其他菜单
     */
    function highlightActiveMenu() {
        const currentPath = window.location.pathname;
        
        // 获取所有菜单项
        const allMenuItems = document.querySelectorAll('.sidebar-menu-item.has-children, .module');
        const menuItemsArray = Array.from(allMenuItems);
        
        // 清除所有激活状态
        document.querySelectorAll('#nav-sidebar a').forEach(function(link) {
            link.classList.remove('active', 'selected');
        });
        
        // 找到当前激活的菜单项
        let activeMenuItem = null;
        let activeMenuLabel = null;
        
        // 方法1: 通过子菜单项找到父菜单
        const submenuItems = document.querySelectorAll('.submenu-item, #nav-sidebar ul a, #nav-sidebar .module ul a');
        submenuItems.forEach(function(item) {
            const href = item.getAttribute('href');
            if (href && (currentPath === href || currentPath.startsWith(href + '/') || href === currentPath)) {
                item.classList.add('active', 'selected');
                // 找到父菜单
                const parentMenu = item.closest('.sidebar-menu-item.has-children, .module');
                if (parentMenu) {
                    activeMenuItem = parentMenu;
                    parentMenu.classList.add('expanded');
                    updateToggleIcon(parentMenu, true);
                }
            }
        });
        
        // 方法2: 根据当前路径匹配主菜单项
        if (!activeMenuItem) {
            const appMatch = currentPath.match(/^\/admin\/([^/]+)\/?/);
            if (appMatch) {
                const appLabel = appMatch[1];
                menuItemsArray.forEach(function(item) {
                    const header = item.querySelector('th[scope=row]') || item.querySelector('.menu-item-header') || item.querySelector('caption');
                    if (header) {
                        const link = header.querySelector('a');
                        if (link) {
                            const linkHref = link.getAttribute('href') || link.href;
                            if (linkHref && (linkHref.includes('/admin/' + appLabel + '/') || linkHref.includes('/admin/' + appLabel))) {
                                activeMenuItem = item;
                                activeMenuLabel = header.textContent.trim() || link.textContent.trim();
                                item.classList.add('expanded');
                                link.classList.add('active', 'selected');
                                updateToggleIcon(item, true);
                            }
                        }
                    }
                });
            }
        }
        
        // 方法3: 精确匹配所有链接
        if (!activeMenuItem) {
            document.querySelectorAll('#nav-sidebar a').forEach(function(link) {
                const href = link.getAttribute('href') || link.href;
                if (href && (currentPath === href || currentPath.startsWith(href + '/'))) {
                    link.classList.add('active', 'selected');
                    const parentMenu = link.closest('.sidebar-menu-item.has-children, .module');
                    if (parentMenu) {
                        activeMenuItem = parentMenu;
                        parentMenu.classList.add('expanded');
                        updateToggleIcon(parentMenu, true);
                    }
                }
            });
        }
        
        // 如果当前路径是首页，显示所有菜单
        const isHomePage = currentPath === '/admin/' || currentPath === '/admin';
        
        // 隐藏其他菜单项（除了首页和当前激活的菜单）
        menuItemsArray.forEach(function(item) {
            const header = item.querySelector('th[scope=row]') || item.querySelector('.menu-item-header') || item.querySelector('caption');
            if (!header) return;
            
            const link = header.querySelector('a');
            const menuText = header.textContent.trim() || (link ? link.textContent.trim() : '');
            
            // 判断是否是首页菜单
            const isHomeMenu = menuText === '首页' || 
                              (link && (link.href.includes('/admin/') && (link.href.endsWith('/admin/') || link.href === window.location.origin + '/admin/')));
            
            // 如果是首页，始终显示
            if (isHomeMenu) {
                item.style.display = '';
                return;
            }
            
            // 如果是首页路径，显示所有菜单
            if (isHomePage) {
                item.style.display = '';
                return;
            }
            
            // 如果是当前激活的菜单，显示并展开
            if (item === activeMenuItem) {
                item.style.display = '';
                item.classList.add('expanded');
                updateToggleIcon(item, true);
                return;
            }
            
            // 其他菜单都隐藏
            item.style.display = 'none';
        });
    }

    // ========== 移动端菜单切换 ==========
    
    /**
     * 初始化移动端菜单切换功能
     */
    function initMobileMenuToggle() {
        // 只在移动端启用
        if (window.innerWidth > 768) return;
        
        const sidebar = findSidebarElement();
        if (!sidebar) return;
        
        // 创建遮罩层
        let overlay = document.querySelector('.sidebar-overlay');
        if (!overlay) {
            overlay = document.createElement('div');
            overlay.className = 'sidebar-overlay';
            document.body.appendChild(overlay);
        }
        
        // 点击遮罩层关闭菜单
        overlay.addEventListener('click', function() {
            sidebar.classList.remove('mobile-open');
            overlay.classList.remove('active');
        });
        
        // 监听窗口大小变化
        let resizeTimer;
        window.addEventListener('resize', function() {
            clearTimeout(resizeTimer);
            resizeTimer = setTimeout(function() {
                if (window.innerWidth > 768) {
                    sidebar.classList.remove('mobile-open');
                    overlay.classList.remove('active');
                }
            }, 250);
        });
        
        // 添加菜单切换按钮（如果需要，可以在header中添加）
        // 这里假设有一个菜单按钮，如果没有可以后续添加
    }
    
    // ========== 键盘导航支持 ==========
    
    /**
     * 初始化键盘导航功能
     */
    function initKeyboardNavigation() {
        const sidebar = findSidebarElement();
        if (!sidebar) return;
        
        let currentFocusIndex = -1;
        const focusableItems = [];
        
        function updateFocusableItems() {
            focusableItems.length = 0;
            sidebar.querySelectorAll('a, #nav-filter').forEach(function(item) {
                if (item.offsetParent !== null) { // 只包含可见元素
                    focusableItems.push(item);
                }
            });
        }
        
        sidebar.addEventListener('keydown', function(e) {
            updateFocusableItems();
            
            if (focusableItems.length === 0) return;
            
            // 向下箭头或Tab键
            if (e.key === 'ArrowDown' || (e.key === 'Tab' && !e.shiftKey)) {
                e.preventDefault();
                currentFocusIndex = (currentFocusIndex + 1) % focusableItems.length;
                focusableItems[currentFocusIndex].focus();
            }
            // 向上箭头或Shift+Tab
            else if (e.key === 'ArrowUp' || (e.key === 'Tab' && e.shiftKey)) {
                e.preventDefault();
                currentFocusIndex = currentFocusIndex <= 0 ? focusableItems.length - 1 : currentFocusIndex - 1;
                focusableItems[currentFocusIndex].focus();
            }
            // Enter或Space展开/折叠
            else if ((e.key === 'Enter' || e.key === ' ') && e.target.closest('.module th[scope=row]')) {
                e.preventDefault();
                const module = e.target.closest('.module');
                if (module) {
                    const header = module.querySelector('th[scope=row]');
                    if (header) {
                        toggleMenu(module, header);
                    }
                }
            }
            // Escape关闭移动端菜单
            else if (e.key === 'Escape' && window.innerWidth <= 768) {
                const sidebar = findSidebarElement();
                if (sidebar) {
                    sidebar.classList.remove('mobile-open');
                    const overlay = document.querySelector('.sidebar-overlay');
                    if (overlay) {
                        overlay.classList.remove('active');
                    }
                }
            }
        });
        
        // 当菜单项获得焦点时，滚动到可见区域
        sidebar.addEventListener('focusin', function(e) {
            if (e.target.tagName === 'A' || e.target.id === 'nav-filter') {
                e.target.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
            }
        });
    }
    
    // ========== 初始化所有功能 ==========
    
    let allInitialized = false;
    
    function initAll() {
        if (allInitialized) return;
        allInitialized = true;
        
        // 贴边功能已取消，不再调用
        // forceSidebarLeftAlign();
        
        updateTopUserName();
        addUserInfoToSidebar();
        initFullscreenToggle();
        initPrimaryMenu();
        initMenuToggle(); // 初始化菜单展开/折叠功能
        initMobileMenuToggle(); // 初始化移动端菜单切换
        initKeyboardNavigation(); // 初始化键盘导航
        
        // 修复菜单筛选功能
        setTimeout(fixMenuFilter, 300);
    }

    // ========== 页面加载时初始化 ==========
    
    // 立即执行一次（如果 DOM 已加载）
    if (document.readyState !== 'loading') {
        waitForSidebar(function() {
            // 贴边功能已取消
        });
    }
    
    // DOMContentLoaded 事件
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            waitForSidebar(function() {
                initAll();
            });
        });
    } else {
        waitForSidebar(function() {
            initAll();
        });
    }
    
    // window.onload 事件
    window.addEventListener('load', function() {
        waitForSidebar(function() {
            initAll();
        });
    });
    
    // 多次延迟执行，确保在所有脚本加载后生效
    setTimeout(function() {
        waitForSidebar(function() {
            initAll();
        });
    }, 50);
    
    // 额外延迟执行菜单筛选修复，确保Django的nav_sidebar.js已加载
    setTimeout(function() {
        fixMenuFilter();
    }, 500);
    
    setTimeout(function() {
        fixMenuFilter();
    }, 1000);
    
    // 延迟初始化菜单展开/折叠功能，确保DOM完全加载
    setTimeout(function() {
        initMenuToggle();
        initMobileMenuToggle();
    }, 800);
    
    // 页面跳转后重新隐藏菜单（监听popstate事件）
    window.addEventListener('popstate', function() {
        setTimeout(function() {
            highlightActiveMenu();
        }, 100);
    });
    
    // 监听URL变化（用于SPA或AJAX导航）
    let lastUrl = window.location.href;
    setInterval(function() {
        if (window.location.href !== lastUrl) {
            lastUrl = window.location.href;
            setTimeout(function() {
                highlightActiveMenu();
            }, 100);
        }
    }, 200);
    
    // 监听窗口大小变化，重新初始化移动端菜单
    let resizeTimeout;
    window.addEventListener('resize', function() {
        clearTimeout(resizeTimeout);
        resizeTimeout = setTimeout(function() {
            initMobileMenuToggle();
        }, 250);
    });
    
    // 贴边功能已取消，移除所有延迟调用
    // setTimeout(function() {
    //     waitForSidebar(function() {
    //         forceSidebarLeftAlign();
    //     });
    // }, 100);
    
    // setTimeout(function() {
    //     waitForSidebar(function() {
    //         forceSidebarLeftAlign();
    //     });
    // }, 200);
    
    // setTimeout(function() {
    //     waitForSidebar(function() {
    //         forceSidebarLeftAlign();
    //     });
    // }, 500);
    
    // setTimeout(function() {
    //     waitForSidebar(function() {
    //         forceSidebarLeftAlign();
    //     });
    // }, 1000);
    
    // setTimeout(function() {
    //     waitForSidebar(function() {
    //         forceSidebarLeftAlign();
    //     });
    // }, 2000);
    
    // 监听窗口大小变化 - 贴边功能已取消
    // window.addEventListener('resize', function() {
    //     forceSidebarLeftAlign();
    // });
    
    // MutationObserver 已禁用，因为贴边功能已取消
    // if (typeof MutationObserver !== 'undefined') {
    //     const observer = new MutationObserver(function(mutations) {
    //         forceSidebarLeftAlign();
    //     });
    //     
    //     setTimeout(function() {
    //         const navSidebar = document.getElementById('nav-sidebar');
    //         if (navSidebar) {
    //             observer.observe(navSidebar, {
    //                 attributes: true,
    //                 attributeFilter: ['style', 'class'],
    //                 childList: true,
    //                 subtree: true
    //             });
    //         }
    //     }, 1000);
    // }
})();


