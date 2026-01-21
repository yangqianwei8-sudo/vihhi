/**
 * 通知中心诊断脚本
 * 在浏览器控制台中运行此脚本，检查通知中心为什么打不开
 * 使用方法：在控制台中输入 notificationDiagnostic() 或直接运行此脚本
 */

(function() {
    'use strict';
    
    function notificationDiagnostic() {
        console.log('========================================');
        console.log('通知中心诊断报告');
        console.log('========================================\n');
        
        const issues = [];
        const warnings = [];
        const info = [];
        
        // 1. 检查脚本是否加载
        console.log('【1. 脚本加载检查】');
        const notificationScript = Array.from(document.querySelectorAll('script')).find(
            script => script.src && script.src.includes('notification_widget.js')
        );
        if (notificationScript) {
            console.log('  ✓ 通知组件脚本已加载');
            console.log('  - 脚本路径:', notificationScript.src);
            info.push('通知组件脚本已加载');
        } else {
            console.log('  ✗ 未找到通知组件脚本');
            issues.push('未找到 notification_widget.js 脚本');
        }
        console.log('');
        
        // 2. 检查样式是否加载
        console.log('【2. 样式检查】');
        const notificationStyles = document.getElementById('notification-widget-styles');
        if (notificationStyles) {
            console.log('  ✓ 通知组件样式已加载');
            info.push('通知组件样式已加载');
        } else {
            console.log('  ✗ 未找到通知组件样式');
            issues.push('未找到 notification-widget-styles 样式');
        }
        console.log('');
        
        // 3. 检查导航栏
        console.log('【3. 导航栏检查】');
        const navbar = document.querySelector('.navbar') || document.querySelector('nav') || document.querySelector('.navbar-nav');
        let navbarInfo = null;
        if (navbar) {
            const navbarRect = navbar.getBoundingClientRect();
            const navbarStyle = window.getComputedStyle(navbar);
            console.log('  ✓ 找到导航栏');
            console.log('  - 元素标签:', navbar.tagName);
            console.log('  - 元素类名:', navbar.className);
            console.log('  - 位置:', navbarRect);
            console.log('  - z-index:', navbarStyle.zIndex);
            console.log('  - pointer-events:', navbarStyle.pointerEvents);
            navbarInfo = {
                element: navbar,
                rect: navbarRect,
                style: navbarStyle,
                zIndex: navbarStyle.zIndex
            };
            info.push('找到导航栏');
        } else {
            console.log('  ✗ 未找到导航栏');
            issues.push('未找到导航栏元素 (.navbar, nav, .navbar-nav)');
        }
        console.log('');
        
        // 4. 检查通知容器
        console.log('【4. 通知容器检查】');
        const notificationContainer = document.querySelector('.notification-dropdown-container');
        if (notificationContainer) {
            const containerRect = notificationContainer.getBoundingClientRect();
            const containerStyle = window.getComputedStyle(notificationContainer);
            console.log('  ✓ 找到通知容器');
            console.log('  - 位置:', containerRect);
            console.log('  - z-index:', containerStyle.zIndex);
            console.log('  - pointer-events:', containerStyle.pointerEvents);
            console.log('  - display:', containerStyle.display);
            console.log('  - position:', containerStyle.position);
            console.log('  - visibility:', containerStyle.visibility);
            console.log('  - opacity:', containerStyle.opacity);
            
            // 检查父元素
            if (notificationContainer.parentElement) {
                const parent = notificationContainer.parentElement;
                const parentStyle = window.getComputedStyle(parent);
                console.log('  - 父元素:', parent.tagName, parent.className);
                console.log('  - 父元素 pointer-events:', parentStyle.pointerEvents);
                console.log('  - 父元素 display:', parentStyle.display);
                
                if (parentStyle.pointerEvents === 'none') {
                    warnings.push('通知容器的父元素设置了 pointer-events: none');
                }
            }
            
            info.push('找到通知容器');
        } else {
            console.log('  ✗ 未找到通知容器');
            issues.push('未找到 .notification-dropdown-container 元素');
        }
        console.log('');
        
        // 5. 检查通知图标包装器
        console.log('【5. 通知图标检查】');
        const iconWrapper = document.getElementById('notificationIcon');
        if (iconWrapper) {
            const iconRect = iconWrapper.getBoundingClientRect();
            const iconStyle = window.getComputedStyle(iconWrapper);
            console.log('  ✓ 找到通知图标');
            console.log('  - 位置:', iconRect);
            console.log('  - z-index:', iconStyle.zIndex);
            console.log('  - pointer-events:', iconStyle.pointerEvents);
            console.log('  - cursor:', iconStyle.cursor);
            console.log('  - display:', iconStyle.display);
            console.log('  - visibility:', iconStyle.visibility);
            console.log('  - opacity:', iconStyle.opacity);
            console.log('  - user-select:', iconStyle.userSelect);
            
            // 检查是否被遮挡
            if (iconRect.width === 0 || iconRect.height === 0) {
                issues.push('通知图标尺寸为0，可能被隐藏');
            }
            
            // 检查 pointer-events
            if (iconStyle.pointerEvents !== 'auto') {
                warnings.push('通知图标的 pointer-events 不是 auto: ' + iconStyle.pointerEvents);
            }
            
            // 检查子元素
            const icon = iconWrapper.querySelector('.notification-icon');
            if (icon) {
                const iconIconStyle = window.getComputedStyle(icon);
                console.log('  - 图标子元素 pointer-events:', iconIconStyle.pointerEvents);
                if (iconIconStyle.pointerEvents !== 'auto') {
                    warnings.push('图标子元素的 pointer-events 不是 auto');
                }
            }
            
            // 检查是否有事件监听器
            // getEventListeners 是 Chrome DevTools 的内部函数，只在控制台中可用
            if (typeof getEventListeners !== 'undefined') {
                try {
                    const listeners = getEventListeners(iconWrapper);
                    if (listeners) {
                        console.log('  - 绑定的事件监听器:', Object.keys(listeners));
                        if (listeners.click && listeners.click.length > 0) {
                            console.log('  - click 事件监听器数量:', listeners.click.length);
                            info.push('找到 ' + listeners.click.length + ' 个 click 事件监听器');
                        } else {
                            issues.push('通知图标没有绑定 click 事件监听器');
                        }
                    }
                } catch (error) {
                    console.log('  ⚠ 无法检测事件监听器:', error.message);
                    warnings.push('无法检测事件监听器: ' + error.message);
                }
            } else {
                console.log('  ℹ getEventListeners 不可用（这是 Chrome DevTools 的内部函数）');
                console.log('  ℹ 从代码分析，应该绑定了 click、mousedown、touchstart 事件');
                info.push('事件监听器检测需要 Chrome DevTools 的 getEventListeners 函数');
            }
            
            info.push('找到通知图标');
        } else {
            console.log('  ✗ 未找到通知图标');
            issues.push('未找到 #notificationIcon 元素');
        }
        console.log('');
        
        // 6. 检查下拉菜单
        console.log('【6. 下拉菜单检查】');
        const dropdown = document.getElementById('notificationDropdown');
        if (dropdown) {
            const dropdownRect = dropdown.getBoundingClientRect();
            const dropdownStyle = window.getComputedStyle(dropdown);
            console.log('  ✓ 找到下拉菜单');
            console.log('  - 位置:', dropdownRect);
            console.log('  - z-index:', dropdownStyle.zIndex);
            console.log('  - display:', dropdownStyle.display);
            console.log('  - visibility:', dropdownStyle.visibility);
            console.log('  - opacity:', dropdownStyle.opacity);
            console.log('  - pointer-events:', dropdownStyle.pointerEvents);
            console.log('  - position:', dropdownStyle.position);
            console.log('  - top:', dropdownStyle.top);
            console.log('  - right:', dropdownStyle.right);
            console.log('  - 是否有 show 类:', dropdown.classList.contains('show'));
            
            const isVisible = dropdownStyle.display !== 'none' && 
                            dropdownStyle.visibility !== 'hidden' && 
                            dropdownStyle.opacity !== '0';
            console.log('  - 是否可见:', isVisible);
            
            info.push('找到下拉菜单');
        } else {
            console.log('  ✗ 未找到下拉菜单');
            issues.push('未找到 #notificationDropdown 元素');
        }
        console.log('');
        
        // 7. 检查通知徽章
        console.log('【7. 通知徽章检查】');
        const badge = document.getElementById('notificationBadge');
        if (badge) {
            const badgeStyle = window.getComputedStyle(badge);
            console.log('  ✓ 找到通知徽章');
            console.log('  - display:', badgeStyle.display);
            console.log('  - 内容:', badge.textContent);
            info.push('找到通知徽章');
        } else {
            console.log('  ⚠ 未找到通知徽章（可能不是关键问题）');
            warnings.push('未找到 #notificationBadge 元素');
        }
        console.log('');
        
        // 8. 检查元素层级关系
        console.log('【8. 元素层级关系检查】');
        if (navbarInfo && iconWrapper) {
            // 检查z-index是否足够
            const navbarZ = parseInt(navbarInfo.style.zIndex) || 0;
            const iconZ = parseInt(window.getComputedStyle(iconWrapper).zIndex) || 0;
            const containerZ = notificationContainer ? 
                parseInt(window.getComputedStyle(notificationContainer).zIndex) || 0 : 0;
            
            console.log('  - 导航栏 z-index:', navbarZ);
            console.log('  - 图标 z-index:', iconZ);
            console.log('  - 容器 z-index:', containerZ);
            
            if (iconZ <= navbarZ) {
                warnings.push('通知图标的 z-index 可能不够高');
            }
            
            // 检查是否在导航栏内
            if (navbar.contains(iconWrapper)) {
                console.log('  ✓ 通知图标在导航栏内');
                info.push('通知图标在导航栏内');
            } else {
                console.log('  ⚠ 通知图标不在导航栏内');
                warnings.push('通知图标不在导航栏内');
            }
        }
        console.log('');
        
        // 9. 检查是否有遮挡元素
        console.log('【9. 遮挡检查】');
        if (iconWrapper) {
            const iconRect = iconWrapper.getBoundingClientRect();
            const centerX = iconRect.left + iconRect.width / 2;
            const centerY = iconRect.top + iconRect.height / 2;
            
            console.log('  - 通知图标中心位置:', Math.round(centerX), Math.round(centerY));
            console.log('  - 通知图标尺寸:', iconRect.width, 'x', iconRect.height);
            console.log('  - 通知图标边界:', {
                left: Math.round(iconRect.left),
                right: Math.round(iconRect.right),
                top: Math.round(iconRect.top),
                bottom: Math.round(iconRect.bottom)
            });
            
            // 检查多个点的元素（更可靠）
            const testPoints = [
                { x: Math.round(centerX), y: Math.round(centerY), name: '中心' },
                { x: Math.round(iconRect.left + 5), y: Math.round(iconRect.top + 5), name: '左上角' },
                { x: Math.round(iconRect.right - 5), y: Math.round(iconRect.top + 5), name: '右上角' },
                { x: Math.round(iconRect.left + 5), y: Math.round(iconRect.bottom - 5), name: '左下角' },
                { x: Math.round(iconRect.right - 5), y: Math.round(iconRect.bottom - 5), name: '右下角' }
            ];
            
            let foundOverlay = false;
            let foundIcon = false;
            
            testPoints.forEach(point => {
                const elem = document.elementFromPoint(point.x, point.y);
                if (elem) {
                    const isIcon = iconWrapper.contains(elem) || iconWrapper.isSameNode(elem);
                    if (isIcon) {
                        foundIcon = true;
                    } else {
                        if (!foundOverlay) {
                            console.log('  ⚠', point.name, '位置发现可能的遮挡元素:', elem.tagName, elem.className || '(无类名)', elem.id || '(无ID)');
                            const overlayStyle = window.getComputedStyle(elem);
                            console.log('    - pointer-events:', overlayStyle.pointerEvents);
                            console.log('    - z-index:', overlayStyle.zIndex);
                            console.log('    - position:', overlayStyle.position);
                            foundOverlay = true;
                            warnings.push(point.name + '位置可能有遮挡: ' + elem.tagName + '.' + (elem.className || ''));
                        }
                    }
                }
            });
            
            if (foundIcon && !foundOverlay) {
                console.log('  ✓ 通知图标区域可以正常点击（未发现遮挡）');
                info.push('没有发现遮挡');
            } else if (foundOverlay) {
                console.log('  ⚠ 在某些位置发现了可能的遮挡元素');
            } else {
                console.log('  ℹ 无法确定遮挡情况（可能是下拉菜单打开时的状态）');
            }
        }
        console.log('');
        
        // 10. 测试点击功能
        console.log('【10. 点击功能测试】');
        if (iconWrapper && dropdown) {
            console.log('  - 尝试模拟点击事件...');
            try {
                // 记录初始状态
                const initialState = {
                    isOpen: dropdown.classList.contains('show'),
                    display: window.getComputedStyle(dropdown).display
                };
                console.log('  - 初始状态 - 是否打开:', initialState.isOpen, 'display:', initialState.display);
                
                let clickTriggered = false;
                let dropdownOpened = false;
                
                const testClickHandler = function(e) {
                    clickTriggered = true;
                    console.log('  ✓ 点击事件成功触发');
                    // 检查下拉菜单是否打开
                    setTimeout(() => {
                        const newState = {
                            isOpen: dropdown.classList.contains('show'),
                            display: window.getComputedStyle(dropdown).display
                        };
                        if (newState.isOpen && newState.display !== 'none') {
                            dropdownOpened = true;
                            console.log('  ✓ 下拉菜单已打开 - display:', newState.display);
                        } else {
                            console.log('  ⚠ 点击事件触发但下拉菜单未打开');
                            console.log('  - 新状态 - 是否打开:', newState.isOpen, 'display:', newState.display);
                        }
                    }, 50);
                    iconWrapper.removeEventListener('click', testClickHandler);
                };
                iconWrapper.addEventListener('click', testClickHandler, true);
                
                // 创建并触发点击事件
                const clickEvent = new MouseEvent('click', {
                    bubbles: true,
                    cancelable: true,
                    view: window,
                    clientX: iconWrapper.getBoundingClientRect().left + iconWrapper.getBoundingClientRect().width / 2,
                    clientY: iconWrapper.getBoundingClientRect().top + iconWrapper.getBoundingClientRect().height / 2
                });
                iconWrapper.dispatchEvent(clickEvent);
                
                // 检查点击外部关闭事件
                setTimeout(() => {
                    const finalState = {
                        isOpen: dropdown.classList.contains('show'),
                        display: window.getComputedStyle(dropdown).display
                    };
                    if (clickTriggered && !dropdownOpened && finalState.display === 'none') {
                        console.log('  ⚠ 点击事件触发后，菜单可能被点击外部关闭事件立即关闭了');
                        warnings.push('菜单可能被点击外部关闭事件过早关闭');
                    }
                }, 150);
            } catch (error) {
                console.log('  ✗ 测试点击时出错:', error.message);
                issues.push('测试点击时出错: ' + error.message);
            }
        } else {
            console.log('  ✗ 无法测试（通知图标或下拉菜单不存在）');
        }
        console.log('');
        
        // 10.5. 检查点击外部关闭事件
        console.log('【10.5. 点击外部关闭事件检查】');
        console.log('  ℹ 正在监听点击外部关闭事件...');
        let externalClickCount = 0;
        let externalClickCloses = 0;
        
        const externalClickMonitor = function(e) {
            const iconWrapper = document.getElementById('notificationIcon');
            const dropdown = document.getElementById('notificationDropdown');
            if (!iconWrapper || !dropdown) return;
            
            // 检查是否点击在通知图标或下拉菜单外部
            if (!iconWrapper.contains(e.target) && !dropdown.contains(e.target)) {
                externalClickCount++;
                const isOpen = dropdown.classList.contains('show') || window.getComputedStyle(dropdown).display !== 'none';
                if (isOpen) {
                    externalClickCloses++;
                    console.log('  ⚠ 检测到点击外部关闭事件 #' + externalClickCloses, 
                               '- 目标元素:', e.target.tagName, e.target.className || '(无类名)',
                               '- 时间:', new Date().toISOString());
                }
            }
        };
        
        document.addEventListener('click', externalClickMonitor, true);
        
        // 5秒后移除监听器并报告
        setTimeout(() => {
            document.removeEventListener('click', externalClickMonitor, true);
            console.log('  - 监听期间点击外部次数:', externalClickCount);
            console.log('  - 导致关闭的次数:', externalClickCloses);
            if (externalClickCloses > 0) {
                warnings.push('检测到点击外部关闭事件可能过早触发');
            }
            info.push('点击外部关闭事件监听完成');
        }, 5000);
        console.log('  ℹ 将在5秒后结束监听（在此期间点击页面任意位置）');
        console.log('');
        
        // 11. 检查API端点
        console.log('【11. API端点检查】');
        fetch('/api/notifications/', {
            method: 'GET',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
            },
            credentials: 'same-origin',
        })
        .then(response => {
            console.log('  - API响应状态:', response.status, response.statusText);
            if (response.ok) {
                console.log('  ✓ API端点可访问');
                info.push('API端点可访问');
                return response.json();
            } else {
                console.log('  ✗ API端点返回错误');
                issues.push('API端点返回错误: ' + response.status);
                throw new Error('API错误');
            }
        })
        .then(data => {
            console.log('  - API返回数据:', data);
            if (data.notifications) {
                console.log('  - 通知数量:', data.notifications.length);
                console.log('  - 未读数量:', data.unread_count || 0);
                info.push('API返回了 ' + data.notifications.length + ' 条通知');
            }
        })
        .catch(error => {
            console.log('  ✗ API请求失败:', error.message);
            issues.push('API请求失败: ' + error.message);
        });
        console.log('');
        
        // 12. 检查控制台错误
        console.log('【12. JavaScript错误检查】');
        console.log('  ℹ 请查看浏览器控制台是否有JavaScript错误');
        console.log('  ℹ 检查 Network 标签页，确认 notification_widget.js 是否正确加载');
        console.log('');
        
        // 13. 总结
        console.log('【13. 诊断总结】');
        console.log('');
        
        if (issues.length === 0 && warnings.length === 0) {
            console.log('  ✓ 未发现明显问题');
        } else {
            if (issues.length > 0) {
                console.log('  发现以下问题：');
                issues.forEach(issue => console.log('  ✗', issue));
                console.log('');
            }
            
            if (warnings.length > 0) {
                console.log('  警告：');
                warnings.forEach(warning => console.log('  ⚠', warning));
                console.log('');
            }
        }
        
        if (info.length > 0) {
            console.log('  信息：');
            info.forEach(i => console.log('  ℹ', i));
            console.log('');
        }
        
        // 提供修复建议
        if (issues.length > 0 || warnings.length > 0) {
            console.log('【修复建议】');
            if (issues.includes('未找到 notification_widget.js 脚本')) {
                console.log('  1. 检查模板是否正确引入了 notification_widget.js');
                console.log('  2. 检查 context_processors 是否正确配置');
            }
            if (issues.includes('未找到 #notificationIcon 元素')) {
                console.log('  1. 检查 initNotificationWidget 函数是否执行');
                console.log('  2. 检查导航栏是否找到');
                console.log('  3. 检查脚本是否在DOM加载完成后执行');
            }
            if (issues.includes('通知图标没有绑定 click 事件监听器')) {
                console.log('  1. 检查 initNotificationFunctionality 函数是否执行');
                console.log('  2. 检查是否有JavaScript错误阻止了事件绑定');
            }
            if (warnings.some(w => w.includes('pointer-events'))) {
                console.log('  1. 检查CSS是否有其他规则覆盖了 pointer-events');
                console.log('  2. 检查是否有 :before 或 :after 伪元素遮挡');
            }
            if (warnings.some(w => w.includes('遮挡'))) {
                console.log('  1. 检查是否有其他元素的 z-index 更高');
                console.log('  2. 检查是否有绝对定位的元素覆盖了通知图标');
            }
            console.log('');
        }
        
        console.log('========================================');
        console.log('诊断完成');
        console.log('========================================');
        
        // 返回诊断结果对象
        return {
            issues: issues,
            warnings: warnings,
            info: info,
            elements: {
                script: !!notificationScript,
                styles: !!notificationStyles,
                navbar: !!navbar,
                container: !!notificationContainer,
                iconWrapper: !!iconWrapper,
                dropdown: !!dropdown,
                badge: !!badge
            },
            navbar: navbarInfo,
            hasProblems: issues.length > 0 || warnings.length > 0
        };
    }
    
    // 辅助函数：获取元素的完整路径
    function getElementPath(element) {
        const path = [];
        let current = element;
        while (current && current !== document.body) {
            let selector = current.tagName.toLowerCase();
            if (current.id) {
                selector += '#' + current.id;
            } else if (current.className) {
                const classes = Array.from(current.classList).slice(0, 2).join('.');
                if (classes) selector += '.' + classes;
            }
            path.unshift(selector);
            current = current.parentElement;
        }
        return path.join(' > ');
    }
    
    // 辅助函数：手动触发通知中心打开（用于测试）
    function testOpenNotification() {
        console.log('测试：手动触发通知中心打开...');
        const iconWrapper = document.getElementById('notificationIcon');
        const dropdown = document.getElementById('notificationDropdown');
        
        if (!iconWrapper) {
            console.error('✗ 找不到通知图标');
            return false;
        }
        
        if (!dropdown) {
            console.error('✗ 找不到下拉菜单');
            return false;
        }
        
        // 直接修改样式打开
        dropdown.style.display = 'flex';
        dropdown.classList.add('show');
        
        console.log('✓ 已手动打开通知中心（仅用于测试）');
        console.log('  下拉菜单现在应该可见');
        console.log('  如果菜单立即关闭，可能是点击外部关闭事件的问题');
        return true;
    }
    
    // 辅助函数：监控实际点击（用于调试）
    function monitorRealClicks() {
        console.log('开始监控实际点击事件...');
        console.log('请在页面上实际点击通知图标，观察下面的输出');
        
        const iconWrapper = document.getElementById('notificationIcon');
        const dropdown = document.getElementById('notificationDropdown');
        
        if (!iconWrapper || !dropdown) {
            console.error('✗ 找不到通知元素');
            return;
        }
        
        let clickSequence = [];
        
        // 监控所有点击事件
        const clickMonitor = function(e) {
            const target = e.target;
            const isIcon = iconWrapper.contains(target) || iconWrapper.isSameNode(target);
            const isDropdown = dropdown.contains(target);
            const isExternal = !isIcon && !isDropdown;
            
            const eventInfo = {
                time: Date.now(),
                target: target.tagName + (target.className ? '.' + target.className.split(' ')[0] : ''),
                isIcon: isIcon,
                isDropdown: isDropdown,
                isExternal: isExternal,
                dropdownOpen: dropdown.classList.contains('show') || window.getComputedStyle(dropdown).display !== 'none'
            };
            
            clickSequence.push(eventInfo);
            
            console.log(`[${clickSequence.length}] 点击事件:`, 
                eventInfo.target,
                '- 图标:', eventInfo.isIcon ? '是' : '否',
                '- 菜单:', eventInfo.isDropdown ? '是' : '否',
                '- 外部:', eventInfo.isExternal ? '是' : '否',
                '- 菜单状态:', eventInfo.dropdownOpen ? '打开' : '关闭');
            
            // 检查是否图标点击后立即被外部点击关闭
            if (clickSequence.length >= 2) {
                const prev = clickSequence[clickSequence.length - 2];
                const curr = clickSequence[clickSequence.length - 1];
                
                if (prev.isIcon && prev.dropdownOpen && curr.isExternal && 
                    (curr.time - prev.time) < 150 && !curr.dropdownOpen) {
                    console.warn('⚠⚠⚠ 检测到问题：图标点击后立即被外部点击关闭！');
                    console.warn('  时间差:', curr.time - prev.time, 'ms');
                    console.warn('  这可能是点击外部关闭事件过早触发导致的');
                }
            }
        };
        
        document.addEventListener('click', clickMonitor, true);
        
        console.log('监控已启动，点击任意位置查看详细信息');
        console.log('停止监控: window.stopMonitoringClicks()');
        
        window.stopMonitoringClicks = function() {
            document.removeEventListener('click', clickMonitor, true);
            console.log('监控已停止');
            console.log('点击事件序列:', clickSequence);
            delete window.stopMonitoringClicks;
        };
        
        return {
            stop: function() {
                window.stopMonitoringClicks();
            }
        };
    }
    
    // 将函数暴露到全局作用域
    window.notificationDiagnostic = notificationDiagnostic;
    window.testOpenNotification = testOpenNotification;
    window.monitorRealClicks = monitorRealClicks;
    
    // 标记脚本已加载
    window.notificationDiagnosticLoaded = true;
    
    // 触发自定义事件，通知脚本已加载
    if (typeof CustomEvent !== 'undefined') {
        window.dispatchEvent(new CustomEvent('notificationDiagnosticLoaded'));
    }
    
    // 如果脚本直接运行，自动执行诊断
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            console.log('通知中心诊断脚本已加载 ✓');
            console.log('使用方法：');
            console.log('  - 运行诊断: notificationDiagnostic()');
            console.log('  - 测试打开: testOpenNotification()');
            console.log('  - 监控实际点击: monitorRealClicks()');
        });
    } else {
        console.log('通知中心诊断脚本已加载 ✓');
        console.log('使用方法：');
        console.log('  - 运行诊断: notificationDiagnostic()');
        console.log('  - 测试打开: testOpenNotification()');
        console.log('  - 监控实际点击: monitorRealClicks()');
    }
    // 提供一个便捷的加载函数（暴露到全局，即使脚本未加载也能调用）
    window.loadNotificationDiagnostic = function(callback) {
        // 如果已经加载，直接执行回调
        if (window.notificationDiagnosticLoaded && window.notificationDiagnostic) {
            console.log('✓ 通知中心诊断脚本已加载，可以直接使用');
            if (callback) callback();
            return Promise.resolve();
        }
        
        // 移除旧的脚本标签（如果有）
        const oldScript = document.querySelector('script[src*="notification_diagnostic.js"]');
        if (oldScript) {
            oldScript.remove();
        }
        
        return new Promise(function(resolve, reject) {
            const script = document.createElement('script');
            script.src = '/static/js/notification_diagnostic.js?' + Date.now();
            
            // 监听加载完成
            script.onload = function() {
                // 等待一小段时间确保函数已定义
                setTimeout(function() {
                    if (window.notificationDiagnosticLoaded && window.notificationDiagnostic) {
                        console.log('✓ 通知中心诊断脚本加载完成');
                        if (callback) callback();
                        resolve();
                    } else {
                        console.warn('⚠ 脚本加载完成但函数未定义，请稍后再试');
                        reject(new Error('脚本函数未定义'));
                    }
                }, 100);
            };
            
            script.onerror = function() {
                console.error('✗ 通知中心诊断脚本加载失败');
                reject(new Error('脚本加载失败'));
            };
            
            document.head.appendChild(script);
        });
    };
    
    // 提供一键诊断函数（暴露到全局）
    window.runNotificationDiagnostic = function() {
        return window.loadNotificationDiagnostic(function() {
            console.log('\n开始运行诊断...\n');
            if (window.notificationDiagnostic) {
                window.notificationDiagnostic();
            } else {
                console.error('✗ notificationDiagnostic 函数未定义');
            }
        });
    };
})();
